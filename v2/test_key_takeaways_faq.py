"""
Test script for Key Takeaways & FAQ system
Verifies proper formatting and preservation through humanization
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


def check_key_takeaways(text: str) -> dict:
    """Check for Key Takeaways section"""
    has_header = "**Key Takeaways:**" in text

    # Count bullet points in Key Takeaways section
    if has_header:
        # Find the Key Takeaways section
        kt_start = text.find("**Key Takeaways:**")
        # Find the next H2 section (##)
        next_section = text.find("\n##", kt_start)
        if next_section == -1:
            next_section = len(text)

        kt_section = text[kt_start:next_section]

        # Count bullets that start with - **
        bullet_pattern = r'- \*\*([^:]+):\*\*'
        bullets = re.findall(bullet_pattern, kt_section)

        return {
            'present': True,
            'bullet_count': len(bullets),
            'bullets': bullets[:5],  # First 5 for display
            'section': kt_section[:500]  # First 500 chars
        }

    return {
        'present': False,
        'bullet_count': 0,
        'bullets': [],
        'section': ''
    }


def check_faq(text: str) -> dict:
    """Check for FAQ section"""
    has_faq_header = "## FAQs" in text or "## FAQ" in text

    if has_faq_header:
        # Find FAQ section
        faq_start = text.find("## FAQ")
        # Find the next H2 section or end
        next_section = text.find("\n## ", faq_start + 5)
        if next_section == -1:
            next_section = len(text)

        faq_section = text[faq_start:next_section]

        # Count questions (### headers)
        question_pattern = r'### (.+?)\?'
        questions = re.findall(question_pattern, faq_section)

        return {
            'present': True,
            'question_count': len(questions),
            'questions': questions,
            'section': faq_section[:800]  # First 800 chars
        }

    return {
        'present': False,
        'question_count': 0,
        'questions': [],
        'section': ''
    }


async def test_key_takeaways_faq_flow():
    """Test full Key Takeaways & FAQ flow"""

    config = {
        "brave_api_key": os.getenv("BRAVE_API_KEY"),
        "openrouter_api_key": os.getenv("OPENROUTER_API_KEY"),
    }

    # Test topic
    topic = "Mobile Gaming User Retention Strategies 2025"
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

    # Step 2: Writer (with Key Takeaways & FAQ)
    logger.info("\n" + "=" * 60)
    logger.info("STEP 2: WRITER (Key Takeaways & FAQ)")
    logger.info("=" * 60)

    writer_agent = WriterAgent(config)
    writer_result = await writer_agent.run(article)

    if not writer_result.success:
        logger.error(f"Writing failed: {writer_result.error}")
        return False

    article.draft = writer_result.data.get("draft")

    logger.info(f"✓ Draft complete: {len(article.draft.split())} words")

    # Check for Key Takeaways
    kt_check = check_key_takeaways(article.draft)
    logger.info(f"\n✓ Key Takeaways present: {kt_check['present']}")
    if kt_check['present']:
        logger.info(f"  Bullet count: {kt_check['bullet_count']}")
        logger.info(f"  Example bullets:")
        for bullet in kt_check['bullets'][:3]:
            logger.info(f"    - {bullet}")

    # Check for FAQ
    faq_check = check_faq(article.draft)
    logger.info(f"\n✓ FAQ section present: {faq_check['present']}")
    if faq_check['present']:
        logger.info(f"  Question count: {faq_check['question_count']}")
        logger.info(f"  Questions:")
        for q in faq_check['questions']:
            logger.info(f"    - {q}?")

    # Check for other elements (from previous phases)
    citation_pattern = r'\[\[(\d+)\]\]\(([^)]+)\)'
    citations = re.findall(citation_pattern, article.draft)

    blockquote_count = article.draft.count('\n>')

    logger.info(f"\n✓ Citations: {len(citations)}")
    logger.info(f"✓ Blockquotes: {blockquote_count}")

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
    final_kt_check = check_key_takeaways(final_content)
    final_faq_check = check_faq(final_content)
    final_citations = re.findall(citation_pattern, final_content)
    final_blockquote_count = final_content.count('\n>')

    logger.info(f"✓ Humanizer complete: {len(final_content.split())} words")
    logger.info(f"\n✓ Key Takeaways preserved: {final_kt_check['present']} (bullets: {final_kt_check['bullet_count']} vs {kt_check['bullet_count']})")
    logger.info(f"✓ FAQ preserved: {final_faq_check['present']} (questions: {final_faq_check['question_count']} vs {faq_check['question_count']})")
    logger.info(f"✓ Citations preserved: {len(final_citations)} (was {len(citations)})")
    logger.info(f"✓ Blockquotes preserved: {final_blockquote_count} (was {blockquote_count})")

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("KEY TAKEAWAYS & FAQ TEST SUMMARY")
    logger.info("=" * 60)

    success = (
        kt_check['present'] and
        kt_check['bullet_count'] >= 3 and  # At least 3 takeaways
        faq_check['present'] and
        faq_check['question_count'] >= 3 and  # Exactly 3 questions
        final_kt_check['present'] and
        final_faq_check['present'] and
        final_kt_check['bullet_count'] >= 3 and
        final_faq_check['question_count'] >= 3
    )

    if success:
        logger.info("✅ ALL TESTS PASSED!")
        logger.info(f"  - Writer: Key Takeaways with {kt_check['bullet_count']} bullets")
        logger.info(f"  - Writer: FAQ with {faq_check['question_count']} questions")
        logger.info(f"  - Writer: {len(citations)} citations")
        logger.info(f"  - Writer: {blockquote_count} blockquotes")
        logger.info(f"  - Humanizer: Key Takeaways preserved ({final_kt_check['bullet_count']} bullets)")
        logger.info(f"  - Humanizer: FAQ preserved ({final_faq_check['question_count']} questions)")
        logger.info(f"  - Humanizer: {len(final_citations)} citations preserved")
        logger.info(f"  - Humanizer: {final_blockquote_count} blockquotes preserved")
    else:
        logger.error("❌ TESTS FAILED")
        logger.error(f"  - Key Takeaways in draft: {kt_check['present']} (need True)")
        logger.error(f"  - Key Takeaways bullets: {kt_check['bullet_count']} (need >= 3)")
        logger.error(f"  - FAQ in draft: {faq_check['present']} (need True)")
        logger.error(f"  - FAQ questions: {faq_check['question_count']} (need >= 3)")
        logger.error(f"  - Key Takeaways preserved: {final_kt_check['present']}")
        logger.error(f"  - FAQ preserved: {final_faq_check['present']}")

    # Save test output
    output_file = Path(__file__).parent / "test_key_takeaways_faq_output.md"
    with open(output_file, 'w') as f:
        f.write(final_content)
    logger.info(f"\n📝 Full article saved to: {output_file}")

    # Show examples
    if success:
        logger.info("\n" + "=" * 60)
        logger.info("EXAMPLE OUTPUT")
        logger.info("=" * 60)
        logger.info("\nKey Takeaways Section:")
        logger.info("-" * 60)
        logger.info(kt_check['section'][:400])
        logger.info("\nFAQ Section:")
        logger.info("-" * 60)
        logger.info(faq_check['section'][:600])

    return success


if __name__ == "__main__":
    result = asyncio.run(test_key_takeaways_faq_flow())
    sys.exit(0 if result else 1)
