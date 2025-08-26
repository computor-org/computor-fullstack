# Build argument for base image - defaults to local build, can be overridden
# ARG MATLAB_BASE_IMAGE=matlab-base:latest

# # Use the MATLAB base image (can be overridden via --build-arg)
# FROM ${MATLAB_BASE_IMAGE}

FROM registry.gitlab.tugraz.at/codeability/testing-frameworks/itp-matlab-testing/matlab:r2024b

USER root

# Install Python and system dependencies
RUN export DEBIAN_FRONTEND=noninteractive \
    && apt-get update \
    && apt-get install --no-install-recommends --yes \
        python3.10 \
        python3-pip \
        python3.10-venv \
        libpython3.10-dev \
        git \
        nano \
        curl \
    && apt-get clean \
    && apt-get autoremove \
    && rm -rf /var/lib/apt/lists/*

RUN cd /opt/matlab/R2024b/extern/engines/python && python setup.py install

ADD docker/temporal-worker-matlab/requirements.txt /home/matlab/requirements_mat.txt
ADD src /home/matlab/

RUN pip install --no-cache-dir --upgrade -r requirements_mat.txt
RUN pip install -e .

RUN chmod -R 777 /home/matlab

RUN rm /etc/sudoers.d/localsudo
RUN passwd -d matlab

USER matlab
WORKDIR /home/matlab

ENV TZ=UTC
ENV TZ=Europe/Berlin

# Ensure python3.10 is used
ENV PYTHON_EXECUTABLE=/usr/bin/python3.10

# Default entrypoint - can be overridden in docker-compose
ENTRYPOINT ["python", "-m", "ctutor_backend.tasks.temporal_worker"]