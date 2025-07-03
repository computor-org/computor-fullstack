#!/bin/bash

set -a
source .env.dev
set +a

echo "Applying Alembic migrations..."
cd src/ctutor_backend && alembic upgrade head