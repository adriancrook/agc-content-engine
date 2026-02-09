"""
WriterAgent for v2 - Using Claude for professional quality
Creates high-quality article drafts from research
"""

import json
import logging
import time
from typing import Dict, List

import requests

from .base import BaseAgent, AgentResult

logger = logging.getLogger(__name__)


class WriterAgent(BaseAgent):
    """
    Writer agent using Claude Sonnet via OpenRouter
    Creates professional, fact-based long-form articles
    """

    def __init__(self, config: Dict = None):
        super().__init__(config)
        self.api_key = config.get("openrouter_api_key") if config else None
        self.model = "anthropic/claude-sonnet-4"
        self.target_word_count = config.get("target_word_count", 3000) if config else 3000
        self.max_word_count = config.get("max_word_count", 4000) if config else 4000  # Hard limit
        self.pass_type = config.get("pass_type", "draft") if config else "draft"  # "draft" or "revision"

        if not self.api_key:
            raise ValueError("OpenRouter API key required for writer agent")

    async def run(self, article) -> AgentResult:
        """
        Generate article draft OR revise with enrichment
        """
        if self.pass_type == "revision":
            return await self._run_revision(article)
        else:
            return await self._run_draft(article)

    async def _run_draft(self, article) -> AgentResult:
        """
        Pass 1: Generate initial article draft from research
        """
        start_time = time.time()

        # Get research data from article
        research = article.research
        if not research:
            return AgentResult(
                success=False,
                data={},
                error="No research data found in article"
            )

        topic = article.title
        outline = research.get("outline", {})
        sources = research.get("sources", [])

        logger.info(f"Writing initial draft for: {topic}")

        try:
            # Write article sections
            intro = self._write_introduction(topic, outline, sources)
            sections = []

            for section in outline.get("sections", []):
                logger.info(f"Writing section: {section.get('h2', '')}")
                section_content = self._write_section(topic, section, sources)
                sections.append(section_content)

            conclusion = self._write_conclusion(topic, outline, sources)

            # Compile full article
            article_md = self._compile_article(
                outline.get("title", topic),
                intro,
                sections,
                conclusion
            )

            word_count = len(article_md.split())
            logger.info(f"Draft complete: {word_count} words")

            # Success if >= 2000 words
            success = word_count >= 2000

            return AgentResult(
                success=success,
                data={"draft": article_md},
                cost=self._estimate_cost(word_count),
                tokens=int(word_count * 1.5),
                error=None if success else f"Short article: {word_count} words"
            )

        except Exception as e:
            logger.error(f"Writing failed: {e}")
            return AgentResult(
                success=False,
                data={},
                error=str(e)
            )

    def _write_introduction(self, topic: str, outline: Dict, sources: List[Dict]) -> str:
        """Write professional introduction with citations"""

        # Build source context with citations
        source_context = ""
        for i, s in enumerate(sources[:5], 1):
            source_context += f"\n[Source {i}] {s.get('title', '')}\n"
            source_context += f"URL: {s.get('url', '')}\n"
            if s.get('snippet'):
                source_context += f"Context: {s.get('snippet', '')[:200]}\n"
            for stat in s.get('key_stats', [])[:2]:
                source_context += f"  • Stat: {stat}\n"
            for quote in s.get('key_quotes', [])[:1]:
                source_context += f"  • Quote: \"{quote}\"\n"

        prompt = f"""Write a professional introduction for an article titled: "{outline.get('title', topic)}"

TOPIC: {topic}

AVAILABLE SOURCES:
{source_context}

REQUIREMENTS:
1. Professional, authoritative tone (NOT casual or conversational)
2. Start with a compelling hook using a specific statistic or fact
3. Cite sources using format: "According to [source name], ..." or "Research shows that [stat] (Source: [name])"
4. NO personal opinions or phrases like "I think", "Let's be honest", "Here's the thing"
5. Focus on factual, data-driven insights
6. **CRITICAL: 200-250 words MAXIMUM - be concise**
7. Preview the key insights the article will cover

Write ONLY the introduction text with proper citations."""

        response = self._call_openrouter(prompt, max_tokens=600)
        return response.strip()

    def _write_section(self, topic: str, section: Dict, sources: List[Dict]) -> str:
        """Write a professional body section with citations"""

        h2 = section.get("h2", "")
        h3s = section.get("h3s", [])
        key_points = section.get("key_points", [])

        # Build comprehensive source context
        source_context = ""
        for i, s in enumerate(sources[:8], 1):
            source_context += f"\n[Source {i}] {s.get('title', '')}\n"
            source_context += f"URL: {s.get('url', '')}\n"
            for stat in s.get('key_stats', [])[:3]:
                source_context += f"  • {stat}\n"
            for quote in s.get('key_quotes', [])[:2]:
                source_context += f"  • \"{quote}\"\n"

        prompt = f"""Write a professional article section for: "{topic}"

SECTION HEADER: {h2}

SUBSECTIONS TO COVER:
{json.dumps(h3s, indent=2)}

KEY POINTS TO ADDRESS:
{json.dumps(key_points, indent=2)}

AVAILABLE SOURCES:
{source_context}

REQUIREMENTS:
1. Professional, authoritative tone - NO casual language
2. Use ## {h2} for main header
3. Use ### for subsections from the list above
4. CITE ALL FACTS: Use specific statistics, data, and quotes from sources
5. Attribution format: "According to [source]..." or "Research by [source] shows..."
6. NO personal opinions, contractions, or phrases like "honestly", "let me tell you"
7. Every claim must be backed by source material
8. **CRITICAL: 400-500 words MAXIMUM - be concise and focused**
9. Include concrete examples and case studies from sources

Write the complete section in Markdown with proper citations."""

        response = self._call_openrouter(prompt, max_tokens=1200)
        return response.strip()

    def _write_conclusion(self, topic: str, outline: Dict, sources: List[Dict]) -> str:
        """Write professional conclusion"""

        # Key findings from sources
        key_findings = []
        for s in sources[:5]:
            for stat in s.get('key_stats', [])[:1]:
                key_findings.append(stat)

        prompt = f"""Write a professional conclusion for article: "{outline.get('title', topic)}"

TOPIC: {topic}

KEY FINDINGS FROM ARTICLE:
{chr(10).join(f"- {f}" for f in key_findings[:5])}

REQUIREMENTS:
1. Professional, authoritative tone
2. Synthesize the main insights covered
3. NO new information or sources
4. Look forward to future trends/implications
5. End with a clear takeaway
6. **CRITICAL: 150-200 words MAXIMUM**
7. NO call-to-action or sales language

Write ONLY the conclusion text."""

        response = self._call_openrouter(prompt, max_tokens=500)
        return response.strip()

    def _compile_article(self, title: str, intro: str, sections: List[str], conclusion: str) -> str:
        """Compile all parts into final article"""

        parts = [
            f"# {title}",
            "",
            intro,
            "",
        ]

        for section in sections:
            parts.append(section)
            parts.append("")

        parts.append("## Conclusion")
        parts.append("")
        parts.append(conclusion)

        return "\n".join(parts)

    def _estimate_cost(self, word_count: int) -> float:
        """Estimate Claude API cost"""
        # Rough estimate: word_count * 1.5 for tokens, Claude Sonnet pricing
        tokens = word_count * 1.5
        cost = (tokens / 1_000_000) * 3.0  # $3 per 1M input tokens
        return cost

    async def _run_revision(self, article) -> AgentResult:
        """
        Pass 2: Revise draft with enrichment data
        """
        start_time = time.time()

        # Get draft and enrichment data
        draft = article.draft
        enrichment = article.enrichment

        if not draft:
            return AgentResult(
                success=False,
                data={},
                error="No draft found to revise"
            )

        if not enrichment:
            return AgentResult(
                success=False,
                data={},
                error="No enrichment data found"
            )

        logger.info(f"Revising draft with enrichment for: {article.title}")

        # Create integration guide
        integration_guide = self._create_integration_guide(enrichment)

        # Create revision prompt
        prompt = f"""You are revising an article for adriancrook.com - a mobile gaming industry blog.

ORIGINAL DRAFT:
{draft}

ENRICHMENT DATA:
{integration_guide}

Your task: Integrate the citations, metrics, testimonials, and media links naturally into the article while maintaining the original structure and voice.

REQUIREMENTS:
1. Add numbered citations [1], [2] at the END of relevant sentences where specified
2. Weave in specific metrics naturally (e.g., "Clash Royale, which has generated over $4+ billion...")
3. Integrate testimonials in appropriate sections
4. Create a "## Sources" section at the bottom with all [1], [2] citations formatted as:
   [1] Source Name - Title - URL
   [2] Source Name - Title - URL
5. Maintain mobile gaming focus and professional but practical tone
6. Keep the same format structure
7. Don't force citations where they don't fit naturally

OUTPUT: The complete revised article in markdown format with all enrichment integrated.
"""

        try:
            revised_draft = self._call_openrouter(prompt)
            word_count = len(revised_draft.split())

            logger.info(f"Revision complete: {word_count} words")

            return AgentResult(
                success=True,
                data={"revised_draft": revised_draft},
                cost=self._estimate_cost(word_count),
                tokens=int(word_count * 1.5)
            )

        except Exception as e:
            logger.error(f"Revision failed: {e}")
            return AgentResult(
                success=False,
                data={},
                error=str(e)
            )

    def _create_integration_guide(self, enrichment: Dict) -> str:
        """Create guide from enrichment data"""
        citations = enrichment.get("citations", [])
        metrics = enrichment.get("metrics", [])
        testimonials = enrichment.get("testimonials", [])
        media = enrichment.get("media", [])

        guide = f"You have {len(citations)} citations, {len(metrics)} metrics, {len(testimonials)} testimonials to integrate.\n\n"

        if citations:
            guide += "CITATIONS:\n"
            for citation in citations:
                guide += f"[{citation['id']}] {citation['source']} - {citation['title']}\n"
                guide += f"   URL: {citation['url']}\n\n"

        if metrics:
            guide += "METRICS:\n"
            for metric in metrics:
                guide += f"- {metric['game']}: {metric['value']}\n"

        if testimonials:
            guide += "\nTESTIMONIALS:\n"
            for t in testimonials:
                guide += f"- {t['client']}: \"{t['quote'][:100]}...\"\n"

        return guide

    def _call_openrouter(self, prompt: str, max_tokens: int = 2048) -> str:
        """Call Claude via OpenRouter API"""
        url = "https://openrouter.ai/api/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://adriancrook.com",
            "X-Title": "AGC Content Engine v2",
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": max_tokens,  # Configurable per section
            "temperature": 0.3,  # Lower for more factual writing
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=300)
            response.raise_for_status()
            data = response.json()

            return data["choices"][0]["message"]["content"]

        except Exception as e:
            logger.error(f"OpenRouter API call failed: {e}")
            raise
