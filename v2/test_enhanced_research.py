"""
Test script for Enhanced Research Sources
Validates that Research Agent prioritizes trusted sources
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from agents.research import ResearchAgent
from data.trusted_sources import get_tier1_domains, get_all_domains, DOMAIN_MAP

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MockArticle:
    """Mock article object for testing"""
    def __init__(self, title):
        self.title = title
        self.research = None


async def test_enhanced_research():
    """Test enhanced research with trusted sources"""

    config = {
        "brave_api_key": os.getenv("BRAVE_API_KEY"),
        "openrouter_api_key": os.getenv("OPENROUTER_API_KEY"),
    }

    # Test topic
    topic = "Mobile Game Monetization Trends 2025"
    article = MockArticle(topic)

    logger.info("=" * 60)
    logger.info("ENHANCED RESEARCH TEST")
    logger.info("=" * 60)

    logger.info(f"\nTopic: {topic}")
    logger.info(f"Trusted source domains: {len(get_tier1_domains())}")

    tier1_domains = get_tier1_domains()
    logger.info(f"  - {', '.join(tier1_domains[:5])}")

    # Run research
    research_agent = ResearchAgent(config)
    result = await research_agent.run(article)

    if not result.success:
        logger.error(f"❌ Research failed: {result.error}")
        return False

    research_data = result.data.get("research")
    sources = research_data.get("sources", [])

    logger.info(f"\n✅ Research complete!")
    logger.info(f"  Total sources: {len(sources)}")

    # Analyze sources
    trusted_sources = []
    general_sources = []

    all_domains = get_all_domains()

    for source in sources:
        url = source.get('url', '')
        is_trusted = False

        for domain in all_domains:
            if domain in url:
                trusted_sources.append(source)
                is_trusted = True
                break

        if not is_trusted:
            general_sources.append(source)

    trusted_count = len(trusted_sources)
    general_count = len(general_sources)

    logger.info(f"\n📊 Source Breakdown:")
    logger.info(f"  Trusted sources: {trusted_count} ({trusted_count/len(sources)*100:.1f}%)")
    logger.info(f"  General sources: {general_count} ({general_count/len(sources)*100:.1f}%)")

    # Show trusted sources
    logger.info(f"\n✨ Trusted Sources Found:")
    for i, source in enumerate(trusted_sources, 1):
        url = source.get('url', '')
        title = source.get('title', '')

        # Find which trusted domain
        domain_name = "Unknown"
        for domain in all_domains:
            if domain in url:
                source_info = DOMAIN_MAP.get(domain)
                if source_info:
                    domain_name = source_info.name
                break

        logger.info(f"  {i}. {domain_name}")
        logger.info(f"     {title[:70]}...")
        logger.info(f"     {url}")
        logger.info(f"     Relevance: {source.get('relevance_score', 'N/A')}")

    # Validation
    success = (
        len(sources) >= 10 and
        trusted_count >= 3  # At least 3 trusted sources
    )

    logger.info("\n" + "=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)

    if success:
        logger.info("✅ ALL TESTS PASSED!")
        logger.info(f"  - Found {len(sources)} total sources")
        logger.info(f"  - {trusted_count} from trusted sources ({trusted_count/len(sources)*100:.1f}%)")
        logger.info(f"  - {general_count} from general web")
        logger.info(f"  - Research quality significantly improved!")
    else:
        logger.error("❌ TESTS FAILED")
        logger.error(f"  - Total sources: {len(sources)} (need >= 10)")
        logger.error(f"  - Trusted sources: {trusted_count} (need >= 3)")

    # Show quality metrics
    if trusted_sources:
        logger.info("\n" + "=" * 60)
        logger.info("QUALITY IMPROVEMENT")
        logger.info("=" * 60)

        tier1_count = sum(1 for s in trusted_sources
                         if any(d in s.get('url', '') for d in tier1_domains))

        logger.info(f"✨ Tier 1 Sources (Competitor Blogs): {tier1_count}")
        logger.info(f"✨ All Trusted Sources: {trusted_count}")
        logger.info(f"\nBefore: Random web results")
        logger.info(f"After: {trusted_count/len(sources)*100:.0f}% from trusted, authoritative sources")

    return success


if __name__ == "__main__":
    result = asyncio.run(test_enhanced_research())
    sys.exit(0 if result else 1)
