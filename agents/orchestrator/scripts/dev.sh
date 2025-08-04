#!/bin/bash

# Development startup script with hot reload

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "🔧 Starting Orchestrator in Development Mode"

# Set development environment variables
export ORCHESTRATOR_DEBUG=true
export ORCHESTRATOR_ENVIRONMENT=development
export ORCHESTRATOR_LOG_LEVEL=DEBUG
export ORCHESTRATOR_HOST=127.0.0.1
export ORCHESTRATOR_PORT=8004

# Add project to Python path
export PYTHONPATH="$PROJECT_DIR/src:$PYTHONPATH"

cd "$PROJECT_DIR"

# Check if running in venv
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Warning: Not running in a virtual environment"
    echo "   Consider activating your venv first"
fi

echo "🔧 Development Configuration:"
echo "   Host: $ORCHESTRATOR_HOST"
echo "   Port: $ORCHESTRATOR_PORT"
echo "   Debug: $ORCHESTRATOR_DEBUG"
echo "   Auto-reload: enabled"
echo ""

# Run with uvicorn directly for better development experience
uvicorn orchestrator.api:app \
    --host "$ORCHESTRATOR_HOST" \
    --port "$ORCHESTRATOR_PORT" \
    --reload \
    --reload-dir src \
    --log-level debug \
    --access-log \
    --use-colors