#!/bin/bash
# start.sh
# Launches the background job scheduler AND the Streamlit dashboard on Render

PORT="${PORT:-10000}"

echo "🚀 Starting AI Career Assistant..."
echo "📅 $(date)"

# Start the background scheduler daemon (applies to jobs daily at 9 AM + on startup)
echo "⏰ Launching background scheduler (AUTO_SUBMIT=${AUTO_SUBMIT:-false}, RUN_ON_STARTUP=${RUN_ON_STARTUP:-false})..."
python run_scheduler.py &
SCHEDULER_PID=$!
echo "  Scheduler started (PID: $SCHEDULER_PID)"

# Start Streamlit server on the dynamic port
echo "🌐 Starting Streamlit dashboard on port $PORT..."
streamlit run app.py --server.port "$PORT" --server.address 0.0.0.0
