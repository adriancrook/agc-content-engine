"""
Sitemap Scraper and Article Indexer
Fetches and indexes articles from adriancrook.com for internal linking
"""

import logging
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

import requests

logger = logging.getLogger(__name__)


@dataclass
class IndexedArticle:
    """An indexed article from the site"""
    url: str
    title: str
    published_date: Optional[str] = None
    excerpt: Optional[str] = None
    categories: List[str] = None
    tags: List[str] = None

    def to_dict(self):
        return {
            "url": self.url,
            "title": self.title,
            "published_date": self.published_date,
            "excerpt": self.excerpt,
            "categories": self.categories or [],
            "tags": self.tags or [],
        }


class SitemapScraper:
    """Scrapes and indexes articles from adriancrook.com sitemap"""

    def __init__(self, sitemap_url: str = "https://adriancrook.com/sitemap.xml"):
        self.sitemap_url = sitemap_url
        self.articles = []

    def fetch_sitemap(self) -> List[str]:
        """Fetch sitemap and extract article URLs"""
        try:
            logger.info(f"Fetching sitemap from {self.sitemap_url}")
            headers = {
                'User-Agent': 'Mozilla/5.0 (compatible; AGC-ContentEngine/2.0; +https://adriancrook.com)'
            }
            response = requests.get(self.sitemap_url, headers=headers, timeout=30)
            response.raise_for_status()

            # Parse XML
            root = ET.fromstring(response.content)

            # Handle sitemap index (multiple sitemaps) or direct sitemap
            urls = []

            # Check if this is a sitemap index
            if root.tag.endswith('sitemapindex'):
                logger.info("Found sitemap index, fetching individual sitemaps")
                for sitemap in root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}sitemap'):
                    loc = sitemap.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
                    if loc is not None:
                        sub_urls = self._fetch_individual_sitemap(loc.text)
                        urls.extend(sub_urls)
            else:
                # Direct sitemap with URLs
                for url in root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}url'):
                    loc = url.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
                    if loc is not None:
                        urls.append(loc.text)

            # Filter for blog posts (exclude pages, categories, etc.)
            article_urls = [u for u in urls if self._is_article_url(u)]

            logger.info(f"Found {len(article_urls)} article URLs")
            return article_urls

        except Exception as e:
            logger.error(f"Failed to fetch sitemap: {e}")
            return []

    def _fetch_individual_sitemap(self, sitemap_url: str) -> List[str]:
        """Fetch an individual sitemap from a sitemap index"""
        try:
            response = requests.get(sitemap_url, timeout=30)
            response.raise_for_status()
            root = ET.fromstring(response.content)

            urls = []
            for url in root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}url'):
                loc = url.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
                if loc is not None:
                    urls.append(loc.text)

            return urls

        except Exception as e:
            logger.warning(f"Failed to fetch individual sitemap {sitemap_url}: {e}")
            return []

    def _is_article_url(self, url: str) -> bool:
        """Check if URL is an article (not a page, category, tag, etc.)"""
        # Exclude common non-article paths
        exclude_patterns = [
            '/category/',
            '/tag/',
            '/author/',
            '/page/',
            '/wp-',
            '/feed',
            '.xml',
            '/privacy',
            '/contact',
            '/about',
        ]

        url_lower = url.lower()

        for pattern in exclude_patterns:
            if pattern in url_lower:
                return False

        # Include if it has a date-like pattern or is a typical blog post
        # adriancrook.com pattern: https://adriancrook.com/some-title/
        if url.startswith('https://adriancrook.com/') and url.count('/') >= 4:
            return True

        return False

    def extract_title_from_url(self, url: str) -> str:
        """Extract title from URL slug"""
        # Remove domain and trailing slash
        path = url.replace('https://adriancrook.com/', '').rstrip('/')

        # Convert hyphens to spaces and title case
        title = path.replace('-', ' ').title()

        return title

    def build_article_index(self, max_articles: int = 200) -> List[IndexedArticle]:
        """Build index of articles from sitemap"""
        urls = self.fetch_sitemap()

        articles = []
        for url in urls[:max_articles]:  # Limit to recent articles
            # For now, we'll extract basic info from URL
            # In future, could scrape each page for full metadata
            title = self.extract_title_from_url(url)

            article = IndexedArticle(
                url=url,
                title=title,
            )
            articles.append(article)

        self.articles = articles
        logger.info(f"Indexed {len(articles)} articles")
        return articles

    def find_related_articles(self, topic: str, keywords: List[str] = None, max_results: int = 5) -> List[IndexedArticle]:
        """Find articles related to a topic using keyword matching"""
        if not self.articles:
            self.build_article_index()

        topic_lower = topic.lower()
        keywords_lower = [k.lower() for k in (keywords or [])]

        scored_articles = []
        for article in self.articles:
            score = 0
            title_lower = article.title.lower()

            # Exact topic match in title
            if topic_lower in title_lower:
                score += 10

            # Individual keyword matches
            topic_words = topic_lower.split()
            for word in topic_words:
                if len(word) > 3 and word in title_lower:  # Skip short words
                    score += 2

            # Additional keywords
            for keyword in keywords_lower:
                if keyword in title_lower:
                    score += 3

            if score > 0:
                scored_articles.append((score, article))

        # Sort by score descending
        scored_articles.sort(reverse=True, key=lambda x: x[0])

        # Return top matches
        return [article for score, article in scored_articles[:max_results]]


def save_article_index(articles: List[IndexedArticle], filepath: str):
    """Save article index to JSON file"""
    import json

    data = [article.to_dict() for article in articles]

    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

    logger.info(f"Saved {len(articles)} articles to {filepath}")


def load_article_index(filepath: str) -> List[IndexedArticle]:
    """Load article index from JSON file"""
    import json

    try:
        with open(filepath, 'r') as f:
            data = json.load(f)

        articles = [
            IndexedArticle(
                url=item['url'],
                title=item['title'],
                published_date=item.get('published_date'),
                excerpt=item.get('excerpt'),
                categories=item.get('categories', []),
                tags=item.get('tags', []),
            )
            for item in data
        ]

        logger.info(f"Loaded {len(articles)} articles from {filepath}")
        return articles

    except Exception as e:
        logger.error(f"Failed to load article index: {e}")
        return []


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    scraper = SitemapScraper()
    articles = scraper.build_article_index()

    print(f"\nIndexed {len(articles)} articles")
    print("\nFirst 10 articles:")
    for i, article in enumerate(articles[:10], 1):
        print(f"{i}. {article.title}")
        print(f"   {article.url}")

    # Test search
    print("\n\nSearching for 'monetization' related articles:")
    related = scraper.find_related_articles("monetization")
    for i, article in enumerate(related, 1):
        print(f"{i}. {article.title}")
        print(f"   {article.url}")

    # Save index
    save_article_index(articles, "article_index.json")
