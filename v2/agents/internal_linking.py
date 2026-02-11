"""
InternalLinkingAgent for v2
Adds internal links to existing adriancrook.com articles
"""

import asyncio
import logging
import re
from typing import Dict, List, Optional

from .base import BaseAgent, AgentResult
from data.curated_articles import find_articles_by_topic, get_curated_articles

logger = logging.getLogger(__name__)


class InternalLinkingAgent(BaseAgent):
    """
    Internal linking agent that suggests and inserts relevant internal links
    """

    def __init__(self, config: Dict = None):
        super().__init__(config)
        self.min_links = config.get("min_internal_links", 2) if config else 2
        self.max_links = config.get("max_internal_links", 5) if config else 5

    async def run(self, article) -> AgentResult:
        """
        Add internal links to article content
        """
        logger.info(f"InternalLinkingAgent.run() called for article: {article.id[:8]}")

        try:
            draft = article.final_content if hasattr(article, 'final_content') else article.draft

            if not draft:
                logger.error("No draft content found")
                return AgentResult(
                    success=False,
                    data={},
                    error="No draft content found"
                )

            topic = article.title
            logger.info(f"Finding internal links for: {topic} (length: {len(draft)} chars)")

            # Extract key topics from the article
            logger.info("Extracting topics...")
            topics = self._extract_topics(topic, draft)
            logger.info(f"Extracted {len(topics)} topics: {topics[:5]}")

            # Find relevant articles
            logger.info("Finding relevant articles...")
            relevant_articles = self._find_relevant_articles(topics)
            logger.info(f"Found {len(relevant_articles)} relevant articles")

            if len(relevant_articles) < self.min_links:
                logger.warning(f"Only found {len(relevant_articles)} relevant articles (need {self.min_links})")

            # Insert links with timeout protection
            logger.info("Inserting internal links...")
            try:
                updated_draft = await asyncio.wait_for(
                    asyncio.to_thread(self._insert_internal_links, draft, relevant_articles),
                    timeout=30.0  # 30 second timeout
                )
                logger.info("Internal link insertion completed")
            except asyncio.TimeoutError:
                logger.error("Internal link insertion timed out after 30 seconds")
                return AgentResult(
                    success=False,
                    data={},
                    error="Internal link insertion timed out"
                )

            # Count inserted links
            original_links = self._count_internal_links(draft)
            final_links = self._count_internal_links(updated_draft)
            link_count = final_links - original_links

            logger.info(f"Added {link_count} internal links (original: {original_links}, final: {final_links})")

            success = link_count >= self.min_links

            return AgentResult(
                success=success,
                data={
                    "final_content": updated_draft,  # Update final_content with links
                    "internal_links_added": link_count,
                    "suggested_articles": [{"title": a['title'], "url": a['url']} for a in relevant_articles]
                },
                cost=0.0,  # No API cost
                tokens=0,
                error=None if success else f"Only added {link_count} links (need {self.min_links})"
            )

        except Exception as e:
            logger.error(f"Internal linking failed: {e}", exc_info=True)
            return AgentResult(
                success=False,
                data={},
                error=str(e)
            )

    def _extract_topics(self, title: str, draft: str) -> List[str]:
        """Extract key topics from title and content"""
        # Common mobile gaming topics
        topic_keywords = [
            "monetization", "iap", "in-app purchase", "ads", "advertising",
            "retention", "engagement", "churn", "onboarding", "ftue",
            "user acquisition", "ua", "marketing", "aso",
            "analytics", "kpis", "metrics", "arpu", "ltv",
            "game design", "core loop", "progression", "economy",
            "live ops", "events", "battle pass",
            "f2p", "free-to-play", "gacha",
            "social", "multiplayer", "community",
            "cross-platform", "cloud gaming",
            "trends", "market", "web3", "nft"
        ]

        text = (title + " " + draft[:3000]).lower()  # First 3000 chars
        found_topics = []

        for keyword in topic_keywords:
            if keyword in text:
                found_topics.append(keyword)

        # Also extract from title words
        title_words = [w for w in title.lower().split() if len(w) > 4]
        found_topics.extend(title_words[:5])  # Top 5 title words

        return list(set(found_topics))  # Deduplicate

    def _find_relevant_articles(self, topics: List[str]) -> List[Dict]:
        """Find relevant articles from curated list"""
        # Combine results from multiple topic searches
        all_results = {}  # Use dict to deduplicate by URL

        for topic in topics[:10]:  # Limit topics to search
            results = find_articles_by_topic(topic, max_results=3)
            for article in results:
                url = article['url']
                if url not in all_results:
                    all_results[url] = article

        # Return top matches
        articles_list = list(all_results.values())
        return articles_list[:self.max_links]

    def _insert_internal_links(self, draft: str, articles: List[Dict]) -> str:
        """Insert internal links naturally into the draft"""
        if not articles:
            return draft

        updated_draft = draft

        # Cache to track what we've already tried to avoid redundant regex
        attempted_patterns = set()

        # For each article, try to find a natural place to link
        for article in articles[:self.max_links]:
            title = article['title']
            url = article['url']

            # Extract anchor text from title (use first 3-5 words)
            words = title.split()
            anchor_candidates = [
                " ".join(words[:3]),
                " ".join(words[:4]),
                " ".join(words[:5]),
            ]

            # Try to find and replace first occurrence
            linked = False
            for anchor in anchor_candidates:
                if len(anchor) < 10:  # Skip very short anchors
                    continue

                anchor_lower = anchor.lower()
                if anchor_lower in attempted_patterns:
                    continue
                attempted_patterns.add(anchor_lower)

                # Simple case-insensitive search first (no regex)
                if anchor_lower not in updated_draft.lower():
                    continue

                # Only use regex if we found the text
                anchor_pattern = re.escape(anchor)
                try:
                    # Check if this text appears and isn't already linked
                    if re.search(r'\b' + anchor_pattern + r'\b', updated_draft, re.IGNORECASE):
                        # Make sure it's not already a link (simpler check)
                        if f'[{anchor}]' not in updated_draft and f']{anchor}' not in updated_draft.lower():
                            # Replace first occurrence
                            updated_draft = re.sub(
                                r'\b(' + anchor_pattern + r')\b',
                                f'[\\1]({url})',
                                updated_draft,
                                count=1,
                                flags=re.IGNORECASE
                            )
                            linked = True
                            logger.info(f"Linked: {anchor} -> {url}")
                            break
                except Exception as e:
                    logger.warning(f"Regex error for anchor '{anchor}': {e}")
                    continue

            # If no natural anchor found, try topic-based keywords (limit to 2 topics)
            if not linked:
                for topic in article.get('topics', [])[:2]:
                    if len(topic) < 5:  # Skip short topics
                        continue

                    topic_lower = topic.lower()
                    if topic_lower in attempted_patterns:
                        continue
                    attempted_patterns.add(topic_lower)

                    # Simple search first
                    if topic_lower not in updated_draft.lower():
                        continue

                    topic_pattern = re.escape(topic)
                    try:
                        if re.search(r'\b' + topic_pattern + r'\b', updated_draft, re.IGNORECASE):
                            # Check not already linked
                            if f'[{topic}]' not in updated_draft and f']{topic}' not in updated_draft.lower():
                                updated_draft = re.sub(
                                    r'\b(' + topic_pattern + r')\b',
                                    f'[\\1]({url})',
                                    updated_draft,
                                    count=1,
                                    flags=re.IGNORECASE
                                )
                                logger.info(f"Linked (topic): {topic} -> {url}")
                                break
                    except Exception as e:
                        logger.warning(f"Regex error for topic '{topic}': {e}")
                        continue

        return updated_draft

    def _count_internal_links(self, text: str) -> int:
        """Count internal links in text (adriancrook.com links)"""
        pattern = r'\[([^\]]+)\]\((https://adriancrook\.com/[^\)]+)\)'
        matches = re.findall(pattern, text)
        return len(matches)


# Export
__all__ = ['InternalLinkingAgent']
