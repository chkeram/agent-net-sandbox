#!/bin/bash
# Test runner script for orchestrator

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Set PYTHONPATH to include src directory
export PYTHONPATH="${SCRIPT_DIR}/src:${PYTHONPATH}"

# Run pytest with all arguments passed to this script
python -m pytest "$@"