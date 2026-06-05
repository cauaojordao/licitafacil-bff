FROM openjdk:11-jdk-slim

WORKDIR /app

# Install Python 3.11
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3-pip \
    gcc \
    cron \
    && rm -rf /var/lib/apt/lists/*

# Copy libs
COPY libs/ /app/libs/

# Copy maintenance app
COPY apps/cronjob/ /app/apps/cronjob/

# Install dependencies
RUN pip install --no-cache-dir -e /app/libs/common
RUN pip install --no-cache-dir -e /app/apps/maintenance

# Set environment
ENV PYTHONUNBUFFERED=1
ENV JAVA_HOME=/usr/local/openjdk-11

# Add crontab file
COPY apps/cronjob/crontab /etc/cron.d/iceberg-maintenance

# Give execution rights
RUN chmod 0644 /etc/cron.d/iceberg-maintenance

# Apply cron job
RUN crontab /etc/cron.d/iceberg-maintenance

# Run cron
CMD ["cron", "-f"]
