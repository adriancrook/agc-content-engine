"""
Test script to generate articles in all 4 formats
Validates prompts before implementing into full pipeline
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

import requests
from FORMAT_PROMPTS import get_format_prompt

# Try to load .env file if it exists
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass


def call_claude(prompt: str, api_key: str) -> str:
    """Call Claude via OpenRouter"""
    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://adriancrook.com",
        "X-Title": "AGC Content Engine v2 - Format Testing",
    }

    payload = {
        "model": "anthropic/claude-sonnet-4",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 8192,
        "temperature": 0.3,
    }

    response = requests.post(url, json=payload, headers=headers, timeout=300)
    response.raise_for_status()
    data = response.json()

    return data["choices"][0]["message"]["content"]


def test_format(format_type: str, topic: str, source: str, api_key: str, output_dir: Path):
    """Generate and save a test article"""
    print(f"\n{'='*60}")
    print(f"Testing Format: {format_type.upper()}")
    print(f"Topic: {topic}")
    print(f"{'='*60}\n")

    # Get the prompt
    prompt = get_format_prompt(format_type, topic, source)

    # Generate article
    print("Generating article...")
    try:
        article = call_claude(prompt, api_key)

        # Save to file
        filename = f"test_{format_type}_{topic.lower().replace(' ', '_')[:30]}.md"
        output_file = output_dir / filename

        with open(output_file, 'w') as f:
            f.write(f"# TEST ARTICLE - {format_type.upper()} FORMAT\n\n")
            f.write(f"**Topic:** {topic}\n\n")
            f.write(f"**Format:** {format_type}\n\n")
            f.write("---\n\n")
            f.write(article)

        print(f"✅ Saved to: {output_file}")
        print(f"📊 Word count: {len(article.split())}")

        return output_file

    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def main():
    # Get API key from argument or environment
    if len(sys.argv) > 1:
        api_key = sys.argv[1]
    else:
        api_key = os.getenv("OPENROUTER_API_KEY")

    if not api_key:
        print("Error: OPENROUTER_API_KEY not found")
        print("Usage: python test_formats.py [API_KEY]")
        print("   or: Set OPENROUTER_API_KEY environment variable")
        sys.exit(1)

    # Create output directory
    output_dir = Path(__file__).parent / "test_outputs"
    output_dir.mkdir(exist_ok=True)

    # Test cases
    tests = [
        {
            "format_type": "prediction",
            "topic": "Mobile Gaming Ad Revenue Trends in 2026",
            "source": "Industry analysis of mobile gaming ad monetization discussing breakthrough $3M daily revenue games, new ad formats, and evolving player expectations"
        },
        {
            "format_type": "guide",
            "topic": "Ultimate Guide to Gacha Mechanics in Mobile Games",
            "source": ""
        },
        {
            "format_type": "conceptual",
            "topic": "Social Features vs Solo Gameplay in Mobile Games",
            "source": ""
        },
        {
            "format_type": "best_practices",
            "topic": "Best Practices for Daily Login Rewards",
            "source": ""
        }
    ]

    print("\n" + "="*60)
    print("FORMAT TESTING - Adrian Crook Blog Styles")
    print("="*60)

    results = []

    for test in tests:
        result = test_format(
            format_type=test["format_type"],
            topic=test["topic"],
            source=test["source"],
            api_key=api_key,
            output_dir=output_dir
        )
        results.append({
            "format": test["format_type"],
            "topic": test["topic"],
            "file": result
        })

    # Summary
    print("\n" + "="*60)
    print("GENERATION COMPLETE")
    print("="*60)
    print("\nGenerated articles:")
    for r in results:
        status = "✅" if r["file"] else "❌"
        print(f"{status} {r['format']:15} - {r['topic']}")

    print(f"\n📁 Output directory: {output_dir}")
    print("\nNext steps:")
    print("1. Review each test article")
    print("2. Compare to actual blog articles")
    print("3. Score quality (0-10)")
    print("4. Identify needed fixes")
    print("5. Refine prompts and regenerate")


if __name__ == "__main__":
    main()
