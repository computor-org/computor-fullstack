FROM python:3.10-slim

RUN apt-get update && apt-get install -y postgresql-client git

RUN useradd -ms /bin/bash uvicorn
WORKDIR /home/uvicorn

# Copy source code and installation files as root, then change ownership
ADD src /home/uvicorn/src
ADD migrations.sh /home/uvicorn/migrations.sh
ADD docker/api/startup.bash startup.bash

# Change ownership of files to uvicorn user
RUN chown -R uvicorn:uvicorn /home/uvicorn

# Switch to uvicorn user
USER uvicorn

# Install dependencies first
RUN pip install --no-cache-dir --upgrade -r src/requirements.txt

# Install the package in editable mode so CLI commands work
RUN cd src && pip install -e .