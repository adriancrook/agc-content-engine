#!/usr/bin/env python3
"""
Check Ollama status and available models.
"""

import requests
import sys


def main():
    print("🔍 Checking Ollama Status")
    print("=" * 40)
    
    try:
        # Check if Ollama is running
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        response.raise_for_status()
        
        data = response.json()
        models = data.get("models", [])
        
        print(f"✅ Ollama is running")
        print(f"\n📦 Available models ({len(models)}):")
        
        required_models = ["qwen2.5:14b"]
        available = set()
        
        for model in models:
            name = model.get("name", "unknown")
            size_gb = model.get("size", 0) / (1024**3)
            print(f"   • {name} ({size_gb:.1f} GB)")
            available.add(name)
        
        print("\n🎯 Required models:")
        for model in required_models:
            if model in available:
                print(f"   ✅ {model}")
            else:
                print(f"   ❌ {model} (missing - run: ollama pull {model})")
        
        # Check if all required models are available
        missing = set(required_models) - available
        if missing:
            print(f"\n⚠️  Missing models: {', '.join(missing)}")
            print("   Run setup_models.sh to install them")
            return 1
        else:
            print("\n✅ All required models available!")
            return 0
            
    except requests.exceptions.ConnectionError:
        print("❌ Ollama is not running")
        print("   Start it with: brew services start ollama")
        return 1
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
