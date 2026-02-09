"""
Minimal test for DataEnrichment agent
Tests with a tiny 200-word draft to isolate the issue
"""

import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).parent.parent))

from dotenv import load_dotenv

# Load .env
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)

from v2.agents.data_enrichment import DataEnrichmentAgent


# Mock article with minimal draft
class MockArticle:
    def __init__(self):
        self.id = "test-minimal"
        self.title = "How Gacha Pity Systems Work"
        self.draft = """# How Gacha Pity Systems Work

Gacha mechanics drive billions in mobile game revenue. Games like Genshin Impact generate over $3 billion annually through sophisticated gacha systems.

## Pity System Basics

Pity systems guarantee a rare item after a certain number of pulls. Most successful games implement pity between 50-100 pulls.

For example, Genshin Impact uses an 80-pull pity system. This keeps players engaged without feeling exploited. The system feels fair while driving strong monetization.

## Why They Work

Players appreciate knowing they will eventually get the item they want. This transparency builds trust and encourages spending."""


async def test_minimal_enrichment():
    """Test DataEnrichment with minimal draft"""

    print("\n" + "="*70)
    print("MINIMAL ENRICHMENT TEST")
    print("="*70)

    # Get API keys
    brave_key = os.getenv("BRAVE_API_KEY")
    openrouter_key = os.getenv("OPENROUTER_API_KEY")

    if not brave_key:
        print("❌ BRAVE_API_KEY not found in .env")
        return

    if not openrouter_key:
        print("❌ OPENROUTER_API_KEY not found in .env")
        return

    print(f"\n✓ API keys loaded")
    print(f"✓ Draft length: {len(MockArticle().draft.split())} words\n")

    # Create agent
    print("Creating DataEnrichment agent...")
    try:
        agent = DataEnrichmentAgent({
            "brave_api_key": brave_key,
            "openrouter_api_key": openrouter_key
        })
        print("✓ Agent created successfully")
    except Exception as e:
        print(f"❌ Agent creation failed: {e}")
        return

    # Create mock article
    article = MockArticle()

    print(f"\nTesting with article: '{article.title}'")
    print(f"Draft: {len(article.draft)} chars, {len(article.draft.split())} words")
    print("\n" + "-"*70)
    print("STARTING ENRICHMENT - Watch for where it hangs...")
    print("-"*70 + "\n")

    start_time = datetime.now()

    try:
        # Add timeout
        result = await asyncio.wait_for(
            agent.run(article),
            timeout=180  # 3 minute timeout
        )

        elapsed = (datetime.now() - start_time).total_seconds()

        print("\n" + "="*70)
        print("✅ ENRICHMENT COMPLETED!")
        print("="*70)
        print(f"\n⏱️  Time: {elapsed:.1f}s")
        print(f"\nSuccess: {result.success}")

        if result.success:
            enrichment = result.data.get("enrichment", {})
            print(f"\n📊 Results:")
            print(f"  Citations: {len(enrichment.get('citations', []))}")
            print(f"  Metrics: {len(enrichment.get('metrics', []))}")
            print(f"  Testimonials: {len(enrichment.get('testimonials', []))}")

            # Show a sample citation
            if enrichment.get('citations'):
                print(f"\n  Sample citation:")
                cit = enrichment['citations'][0]
                print(f"    - {cit.get('claim', 'No claim')[:60]}...")
                print(f"    - Source: {cit.get('source', 'No source')}")
        else:
            print(f"\n❌ Error: {result.error}")

    except asyncio.TimeoutError:
        elapsed = (datetime.now() - start_time).total_seconds()
        print("\n" + "="*70)
        print(f"❌ TIMEOUT after {elapsed:.1f}s")
        print("="*70)
        print("\nThe enrichment agent hung for 3+ minutes.")
        print("This confirms there's a blocking issue in the agent code.")

    except Exception as e:
        elapsed = (datetime.now() - start_time).total_seconds()
        print("\n" + "="*70)
        print(f"❌ EXCEPTION after {elapsed:.1f}s")
        print("="*70)
        print(f"\nError: {e}")
        print(f"Type: {type(e).__name__}")

        import traceback
        print("\nTraceback:")
        traceback.print_exc()


if __name__ == "__main__":
    print("\n🔬 Testing DataEnrichment agent with minimal 150-word draft")
    print("This will help identify if the issue is draft size or agent logic.\n")

    asyncio.run(test_minimal_enrichment())

    print("\n" + "="*70)
    print("If this test:")
    print("  ✅ Completes quickly → Performance issue with large drafts")
    print("  ❌ Hangs/times out → Logic bug in DataEnrichment agent")
    print("  ❌ Errors → Check error message and traceback")
    print("="*70 + "\n")
