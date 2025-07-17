#!/bin/bash
# Generate TypeScript interfaces from Pydantic models

echo "🚀 Generating TypeScript interfaces from Pydantic models..."

# Check if in virtual environment
if [[ -z "${VIRTUAL_ENV}" ]]; then
    echo "⚠️  No virtual environment detected. Activating .venv..."
    source .venv/bin/activate 2>/dev/null || source venv/bin/activate 2>/dev/null || {
        echo "❌ Could not activate virtual environment. Please activate it manually."
        exit 1
    }
fi

# Run the generator
cd src && python -m ctutor_backend.cli.cli generate-types "$@"

echo "✅ TypeScript interfaces generated successfully!"
echo "📁 Check frontend/src/types/generated/ for the generated files"