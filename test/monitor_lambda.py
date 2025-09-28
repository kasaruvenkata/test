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
S3_BUCKET_UAT = os.getenv("S3_UAT_BUCKET", "aabackstop-uat")
S3_BUCKET_PROD = os.getenv("S3_PROD_BUCKET", "aabackstop-prod")
AZURE_CONTAINER_UAT = os.getenv("AZURE_CONTAINER_UAT", "uat")
AZURE_CONTAINER_PROD = os.getenv("AZURE_CONTAINER_PROD", "prod")
EMAIL_TO = os.getenv("EMAIL_TO", "venkata.kasaru@theaa.com")
AWS_REGION = os.getenv("AWS_REGION", "eu-west-1")
MODE = os.getenv("MODE", "daily")  # daily / weekly

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
    """Send email using AWS SES or SMTP"""
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_TO
    msg["To"] = EMAIL_TO

    try:
        # Using local SMTP; replace with SES if needed
        with smtplib.SMTP("localhost") as server:
            server.sendmail(EMAIL_TO, [EMAIL_TO], msg.as_string())
        print(f"Email sent to {EMAIL_TO}")
    except Exception as e:
        print(f"❌ Error sending email: {e}")

# ========================
# Monitor Functions
# ========================

def validate_daily(blob_service_client):
    """Validate files for today exist and have size > 0"""
    today = datetime.utcnow().strftime("%Y%m%d")
    expected_patterns = [
        f"indoor_users_{today}_",  # TXT file prefix
        f"Oracle/AABS-{datetime.utcnow().strftime('%Y-%m-%d')}.zip",
    ]
    missing_files = []

    containers = {
        "uat": AZURE_CONTAINER_UAT,
        "prod": AZURE_CONTAINER_PROD
    }
    buckets = {
        "uat": S3_BUCKET_UAT,
        "prod": S3_BUCKET_PROD
    }

    for env, container_name in containers.items():
        container_client = blob_service_client.get_container_client(container_name)
        s3_bucket = buckets[env]

        # Azure blobs
        blobs = {b.name: b.size for b in container_client.list_blobs()}
        # S3 objects
        resp = s3_client.list_objects_v2(Bucket=s3_bucket)
        s3_objs = {o["Key"]: o["Size"] for o in resp.get("Contents", [])}

        for pattern in expected_patterns:
            azure_match = [name for name in blobs if name.startswith(pattern)]
            if not azure_match:
                missing_files.append(f"Azure {env} missing {pattern}")
            else:
                for name in azure_match:
                    if blobs[name] == 0:
                        missing_files.append(f"Azure {env} {name} has size 0")

            s3_match = [key for key in s3_objs if key.startswith(pattern)]
            if not s3_match:
                missing_files.append(f"S3 {env} missing {pattern}")
            else:
                for key in s3_match:
                    if s3_objs[key] == 0:
                        missing_files.append(f"S3 {env} {key} has size 0")

    if missing_files:
        print("❌ Missing or empty files detected:")
        for mf in missing_files:
            print("   -", mf)
        send_email("❌ Daily File Transfer Validation Failed", "\n".join(missing_files))
        sys.exit(1)
    else:
        print("✅ All expected files exist and have valid size for today.")

def generate_weekly_report(blob_service_client):
    """Generate summary report of files in Azure and S3 for last 7 days"""
    report_lines = []
    containers = {
        "uat": AZURE_CONTAINER_UAT,
        "prod": AZURE_CONTAINER_PROD
    }
    buckets = {
        "uat": S3_BUCKET_UAT,
        "prod": S3_BUCKET_PROD
    }

    for env, container_name in containers.items():
        container_client = blob_service_client.get_container_client(container_name)
        s3_bucket = buckets[env]

        report_lines.append(f"--- {env.upper()} ---")
        report_lines.append("Azure Blob:")
        for blob in container_client.list_blobs():
            report_lines.append(f"  {blob.name} ({blob.size} bytes)")

        report_lines.append("S3:")
        resp = s3_client.list_objects_v2(Bucket=s3_bucket)
        for obj in resp.get("Contents", []):
            report_lines.append(f"  {obj['Key']} ({obj['Size']} bytes)")
        report_lines.append("")

    body = "\n".join(report_lines)
    send_email("✅ Weekly File Transfer Summary", body)
    print("Weekly report generated and emailed.")

# ========================
# Main Lambda Handler
# ========================

def lambda_handler(event=None, context=None):
    secret = get_secret()
    connection_string = secret["connection_string"]

    blob_service_client = BlobServiceClient.from_connection_string(conn_str=connection_string)

    if MODE.lower() == "daily":
        validate_daily(blob_service_client)
    elif MODE.lower() == "weekly":
        generate_weekly_report(blob_service_client)
    else:
        print(f"❌ Unknown MODE: {MODE}")
        sys.exit(1)

if __name__ == "__main__":
    lambda_handler()
