azne-subn-roanon-t-chicane-dev-2 - subnet
monitor_daily.yml – Daily File Validation


Reports missing files in Azure or S3.

Reports zero-size files (files copied but empty).

Email body includes all mismatches, not just a single alert.

Fully parameterized by environment (ENV=uat/prod) for pipeline selection.



Purpose
✅ Key Features

Environment parameter (ENV)

You can choose UAT or PROD at pipeline trigger time.

Lambda uses this to select correct S3 bucket and Azure container.

Daily Validation

Checks both existence and file size.

Reports all missing or zero-size files in the email.

Email Alerts

Only sent if validation fails (condition: failed()).

Recipient: venkata.kasaru@theaa.com.

Reusability

Same Docker image can be used for multiple environments.

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
