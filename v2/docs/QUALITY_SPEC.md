# AGC v2 Quality Spec — SEObot Parity

*Target: Match or exceed SEObot output quality*

Reference article analyzed: "How To Reduce Drop-Off During Onboarding" (adriancrook.com)

---

## Executive Summary

SEObot produces high-quality, research-backed articles with:
- Clickable source citations `[[1]]`, `[[2]]`
- Real game/company examples with hyperlinks
- Expert quotes in blockquotes
- YouTube video embeds
- Infographics/figures
- FAQ sections
- Internal links to other site articles
- Key takeaways summary at top

**AGC v2 current gaps:**
1. No clickable citation links
2. No game/company hyperlinks
3. Generic language instead of expert quotes
4. No video embeds
5. No figures/infographics
6. No FAQ section
7. No internal linking
8. No key takeaways summary
9. Too much "fluffy" corporate language

---

## Article Structure Template

```markdown
# [Title]

[Opening hook with specific statistic + context]

**Key Takeaways:**
- **[Action 1]:** Brief explanation
- **[Action 2]:** Brief explanation
- **[Action 3]:** Brief explanation
- **[Action 4]:** Brief explanation

![Figure description](image-url)
*Caption: Figure description*

## [YouTube Video Title]
[Embedded YouTube video]

## [Section 1 H2]

[Content with citations [[1]][[2]]]

### [Subsection H3]

[Content with expert quote in blockquote]

> "Quote text" [[source]]
> — Expert Name, Title at Company

[More content with game examples linked]

... [repeat sections] ...

## Conclusion

[Summary + call to action]

## FAQs

### [Question 1]
[Answer]

### [Question 2]
[Answer]

### [Question 3]
[Answer]
```

---

## Agent-by-Agent Requirements

### 1. Research Agent

**Current:** Gathers sources, creates outline
**Required additions:**

```python
research_output = {
    "sources": [
        {
            "id": 1,
            "url": "https://developer.apple.com/...",
            "title": "Apple Developer - Onboarding for Games",
            "type": "documentation",  # documentation|article|study|news
            "key_stats": ["20% abandon in 2 min", "..."],
            "key_quotes": [
                {
                    "text": "Users should do something fun...",
                    "author": "GameAnalytics",
                    "author_url": "https://gameanalytics.com"
                }
            ],
            "credibility": "high"  # high|medium|low
        }
    ],
    "game_examples": [
        {
            "name": "Clash Royale",
            "company": "Supercell",
            "url": "https://supercell.com/en/games/clashroyale/",
            "relevance": "Tutorial structure example"
        }
    ],
    "youtube_videos": [
        {
            "id": "xaLNqVdKDhE",
            "title": "How to Improve Your App's Onboard Process",
            "channel": "Sean Allen",
            "relevance_score": 0.9
        }
    ],
    "internal_links": [
        {
            "url": "/innovative-retention-strategies/",
            "anchor_text": "innovative retention strategies",
            "context": "When discussing retention"
        }
    ],
    "statistics": [
        {
            "stat": "73% of players quit within 24 hours",
            "source_id": 1,
            "verification": "confirmed"
        }
    ]
}
```

**New tasks:**
- [ ] Find 10-20 credible sources per article
- [ ] Extract 3-5 expert quotes with attribution
- [ ] Find 5-8 real game examples with URLs
- [ ] Search YouTube for 1-2 relevant videos
- [ ] Query existing site for internal link opportunities
- [ ] Verify statistics against sources

---

### 2. Writer Agent

**Current:** Generates draft prose
**Required additions:**

**Citation format:**
```markdown
<!-- WRONG (current AGC) -->
Research by Appinventiv reveals that hybrid monetization strategies are becoming common.

<!-- RIGHT (SEObot style) -->
Research by [Appinventiv](https://appinventiv.com) reveals that hybrid monetization strategies are becoming the default approach [[2]](https://appinventiv.com/blog/mobile-monetization).
```

**Quote format:**
```markdown
<!-- WRONG -->
Experts suggest that onboarding should be fun and fast.

<!-- RIGHT -->
> "Users should do something fun as soon as they open your mobile game" [[9]](https://gameanalytics.com/blog/ftue)
> — GameAnalytics
```

**Game example format:**
```markdown
<!-- WRONG -->
Games like Clash Royale use tiered tutorials effectively.

<!-- RIGHT -->
[Clash Royale](https://supercell.com/en/games/clashroyale/) breaks its onboarding into five short tutorials. Each segment introduces a new concept, such as combining cards for stronger attacks [[2]](https://developer.apple.com/app-store/onboarding-for-games).
```

**Prompt additions:**
```
CRITICAL FORMATTING RULES:
1. Every statistic MUST have a citation: "73% quit in 24h [[1]]"
2. Every quote MUST be in blockquote with attribution
3. Every game mention MUST include company URL
4. Every company mention MUST be hyperlinked
5. Use specific numbers, not "many" or "significant"
6. Avoid: "transformative", "paradigm shift", "unprecedented", "landscape"
7. Prefer: direct, specific, actionable language
```

**Structure requirements:**
- [ ] Opening hook with specific stat (first paragraph)
- [ ] Key takeaways bullets (after intro, before first H2)
- [ ] Minimum 15 citations per article
- [ ] Minimum 3 expert quotes in blockquotes
- [ ] Minimum 5 game/company examples with links
- [ ] Conclusion with actionable summary
- [ ] 3 FAQ items at end

---

### 3. Fact Checker Agent

**Current:** Verifies claims
**Required additions:**

- [ ] Verify every `[[n]]` citation URL is accessible
- [ ] Verify quoted statistics match source
- [ ] Verify expert quotes are real (not hallucinated)
- [ ] Verify game/company URLs are correct
- [ ] Flag any unverified claims for removal or rewrite
- [ ] Check publication dates (reject sources older than 2 years for stats)

**Output format:**
```python
fact_check_result = {
    "verified_citations": [1, 2, 3, 5, 7],
    "failed_citations": [
        {"id": 4, "reason": "URL 404", "action": "remove"}
    ],
    "unverified_quotes": [
        {"text": "...", "reason": "Cannot find source", "action": "remove"}
    ],
    "hallucination_flags": [],
    "overall_score": 0.92
}
```

---

### 4. SEO Agent

**Current:** Keyword optimization
**Required additions:**

- [ ] Generate meta description (150-160 chars)
- [ ] Generate meta keywords (8-10 terms)
- [ ] Ensure H2/H3 hierarchy is correct
- [ ] Add internal links (2-3 per article)
- [ ] Verify keyword density (1-2% primary keyword)
- [ ] Generate FAQ schema markup
- [ ] Generate article schema markup

**Internal linking logic:**
```python
# Query existing published articles
existing_articles = fetch_sitemap("https://adriancrook.com/sitemap.xml")

# Find relevant internal links based on topic overlap
for section in article.sections:
    related = find_related_articles(section.topic, existing_articles)
    if related:
        insert_internal_link(section, related[0])
```

---

### 5. Media Agent

**Current:** Placeholder for images
**Required additions:**

**YouTube embedding:**
```python
def find_youtube_video(topic: str, research_data: dict) -> dict:
    """Find relevant YouTube video from research or search."""
    # Priority 1: Use video from research agent
    if research_data.get("youtube_videos"):
        return research_data["youtube_videos"][0]
    
    # Priority 2: Search YouTube API
    results = youtube_search(
        query=f"{topic} tutorial",
        published_after="2024-01-01",
        max_results=5
    )
    return select_best_video(results, topic)

def embed_youtube(video_id: str) -> str:
    return f'<iframe src="https://www.youtube.com/embed/{video_id}" ...></iframe>'
```

**Header image (using Gemini 3 Pro Image):**
```python
def generate_header_image(title: str, brand_style: str) -> str:
    """Generate header image using nano-banana-pro skill."""
    prompt = f"""
    Photorealistic image for article: {title}
    Style: Modern, professional, clean composition
    Color palette: Warm, approachable
    NO text in image
    """
    return generate_image(prompt, model="gemini-3-pro-image")
```

**Figure/infographic generation:**
```python
def generate_comparison_table_image(data: dict) -> str:
    """Generate infographic for statistics/comparisons."""
    # Use structured data to create visual
    # Can use: matplotlib, plotly, or AI image generation
    pass
```

---

### 6. Humanizer Agent

**Current:** Makes content pass AI detectors
**Required additions:**

**Remove corporate fluff:**
```python
BANNED_PHRASES = [
    "transformative", "paradigm shift", "unprecedented",
    "landscape", "leverage", "synergy", "holistic",
    "cutting-edge", "game-changer", "best-in-class",
    "at the end of the day", "moving forward",
    "in today's world", "it goes without saying"
]

REPLACEMENT_RULES = {
    "utilize": "use",
    "implement": "add" or "build",
    "facilitate": "help" or "enable",
    "leverage": "use",
    "optimize": "improve",
    "robust": "strong" or "solid"
}
```

**Tone matching (from SEOBOT_REFERENCE.md):**
```
Apply style, voice and tone:
- Direct, not meandering
- Specific, not vague
- Evidence-backed, not opinion
- Actionable, not theoretical
- Conversational but professional
```

---

### 7. NEW: Enrichment Agent

**Purpose:** Add missing elements before final output

**Checklist:**
- [ ] Key takeaways present? If not, generate from content
- [ ] YouTube video embedded? If not, search and add
- [ ] FAQ section present? If not, generate 3 questions
- [ ] Header image present? If not, generate
- [ ] Internal links present (min 2)? If not, find and add
- [ ] All citations properly formatted as `[[n]](url)`?
- [ ] All game/company names hyperlinked?

---

## Quality Gates

### Pre-Publication Checklist

| Check | Requirement | Pass Threshold |
|-------|-------------|----------------|
| Word count | 2000-3500 words | Hard requirement |
| Citations | Clickable `[[n]]` format | Min 15 |
| Expert quotes | Blockquote format | Min 3 |
| Game examples | With hyperlinks | Min 5 |
| YouTube embed | Working video | Min 1 |
| Internal links | To existing articles | Min 2 |
| FAQ section | 3 questions | Required |
| Key takeaways | Bullet list at top | Required |
| Header image | Generated or sourced | Required |
| AI detection | Pass Originality.ai | >90% human |
| Fact check | All claims verified | 100% |
| Broken links | None | 0 |

### Scoring Rubric

```python
def calculate_quality_score(article: Article) -> float:
    score = 0.0
    
    # Structure (25%)
    score += 0.05 if article.has_key_takeaways else 0
    score += 0.05 if article.has_faq_section else 0
    score += 0.05 if article.has_youtube_embed else 0
    score += 0.05 if article.has_header_image else 0
    score += 0.05 if article.word_count >= 2000 else 0
    
    # Citations (25%)
    citation_ratio = len(article.citations) / 15
    score += min(0.25, citation_ratio * 0.25)
    
    # Evidence (25%)
    score += 0.08 if len(article.expert_quotes) >= 3 else 0
    score += 0.08 if len(article.game_examples) >= 5 else 0
    score += 0.09 if len(article.statistics) >= 10 else 0
    
    # Quality (25%)
    score += 0.10 if article.fact_check_score >= 0.95 else 0
    score += 0.10 if article.ai_detection_score >= 0.90 else 0
    score += 0.05 if article.broken_links == 0 else 0
    
    return score  # 0.0 to 1.0
```

**Minimum score to publish: 0.80**

---

## Implementation Priority

### Phase 1: Citations & Links (Week 1)
1. Update Research Agent to extract source URLs
2. Update Writer Agent to use `[[n]](url)` format
3. Add link validation to Fact Checker

### Phase 2: Evidence & Quotes (Week 2)
1. Update Research Agent to extract expert quotes
2. Update Writer Agent to use blockquote format
3. Add game/company URL lookup

### Phase 3: Media & Structure (Week 3)
1. Add YouTube search to Research Agent
2. Add embed formatting to Media Agent
3. Add key takeaways generation
4. Add FAQ generation

### Phase 4: Enrichment & Polish (Week 4)
1. Build Enrichment Agent
2. Add internal link discovery
3. Add header image generation
4. Implement quality scoring

---

## Example: Before & After

### Before (Current AGC)

```markdown
## In-App Advertising Strategies

As the mobile monetization landscape continues its rapid evolution toward 2026, 
in-app advertising has solidified its position as the dominant revenue strategy 
for developers worldwide. According to Onix Systems research, in-app advertising 
is expected to comprise 52% of mobile monetization strategies.
```

### After (SEObot Parity)

```markdown
## In-App Advertising Strategies

Did you know that **52% of mobile games** will rely on in-app advertising as their 
primary revenue source by 2026? [[1]](https://onixsystems.com/blog/mobile-monetization-2026) 
That's a massive shift from traditional premium models.

[Candy Crush Saga](https://king.com/game/candycrush) pioneered this approach, 
generating **$1.2 billion annually** through a mix of rewarded video ads and 
optional IAP [[2]](https://sensortower.com/blog/candy-crush-revenue).

> "The key is making ads feel like part of the game, not an interruption"
> — Eric Seufert, Mobile Dev Memo [[3]](https://mobiledevmemo.com/ad-integration)
```

---

## Reference Files

- `/docs/SEOBOT_REFERENCE.md` — Full SEObot settings capture
- `/docs/QUALITY_SPEC.md` — This document
- `/examples/seobot-article.md` — Example high-quality article
- `/examples/agc-article.md` — Current AGC output for comparison

---

*Last updated: 2026-02-10*
*Author: Kit 🦊*
