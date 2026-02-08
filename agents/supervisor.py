"""
Supervisor Agent - Orchestrates pipeline and performs final QA.

Model: Claude Opus (cloud) - best reasoning for QA
"""

import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import anthropic

from .base import BaseAgent, AgentInput, AgentOutput

logger = logging.getLogger(__name__)


class SupervisorAgent(BaseAgent):
    """
    Supervisor agent that orchestrates the pipeline and performs QA.
    
    Uses Claude Opus for highest quality reasoning and decision making.
    
    Responsibilities:
    1. Validate inputs before starting
    2. Check quality gates between stages
    3. Decide on retries vs. proceeding
    4. Final QA before publishing
    5. Track costs and timing
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-opus-4-20250514",
    ):
        super().__init__(
            name="supervisor",
            model=model,
            model_type="anthropic",
            api_key=api_key or os.getenv("ANTHROPIC_API_KEY"),
            temperature=0.3,  # Lower creativity for consistency
            max_tokens=4096,
        )
        
        self.stage_costs = {}
        self.stage_times = {}
    
    def run(self, input: AgentInput) -> AgentOutput:
        """
        Perform final QA on completed article.
        
        Input data:
            - final_article: str - The completed article
            - research_data: Dict - Original research
            - all_outputs: List[Dict] - Outputs from all stages
        """
        start_time = time.time()
        errors = []
        
        final_article = input.data.get("final_article", "")
        research_data = input.data.get("research_data", {})
        all_outputs = input.data.get("all_outputs", [])
        
        if not final_article:
            return AgentOutput(
                data={},
                success=False,
                errors=["No final article provided"],
            )
        
        logger.info("Starting final QA review")
        
        # Step 1: Comprehensive quality check
        quality_report = self._comprehensive_quality_check(final_article, research_data)
        
        # Step 2: Fact verification sample
        fact_check = self._sample_fact_check(final_article, research_data.get("sources", []))
        
        # Step 3: SEO final check
        seo_check = self._seo_final_check(final_article)
        
        # Step 4: Readability analysis
        readability = self._analyze_readability(final_article)
        
        # Step 5: AI detection risk assessment
        ai_risk = self._assess_ai_detection_risk(final_article)
        
        # Step 6: Calculate final scores
        overall_score = self._calculate_overall_score(
            quality=quality_report.get("score", 0),
            facts=fact_check.get("score", 0),
            seo=seo_check.get("score", 0),
            readability=readability.get("score", 0),
            ai_risk=ai_risk.get("score", 0),
        )
        
        # Step 7: Generate publishing recommendation
        recommendation = self._generate_recommendation(
            overall_score=overall_score,
            quality_report=quality_report,
            fact_check=fact_check,
            seo_check=seo_check,
        )
        
        # Step 8: Calculate total pipeline cost
        total_cost = sum(o.get("cost_usd", 0) for o in all_outputs)
        total_time = sum(o.get("duration_seconds", 0) for o in all_outputs)
        
        duration = time.time() - start_time
        
        output_data = {
            "overall_score": overall_score,
            "quality_report": quality_report,
            "fact_check": fact_check,
            "seo_check": seo_check,
            "readability": readability,
            "ai_detection_risk": ai_risk,
            "recommendation": recommendation,
            "pipeline_metrics": {
                "total_cost_usd": total_cost,
                "total_time_seconds": total_time,
                "supervisor_time_seconds": duration,
                "stage_count": len(all_outputs),
            },
            "approved_for_publishing": overall_score >= 75 and recommendation.get("approve", False),
        }
        
        success = overall_score >= 75
        
        if overall_score < 75:
            errors.append(f"Overall score {overall_score} below 75 threshold")
        
        # Estimate supervisor cost
        cost = 0.05  # Rough estimate for Opus usage
        
        return AgentOutput(
            data=output_data,
            success=success,
            errors=errors,
            duration_seconds=duration,
            cost_usd=cost,
        )
    
    def validate_output(self, output: AgentOutput) -> bool:
        """Check if QA passes."""
        return output.data.get("approved_for_publishing", False)
    
    def check_stage_output(
        self,
        stage_name: str,
        output: AgentOutput,
        min_score: int = 70,
    ) -> Dict:
        """Check if a stage's output passes quality gate."""
        
        # Track metrics
        self.stage_costs[stage_name] = output.cost_usd
        self.stage_times[stage_name] = output.duration_seconds
        
        result = {
            "stage": stage_name,
            "passed": output.success,
            "errors": output.errors,
            "cost": output.cost_usd,
            "duration": output.duration_seconds,
        }
        
        if not output.success:
            result["recommendation"] = "retry"
            result["reason"] = output.errors[0] if output.errors else "Unknown failure"
        else:
            result["recommendation"] = "proceed"
        
        return result
    
    def _comprehensive_quality_check(self, article: str, research: Dict) -> Dict:
        """Deep quality analysis using Opus."""
        
        sources = research.get("sources", [])
        topic = research.get("topic", "")
        
        prompt = f"""Perform a comprehensive quality review of this article.

TOPIC: {topic}

AVAILABLE SOURCES:
{json.dumps([s.get('title', '') for s in sources[:10]], indent=2)}

ARTICLE:
{article[:8000]}

Evaluate on these criteria (score each 0-100):

1. **Accuracy**: Are facts and claims well-supported?
2. **Completeness**: Does it cover the topic thoroughly?
3. **Originality**: Does it offer unique insights vs competitors?
4. **Structure**: Is it well-organized with clear flow?
5. **Engagement**: Is it interesting and compelling to read?
6. **Actionability**: Does the reader learn something useful?

Respond in JSON:
{{
    "scores": {{
        "accuracy": 85,
        "completeness": 80,
        "originality": 75,
        "structure": 90,
        "engagement": 70,
        "actionability": 80
    }},
    "overall_score": 80,
    "strengths": ["list of 2-3 strengths"],
    "weaknesses": ["list of 2-3 weaknesses"],
    "suggestions": ["list of specific improvements"]
}}"""

        try:
            response = self._call_anthropic(prompt)
            
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]
            
            data = json.loads(response.strip())
            data["score"] = data.get("overall_score", 0)
            return data
        
        except Exception as e:
            logger.error(f"Quality check failed: {e}")
            return {"score": 50, "error": str(e)}
    
    def _sample_fact_check(self, article: str, sources: List[Dict]) -> Dict:
        """Spot-check a sample of facts."""
        
        prompt = f"""Verify the accuracy of key claims in this article.

AVAILABLE SOURCES:
{json.dumps([{'title': s.get('title', ''), 'url': s.get('url', '')} for s in sources[:10]], indent=2)}

ARTICLE EXCERPT:
{article[:4000]}

Tasks:
1. Identify the 5 most important factual claims
2. Check if each is supported by the sources
3. Flag any potentially inaccurate claims

Respond in JSON:
{{
    "claims_checked": 5,
    "verified": 4,
    "unverified": 1,
    "accuracy_rate": 0.8,
    "flagged_claims": ["claim that couldn't be verified"],
    "score": 80
}}"""

        try:
            response = self._call_anthropic(prompt)
            
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]
            
            return json.loads(response.strip())
        
        except Exception as e:
            logger.error(f"Fact check failed: {e}")
            return {"score": 50, "error": str(e)}
    
    def _seo_final_check(self, article: str) -> Dict:
        """Final SEO verification."""
        import re
        
        checks = {
            "has_h1": bool(re.search(r'^# ', article, re.MULTILINE)),
            "has_h2s": len(re.findall(r'^## ', article, re.MULTILINE)) >= 4,
            "word_count": len(article.split()) >= 2000,
            "has_links": bool(re.search(r'\[.+?\]\(.+?\)', article)),
            "has_lists": bool(re.search(r'^[\-\*] ', article, re.MULTILINE)),
        }
        
        passed = sum(checks.values())
        total = len(checks)
        
        return {
            "checks": checks,
            "passed": passed,
            "total": total,
            "score": int((passed / total) * 100),
        }
    
    def _analyze_readability(self, article: str) -> Dict:
        """Analyze readability metrics."""
        words = article.split()
        sentences = article.replace('!', '.').replace('?', '.').split('.')
        sentences = [s for s in sentences if s.strip()]
        
        word_count = len(words)
        sentence_count = len(sentences)
        avg_sentence_length = word_count / sentence_count if sentence_count > 0 else 0
        
        # Simple Flesch-like score estimation
        # Ideal: 60-70 for general audience
        if 12 <= avg_sentence_length <= 20:
            score = 80
        elif 10 <= avg_sentence_length <= 25:
            score = 70
        else:
            score = 50
        
        return {
            "word_count": word_count,
            "sentence_count": sentence_count,
            "avg_sentence_length": round(avg_sentence_length, 1),
            "score": score,
        }
    
    def _assess_ai_detection_risk(self, article: str) -> Dict:
        """Estimate risk of AI detection."""
        
        # Count AI pattern indicators
        ai_phrases = [
            "it's important to note", "in conclusion", "let's dive",
            "in today's world", "first and foremost", "last but not least",
        ]
        
        found = []
        text_lower = article.lower()
        for phrase in ai_phrases:
            if phrase in text_lower:
                found.append(phrase)
        
        # Sentence variance
        sentences = article.replace('!', '.').replace('?', '.').split('.')
        lengths = [len(s.split()) for s in sentences if s.strip()]
        
        if lengths:
            avg = sum(lengths) / len(lengths)
            variance = sum((l - avg) ** 2 for l in lengths) / len(lengths)
        else:
            variance = 0
        
        # Low variance = higher AI risk
        variance_risk = "high" if variance < 20 else "medium" if variance < 40 else "low"
        
        # Calculate overall risk score (higher = safer)
        risk_score = 100 - (len(found) * 10) - (30 if variance < 20 else 0)
        risk_score = max(0, min(100, risk_score))
        
        return {
            "ai_phrases_found": found,
            "sentence_variance": round(variance, 1),
            "variance_risk": variance_risk,
            "score": risk_score,
            "risk_level": "low" if risk_score >= 70 else "medium" if risk_score >= 50 else "high",
        }
    
    def _calculate_overall_score(
        self,
        quality: int,
        facts: int,
        seo: int,
        readability: int,
        ai_risk: int,
    ) -> int:
        """Calculate weighted overall score."""
        weights = {
            "quality": 0.30,
            "facts": 0.25,
            "seo": 0.20,
            "readability": 0.15,
            "ai_risk": 0.10,
        }
        
        score = (
            quality * weights["quality"] +
            facts * weights["facts"] +
            seo * weights["seo"] +
            readability * weights["readability"] +
            ai_risk * weights["ai_risk"]
        )
        
        return int(score)
    
    def _generate_recommendation(
        self,
        overall_score: int,
        quality_report: Dict,
        fact_check: Dict,
        seo_check: Dict,
    ) -> Dict:
        """Generate publishing recommendation."""
        
        approve = overall_score >= 75
        
        if overall_score >= 85:
            confidence = "high"
            action = "Approve for immediate publishing"
        elif overall_score >= 75:
            confidence = "medium"
            action = "Approve with minor review"
        elif overall_score >= 60:
            confidence = "low"
            action = "Needs revision before publishing"
        else:
            confidence = "none"
            action = "Significant rewrite required"
        
        return {
            "approve": approve,
            "confidence": confidence,
            "action": action,
            "overall_score": overall_score,
            "timestamp": datetime.now().isoformat(),
        }
