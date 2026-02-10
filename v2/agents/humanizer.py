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

        # Filter out empty or header-only sections
        filtered_sections = []
        for section in sections:
            # Count non-empty, non-header lines
            content_lines = [line for line in section.split('\n')
                           if line.strip() and not line.startswith('#')]
            # Only keep sections with actual content (at least 2 lines)
            if len(content_lines) >= 2:
                filtered_sections.append(section)
            else:
                logger.warning(f"Skipping empty/incomplete section: {section[:50]}...")

        return filtered_sections

    def _humanize_section(self, section: str) -> str:
        """Polish and refine a single section with Claude"""

        prompt = f"""Refine and polish this article section while maintaining professional quality.

ORIGINAL SECTION:
{section}

REFINEMENT GUIDELINES:
1. Maintain professional, authoritative tone throughout
2. Vary sentence structure and length for better flow
3. Add smooth transitions between paragraphs
4. Polish any awkward phrasings
5. Ensure logical progression of ideas
6. Keep the writing engaging but professional
7. **CRITICAL**: PRESERVE all citation links in [[n]](url) format EXACTLY as written
8. **CRITICAL**: PRESERVE the ## Sources section exactly if present
9. DO NOT add casual language, contractions, or personal opinions

IMPORTANT:
- Keep the same H2/H3 headers exactly
- Maintain the same structure and organization
- Preserve ALL factual content and citations
- DO NOT modify, remove, or reformat [[n]](url) citations
- DO NOT change URLs or citation numbers
- The goal is polish and flow, not casualization
- This should read like a high-quality professional blog post

Write the refined version with ALL citation links preserved:"""

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
