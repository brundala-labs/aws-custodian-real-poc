#!/bin/bash
set -e
cd "$(dirname "$0")/.."
echo "Starting CoreStack API on http://localhost:8080"
echo "Docs: http://localhost:8080/docs"
python -m uvicorn integration.app:app --host 0.0.0.0 --port 8080 --reload
