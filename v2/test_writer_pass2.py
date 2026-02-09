"""
Test Writer Pass 2 - Integration of enrichment data
Takes draft + enrichment guide and produces final enriched article
"""

import asyncio
import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from dotenv import load_dotenv

# Load .env
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)

import requests


def call_claude(prompt: str, api_key: str) -> str:
    """Call Claude via OpenRouter for Writer Pass 2"""
    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://adriancrook.com",
        "X-Title": "AGC Content Engine v2 - Writer Pass 2",
    }

    payload = {
        "model": "anthropic/claude-sonnet-4",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 8192,
        "temperature": 0.3,  # Lower for precise integration
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=300)
        response.raise_for_status()
        data = response.json()

        return data["choices"][0]["message"]["content"]

    except Exception as e:
        print(f"❌ OpenRouter API call failed: {e}")
        raise


async def test_writer_pass2():
    """Test Writer Pass 2 with enrichment data"""

    # Get API key
    api_key = os.getenv("OPENROUTER_API_KEY")

    if not api_key:
        print("Error: OPENROUTER_API_KEY not found")
        return

    # Load the original draft
    draft_file = Path(__file__).parent / "test_outputs" / "test_guide_ultimate_guide_to_gacha_mechan.md"

    if not draft_file.exists():
        print(f"Error: Draft file not found: {draft_file}")
        return

    with open(draft_file, 'r') as f:
        content = f.read()

    # Extract just the article content (skip header)
    lines = content.split('\n')
    start_idx = 0
    for i, line in enumerate(lines):
        if line.startswith('# The Ultimate Guide'):
            start_idx = i
            break

    original_draft = '\n'.join(lines[start_idx:])

    # Load the enrichment guide
    guide_file = Path(__file__).parent / "test_outputs" / "enrichment_guide.txt"

    if not guide_file.exists():
        print(f"Error: Enrichment guide not found: {guide_file}")
        return

    with open(guide_file, 'r') as f:
        enrichment_guide = f.read()

    print("\n" + "="*60)
    print("TESTING WRITER PASS 2 - ENRICHMENT INTEGRATION")
    print("="*60)
    print(f"\nOriginal draft: {len(original_draft.split())} words")
    print(f"Enrichment: 5 citations, 5 metrics, 1 testimonial\n")

    # Create Writer Pass 2 prompt
    prompt = f"""You are revising an article for adriancrook.com - a mobile gaming industry blog.

ORIGINAL DRAFT:
{original_draft}

ENRICHMENT DATA:
{enrichment_guide}

Your task: Integrate the citations, metrics, testimonials, and media links naturally into the article while maintaining the original structure and voice.

REQUIREMENTS:
1. Add numbered citations [1], [2] at the END of relevant sentences where specified
2. Weave in specific metrics naturally (e.g., "Clash Royale, which has generated over $4+ billion in lifetime revenue...")
3. Integrate the testimonial in a "Professional Design Support" or relevant section
4. Create a "## Sources" section at the bottom with all [1], [2] citations formatted as:
   [1] Source Name - Title - URL
   [2] Source Name - Title - URL
5. Maintain mobile gaming focus and professional but practical tone
6. Keep the same format structure (Ultimate Guide format with Key Takeaways, tables, FAQs)
7. Don't force citations where they don't fit naturally - find the best integration points

OUTPUT: The complete revised article in markdown format with all enrichment integrated.
"""

    print("Running Writer Pass 2...")
    print("-" * 60)

    try:
        enriched_article = call_claude(prompt, api_key)

        # Save the enriched article
        output_file = Path(__file__).parent / "test_outputs" / "gacha_guide_ENRICHED.md"
        with open(output_file, 'w') as f:
            f.write(enriched_article)

        print("✅ Writer Pass 2 complete!\n")

        # Analyze results
        enriched_word_count = len(enriched_article.split())
        citation_count = enriched_article.count('[')  # Rough count of citations

        print(f"📊 RESULTS:")
        print(f"  Original: {len(original_draft.split())} words")
        print(f"  Enriched: {enriched_word_count} words")
        print(f"  Change: +{enriched_word_count - len(original_draft.split())} words")
        print(f"  Citations added: ~{citation_count}")
        print(f"  Has Sources section: {'## Sources' in enriched_article}")
        print(f"  Has testimonial: {'AC&A' in enriched_article or 'Adrian' in enriched_article}")

        print(f"\n📝 Enriched article saved to: {output_file}")

        print("\n" + "="*60)
        print("NEXT STEPS:")
        print("="*60)
        print("1. Review the enriched article")
        print("2. Compare to your real blog articles")
        print("3. Check citation quality and integration")
        print("4. Validate metrics are woven naturally")
        print("5. Confirm testimonial placement makes sense")

    except Exception as e:
        print(f"❌ Writer Pass 2 failed: {e}")


if __name__ == "__main__":
    asyncio.run(test_writer_pass2())
