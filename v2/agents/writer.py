"""
WriterAgent for v2 - Adapted from v1
Creates article drafts from research using local LLM
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
    Writer agent using local LLM (qwen2.5:14b)
    Creates long-form article drafts from research
    """

    def __init__(self, config: Dict = None):
        super().__init__(config)
        self.ollama_url = config.get("ollama_url", "http://localhost:11434") if config else "http://localhost:11434"
        self.model = config.get("model", "qwen2.5:14b") if config else "qwen2.5:14b"
        self.target_word_count = config.get("target_word_count", 2500) if config else 2500

    async def run(self, article) -> AgentResult:
        """
        Generate article draft from research
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

        logger.info(f"Writing draft for: {topic}")

        try:
            # Step 1: Introduction
            intro = self._write_introduction(topic, outline, sources)

            # Step 2: Body sections
            sections_md = []
            for section in outline.get("sections", []):
                section_md = self._write_section(topic, section, sources)
                sections_md.append(section_md)

            # Step 3: Conclusion
            conclusion = self._write_conclusion(topic, outline)

            # Step 4: Compile full article
            article_md = self._compile_article(
                title=outline.get("title", topic),
                intro=intro,
                sections=sections_md,
                conclusion=conclusion
            )

            # Count words
            word_count = len(article_md.split())

            logger.info(f"Draft complete: {word_count} words")

            success = word_count >= self.target_word_count * 0.8

            return AgentResult(
                success=success,
                data={"draft": article_md},
                cost=0.0,
                tokens=0,
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
        """Write engaging introduction"""

        # Build source context
        source_context = ""
        for s in sources[:3]:
            source_context += f"- {s.get('title', '')}: {s.get('snippet', '')[:150]}\n"
            for stat in s.get('key_stats', [])[:1]:
                source_context += f"  • {stat}\n"

        prompt = f"""Write an engaging introduction for: "{outline.get('title', topic)}"

Topic: {topic}

Key information:
{source_context}

Guidelines:
- Start with a hook (stat, question, or bold statement)
- Explain why this matters now
- Preview what reader will learn
- 150-200 words
- Conversational but informative tone

Write ONLY the introduction text."""

        response = self._call_ollama(prompt)
        return response.strip()

    def _write_section(self, topic: str, section: Dict, sources: List[Dict]) -> str:
        """Write a body section"""

        h2 = section.get("h2", "")
        h3s = section.get("h3s", [])
        key_points = section.get("key_points", [])

        # Find relevant sources
        relevant_info = ""
        for s in sources[:5]:
            for stat in s.get('key_stats', [])[:2]:
                relevant_info += f"- {stat}\n"
            for quote in s.get('key_quotes', [])[:1]:
                relevant_info += f'- "{quote}"\n'

        prompt = f"""Write section: "{h2}" for article about "{topic}"

Subsections to cover:
{json.dumps(h3s, indent=2)}

Key points:
{json.dumps(key_points, indent=2)}

Supporting information:
{relevant_info}

Guidelines:
- Use ## {h2} for main header
- Use ### for subsections
- Include specific stats and quotes
- 400-600 words
- Conversational but authoritative
- Add concrete examples

Write the complete section in Markdown."""

        response = self._call_ollama(prompt)
        return response.strip()

    def _write_conclusion(self, topic: str, outline: Dict) -> str:
        """Write conclusion"""

        sections = [s.get("h2", "") for s in outline.get("sections", [])]

        prompt = f"""Write conclusion for article about "{topic}"

Sections covered:
{json.dumps(sections, indent=2)}

Guidelines:
- Summarize 3-4 key takeaways
- End with actionable advice
- Forward-looking perspective
- 150-200 words
- Inspiring but practical

Write ONLY the conclusion text."""

        response = self._call_ollama(prompt)
        return response.strip()

    def _compile_article(self, title: str, intro: str, sections: List[str], conclusion: str) -> str:
        """Compile full article in Markdown"""

        parts = [
            f"# {title}\n",
            intro,
            "",
        ]

        for section in sections:
            parts.append(section)
            parts.append("")

        parts.append("## Conclusion\n")
        parts.append(conclusion)

        return "\n".join(parts)

    def _call_ollama(self, prompt: str) -> str:
        """Call local Ollama model"""
        url = f"{self.ollama_url}/api/generate"

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "num_predict": 8192,  # Long-form content
            }
        }

        try:
            response = requests.post(url, json=payload, timeout=600)  # 10 min timeout
            response.raise_for_status()
            result = response.json()
            return result.get("response", "")
        except Exception as e:
            logger.error(f"Ollama call failed: {e}")
            raise
