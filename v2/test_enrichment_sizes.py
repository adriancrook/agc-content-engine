"""
Test DataEnrichment with incrementally larger drafts to find breaking point
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

# Load .env file
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)

from v2.agents.data_enrichment import DataEnrichmentAgent

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)

logger = logging.getLogger(__name__)


def generate_draft(word_count: int) -> str:
    """Generate a test draft with specified word count"""

    # Base paragraphs about gacha mechanics
    paragraphs = [
        "Gacha mechanics drive billions in mobile game revenue globally.",
        "Games like Genshin Impact generate massive revenue through gacha systems.",
        "Pity systems guarantee rare items after specific pull counts.",
        "Most games implement pity between fifty and one hundred pulls.",
        "This keeps players engaged without feeling exploited by mechanics.",
        "Monetization strategies balance revenue generation with player satisfaction carefully.",
        "Free-to-play models depend heavily on whale spending patterns.",
        "Average revenue per daily active user varies significantly.",
        "Retention rates improve with fair gacha mechanics implementation.",
        "Player psychology plays crucial role in monetization design.",
    ]

    # Repeat paragraphs to reach target word count
    draft = "# Gacha Mechanics in Mobile Games\n\n"
    draft += "## Introduction\n\n"

    words = []
    para_index = 0

    while len(words) < word_count:
        words.extend(paragraphs[para_index % len(paragraphs)].split())
        para_index += 1

        # Add section headers periodically
        if para_index % 5 == 0:
            draft += f"\n## Section {para_index // 5}\n\n"

    # Join words and trim to exact count
    draft += " ".join(words[:word_count])

    return draft


class MockArticle:
    """Mock article object for testing"""
    def __init__(self, title: str, draft: str):
        self.id = 1
        self.title = title
        self.draft = draft
        self.state = "enriching"


async def test_enrichment_size(word_count: int) -> bool:
    """Test enrichment with a specific word count"""

    logger.info(f"\n{'='*60}")
    logger.info(f"Testing with {word_count} word draft...")
    logger.info(f"{'='*60}\n")

    # Load API keys
    config = {
        "openrouter_api_key": os.getenv("OPENROUTER_API_KEY"),
        "brave_api_key": os.getenv("BRAVE_API_KEY")
    }

    if not config["openrouter_api_key"]:
        logger.error("OPENROUTER_API_KEY not found in environment")
        return False

    # Generate test draft
    draft = generate_draft(word_count)
    logger.info(f"Generated draft: {len(draft)} chars, {word_count} words")

    # Create mock article
    article = MockArticle(
        title="Understanding Gacha Mechanics in Mobile Gaming",
        draft=draft
    )

    # Run enrichment with timeout
    agent = DataEnrichmentAgent(config)

    try:
        # Set a 90-second timeout
        result = await asyncio.wait_for(
            agent.run(article),
            timeout=90.0
        )

        if result.success:
            logger.info(f"\n✅ SUCCESS with {word_count} words!")
            logger.info(f"   Citations: {len(result.data.get('enrichment', {}).get('citations', []))}")
            logger.info(f"   Metrics: {len(result.data.get('enrichment', {}).get('metrics', []))}")
            logger.info(f"   Testimonials: {len(result.data.get('enrichment', {}).get('testimonials', []))}")
            return True
        else:
            logger.error(f"\n❌ FAILED with {word_count} words: {result.error}")
            return False

    except asyncio.TimeoutError:
        logger.error(f"\n⏱️ TIMEOUT after 90s with {word_count} words!")
        return False
    except Exception as e:
        logger.error(f"\n❌ ERROR with {word_count} words: {e}")
        return False


async def main():
    """Run tests with increasing word counts"""

    # Test sizes: start small, increase gradually
    test_sizes = [
        100,    # Baseline (known to work)
        250,
        500,
        750,
        1000,
        1500,
        2000,
        3000,
        4000,
        5000,   # Full-size draft
    ]

    results = {}

    for size in test_sizes:
        success = await test_enrichment_size(size)
        results[size] = success

        if not success:
            logger.warning(f"\n⚠️ Found breaking point at {size} words!")
            break

        # Brief pause between tests
        await asyncio.sleep(2)

    # Summary
    logger.info(f"\n{'='*60}")
    logger.info("TEST SUMMARY")
    logger.info(f"{'='*60}")

    for size, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{size:5d} words: {status}")

    # Find breaking point
    passing = [s for s, success in results.items() if success]
    failing = [s for s, success in results.items() if not success]

    if passing and failing:
        logger.info(f"\n🎯 Breaking point: Between {max(passing)} and {min(failing)} words")
    elif not failing:
        logger.info(f"\n✅ All tests passed! Max tested: {max(passing)} words")
    else:
        logger.info(f"\n❌ All tests failed! Smallest tested: {min(failing)} words")


if __name__ == "__main__":
    asyncio.run(main())
