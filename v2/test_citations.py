"""
Test script for citation system
Verifies that [[n]](url) citations work end-to-end
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from agents.research import ResearchAgent
from agents.writer import WriterAgent
from agents.humanizer import HumanizerAgent
from agents.fact_checker import FactCheckerAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MockArticle:
    """Mock article object for testing"""
    def __init__(self, title):
        self.title = title
        self.research = None
        self.draft = None
        self.seo = None


async def test_citation_flow():
    """Test full citation flow from research to fact check"""

    config = {
        "brave_api_key": os.getenv("BRAVE_API_KEY"),
        "openrouter_api_key": os.getenv("OPENROUTER_API_KEY"),
    }

    # Test topic
    topic = "Mobile Gaming Revenue Trends 2025"
    article = MockArticle(topic)

    # Step 1: Research
    logger.info("=" * 60)
    logger.info("STEP 1: RESEARCH")
    logger.info("=" * 60)

    research_agent = ResearchAgent(config)
    research_result = await research_agent.run(article)

    if not research_result.success:
        logger.error(f"Research failed: {research_result.error}")
        return False

    article.research = research_result.data.get("research")
    sources = article.research.get("sources", [])

    logger.info(f"✓ Research complete: {len(sources)} sources")
    for i, s in enumerate(sources[:3], 1):
        logger.info(f"  [{i}] {s['title'][:60]}...")
        logger.info(f"      {s['url']}")

    # Step 2: Writer (Draft)
    logger.info("\n" + "=" * 60)
    logger.info("STEP 2: WRITER (Draft)")
    logger.info("=" * 60)

    writer_agent = WriterAgent(config)
    writer_result = await writer_agent.run(article)

    if not writer_result.success:
        logger.error(f"Writing failed: {writer_result.error}")
        return False

    article.draft = writer_result.data.get("draft")

    logger.info(f"✓ Draft complete: {len(article.draft.split())} words")

    # Check for citations in draft
    import re
    citation_pattern = r'\[\[(\d+)\]\]\(([^)]+)\)'
    citations = re.findall(citation_pattern, article.draft)

    logger.info(f"✓ Found {len(citations)} [[n]](url) citations in draft")
    for num, url in citations[:5]:
        logger.info(f"  [[{num}]]({url[:60]}...)")

    # Check for Sources section
    has_sources = "## Sources" in article.draft
    logger.info(f"✓ Sources section present: {has_sources}")

    # Step 3: Fact Checker
    logger.info("\n" + "=" * 60)
    logger.info("STEP 3: FACT CHECKER (Citation Validation)")
    logger.info("=" * 60)

    fact_checker = FactCheckerAgent(config)
    fact_check_result = await fact_checker.run(article)

    fact_check_data = fact_check_result.data.get("fact_check", {})
    citations_check = fact_check_data.get("citations", {})

    logger.info(f"✓ Fact check complete")
    logger.info(f"  Claims: {fact_check_data.get('verified_claims')}/{fact_check_data.get('total_claims')} verified")
    logger.info(f"  Citations: {citations_check.get('valid_citations')}/{citations_check.get('total_citations')} valid")
    logger.info(f"  All citations valid: {citations_check.get('all_valid')}")

    if citations_check.get('issues'):
        logger.warning("  Citation issues:")
        for issue in citations_check['issues']:
            logger.warning(f"    - {issue}")

    # Step 4: Humanizer
    logger.info("\n" + "=" * 60)
    logger.info("STEP 4: HUMANIZER (Citation Preservation)")
    logger.info("=" * 60)

    humanizer = HumanizerAgent(config)
    humanizer_result = await humanizer.run(article)

    if not humanizer_result.success:
        logger.error(f"Humanizer failed: {humanizer_result.error}")
        return False

    final_content = humanizer_result.data.get("final_content")

    # Check citations preserved
    final_citations = re.findall(citation_pattern, final_content)
    logger.info(f"✓ Humanizer complete: {len(final_content.split())} words")
    logger.info(f"✓ Citations preserved: {len(final_citations)} (was {len(citations)})")

    # Check Sources section preserved
    has_sources_final = "## Sources" in final_content
    logger.info(f"✓ Sources section preserved: {has_sources_final}")

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("CITATION SYSTEM TEST SUMMARY")
    logger.info("=" * 60)

    success = (
        len(citations) > 0 and
        has_sources and
        citations_check.get('all_valid', False) and
        len(final_citations) > 0 and
        has_sources_final
    )

    if success:
        logger.info("✅ ALL TESTS PASSED!")
        logger.info(f"  - Research: {len(sources)} sources with URLs")
        logger.info(f"  - Writer: {len(citations)} [[n]](url) citations")
        logger.info(f"  - Writer: Sources section included")
        logger.info(f"  - Fact Checker: All citations validated")
        logger.info(f"  - Humanizer: Citations preserved")
    else:
        logger.error("❌ TESTS FAILED")
        logger.error(f"  - Citations in draft: {len(citations)}")
        logger.error(f"  - Sources section: {has_sources}")
        logger.error(f"  - Citations valid: {citations_check.get('all_valid')}")
        logger.error(f"  - Citations after humanizer: {len(final_citations)}")
        logger.error(f"  - Sources preserved: {has_sources_final}")

    # Save test output
    output_file = Path(__file__).parent / "test_citations_output.md"
    with open(output_file, 'w') as f:
        f.write(final_content)
    logger.info(f"\n📝 Full article saved to: {output_file}")

    return success


if __name__ == "__main__":
    result = asyncio.run(test_citation_flow())
    sys.exit(0 if result else 1)
