FROM python:3.9.2

RUN mkdir /app
WORKDIR /app

ADD *.py /app/

ADD requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt

ENTRYPOINT ["python", "main.py"]
