#!/bin/bash
# Script to set up environment file based on mode (dev/prod)

MODE=${1:-dev}

if [ "$MODE" = "dev" ]; then
    echo "Setting up development environment..."
    cat .env.common .env.dev > .env
elif [ "$MODE" = "prod" ]; then
    echo "Setting up production environment..."
    cat .env.common .env.prod > .env
else
    echo "Invalid mode: $MODE"
    echo "Usage: $0 [dev|prod]"
    exit 1
fi

echo "Environment file created successfully!"