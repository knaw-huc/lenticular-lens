FROM python:3.7-slim

ENV PYTHONPATH /common
ENV PYTHONUNBUFFERED 1

COPY ./requirements.txt /app/requirements.txt
RUN pip install --trusted-host pypi.python.org -r /app/requirements.txt

COPY src /app
COPY vue_app/dist /web