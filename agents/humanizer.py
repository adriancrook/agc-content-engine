"""
Humanizer Agent - Makes AI content undetectable.

Model: Claude Sonnet (cloud) - best at natural, varied writing
"""

import json
import logging
import os
import time
from typing import Dict, List, Optional

import anthropic

from .base import BaseAgent, AgentInput, AgentOutput

logger = logging.getLogger(__name__)


class HumanizerAgent(BaseAgent):
    """
    Humanizer agent that makes AI content undetectable.
    
    Uses Claude Sonnet for high-quality, natural rewriting.
    Key techniques:
    - Vary sentence structure and length
    - Add personal touches and opinions
    - Include imperfections (contractions, informal phrases)
    - Break predictable AI patterns
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-sonnet-4-20250514",
    ):
        super().__init__(
            name="humanizer",
            model=model,
            model_type="anthropic",
            api_key=api_key or os.getenv("ANTHROPIC_API_KEY"),
            temperature=0.8,  # High creativity for varied output
            max_tokens=8192,
        )
    
    def run(self, input: AgentInput) -> AgentOutput:
        """
        Humanize an article to pass AI detection.
        
        Input data:
            - article: str - The article to humanize
            - author_voice: str - Description of desired voice/style
            - intensity: str - low/medium/high (how much to rewrite)
        """
        start_time = time.time()
        errors = []
        
        article = input.data.get("article", "")
        author_voice = input.data.get("author_voice", "knowledgeable but approachable tech writer")
        intensity = input.data.get("intensity", "medium")
        
        if not article:
            return AgentOutput(
                data={},
                success=False,
                errors=["No article provided"],
            )
        
        logger.info(f"Humanizing article (intensity: {intensity})")
        
        # Step 1: Analyze current AI patterns
        ai_patterns = self._detect_ai_patterns(article)
        logger.info(f"Detected {len(ai_patterns)} AI patterns")
        
        # Step 2: Humanize section by section
        humanized_sections = []
        sections = self._split_into_sections(article)
        
        for section in sections:
            humanized = self._humanize_section(
                section=section,
                voice=author_voice,
                intensity=intensity,
                patterns_to_avoid=ai_patterns,
            )
            humanized_sections.append(humanized)
        
        # Step 3: Reassemble article
        humanized_article = "\n\n".join(humanized_sections)
        
        # Step 4: Final polish pass
        humanized_article = self._final_polish(humanized_article, author_voice)
        
        # Step 5: Verify humanization
        remaining_patterns = self._detect_ai_patterns(humanized_article)
        
        duration = time.time() - start_time
        
        output_data = {
            "humanized_article": humanized_article,
            "original_word_count": len(article.split()),
            "humanized_word_count": len(humanized_article.split()),
            "ai_patterns_before": len(ai_patterns),
            "ai_patterns_after": len(remaining_patterns),
            "patterns_removed": ai_patterns,
        }
        
        # Estimate tokens and cost
        input_tokens = len(article.split()) * 1.3
        output_tokens = len(humanized_article.split()) * 1.3
        cost = (input_tokens * 0.003 + output_tokens * 0.015) / 1000
        
        success = len(remaining_patterns) <= len(ai_patterns) // 2
        
        if not success:
            errors.append("Too many AI patterns remain")
        
        return AgentOutput(
            data=output_data,
            success=success,
            errors=errors,
            duration_seconds=duration,
            tokens_used=int(input_tokens + output_tokens),
            cost_usd=cost,
        )
    
    def validate_output(self, output: AgentOutput) -> bool:
        """Check if humanization meets quality gate."""
        data = output.data
        
        # Must reduce AI patterns by at least 50%
        before = data.get("ai_patterns_before", 0)
        after = data.get("ai_patterns_after", 0)
        
        if before > 0 and after > before // 2:
            return False
        
        return True
    
    def _detect_ai_patterns(self, text: str) -> List[str]:
        """Detect common AI writing patterns."""
        patterns = []
        
        # Common AI phrases
        ai_phrases = [
            "it's important to note",
            "it's worth noting",
            "in conclusion",
            "to summarize",
            "let's dive in",
            "without further ado",
            "in today's world",
            "in this article",
            "as we all know",
            "it goes without saying",
            "at the end of the day",
            "the bottom line is",
            "needless to say",
            "it's no secret that",
            "when it comes to",
            "in terms of",
            "on the other hand",
            "with that being said",
            "having said that",
            "that being said",
            "first and foremost",
            "last but not least",
            "all in all",
            "in a nutshell",
            "to put it simply",
            "simply put",
            "in essence",
            "in other words",
            "that is to say",
            "for instance",
            "for example",
            "such as",
            "including but not limited to",
        ]
        
        text_lower = text.lower()
        for phrase in ai_phrases:
            if phrase in text_lower:
                patterns.append(phrase)
        
        # Check for repetitive sentence starters
        sentences = text.split('. ')
        starters = {}
        for s in sentences:
            words = s.strip().split()[:2]
            if words:
                starter = ' '.join(words).lower()
                starters[starter] = starters.get(starter, 0) + 1
        
        for starter, count in starters.items():
            if count > 3:
                patterns.append(f"repetitive starter: '{starter}' ({count}x)")
        
        # Check sentence length uniformity
        lengths = [len(s.split()) for s in sentences if s.strip()]
        if lengths:
            avg = sum(lengths) / len(lengths)
            variance = sum((l - avg) ** 2 for l in lengths) / len(lengths)
            if variance < 20:  # Low variance = AI-like uniformity
                patterns.append("uniform sentence lengths")
        
        return patterns
    
    def _split_into_sections(self, article: str) -> List[str]:
        """Split article into manageable sections."""
        sections = []
        current_section = []
        
        for line in article.split('\n'):
            if line.startswith('## '):
                if current_section:
                    sections.append('\n'.join(current_section))
                current_section = [line]
            else:
                current_section.append(line)
        
        if current_section:
            sections.append('\n'.join(current_section))
        
        return sections
    
    def _humanize_section(
        self,
        section: str,
        voice: str,
        intensity: str,
        patterns_to_avoid: List[str],
    ) -> str:
        """Humanize a single section."""
        
        intensity_instructions = {
            "low": "Make subtle changes - fix obvious AI patterns while preserving most of the original text.",
            "medium": "Rewrite significantly - vary sentence structure, add personal touches, change word choices.",
            "high": "Complete rewrite - same information but entirely different expression. Make it sound like a human expert wrote it from scratch.",
        }
        
        prompt = f"""Rewrite this content to sound authentically human-written.

AUTHOR VOICE: {voice}
INTENSITY: {intensity}
{intensity_instructions.get(intensity, intensity_instructions["medium"])}

PATTERNS TO ELIMINATE:
{chr(10).join(f'- {p}' for p in patterns_to_avoid[:10])}

HUMANIZATION TECHNIQUES:
1. Vary sentence length dramatically (5-word punchy sentences mixed with longer 25-word explanations)
2. Use contractions naturally (it's, don't, can't, we're)
3. Start sentences differently - avoid repetitive patterns
4. Add brief personal observations or mild opinions
5. Use informal transitions occasionally (So, Now, Look, Here's the thing)
6. Include rhetorical questions sparingly
7. Break grammar rules occasionally for effect (sentence fragments, starting with "And" or "But")
8. Add specific, concrete details instead of generic statements
9. Use active voice predominantly
10. Include occasional self-corrections or clarifications ("well, actually...")

SECTION TO HUMANIZE:
{section}

IMPORTANT:
- Preserve all factual information and statistics
- Keep markdown formatting (headers, links, lists)
- Maintain the same approximate length
- Don't add [brackets] or (parenthetical asides) excessively

Return ONLY the humanized text, no explanations."""

        try:
            response = self._call_anthropic(prompt)
            return response.strip()
        except Exception as e:
            logger.error(f"Failed to humanize section: {e}")
            return section  # Return original on failure
    
    def _final_polish(self, article: str, voice: str) -> str:
        """Final pass to ensure consistency and flow."""
        
        prompt = f"""Review and polish this article for final publication.

AUTHOR VOICE: {voice}

Focus on:
1. Smooth transitions between sections
2. Consistent tone throughout
3. Natural flow and readability
4. Remove any remaining robotic phrases

ARTICLE:
{article}

Return the polished article. Make only necessary adjustments for flow and consistency."""

        try:
            response = self._call_anthropic(prompt)
            # Verify it's a complete article
            if len(response) > len(article) * 0.5 and "# " in response:
                return response.strip()
            return article
        except Exception as e:
            logger.error(f"Failed to polish: {e}")
            return article
