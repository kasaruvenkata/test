import boto3
import os
import logging
from azure.storage.blob import BlobServiceClient
from botocore.exceptions import ClientError

# Setup logging
log_file = "sync_log.txt"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

# ENV
SECRET_NAME = "azneprod"
AZURE_CONTAINER = os.getenv("AZURE_CONTAINER")
S3_BUCKET = os.getenv("S3_BUCKET")
MODE = os.getenv("MODE", "daily")

secrets_client = boto3.client("secretsmanager")
s3_client = boto3.client("s3")

def get_secret():
    try:
        response = secrets_client.get_secret_value(SecretId=SECRET_NAME)
        return eval(response["SecretString"])
    except ClientError as e:
        logging.error(f"Error retrieving secret: {e}")
        raise

def get_azure_blobs(connection_string):
    blob_service_client = BlobServiceClient.from_connection_string(conn_str=connection_string)
    container_client = blob_service_client.get_container_client(AZURE_CONTAINER)
    blobs = container_client.list_blobs()
    return {blob.name: blob.size for blob in blobs}

def get_s3_objects():
    response = s3_client.list_objects_v2(Bucket=S3_BUCKET)
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
    secret = get_secret()
    connection_string = secret["connection_string"]

    azure_blobs = get_azure_blobs(connection_string)
    s3_objects = get_s3_objects()
    mismatches = compare_blobs(azure_blobs, s3_objects)

    if mismatches:
        logging.warning(f"{len(mismatches)} mismatches found:")
        for m in mismatches:
            logging.warning(m)
    else:
        logging.info("✅ All files match between Azure and S3.")

def lambda_handler(event, context):
    main()

if __name__ == "__main__":
    lambda_handler({}, {})
