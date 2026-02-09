"""
DataEnrichmentAgent for v2
Finds citations, metrics, testimonials, and media links to enrich articles
Runs between Writer Pass 1 and Writer Pass 2
"""

import json
import logging
import time
from pathlib import Path
from typing import Dict, List

import requests

from .base import BaseAgent, AgentResult

logger = logging.getLogger(__name__)


class DataEnrichmentAgent(BaseAgent):
    """
    DataEnrichment agent that enriches articles with citations, data, and testimonials
    Runs after initial Writer pass, before Writer revision pass
    """

    def __init__(self, config: Dict = None):
        super().__init__(config)
        self.brave_api_key = config.get("brave_api_key") if config else None
        self.openrouter_api_key = config.get("openrouter_api_key") if config else None

        if not self.brave_api_key:
            logger.warning("No Brave API key - citation search will be limited")

        if not self.openrouter_api_key:
            raise ValueError("OpenRouter API key required for enrichment agent")

        # Load testimonials database
        self.testimonials = self._load_testimonials()

        # Load game metrics database
        self.game_metrics = self._load_game_metrics()

    def _load_testimonials(self) -> List[Dict]:
        """Load testimonials from JSON file"""
        testimonials_path = Path(__file__).parent.parent / "data" / "testimonials.json"

        if not testimonials_path.exists():
            logger.warning(f"Testimonials file not found: {testimonials_path}")
            return []

        with open(testimonials_path, 'r') as f:
            data = json.load(f)
            return data.get("testimonials", [])

    def _load_game_metrics(self) -> Dict:
        """Load game metrics from JSON file"""
        metrics_path = Path(__file__).parent.parent / "data" / "game_metrics.json"

        if not metrics_path.exists():
            logger.warning(f"Game metrics file not found: {metrics_path}")
            return {"games": []}

        with open(metrics_path, 'r') as f:
            data = json.load(f)
            return data

    async def run(self, article) -> AgentResult:
        """
        Main enrichment pipeline
        """
        start_time = time.time()

        draft = article.draft
        topic = article.title

        if not draft:
            return AgentResult(
                success=False,
                data={},
                error="No draft found to enrich"
            )

        # Performance optimization: Truncate very large drafts for analysis
        # We only need to identify claims/examples, not analyze the entire article
        original_length = len(draft)
        MAX_ANALYSIS_WORDS = 1500  # ~10KB, enough to identify enrichment needs

        words = draft.split()
        if len(words) > MAX_ANALYSIS_WORDS:
            # Take first 1000 words + last 500 words (to capture intro and conclusion)
            draft_for_analysis = ' '.join(words[:1000] + ['...'] + words[-500:])
            logger.info(f"Truncating draft for analysis: {original_length} chars → {len(draft_for_analysis)} chars")
        else:
            draft_for_analysis = draft

        logger.info(f"Enriching article: {topic} ({len(words)} words)")

        try:
            # 1. Analyze draft for enrichment opportunities
            logger.info("Analyzing draft for enrichment needs...")
            enrichment_needs = self._analyze_draft(draft_for_analysis, topic)

            # 2. Find citations
            logger.info(f"Finding citations for {len(enrichment_needs['claims'])} claims...")
            citations = self._find_citations(enrichment_needs['claims'])

            # 3. Find metrics (placeholder for now)
            logger.info("Finding metrics...")
            metrics = self._find_metrics(enrichment_needs['examples'])

            # 4. Match testimonials
            logger.info("Matching testimonials...")
            testimonials = self._match_testimonials(topic, enrichment_needs['sections'])

            # 5. Find media links (placeholder)
            logger.info("Finding media links...")
            media = self._find_media_links(topic)

            # 6. Create integration guide
            logger.info("Creating integration guide...")
            integration_guide = self._create_integration_guide(
                draft, citations, metrics, testimonials, media
            )

            duration = time.time() - start_time

            logger.info(f"Enrichment complete: {len(citations)} citations, "
                       f"{len(metrics)} metrics, {len(testimonials)} testimonials")

            return AgentResult(
                success=True,
                data={
                    "enrichment": {
                        "citations": citations,
                        "metrics": metrics,
                        "testimonials": testimonials,
                        "media": media
                    },
                    "integration_guide": integration_guide
                },
                cost=self._estimate_cost(draft),
                tokens=int(len(draft.split()) * 1.5)
            )

        except Exception as e:
            logger.error(f"Enrichment failed: {e}")
            return AgentResult(
                success=False,
                data={},
                error=str(e)
            )

    def _analyze_draft(self, draft: str, topic: str) -> Dict:
        """
        Analyze draft to identify enrichment opportunities using Claude
        """
        prompt = f"""Analyze this article draft to identify enrichment opportunities.

ARTICLE TOPIC: {topic}

DRAFT:
{draft}

Identify:
1. CLAIMS that need citations (statements of fact, statistics, trends)
2. EXAMPLES that need specific metrics (games mentioned without data)
3. SECTIONS that would benefit from testimonials

Return JSON format:
{{
  "claims": [
    {{"text": "claim text", "location": "Section 2, paragraph 3"}}
  ],
  "examples": [
    {{"game": "Game Name", "metric_type": "revenue|DAU|retention", "location": "Section X"}}
  ],
  "sections": [
    {{"title": "Section Name", "topics": ["topic1", "topic2"]}}
  ]
}}

Return ONLY valid JSON, no other text."""

        response = self._call_openrouter(prompt)

        try:
            # Strip markdown code blocks if present
            response = response.strip()
            if response.startswith('```json'):
                response = response[7:]  # Remove ```json
            if response.startswith('```'):
                response = response[3:]   # Remove ```
            if response.endswith('```'):
                response = response[:-3]  # Remove trailing ```
            response = response.strip()

            # Parse JSON response
            result = json.loads(response)
            return result
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse enrichment analysis: {e}")
            logger.error(f"Response: {response[:300]}")
            return {"claims": [], "examples": [], "sections": []}

    def _find_citations(self, claims: List[Dict]) -> List[Dict]:
        """
        Find citations for claims using Brave Search
        """
        citations = []

        for i, claim in enumerate(claims[:5]):  # Limit to 5 citations for now
            try:
                # Search for sources
                search_query = f"{claim['text']} mobile gaming statistics data"
                results = self._search_brave(search_query)

                if results:
                    # Use first relevant result
                    best_result = results[0]

                    citations.append({
                        "id": i + 1,
                        "claim": claim['text'],
                        "source": best_result.get('source', 'Unknown'),
                        "title": best_result.get('title', ''),
                        "url": best_result.get('url', ''),
                        "quote": best_result.get('snippet', ''),
                        "integration_point": claim.get('location', 'Unknown')
                    })

            except Exception as e:
                logger.error(f"Citation search failed for claim: {e}")

        return citations

    def _search_brave(self, query: str) -> List[Dict]:
        """
        Search using Brave Search API
        """
        if not self.brave_api_key:
            logger.warning("No Brave API key - using placeholder citations")
            return []

        url = "https://api.search.brave.com/res/v1/web/search"

        headers = {
            "Accept": "application/json",
            "X-Subscription-Token": self.brave_api_key
        }

        params = {
            "q": query,
            "count": 5
        }

        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            results = []
            for item in data.get("web", {}).get("results", [])[:5]:
                results.append({
                    "source": self._extract_domain(item.get("url", "")),
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "snippet": item.get("description", "")
                })

            return results

        except Exception as e:
            logger.error(f"Brave search failed: {e}")
            return []

    def _extract_domain(self, url: str) -> str:
        """Extract domain name from URL"""
        try:
            from urllib.parse import urlparse
            domain = urlparse(url).netloc
            # Remove www.
            domain = domain.replace("www.", "")
            # Capitalize first letter
            return domain.split('.')[0].capitalize()
        except:
            return "Unknown"

    def _find_metrics(self, examples: List[Dict]) -> List[Dict]:
        """
        Find specific metrics for game examples using database
        """
        metrics = []

        for example in examples[:5]:  # Limit to 5
            game_name = example.get('game', 'Unknown')
            metric_type = example.get('metric_type', 'revenue')
            location = example.get('location', 'Unknown')

            # Look up game in database
            game_data = self._lookup_game(game_name)

            if game_data:
                # Get the requested metric
                metric_value = self._get_metric_value(game_data, metric_type)

                if metric_value:
                    # Find source if available
                    source_data = self._get_metric_source(game_data, metric_type)

                    metrics.append({
                        "game": game_name,
                        "metric": metric_type,
                        "value": metric_value,
                        "source": source_data.get("source", "Industry Reports"),
                        "url": source_data.get("url", ""),
                        "integration_point": location
                    })
            else:
                # Fallback for games not in database
                logger.warning(f"No metrics found for {game_name}")
                metrics.append({
                    "game": game_name,
                    "metric": metric_type,
                    "value": f"[Leading mobile game with significant market presence]",
                    "source": "Industry Reports",
                    "url": "",
                    "integration_point": location
                })

        return metrics

    def _lookup_game(self, game_name: str) -> Dict:
        """Look up game in metrics database"""
        game_name_lower = game_name.lower()

        for game in self.game_metrics.get("games", []):
            if game["name"].lower() == game_name_lower:
                return game

        return None

    def _get_metric_value(self, game_data: Dict, metric_type: str) -> str:
        """Get specific metric value from game data"""
        metrics = game_data.get("metrics", {})

        # Map metric types to database keys
        metric_mapping = {
            "revenue": ["lifetime_revenue", "annual_revenue", "lifetime_revenue_mobile"],
            "dau": ["dau", "dau_estimate"],
            "downloads": ["downloads"],
            "retention": ["retention_d7"],
            "arppu": ["arppu"],
            "arpdau": ["arpdau", "monthly_revenue"]
        }

        # Try to find matching metric
        possible_keys = metric_mapping.get(metric_type, [metric_type])

        for key in possible_keys:
            if key in metrics:
                return metrics[key]

        # Return first available metric if no exact match
        if metrics:
            return list(metrics.values())[0]

        return None

    def _get_metric_source(self, game_data: Dict, metric_type: str) -> Dict:
        """Get source information for metric"""
        sources = game_data.get("sources", [])

        if sources:
            # Find source for this metric type
            for source in sources:
                if metric_type in source.get("metric", "").lower():
                    return source

            # Return first source as fallback
            return sources[0]

        return {"source": "Industry Reports", "url": ""}

    def _match_testimonials(self, topic: str, sections: List[Dict]) -> List[Dict]:
        """
        Match relevant testimonials from database
        """
        if not self.testimonials:
            return []

        # Extract topics from sections
        all_topics = set()
        for section in sections:
            all_topics.update(section.get('topics', []))

        # Simple keyword matching
        matched_testimonials = []

        for testimonial in self.testimonials:
            testimonial_topics = set(testimonial.get('topics', []))

            # Check topic overlap
            overlap = all_topics.intersection(testimonial_topics)

            if overlap or any(topic_word in topic.lower() for topic_word in testimonial_topics):
                matched_testimonials.append({
                    "client": testimonial['client'],
                    "title": testimonial.get('title'),
                    "company": testimonial.get('company'),
                    "quote": testimonial['quote'],
                    "topics": list(testimonial_topics),
                    "integration_point": "After relevant section"
                })

        return matched_testimonials[:2]  # Max 2 testimonials

    def _find_media_links(self, topic: str) -> List[Dict]:
        """
        Find YouTube videos, GDC talks, etc.
        Placeholder for now
        """
        # TODO: Implement YouTube/GDC search
        return []

    def _create_integration_guide(
        self,
        draft: str,
        citations: List[Dict],
        metrics: List[Dict],
        testimonials: List[Dict],
        media: List[Dict]
    ) -> str:
        """
        Create detailed instructions for Writer Pass 2
        """

        guide = f"""INTEGRATION GUIDE FOR WRITER PASS 2

Original Draft: {len(draft.split())} words

You have {len(citations)} citations, {len(metrics)} metrics, {len(testimonials)} testimonials, and {len(media)} media links to integrate.

INSTRUCTIONS:

1. CITATIONS ({len(citations)} total)
   Add numbered citations [1], [2], etc. at the end of relevant sentences.

"""

        # Add citation instructions
        for citation in citations:
            guide += f"""   [{citation['id']}] Location: {citation['integration_point']}
   Claim: "{citation['claim']}"
   Source: {citation['source']} - {citation['title']}
   Add: Cite as "According to {citation['source']}, {citation['quote'][:100]}..." [{citation['id']}]
   URL: {citation['url']}

"""

        # Add metrics instructions
        if metrics:
            guide += f"\n2. METRICS ({len(metrics)} total)\n"
            for metric in metrics:
                guide += f"""   Game: {metric['game']}
   Location: {metric['integration_point']}
   Add: Specific metric "{metric['value']}" from {metric['source']}

"""

        # Add testimonial instructions
        if testimonials:
            guide += f"\n3. TESTIMONIALS ({len(testimonials)} total)\n"
            for testimonial in testimonials:
                client_info = f"{testimonial['client']}"
                if testimonial.get('title'):
                    client_info += f", {testimonial['title']}"
                if testimonial.get('company'):
                    client_info += f", {testimonial['company']}"

                guide += f"""   Client: {client_info}
   Quote: "{testimonial['quote']}"
   Integration: Add in "Professional Services" or relevant section

"""

        # Add media instructions
        if media:
            guide += f"\n4. MEDIA LINKS ({len(media)} total)\n"
            for m in media:
                guide += f"""   Type: {m['type']}
   Title: {m['title']}
   URL: {m['url']}

"""

        guide += """
5. SOURCES SECTION
   Create a "Sources" section at the end with all numbered citations.

   Format:
   ## Sources
   [1] Source Name - Title - URL
   [2] Source Name - Title - URL
   ...

IMPORTANT:
- Maintain original structure and flow
- Weave citations naturally into sentences
- Add testimonials in appropriate sections
- Keep mobile gaming focus
- Preserve professional but practical tone
- Don't force citations where they don't fit naturally
"""

        return guide

    def _estimate_cost(self, draft: str) -> float:
        """Estimate API cost"""
        # Rough estimate for analysis + searches
        return 0.02

    def _call_openrouter(self, prompt: str) -> str:
        """Call Claude via OpenRouter API"""
        url = "https://openrouter.ai/api/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {self.openrouter_api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://adriancrook.com",
            "X-Title": "AGC Content Engine v2 - Data Enrichment",
        }

        payload = {
            "model": "anthropic/claude-sonnet-4",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 4096,
            "temperature": 0.2,  # Lower for more structured output
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=120)
            response.raise_for_status()
            data = response.json()

            return data["choices"][0]["message"]["content"]

        except Exception as e:
            logger.error(f"OpenRouter API call failed: {e}")
            raise
