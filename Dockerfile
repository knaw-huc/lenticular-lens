FROM postgres:10.5

RUN apt-get update && apt-get install -y python3-pip
RUN pip3 install requests
RUN apt-get install -y postgresql-10-python3-multicorn
RUN apt-get install -y postgresql-plpython3-10

COPY src /app
ENV PYTHONPATH "/app"
