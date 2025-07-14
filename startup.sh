#!/bin/bash

# Stop on error
set -e

# Export env vars from .env
set -a
source .env
set +a

ENVIRONMENT=${1:-dev}

DOCKERCFILE="docker-compose-${ENVIRONMENT}.yaml"

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

# Create Keycloak directories if they don't exist
keycloak_imports="${SYSTEM_DEPLOYMENT_PATH}/keycloak/imports"
keycloak_themes="${SYSTEM_DEPLOYMENT_PATH}/keycloak/themes"

if [ ! -d "$keycloak_imports" ]; then
    echo "Create Directory: $keycloak_imports"
    mkdir -p "$keycloak_imports"
fi

if [ ! -d "$keycloak_themes" ]; then
    echo "Create Directory: $keycloak_themes"
    mkdir -p "$keycloak_themes"
fi

# Copy Keycloak realm configuration if it exists
if [ -f "data/keycloak/computor-realm.json" ]; then
    echo "Copying Keycloak realm configuration..."
    cp data/keycloak/computor-realm.json "$keycloak_imports/"
fi

echo "[Starting ${SYSTEM_TITLE} Server]"

docker-compose -f $DOCKERCFILE up --build