# Task Worker Dockerfile
# Based on the API Dockerfile but optimized for worker processes

FROM prefecthq/prefect:2.20.3-python3.10

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd -ms /bin/bash taskworker
USER taskworker
WORKDIR /home/taskworker

# Copy source code and requirements
ADD src /home/taskworker/src
ADD docker/task-worker/startup.bash /home/taskworker/startup.bash

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade -r src/requirements.txt

# Make startup script executable
USER root
RUN chmod +x /home/taskworker/startup.bash
USER taskworker

# Set default environment variables
ENV PYTHONPATH=/home/taskworker/src
ENV TASK_QUEUES=high_priority,default,low_priority

# Health check to ensure worker is running
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import redis; r = redis.Redis.from_url('${REDIS_URL}', password='${REDIS_PASSWORD}'); r.ping()" || exit 1

# Default command
CMD ["./startup.bash"]