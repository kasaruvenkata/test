# Infra/modules/lambda/MonitorLambda/lambda_monitor.py

"""
Monitor Lambda - validate Azure Blob -> S3 sync.
- Reuses SECRET_NAME, AZURE_CONTAINER, S3_BUCKET env vars used by your SyncLambda.
- If AZURE_CONNECTION_STRING env var is present, it will use that (easy local testing).
- Writes a plain text report to /tmp and uploads it to S3 under:
    s3://<S3_BUCKET>/monitor-reports/<env>-monitor-<YYYYMMDDHHMMSS>.txt
- Returns JSON with 'discrepancies' list and 'report_s3_key' if uploaded.

Event examples:
  {"mode":"daily", "days":2}
  {"mode":"daily", "expected_files":["indoor_users_20250908_140922.txt","Oracle/AABS-2025-08-29.zip"]}
"""

import os
import json
import boto3
import botocore
from datetime import datetime, timedelta, timezone
from azure.storage.blob import BlobServiceClient

# --- Reuse existing variable names from your sync lambda ---
SECRET_NAME = os.getenv("SECRET_NAME", "azneprod")
AZURE_CONTAINER = os.getenv("AZURE_CONTAINER", "uat")
S3_BUCKET = os.getenv("S3_BUCKET")  # must be set in Lambda env or passed on local run

# Local testing possibility: provide AZURE_CONNECTION_STRING env var
AZURE_CONNECTION_STRING = os.getenv("AZURE_CONNECTION_STRING", "")

# Report prefix in S3
REPORT_PREFIX = os.getenv("REPORT_PREFIX", "monitor-reports/")

# AWS clients
secrets_client = boto3.client("secretsmanager")
s3_client = boto3.client("s3")

def get_secret_dict():
    """Fetch secret from Secrets Manager. Return dict or {}."""
    if AZURE_CONNECTION_STRING:
        return {"connection_string": AZURE_CONNECTION_STRING}
    try:
        resp = secrets_client.get_secret_value(SecretId=SECRET_NAME)
        sec = resp.get("SecretString", "{}")
        return json.loads(sec)
    except Exception as e:
        print("Warning: could not read secret from Secrets Manager:", e)
        return {}

def get_container_client():
    secret = get_secret_dict()
    conn = secret.get("connection_string") or secret.get("AZURE_STORAGE_CONNECTION_STRING") or secret.get("connectionString")
    if not conn:
        raise RuntimeError("Azure connection string not found. Set AZURE_CONNECTION_STRING locally or ensure Secrets Manager contains connection_string under secret: " + SECRET_NAME)
    bsc = BlobServiceClient.from_connection_string(conn)
    return bsc.get_container_client(AZURE_CONTAINER)

def list_recent_blobs(container_client, days=2, prefixes=None):
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    for blob in container_client.list_blobs():
        if prefixes and not any(blob.name.startswith(p) for p in prefixes):
            continue
        if blob.last_modified and blob.last_modified >= cutoff:
            yield blob

def check_specific_blob(container_client, blob_name):
    try:
        props = container_client.get_blob_client(blob_name).get_blob_properties()
        return props
    except Exception as e:
        # Return a fake object with name and size=None to indicate missing in Azure
        class Missing:
            pass
        m = Missing()
        m.name = blob_name
        m.size = None
        m.last_modified = None
        return m

def validate_blobs(container_client, blobs):
    discrepancies = []
    checked = 0
    for blob in blobs:
        checked += 1
        key = blob.name
        azure_size = getattr(blob, "size", None)
        # Check S3
        try:
            head = s3_client.head_object(Bucket=S3_BUCKET, Key=key)
            s3_size = head["ContentLength"]
            if azure_size is None:
                # Blob missing in Azure
                discrepancies.append(f"MISSING_IN_AZURE: {key}")
            else:
                if azure_size != s3_size:
                    discrepancies.append(f"SIZE_MISMATCH: {key} | azure={azure_size} | s3={s3_size}")
        except botocore.exceptions.ClientError as e:
            code = e.response.get("Error", {}).get("Code", "")
            if code in ("404", "NotFound", "NoSuchKey", "NoSuchBucket"):
                discrepancies.append(f"MISSING_IN_S3: {key}")
            else:
                discrepancies.append(f"S3_ERROR: {key} | {str(e)}")
    return discrepancies, checked

def write_report_and_upload(discrepancies, checked_count, mode):
    now = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    if not S3_BUCKET:
        print("S3_BUCKET not set, skipping S3 upload of report")
        report_key = None
    else:
        report_name = f"{mode}-monitor-{now}.txt"
        report_key = REPORT_PREFIX.rstrip("/") + "/" + report_name
    lines = []
    lines.append(f"Mode: {mode}")
    lines.append(f"Bucket: {S3_BUCKET}")
    lines.append(f"Container: {AZURE_CONTAINER}")
    lines.append(f"Checked objects: {checked_count}")
    lines.append(f"Time(UTC): {now}")
    lines.append("")
    if not discrepancies:
        lines.append("RESULT: ALL_OK")
    else:
        lines.append("RESULT: DISCREPANCIES_FOUND")
        lines.append("")
        lines.extend(discrepancies)
    body = "\n".join(lines)
    # write local tmp file
    local_path = f"/tmp/{mode}-monitor-{now}.txt"
    with open(local_path, "w") as f:
        f.write(body)
    # upload to S3 (so pipeline or ops can fetch as artifact)
    if report_key and S3_BUCKET:
        try:
            with open(local_path, "rb") as f:
                s3_client.put_object(Bucket=S3_BUCKET, Key=report_key, Body=f)
            print(f"Uploaded report to s3://{S3_BUCKET}/{report_key}")
        except Exception as e:
            print("Failed to upload report to S3:", e)
            report_key = None
    return local_path, report_key

def lambda_handler(event, context):
    """
    event options:
      - mode: "daily" (default) or "weekly"
      - days: integer overriding default days (daily=2, weekly=7)
      - prefixes: list of prefixes to filter (default ["indoor_users_", "Oracle/"])
      - expected_files: optional list of exact blob names to validate
    """
    mode = event.get("mode", "daily")
    days = int(event.get("days", 2 if mode == "daily" else 7))
    prefixes = event.get("prefixes", ["indoor_users_", "Oracle/"])
    expected_files = event.get("expected_files", None)

    if not S3_BUCKET:
        raise RuntimeError("S3_BUCKET env var must be set in Lambda environment")

    container_client = get_container_client()

    to_check = []
    if expected_files:
        for f in expected_files:
            to_check.append(check_specific_blob(container_client, f))
    else:
        # list recent blobs matching prefixes
        for b in list_recent_blobs(container_client, days=days, prefixes=prefixes):
            to_check.append(b)

    discrepancies, checked_count = validate_blobs(container_client, to_check)
    local_report, report_s3_key = write_report_and_upload(discrepancies, checked_count, mode)

    result = {
        "status": "ok",
        "mode": mode,
        "checked": checked_count,
        "discrepancies": discrepancies,
        "local_report_path": local_report,
        "report_s3_key": report_s3_key
    }
    # print JSON to stdout so callers (CLI/pipelines) capture it
    print(json.dumps(result))
    return result

# allow local quick test
if __name__ == "__main__":
    import sys
    # allow passing expected filenames from CLI separated by comma:
    args = {}
    if len(sys.argv) > 1:
        args["mode"] = sys.argv[1]
    if len(sys.argv) > 2:
        args["expected_files"] = sys.argv[2].split(",")
    print("Running local test with args:", args)
    print(lambda_handler(args, None))
