"""
Topic Discovery Agent - Finds high-value article opportunities.

Researches:
- Trending topics in the niche
- Keyword opportunities (volume vs competition)
- Competitor content gaps
- Seasonal/timely topics
- Evergreen opportunities

Model: Claude 3.5 Sonnet via OpenRouter
"""

import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Any

import requests

logger = logging.getLogger(__name__)


@dataclass
class TopicIdea:
    """A potential article topic."""
    title: str
    primary_keyword: str
    secondary_keywords: List[str]
    search_volume_estimate: str  # "high", "medium", "low"
    competition_level: str  # "high", "medium", "low"
    opportunity_score: float  # 0-100
    reasoning: str
    topic_type: str  # "trending", "evergreen", "seasonal", "gap"
    urgency: str  # "high", "medium", "low"

    def to_dict(self) -> Dict:
        return {
            "title": self.title,
            "primary_keyword": self.primary_keyword,
            "secondary_keywords": self.secondary_keywords,
            "search_volume_estimate": self.search_volume_estimate,
            "competition_level": self.competition_level,
            "opportunity_score": self.opportunity_score,
            "reasoning": self.reasoning,
            "topic_type": self.topic_type,
            "urgency": self.urgency,
        }


class TopicDiscoveryAgent:
    """
    Topic discovery agent that finds article opportunities.

    Uses Brave Search + Claude to identify high-value topics.
    Note: This agent doesn't follow BaseAgent pattern since it doesn't operate on articles.
    """

    def __init__(
        self,
        brave_api_key: str,
        openrouter_api_key: str,
        niche: str = "mobile gaming, game design, and game monetization",
        blog_url: str = "https://adriancrook.com",
    ):
        self.brave_api_key = brave_api_key
        self.openrouter_api_key = openrouter_api_key
        self.niche = niche
        self.blog_url = blog_url

    async def discover_topics(
        self,
        existing_articles: List[str] = None,
        focus_areas: List[str] = None,
        max_topics: int = 10
    ) -> Dict[str, Any]:
        """
        Discover article topic opportunities.

        Args:
            existing_articles: List[str] - Titles of existing blog articles
            focus_areas: List[str] - Specific areas to focus on
            max_topics: int - Maximum topics to return (default 10)

        Returns:
            Dict with topics list and metadata
        """
        start_time = time.time()

        existing_articles = existing_articles or []
        focus_areas = focus_areas or [
            "mobile game monetization",
            "free-to-play game design",
            "gacha mechanics",
            "battle pass design",
            "game economy",
            "player retention strategies",
            "mobile game marketing",
            "live ops and events",
            "mobile gaming psychology",
            "family gaming",
        ]

        logger.info(f"🔍 Discovering topics for: {self.niche}")
        logger.info(f"   Focus areas: {', '.join(focus_areas[:3])}...")

        all_topics = []

        # Step 1: Find trending topics
        trending = await self._find_trending_topics(focus_areas)
        all_topics.extend(trending)
        logger.info(f"   ✓ Found {len(trending)} trending topics")

        # Step 2: Find evergreen opportunities
        evergreen = await self._find_evergreen_topics(focus_areas)
        all_topics.extend(evergreen)
        logger.info(f"   ✓ Found {len(evergreen)} evergreen topics")

        # Step 3: Analyze competitor gaps
        gaps = await self._find_competitor_gaps(focus_areas, existing_articles)
        all_topics.extend(gaps)
        logger.info(f"   ✓ Found {len(gaps)} competitor gap topics")

        # Step 4: Find seasonal/timely topics
        seasonal = await self._find_seasonal_topics(focus_areas)
        all_topics.extend(seasonal)
        logger.info(f"   ✓ Found {len(seasonal)} seasonal topics")

        # Step 5: Filter out topics we already have
        filtered_topics = self._filter_existing(all_topics, existing_articles)
        logger.info(f"   ✓ Filtered to {len(filtered_topics)} unique topics")

        # Step 6: Score and rank topics
        scored_topics = self._score_topics(filtered_topics)

        # Step 7: Select top topics
        top_topics = sorted(scored_topics, key=lambda x: x.opportunity_score, reverse=True)[:max_topics]

        duration = time.time() - start_time

        logger.info(f"✓ Topic discovery complete in {duration:.1f}s - {len(top_topics)} topics")

        return {
            "topics": [t.to_dict() for t in top_topics],
            "total_discovered": len(all_topics),
            "after_filtering": len(filtered_topics),
            "niche": self.niche,
            "focus_areas": focus_areas,
            "duration_seconds": duration,
            "success": len(top_topics) >= 5,
        }

    def _web_search(self, query: str, count: int = 10, freshness: str = "pm") -> List[Dict]:
        """Search web using Brave API."""
        url = "https://api.search.brave.com/res/v1/web/search"

        headers = {
            "Accept": "application/json",
            "X-Subscription-Token": self.brave_api_key,
        }

        params = {
            "q": query,
            "count": count,
            "freshness": freshness,  # pm = past month, pw = past week, py = past year
        }

        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            results = []
            for r in data.get("web", {}).get("results", []):
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "description": r.get("description", ""),
                })
            return results
        except Exception as e:
            logger.error(f"Web search failed: {e}")
            return []

    async def _call_claude(self, prompt: str) -> str:
        """Call Claude via OpenRouter."""
        url = "https://openrouter.ai/api/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {self.openrouter_api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": "anthropic/claude-3.5-sonnet",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"Claude API call failed: {e}")
            return ""

    async def _find_trending_topics(self, focus_areas: List[str]) -> List[TopicIdea]:
        """Find currently trending topics."""
        topics = []

        for area in focus_areas[:3]:  # Limit to avoid too many API calls
            # Search for recent news/articles
            results = self._web_search(f"{area} 2025 trends news", count=10, freshness="pw")

            if not results:
                continue

            # Use Claude to extract topic ideas
            prompt = f"""Analyze these recent articles about "{area}" and suggest 2-3 article topics that would perform well for a blog focused on {self.niche}.

Recent articles:
{json.dumps([r['title'] for r in results], indent=2)}

For each topic, provide:
- A compelling article title (actionable, specific, benefit-driven)
- Primary keyword (2-4 words)
- 3-5 secondary keywords
- Why this topic is timely and valuable

Respond ONLY with valid JSON (no markdown, no explanations):
{{
    "topics": [
        {{
            "title": "Article Title",
            "primary_keyword": "main keyword",
            "secondary_keywords": ["kw1", "kw2", "kw3"],
            "reasoning": "Why this is timely and valuable"
        }}
    ]
}}"""

            try:
                response = await self._call_claude(prompt)

                # Clean up markdown code blocks if present
                if "```json" in response:
                    response = response.split("```json")[1].split("```")[0]
                elif "```" in response:
                    response = response.split("```")[1].split("```")[0]

                data = json.loads(response.strip())

                for t in data.get("topics", []):
                    topics.append(TopicIdea(
                        title=t.get("title", ""),
                        primary_keyword=t.get("primary_keyword", ""),
                        secondary_keywords=t.get("secondary_keywords", []),
                        search_volume_estimate="medium",
                        competition_level="medium",
                        opportunity_score=70,
                        reasoning=t.get("reasoning", ""),
                        topic_type="trending",
                        urgency="high",
                    ))
            except Exception as e:
                logger.warning(f"Failed to parse trending topics for '{area}': {e}")

        return topics

    async def _find_evergreen_topics(self, focus_areas: List[str]) -> List[TopicIdea]:
        """Find evergreen content opportunities."""
        topics = []

        prompt = f"""Suggest 5 evergreen article topics for a blog about {self.niche}.

Focus areas: {', '.join(focus_areas)}

Evergreen topics should:
- Be relevant year-round
- Have consistent search interest
- Provide lasting value
- Be comprehensive guides or explanations

For each topic, provide:
- A compelling article title (include "Guide", "How to", "Complete", etc.)
- Primary keyword (2-4 words, good search volume)
- 3-5 secondary keywords
- Why this is a good evergreen topic

Respond ONLY with valid JSON (no markdown, no explanations):
{{
    "topics": [
        {{
            "title": "Article Title",
            "primary_keyword": "main keyword",
            "secondary_keywords": ["kw1", "kw2", "kw3"],
            "reasoning": "Why this is good evergreen content"
        }}
    ]
}}"""

        try:
            response = await self._call_claude(prompt)

            # Clean up markdown code blocks
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]

            data = json.loads(response.strip())

            for t in data.get("topics", []):
                topics.append(TopicIdea(
                    title=t.get("title", ""),
                    primary_keyword=t.get("primary_keyword", ""),
                    secondary_keywords=t.get("secondary_keywords", []),
                    search_volume_estimate="high",
                    competition_level="medium",
                    opportunity_score=75,
                    reasoning=t.get("reasoning", ""),
                    topic_type="evergreen",
                    urgency="low",
                ))
        except Exception as e:
            logger.warning(f"Failed to parse evergreen topics: {e}")

        return topics

    async def _find_competitor_gaps(self, focus_areas: List[str], existing_articles: List[str]) -> List[TopicIdea]:
        """Find topics competitors cover that we don't."""
        topics = []

        # Search for top competitor content
        results = self._web_search(f"best {self.niche} articles guides", count=20, freshness="py")

        if not results:
            return topics

        prompt = f"""Analyze competitor articles and identify content gaps for a blog about {self.niche}.

Competitor articles:
{json.dumps([r['title'] for r in results[:15]], indent=2)}

Our existing articles:
{json.dumps(existing_articles[:20] if existing_articles else ['(no existing articles)'], indent=2)}

Identify 3-5 topics that competitors cover well but we're missing.
Focus on: {', '.join(focus_areas)}

For each gap, provide:
- A better article title than competitors
- Primary keyword
- 3-5 secondary keywords
- What angle we should take

Respond ONLY with valid JSON (no markdown, no explanations):
{{
    "topics": [
        {{
            "title": "Article Title",
            "primary_keyword": "main keyword",
            "secondary_keywords": ["kw1", "kw2", "kw3"],
            "reasoning": "What gap this fills and our angle"
        }}
    ]
}}"""

        try:
            response = await self._call_claude(prompt)

            # Clean up markdown code blocks
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]

            data = json.loads(response.strip())

            for t in data.get("topics", []):
                topics.append(TopicIdea(
                    title=t.get("title", ""),
                    primary_keyword=t.get("primary_keyword", ""),
                    secondary_keywords=t.get("secondary_keywords", []),
                    search_volume_estimate="high",
                    competition_level="high",
                    opportunity_score=80,
                    reasoning=t.get("reasoning", ""),
                    topic_type="gap",
                    urgency="medium",
                ))
        except Exception as e:
            logger.warning(f"Failed to parse competitor gaps: {e}")

        return topics

    async def _find_seasonal_topics(self, focus_areas: List[str]) -> List[TopicIdea]:
        """Find seasonal/timely topics."""
        topics = []

        current_month = datetime.now().strftime("%B")
        current_year = datetime.now().year

        prompt = f"""Suggest 3 timely/seasonal article topics for a blog about {self.niche}.

Current date: {current_month} {current_year}

Consider:
- Upcoming game releases
- Industry events (GDC, Game Awards, etc.)
- Seasonal gaming trends
- Annual reports/reviews
- Holiday-related gaming

Focus areas: {', '.join(focus_areas)}

For each topic, provide:
- A timely article title
- Primary keyword
- 3-5 secondary keywords
- Why this is timely NOW

Respond ONLY with valid JSON (no markdown, no explanations):
{{
    "topics": [
        {{
            "title": "Article Title",
            "primary_keyword": "main keyword",
            "secondary_keywords": ["kw1", "kw2", "kw3"],
            "reasoning": "Why this is timely right now"
        }}
    ]
}}"""

        try:
            response = await self._call_claude(prompt)

            # Clean up markdown code blocks
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]

            data = json.loads(response.strip())

            for t in data.get("topics", []):
                topics.append(TopicIdea(
                    title=t.get("title", ""),
                    primary_keyword=t.get("primary_keyword", ""),
                    secondary_keywords=t.get("secondary_keywords", []),
                    search_volume_estimate="medium",
                    competition_level="low",
                    opportunity_score=85,
                    reasoning=t.get("reasoning", ""),
                    topic_type="seasonal",
                    urgency="high",
                ))
        except Exception as e:
            logger.warning(f"Failed to parse seasonal topics: {e}")

        return topics

    def _filter_existing(self, topics: List[TopicIdea], existing_articles: List[str]) -> List[TopicIdea]:
        """Filter out topics too similar to existing articles."""
        if not existing_articles:
            return topics

        existing_lower = [a.lower() for a in existing_articles]
        filtered = []

        for topic in topics:
            title_lower = topic.title.lower()
            keyword_lower = topic.primary_keyword.lower()

            # Check for too-similar titles
            is_duplicate = False
            for existing in existing_lower:
                if keyword_lower in existing or title_lower[:30] in existing:
                    is_duplicate = True
                    break

            if not is_duplicate:
                filtered.append(topic)

        return filtered

    def _score_topics(self, topics: List[TopicIdea]) -> List[TopicIdea]:
        """Score topics based on opportunity."""
        for topic in topics:
            score = 50  # Base score

            # Volume bonus
            if topic.search_volume_estimate == "high":
                score += 20
            elif topic.search_volume_estimate == "medium":
                score += 10

            # Competition penalty
            if topic.competition_level == "high":
                score -= 10
            elif topic.competition_level == "low":
                score += 15

            # Type bonus
            if topic.topic_type == "gap":
                score += 10  # Filling a gap is valuable
            elif topic.topic_type == "trending":
                score += 5
            elif topic.topic_type == "seasonal":
                score += 15  # Timely content

            # Urgency bonus
            if topic.urgency == "high":
                score += 10

            topic.opportunity_score = min(100, max(0, score))

        return topics
