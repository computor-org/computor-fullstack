FROM python:3.10-slim

RUN apt-get update && apt-get install -y postgresql-client git

RUN useradd -ms /bin/bash worker
WORKDIR /home/worker

# Switch to worker user early
USER worker

# Install dependencies first (this will be cached if requirements.txt doesn't change)
COPY --chown=worker:worker src/requirements.txt /home/worker/requirements.txt
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# The source code will be mounted as a volume for hot reload
# We'll add the source to PYTHONPATH instead of using editable install
WORKDIR /home/worker/src

# Start temporal worker with testing-python queue
CMD ["python", "-m", "ctutor_backend.tasks.temporal_worker", "--queues=testing-python"]