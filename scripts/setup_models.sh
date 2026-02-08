#!/bin/bash
# Setup script for local LLM models
# Requires: Ollama installed and running

set -e

echo "🤖 AGC Content Engine - Model Setup"
echo "===================================="
echo ""

# Check Ollama is running
if ! ollama list &>/dev/null; then
    echo "❌ Ollama not running. Starting..."
    brew services start ollama
    sleep 5
fi

echo "📦 Pulling models for 32GB Mac Mini..."
echo ""

# Research & SEO Agent
echo "1/3: Pulling Qwen 2.5 14B (Research, SEO)..."
ollama pull qwen2.5:14b

# Writer Agent  
echo "2/3: Pulling Llama 3.2 11B (Writer)..."
ollama pull llama3.2:11b

# Fact Checker Agent
echo "3/3: Pulling DeepSeek-R1 14B (Fact Checker)..."
ollama pull deepseek-r1:14b

echo ""
echo "✅ All models installed!"
echo ""
echo "Installed models:"
ollama list

echo ""
echo "💡 Test with: ollama run qwen2.5:14b 'Hello, world!'"
