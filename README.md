monitor_daily.yml – Daily File Validation


Reports missing files in Azure or S3.

Reports zero-size files (files copied but empty).

Email body includes all mismatches, not just a single alert.

Fully parameterized by environment (ENV=uat/prod) for pipeline selection.



Purpose

Validate that all expected files are successfully copied from Azure Blob Storage → AWS S3 for today’s date.

Send an email alert if any file is missing, so the Ops team can investigate immediately.

Pipeline Outline

Trigger

Runs on the monitor branch (manual trigger by default, cron commented).

Environment Variables / Secrets

S3_UAT_BUCKET / S3_PROD_BUCKET → AWS S3 bucket names.

AZURE_CONTAINER_UAT / AZURE_CONTAINER_PROD → Azure Blob container names.

SECRET_NAME → AWS Secrets Manager key storing Azure connection string.

AWS_REGION → Region for AWS operations.

MODE=daily → Tells the Lambda code to perform daily validation.

Build Docker Image

Uses Dockerfile in modules/lambda/MonitorLambda/.

Builds an image with all Python dependencies (boto3, azure-storage-blob).

Push Docker Image to ECR

Tags image as monitorlambda.

Pushes to AWS ECR (separate repos for uat / prod).

Run Daily Monitor (Lambda code inside container)

monitor_lambda.py connects to Azure Blob & S3.

Checks if today’s files exist:

TXT files: indoor_users_YYYYMMDD_*.txt

ZIP files: Oracle/AABS-YYYY-MM-DD.zip

If any file is missing → exits with failure.

===================================================================================================
2️⃣ monitor_weekly.yml – Weekly Summary
Purpose

Generate a summary of all files from the last 7 days in both Azure Blob and AWS S3.

Attach the report to an email, giving confidence that monitoring is working and files are synced correctly over time.

Pipeline Outline

Trigger

Runs on the monitor branch.

Cron schedule commented out (you can configure for weekly runs later).

Environment Variables / Secrets

Same as monitor_daily.yml, except MODE=weekly.

Build Docker Image

Same Dockerfile as daily, containing monitor_lambda.py.

Push Docker Image to ECR

Same as daily, tag as monitorlambda.

Run Weekly Monitor

monitor_lambda.py reads all blobs in Azure and objects in S3 from last 7 days.

Generates a report: weekly_report.txt containing:

--- UAT ---
Azure Blob:
  indoor_users_20250922_*.txt
  Oracle/AABS-2025-09-22.zip
AWS S3:
  indoor_users_20250922_*.txt
  Oracle/AABS-2025-09-22.zip

--- PROD ---
Azure Blob:
  indoor_users_20250922_*.txt
  Oracle/AABS-2025-09-22.zip
AWS S3:
  indoor_users_20250922_*.txt
  Oracle/AABS-2025-09-22.zip


Email Notification

Sends the weekly_report.txt to ROAD_Ops_L2_Support@theaa.com.

Provides visual confirmation of all files in both environments.

Email Notification (Optional)

If the task fails, sends an email to ROAD_Ops_L2_Support@theaa.com.
