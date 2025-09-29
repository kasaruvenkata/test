import boto3
from azure.storage.blob import ContainerClient
import os
import logging

# Setup logging to file and console
log_file = "sync_log.txt"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

# Environment variables
AZURE_CONN_STR = os.getenv("AZURE_CONN_STR")
AZURE_CONTAINER = os.getenv("AZURE_CONTAINER")
S3_BUCKET = os.getenv("S3_BUCKET")
MODE = os.getenv("MODE", "daily")  # 'daily' or 'weekly'

def get_azure_blobs():
    container = ContainerClient.from_connection_string(AZURE_CONN_STR, AZURE_CONTAINER)
    blobs = container.list_blobs()
    return {blob.name: blob.size for blob in blobs}

def get_s3_objects():
    s3 = boto3.client('s3')
    response = s3.list_objects_v2(Bucket=S3_BUCKET)
    if 'Contents' not in response:
        return {}
    return {obj['Key']: obj['Size'] for obj in response['Contents']}

def compare_blobs(azure_blobs, s3_objects):
    mismatches = []
    for name, size in azure_blobs.items():
        if name not in s3_objects:
            mismatches.append(f"❌ Missing in S3: {name}")
        elif s3_objects[name] != size:
            mismatches.append(f"⚠️ Size mismatch for {name}: Azure={size}, S3={s3_objects[name]}")
    return mismatches

def main():
    logging.info(f"🔍 Starting {MODE.upper()} sync validation...")
    azure_blobs = get_azure_blobs()
    s3_objects = get_s3_objects()
    mismatches = compare_blobs(azure_blobs, s3_objects)

    if mismatches:
        logging.warning(f"{len(mismatches)} mismatches found:")
        for m in mismatches:
            logging.warning(m)
    else:
        logging.info("✅ All files match between Azure and S3.")

# Lambda-compatible entry point
def lambda_handler(event, context):
    main()
