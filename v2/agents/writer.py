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

            # Generate Key Takeaways
            logger.info("Generating Key Takeaways")
            key_takeaways = self._generate_key_takeaways(topic, outline, sources)

            sections = []
            for section in outline.get("sections", []):
                logger.info(f"Writing section: {section.get('h2', '')}")
                section_content = self._write_section(topic, section, sources)
                sections.append(section_content)

            conclusion = self._write_conclusion(topic, outline, sources)

            # Generate FAQ section
            logger.info("Generating FAQ section")
            faq = self._generate_faq(topic, outline, sources)

            # Compile full article with all sections
            article_md = self._compile_article(
                outline.get("title", topic),
                intro,
                key_takeaways,
                sections,
                conclusion,
                faq,
                sources  # Pass sources for citation list
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

        # Build source context with numbered citations
        source_context = ""
        for i, s in enumerate(sources[:5], 1):
            source_context += f"\n[{i}] {s.get('title', '')}\n"
            source_context += f"URL: {s.get('url', '')}\n"
            if s.get('snippet'):
                source_context += f"Context: {s.get('snippet', '')[:200]}\n"
            for stat in s.get('key_stats', [])[:2]:
                source_context += f"  • Stat: {stat}\n"
            for quote in s.get('key_quotes', [])[:1]:
                source_context += f"  • Quote: \"{quote}\"\n"

        prompt = f"""Write a professional introduction for an article titled: "{outline.get('title', topic)}"

TOPIC: {topic}

AVAILABLE SOURCES (numbered for citation):
{source_context}

REQUIREMENTS:
1. Professional, authoritative tone (NOT casual or conversational)
2. Start with a compelling hook using a specific statistic or fact

3. **CRITICAL CITATION FORMAT**: Use clickable citation links like [[1]]({sources[0].get('url', '')}) at the END of sentences
   - Example: "The mobile gaming market reached $100 billion in 2024[[1]](https://example.com/source)."
   - Place citation AFTER the period/punctuation
   - Use the actual source URL from the numbered sources above

4. **CRITICAL GAME/COMPANY HYPERLINKS**: When mentioning mobile games or companies, hyperlink them
   - Games: [Clash Royale](https://supercell.com/en/games/clashroyale/)
   - Companies: [Supercell](https://supercell.com/)
   - Common games: Clash Royale, Candy Crush, Pokémon GO, Genshin Impact, etc.
   - Common companies: Supercell, King, Niantic, Riot Games, Tencent, etc.

5. NO personal opinions or phrases like "I think", "Let's be honest", "Here's the thing"
6. Focus on factual, data-driven insights
7. **CRITICAL: 200-250 words MAXIMUM - be concise**
8. Preview the key insights the article will cover
9. Cite at least 2-3 sources using the [[n]](url) format

Write ONLY the introduction text with proper [[n]](url) citations and game/company hyperlinks."""

        response = self._call_openrouter(prompt, max_tokens=600)
        return response.strip()

    def _write_section(self, topic: str, section: Dict, sources: List[Dict]) -> str:
        """Write a professional body section with citations"""

        h2 = section.get("h2", "")
        h3s = section.get("h3s", [])
        key_points = section.get("key_points", [])

        # Build comprehensive source context with numbered citations
        source_context = ""
        for i, s in enumerate(sources[:8], 1):
            source_context += f"\n[{i}] {s.get('title', '')}\n"
            source_context += f"URL: {s.get('url', '')}\n"
            for stat in s.get('key_stats', [])[:3]:
                source_context += f"  • Stat: {stat}\n"

            # Handle structured quotes (new format)
            for quote in s.get('key_quotes', [])[:2]:
                if isinstance(quote, dict):
                    quote_text = quote.get('text', '')
                    author = quote.get('author', '')
                    author_title = quote.get('author_title', '')
                    source_context += f"  • Quote: \"{quote_text}\"\n"
                    source_context += f"    Author: {author}"
                    if author_title:
                        source_context += f", {author_title}"
                    source_context += "\n"
                else:
                    # Fallback for old string format
                    source_context += f"  • Quote: \"{quote}\"\n"

        prompt = f"""Write a professional article section for: "{topic}"

SECTION HEADER: {h2}

SUBSECTIONS TO COVER:
{json.dumps(h3s, indent=2)}

KEY POINTS TO ADDRESS:
{json.dumps(key_points, indent=2)}

AVAILABLE SOURCES (numbered for citation):
{source_context}

REQUIREMENTS:
1. Professional, authoritative tone - NO casual language
2. Use ## {h2} for main header
3. Use ### for subsections from the list above

4. **CRITICAL CITATION FORMAT**: Use clickable citation links like [[1]](url), [[2]](url) at the END of sentences
   - Example: "Clash Royale generated over $4 billion in lifetime revenue[[3]](https://example.com/source)."
   - Place citation AFTER the period/punctuation
   - Use the actual source URLs from the numbered sources above

5. **CRITICAL EXPERT QUOTE FORMAT**: Format quotes as blockquotes with attribution and citation
   - Use markdown blockquote syntax (lines starting with >)
   - Include attribution on a second line with — (em dash)
   - Include citation link after attribution
   - Example format:
     > "Users should do something fun as soon as they open your mobile game"
     > — GameAnalytics[[5]](https://gameanalytics.com/blog)

6. **CRITICAL GAME/COMPANY HYPERLINKS**: When mentioning mobile games or companies, hyperlink them on FIRST mention
   - Games: [Clash Royale](https://supercell.com/en/games/clashroyale/)
   - Companies: [Supercell](https://supercell.com/)
   - Only hyperlink the FIRST mention in each section
   - Common games to link: Clash Royale, Candy Crush, Pokémon GO, Genshin Impact, PUBG Mobile, etc.
   - Common companies to link: Supercell, King, Niantic, Riot Games, Tencent, etc.

7. CITE ALL FACTS: Every statistic, data point, or claim needs a [[n]](url) citation
8. NO personal opinions, contractions, or phrases like "honestly", "let me tell you"
9. Every claim must be backed by source material with proper citation links
10. **CRITICAL: 400-500 words MAXIMUM - be concise and focused**
11. Include at least 1 expert quote in blockquote format per section (if available in sources)
12. Use at least 3-5 [[n]](url) citations throughout the section

Write the complete section in Markdown with proper [[n]](url) citations, blockquoted expert quotes, and game/company hyperlinks."""

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
3. NO new citations needed in conclusion (summary only)
4. Look forward to future trends/implications
5. End with a clear takeaway
6. **CRITICAL: 150-200 words MAXIMUM**
7. NO call-to-action or sales language

Write ONLY the conclusion text."""

        response = self._call_openrouter(prompt, max_tokens=500)
        return response.strip()

    def _generate_key_takeaways(self, topic: str, outline: Dict, sources: List[Dict]) -> str:
        """Generate Key Takeaways bullet list from article content"""

        # Build context from outline and sources
        section_summaries = []
        for section in outline.get("sections", [])[:5]:
            section_summaries.append(f"- {section.get('h2', '')}")

        # Get key stats
        key_stats = []
        for s in sources[:5]:
            for stat in s.get('key_stats', [])[:2]:
                key_stats.append(stat)

        prompt = f"""Generate Key Takeaways for an article titled: "{outline.get('title', topic)}"

TOPIC: {topic}

ARTICLE SECTIONS:
{chr(10).join(section_summaries)}

KEY STATISTICS:
{chr(10).join(f"- {stat}" for stat in key_stats[:8])}

REQUIREMENTS:
1. Create 4-5 actionable key takeaways
2. Format: **[Bold Action/Insight]:** Brief explanation (1 sentence)
3. Each takeaway should be specific and data-driven
4. Focus on practical insights readers can use
5. Use strong action verbs (Leverage, Optimize, Implement, Focus on, etc.)
6. Keep each takeaway to 15-25 words
7. NO vague language - be specific

EXACT FORMAT TO USE:
**Key Takeaways:**
- **[Action 1]:** Brief explanation with specific detail.
- **[Action 2]:** Brief explanation with specific detail.
- **[Action 3]:** Brief explanation with specific detail.
- **[Action 4]:** Brief explanation with specific detail.

EXAMPLE:
**Key Takeaways:**
- **Prioritize hybrid monetization:** Combine in-app purchases with rewarded video ads to maximize revenue across both paying and non-paying users.
- **Target high-ARPU markets:** Focus on US, Japan, and China where mobile gamers spend $60+ annually per user.

Write ONLY the Key Takeaways section (4-5 bullets) using the exact format above:"""

        response = self._call_openrouter(prompt, max_tokens=400)
        return response.strip()

    def _generate_faq(self, topic: str, outline: Dict, sources: List[Dict]) -> str:
        """Generate FAQ section with 3 questions"""

        # Build context from outline
        section_summaries = []
        for section in outline.get("sections", []):
            section_summaries.append(section.get('h2', ''))

        prompt = f"""Generate an FAQ section for an article titled: "{outline.get('title', topic)}"

TOPIC: {topic}

ARTICLE COVERS:
{chr(10).join(f"- {s}" for s in section_summaries)}

REQUIREMENTS:
1. Create exactly 3 frequently asked questions
2. Questions should cover different aspects of the topic
3. Answers should be concise (50-75 words each)
4. Use ### for each question header
5. Answer should be practical and specific
6. NO sales language or calls to action

EXACT FORMAT TO USE:
## FAQs

### [Question 1]?
[Answer with specific details and insights]

### [Question 2]?
[Answer with specific details and insights]

### [Question 3]?
[Answer with specific details and insights]

EXAMPLE:
## FAQs

### What is the most profitable mobile game monetization model?
Hybrid monetization combining in-app purchases with rewarded video ads generates the highest revenue. This model caters to both paying users through IAP and non-paying users through ads, maximizing lifetime value across your entire player base.

Write ONLY the FAQ section with exactly 3 questions using the format above:"""

        response = self._call_openrouter(prompt, max_tokens=800)
        return response.strip()

    def _generate_sources_section(self, sources: List[Dict]) -> str:
        """Generate the Sources section with numbered citations"""
        sources_lines = ["## Sources", ""]

        for i, source in enumerate(sources, 1):
            title = source.get('title', 'Source')
            url = source.get('url', '')

            # Format: [1] Title - URL
            sources_lines.append(f"[{i}] {title} - {url}")

        return "\n".join(sources_lines)

    def _compile_article(self, title: str, intro: str, key_takeaways: str, sections: List[str], conclusion: str, faq: str, sources: List[Dict] = None) -> str:
        """Compile all parts into final article with key takeaways, FAQ, and sources"""

        parts = [
            f"# {title}",
            "",
            intro,
            "",
            key_takeaways,  # Key Takeaways right after intro
            "",
        ]

        for section in sections:
            parts.append(section)
            parts.append("")

        parts.append("## Conclusion")
        parts.append("")
        parts.append(conclusion)
        parts.append("")
        parts.append("")

        # Add FAQ section
        parts.append(faq)

        # Add Sources section if sources provided
        if sources:
            parts.append("")
            parts.append("")
            sources_section = self._generate_sources_section(sources)
            parts.append(sources_section)

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
