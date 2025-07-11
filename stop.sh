#!/bin/bash

# Stop on error
set -e

# Export env vars from .env
set -a
source .env
set +a

ENVIRONMENT=${1:-dev}

DOCKERFILE="docker-compose-${ENVIRONMENT}.yaml"

echo "[Stopping ${SYSTEM_TITLE} Server]"

docker-compose -f $DOCKERCFILE down