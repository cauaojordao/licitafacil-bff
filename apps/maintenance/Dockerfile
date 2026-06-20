FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y openjdk-17-jdk curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
COPY apps/ingestion/pyproject.toml apps/ingestion/pyproject.toml
COPY apps/processor/pyproject.toml apps/processor/pyproject.toml
COPY apps/maintenance/pyproject.toml apps/maintenance/pyproject.toml

RUN pip install --no-cache-dir prefect pyspark pymongo kafka-python python-dotenv requests supabase google-generativeai

COPY . .

ENV PYTHONPATH=/app