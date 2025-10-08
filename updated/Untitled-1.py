# Infra/modules/lambda/MonitorLambda/lambda_monitor.py

"""
Monitor lambda: validate files copied from Azure Blob -> S3.
Reuses SECRET_NAME, AZURE_CONTAINER, S3_BUCKET env vars from your SyncLambda.
Behavior:
 - daily mode: checks blobs modified in last N days (default 2)
 - weekly mode: checks blobs modified within last 7 days and produces a summary
If SES fails, optionally publish to SNS topic (SNS_TOPIC_ARN env var).
"""

import os
import json
import boto3
import botocore
from datetime import datetime, timedelta, timezone
from azure.storage.blob import BlobServiceClient

# --- Reused / consistent with your SyncLambda ---
SECRET_NAME = os.getenv("SECRET_NAME", "azneprod")
AZURE_CONTAINER = os.getenv("AZURE_CONTAINER", "uat")
S3_BUCKET = os.getenv("S3_BUCKET")  # e.g. aabackstop-uat or aabackstop-prod

# Email config
EMAIL_RECIPIENT = os.getenv("EMAIL_RECIPIENT", "ROAD_Ops_L2_Support@theaa.com")
EMAIL_SOURCE = os.getenv("EMAIL_SOURCE", EMAIL_RECIPIENT)  # SES identity; must be verified
SNS_TOPIC_ARN = os.getenv("SNS_TOPIC_ARN", "")  # optional fallback

# clients
secrets_client = boto3.client("secretsmanager")
s3_client = boto3.client("s3")
ses_client = boto3.client("ses")
sns_client = boto3.client("sns")

def get_secret_dict():
    try:
        resp = secrets_client.get_secret_value(SecretId=SECRET_NAME)
        secret_string = resp.get("SecretString", "{}")
        return json.loads(secret_string)
    except Exception as e:
        print("Error reading secret:", e)
        raise

def get_container_client():
    secret = get_secret_dict()
    # support multiple key names for connection string
    conn = secret.get("connection_string") or secret.get("AZURE_STORAGE_CONNECTION_STRING") or secret.get("connectionString")
    if not conn:
        raise RuntimeError("Azure connection string not found in Secrets Manager under keys: connection_string / AZURE_STORAGE_CONNECTION_STRING")
    bsc = BlobServiceClient.from_connection_string(conn)
    return bsc.get_container_client(AZURE_CONTAINER)

def list_recent_blobs(container_client, days=2, prefixes=None):
    """Yield blobs modified in last `days`. Filter by prefixes (list) if provided."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    for blob in container_client.list_blobs():
        # optional prefix filter
        if prefixes and not any(blob.name.startswith(p) for p in prefixes):
            continue
        if blob.last_modified >= cutoff:
            yield blob

def validate_blobs(blobs):
    """Compare each blob to S3 key of same name. Return list of discrepancy strings."""
    discrepancies = []
    for blob in blobs:
        key = blob.name
        azure_size = getattr(blob, "size", None)
        try:
            head = s3_client.head_object(Bucket=S3_BUCKET, Key=key)
            s3_size = head["ContentLength"]
            if azure_size != s3_size:
                discrepancies.append(f"SIZE_MISMATCH: {key} | azure={azure_size} | s3={s3_size}")
        except botocore.exceptions.ClientError as e:
            code = e.response.get("Error", {}).get("Code", "")
            # not found on S3
            if code in ("404", "NotFound", "NoSuchKey", "NoSuchBucket"):
                discrepancies.append(f"MISSING_IN_S3: {key}")
            else:
                discrepancies.append(f"S3_ERROR: {key} | {str(e)}")
    return discrepancies

def send_email(subject, body):
    """Try SES first. If SES fails and SNS_TOPIC_ARN provided, publish to SNS."""
    try:
        ses_client.send_email(
            Source=EMAIL_SOURCE,
            Destination={"ToAddresses": [EMAIL_RECIPIENT]},
            Message={
                "Subject": {"Data": subject},
                "Body": {"Text": {"Data": body}},
            },
        )
        print("SES email sent")
        return True
    except Exception as e:
        print("SES send failed:", e)
        if SNS_TOPIC_ARN:
            try:
                sns_client.publish(TopicArn=SNS_TOPIC_ARN, Subject=subject, Message=body)
                print("Published to SNS")
                return True
            except Exception as e2:
                print("SNS publish failed:", e2)
        return False

def make_summary(mode, discrepancies, checked_count):
    now = datetime.now(timezone.utc)
    if not discrepancies:
        return f"[{mode.upper()}] All good for bucket {S3_BUCKET} / container {AZURE_CONTAINER}.\nChecked objects: {checked_count}\nTime: {now.isoformat()}"
    else:
        lines = [f"[{mode.upper()}] Discrepancies found for bucket {S3_BUCKET} / container {AZURE_CONTAINER}"]
        lines.append(f"Checked objects: {checked_count}")
        lines.extend(discrepancies)
        lines.append(f"Time: {now.isoformat()}")
        return "\n".join(lines)

def lambda_handler(event, context):
    """
    event example:
      {"mode": "daily", "days": 2, "prefixes": ["indoor_users_", "Oracle/"]}
      {"mode": "weekly", "days": 7}
      or pass "expected_files": ["indoor_users_20250908_140922.txt", "Oracle/AABS-2025-08-29.zip"]
    """
    mode = event.get("mode", "daily")
    days = int(event.get("days", 2 if mode == "daily" else 7))
    prefixes = event.get("prefixes", ["indoor_users_", "Oracle/"])
    expected_files = event.get("expected_files", None)

    if not S3_BUCKET:
        raise RuntimeError("S3_BUCKET env var is not set")

    container_client = get_container_client()

    # build list of blobs to check
    to_check = []
    if expected_files:
        # validate specific files requested
        for f in expected_files:
            # fetch blob properties (if exists)
            try:
                blob_client = container_client.get_blob_client(f)
                props = blob_client.get_blob_properties()
                to_check.append(props)
            except Exception as e:
                # blob missing in Azure; include as discrepancy
                print(f"Expected blob missing from Azure: {f} -> {e}")
                to_check.append(type("Missing", (), {"name": f, "size": None, "last_modified": None}))
    else:
        # default: scan recent blobs
        for b in list_recent_blobs(container_client, days=days, prefixes=prefixes):
            to_check.append(b)

    print(f"Checking {len(to_check)} objects from Azure container '{AZURE_CONTAINER}' for S3 bucket '{S3_BUCKET}' (mode={mode})")
    discrepancies = validate_blobs([b for b in to_check if getattr(b, "name", None) is not None])
    summary = make_summary(mode, discrepancies, len(to_check))
    subject = f"[MONITOR-{mode.upper()}] Sync check for {S3_BUCKET}"
    send_email(subject, summary)

    return {"status": "ok", "mode": mode, "checked": len(to_check), "discrepancies": discrepancies}

# local run for testing
if __name__ == "__main__":
    print(lambda_handler({"mode": "daily", "days": 7}, None))
