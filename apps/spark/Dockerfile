FROM openjdk:11-jdk-slim

WORKDIR /app

# Install Python 3.11
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3-pip \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy libs
COPY libs/ /app/libs/

# Copy spark app
COPY apps/spark/ /app/apps/spark/

# Install dependencies
RUN pip install --no-cache-dir -e /app/libs/common
RUN pip install --no-cache-dir -e /app/libs/clients
RUN pip install --no-cache-dir -e /app/apps/spark

# Set environment
ENV PYTHONUNBUFFERED=1
ENV JAVA_HOME=/usr/local/openjdk-11

# Run spark job
CMD ["spark-streaming"]
