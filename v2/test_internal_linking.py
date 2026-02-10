"""
Test script for Internal Linking system
Validates internal link suggestions and insertion
"""

import asyncio
import logging
import os
import re
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from agents.internal_linking import InternalLinkingAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MockArticle:
    """Mock article object for testing"""
    def __init__(self, title, draft):
        self.title = title
        self.draft = draft


def count_adriancrook_links(text: str) -> int:
    """Count internal adriancrook.com links"""
    pattern = r'\[([^\]]+)\]\((https://adriancrook\.com/[^\)]+)\)'
    matches = re.findall(pattern, text)
    return len(matches)


def extract_links(text: str) -> list:
    """Extract all internal links"""
    pattern = r'\[([^\]]+)\]\((https://adriancrook\.com/[^\)]+)\)'
    matches = re.findall(pattern, text)
    return [(anchor, url) for anchor, url in matches]


async def test_internal_linking():
    """Test internal linking system"""

    # Sample article about monetization
    title = "Mobile Game Monetization Strategies 2025"

    draft = """# Mobile Game Monetization Strategies 2025

The mobile gaming industry continues to evolve, with monetization strategies becoming increasingly sophisticated. In-app purchases remain the dominant revenue model, accounting for 72% of mobile game revenue. However, successful publishers are embracing hybrid monetization approaches that combine IAP with advertising.

## In-App Purchase Strategies

Player retention is crucial for maximizing IAP revenue. Games must balance monetization with user experience to avoid alienating players. Battle pass systems have emerged as a popular model, offering players ongoing value through seasonal content.

## Advertising Integration

Rewarded video ads have become the preferred ad format, allowing players to voluntarily engage with advertisements in exchange for in-game rewards. This approach maintains user experience while generating revenue from non-paying players.

## User Acquisition and Analytics

Understanding your game's KPIs is essential for optimizing monetization. Metrics like ARPU and cohort analysis help developers make data-driven decisions about pricing and content.

## Game Design Considerations

The core loop must support monetization without feeling exploitative. Economy design is critical for balancing progression with revenue generation.

## Conclusion

Successful mobile game monetization requires understanding player psychology, leveraging data analytics, and continuously optimizing based on performance metrics."""

    article = MockArticle(title, draft)

    logger.info("=" * 60)
    logger.info("INTERNAL LINKING TEST")
    logger.info("=" * 60)

    logger.info(f"\nArticle: {title}")
    logger.info(f"Original word count: {len(draft.split())} words")

    # Count existing links (should be 0)
    original_links = count_adriancrook_links(draft)
    logger.info(f"Original internal links: {original_links}")

    # Run internal linking agent
    config = {}
    linking_agent = InternalLinkingAgent(config)

    result = await linking_agent.run(article)

    if not result.success:
        logger.error(f"❌ Internal linking failed: {result.error}")
        return False

    updated_draft = result.data.get("draft_with_links")
    links_added = result.data.get("internal_links_added")
    suggested = result.data.get("suggested_articles", [])

    # Count final links
    final_links = count_adriancrook_links(updated_draft)
    actual_links = extract_links(updated_draft)

    logger.info(f"\n✅ Internal linking complete!")
    logger.info(f"  Links added: {links_added}")
    logger.info(f"  Final link count: {final_links}")
    logger.info(f"  Articles suggested: {len(suggested)}")

    # Show suggested articles
    logger.info(f"\nSuggested Articles:")
    for i, article_info in enumerate(suggested, 1):
        logger.info(f"  {i}. {article_info['title']}")
        logger.info(f"     {article_info['url']}")

    # Show inserted links
    logger.info(f"\nInserted Links:")
    for i, (anchor, url) in enumerate(actual_links, 1):
        logger.info(f"  {i}. [{anchor}]({url})")

    # Validation
    success = (
        final_links >= 2 and  # At least 2 internal links
        links_added >= 2 and
        len(suggested) >= 2
    )

    logger.info("\n" + "=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)

    if success:
        logger.info("✅ ALL TESTS PASSED!")
        logger.info(f"  - Suggested {len(suggested)} relevant articles")
        logger.info(f"  - Added {links_added} internal links")
        logger.info(f"  - Final article has {final_links} internal links")
    else:
        logger.error("❌ TESTS FAILED")
        logger.error(f"  - Final links: {final_links} (need >= 2)")
        logger.error(f"  - Links added: {links_added} (need >= 2)")
        logger.error(f"  - Suggested: {len(suggested)} (need >= 2)")

    # Save output
    output_file = Path(__file__).parent / "test_internal_linking_output.md"
    with open(output_file, 'w') as f:
        f.write(updated_draft)
    logger.info(f"\n📝 Updated article saved to: {output_file}")

    # Show snippet
    if actual_links:
        logger.info("\n" + "=" * 60)
        logger.info("EXAMPLE LINK IN CONTEXT")
        logger.info("=" * 60)
        # Find first link and show context
        first_anchor, first_url = actual_links[0]
        link_pattern = re.escape(f"[{first_anchor}]({first_url})")
        match = re.search(f".{{50}}{link_pattern}.{{50}}", updated_draft, re.DOTALL)
        if match:
            context = match.group(0)
            logger.info(f"\n{context}\n")

    return success


if __name__ == "__main__":
    result = asyncio.run(test_internal_linking())
    sys.exit(0 if result else 1)
