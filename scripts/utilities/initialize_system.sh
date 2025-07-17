#!/bin/bash

set -a
source .env
set +a

echo "Initializing system data..."
cd src/ctutor_backend && python scripts/initialize_system_data.py