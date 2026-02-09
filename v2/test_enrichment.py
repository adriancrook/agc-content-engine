"""
Test script for DataEnrichment agent
Takes a test article and enriches it with citations, metrics, testimonials
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

from agents.data_enrichment import DataEnrichmentAgent


class MockArticle:
    """Mock article object for testing"""

    def __init__(self, title: str, draft: str):
        self.title = title
        self.draft = draft
        self.enrichment = None


async def test_enrichment():
    """Test enrichment on a sample article"""

    # Get API keys
    brave_key = os.getenv("BRAVE_API_KEY")
    openrouter_key = os.getenv("OPENROUTER_API_KEY")

    if not openrouter_key:
        print("Error: OPENROUTER_API_KEY not found")
        return

    # Load one of the test articles
    test_file = Path(__file__).parent / "test_outputs" / "test_guide_ultimate_guide_to_gacha_mechan.md"

    if not test_file.exists():
        print(f"Error: Test file not found: {test_file}")
        print("Run test_formats.py first to generate test articles")
        return

    with open(test_file, 'r') as f:
        content = f.read()

    # Extract just the article content (skip the header)
    lines = content.split('\n')
    start_idx = 0
    for i, line in enumerate(lines):
        if line.startswith('# The Ultimate Guide'):
            start_idx = i
            break

    draft = '\n'.join(lines[start_idx:])

    print("\n" + "="*60)
    print("TESTING DATA ENRICHMENT AGENT")
    print("="*60)
    print(f"\nArticle: Ultimate Guide to Gacha Mechanics")
    print(f"Draft length: {len(draft.split())} words\n")

    # Create mock article
    article = MockArticle(
        title="Ultimate Guide to Gacha Mechanics in Mobile Games",
        draft=draft
    )

    # Create enrichment agent
    config = {
        "brave_api_key": brave_key,
        "openrouter_api_key": openrouter_key
    }

    agent = DataEnrichmentAgent(config)

    # Run enrichment
    print("Running enrichment agent...")
    print("-" * 60)

    result = await agent.run(article)

    if result.success:
        print("✅ Enrichment successful!\n")

        enrichment = result.data['enrichment']
        guide = result.data['integration_guide']

        # Display results
        print(f"📊 ENRICHMENT RESULTS:")
        print(f"  - Citations found: {len(enrichment['citations'])}")
        print(f"  - Metrics found: {len(enrichment['metrics'])}")
        print(f"  - Testimonials matched: {len(enrichment['testimonials'])}")
        print(f"  - Media links found: {len(enrichment['media'])}")

        # Show citations
        if enrichment['citations']:
            print(f"\n📖 CITATIONS:")
            for citation in enrichment['citations']:
                print(f"  [{citation['id']}] {citation['source']}")
                print(f"      {citation['title'][:80]}...")
                print(f"      URL: {citation['url'][:60]}...")
                print()

        # Show testimonials
        if enrichment['testimonials']:
            print(f"\n💬 TESTIMONIALS:")
            for t in enrichment['testimonials']:
                print(f"  - {t['client']}")
                print(f"    \"{t['quote'][:100]}...\"")
                print()

        # Save integration guide
        output_file = Path(__file__).parent / "test_outputs" / "enrichment_guide.txt"
        with open(output_file, 'w') as f:
            f.write(guide)

        print(f"\n📝 Integration guide saved to: {output_file}")

        print(f"\n⏱️  Processing time: {result.data.get('duration', 0):.1f}s")
        print(f"💰 Estimated cost: ${result.cost:.3f}")

    else:
        print(f"❌ Enrichment failed: {result.error}")


if __name__ == "__main__":
    asyncio.run(test_enrichment())
