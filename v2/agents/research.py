"""
ResearchAgent for v2 - Cloud-ready version
Gathers web sources and creates research bundle using Claude Haiku
"""

import json
import logging
import re
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Dict, Optional

import requests

from .base import BaseAgent, AgentResult

logger = logging.getLogger(__name__)


@dataclass
class Source:
    """A research source"""
    url: str
    title: str
    snippet: str
    published_date: Optional[str] = None
    key_stats: List[str] = None
    key_quotes: List[str] = None
    relevance_score: float = 0.0

    def to_dict(self) -> Dict:
        return {
            "url": self.url,
            "title": self.title,
            "snippet": self.snippet,
            "published_date": self.published_date,
            "key_stats": self.key_stats or [],
            "key_quotes": self.key_quotes or [],
            "relevance_score": self.relevance_score,
        }


class ResearchAgent(BaseAgent):
    """
    Research agent using Brave Search + Claude 3.5 Haiku via OpenRouter
    """

    def __init__(self, config: Dict = None):
        super().__init__(config)
        self.brave_api_key = config.get("brave_api_key") if config else None
        self.openrouter_api_key = config.get("openrouter_api_key") if config else None

        if not self.brave_api_key:
            raise ValueError("Brave API key required for research agent")
        if not self.openrouter_api_key:
            raise ValueError("OpenRouter API key required for research agent")

    async def run(self, article) -> AgentResult:
        """
        Execute research for article topic
        Returns research bundle with sources, outline, gaps
        """
        start_time = time.time()

        topic = article.title
        logger.info(f"Researching: {topic}")

        try:
            # Step 1: Web search
            all_sources = []

            # Search main topic
            sources = self._web_search(topic, count=15)
            all_sources.extend(sources)

            # Deduplicate by URL
            seen_urls = set()
            unique_sources = []
            for source in all_sources:
                if source.url not in seen_urls:
                    seen_urls.add(source.url)
                    unique_sources.append(source)

            logger.info(f"Found {len(unique_sources)} unique sources")

            # Step 2: Analyze sources with Claude
            analyzed_sources = []
            for source in unique_sources[:20]:  # Limit to 20 sources
                try:
                    analyzed = await self._analyze_source(source, topic)
                    analyzed_sources.append(analyzed)
                except Exception as e:
                    logger.warning(f"Failed to analyze {source.url}: {e}")

            # Step 3: Filter recent sources
            cutoff_date = datetime.now() - timedelta(days=365)  # 1 year
            recent_sources = []
            older_sources = []

            for source in analyzed_sources:
                if source.published_date:
                    try:
                        pub_date = datetime.fromisoformat(source.published_date.replace("Z", "+00:00"))
                        if pub_date > cutoff_date:
                            recent_sources.append(source)
                        else:
                            older_sources.append(source)
                    except:
                        older_sources.append(source)
                else:
                    older_sources.append(source)

            # Combine: prioritize recent
            final_sources = recent_sources + older_sources[:20 - len(recent_sources)]

            logger.info(f"Selected {len(final_sources)} sources ({len(recent_sources)} recent)")

            # Step 4: Generate outline
            outline = await self._generate_outline(topic, final_sources)

            # Step 5: Identify gaps
            gaps = await self._identify_gaps(topic, final_sources)

            duration = time.time() - start_time

            # Build research bundle
            research_data = {
                "topic": topic,
                "sources": [s.to_dict() for s in final_sources],
                "recent_sources_count": len(recent_sources),
                "outline": outline,
                "competitor_gaps": gaps,
                "keywords": [],  # Could extract from sources
            }

            # Success criteria: 10+ sources, 5+ recent
            success = len(final_sources) >= 10 and len(recent_sources) >= 5

            error_msg = None
            if not success:
                error_msg = f"Insufficient sources: {len(final_sources)} total, {len(recent_sources)} recent"

            # Estimate cost (Claude Haiku: $0.25/M input, $1.25/M output)
            # 20 sources * 200 tokens each = 4000 tokens input, ~500 tokens output
            input_tokens = len(final_sources) * 200
            output_tokens = 500
            cost = (input_tokens / 1_000_000 * 0.25) + (output_tokens / 1_000_000 * 1.25)

            return AgentResult(
                success=success,
                data={"research": research_data},
                cost=cost,
                tokens=input_tokens + output_tokens,
                error=error_msg
            )

        except Exception as e:
            logger.error(f"Research failed: {e}")
            return AgentResult(
                success=False,
                data={},
                error=str(e)
            )

    def _web_search(self, query: str, count: int = 10) -> List[Source]:
        """Search web using Brave API"""
        url = "https://api.search.brave.com/res/v1/web/search"

        headers = {
            "Accept": "application/json",
            "X-Subscription-Token": self.brave_api_key,
        }

        params = {
            "q": query,
            "count": count,
            "freshness": "py",  # Past year
        }

        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            sources = []
            for result in data.get("web", {}).get("results", []):
                source = Source(
                    url=result.get("url", ""),
                    title=result.get("title", ""),
                    snippet=result.get("description", ""),
                    published_date=result.get("age"),
                )
                sources.append(source)

            return sources

        except Exception as e:
            logger.error(f"Web search failed: {e}")
            return []

    async def _analyze_source(self, source: Source, topic: str) -> Source:
        """Use Claude to extract key information from source"""
        prompt = f"""Analyze this source for an article about "{topic}".

Source URL: {source.url}
Source Title: {source.title}
Snippet: {source.snippet}

Extract:
1. Key statistics (numbers, percentages, data points)
2. Notable quotes from experts
3. Relevance score (0.0 to 1.0) for the topic

Respond ONLY with valid JSON (no markdown, no explanations):
{{
    "key_stats": ["stat1", "stat2"],
    "key_quotes": ["quote1", "quote2"],
    "relevance_score": 0.85,
    "estimated_date": "2025-06-15"
}}"""

        try:
            response = await self._call_claude(prompt)

            # Clean up response
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]

            response = response.strip()

            data = json.loads(response)

            source.key_stats = data.get("key_stats", [])
            source.key_quotes = data.get("key_quotes", [])
            source.relevance_score = data.get("relevance_score", 0.5)

            if data.get("estimated_date"):
                source.published_date = data["estimated_date"]

        except Exception as e:
            logger.warning(f"Failed to parse Claude response: {e}")
            source.relevance_score = 0.5

        return source

    async def _generate_outline(self, topic: str, sources: List[Source]) -> Dict:
        """Generate article outline from sources"""

        # Compile key information
        all_stats = []
        all_quotes = []
        for source in sources[:10]:
            all_stats.extend(source.key_stats or [])
            all_quotes.extend(source.key_quotes or [])

        prompt = f"""Create an article outline for: "{topic}"

Available statistics:
{json.dumps(all_stats[:20], indent=2)}

Available expert quotes:
{json.dumps(all_quotes[:10], indent=2)}

Create a comprehensive outline with:
- Compelling title
- 5-7 H2 sections
- 2-3 H3 subsections per H2
- Key points for each section

Respond ONLY with valid JSON (no markdown, no explanations):
{{
    "title": "Article Title",
    "sections": [
        {{
            "h2": "Section Title",
            "h3s": ["Subsection 1", "Subsection 2"],
            "key_points": ["point 1", "point 2"]
        }}
    ]
}}"""

        try:
            response = await self._call_claude(prompt)

            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]

            return json.loads(response.strip())

        except Exception as e:
            logger.error(f"Failed to generate outline: {e}")
            return {"title": topic, "sections": []}

    async def _identify_gaps(self, topic: str, sources: List[Source]) -> List[str]:
        """Identify content gaps vs competitors"""

        titles = [s.title for s in sources[:10]]

        prompt = f"""Based on these existing articles about "{topic}":

{json.dumps(titles, indent=2)}

What content gaps exist? What angles are competitors NOT covering?
List 3-5 unique angles we could take.

Respond ONLY as a JSON array (no markdown, no explanations):
["gap 1", "gap 2", "gap 3"]"""

        try:
            response = await self._call_claude(prompt)

            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]

            return json.loads(response.strip())

        except Exception as e:
            logger.error(f"Failed to identify gaps: {e}")
            return []

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
            "temperature": 0.7,
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"Claude API call failed: {e}")
            raise
