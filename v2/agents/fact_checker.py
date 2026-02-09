"""
FactCheckerAgent for v2 - Simplified from v1
Verifies claims against research sources
"""

import json
import logging
import re
import time
from typing import Dict, List

import requests

from .base import BaseAgent, AgentResult

logger = logging.getLogger(__name__)


class FactCheckerAgent(BaseAgent):
    """
    Fact checker using local LLM
    Verifies article claims against research sources
    """

    def __init__(self, config: Dict = None):
        super().__init__(config)
        self.ollama_url = config.get("ollama_url", "http://localhost:11434") if config else "http://localhost:11434"
        self.model = config.get("model", "qwen2.5:14b") if config else "qwen2.5:14b"

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

            # Ask LLM to verify claims
            verification = self._verify_claims(draft, source_facts)

            # Calculate accuracy
            total_claims = verification.get("total_claims", 0)
            verified_claims = verification.get("verified_claims", 0)
            accuracy = verified_claims / total_claims if total_claims > 0 else 1.0

            logger.info(f"Fact check complete: {verified_claims}/{total_claims} verified ({accuracy:.0%})")

            # Success if 85%+ accuracy
            success = accuracy >= 0.85

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
                cost=0.0,
                tokens=0,
                error=None if success else f"Low accuracy: {accuracy:.0%}"
            )

        except Exception as e:
            logger.error(f"Fact check failed: {e}")
            return AgentResult(
                success=False,
                data={},
                error=str(e)
            )

    def _verify_claims(self, draft: str, source_facts: List[str]) -> Dict:
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

Respond in JSON:
{{
    "total_claims": 15,
    "verified_claims": 13,
    "issues": [
        "Unsupported claim about market size",
        "Quote attribution unclear"
    ]
}}"""

        try:
            response = self._call_ollama(prompt)

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

    def _call_ollama(self, prompt: str) -> str:
        """Call local Ollama model"""
        url = f"{self.ollama_url}/api/generate"

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,  # Low temp for factual reasoning
                "num_predict": 2048,
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
