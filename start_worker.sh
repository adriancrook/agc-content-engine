#!/bin/bash
# AGC Local Worker - runs on Mac Mini
# Processes tasks using local Ollama models

cd "$(dirname "$0")"

# Load environment from .env if exists
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Check Ollama
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "❌ Ollama not running! Start with: ollama serve"
    exit 1
fi

# Activate venv
source venv/bin/activate

# Start worker
echo "🚀 Starting AGC Local Worker..."
python worker/local_worker.py
