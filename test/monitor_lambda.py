trigger:
  branches:
    include:
      - monitor

# schedule:
# - cron: "0 7 * * *"  # Daily 7 AM UTC (commented for now)

pool:
  vmImage: ubuntu-latest

variables:
  S3_UAT_BUCKET: "aabackstop-uat"
  S3_PROD_BUCKET: "aabackstop-prod"
  AZURE_CONTAINER_UAT: "uat"
  AZURE_CONTAINER_PROD: "prod"
  EMAIL_TO: "venkata.kasaru@theaa.com"
  SECRET_NAME: "azneprod"
  AWS_REGION: "eu-west-1"
  MODE: "daily"

steps:
- task: DockerInstaller@0
  displayName: 'Install Docker'

- task: Docker@2
  displayName: 'Monitor Lambda - Build Docker Image'
  inputs:
    command: build
    repository: 'aa-monitorlambda'
    Dockerfile: 'modules/lambda/MonitorLambda/Dockerfile'
    buildContext: 'modules/lambda/MonitorLambda'
    tags: |
      $(Build.BuildId)
    arguments: |
      --build-arg S3_BUCKET=aabackstop-$(parameters.environment)

- task: ECRPushImage@1
  displayName: 'Monitor Lambda - Push image to ECR'
  inputs:
    awsCredentials: 'AWS-ECR-$(parameters.environment)'
    regionName: 'eu-west-1'
    imageSource: 'imagename'
    sourceImageName: 'aa-monitorlambda'
    sourceImageTag: '$(Build.BuildId)'
    repositoryName: 'aa-monitorlambda-ecr'
    pushTag: 'monitorlambda'

- script: |
    pip install -r modules/lambda/MonitorLambda/requirements.txt
    python modules/lambda/MonitorLambda/monitor_lambda.py
  displayName: "Run Daily Monitor"

- task: SendEmail@1
  condition: failed()
  inputs:
    To: "$(EMAIL_TO)"
    Subject: "❌ Daily File Transfer Validation Failed"
    Body: |
      One or more expected files are missing or have size 0 in Azure Blob or S3.
      Please check the pipeline logs for details.
