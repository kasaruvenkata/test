import boto3
import os
import sys
from datetime import datetime, timedelta
from azure.storage.blob import BlobServiceClient
from botocore.exceptions import ClientError

# ENV from pipeline vars
SECRET_NAME = os.getenv("SECRET_NAME")
REGION = os.getenv("AWS_REGION")
AZURE_CONTAINERS = {
    "uat": os.getenv("AZURE_CONTAINER_UAT"),
    "prod": os.getenv("AZURE_CONTAINER_PROD"),
}
S3_BUCKETS = {
    "uat": os.getenv("S3_UAT_BUCKET"),
    "prod": os.getenv("S3_PROD_BUCKET"),
}

MODE = os.getenv("MODE", "daily")  # daily | weekly

secrets_client = boto3.client("secretsmanager", region_name=REGION)
s3_client = boto3.client("s3", region_name=REGION)

def get_secret():
    try:
        response = secrets_client.get_secret_value(SecretId=SECRET_NAME)
        return eval(response["SecretString"])
    except ClientError as e:
        print(f"❌ Error retrieving secret: {e}")
        sys.exit(1)

def validate_daily(blob_service_client):
    today = datetime.utcnow().strftime("%Y%m%d")
    expected_patterns = [
        f"indoor_users_{today}_",  # txt file prefix
        f"Oracle/AABS-{datetime.utcnow().strftime('%Y-%m-%d')}.zip",
    ]
    missing_files = []

    for env, container_name in AZURE_CONTAINERS.items():
        container_client = blob_service_client.get_container_client(container_name)
        s3_bucket = S3_BUCKETS[env]

        blobs = [b.name for b in container_client.list_blobs()]
        s3_keys = [o["Key"] for o in s3_client.list_objects_v2(Bucket=s3_bucket).get("Contents", [])]

        for pattern in expected_patterns:
            if not any(b.startswith(pattern) for b in blobs):
                missing_files.append(f"Azure {env} missing {pattern}")
            if not any(k.startswith(pattern) for k in s3_keys):
                missing_files.append(f"S3 {env} missing {pattern}")

    if missing_files:
        print("❌ Missing files detected:")
        for mf in missing_files:
            print("   -", mf)
        sys.exit(1)
    else:
        print("✅ All expected files exist for today.")

def list_recent_blobs(container_client, days=7):
    cutoff = datetime.utcnow() - timedelta(days=days)
    blobs = []
    for blob in container_client.list_blobs():
        if blob.last_modified >= cutoff:
            blobs.append(f"{blob.name} ({blob.last_modified})")
    return blobs

def list_recent_s3(bucket: str, days=7):
    cutoff = datetime.utcnow() - timedelta(days=days)
    objs = []
    resp = s3_client.list_objects_v2(Bucket=bucket)
    for obj in resp.get("Contents", []):
        if obj["LastModified"].replace(tzinfo=None) >= cutoff:
            objs.append(f"{obj['Key']} ({obj['LastModified']})")
    return objs

def generate_weekly_report(blob_service_client):
    with open("weekly_report.txt", "w") as f:
        f.write("📊 Weekly File Transfer Report\n")
        f.write(f"Generated: {datetime.utcnow()}\n\n")

        for env, container_name in AZURE_CONTAINERS.items():
            f.write(f"--- {env.upper()} ---\n")
            container_client = blob_service_client.get_container_client(container_name)

            blobs = list_recent_blobs(container_client)
            f.write("Azure Blob:\n" + ("\n".join(blobs) if blobs else "No files found") + "\n\n")

            s3_bucket = S3_BUCKETS[env]
            s3_objs = list_recent_s3(s3_bucket)
            f.write("AWS S3:\n" + ("\n".join(s3_objs) if s3_objs else "No files found") + "\n\n")

    print("✅ Weekly report written to weekly_report.txt")

def main():
    secret = get_secret()
    connection_string = secret["connection_string"]
    blob_service_client = BlobServiceClient.from_connection_string(conn_str=connection_string)

    if MODE == "daily":
        validate_daily(blob_service_client)
    elif MODE == "weekly":
        generate_weekly_report(blob_service_client)
    else:
        print(f"❌ Unknown MODE: {MODE}")
        sys.exit(1)

if __name__ == "__main__":
    main()
