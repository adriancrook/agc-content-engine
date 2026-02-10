"""
WordPressFormatterAgent for v2
Formats articles for WordPress with SEO metadata
"""

import logging
from typing import Dict

from .base import BaseAgent, AgentResult
from formatters.wordpress import WordPressFormatter

logger = logging.getLogger(__name__)


class WordPressFormatterAgent(BaseAgent):
    """
    WordPress formatting agent
    Generates SEO metadata and WordPress-ready output
    """

    def __init__(self, config: Dict = None):
        super().__init__(config)
        self.formatter = WordPressFormatter(config)

    async def run(self, article) -> AgentResult:
        """
        Format article for WordPress
        """
        logger.info(f"Formatting article for WordPress: {article.title}")

        try:
            # Prepare article data
            article_data = {
                "title": article.title,
                "final_content": article.final_content if hasattr(article, 'final_content') and article.final_content else article.draft,
                "research": article.research if hasattr(article, 'research') else {},
                "seo": article.seo if hasattr(article, 'seo') else {},
                "media": article.media if hasattr(article, 'media') else {},
            }

            # Format for WordPress
            result = self.formatter.format(article_data)

            # Log validation issues
            if result["validation_issues"]:
                logger.warning(f"Validation issues: {len(result['validation_issues'])}")
                for issue in result["validation_issues"]:
                    logger.warning(f"  - {issue}")

            logger.info(f"WordPress formatting complete. Export ready: {result['export_ready']}")

            return AgentResult(
                success=True,
                data={
                    "wordpress_content": result["wordpress_content"],
                    "wordpress_metadata": result["metadata"],
                    "wordpress_export_ready": result["export_ready"],
                    "wordpress_validation_issues": result["validation_issues"],
                },
                cost=0.0,  # No API cost
                tokens=0
            )

        except Exception as e:
            logger.error(f"WordPress formatting failed: {e}")
            return AgentResult(
                success=False,
                data={},
                error=str(e)
            )


# Export
__all__ = ['WordPressFormatterAgent']
