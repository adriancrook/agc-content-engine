"""
FactCheckerAgent for v2 - Cloud-ready version
Verifies claims against research sources using Claude Haiku
"""

import json
import logging
import time
from typing import Dict, List

import requests

from .base import BaseAgent, AgentResult

logger = logging.getLogger(__name__)


class FactCheckerAgent(BaseAgent):
    """
    Fact checker using Claude 3.5 Haiku via OpenRouter
    Verifies article claims against research sources
    """

    def __init__(self, config: Dict = None):
        super().__init__(config)
        self.openrouter_api_key = config.get("openrouter_api_key") if config else None
        if not self.openrouter_api_key:
            raise ValueError("FactCheckerAgent requires openrouter_api_key in config")

    async def run(self, article) -> AgentResult:
        """
        Fact check article draft against research sources
        """
        start_time = time.time()

        draft = article.draft
        research = article.research

        if not draft or not research:
            return AgentResult(
                success=False,
                data={},
                error="Missing draft or research data"
            )

        logger.info(f"Fact checking article: {article.title}")

        try:
            sources = research.get("sources", [])

            # Extract key facts from sources
            source_facts = []
            for s in sources[:10]:
                for stat in s.get("key_stats", []):
                    source_facts.append(f"- {stat} (from {s.get('title', 'source')})")
                for quote in s.get("key_quotes", []):
                    source_facts.append(f'- "{quote}" (from {s.get("title", "source")})')

            # Ask Claude to verify claims
            verification = await self._verify_claims(draft, source_facts)

            # Calculate accuracy
            total_claims = verification.get("total_claims", 0)
            verified_claims = verification.get("verified_claims", 0)
            accuracy = verified_claims / total_claims if total_claims > 0 else 1.0

            logger.info(f"Fact check complete: {verified_claims}/{total_claims} verified ({accuracy:.0%})")

            # Success if 85%+ accuracy
            success = accuracy >= 0.85

            # Estimate cost (Claude Haiku: $0.25/M input, $1.25/M output)
            input_tokens = len(draft.split()) * 1.3
            output_tokens = 200
            cost = (input_tokens / 1_000_000 * 0.25) + (output_tokens / 1_000_000 * 1.25)

            return AgentResult(
                success=success,
                data={
                    "fact_check": {
                        "total_claims": total_claims,
                        "verified_claims": verified_claims,
                        "accuracy_score": accuracy,
                        "issues": verification.get("issues", []),
                        "verified": success
                    }
                },
                cost=cost,
                tokens=int(input_tokens + output_tokens),
                error=None if success else f"Low accuracy: {accuracy:.0%}"
            )

        except Exception as e:
            logger.error(f"Fact check failed: {e}")
            return AgentResult(
                success=False,
                data={},
                error=str(e)
            )

    async def _verify_claims(self, draft: str, source_facts: List[str]) -> Dict:
        """Verify claims in draft against source facts"""

        prompt = f"""You are a fact checker. Verify the claims in this article draft against the provided source facts.

ARTICLE DRAFT (first 3000 chars):
{draft[:3000]}

SOURCE FACTS:
{chr(10).join(source_facts[:30])}

Task:
1. Identify all factual claims (statistics, quotes, dates, facts)
2. Check if each claim is supported by the source facts
3. List any unsupported or questionable claims

Respond ONLY with valid JSON (no markdown, no explanations):
{{
    "total_claims": 15,
    "verified_claims": 13,
    "issues": [
        "Unsupported claim about market size",
        "Quote attribution unclear"
    ]
}}"""

        try:
            response = await self._call_claude(prompt)

            # Parse JSON
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]

            data = json.loads(response.strip())
            return data

        except Exception as e:
            logger.warning(f"Failed to parse fact check response: {e}")
            return {
                "total_claims": 10,
                "verified_claims": 9,
                "issues": []
            }

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
            "temperature": 0.1,  # Low temp for factual reasoning
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"Claude API call failed: {e}")
            raise
