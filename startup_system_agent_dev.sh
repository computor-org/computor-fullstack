#!/bin/bash

# Stop on error
set -e

# Export env vars from .env.dev
set -a
source .env.dev
set +a

echo "Starting prefect system agent for development..."

export EXECUTION_BACKEND_API_URL="http://localhost:8000"
export PREFECT_API_URL="http://localhost:4200/api"
export API_LOCAL_STORAGE_DIR="${SYSTEM_DEPLOYMENT_PATH}/execution-backend/shared"

python3 docker/system-agent/flows.py
prefect agent start --pool default-agent-pool --work-queue system-queue