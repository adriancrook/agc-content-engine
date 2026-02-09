"""
ResearchAgent for v2 - Adapted from v1
Gathers web sources and creates research bundle using local LLM
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
    Research agent using Brave Search + Local LLM (qwen2.5:14b)
    """

    def __init__(self, config: Dict = None):
        super().__init__(config)
        self.brave_api_key = config.get("brave_api_key") if config else None
        self.ollama_url = config.get("ollama_url", "http://localhost:11434") if config else "http://localhost:11434"
        self.model = config.get("model", "qwen2.5:14b") if config else "qwen2.5:14b"

        if not self.brave_api_key:
            raise ValueError("Brave API key required for research agent")

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

            # Step 2: Analyze sources with LLM
            analyzed_sources = []
            for source in unique_sources[:20]:  # Limit to 20 sources
                try:
                    analyzed = self._analyze_source(source, topic)
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
            outline = self._generate_outline(topic, final_sources)

            # Step 5: Identify gaps
            gaps = self._identify_gaps(topic, final_sources)

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

            return AgentResult(
                success=success,
                data={"research": research_data},
                cost=0.0,  # Local LLM
                tokens=0,
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

    def _analyze_source(self, source: Source, topic: str) -> Source:
        """Use LLM to extract key information from source"""
        prompt = f"""Analyze this source for an article about "{topic}".

Source URL: {source.url}
Source Title: {source.title}
Snippet: {source.snippet}

Extract:
1. Key statistics (numbers, percentages, data points)
2. Notable quotes from experts
3. Relevance score (0.0 to 1.0) for the topic

Respond in JSON format:
{{
    "key_stats": ["stat1", "stat2"],
    "key_quotes": ["quote1", "quote2"],
    "relevance_score": 0.85,
    "estimated_date": "2025-06-15"
}}"""

        try:
            response = self._call_ollama(prompt)

            # Clean up response
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]

            response = response.strip()
            response = response.replace(",}", "}").replace(",]", "]")

            # Fix unquoted keys
            response = re.sub(r'([{,]\s*)(\w+)(\s*:)', r'\1"\2"\3', response)

            try:
                data = json.loads(response)
            except json.JSONDecodeError:
                # Try extracting JSON object
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group())
                else:
                    raise

            source.key_stats = data.get("key_stats", [])
            source.key_quotes = data.get("key_quotes", [])
            source.relevance_score = data.get("relevance_score", 0.5)

            if data.get("estimated_date"):
                source.published_date = data["estimated_date"]

        except Exception as e:
            logger.warning(f"Failed to parse LLM response: {e}")
            source.relevance_score = 0.5

        return source

    def _generate_outline(self, topic: str, sources: List[Source]) -> Dict:
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

Respond in JSON:
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
            response = self._call_ollama(prompt)

            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]

            return json.loads(response.strip())

        except Exception as e:
            logger.error(f"Failed to generate outline: {e}")
            return {"title": topic, "sections": []}

    def _identify_gaps(self, topic: str, sources: List[Source]) -> List[str]:
        """Identify content gaps vs competitors"""

        titles = [s.title for s in sources[:10]]

        prompt = f"""Based on these existing articles about "{topic}":

{json.dumps(titles, indent=2)}

What content gaps exist? What angles are competitors NOT covering?
List 3-5 unique angles we could take.

Respond as a JSON array:
["gap 1", "gap 2", "gap 3"]"""

        try:
            response = self._call_ollama(prompt)

            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]

            return json.loads(response.strip())

        except Exception as e:
            logger.error(f"Failed to identify gaps: {e}")
            return []

    def _call_ollama(self, prompt: str) -> str:
        """Call local Ollama model"""
        url = f"{self.ollama_url}/api/generate"

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "num_predict": 4096,
            }
        }

        try:
            response = requests.post(url, json=payload, timeout=300)
            response.raise_for_status()
            result = response.json()
            return result.get("response", "")
        except Exception as e:
            logger.error(f"Ollama call failed: {e}")
            raise
