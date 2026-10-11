#!/usr/bin/env bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "=========================================================="
echo " Starting AI Procurement Request Copilot..."
echo "=========================================================="

if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
    source .venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
else
    source .venv/bin/activate
fi

# Run pre-flight test verification
echo "Running test suite validation..."
python -m pytest tests/ -q

echo "Initializing benchmark artifacts..."
python -m eval.run_eval > /dev/null 2>&1 || true

PORT=${PORT:-8000}
HOST=${HOST:-127.0.0.1}

echo ""
echo "🚀 Copilot Web Application is live at: http://${HOST}:${PORT}"
echo "Dual Architecture Evaluation, Trace Visualizer & Human Controls active."
echo "Press Ctrl+C to stop."
echo ""

exec python -m uvicorn app.server:app --host "${HOST}" --port "${PORT}" --reload
