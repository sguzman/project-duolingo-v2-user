FROM python:3.9.2

RUN mkdir /app
WORKDIR /app

ADD main.py /app/main.py
ADD http_pb2.py /app/http_pb2.py
ADD http_pb2_grpc.py /app/http_pb2_grpc.py

ADD requirements.txt /app/requirements.txt

RUN pip install -r requirements.txt

ENTRYPOINT ["python", "main.py"]
