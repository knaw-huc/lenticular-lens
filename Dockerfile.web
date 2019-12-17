FROM node:alpine AS builder

COPY ./vue_app /vue_app
WORKDIR /vue_app

RUN npm install
RUN npm run build

FROM python:3.7-slim

ENV PYTHONPATH /app
ENV PYTHONUNBUFFERED 1

RUN apt-get update && apt-get install -y procps locales

RUN echo "en_US.UTF-8 UTF-8" >> /etc/locale.gen &&\
  echo "de_DE.UTF-8 UTF-8" >> /etc/locale.gen &&\
  locale-gen

COPY ./requirements.txt /app/requirements.txt

RUN pip install --trusted-host pypi.python.org -r /app/requirements.txt

ENV LC_ALL de_DE.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US.UTF-8

COPY ./src /app
COPY --from=builder /src/static/core /app/static/core

ENV FLASK_APP=/app/web_server/app.py
ENV FLASK_ENV=production

CMD ["gunicorn", "-b", ":8000", "-t", "60", "web:app"]
