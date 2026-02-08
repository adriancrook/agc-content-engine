"""
SEO Agent - Optimizes article for search engines.

Model: qwen2.5:14b (local)
"""

import json
import logging
import re
import time
from typing import Dict, List, Optional

from .base import BaseAgent, AgentInput, AgentOutput

logger = logging.getLogger(__name__)


class SEOAgent(BaseAgent):
    """
    SEO agent that optimizes articles for search engines.
    
    Adds meta descriptions, optimizes headers, internal links, etc.
    """
    
    def __init__(
        self,
        ollama_url: str = "http://localhost:11434",
        model: str = "qwen2.5:14b",
    ):
        super().__init__(
            name="seo",
            model=model,
            model_type="ollama",
            ollama_url=ollama_url,
            temperature=0.3,  # Low creativity for SEO
            max_tokens=4096,
        )
    
    def run(self, input: AgentInput) -> AgentOutput:
        """
        Optimize article for SEO.
        
        Input data:
            - article: str - The article markdown
            - primary_keyword: str - Main keyword
            - secondary_keywords: List[str] - Additional keywords
            - existing_articles: List[Dict] - Other blog articles for internal linking
        """
        start_time = time.time()
        errors = []
        
        article = input.data.get("article", "")
        primary_keyword = input.data.get("primary_keyword", "")
        secondary_keywords = input.data.get("secondary_keywords", [])
        existing_articles = input.data.get("existing_articles", [])
        
        if not article:
            return AgentOutput(
                data={},
                success=False,
                errors=["No article provided"],
            )
        
        logger.info(f"Optimizing for: {primary_keyword}")
        
        # Step 1: Analyze current SEO state
        current_score = self._analyze_seo(article, primary_keyword)
        logger.info(f"Current SEO score: {current_score}")
        
        # Step 2: Generate meta description
        meta_description = self._generate_meta_description(article, primary_keyword)
        
        # Step 3: Optimize title for SEO
        optimized_title = self._optimize_title(article, primary_keyword)
        
        # Step 4: Add keyword variations
        optimized_article = self._optimize_keyword_density(
            article, primary_keyword, secondary_keywords
        )
        
        # Step 5: Add internal links
        if existing_articles:
            optimized_article = self._add_internal_links(
                optimized_article, existing_articles
            )
        
        # Step 6: Generate schema markup
        schema = self._generate_schema(optimized_article, meta_description)
        
        # Step 7: Final SEO analysis
        final_score = self._analyze_seo(optimized_article, primary_keyword)
        
        # Step 8: Generate alt text suggestions for images
        alt_texts = self._suggest_alt_texts(optimized_article, primary_keyword)
        
        duration = time.time() - start_time
        
        output_data = {
            "optimized_article": optimized_article,
            "meta_description": meta_description,
            "optimized_title": optimized_title,
            "schema_markup": schema,
            "alt_text_suggestions": alt_texts,
            "seo_score_before": current_score,
            "seo_score_after": final_score,
            "primary_keyword": primary_keyword,
            "keyword_density": self._calculate_keyword_density(optimized_article, primary_keyword),
        }
        
        success = final_score >= 70
        
        if final_score < 70:
            errors.append(f"SEO score {final_score} below 70 threshold")
        
        return AgentOutput(
            data=output_data,
            success=success,
            errors=errors,
            duration_seconds=duration,
        )
    
    def validate_output(self, output: AgentOutput) -> bool:
        """Check if SEO optimization meets quality gate."""
        data = output.data
        
        # Need 70+ SEO score
        if data.get("seo_score_after", 0) < 70:
            return False
        
        # Need meta description
        if not data.get("meta_description"):
            return False
        
        return True
    
    def _analyze_seo(self, article: str, keyword: str) -> int:
        """Calculate SEO score (0-100)."""
        score = 0
        
        # Title includes keyword (+20)
        title_match = re.search(r'^# (.+)$', article, re.MULTILINE)
        if title_match and keyword.lower() in title_match.group(1).lower():
            score += 20
        
        # First paragraph includes keyword (+15)
        paragraphs = article.split('\n\n')
        for p in paragraphs[:3]:
            if not p.startswith('#') and keyword.lower() in p.lower():
                score += 15
                break
        
        # Keyword density 1-3% (+15)
        density = self._calculate_keyword_density(article, keyword)
        if 0.01 <= density <= 0.03:
            score += 15
        elif 0.005 <= density <= 0.05:
            score += 10
        
        # H2 headers include keyword variants (+15)
        h2s = re.findall(r'^## (.+)$', article, re.MULTILINE)
        keyword_h2s = sum(1 for h in h2s if keyword.lower() in h.lower())
        if keyword_h2s >= 1:
            score += 15
        
        # Article length (+15)
        word_count = len(article.split())
        if word_count >= 2500:
            score += 15
        elif word_count >= 1500:
            score += 10
        
        # Has internal/external links (+10)
        links = re.findall(r'\[.+?\]\(.+?\)', article)
        if len(links) >= 3:
            score += 10
        elif len(links) >= 1:
            score += 5
        
        # Has bullet/numbered lists (+10)
        if re.search(r'^[\-\*\d]\s', article, re.MULTILINE):
            score += 10
        
        return min(score, 100)
    
    def _calculate_keyword_density(self, article: str, keyword: str) -> float:
        """Calculate keyword density percentage."""
        words = article.lower().split()
        keyword_words = keyword.lower().split()
        
        if not words:
            return 0.0
        
        keyword_count = article.lower().count(keyword.lower())
        return keyword_count / len(words)
    
    def _generate_meta_description(self, article: str, keyword: str) -> str:
        """Generate SEO meta description."""
        prompt = f"""Generate an SEO meta description for this article.

Primary keyword: {keyword}

Article excerpt:
{article[:2000]}

Requirements:
- 150-160 characters
- Include primary keyword naturally
- Compelling call to action
- Summarize main value proposition

Return ONLY the meta description text, no quotes or labels."""

        try:
            response = self._call_model(prompt)
            meta = response.strip().strip('"').strip("'")
            # Truncate if too long
            if len(meta) > 160:
                meta = meta[:157] + "..."
            return meta
        except Exception as e:
            logger.error(f"Failed to generate meta description: {e}")
            return ""
    
    def _optimize_title(self, article: str, keyword: str) -> str:
        """Optimize article title for SEO."""
        # Extract current title
        title_match = re.search(r'^# (.+)$', article, re.MULTILINE)
        current_title = title_match.group(1) if title_match else ""
        
        if keyword.lower() in current_title.lower():
            return current_title  # Already optimized
        
        prompt = f"""Optimize this article title for SEO.

Current title: {current_title}
Primary keyword: {keyword}

Requirements:
- 50-60 characters ideal
- Include keyword naturally (front-load if possible)
- Compelling and click-worthy
- Keep the core meaning

Return ONLY the optimized title, no quotes."""

        try:
            response = self._call_model(prompt)
            return response.strip().strip('"').strip('#').strip()
        except Exception as e:
            logger.error(f"Failed to optimize title: {e}")
            return current_title
    
    def _optimize_keyword_density(
        self,
        article: str,
        primary: str,
        secondary: List[str],
    ) -> str:
        """Adjust keyword density in article."""
        current_density = self._calculate_keyword_density(article, primary)
        
        # If density is good, don't change
        if 0.01 <= current_density <= 0.025:
            return article
        
        prompt = f"""Optimize keyword density in this article.

Primary keyword: {primary}
Secondary keywords: {', '.join(secondary[:5])}

Current keyword density: {current_density:.1%}
Target density: 1.5-2%

Article:
{article[:5000]}

Instructions:
- Add keyword variations naturally where appropriate
- Don't over-optimize (avoid keyword stuffing)
- Maintain readability and flow
- Use synonyms and related terms

Return the COMPLETE optimized article in markdown."""

        try:
            response = self._call_model(prompt)
            # Verify it's actually an article, not just instructions
            if len(response) > 1000 and "# " in response:
                return response.strip()
            return article
        except Exception as e:
            logger.error(f"Failed to optimize keyword density: {e}")
            return article
    
    def _add_internal_links(
        self,
        article: str,
        existing_articles: List[Dict],
    ) -> str:
        """Add internal links to related articles."""
        if not existing_articles:
            return article
        
        # Format existing articles for prompt
        articles_info = []
        for a in existing_articles[:20]:
            articles_info.append({
                "title": a.get("title", ""),
                "url": a.get("url", ""),
                "topic": a.get("topic", ""),
            })
        
        prompt = f"""Add internal links to this article.

Available articles to link to:
{json.dumps(articles_info, indent=2)}

Article:
{article[:5000]}

Instructions:
- Add 2-4 relevant internal links
- Use natural anchor text (not "click here")
- Place links where contextually appropriate
- Format: [anchor text](url)

Return the article with internal links added."""

        try:
            response = self._call_model(prompt)
            if len(response) > 1000 and "# " in response:
                return response.strip()
            return article
        except Exception as e:
            logger.error(f"Failed to add internal links: {e}")
            return article
    
    def _generate_schema(self, article: str, meta_description: str) -> Dict:
        """Generate JSON-LD schema markup."""
        # Extract title
        title_match = re.search(r'^# (.+)$', article, re.MULTILINE)
        title = title_match.group(1) if title_match else "Article"
        
        # Count words
        word_count = len(article.split())
        
        # Basic Article schema
        schema = {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": title,
            "description": meta_description,
            "wordCount": word_count,
            "author": {
                "@type": "Person",
                "name": "Adrian Crook"
            },
            "publisher": {
                "@type": "Organization",
                "name": "Adrian Crook & Associates",
                "url": "https://adriancrook.com"
            }
        }
        
        return schema
    
    def _suggest_alt_texts(self, article: str, keyword: str) -> List[Dict]:
        """Suggest alt texts for images."""
        # Find image placeholders or references
        images = re.findall(r'!\[([^\]]*)\]\(([^\)]+)\)', article)
        
        suggestions = []
        for alt, src in images:
            if not alt or alt == "image":
                suggestions.append({
                    "src": src,
                    "current_alt": alt,
                    "suggested_alt": f"{keyword} - descriptive image",
                })
        
        return suggestions
