# Build argument for base image - defaults to local build, can be overridden
ARG MATLAB_BASE_IMAGE=matlab-base:latest

# Use the MATLAB base image (can be overridden via --build-arg)
FROM ${MATLAB_BASE_IMAGE}

USER root

# Install Python and system dependencies
RUN export DEBIAN_FRONTEND=noninteractive \
    && apt-get update \
    && apt-get install --no-install-recommends --yes \
        python3.10 \
        python3-pip \
        python3.10-venv \
        postgresql-client \
        git \
    && apt-get clean \
    && apt-get autoremove \
    && rm -rf /var/lib/apt/lists/*

# Create worker user if it doesn't exist (matlab image already has matlab user)
RUN useradd -ms /bin/bash worker || true

# Set up Python environment
WORKDIR /home/worker

# Copy and install Python requirements as root
COPY src/requirements.txt /home/worker/requirements.txt
RUN python3.10 -m pip install --no-cache-dir --upgrade pip \
    && python3.10 -m pip install --no-cache-dir --upgrade -r requirements.txt

# Install MATLAB Engine API for Python if available
# This will fail silently if MATLAB is not properly configured
RUN python3.10 -m pip install matlabengine || true

# Copy source code will be mounted as volume in docker-compose
WORKDIR /home/worker/src

# Switch to worker user for execution
USER worker

# Ensure python3.10 is used
ENV PYTHON_EXECUTABLE=/usr/bin/python3.10

# Start temporal worker with testing-matlab queue
CMD ["/usr/bin/python3.10", "-m", "ctutor_backend.tasks.temporal_worker", "--queues=testing-matlab"]