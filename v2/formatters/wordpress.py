"""
WordPress Formatter
Generates WordPress-ready markdown with metadata
"""

import re
import logging
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class WordPressFormatter:
    """
    Formats article content for WordPress publishing
    Generates SEO metadata, categories, tags, and frontmatter
    """

    # Mobile gaming taxonomy (categories)
    CATEGORIES = [
        "Monetization Strategy",
        "Player Analytics",
        "Game Design",
        "User Acquisition",
        "Retention Systems",
        "Live Operations",
        "Market Research",
        "Product Management",
        "Player Psychology",
        "Game Economy Design",
    ]

    # Common mobile gaming keywords for tag generation
    TAG_KEYWORDS = [
        "freemium", "f2p", "free-to-play", "mobile gaming", "mobile games",
        "iap", "in-app purchase", "monetization", "revenue", "arpu", "ltv",
        "retention", "engagement", "churn", "onboarding", "ftue",
        "user acquisition", "ua", "marketing", "aso", "app store",
        "analytics", "kpis", "metrics", "cohort analysis", "data",
        "game design", "core loop", "progression", "economy", "balance",
        "live ops", "events", "battle pass", "seasons",
        "ads", "advertising", "rewarded video", "interstitial",
        "gacha", "loot boxes", "mystery boxes",
        "social", "multiplayer", "pvp", "guilds", "clans",
        "rpg", "strategy", "puzzle", "casual", "midcore", "hardcore",
        "ios", "android", "cross-platform",
        "trends", "market", "industry", "web3", "nft", "blockchain",
    ]

    def __init__(self, config: Dict = None):
        self.config = config or {}

    def format(self, article_data: Dict) -> Dict:
        """
        Format article for WordPress

        Args:
            article_data: Dict with keys: title, final_content, research, seo, media

        Returns:
            Dict with:
                - wordpress_content: Full markdown with frontmatter
                - metadata: SEO metadata dict
                - export_ready: bool
        """
        title = article_data.get("title", "Untitled Article")
        content = article_data.get("final_content", "")
        research = article_data.get("research", {})
        seo = article_data.get("seo", {})
        media = article_data.get("media", {})

        logger.info(f"Formatting article for WordPress: {title}")

        # Generate metadata
        metadata = self._generate_metadata(title, content, research, seo)

        # Generate frontmatter
        frontmatter = self._generate_frontmatter(metadata, media)

        # Combine frontmatter + content
        wordpress_content = frontmatter + "\n\n" + content

        # Validation
        export_ready = self._validate_for_export(metadata, content, media)

        return {
            "wordpress_content": wordpress_content,
            "metadata": metadata,
            "export_ready": export_ready,
            "validation_issues": self._get_validation_issues(metadata, content, media)
        }

    def _generate_metadata(self, title: str, content: str, research: Dict, seo: Dict) -> Dict:
        """Generate SEO metadata"""

        # SEO Title (50-60 characters)
        seo_title = self._generate_seo_title(title, seo)

        # Meta Description (150-160 characters)
        meta_description = self._generate_meta_description(title, content, seo)

        # Keywords
        keywords = self._extract_keywords(title, content)

        # Categories (1-2)
        categories = self._assign_categories(title, content)

        # Tags (8-12)
        tags = self._generate_tags(title, content, keywords)

        # Featured image alt text
        featured_image_alt = self._generate_image_alt_text(title)

        return {
            "seo_title": seo_title,
            "meta_description": meta_description,
            "keywords": keywords,
            "categories": categories,
            "tags": tags,
            "featured_image_alt": featured_image_alt,
            "author": "Adrian Crook",
            "date": datetime.utcnow().strftime("%Y-%m-%d"),
        }

    def _generate_seo_title(self, title: str, seo: Dict) -> str:
        """Generate SEO-optimized title (50-60 chars)"""

        # Use existing SEO title if available
        if seo.get("meta_title"):
            return seo["meta_title"][:60]

        # Shorten if too long
        if len(title) <= 60:
            return title

        # Truncate intelligently at word boundary
        truncated = title[:57]
        last_space = truncated.rfind(" ")
        if last_space > 40:
            return truncated[:last_space] + "..."

        return truncated + "..."

    def _generate_meta_description(self, title: str, content: str, seo: Dict) -> str:
        """Generate meta description (150-160 chars)"""

        # Use existing SEO description if available
        if seo.get("meta_description"):
            return seo["meta_description"][:160]

        # Extract first paragraph (after title)
        lines = content.split("\n")
        first_para = ""
        for line in lines:
            line = line.strip()
            if line and not line.startswith("#") and len(line) > 50:
                first_para = line
                break

        if not first_para:
            return f"Expert insights on {title.lower()} for mobile game developers."[:160]

        # Clean markdown links and formatting
        first_para = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', first_para)  # Remove links
        first_para = re.sub(r'\*\*([^\*]+)\*\*', r'\1', first_para)  # Remove bold
        first_para = re.sub(r'\[\[(\d+)\]\]\([^\)]+\)', '', first_para)  # Remove citations

        # Truncate to 157 chars (leave room for "...")
        if len(first_para) <= 160:
            return first_para

        truncated = first_para[:157]
        last_space = truncated.rfind(" ")
        if last_space > 120:
            return truncated[:last_space] + "..."

        return truncated + "..."

    def _extract_keywords(self, title: str, content: str) -> List[str]:
        """Extract 5-10 keywords from title and content"""

        text = (title + " " + content[:2000]).lower()

        # Find matching keywords from our TAG_KEYWORDS list
        found_keywords = []
        for keyword in self.TAG_KEYWORDS:
            if keyword in text and keyword not in found_keywords:
                found_keywords.append(keyword)
                if len(found_keywords) >= 10:
                    break

        # Add words from title
        title_words = [w.lower() for w in re.findall(r'\b[a-z]{4,}\b', title.lower())]
        for word in title_words:
            if word not in found_keywords and word not in ['that', 'this', 'with', 'from', 'your', 'for', 'the']:
                found_keywords.append(word)
                if len(found_keywords) >= 10:
                    break

        return found_keywords[:10]

    def _assign_categories(self, title: str, content: str) -> List[str]:
        """Assign 1-2 categories based on content"""

        text = (title + " " + content[:3000]).lower()

        category_keywords = {
            "Monetization Strategy": ["monetization", "revenue", "iap", "ads", "arpu", "ltv", "pricing"],
            "Player Analytics": ["analytics", "metrics", "kpis", "data", "cohort", "tracking"],
            "Game Design": ["game design", "gameplay", "core loop", "mechanics", "ux"],
            "User Acquisition": ["user acquisition", "ua", "marketing", "aso", "install"],
            "Retention Systems": ["retention", "engagement", "churn", "loyalty", "habit"],
            "Live Operations": ["live ops", "events", "seasons", "battle pass", "updates"],
            "Market Research": ["market", "trends", "industry", "research", "competition"],
            "Product Management": ["product", "roadmap", "features", "prioritization"],
            "Player Psychology": ["psychology", "behavior", "motivation", "spending"],
            "Game Economy Design": ["economy", "balance", "progression", "currency"],
        }

        scores = {}
        for category, keywords in category_keywords.items():
            score = sum(1 for kw in keywords if kw in text)
            if score > 0:
                scores[category] = score

        # Sort by score and return top 1-2
        sorted_categories = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [cat for cat, score in sorted_categories[:2]]

    def _generate_tags(self, title: str, content: str, keywords: List[str]) -> List[str]:
        """Generate 8-12 tags"""

        tags = []

        # Start with keywords
        tags.extend(keywords[:8])

        # Add specific game-related terms found in content
        text = content[:3000].lower()

        # Add mobile gaming if not present
        if "mobile gaming" not in tags and "mobile games" not in tags:
            tags.append("mobile gaming")

        # Add specific genres/types if mentioned
        game_types = ["rpg", "strategy", "puzzle", "casual", "midcore", "hardcore", "mmo"]
        for game_type in game_types:
            if game_type in text and game_type not in tags:
                tags.append(game_type)
                if len(tags) >= 12:
                    break

        return tags[:12]

    def _generate_image_alt_text(self, title: str) -> str:
        """Generate alt text for featured image"""
        return f"Illustration for article: {title}"

    def _generate_frontmatter(self, metadata: Dict, media: Dict) -> str:
        """Generate YAML frontmatter for WordPress"""

        frontmatter_lines = ["---"]

        # Title
        frontmatter_lines.append(f'title: "{metadata["seo_title"]}"')

        # Meta description
        frontmatter_lines.append(f'description: "{metadata["meta_description"]}"')

        # Keywords (YAML array)
        keywords_yaml = ", ".join(f'"{kw}"' for kw in metadata["keywords"])
        frontmatter_lines.append(f"keywords: [{keywords_yaml}]")

        # Categories (YAML array)
        categories_yaml = ", ".join(f'"{cat}"' for cat in metadata["categories"])
        frontmatter_lines.append(f"categories: [{categories_yaml}]")

        # Tags (YAML array)
        tags_yaml = ", ".join(f'"{tag}"' for tag in metadata["tags"])
        frontmatter_lines.append(f"tags: [{tags_yaml}]")

        # Author & Date
        frontmatter_lines.append(f'author: "{metadata["author"]}"')
        frontmatter_lines.append(f'date: "{metadata["date"]}"')

        # Featured image
        if media.get("featured_image"):
            frontmatter_lines.append(f'featured_image: "{media["featured_image"]}"')
            frontmatter_lines.append(f'featured_image_alt: "{metadata["featured_image_alt"]}"')

        frontmatter_lines.append("---")

        return "\n".join(frontmatter_lines)

    def _validate_for_export(self, metadata: Dict, content: str, media: Dict) -> bool:
        """Check if article is ready for WordPress export"""

        issues = self._get_validation_issues(metadata, content, media)
        return len(issues) == 0

    def _get_validation_issues(self, metadata: Dict, content: str, media: Dict) -> List[str]:
        """Get list of validation issues"""

        issues = []

        # Check word count
        word_count = len(content.split())
        if word_count < 2000:
            issues.append(f"Word count too low: {word_count} (need 2000+)")

        # Check metadata
        if len(metadata.get("seo_title", "")) > 60:
            issues.append("SEO title too long (max 60 chars)")

        if len(metadata.get("meta_description", "")) > 160:
            issues.append("Meta description too long (max 160 chars)")

        if len(metadata.get("categories", [])) == 0:
            issues.append("No categories assigned")

        if len(metadata.get("tags", [])) < 5:
            issues.append(f"Too few tags: {len(metadata.get('tags', []))} (need 5+)")

        # Check citations
        citation_count = len(re.findall(r'\[\[\d+\]\]\([^\)]+\)', content))
        if citation_count < 10:
            issues.append(f"Too few citations: {citation_count} (need 10+)")

        # Check for Sources section
        if "## Sources" not in content and "## References" not in content:
            issues.append("No Sources/References section found")

        # Check for featured image
        if not media.get("featured_image"):
            issues.append("No featured image")

        return issues


# Export
__all__ = ['WordPressFormatter']
