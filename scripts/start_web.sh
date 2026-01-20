#!/bin/bash

# Quick start script for Web Interface

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR/.."

# Activate virtual environment if exists
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

echo "Starting Backup System Web Interface..."
echo "Access at: http://localhost:5000"
echo "Press Ctrl+C to stop"
echo ""

# Run web interface
python3 main.py --web
