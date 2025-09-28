FROM public.ecr.aws/lambda/python:3.11

RUN yum install -y gcc libffi-devel openssl-devel python3-devel rust cargo

COPY requirements.txt .
RUN pip3 install --upgrade pip && pip3 install -r requirements.txt

COPY monitor_lambda.py .

CMD ["monitor_lambda.main"]
