#!/bin/bash

# Script to generate JSON Schema for VS Code from Pydantic models

echo "🔧 Generating JSON Schema for meta.yaml files..."

# Navigate to the project root
cd "$(dirname "$0")"

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Run the schema generation script
python src/ctutor_backend/scripts/generate_json_schema.py

if [ $? -eq 0 ]; then
    echo "✅ JSON Schema generation completed successfully!"
else
    echo "❌ JSON Schema generation failed!"
    exit 1
fi