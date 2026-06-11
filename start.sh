#!/bin/bash
# start.sh
# Bind port dynamically for Render deployments
PORT="${PORT:-10000}"
echo "🚀 Starting Streamlit server on port $PORT..."
streamlit run app.py --server.port "$PORT" --server.address 0.0.0.0
