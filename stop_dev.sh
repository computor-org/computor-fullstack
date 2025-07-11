#!/bin/bash

# Stop on error
set -e

# Export env vars from .env.dev
set -a
source .env.dev
set +a

DOCKERCFILE="docker-compose-dev.yaml"

echo "[Stopping ${SYSTEM_TITLE} Server]"

docker-compose -f $DOCKERCFILE down