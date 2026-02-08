"""
Writer Agent - Creates the initial article draft.

Model: llama3.2:11b (local) or qwen2.5:14b
"""

import json
import logging
import time
from typing import Dict, List, Optional

from .base import BaseAgent, AgentInput, AgentOutput

logger = logging.getLogger(__name__)


class WriterAgent(BaseAgent):
    """
    Writer agent that creates article drafts from research.
    
    Uses local LLM for cost efficiency.
    """
    
    def __init__(
        self,
        ollama_url: str = "http://localhost:11434",
        model: str = "qwen2.5:14b",
    ):
        super().__init__(
            name="writer",
            model=model,
            model_type="ollama",
            ollama_url=ollama_url,
            temperature=0.7,  # Some creativity
            max_tokens=8192,  # Long-form content
        )
    
    def run(self, input: AgentInput) -> AgentOutput:
        """
        Generate article draft from research.
        
        Input data:
            - research: Dict - Output from research agent
            - tone: str - Article tone (informative, conversational, etc.)
            - target_word_count: int - Target length
        """
        start_time = time.time()
        errors = []
        
        research = input.data.get("research", {})
        tone = input.data.get("tone", "informative yet conversational")
        target_word_count = input.data.get("target_word_count", 2500)
        
        if not research:
            return AgentOutput(
                data={},
                success=False,
                errors=["No research data provided"],
            )
        
        topic = research.get("topic", "")
        outline = research.get("outline", {})
        sources = research.get("sources", [])
        
        logger.info(f"Writing article: {topic}")
        
        # Step 1: Write introduction
        intro = self._write_section(
            topic=topic,
            section_type="introduction",
            outline=outline,
            sources=sources,
            tone=tone,
        )
        
        # Step 2: Write each section
        sections_content = []
        for section in outline.get("sections", []):
            section_text = self._write_section(
                topic=topic,
                section_type="body",
                section=section,
                sources=sources,
                tone=tone,
            )
            sections_content.append({
                "h2": section.get("h2", ""),
                "content": section_text,
            })
        
        # Step 3: Write conclusion
        conclusion = self._write_section(
            topic=topic,
            section_type="conclusion",
            outline=outline,
            sources=sources,
            tone=tone,
        )
        
        # Step 4: Compile full article
        article = self._compile_article(
            title=outline.get("title", topic),
            intro=intro,
            sections=sections_content,
            conclusion=conclusion,
        )
        
        # Step 5: Count words
        word_count = len(article.split())
        
        if word_count < target_word_count * 0.8:
            errors.append(f"Article is short: {word_count} words (target: {target_word_count})")
        
        duration = time.time() - start_time
        
        output_data = {
            "title": outline.get("title", topic),
            "article_markdown": article,
            "word_count": word_count,
            "sections_count": len(sections_content),
        }
        
        success = word_count >= target_word_count * 0.8
        
        return AgentOutput(
            data=output_data,
            success=success,
            errors=errors,
            duration_seconds=duration,
        )
    
    def validate_output(self, output: AgentOutput) -> bool:
        """Check if article meets quality gate."""
        if not output.success:
            return False
        
        data = output.data
        word_count = data.get("word_count", 0)
        article = data.get("article_markdown", "")
        
        # Must have minimum length
        if word_count < 2000:
            return False
        
        # Must have H2 headers
        if article.count("## ") < 4:
            return False
        
        return True
    
    def _write_section(
        self,
        topic: str,
        section_type: str,
        outline: Dict = None,
        section: Dict = None,
        sources: List[Dict] = None,
        tone: str = "informative",
    ) -> str:
        """Write a single section of the article."""
        
        # Build source context
        source_context = ""
        if sources:
            relevant_sources = sources[:5]  # Top 5 sources
            source_bullets = []
            for s in relevant_sources:
                source_bullets.append(f"- {s.get('title', 'Unknown')}: {s.get('snippet', '')[:200]}")
                for stat in s.get('key_stats', [])[:2]:
                    source_bullets.append(f"  • Stat: {stat}")
            source_context = "\n".join(source_bullets)
        
        if section_type == "introduction":
            prompt = f"""Write an engaging introduction for an article titled "{outline.get('title', topic)}".

Topic: {topic}

Available source information:
{source_context}

Guidelines:
- Start with a hook (surprising stat, question, or bold statement)
- Explain why this topic matters now
- Preview what the reader will learn
- Target: 150-200 words
- Tone: {tone}

Write ONLY the introduction text, no headers."""

        elif section_type == "conclusion":
            prompt = f"""Write a strong conclusion for an article about "{topic}".

Article sections covered:
{json.dumps([s.get('h2', '') for s in outline.get('sections', [])], indent=2)}

Guidelines:
- Summarize key takeaways
- End with actionable advice or forward-looking thought
- Include a subtle call to action if appropriate
- Target: 150-200 words
- Tone: {tone}

Write ONLY the conclusion text, no headers."""

        else:  # body section
            h2 = section.get("h2", "")
            h3s = section.get("h3s", [])
            key_points = section.get("key_points", [])
            
            prompt = f"""Write a section for an article about "{topic}".

Section title (H2): {h2}
Subsections (H3): {json.dumps(h3s)}
Key points to cover: {json.dumps(key_points)}

Available source information:
{source_context}

Guidelines:
- Start with the H2 header: ## {h2}
- Include H3 subsections where appropriate
- Cite statistics and data where available
- Use examples to illustrate points
- Target: 300-400 words
- Tone: {tone}

Write the complete section in markdown format."""

        try:
            response = self._call_model(prompt)
            return response.strip()
        except Exception as e:
            logger.error(f"Failed to write section: {e}")
            return f"[Error writing section: {e}]"
    
    def _compile_article(
        self,
        title: str,
        intro: str,
        sections: List[Dict],
        conclusion: str,
    ) -> str:
        """Compile all sections into full article."""
        
        parts = [
            f"# {title}",
            "",
            intro,
            "",
        ]
        
        for section in sections:
            content = section.get("content", "")
            # Ensure section starts with H2 if not already
            if not content.strip().startswith("## "):
                content = f"## {section.get('h2', 'Section')}\n\n{content}"
            parts.append(content)
            parts.append("")
        
        parts.extend([
            "## Conclusion",
            "",
            conclusion,
        ])
        
        return "\n".join(parts)
