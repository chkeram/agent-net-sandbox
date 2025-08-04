#!/bin/bash

# Multi-Protocol Agent Orchestrator Startup Script

set -e

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "🚀 Starting Multi-Protocol Agent Orchestrator"
echo "Project directory: $PROJECT_DIR"

# Check if virtual environment exists
if [ ! -d "$PROJECT_DIR/venv" ] && [ ! -d "$PROJECT_DIR/.venv" ]; then
    echo "❌ Virtual environment not found. Please create one first:"
    echo "   python -m venv venv"
    echo "   source venv/bin/activate  # or venv\\Scripts\\activate on Windows"
    echo "   pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment if not already active
if [ -z "$VIRTUAL_ENV" ]; then
    if [ -d "$PROJECT_DIR/venv" ]; then
        echo "📦 Activating virtual environment..."
        source "$PROJECT_DIR/venv/bin/activate"
    elif [ -d "$PROJECT_DIR/.venv" ]; then
        echo "📦 Activating virtual environment..."
        source "$PROJECT_DIR/.venv/bin/activate"
    fi
fi

# Set environment variables
export PYTHONPATH="$PROJECT_DIR/src:$PYTHONPATH"

# Default configuration
export ORCHESTRATOR_HOST="${ORCHESTRATOR_HOST:-0.0.0.0}"
export ORCHESTRATOR_PORT="${ORCHESTRATOR_PORT:-8004}"
export ORCHESTRATOR_LOG_LEVEL="${ORCHESTRATOR_LOG_LEVEL:-INFO}"
export ORCHESTRATOR_DEBUG="${ORCHESTRATOR_DEBUG:-false}"
export ORCHESTRATOR_ENVIRONMENT="${ORCHESTRATOR_ENVIRONMENT:-development}"

# LLM Configuration
if [ -z "$OPENAI_API_KEY" ] && [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "⚠️  Warning: No LLM API keys found in environment"
    echo "   Set OPENAI_API_KEY or ANTHROPIC_API_KEY to enable AI routing"
    echo "   The orchestrator will still start but routing may be limited"
fi

echo "🔧 Configuration:"
echo "   Host: $ORCHESTRATOR_HOST"
echo "   Port: $ORCHESTRATOR_PORT"
echo "   Environment: $ORCHESTRATOR_ENVIRONMENT"
echo "   Log Level: $ORCHESTRATOR_LOG_LEVEL"
echo "   Debug Mode: $ORCHESTRATOR_DEBUG"

# Change to project directory
cd "$PROJECT_DIR"

# Run the orchestrator
echo "🎯 Starting orchestrator..."
python -m orchestrator.main "$@"