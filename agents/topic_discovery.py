"""
Topic Discovery Agent - Finds high-value article opportunities.

Researches:
- Trending topics in the niche
- Keyword opportunities (volume vs competition)
- Competitor content gaps
- Seasonal/timely topics
- Evergreen opportunities

Model: qwen2.5:14b (local)
"""

import json
import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import requests

from .base import BaseAgent, AgentInput, AgentOutput

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


class TopicDiscoveryAgent(BaseAgent):
    """
    Topic discovery agent that finds article opportunities.
    
    Uses web search + LLM analysis to identify high-value topics.
    """
    
    def __init__(
        self,
        brave_api_key: str,
        niche: str = "mobile gaming and game design",
        blog_url: str = "https://adriancrook.com",
        ollama_url: str = "http://localhost:11434",
        model: str = "qwen2.5:14b",
    ):
        super().__init__(
            name="topic_discovery",
            model=model,
            model_type="ollama",
            ollama_url=ollama_url,
        )
        self.brave_api_key = brave_api_key
        self.niche = niche
        self.blog_url = blog_url
    
    def run(self, input: AgentInput) -> AgentOutput:
        """
        Discover article topic opportunities.
        
        Input data:
            - existing_articles: List[str] - Titles of existing blog articles
            - focus_areas: List[str] - Specific areas to focus on
            - max_topics: int - Maximum topics to return (default 10)
        """
        start_time = time.time()
        errors = []
        
        existing_articles = input.data.get("existing_articles", [])
        focus_areas = input.data.get("focus_areas", [
            "mobile game monetization",
            "free-to-play design",
            "game economy",
            "player retention",
            "mobile game marketing",
            "gacha mechanics",
            "battle pass design",
        ])
        max_topics = input.data.get("max_topics", 10)
        
        logger.info(f"Discovering topics for: {self.niche}")
        
        all_topics = []
        
        # Step 1: Find trending topics
        trending = self._find_trending_topics(focus_areas)
        all_topics.extend(trending)
        logger.info(f"Found {len(trending)} trending topics")
        
        # Step 2: Find evergreen opportunities
        evergreen = self._find_evergreen_topics(focus_areas)
        all_topics.extend(evergreen)
        logger.info(f"Found {len(evergreen)} evergreen topics")
        
        # Step 3: Analyze competitor gaps
        gaps = self._find_competitor_gaps(focus_areas, existing_articles)
        all_topics.extend(gaps)
        logger.info(f"Found {len(gaps)} competitor gap topics")
        
        # Step 4: Find seasonal/timely topics
        seasonal = self._find_seasonal_topics(focus_areas)
        all_topics.extend(seasonal)
        logger.info(f"Found {len(seasonal)} seasonal topics")
        
        # Step 5: Filter out topics we already have
        filtered_topics = self._filter_existing(all_topics, existing_articles)
        
        # Step 6: Score and rank topics
        scored_topics = self._score_topics(filtered_topics)
        
        # Step 7: Select top topics
        top_topics = sorted(scored_topics, key=lambda x: x.opportunity_score, reverse=True)[:max_topics]
        
        duration = time.time() - start_time
        
        output_data = {
            "topics": [t.to_dict() for t in top_topics],
            "total_discovered": len(all_topics),
            "after_filtering": len(filtered_topics),
            "niche": self.niche,
            "focus_areas": focus_areas,
        }
        
        success = len(top_topics) >= 5
        
        if len(top_topics) < 5:
            errors.append(f"Only found {len(top_topics)} topics (need 5+)")
        
        return AgentOutput(
            data=output_data,
            success=success,
            errors=errors,
            duration_seconds=duration,
        )
    
    def validate_output(self, output: AgentOutput) -> bool:
        """Check if topic discovery meets quality gate."""
        data = output.data
        topics = data.get("topics", [])
        return len(topics) >= 5
    
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
            "freshness": freshness,  # pm = past month, pw = past week
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
    
    def _find_trending_topics(self, focus_areas: List[str]) -> List[TopicIdea]:
        """Find currently trending topics."""
        topics = []
        
        for area in focus_areas[:3]:  # Limit to avoid too many API calls
            # Search for recent news/articles
            results = self._web_search(f"{area} 2025 trends news", count=10, freshness="pw")
            
            if not results:
                continue
            
            # Use LLM to extract topic ideas
            prompt = f"""Analyze these recent articles about "{area}" and suggest 2-3 article topics that would perform well.

Recent articles:
{json.dumps([r['title'] for r in results], indent=2)}

For each topic, provide:
- A compelling article title
- Primary keyword (2-4 words)
- 3-5 secondary keywords
- Why this topic is timely

Respond in JSON:
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
                response = self._call_model(prompt)
                
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
                logger.warning(f"Failed to parse trending topics: {e}")
        
        return topics
    
    def _find_evergreen_topics(self, focus_areas: List[str]) -> List[TopicIdea]:
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

Respond in JSON:
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
            response = self._call_model(prompt)
            
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
    
    def _find_competitor_gaps(self, focus_areas: List[str], existing_articles: List[str]) -> List[TopicIdea]:
        """Find topics competitors cover that we don't."""
        topics = []
        
        # Search for top competitor content
        results = self._web_search(f"best {self.niche} articles guides", count=20, freshness="py")
        
        if not results:
            return topics
        
        prompt = f"""Analyze competitor articles and identify content gaps.

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

Respond in JSON:
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
            response = self._call_model(prompt)
            
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
    
    def _find_seasonal_topics(self, focus_areas: List[str]) -> List[TopicIdea]:
        """Find seasonal/timely topics."""
        topics = []
        
        current_month = datetime.now().strftime("%B")
        current_year = datetime.now().year
        
        prompt = f"""Suggest 3 timely/seasonal article topics for a blog about {self.niche}.

Current date: {current_month} {current_year}

Consider:
- Upcoming game releases
- Industry events (GDC, E3, etc.)
- Seasonal gaming trends
- Annual reports/reviews
- Holiday-related gaming

Focus areas: {', '.join(focus_areas)}

For each topic, provide:
- A timely article title
- Primary keyword
- 3-5 secondary keywords
- Why this is timely NOW

Respond in JSON:
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
            response = self._call_model(prompt)
            
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
