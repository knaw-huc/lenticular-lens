FROM python:3.9-slim AS worker

ENV PYTHONPATH /app
ENV PYTHONUNBUFFERED 1

COPY ./requirements.txt /app/requirements.txt
RUN pip install --trusted-host pypi.python.org -r /app/requirements.txt

COPY ./src /app

CMD ["python", "/app/worker.py"]

FROM worker AS web

ENV FLASK_APP=/app/web_server/app.py
ENV FLASK_ENV=production

EXPOSE 8000

CMD ["gunicorn", "-b", ":8000", "-t", "60", "-w", "4", "web:app"]
