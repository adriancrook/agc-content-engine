"""
SEOAgent for v2 - Cloud-ready version
Optimizes article for search engines using Claude Haiku
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
    SEO optimizer using Claude 3.5 Haiku via OpenRouter
    Generates meta description, optimizes content
    """

    def __init__(self, config: Dict = None):
        super().__init__(config)
        self.openrouter_api_key = config.get("openrouter_api_key") if config else None
        if not self.openrouter_api_key:
            raise ValueError("SEOAgent requires openrouter_api_key in config")

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
            # Step 1: Generate meta description and analyze SEO
            seo_analysis = await self._analyze_seo(draft, primary_keyword)

            # Step 2: Calculate keyword density
            keyword_density = self._calculate_keyword_density(draft, primary_keyword)

            logger.info(f"SEO complete: score {seo_analysis['seo_score']}/100")

            # Success if score >= 35
            success = seo_analysis['seo_score'] >= 35

            # Estimate cost (Claude Haiku: $0.25/M input, $1.25/M output)
            input_tokens = len(draft.split()) * 1.3
            output_tokens = 300
            cost = (input_tokens / 1_000_000 * 0.25) + (output_tokens / 1_000_000 * 1.25)

            return AgentResult(
                success=success,
                data={
                    "seo": {
                        "primary_keyword": primary_keyword,
                        "meta_description": seo_analysis['meta_description'],
                        "seo_score": seo_analysis['seo_score'],
                        "suggestions": seo_analysis['suggestions'],
                        "keyword_density": keyword_density
                    }
                },
                cost=cost,
                tokens=int(input_tokens + output_tokens),
                error=None if success else f"Low SEO score: {seo_analysis['seo_score']}/100"
            )

        except Exception as e:
            logger.error(f"SEO optimization failed: {e}")
            return AgentResult(
                success=False,
                data={},
                error=str(e)
            )

    async def _analyze_seo(self, draft: str, keyword: str) -> Dict:
        """Use Claude to analyze SEO and generate meta description"""

        prompt = f"""You are an SEO expert. Analyze this article and provide SEO optimization recommendations.

PRIMARY KEYWORD: {keyword}

ARTICLE (first 3000 chars):
{draft[:3000]}

Tasks:
1. Write a compelling meta description (150-160 characters) that includes the primary keyword
2. Calculate an SEO score (0-100) based on:
   - Keyword usage in title and headings
   - Content quality and readability
   - Proper heading structure
   - Content length
3. Provide 3-5 actionable suggestions to improve SEO

Respond ONLY with valid JSON (no markdown, no explanations):
{{
    "meta_description": "Compelling 150-160 char description with keyword",
    "seo_score": 75,
    "suggestions": [
        "Add keyword to first paragraph",
        "Include more subheadings",
        "Add internal links"
    ]
}}"""

        try:
            response = await self._call_claude(prompt)

            # Parse JSON
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]

            data = json.loads(response.strip())
            return data

        except Exception as e:
            logger.warning(f"Failed to parse SEO response: {e}")
            return {
                "meta_description": draft[:160],
                "seo_score": 50,
                "suggestions": ["Review keyword placement", "Improve heading structure"]
            }

    def _calculate_keyword_density(self, draft: str, keyword: str) -> float:
        """Calculate keyword density"""
        words = draft.lower().split()
        keyword_lower = keyword.lower()
        keyword_count = words.count(keyword_lower)
        total_words = len(words)

        if total_words == 0:
            return 0.0

        density = (keyword_count / total_words) * 100
        return round(density, 2)

    async def _call_claude(self, prompt: str) -> str:
        """Call Claude Haiku via OpenRouter"""
        url = "https://openrouter.ai/api/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {self.openrouter_api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": "anthropic/claude-3.5-haiku",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"Claude API call failed: {e}")
            raise
