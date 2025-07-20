# Unified Celery Worker Dockerfile
# Supports different worker types via WORKER_TYPE environment variable

FROM python:3.10-slim

# Build arguments for git configuration
ARG SYSTEM_GIT_NAME="ComputingTutor API"
ARG SYSTEM_GIT_EMAIL="noreply@domain.com"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    gcc \
    g++ \
    make \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -ms /bin/bash celery
USER celery
WORKDIR /home/celery

# Copy requirements and install Python dependencies
COPY --chown=celery:celery src/requirements.txt /home/celery/requirements.txt
RUN pip install --user --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=celery:celery src/ctutor_backend /home/celery/ctutor_backend

# Configure git (for system worker tasks)
RUN git config --global user.email "${SYSTEM_GIT_EMAIL}" && \
    git config --global user.name "${SYSTEM_GIT_NAME}"

# Environment variables for worker configuration
ENV WORKER_TYPE=system
ENV WORKER_QUEUES=high_priority,default,low_priority
ENV WORKER_CONCURRENCY=4
ENV WORKER_LOG_LEVEL=info
ENV PYTHONPATH=/home/celery

# Default command - can be overridden in docker-compose
CMD ["sh", "-c", "python -m celery -A ctutor_backend.tasks.celery_app worker \
    --queues=${WORKER_QUEUES} \
    --loglevel=${WORKER_LOG_LEVEL} \
    --concurrency=${WORKER_CONCURRENCY}"]