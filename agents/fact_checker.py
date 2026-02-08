"""
Fact Checker Agent - Verifies claims and citations.

Model: deepseek-r1:14b (local) - good at reasoning
"""

import json
import logging
import re
import time
from dataclasses import dataclass
from typing import Dict, List, Optional

from .base import BaseAgent, AgentInput, AgentOutput

logger = logging.getLogger(__name__)


@dataclass
class Claim:
    """A factual claim to verify."""
    text: str
    location: str  # Where in article
    category: str  # stat, quote, date, general
    verified: bool = False
    source_url: Optional[str] = None
    confidence: float = 0.0
    correction: Optional[str] = None


class FactCheckerAgent(BaseAgent):
    """
    Fact checker agent that verifies claims in articles.
    
    Uses reasoning-focused LLM for verification logic.
    """
    
    def __init__(
        self,
        ollama_url: str = "http://localhost:11434",
        model: str = "deepseek-r1:14b",
    ):
        super().__init__(
            name="fact_checker",
            model=model,
            model_type="ollama",
            ollama_url=ollama_url,
            temperature=0.1,  # Low temp for factual reasoning
            max_tokens=4096,
        )
    
    def run(self, input: AgentInput) -> AgentOutput:
        """
        Verify facts in an article.
        
        Input data:
            - article: str - The article markdown
            - sources: List[Dict] - Research sources to verify against
        """
        start_time = time.time()
        errors = []
        
        article = input.data.get("article", "")
        sources = input.data.get("sources", [])
        
        if not article:
            return AgentOutput(
                data={},
                success=False,
                errors=["No article provided"],
            )
        
        logger.info("Starting fact check")
        
        # Step 1: Extract claims from article
        claims = self._extract_claims(article)
        logger.info(f"Extracted {len(claims)} claims to verify")
        
        # Step 2: Build source index
        source_index = self._build_source_index(sources)
        
        # Step 3: Verify each claim
        verified_claims = []
        for claim in claims:
            verified = self._verify_claim(claim, source_index, article)
            verified_claims.append(verified)
        
        # Step 4: Calculate accuracy score
        total_claims = len(verified_claims)
        verified_count = sum(1 for c in verified_claims if c.verified)
        high_confidence = sum(1 for c in verified_claims if c.confidence >= 0.8)
        
        accuracy_score = verified_count / total_claims if total_claims > 0 else 0
        
        # Step 5: Generate corrections
        corrections_needed = [c for c in verified_claims if not c.verified]
        
        # Step 6: Create corrected article if needed
        corrected_article = article
        if corrections_needed:
            corrected_article = self._apply_corrections(article, corrections_needed)
        
        duration = time.time() - start_time
        
        output_data = {
            "total_claims": total_claims,
            "verified_claims": verified_count,
            "high_confidence_claims": high_confidence,
            "accuracy_score": accuracy_score,
            "claims": [self._claim_to_dict(c) for c in verified_claims],
            "corrections_needed": len(corrections_needed),
            "corrected_article": corrected_article if corrections_needed else None,
        }
        
        # Success if 90%+ claims verified OR all corrections applied
        success = accuracy_score >= 0.9 or corrected_article != article
        
        if accuracy_score < 0.9:
            errors.append(f"Accuracy score {accuracy_score:.0%} below 90% threshold")
        
        return AgentOutput(
            data=output_data,
            success=success,
            errors=errors,
            duration_seconds=duration,
        )
    
    def validate_output(self, output: AgentOutput) -> bool:
        """Check if fact check meets quality gate."""
        data = output.data
        
        # Need 90%+ accuracy
        if data.get("accuracy_score", 0) < 0.9:
            return False
        
        return True
    
    def _extract_claims(self, article: str) -> List[Claim]:
        """Extract verifiable claims from article."""
        prompt = f"""Analyze this article and extract ALL verifiable factual claims.

Article:
{article[:6000]}  # Truncate for context window

For each claim, identify:
- The exact claim text
- Category: "statistic", "quote", "date", "fact"
- Location: section heading where it appears

Focus on:
- Numbers and percentages
- Dates and timelines
- Quoted statements
- Specific facts that could be wrong

Return as JSON:
{{
    "claims": [
        {{"text": "claim text", "category": "statistic", "location": "Introduction"}}
    ]
}}"""

        try:
            response = self._call_model(prompt)
            
            # Parse JSON
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]
            
            data = json.loads(response.strip())
            
            claims = []
            for c in data.get("claims", []):
                claims.append(Claim(
                    text=c.get("text", ""),
                    category=c.get("category", "fact"),
                    location=c.get("location", "unknown"),
                ))
            
            return claims
        
        except Exception as e:
            logger.error(f"Failed to extract claims: {e}")
            return []
    
    def _build_source_index(self, sources: List[Dict]) -> Dict:
        """Build searchable index of sources."""
        index = {
            "by_stat": {},  # stat text -> source
            "by_quote": {},  # quote text -> source
            "all_sources": sources,
        }
        
        for source in sources:
            for stat in source.get("key_stats", []):
                # Extract numbers from stat
                numbers = re.findall(r'\d+\.?\d*%?', stat)
                for num in numbers:
                    index["by_stat"][num] = source
            
            for quote in source.get("key_quotes", []):
                # Index by first 50 chars
                key = quote[:50].lower()
                index["by_quote"][key] = source
        
        return index
    
    def _verify_claim(self, claim: Claim, source_index: Dict, article: str) -> Claim:
        """Verify a single claim against sources."""
        
        # Quick lookup for statistics
        if claim.category == "statistic":
            numbers = re.findall(r'\d+\.?\d*%?', claim.text)
            for num in numbers:
                if num in source_index["by_stat"]:
                    source = source_index["by_stat"][num]
                    claim.verified = True
                    claim.source_url = source.get("url", "")
                    claim.confidence = 0.9
                    return claim
        
        # Use LLM for complex verification
        prompt = f"""Verify this claim using the provided sources.

Claim: {claim.text}
Category: {claim.category}

Available sources:
{json.dumps([{'url': s.get('url'), 'title': s.get('title'), 'snippet': s.get('snippet', '')[:200]} for s in source_index['all_sources'][:10]], indent=2)}

Analyze:
1. Is this claim verifiable from the sources?
2. Is it likely accurate based on your knowledge?
3. If inaccurate, what's the correction?

Respond in JSON:
{{
    "verified": true/false,
    "confidence": 0.0-1.0,
    "source_url": "url if found" or null,
    "reasoning": "brief explanation",
    "correction": "corrected text if needed" or null
}}"""

        try:
            response = self._call_model(prompt)
            
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]
            
            data = json.loads(response.strip())
            
            claim.verified = data.get("verified", False)
            claim.confidence = data.get("confidence", 0.5)
            claim.source_url = data.get("source_url")
            claim.correction = data.get("correction")
            
        except Exception as e:
            logger.warning(f"Failed to verify claim: {e}")
            claim.verified = False
            claim.confidence = 0.3
        
        return claim
    
    def _apply_corrections(self, article: str, corrections: List[Claim]) -> str:
        """Apply corrections to article."""
        corrected = article
        
        for claim in corrections:
            if claim.correction:
                # Simple text replacement
                corrected = corrected.replace(claim.text, claim.correction)
        
        return corrected
    
    def _claim_to_dict(self, claim: Claim) -> Dict:
        """Convert claim to dictionary."""
        return {
            "text": claim.text,
            "location": claim.location,
            "category": claim.category,
            "verified": claim.verified,
            "confidence": claim.confidence,
            "source_url": claim.source_url,
            "correction": claim.correction,
        }
