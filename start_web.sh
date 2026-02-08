#!/bin/bash
# AGC Content Engine - Web Interface Startup Script

cd /Users/kitwren/agc-content-engine

# Activate virtual environment
source venv/bin/activate

# Set API keys from credentials
export BRAVE_API_KEY=$(cat ~/.credentials/brave-api.txt 2>/dev/null)
export OPENROUTER_API_KEY=$(cat ~/.credentials/openrouter.txt 2>/dev/null)
export GOOGLE_API_KEY=$(cat ~/.credentials/gemini-api.txt 2>/dev/null)

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "⚠️  Ollama is not running. Starting in CPU mode..."
    OLLAMA_FLASH_ATTENTION="1" OLLAMA_KV_CACHE_TYPE="q8_0" /opt/homebrew/opt/ollama/bin/ollama serve &
    sleep 5
fi

echo ""
echo "🚀 AGC Content Engine"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Web Interface: http://$(hostname):8080"
echo "              http://localhost:8080"
echo ""
echo "API Keys:"
echo "  • Brave Search: $([ -n "$BRAVE_API_KEY" ] && echo '✅' || echo '❌')"
echo "  • OpenRouter:   $([ -n "$OPENROUTER_API_KEY" ] && echo '✅' || echo '❌')"
echo "  • Google/Gemini:$([ -n "$GOOGLE_API_KEY" ] && echo '✅' || echo '❌')"
echo ""
echo "Press Ctrl+C to stop"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Start Flask app
python web/app.py
