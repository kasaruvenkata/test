Infra/modules/lambda/MonitorLambda/Dockerfile

FROM public.ecr.aws/lambda/python:3.9

# Install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy function code
COPY lambda_monitor.py ${LAMBDA_TASK_ROOT}/

# Handler
CMD ["lambda_monitor.lambda_handler"]
