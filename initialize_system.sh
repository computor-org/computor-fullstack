#!/bin/bash

set -a
source .env.dev
set +a

echo "Initializing system data..."
cd src/ctutor_backend && python scripts/initialize_system_data.py