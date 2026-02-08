#!/bin/bash
# Start the AGC Content Engine web server

cd "$(dirname "$0")"

# Activate virtual environment
source venv/bin/activate

# Load API keys
export BRAVE_API_KEY=$(cat ~/.credentials/brave-api.txt 2>/dev/null | head -1)
export OPENROUTER_API_KEY=$(grep -oP 'OPENROUTER_API_KEY=\K.*' ~/.credentials/openrouter.txt 2>/dev/null || cat ~/.credentials/openrouter.txt 2>/dev/null | grep -v '^#' | head -1)
export GEMINI_API_KEY=$(cat ~/.credentials/gemini-api.txt 2>/dev/null | head -1)

echo "🚀 Starting AGC Content Engine..."
echo "   BRAVE_API_KEY: ${BRAVE_API_KEY:0:10}..."
echo "   OPENROUTER_API_KEY: ${OPENROUTER_API_KEY:0:20}..."
echo "   Web UI: http://192.168.1.162:8080"

# Ensure Ollama is running
if ! curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
    echo "⚠️  Ollama not running. Starting..."
    OLLAMA_FLASH_ATTENTION="1" OLLAMA_KV_CACHE_TYPE="q8_0" ollama serve &
    sleep 3
fi

# Start Flask
python web/app.py
