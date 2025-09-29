# Base image for Python 3.11 Lambda container
FROM public.ecr.aws/lambda/python:3.11

# Install system packages required by cryptography + azure-identity
RUN yum install -y gcc libffi-devel openssl-devel python3-devel rust cargo

ARG S3_BUCKET
ENV S3_BUCKET=${S3_BUCKET}

# Copy function code and dependencies
COPY requirements.txt .
RUN pip3 install --upgrade pip && pip3 install -r requirements.txt

COPY monitor_lambda.py .

# Command to run the Lambda function
CMD ["monitor_lambda.lambda_handler"]
