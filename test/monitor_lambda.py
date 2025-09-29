import os
import sys
from datetime import datetime
from azure.storage.blob import BlobServiceClient
import boto3

def log(msg):
    print(f"[MonitorLambda] {msg}")

def get_expected_filename(prefix: str) -> str:
    """Generate expected filename based on today's date."""
    today = datetime.now().strftime("%d%m%Y")
    return f"{prefix}{today}.txt"

def get_blob_file_size(connection_string: str, container: str, blob_name: str) -> int:
    """Fetch size of a blob file from Azure Blob Storage."""
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    blob_client = blob_service_client.get_blob_client(container=container, blob=blob_name)
    props = blob_client.get_blob_properties()
    return props.size

def get_s3_file_size(bucket: str, key: str, aws_region: str = "us-east-1") -> int:
    """Fetch size of a file from S3."""
    s3 = boto3.client("s3", region_name=aws_region)
    response = s3.head_object(Bucket=bucket, Key=key)
    return response["ContentLength"]

def validate_file_transfer(env: str):
    """
    Validate that files exist in both Azure Blob and AWS S3
    and their sizes match.
    """
    log(f"Starting validation for {env.upper()}")

    # 🔹 Environment variables for Azure & AWS
    azure_conn_str = os.getenv(f"AZURE_STORAGE_CONNECTION_STRING_{env.upper()}")
    azure_container = os.getenv(f"AZURE_CONTAINER_{env.upper()}")
    aws_bucket = os.getenv(f"AWS_BUCKET_{env.upper()}")
    file_prefix = os.getenv("FILE_PREFIX", "myhr")

    # 🔹 Expected file name
    filename = get_expected_filename(file_prefix)

    # 🔹 Validate .txt file
    azure_blob = f"{env}/{filename}"     # e.g., uat/myhrDDMMYYYY.txt
    s3_key = f"{filename}"              # e.g., myhrDDMMYYYY.txt

    azure_size = get_blob_file_size(azure_conn_str, azure_container, azure_blob)
    aws_size = get_s3_file_size(aws_bucket, s3_key)

    if azure_size != aws_size:
        raise Exception(
            f"File size mismatch for {filename} → Azure={azure_size} vs AWS={aws_size}"
        )

    log(f"✅ Validation successful for {filename}, Size={aws_size} bytes")

    # 🔹 Validate Oracle .zip file
    oracle_filename = f"Oracle/{env}_oracle_{datetime.now().strftime('%d%m%Y')}.zip"
    azure_oracle_blob = f"{env}/{oracle_filename}"
    s3_oracle_key = oracle_filename

    azure_oracle_size = get_blob_file_size(azure_conn_str, azure_container, azure_oracle_blob)
    aws_oracle_size = get_s3_file_size(aws_bucket, s3_oracle_key)

    if azure_oracle_size != aws_oracle_size:
        raise Exception(
            f"Oracle ZIP mismatch → Azure={azure_oracle_size} vs AWS={aws_oracle_size}"
        )

    log(f"✅ Validation successful for {oracle_filename}, Size={aws_oracle_size} bytes")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python monitor_lambda.py <env>")
        sys.exit(1)

    env = sys.argv[1]
    try:
        validate_file_transfer(env)
    except Exception as e:
        log(f"❌ Validation failed: {e}")
        sys.exit(1)
