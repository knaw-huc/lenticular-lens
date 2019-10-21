FROM postgres:11

RUN apt-get update && apt-get install -y \
    python3-pip \
    postgresql-plpython3-11

RUN echo listen_addresses='0.0.0.0' >> /usr/lib/tmpfiles.d/postgresql.conf

COPY ./postgresql/ /app/

RUN pip3 install --trusted-host pypi.python.org -r /app/requirements.txt

ENV PYTHONPATH /app

COPY ./postgresql/setup.sql /docker-entrypoint-initdb.d