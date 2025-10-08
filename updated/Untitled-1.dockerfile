Infra/modules/lambda/MonitorLambda/Dockerfile

FROM public.ecr.aws/lambda/python:3.9

COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY lambda_monitor.py ${LAMBDA_TASK_ROOT}/

CMD ["lambda_monitor.lambda_handler"]
