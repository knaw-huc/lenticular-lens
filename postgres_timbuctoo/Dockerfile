FROM postgres:10.6

RUN apt-get update && apt-get install -y \
    python3-pip \
    postgresql-10-python3-multicorn \
    postgresql-plpython3-10

RUN echo listen_addresses='0.0.0.0' >> /usr/lib/tmpfiles.d/postgresql.conf

RUN pip3 install requests

ENV PYTHONPATH "/app"
COPY src /app

COPY src/setup.sql /docker-entrypoint-initdb.d
