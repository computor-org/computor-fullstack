FROM python:3.10-slim

# Install system dependencies including MATLAB runtime dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    git \
    wget \
    unzip \
    libx11-6 \
    libxext6 \
    libxrender1 \
    libxtst6 \
    libxi6 \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -ms /bin/bash worker
WORKDIR /home/worker

# Switch to worker user early
USER worker

# Install Python dependencies
COPY --chown=worker:worker src/requirements.txt /home/worker/requirements.txt
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Install MATLAB Engine API for Python if needed
# RUN pip install matlabengine

# The source code will be mounted as a volume
WORKDIR /home/worker/src

# Start temporal worker with testing-matlab queue
CMD ["python", "-m", "ctutor_backend.tasks.temporal_worker", "--queues=testing-matlab"]