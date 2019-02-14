FROM postgres:11.1

RUN apt-get update && apt-get install -y \
    python3-pip \
    postgresql-plpython3-11

RUN echo listen_addresses='0.0.0.0' >> /usr/lib/tmpfiles.d/postgresql.conf

RUN pip3 install requests

ENV PYTHONPATH "/app"
COPY src /app

COPY src/setup.sql /docker-entrypoint-initdb.d
