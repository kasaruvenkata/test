import os
import sys
import boto3
from azure.storage.blob import BlobServiceClient
from botocore.exceptions import ClientError
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText

# ========================
# ENV / CONFIG
# ========================
SECRET_NAME = os.getenv("SECRET_NAME", "azneprod")
ENV = os.getenv("ENV", "uat")  # Parameterized: uat or prod
AWS_REGION = os.getenv("AWS_REGION", "eu-west-1")
EMAIL_TO = os.getenv("EMAIL_TO", "venkata.kasaru@theaa.com")
MODE = os.getenv("MODE", "daily")  # daily / weekly

# Map environment to S3 bucket and Azure container
ENV_MAP = {
    "uat": {"S3_BUCKET": "aabackstop-uat", "AZURE_CONTAINER": "uat"},
    "prod": {"S3_BUCKET": "aabackstop-prod", "AZURE_CONTAINER": "prod"},
}

S3_BUCKET = ENV_MAP[ENV]["S3_BUCKET"]
AZURE_CONTAINER = ENV_MAP[ENV]["AZURE_CONTAINER"]

# ========================
# AWS Clients
# ========================
secrets_client = boto3.client("secretsmanager", region_name=AWS_REGION)
s3_client = boto3.client("s3", region_name=AWS_REGION)

# ========================
# Helper Functions
# ========================
def get_secret():
    """Fetch Azure connection string from AWS Secrets Manager"""
    try:
        response = secrets_client.get_secret_value(SecretId=SECRET_NAME)
        return eval(response["SecretString"])
    except ClientError as e:
        print(f"Error retrieving secret: {e}")
        raise

def send_email(subject, body):
    """Send email using SMTP or AWS SES"""
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_TO
    msg["To"] = EMAIL_TO

    try:
        with smtplib.SMTP("localhost") as server:
            server.sendmail(EMAIL_TO, [EMAIL_TO], msg.as_string())
        print(f"Email sent to {EMAIL_TO}")
    except Exception as e:
        print(f"❌ Error sending email: {e}")

# ========================
# Monitor Functions
# ========================
def validate_daily(blob_service_client):
    """Validate files exist and size > 0, report missing or incorrect files"""
    today = datetime.utcnow().strftime("%Y%m%d")
    expected_patterns = [
        f"indoor_users_{today}_",  # TXT file prefix
        f"Oracle/AABS-{datetime.utcnow().strftime('%Y-%m-%d')}.zip",
    ]

    container_client = blob_service_client.get_container_client(AZURE_CONTAINER)

    # Azure blobs
    azure_blobs = {b.name: b.size for b in container_client.list_blobs()}
    # S3 objects
    resp = s3_client.list_objects_v2(Bucket=S3_BUCKET)
    s3_objs = {o["Key"]: o["Size"] for o in resp.get("Contents", [])}

    report_lines = []

    for pattern in expected_patterns:
        # Check Azure
        azure_match = [name for name in azure_blobs if name.startswith(pattern)]
        if not azure_match:
            report_lines.append(f"Missing in Azure: {pattern}")
        else:
            for name in azure_match:
                if azure_blobs[name] == 0:
                    report_lines.append(f"Zero-size in Azure: {name}")

        # Check S3
        s3_match = [key for key in s3_objs if key.startswith(pattern)]
        if not s3_match:
            report_lines.append(f"Missing in S3: {pattern}")
        else:
            for key in s3_match:
                if s3_objs[key] == 0:
                    report_lines.append(f"Zero-size in S3: {key}")

    if report_lines:
        body = f"Daily File Transfer Validation Report - Environment: {ENV.upper()}\n\n" + "\n".join(report_lines)
        print("❌ Validation issues found:")
        for line in report_lines:
            print("   -", line)
        send_email(f"❌ Daily File Validation Failed - {ENV.upper()}", body)
        sys.exit(1)
    else:
        print(f"✅ All expected files exist and have valid size for today ({ENV.upper()})")

# ========================
# Main Lambda Handler
# ========================
def lambda_handler(event=None, context=None):
    secret = get_secret()
    connection_string = secret["connection_string"]
    blob_service_client = BlobServiceClient.from_connection_string(conn_str=connection_string)

    if MODE.lower() == "daily":
        validate_daily(blob_service_client)
    else:
        print(f"❌ Unsupported MODE: {MODE}")
        sys.exit(1)

if __name__ == "__main__":
    lambda_handler()
