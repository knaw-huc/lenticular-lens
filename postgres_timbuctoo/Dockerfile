FROM postgres:10.5

RUN apt-get update && apt-get install -y python3-pip
RUN pip3 install requests
RUN apt-get install -y postgresql-10-python3-multicorn
RUN apt-get install -y postgresql-plpython3-10

ENV PYTHONPATH "/app"
COPY src /app

COPY src/setup.sql /docker-entrypoint-initdb.d
