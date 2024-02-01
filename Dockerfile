FROM python:3.13.0a3-slim AS worker

ENV PYTHONPATH /app
ENV PYTHONUNBUFFERED 1

COPY ./requirements.txt /app/requirements.txt
RUN pip install --trusted-host pypi.python.org -r /app/requirements.txt

COPY ./src /app

CMD ["python", "/app/worker.py"]

FROM worker AS web

EXPOSE 8000

CMD ["gunicorn", "-k", "eventlet", "-b", ":8000", "-t", "60", "-w", "1", "web:app"]
