"""
Test script for MediaAgent image generation with OpenRouter Gemini
"""

import asyncio
import logging
import os
import sys
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from agents.media import MediaAgent

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class MockArticle:
    """Mock article object for testing"""
    def __init__(self, title, draft=None, research=None):
        self.title = title
        self.draft = draft or ""
        self.research = research or {}


async def test_image_generation():
    """Test image generation with a simple article"""

    # Load environment variables
    load_dotenv()
    google_api_key = os.getenv("GOOGLE_API_KEY")

    if not google_api_key:
        logger.error("GOOGLE_API_KEY not found in environment")
        return

    # Create agent
    config = {
        "google_api_key": google_api_key,
        "output_dir": "generated_images"
    }

    agent = MediaAgent(config)

    # Create test article
    article = MockArticle(
        title="Mobile Game Monetization Strategies for 2025",
        draft="This article covers the latest trends in mobile game monetization...",
        research={}
    )

    logger.info(f"Testing image generation for: {article.title}")

    # Generate image
    result = await agent.run(article)

    if result.success:
        logger.info("✓ Image generation successful!")
        logger.info(f"  Image path: {result.data.get('header_image_path')}")
        logger.info(f"  Image URL: {result.data.get('image_url')}")
        logger.info(f"  Prompt used: {result.data.get('image_prompt')[:200]}...")

        # Check if file exists
        image_path = result.data.get('header_image_path')
        if image_path and os.path.exists(image_path):
            file_size = os.path.getsize(image_path)
            logger.info(f"  File size: {file_size:,} bytes")
        else:
            logger.warning("  Image file not found on disk")
    else:
        logger.error(f"✗ Image generation failed: {result.error}")

    return result


if __name__ == "__main__":
    result = asyncio.run(test_image_generation())

    if result and result.success:
        print("\n" + "="*60)
        print("TEST PASSED: Image generated successfully")
        print("="*60)
    else:
        print("\n" + "="*60)
        print("TEST FAILED: Image generation unsuccessful")
        print("="*60)
        sys.exit(1)
