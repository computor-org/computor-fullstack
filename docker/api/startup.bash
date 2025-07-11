#!/bin/bash

# Set working directory
cd /home/uvicorn

# Run Alembic migrations  
cd src/ctutor_backend && alembic upgrade head

cd /home/uvicorn

# Initialize system data (roles, admin user, etc.)
python src/ctutor_backend/scripts/initialize_system_data.py

# Start the server
cd src && python server.py