FROM python:3.12-slim AS worker

ENV PYTHONPATH /app
ENV PYTHONUNBUFFERED 1

RUN pip3 install poetry

WORKDIR /app
COPY pyproject.toml /app

RUN poetry config virtualenvs.create false && \
    poetry install

COPY lenticularlens /app/lenticularlens

CMD ["python", "/app/lenticularlens/run_worker.py"]

FROM worker AS web

ENV WEB_CONCURRENCY 1

EXPOSE 8000

CMD ["python", "/app/lenticularlens/run_web.py"]
