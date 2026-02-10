"""
Curated Article Database for Internal Linking
Manually curated list of adriancrook.com articles for internal linking
Used as fallback if sitemap scraping fails
"""

from typing import List, Dict

# Curated list of popular adriancrook.com articles
# Format: {"title": "...", "url": "...", "topics": ["topic1", "topic2"]}
CURATED_ARTICLES = [
    # Monetization
    {
        "title": "Mobile Game Monetization Strategies That Actually Work",
        "url": "https://adriancrook.com/mobile-game-monetization-strategies/",
        "topics": ["monetization", "iap", "ads", "revenue", "business model"]
    },
    {
        "title": "How To Reduce Drop-Off During Onboarding",
        "url": "https://adriancrook.com/reduce-drop-off-onboarding/",
        "topics": ["onboarding", "ftue", "retention", "ux", "user experience"]
    },
    {
        "title": "F2P Game Design: Balancing Fun and Revenue",
        "url": "https://adriancrook.com/f2p-game-design-balancing/",
        "topics": ["f2p", "free-to-play", "game design", "monetization", "balance"]
    },
    {
        "title": "In-App Purchase Best Practices for Mobile Games",
        "url": "https://adriancrook.com/iap-best-practices/",
        "topics": ["iap", "in-app purchase", "monetization", "pricing"]
    },
    {
        "title": "Rewarded Video Ads: Implementation Guide",
        "url": "https://adriancrook.com/rewarded-video-ads-guide/",
        "topics": ["ads", "rewarded video", "monetization", "user experience"]
    },

    # Retention & Engagement
    {
        "title": "Player Retention Strategies for Mobile Games",
        "url": "https://adriancrook.com/player-retention-strategies/",
        "topics": ["retention", "engagement", "churn", "ltv", "loyalty"]
    },
    {
        "title": "Building Habit-Forming Mobile Games",
        "url": "https://adriancrook.com/habit-forming-games/",
        "topics": ["retention", "habits", "engagement", "psychology", "game design"]
    },
    {
        "title": "Push Notification Best Practices",
        "url": "https://adriancrook.com/push-notification-best-practices/",
        "topics": ["push notifications", "retention", "engagement", "messaging"]
    },
    {
        "title": "Social Features That Drive Retention",
        "url": "https://adriancrook.com/social-features-retention/",
        "topics": ["social", "retention", "engagement", "multiplayer", "community"]
    },
    {
        "title": "Daily Login Rewards and Retention",
        "url": "https://adriancrook.com/daily-login-rewards/",
        "topics": ["retention", "rewards", "engagement", "monetization"]
    },

    # User Acquisition
    {
        "title": "Mobile Game User Acquisition Strategies",
        "url": "https://adriancrook.com/user-acquisition-strategies/",
        "topics": ["ua", "user acquisition", "marketing", "growth", "cpi"]
    },
    {
        "title": "App Store Optimization (ASO) Guide",
        "url": "https://adriancrook.com/aso-guide/",
        "topics": ["aso", "app store", "optimization", "marketing", "discovery"]
    },
    {
        "title": "Creative Testing for Mobile Game Ads",
        "url": "https://adriancrook.com/creative-testing-mobile-ads/",
        "topics": ["ua", "ads", "creative", "testing", "marketing"]
    },

    # Analytics & Metrics
    {
        "title": "Mobile Game KPIs You Should Track",
        "url": "https://adriancrook.com/mobile-game-kpis/",
        "topics": ["analytics", "kpis", "metrics", "data", "performance"]
    },
    {
        "title": "Understanding ARPU and ARPPU",
        "url": "https://adriancrook.com/arpu-arppu-explained/",
        "topics": ["arpu", "arppu", "monetization", "metrics", "revenue"]
    },
    {
        "title": "Cohort Analysis for Mobile Games",
        "url": "https://adriancrook.com/cohort-analysis-mobile-games/",
        "topics": ["analytics", "cohorts", "retention", "ltv", "data"]
    },

    # Game Design
    {
        "title": "Core Loop Design for Mobile Games",
        "url": "https://adriancrook.com/core-loop-design/",
        "topics": ["game design", "core loop", "gameplay", "mechanics"]
    },
    {
        "title": "Progression Systems in Mobile Games",
        "url": "https://adriancrook.com/progression-systems/",
        "topics": ["progression", "game design", "retention", "engagement"]
    },
    {
        "title": "Economy Design for F2P Games",
        "url": "https://adriancrook.com/economy-design-f2p/",
        "topics": ["economy", "game design", "monetization", "balance"]
    },
    {
        "title": "Gacha Mechanics and Psychology",
        "url": "https://adriancrook.com/gacha-mechanics-psychology/",
        "topics": ["gacha", "monetization", "psychology", "game design"]
    },

    # Live Ops
    {
        "title": "Live Operations Best Practices",
        "url": "https://adriancrook.com/live-ops-best-practices/",
        "topics": ["live ops", "events", "engagement", "retention", "content"]
    },
    {
        "title": "Seasonal Events and Limited-Time Content",
        "url": "https://adriancrook.com/seasonal-events-content/",
        "topics": ["events", "live ops", "engagement", "monetization"]
    },
    {
        "title": "Battle Pass Systems Explained",
        "url": "https://adriancrook.com/battle-pass-systems/",
        "topics": ["battle pass", "monetization", "engagement", "retention"]
    },

    # Platform & Technology
    {
        "title": "Cross-Platform Play Implementation",
        "url": "https://adriancrook.com/cross-platform-play/",
        "topics": ["cross-platform", "multiplayer", "technical", "ux"]
    },
    {
        "title": "Cloud Gaming and Mobile",
        "url": "https://adriancrook.com/cloud-gaming-mobile/",
        "topics": ["cloud gaming", "technology", "streaming", "future"]
    },

    # Market & Trends
    {
        "title": "Mobile Gaming Market Trends",
        "url": "https://adriancrook.com/mobile-gaming-trends/",
        "topics": ["trends", "market", "industry", "future", "analysis"]
    },
    {
        "title": "Hypercasual Games: Market Analysis",
        "url": "https://adriancrook.com/hypercasual-market-analysis/",
        "topics": ["hypercasual", "market", "trends", "monetization"]
    },
    {
        "title": "Web3 Gaming and NFTs",
        "url": "https://adriancrook.com/web3-gaming-nfts/",
        "topics": ["web3", "nft", "blockchain", "trends", "monetization"]
    },
]


def get_curated_articles() -> List[Dict]:
    """Get all curated articles"""
    return CURATED_ARTICLES


def find_articles_by_topic(topic: str, max_results: int = 5) -> List[Dict]:
    """Find curated articles matching a topic"""
    topic_lower = topic.lower()
    topic_words = topic_lower.split()

    scored_articles = []

    for article in CURATED_ARTICLES:
        score = 0
        title_lower = article['title'].lower()
        topics_lower = [t.lower() for t in article['topics']]

        # Check if topic words appear in article topics
        for word in topic_words:
            if len(word) <= 3:  # Skip short words
                continue

            # Exact match in topics list
            if word in topics_lower:
                score += 10

            # Partial match in topics
            for topic_tag in topics_lower:
                if word in topic_tag:
                    score += 5

            # Match in title
            if word in title_lower:
                score += 3

        if score > 0:
            scored_articles.append((score, article))

    # Sort by score descending
    scored_articles.sort(reverse=True, key=lambda x: x[0])

    return [article for score, article in scored_articles[:max_results]]


# Example usage
if __name__ == "__main__":
    print(f"Total curated articles: {len(CURATED_ARTICLES)}\n")

    # Test search
    test_topics = ["monetization", "retention", "onboarding", "analytics"]

    for topic in test_topics:
        print(f"\nSearching for '{topic}':")
        results = find_articles_by_topic(topic, max_results=3)
        for i, article in enumerate(results, 1):
            print(f"  {i}. {article['title']}")
            print(f"     {article['url']}")
