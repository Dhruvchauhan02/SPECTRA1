#!/bin/bash
# SPECTRA-AI startup script
# Usage: ./start.sh [dev|prod]

MODE=${1:-dev}

if [ "$MODE" = "prod" ]; then
    echo "Starting SPECTRA-AI in production mode..."
    python -m uvicorn api.main1:app --host 0.0.0.0 --port 8000 --workers 1
else
    echo "Starting SPECTRA-AI in development mode..."
    python -m uvicorn api.main1:app --host 0.0.0.0 --port 8000 --reload
fi
