FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    MYLAB_HOST=0.0.0.0 \
    MYLAB_PORT=8000

COPY pyproject.toml README.md ./
COPY app ./app
COPY data ./data

RUN pip install .

EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:app --host ${MYLAB_HOST} --port ${MYLAB_PORT}"]
