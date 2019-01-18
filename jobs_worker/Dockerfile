FROM python:3.7-slim

ENV PYTHONPATH /common
ENV PYTHONUNBUFFERED 1

RUN apt-get update && apt-get install -y procps
COPY ./requirements.txt /app/requirements.txt
RUN pip install --trusted-host pypi.python.org -r /app/requirements.txt

COPY src /app