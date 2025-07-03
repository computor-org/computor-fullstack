#!/bin/bash

set -e

echo "Applying Alembic migrations..."
cd src/ctutor_backend && alembic upgrade head