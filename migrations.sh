#!/bin/bash

set -a
source .env
set +a

echo "Applying Alembic migrations..."
cd src
export PYTHONPATH=$PWD:$PYTHONPATH
cd ctutor_backend && alembic upgrade head