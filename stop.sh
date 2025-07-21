#!/bin/bash

# Stop on error
set -e

# Export env vars from .env
set -a
source .env
set +a

ENVIRONMENT=${1:-dev}

DOCKERCFILE="docker-compose-${ENVIRONMENT}.yaml"

echo "[Stopping Computor Server]"

docker-compose -f $DOCKERCFILE down