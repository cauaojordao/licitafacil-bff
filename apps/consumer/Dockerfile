FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy libs
COPY libs/ /app/libs/

# Copy consumer app
COPY apps/consumer/ /app/apps/consumer/

# Install dependencies
RUN pip install --no-cache-dir -e /app/libs/common
RUN pip install --no-cache-dir -e /app/libs/clients
RUN pip install --no-cache-dir -e /app/apps/consumer

# Set environment
ENV PYTHONUNBUFFERED=1

# Run consumer
CMD ["consumer"]
