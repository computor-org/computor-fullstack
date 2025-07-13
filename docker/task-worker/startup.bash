#!/bin/bash

# Task Worker Startup Script
# This script initializes the task worker environment and starts the RQ worker

set -e

echo "🚀 Starting Task Worker..."
echo "Queue configuration: ${TASK_QUEUES:-high_priority,default,low_priority}"
echo "Redis URL: ${REDIS_URL}"
echo "API URL: ${EXECUTION_BACKEND_API_URL}"

# Wait for Redis to be available
echo "⏳ Waiting for Redis connection..."
while ! python -c "
import redis
import os
import sys
try:
    r = redis.Redis.from_url(os.environ.get('REDIS_URL', 'redis://localhost:6379'), password=os.environ.get('REDIS_PASSWORD'))
    r.ping()
    print('✅ Redis connection successful')
    sys.exit(0)
except Exception as e:
    print(f'❌ Redis connection failed: {e}')
    sys.exit(1)
"; do
  echo "Waiting for Redis..."
  sleep 2
done

# Wait for API backend to be available
echo "⏳ Waiting for API backend..."
while ! python -c "
import requests
import os
import sys
try:
    url = os.environ.get('EXECUTION_BACKEND_API_URL', 'http://localhost:8000')
    response = requests.get(f'{url}/info', timeout=5)
    if response.status_code == 200:
        print('✅ API backend connection successful')
        sys.exit(0)
    else:
        print(f'❌ API backend returned status {response.status_code}')
        sys.exit(1)
except Exception as e:
    print(f'❌ API backend connection failed: {e}')
    sys.exit(1)
"; do
  echo "Waiting for API backend..."
  sleep 5
done

# Import task modules to ensure registration
echo "📦 Importing task modules..."
python -c "
from ctutor_backend.tasks import task_registry
from ctutor_backend.tasks.examples import *
from ctutor_backend.tasks.student_testing import *
tasks = task_registry.list_tasks()
print(f'✅ Registered {len(tasks)} task types: {list(tasks.keys())}')
"

# Start the worker with the specified queues
echo "🏃 Starting RQ worker..."
echo "Command: python -m ctutor_backend.cli.cli worker start --queues=${TASK_QUEUES:-high_priority,default,low_priority}"

exec python -m ctutor_backend.cli.cli worker start --queues="${TASK_QUEUES:-high_priority,default,low_priority}"