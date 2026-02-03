#!/bin/bash
set -e
cd "$(dirname "$0")/.."
echo "Starting Streamlit UI on http://localhost:8501"
python -m streamlit run ui/streamlit_app.py --server.port 8501
