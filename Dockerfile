FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY pyproject.toml ./
COPY iris_runtime ./iris_runtime
RUN pip install --no-cache-dir .
COPY fixtures ./fixtures
CMD ["iris-worker"]
