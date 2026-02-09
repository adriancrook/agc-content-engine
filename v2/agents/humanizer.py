"""
HumanizerAgent for v2 - Uses Claude via OpenRouter
Makes AI content undetectable by adding natural variations
"""

import logging
import time
from typing import Dict

import requests

from .base import BaseAgent, AgentResult

logger = logging.getLogger(__name__)


class HumanizerAgent(BaseAgent):
    """
    Humanizer using Claude Sonnet via OpenRouter
    Rewrites content to pass AI detection
    """

    def __init__(self, config: Dict = None):
        super().__init__(config)
        self.api_key = config.get("openrouter_api_key") if config else None
        self.model = "anthropic/claude-sonnet-4"

        if not self.api_key:
            raise ValueError("OpenRouter API key required for humanizer agent")

    async def run(self, article) -> AgentResult:
        """
        Humanize article to pass AI detection
        """
        start_time = time.time()

        # Get content from SEO stage
        seo_data = article.seo
        draft = article.draft

        if not draft:
            return AgentResult(
                success=False,
                data={},
                error="No draft content found"
            )

        logger.info(f"Humanizing article: {article.title}")

        try:
            # Humanize section by section
            sections = self._split_sections(draft)
            humanized_sections = []

            for i, section in enumerate(sections):
                logger.info(f"Humanizing section {i+1}/{len(sections)}")
                humanized = self._humanize_section(section)
                humanized_sections.append(humanized)

            # Compile final content
            final_content = "\n\n".join(humanized_sections)
            word_count = len(final_content.split())

            logger.info(f"Humanization complete: {word_count} words")

            # Estimate cost (Claude Sonnet pricing)
            tokens_used = word_count * 1.5  # Rough estimate
            cost = (tokens_used / 1_000_000) * 3.0  # $3 per 1M tokens

            return AgentResult(
                success=True,
                data={"final_content": final_content},
                cost=cost,
                tokens=int(tokens_used),
                error=None
            )

        except Exception as e:
            logger.error(f"Humanization failed: {e}")
            return AgentResult(
                success=False,
                data={},
                error=str(e)
            )

    def _split_sections(self, draft: str) -> list:
        """Split article into manageable sections"""
        sections = []
        current_section = []

        for line in draft.split('\n'):
            if line.startswith('## ') and current_section:
                # New section - save previous
                sections.append('\n'.join(current_section))
                current_section = [line]
            else:
                current_section.append(line)

        # Add final section
        if current_section:
            sections.append('\n'.join(current_section))

        return sections

    def _humanize_section(self, section: str) -> str:
        """Humanize a single section with Claude"""

        prompt = f"""Rewrite this section to make it undetectable by AI detection tools.

ORIGINAL SECTION:
{section}

HUMANIZATION GUIDELINES:
1. Vary sentence structure and length dramatically
2. Add natural imperfections (contractions, informal phrases)
3. Include personal touches and opinions
4. Use unexpected word choices
5. Break predictable AI patterns
6. Add transitional phrases that feel human
7. Vary paragraph lengths (some short, some long)
8. Keep all factual information accurate

IMPORTANT:
- Maintain the same H2/H3 headers
- Keep the same general structure
- Preserve all statistics and quotes
- Make it sound like a real person wrote it

Write the humanized version:"""

        response = self._call_openrouter(prompt)
        return response.strip()

    def _call_openrouter(self, prompt: str) -> str:
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
            "max_tokens": 8192,
            "temperature": 0.8,  # High for creativity
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=300)
            response.raise_for_status()
            data = response.json()

            return data["choices"][0]["message"]["content"]

        except Exception as e:
            logger.error(f"OpenRouter API call failed: {e}")
            raise
