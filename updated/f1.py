Infra/modules/lambda/MonitorLambda/lambda_monitor.py
-----------------------------------------------------

"""
Monitor lambda: validate files copied from Azure Blob -> S3.
No email in this version — only returns JSON with discrepancies.
"""

import os
import json
import boto3
import botocore
from datetime import datetime, timedelta, timezone
from azure.storage.blob import BlobServiceClient

# --- Reused values from your SyncLambda ---
SECRET_NAME = os.getenv("SECRET_NAME", "azneprod")
AZURE_CONTAINER = os.getenv("AZURE_CONTAINER", "uat")
S3_BUCKET = os.getenv("S3_BUCKET")  # e.g., aabackstop-uat or aabackstop-prod

# Clients
secrets_client = boto3.client("secretsmanager")
s3_client = boto3.client("s3")

def get_secret_dict():
    resp = secrets_client.get_secret_value(SecretId=SECRET_NAME)
    secret_string = resp.get("SecretString", "{}")
    return json.loads(secret_string)

def get_container_client():
    secret = get_secret_dict()
    conn = secret.get("connection_string") or secret.get("AZURE_STORAGE_CONNECTION_STRING") or secret.get("connectionString")
    if not conn:
        raise RuntimeError("Azure connection string not found in Secrets Manager under keys: connection_string / AZURE_STORAGE_CONNECTION_STRING")
    bsc = BlobServiceClient.from_connection_string(conn)
    return bsc.get_container_client(AZURE_CONTAINER)

def list_recent_blobs(container_client, days=2, prefixes=None):
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    for blob in container_client.list_blobs():
        if prefixes and not any(blob.name.startswith(p) for p in prefixes):
            continue
        # Only include recent blobs
        if blob.last_modified >= cutoff:
            yield blob

def validate_blobs(blobs):
    discrepancies = []
    checked = 0
    for blob in blobs:
        checked += 1
        key = blob.name
        azure_size = getattr(blob, "size", None)
        try:
            head = s3_client.head_object(Bucket=S3_BUCKET, Key=key)
            s3_size = head["ContentLength"]
            if azure_size != s3_size:
                discrepancies.append({
                    "type": "SIZE_MISMATCH",
                    "key": key,
                    "azure_size": azure_size,
                    "s3_size": s3_size
                })
        except botocore.exceptions.ClientError as e:
            code = e.response.get("Error", {}).get("Code", "")
            if code in ("404", "NotFound", "NoSuchKey", "NoSuchBucket"):
                discrepancies.append({
                    "type": "MISSING_IN_S3",
                    "key": key
                })
            else:
                discrepancies.append({
                    "type": "S3_ERROR",
                    "key": key,
                    "error": str(e)
                })
    return checked, discrepancies

def lambda_handler(event, context):
    mode = event.get("mode", "daily")  # "daily" or "weekly"
    days = int(event.get("days", 2 if mode == "daily" else 7))
    # default prefixes to watch
    prefixes = event.get("prefixes", ["indoor_users_", "Oracle/"])
    expected_files = event.get("expected_files", None)

    if not S3_BUCKET:
        raise RuntimeError("S3_BUCKET env var is not set in Lambda environment")

    container_client = get_container_client()

    to_check = []
    if expected_files:
        # build props for each expected file (if present in Azure)
        for f in expected_files:
            try:
                blob_client = container_client.get_blob_client(f)
                props = blob_client.get_blob_properties()
                to_check.append(props)
            except Exception:
                # missing in Azure will show up as discrepancy (we still want to record it)
                # create a dummy object for validation step
                class Missing:
                    def __init__(self, name):
                        self.name = name
                        self.size = None
                        self.last_modified = None
                to_check.append(Missing(f))
    else:
        for b in list_recent_blobs(container_client, days=days, prefixes=prefixes):
            to_check.append(b)

    checked_count, discrepancies = validate_blobs(to_check)

    result = {
        "mode": mode,
        "s3_bucket": S3_BUCKET,
        "azure_container": AZURE_CONTAINER,
        "checked_count": checked_count,
        "discrepancies": discrepancies,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    # Print for logs & pipeline capture
    print(json.dumps(result, default=str))
    return result

if __name__ == "__main__":
    # quick test stub (won't run in Azure DevOps)
    print(lambda_handler({"mode": "daily", "days": 2}, None))
