"""
Test script for Evidence & Quotes system
Verifies expert quotes in blockquotes and game/company hyperlinks
"""

import asyncio
import logging
import os
import re
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from agents.research import ResearchAgent
from agents.writer import WriterAgent
from agents.humanizer import HumanizerAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MockArticle:
    """Mock article object for testing"""
    def __init__(self, title):
        self.title = title
        self.research = None
        self.draft = None
        self.seo = None


def count_blockquotes(text: str) -> int:
    """Count blockquote sections in markdown"""
    # Match lines that start with >
    lines = text.split('\n')
    blockquote_count = 0
    in_blockquote = False

    for line in lines:
        if line.strip().startswith('>'):
            if not in_blockquote:
                blockquote_count += 1
                in_blockquote = True
        else:
            in_blockquote = False

    return blockquote_count


def count_entity_links(text: str) -> dict:
    """Count game/company hyperlinks in markdown"""
    # Pattern: [Text](url)
    link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
    matches = re.findall(link_pattern, text)

    # Filter out citation links [[n]](url)
    entity_links = []
    for link_text, url in matches:
        if not link_text.startswith('['):  # Not a citation
            entity_links.append((link_text, url))

    # Categorize links
    game_domains = ['supercell.com', 'king.com', 'pokemon', 'genshin', 'pubg', 'roblox']
    company_domains = ['supercell.com', 'king.com', 'riot', 'tencent', 'niantic']

    games = [link for link in entity_links if any(domain in link[1].lower() for domain in game_domains)]
    companies = [link for link in entity_links if any(domain in link[1].lower() for domain in company_domains)]

    return {
        'total': len(entity_links),
        'games': len(games),
        'companies': len(companies),
        'examples': entity_links[:5]
    }


def extract_blockquote_text(text: str) -> list:
    """Extract all blockquote sections with their content"""
    blockquotes = []
    lines = text.split('\n')
    current_quote = []

    for line in lines:
        if line.strip().startswith('>'):
            current_quote.append(line)
        elif current_quote:
            blockquotes.append('\n'.join(current_quote))
            current_quote = []

    if current_quote:
        blockquotes.append('\n'.join(current_quote))

    return blockquotes


async def test_evidence_quotes_flow():
    """Test full evidence & quotes flow"""

    config = {
        "brave_api_key": os.getenv("BRAVE_API_KEY"),
        "openrouter_api_key": os.getenv("OPENROUTER_API_KEY"),
    }

    # Test topic - gaming-related to utilize entity database
    topic = "Mobile Gaming Monetization Strategies 2025"
    article = MockArticle(topic)

    # Step 1: Research with structured quotes
    logger.info("=" * 60)
    logger.info("STEP 1: RESEARCH (Structured Quotes)")
    logger.info("=" * 60)

    research_agent = ResearchAgent(config)
    research_result = await research_agent.run(article)

    if not research_result.success:
        logger.error(f"Research failed: {research_result.error}")
        return False

    article.research = research_result.data.get("research")
    sources = article.research.get("sources", [])

    logger.info(f"✓ Research complete: {len(sources)} sources")

    # Check for structured quotes
    total_quotes = 0
    structured_quotes = 0
    for source in sources:
        quotes = source.get('key_quotes', [])
        total_quotes += len(quotes)
        for quote in quotes:
            if isinstance(quote, dict) and 'author' in quote:
                structured_quotes += 1
                logger.info(f"  Quote: \"{quote['text'][:50]}...\"")
                logger.info(f"  Author: {quote['author']}")
                if quote.get('author_title'):
                    logger.info(f"  Title: {quote['author_title']}")
                break  # Show one example

    logger.info(f"✓ Found {total_quotes} quotes, {structured_quotes} with attribution")

    # Step 2: Writer (with blockquotes and entity links)
    logger.info("\n" + "=" * 60)
    logger.info("STEP 2: WRITER (Blockquotes & Entity Links)")
    logger.info("=" * 60)

    writer_agent = WriterAgent(config)
    writer_result = await writer_agent.run(article)

    if not writer_result.success:
        logger.error(f"Writing failed: {writer_result.error}")
        return False

    article.draft = writer_result.data.get("draft")

    logger.info(f"✓ Draft complete: {len(article.draft.split())} words")

    # Check for blockquotes
    blockquote_count = count_blockquotes(article.draft)
    blockquotes = extract_blockquote_text(article.draft)

    logger.info(f"✓ Found {blockquote_count} blockquote sections")
    if blockquotes:
        logger.info(f"  Example blockquote:")
        for line in blockquotes[0].split('\n')[:3]:
            logger.info(f"    {line}")

    # Check for entity links
    entity_links = count_entity_links(article.draft)
    logger.info(f"✓ Found {entity_links['total']} entity hyperlinks")
    logger.info(f"  Games linked: {entity_links['games']}")
    logger.info(f"  Companies linked: {entity_links['companies']}")
    if entity_links['examples']:
        logger.info(f"  Examples:")
        for text, url in entity_links['examples'][:3]:
            logger.info(f"    [{text}]({url})")

    # Check for citations (from previous phase)
    citation_pattern = r'\[\[(\d+)\]\]\(([^)]+)\)'
    citations = re.findall(citation_pattern, article.draft)
    logger.info(f"✓ Citations: {len(citations)} [[n]](url) style")

    # Step 3: Humanizer (preservation test)
    logger.info("\n" + "=" * 60)
    logger.info("STEP 3: HUMANIZER (Preservation Test)")
    logger.info("=" * 60)

    humanizer = HumanizerAgent(config)
    humanizer_result = await humanizer.run(article)

    if not humanizer_result.success:
        logger.error(f"Humanizer failed: {humanizer_result.error}")
        return False

    final_content = humanizer_result.data.get("final_content")

    # Check preservation
    final_blockquote_count = count_blockquotes(final_content)
    final_entity_links = count_entity_links(final_content)
    final_citations = re.findall(citation_pattern, final_content)

    logger.info(f"✓ Humanizer complete: {len(final_content.split())} words")
    logger.info(f"✓ Blockquotes preserved: {final_blockquote_count} (was {blockquote_count})")
    logger.info(f"✓ Entity links preserved: {final_entity_links['total']} (was {entity_links['total']})")
    logger.info(f"✓ Citations preserved: {len(final_citations)} (was {len(citations)})")

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("EVIDENCE & QUOTES TEST SUMMARY")
    logger.info("=" * 60)

    success = (
        structured_quotes > 0 and
        blockquote_count >= 2 and  # At least 2 blockquotes
        entity_links['total'] >= 3 and  # At least 3 entity links
        final_blockquote_count >= blockquote_count * 0.8 and  # 80%+ preserved
        final_entity_links['total'] >= entity_links['total'] * 0.8  # 80%+ preserved
    )

    if success:
        logger.info("✅ ALL TESTS PASSED!")
        logger.info(f"  - Research: {structured_quotes} structured quotes extracted")
        logger.info(f"  - Writer: {blockquote_count} blockquotes formatted")
        logger.info(f"  - Writer: {entity_links['total']} entity hyperlinks added")
        logger.info(f"  - Writer: {len(citations)} citations included")
        logger.info(f"  - Humanizer: {final_blockquote_count} blockquotes preserved")
        logger.info(f"  - Humanizer: {final_entity_links['total']} entity links preserved")
    else:
        logger.error("❌ TESTS FAILED")
        logger.error(f"  - Structured quotes: {structured_quotes} (need > 0)")
        logger.error(f"  - Blockquotes in draft: {blockquote_count} (need >= 2)")
        logger.error(f"  - Entity links in draft: {entity_links['total']} (need >= 3)")
        logger.error(f"  - Blockquotes preserved: {final_blockquote_count} (need >= 80%)")
        logger.error(f"  - Entity links preserved: {final_entity_links['total']} (need >= 80%)")

    # Save test output
    output_file = Path(__file__).parent / "test_evidence_quotes_output.md"
    with open(output_file, 'w') as f:
        f.write(final_content)
    logger.info(f"\n📝 Full article saved to: {output_file}")

    return success


if __name__ == "__main__":
    result = asyncio.run(test_evidence_quotes_flow())
    sys.exit(0 if result else 1)
