import boto3
import os
import sys
from datetime import datetime, timedelta
from azure.storage.blob import BlobServiceClient
from botocore.exceptions import ClientError

# Environment variables from Azure DevOps pipeline
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
EMAIL_TO = os.getenv("EMAIL_TO", "ROAD_Ops_L2_Support@theaa.com")

# AWS clients
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
    zip_today = datetime.utcnow().strftime("%Y-%m-%d")
    # Expected patterns for today
    expected_files = [
        f"indoor_users_{today}_",        # txt file prefix
        f"Oracle/AABS-{zip_today}.zip",  # zip file exact name
    ]

    missing_files = []
    size_mismatch_files = []

    for env, container_name in AZURE_CONTAINERS.items():
        s3_bucket = S3_BUCKETS[env]
        container_client = blob_service_client.get_container_client(container_name)

        # List all Azure blobs
        azure_blobs = {b.name: b.size for b in container_client.list_blobs()}
        # List all S3 objects
        s3_objs_resp = s3_client.list_objects_v2(Bucket=s3_bucket)
        s3_objects = {obj["Key"]: obj["Size"] for obj in s3_objs_resp.get("Contents", [])}

        for pattern in expected_files:
            # Find blob in Azure
            azure_match = [name for name in azure_blobs if name.startswith(pattern)]
            if not azure_match:
                missing_files.append(f"Azure {env} missing {pattern}")
                continue  # Skip S3 size check if missing in Azure

            # Check S3
            s3_match = [key for key in s3_objects if key.startswith(pattern)]
            if not s3_match:
                missing_files.append(f"S3 {env} missing {pattern}")
                continue

            # Compare sizes
            azure_size = azure_blobs[azure_match[0]]
            s3_size = s3_objects[s3_match[0]]
            if azure_size != s3_size:
                size_mismatch_files.append(
                    f"{env}: File {pattern} size mismatch - Azure({azure_size}) != S3({s3_size})"
                )

    # Report results
    if missing_files or size_mismatch_files:
        print("❌ File Validation Failed:")
        for mf in missing_files + size_mismatch_files:
            print("   -", mf)
        sys.exit(1)
    else:
        print("✅ All files exist and sizes match for today.")

def main():
    secret = get_secret()
    connection_string = secret["connection_string"]
    blob_service_client = BlobServiceClient.from_connection_string(conn_str=connection_string)

    if MODE == "daily":
        validate_daily(blob_service_client)
    else:
        print("❌ Weekly mode not implemented yet. Only daily validation.")
        sys.exit(1)

if __name__ == "__main__":
    main()
