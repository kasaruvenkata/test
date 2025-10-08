# Infra/modules/lambda/MonitorLambda/Dockerfile

# Use AWS Lambda base image for Python 3.9
FROM public.ecr.aws/lambda/python:3.9

# Install requirements
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy function
COPY lambda_monitor.py ${LAMBDA_TASK_ROOT}/

# Lambda entrypoint
CMD ["lambda_monitor.lambda_handler"]
