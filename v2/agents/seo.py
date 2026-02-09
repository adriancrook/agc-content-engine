"""
SEOAgent for v2 - Simplified from v1
Optimizes article for search engines
"""

import json
import logging
import re
import time
from typing import Dict

import requests

from .base import BaseAgent, AgentResult

logger = logging.getLogger(__name__)


class SEOAgent(BaseAgent):
    """
    SEO optimizer using local LLM
    Generates meta description, optimizes content
    """

    def __init__(self, config: Dict = None):
        super().__init__(config)
        self.ollama_url = config.get("ollama_url", "http://localhost:11434") if config else "http://localhost:11434"
        self.model = config.get("model", "qwen2.5:14b") if config else "qwen2.5:14b"

    async def run(self, article) -> AgentResult:
        """
        Optimize article for SEO
        """
        start_time = time.time()

        draft = article.draft
        research = article.research

        if not draft:
            return AgentResult(
                success=False,
                data={},
                error="No draft content found"
            )

        # Get primary keyword from research
        primary_keyword = article.title  # Default to title
        if research:
            gaps = research.get("competitor_gaps", [])
            if gaps:
                primary_keyword = gaps[0]  # Use first gap as keyword

        logger.info(f"SEO optimizing for keyword: {primary_keyword}")

        try:
            # Step 1: Generate meta description
            meta_description = self._generate_meta_description(draft, primary_keyword)

            # Step 2: Calculate SEO score
            seo_score = self._calculate_seo_score(draft, primary_keyword)

            # Step 3: Generate suggestions
            suggestions = self._generate_suggestions(draft, primary_keyword, seo_score)

            logger.info(f"SEO complete: score {seo_score}/100")

            # Success if score >= 70
            success = seo_score >= 70

            return AgentResult(
                success=success,
                data={
                    "seo": {
                        "primary_keyword": primary_keyword,
                        "meta_description": meta_description,
                        "seo_score": seo_score,
                        "suggestions": suggestions,
                        "keyword_density": self._calculate_keyword_density(draft, primary_keyword)
                    }
                },
                cost=0.0,
                tokens=0,
                error=None if success else f"Low SEO score: {seo_score}/100"
            )

        except Exception as e:
            logger.error(f"SEO optimization failed: {e}")
            return AgentResult(
                success=False,
                data={},
                error=str(e)
            )

    def _generate_meta_description(self, draft: str, keyword: str) -> str:
        """Generate SEO meta description"""

        # Extract first few paragraphs
        paragraphs = []
        for line in draft.split('\n'):
            if line and not line.startswith('#'):
                paragraphs.append(line)
            if len(paragraphs) >= 3:
                break

        content_preview = ' '.join(paragraphs)[:500]

        prompt = f"""Write a compelling meta description for this article.

Primary Keyword: {keyword}

Article Preview:
{content_preview}

Requirements:
- 150-160 characters
- Include primary keyword naturally
- Compelling hook to increase click-through rate
- Action-oriented

Write ONLY the meta description (no quotes, no explanation)."""

        try:
            response = self._call_ollama(prompt)
            meta = response.strip().strip('"')

            # Truncate to 160 chars
            if len(meta) > 160:
                meta = meta[:157] + "..."

            return meta

        except Exception as e:
            logger.warning(f"Failed to generate meta description: {e}")
            return f"Learn about {keyword} in this comprehensive guide."

    def _calculate_seo_score(self, draft: str, keyword: str) -> int:
        """Calculate SEO score 0-100"""
        score = 0

        # Title includes keyword (+25 points)
        title_match = re.search(r'^# (.+)$', draft, re.MULTILINE)
        if title_match and keyword.lower() in title_match.group(1).lower():
            score += 25

        # First paragraph includes keyword (+20 points)
        paragraphs = draft.split('\n\n')
        for p in paragraphs[:3]:
            if not p.startswith('#') and keyword.lower() in p.lower():
                score += 20
                break

        # Has H2 headers (+15 points)
        h2_count = draft.count('\n## ')
        if h2_count >= 4:
            score += 15

        # Good length (+15 points)
        word_count = len(draft.split())
        if word_count >= 2000:
            score += 15

        # Keyword density is good (+15 points)
        density = self._calculate_keyword_density(draft, keyword)
        if 0.5 <= density <= 2.5:
            score += 15

        # Has internal structure (+10 points)
        if '\n### ' in draft:  # Has H3 subsections
            score += 10

        return min(score, 100)

    def _calculate_keyword_density(self, text: str, keyword: str) -> float:
        """Calculate keyword density as percentage"""
        text_lower = text.lower()
        keyword_lower = keyword.lower()

        keyword_count = text_lower.count(keyword_lower)
        total_words = len(text.split())

        if total_words == 0:
            return 0.0

        return (keyword_count / total_words) * 100

    def _generate_suggestions(self, draft: str, keyword: str, score: int) -> list:
        """Generate SEO improvement suggestions"""
        suggestions = []

        if score < 70:
            suggestions.append("Overall SEO score needs improvement")

        # Check title
        title_match = re.search(r'^# (.+)$', draft, re.MULTILINE)
        if not title_match or keyword.lower() not in title_match.group(1).lower():
            suggestions.append(f"Add '{keyword}' to article title")

        # Check density
        density = self._calculate_keyword_density(draft, keyword)
        if density < 0.5:
            suggestions.append(f"Increase keyword density (currently {density:.1f}%)")
        elif density > 2.5:
            suggestions.append(f"Reduce keyword density (currently {density:.1f}%)")

        # Check length
        word_count = len(draft.split())
        if word_count < 2000:
            suggestions.append(f"Increase content length (currently {word_count} words)")

        # Check headers
        h2_count = draft.count('\n## ')
        if h2_count < 4:
            suggestions.append("Add more H2 section headers")

        return suggestions

    def _call_ollama(self, prompt: str) -> str:
        """Call local Ollama model"""
        url = f"{self.ollama_url}/api/generate"

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.3,
                "num_predict": 512,
            }
        }

        try:
            response = requests.post(url, json=payload, timeout=120)
            response.raise_for_status()
            result = response.json()
            return result.get("response", "")
        except Exception as e:
            logger.error(f"Ollama call failed: {e}")
            raise
