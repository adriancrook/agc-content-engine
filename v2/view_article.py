#!/usr/bin/env python3
"""
Simple article viewer - Shows enriched article content
Usage: python view_article.py <article_id>
"""

import sys
import requests
import json

def view_article(article_id: str):
    """Fetch and display article with enrichment data"""

    response = requests.get(f"http://localhost:8000/articles/{article_id}")

    if response.status_code != 200:
        print(f"❌ Article not found: {article_id}")
        return

    article = response.json()

    print("=" * 70)
    print(f"📰 {article['title']}")
    print("=" * 70)
    print(f"State: {article['state']}")
    print(f"Created: {article.get('created_at', 'N/A')}")
    print()

    # Research data
    if article.get('research'):
        research = article['research']
        sources = research.get('sources', [])
        print(f"🔍 Research: {len(sources)} sources")
        print()

    # Draft
    if article.get('draft'):
        word_count = len(article['draft'].split())
        print(f"📝 Draft: {word_count} words")
        print()

    # Enrichment data
    enrichment = article.get('enrichment')
    if enrichment:
        print("✨ ENRICHMENT DATA:")
        print("-" * 70)

        citations = enrichment.get('citations', [])
        metrics = enrichment.get('metrics', [])
        testimonials = enrichment.get('testimonials', [])
        media = enrichment.get('media', [])

        print(f"\n📚 Citations: {len(citations)}")
        for i, cite in enumerate(citations[:3], 1):
            print(f"  {i}. {cite.get('claim', 'N/A')[:60]}...")
            print(f"     Source: {cite.get('source_name', 'N/A')}")
            print(f"     URL: {cite.get('url', 'N/A')}")
            print()

        print(f"\n📊 Metrics: {len(metrics)}")
        for i, metric in enumerate(metrics[:3], 1):
            print(f"  {i}. {metric.get('game_name', 'N/A')}: {metric.get('metric_type', 'N/A')}")
            print(f"     Value: {metric.get('value', 'N/A')}")
            print()

        print(f"\n💬 Testimonials: {len(testimonials)}")
        for i, test in enumerate(testimonials[:3], 1):
            print(f"  {i}. {test.get('text', 'N/A')[:80]}...")
            print(f"     - {test.get('author', 'N/A')}")
            print()

        print(f"\n🎬 Media Links: {len(media)}")
        print()

        # Integration guide
        guide = enrichment.get('integration_guide')
        if guide:
            print("📖 INTEGRATION GUIDE:")
            print("-" * 70)
            print(guide)
            print()

    # Revised draft
    if article.get('revised_draft'):
        word_count = len(article['revised_draft'].split())
        print(f"✏️  Revised Draft: {word_count} words")
        print()

    # Final content
    if article.get('final_content'):
        word_count = len(article['final_content'].split())
        print(f"✅ Final Content: {word_count} words")
        print()

    print("=" * 70)


def list_articles():
    """List all articles"""

    response = requests.get("http://localhost:8000/articles")
    articles = response.json()

    print("\n📋 All Articles:")
    print("=" * 70)

    for article in articles:
        state_icon = {
            "ready": "✅",
            "failed": "❌",
            "enriching": "✨",
            "writing": "📝",
            "researching": "🔍",
        }.get(article['state'], "⏳")

        print(f"{state_icon} [{article['state'].upper():12}] {article['title'][:50]}")
        print(f"   ID: {article['id']}")
        print()

    print("=" * 70)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python view_article.py <article_id>  - View specific article")
        print("  python view_article.py list          - List all articles")
        sys.exit(1)

    if sys.argv[1] == "list":
        list_articles()
    else:
        view_article(sys.argv[1])
