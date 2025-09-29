import boto3
import os
from azure.storage.blob import BlobServiceClient
from botocore.exceptions import ClientError

# ENV
SECRET_NAME = "azneprod"   # from AWS Secrets Manager
AZURE_CONTAINER = os.getenv("AZURE_CONTAINER", "uat")
S3_BUCKET = os.getenv("S3_BUCKET")
ALERT_EMAIL = "ROAD_Ops_L2_Support@theaa.com"

secrets_client = boto3.client("secretsmanager")
s3_client = boto3.client("s3")
ses_client = boto3.client("ses", region_name="eu-west-1")

def get_secret():
    try:
        response = secrets_client.get_secret_value(SecretId=SECRET_NAME)
        return eval(response["SecretString"])
    except ClientError as e:
        print(f"❌ Error retrieving secret: {e}")
        raise

def send_email(subject, body):
    try:
        response = ses_client.send_email(
            Source="noreply@theaa.com",  # must be verified in SES
            Destination={"ToAddresses": [ALERT_EMAIL]},
            Message={
                "Subject": {"Data": subject},
                "Body": {"Text": {"Data": body}}
            }
        )
        print(f"📧 Alert email sent: {response['MessageId']}")
    except Exception as e:
        print(f"❌ Error sending email: {e}")

def lambda_handler(event, context):
    secret = get_secret()
    connection_string = secret["connection_string"]

    blob_service_client = BlobServiceClient.from_connection_string(conn_str=connection_string)
    container_client = blob_service_client.get_container_client(AZURE_CONTAINER)

    print(f"🔎 Validating blobs in container '{AZURE_CONTAINER}' against S3 bucket '{S3_BUCKET}'")

    mismatches = []
    for blob in container_client.list_blobs():
        blob_name = blob.name
        blob_size = blob.size
        print(f"Found blob: {blob_name} ({blob_size} bytes)")

        try:
            s3_object = s3_client.head_object(Bucket=S3_BUCKET, Key=blob_name)
            s3_size = s3_object["ContentLength"]

            if s3_size != blob_size:
                mismatches.append(f"❌ Size mismatch: {blob_name} | Blob={blob_size} | S3={s3_size}")
        except ClientError:
            mismatches.append(f"❌ Missing in S3: {blob_name}")

    if mismatches:
        subject = f"[ALERT] File Validation Failed in {S3_BUCKET}"
        body = "\n".join(mismatches)
        send_email(subject, body)
    else:
        print("✅ All files validated successfully. Sizes match.")

if __name__ == "__main__":
    lambda_handler({}, {})
