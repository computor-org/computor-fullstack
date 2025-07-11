#!/bin/bash

# Stop on error
set -e

# Export env vars from .env
set -a
source .env
set +a

ENVIRONMENT=${1:-dev}

DOCKERFILE="docker-compose-${ENVIRONMENT}.yaml"

destination="${SYSTEM_DEPLOYMENT_PATH}/execution-backend/shared"

directories=(
    "documents"
    "courses"
    "course-contents"
    "defaults"
    "repositories"
)

for dir in "${directories[@]}"; do

    full_path="${destination}/${dir}"

    if [ ! -d "$full_path" ]; then
        echo "Create Directory: $full_path"
        mkdir -p "$full_path"
    fi
done

cp -r src/defaults "${SYSTEM_DEPLOYMENT_PATH}/execution-backend/shared"

echo "[Starting ${SYSTEM_TITLE} Server]"

docker-compose -f $DOCKERCFILE up --build