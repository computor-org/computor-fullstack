FROM prefecthq/prefect:2.20.3-python3.10

RUN apt-get update && apt-get install -y postgresql-client

RUN useradd -ms /bin/bash uvicorn
WORKDIR /home/uvicorn

# Copy source code and installation files as root, then change ownership
ADD src /home/uvicorn/src
ADD scripts/utilities/migrations.sh /home/uvicorn/migrations.sh
ADD docker/api/startup.bash startup.bash

# Change ownership of files to uvicorn user
RUN chown -R uvicorn:uvicorn /home/uvicorn

# Switch to uvicorn user
USER uvicorn

# Install dependencies first
RUN pip install --no-cache-dir --upgrade -r src/requirements.txt

# Install the package in editable mode so CLI commands work
RUN cd src && pip install -e .