"""
Trusted Research Sources Database
Comprehensive database of competitor blogs, industry reports, and authoritative sources
for enhanced research quality
"""

from typing import Dict, List
from dataclasses import dataclass


@dataclass
class TrustedSource:
    """A trusted research source"""
    name: str
    domain: str
    base_url: str
    source_type: str  # blog, report, conference, news, data, academic
    credibility: float  # 0.0-1.0
    topics: List[str]
    update_frequency: str  # daily, weekly, monthly, quarterly, annual
    notes: str = ""


# ============================================================================
# TIER 1: COMPETITOR BLOGS & ANALYSIS (HIGH PRIORITY)
# ============================================================================

COMPETITOR_BLOGS = [
    TrustedSource(
        name="Deconstructor of Fun",
        domain="deconstructoroffun.com",
        base_url="https://www.deconstructoroffun.com",
        source_type="blog",
        credibility=1.0,
        topics=["game design", "monetization", "f2p", "analysis", "market trends"],
        update_frequency="weekly",
        notes="Deep dives into F2P game design and monetization. Must-read for mobile gaming."
    ),
    TrustedSource(
        name="Naavik",
        domain="naavik.co",
        base_url="https://naavik.co",
        source_type="blog",
        credibility=1.0,
        topics=["gaming industry", "market analysis", "investment", "trends", "web3"],
        update_frequency="weekly",
        notes="Premium gaming industry analysis and insights."
    ),
    TrustedSource(
        name="Mobile Dev Memo",
        domain="mobiledevmemo.com",
        base_url="https://mobiledevmemo.com",
        source_type="blog",
        credibility=1.0,
        topics=["mobile marketing", "ua", "attribution", "privacy", "adtech"],
        update_frequency="daily",
        notes="Eric Seufert's blog. Authority on mobile marketing and privacy."
    ),
    TrustedSource(
        name="GameRefinery by Vungle",
        domain="gamerefinery.com",
        base_url="https://www.gamerefinery.com",
        source_type="blog",
        credibility=0.95,
        topics=["game features", "market trends", "monetization", "genre analysis"],
        update_frequency="monthly",
        notes="Data-driven game feature analysis and market reports."
    ),
    TrustedSource(
        name="PocketGamer.biz",
        domain="pocketgamer.biz",
        base_url="https://www.pocketgamer.biz",
        source_type="news",
        credibility=0.9,
        topics=["mobile gaming", "news", "market data", "interviews", "funding"],
        update_frequency="daily",
        notes="Leading mobile gaming industry news and analysis."
    ),
    TrustedSource(
        name="GameDeveloper (formerly Gamasutra)",
        domain="gamedeveloper.com",
        base_url="https://www.gamedeveloper.com",
        source_type="blog",
        credibility=0.95,
        topics=["game development", "design", "business", "technology", "postmortems"],
        update_frequency="daily",
        notes="Industry-standard game development content."
    ),
]

# ============================================================================
# TIER 2: DATA & ANALYTICS PROVIDERS
# ============================================================================

DATA_PROVIDERS = [
    TrustedSource(
        name="Sensor Tower",
        domain="sensortower.com",
        base_url="https://sensortower.com",
        source_type="data",
        credibility=1.0,
        topics=["app analytics", "revenue data", "downloads", "market intelligence"],
        update_frequency="monthly",
        notes="Gold standard for mobile app market data."
    ),
    TrustedSource(
        name="data.ai (formerly App Annie)",
        domain="data.ai",
        base_url="https://www.data.ai",
        source_type="data",
        credibility=1.0,
        topics=["app intelligence", "market data", "trends", "downloads", "revenue"],
        update_frequency="monthly",
        notes="Comprehensive app market intelligence."
    ),
    TrustedSource(
        name="Newzoo",
        domain="newzoo.com",
        base_url="https://newzoo.com",
        source_type="report",
        credibility=1.0,
        topics=["gaming market", "esports", "forecasts", "consumer insights"],
        update_frequency="quarterly",
        notes="Leading gaming market research and forecasts."
    ),
    TrustedSource(
        name="AppMagic",
        domain="appmagic.rocks",
        base_url="https://appmagic.rocks",
        source_type="data",
        credibility=0.85,
        topics=["app analytics", "market data", "downloads", "revenue estimates"],
        update_frequency="monthly",
        notes="Affordable app market intelligence."
    ),
    TrustedSource(
        name="GameAnalytics",
        domain="gameanalytics.com",
        base_url="https://gameanalytics.com",
        source_type="blog",
        credibility=0.9,
        topics=["game analytics", "benchmarks", "best practices", "kpis"],
        update_frequency="monthly",
        notes="Free analytics platform with excellent blog content."
    ),
]

# ============================================================================
# TIER 3: PLATFORM & VENDOR BLOGS
# ============================================================================

PLATFORM_BLOGS = [
    TrustedSource(
        name="Unity Blog",
        domain="blog.unity.com",
        base_url="https://blog.unity.com",
        source_type="blog",
        credibility=0.85,
        topics=["game development", "unity", "technology", "case studies"],
        update_frequency="weekly",
        notes="Engine vendor perspective with good case studies."
    ),
    TrustedSource(
        name="ironSource Blog",
        domain="ironsource.com/blog",
        base_url="https://www.ironsrc.com/blog",
        source_type="blog",
        credibility=0.85,
        topics=["monetization", "mediation", "ua", "adtech"],
        update_frequency="weekly",
        notes="Mediation platform with solid monetization insights."
    ),
    TrustedSource(
        name="AppLovin Blog",
        domain="applovin.com/blog",
        base_url="https://www.applovin.com/blog",
        source_type="blog",
        credibility=0.85,
        topics=["mobile marketing", "monetization", "ua", "growth"],
        update_frequency="monthly",
        notes="Major adtech platform insights."
    ),
    TrustedSource(
        name="Google Play Developer Blog",
        domain="android-developers.googleblog.com",
        base_url="https://android-developers.googleblog.com",
        source_type="blog",
        credibility=0.9,
        topics=["android", "play store", "monetization", "policy"],
        update_frequency="weekly",
        notes="Official Google Play updates and best practices."
    ),
    TrustedSource(
        name="Apple Developer News",
        domain="developer.apple.com/news",
        base_url="https://developer.apple.com/news",
        source_type="blog",
        credibility=0.9,
        topics=["ios", "app store", "monetization", "policy"],
        update_frequency="monthly",
        notes="Official Apple platform updates."
    ),
]

# ============================================================================
# TIER 4: CONFERENCE & TRADE SHOWS
# ============================================================================

CONFERENCE_SOURCES = [
    TrustedSource(
        name="GDC Vault",
        domain="gdcvault.com",
        base_url="https://www.gdcvault.com",
        source_type="conference",
        credibility=1.0,
        topics=["game development", "design", "talks", "postmortems", "technical"],
        update_frequency="annual",
        notes="Game Developers Conference talks and presentations."
    ),
    TrustedSource(
        name="GDC YouTube",
        domain="youtube.com/@gdconf",
        base_url="https://www.youtube.com/@gdconf",
        source_type="conference",
        credibility=1.0,
        topics=["game development", "design", "talks", "postmortems"],
        update_frequency="annual",
        notes="Free GDC talks on YouTube."
    ),
    TrustedSource(
        name="Pocket Gamer Connects",
        domain="pgconnects.com",
        base_url="https://www.pgconnects.com",
        source_type="conference",
        credibility=0.85,
        topics=["mobile gaming", "talks", "industry trends"],
        update_frequency="quarterly",
        notes="Mobile gaming conference talks and content."
    ),
]

# ============================================================================
# TIER 5: ACADEMIC & RESEARCH
# ============================================================================

ACADEMIC_SOURCES = [
    TrustedSource(
        name="ACM Digital Library (Games)",
        domain="dl.acm.org",
        base_url="https://dl.acm.org",
        source_type="academic",
        credibility=1.0,
        topics=["game research", "hci", "player behavior", "algorithms"],
        update_frequency="continuous",
        notes="Peer-reviewed academic papers on games."
    ),
    TrustedSource(
        name="DiGRA (Digital Games Research)",
        domain="digra.org",
        base_url="https://www.digra.org",
        source_type="academic",
        credibility=0.95,
        topics=["game studies", "research", "theory", "culture"],
        update_frequency="annual",
        notes="Academic game studies research."
    ),
]

# ============================================================================
# COMBINED LISTS
# ============================================================================

ALL_SOURCES = (
    COMPETITOR_BLOGS +
    DATA_PROVIDERS +
    PLATFORM_BLOGS +
    CONFERENCE_SOURCES +
    ACADEMIC_SOURCES
)

# Domain to Source mapping for quick lookup
DOMAIN_MAP = {source.domain: source for source in ALL_SOURCES}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_sources_by_type(source_type: str) -> List[TrustedSource]:
    """Get all sources of a specific type"""
    return [s for s in ALL_SOURCES if s.source_type == source_type]


def get_sources_by_credibility(min_credibility: float = 0.9) -> List[TrustedSource]:
    """Get sources above a credibility threshold"""
    return [s for s in ALL_SOURCES if s.credibility >= min_credibility]


def get_sources_by_topic(topic: str) -> List[TrustedSource]:
    """Get sources covering a specific topic"""
    topic_lower = topic.lower()
    return [s for s in ALL_SOURCES if topic_lower in [t.lower() for t in s.topics]]


def get_tier1_domains() -> List[str]:
    """Get Tier 1 competitor blog domains for priority search"""
    return [s.domain for s in COMPETITOR_BLOGS]


def get_all_domains() -> List[str]:
    """Get all trusted source domains"""
    return [s.domain for s in ALL_SOURCES]


def format_brave_search_query(topic: str, include_domains: List[str] = None) -> str:
    """
    Format a Brave Search query with site: filters

    Args:
        topic: The search topic
        include_domains: List of domains to search within

    Returns:
        Formatted search query with site: filters
    """
    if not include_domains:
        include_domains = get_tier1_domains()

    # Brave Search format: topic (site:domain1.com OR site:domain2.com)
    site_filters = " OR ".join([f"site:{domain}" for domain in include_domains])
    return f"{topic} ({site_filters})"


def get_source_info(domain: str) -> TrustedSource:
    """Get source information by domain"""
    return DOMAIN_MAP.get(domain)


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    print(f"Total trusted sources: {len(ALL_SOURCES)}\n")

    print("TIER 1: Competitor Blogs")
    print("-" * 60)
    for source in COMPETITOR_BLOGS:
        print(f"  {source.name} ({source.domain})")
        print(f"    Credibility: {source.credibility} | Topics: {', '.join(source.topics[:3])}")

    print("\nDATA PROVIDERS")
    print("-" * 60)
    for source in DATA_PROVIDERS:
        print(f"  {source.name} ({source.domain})")

    print("\nExample: Find sources about 'monetization'")
    print("-" * 60)
    monetization_sources = get_sources_by_topic("monetization")
    for source in monetization_sources[:5]:
        print(f"  - {source.name} ({source.credibility})")

    print("\nExample: Brave Search query")
    print("-" * 60)
    query = format_brave_search_query("mobile game retention strategies")
    print(f"  {query}")
