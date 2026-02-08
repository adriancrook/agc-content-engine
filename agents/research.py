"""
Research Agent - Gathers sources and creates research bundle.

Model: qwen2.5:14b (local)
"""

import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

from .base import BaseAgent, AgentInput, AgentOutput

logger = logging.getLogger(__name__)


@dataclass
class Source:
    """A research source."""
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
    Research agent that gathers sources for a topic.
    
    Uses web search (Brave API) and local LLM for analysis.
    """
    
    def __init__(
        self,
        brave_api_key: str,
        ollama_url: str = "http://localhost:11434",
        model: str = "qwen2.5:14b",
    ):
        super().__init__(
            name="research",
            model=model,
            model_type="ollama",
            ollama_url=ollama_url,
        )
        self.brave_api_key = brave_api_key
    
    def run(self, input: AgentInput) -> AgentOutput:
        """
        Execute research for a topic.
        
        Input data:
            - topic: str - The main topic
            - keywords: List[str] - Related keywords
            - max_sources: int - Maximum sources to gather (default 20)
            - max_age_months: int - Maximum age of sources (default 12)
        """
        start_time = time.time()
        errors = []
        
        topic = input.data.get("topic", "")
        keywords = input.data.get("keywords", [])
        max_sources = input.data.get("max_sources", 20)
        max_age_months = input.data.get("max_age_months", 12)
        
        if not topic:
            return AgentOutput(
                data={},
                success=False,
                errors=["No topic provided"],
            )
        
        logger.info(f"Researching topic: {topic}")
        
        # Step 1: Web search
        all_sources = []
        
        # Search main topic
        sources = self._web_search(topic, count=10)
        all_sources.extend(sources)
        
        # Search keywords
        for keyword in keywords[:5]:  # Limit to 5 keywords
            sources = self._web_search(f"{topic} {keyword}", count=5)
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
        for source in unique_sources[:max_sources]:
            try:
                analyzed = self._analyze_source(source, topic)
                analyzed_sources.append(analyzed)
            except Exception as e:
                logger.warning(f"Failed to analyze source {source.url}: {e}")
                errors.append(f"Failed to analyze: {source.url}")
        
        # Step 3: Filter by date
        cutoff_date = datetime.now() - timedelta(days=max_age_months * 30)
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
        
        # Combine: prioritize recent, add older if needed
        final_sources = recent_sources + older_sources[:max_sources - len(recent_sources)]
        
        # Step 4: Generate outline
        outline = self._generate_outline(topic, final_sources)
        
        # Step 5: Identify competitor gaps
        gaps = self._identify_gaps(topic, final_sources)
        
        duration = time.time() - start_time
        
        output_data = {
            "topic": topic,
            "keywords": keywords,
            "sources": [s.to_dict() for s in final_sources],
            "recent_sources_count": len(recent_sources),
            "outline": outline,
            "competitor_gaps": gaps,
        }
        
        success = len(final_sources) >= 10 and len(recent_sources) >= 5
        
        if len(final_sources) < 10:
            errors.append(f"Only found {len(final_sources)} sources (need 10+)")
        if len(recent_sources) < 5:
            errors.append(f"Only {len(recent_sources)} recent sources (need 5+)")
        
        return AgentOutput(
            data=output_data,
            success=success,
            errors=errors,
            duration_seconds=duration,
        )
    
    def validate_output(self, output: AgentOutput) -> bool:
        """Check if research meets quality gate."""
        if not output.success:
            return False
        
        data = output.data
        sources = data.get("sources", [])
        outline = data.get("outline", {})
        
        # Must have 10+ sources
        if len(sources) < 10:
            return False
        
        # Must have 5+ recent sources
        if data.get("recent_sources_count", 0) < 5:
            return False
        
        # Outline must have 4+ sections
        sections = outline.get("sections", [])
        if len(sections) < 4:
            return False
        
        return True
    
    def _web_search(self, query: str, count: int = 10) -> List[Source]:
        """Search web using Brave API."""
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
                    published_date=result.get("age"),  # Brave provides relative age
                )
                sources.append(source)
            
            return sources
        
        except Exception as e:
            logger.error(f"Web search failed: {e}")
            return []
    
    def _analyze_source(self, source: Source, topic: str) -> Source:
        """Use LLM to extract key information from source."""
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
            response = self._call_model(prompt)
            
            # Parse JSON from response
            # Handle potential markdown code blocks
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]
            
            data = json.loads(response.strip())
            
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
        """Generate article outline from sources."""
        
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
            response = self._call_model(prompt)
            
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]
            
            return json.loads(response.strip())
        
        except Exception as e:
            logger.error(f"Failed to generate outline: {e}")
            return {"title": topic, "sections": []}
    
    def _identify_gaps(self, topic: str, sources: List[Source]) -> List[str]:
        """Identify content gaps vs competitors."""
        
        titles = [s.title for s in sources[:10]]
        
        prompt = f"""Based on these existing articles about "{topic}":

{json.dumps(titles, indent=2)}

What content gaps exist? What angles are competitors NOT covering?
List 3-5 unique angles we could take.

Respond as a JSON array:
["gap 1", "gap 2", "gap 3"]"""

        try:
            response = self._call_model(prompt)
            
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]
            
            return json.loads(response.strip())
        
        except Exception as e:
            logger.error(f"Failed to identify gaps: {e}")
            return []
