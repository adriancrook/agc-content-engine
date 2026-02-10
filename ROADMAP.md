# AGC Content Engine - Product Roadmap

**Goal:** Achieve feature parity with SEObot.ai and create WordPress-ready, citation-rich articles for adriancrook.com

**Last Updated:** 2025-02-09

---

## Current State

### ✅ Completed Features
- Multi-agent architecture (Research, Writer, SEO, Fact Checker, Humanizer, Media)
- Google Imagen 3 integration for header images
- Claude Sonnet 4 for all text generation (migrated from Ollama)
- Basic article generation pipeline
- Web UI for article management
- Progress tracking API
- Draft revision with enrichment data
- Source citation system (basic)

### 🚧 In Progress
- Image generation refinement (needs full article context)
- WordPress-compatible markdown output
- Enhanced citation and statistics integration

---

## Phase 1: WordPress-Ready Output (Priority: HIGH)

### 1.1 WordPress-Compatible Markdown
**Status:** Not Started
**Effort:** 2-3 days

**Requirements:**
- [ ] Use proper WordPress markdown/HTML formatting
- [ ] Ensure all HTML tags are WordPress-compatible
- [ ] Test image embedding formats (featured + inline)
- [ ] Validate heading hierarchy (H1 = title, H2-H6 for content)
- [ ] Support WordPress shortcodes where appropriate
- [ ] Handle lists, tables, quotes properly
- [ ] Add meta tags (title, description, keywords, categories, tags)

**Deliverables:**
- `WordPressFormatter` class in `v2/formatters/wordpress.py`
- Output validation tests
- Example WordPress-ready article in `test_outputs/`

---

## Phase 2: Rich Content Enhancement (Priority: HIGH)

### 2.1 Heavy Statistics & Citations
**Status:** Partially Complete
**Effort:** 3-4 days

**Current:** Basic citations in sources section
**Target:** SEObot-level citation density

**Requirements:**
- [ ] Inline citations throughout article [1], [2], [3]
- [ ] Structured Sources section at article end
  ```markdown
  ## Sources
  [1] Source Name - Article Title - https://url.com
  [2] Source Name - Article Title - https://url.com
  ```
- [ ] Minimum 10-15 citations per article
- [ ] Citation placement rules:
  - After every statistic
  - After every claim requiring verification
  - After quotes or expert opinions
- [ ] Fact-checker validation before citation assignment

**Implementation:**
- Enhance `DataEnrichmentAgent` to extract more sources
- Update `WriterAgent` revision pass to integrate inline citations
- Create citation validation in `FactCheckerAgent`

### 2.2 Tables & Structured Data
**Status:** Not Started
**Effort:** 2-3 days

**Requirements:**
- [ ] Comparison tables (e.g., game metrics, monetization models)
- [ ] Statistical summaries in table format
- [ ] Key metrics callout tables
- [ ] WordPress-compatible table markdown
- [ ] Mobile-responsive table formatting

**Example Tables to Support:**
| Game | ARPU | D30 Retention | Revenue Model |
|------|------|---------------|---------------|
| Candy Crush | $1.50 | 42% | Freemium |
| Clash Royale | $2.80 | 38% | Freemium |

**Implementation:**
- Add table generation to `WriterAgent`
- Create `TableBuilder` utility class
- Update prompts to request structured data in tables

### 2.3 Expert Quotes & Testimonials
**Status:** Basic (in enrichment)
**Effort:** 1-2 days

**Requirements:**
- [ ] Extract expert quotes from sources
- [ ] Format as blockquotes with attribution
- [ ] Include testimonials where relevant
- [ ] Minimum 2-3 quotes per article

**Format:**
```markdown
> "Quote text here that provides valuable insight."
> — Expert Name, Company/Publication
```

---

## Phase 3: Enhanced Image Generation (Priority: MEDIUM)

### 3.1 Smarter Image Prompts
**Status:** Partially Complete
**Effort:** 1-2 days

**Current:** Uses title + first paragraph
**Target:** Full article context for better relevance

**Requirements:**
- [ ] Send complete article text to image prompt generation
- [ ] Extract key themes and concepts from entire article
- [ ] Generate more specific, article-relevant prompts
- [ ] Ensure "photorealistic" style per SEObot specs
- [ ] 16:9 aspect ratio (already implemented)
- [ ] Alt text generation based on article content

**Implementation:**
- Update `MediaAgent._create_image_prompt()` to accept full article
- Use Claude to extract visual themes from complete text
- Refine prompt engineering for Imagen 3

### 3.2 Inline Images (Future)
**Status:** Not Started
**Effort:** 3-4 days
**Priority:** LOW (can be manual for now)

**Requirements:**
- [ ] Generate 2-3 inline images per article
- [ ] Simple illustrations/diagrams style (per SEObot specs)
- [ ] Section-specific images
- [ ] Proper WordPress embedding

---

## Phase 4: SEO & Link Optimization (Priority: HIGH)

### 4.1 Internal Linking
**Status:** Not Started
**Effort:** 2-3 days

**Requirements:**
- [ ] Scan existing adriancrook.com articles
- [ ] Build internal link database/index
- [ ] Automatically suggest relevant internal links
- [ ] Insert links naturally in article text
- [ ] Target: 3-5 internal links per article

**Implementation:**
- Create `InternalLinkingAgent` or add to `SEOAgent`
- Scrape/index existing blog posts
- Use semantic matching to find relevant links
- Update `WriterAgent` revision pass to integrate links

### 4.2 External Linking
**Status:** Basic (in research sources)
**Effort:** 1 day

**Requirements:**
- [ ] Link to authoritative external sources
- [ ] Open in new tab (WordPress setting)
- [ ] Minimum 5-8 external links per article
- [ ] Prioritize industry sources: Game Developer, Pocket Gamer, etc.

### 4.3 SEO Metadata Enhancement
**Status:** Basic
**Effort:** 1-2 days

**Requirements:**
- [ ] Generate SEO title (50-60 characters)
- [ ] Meta description (150-160 characters)
- [ ] Meta keywords (5-10 keywords)
- [ ] Categories from taxonomy tree
- [ ] Tags (8-12 tags)
- [ ] Open Graph tags for social sharing
- [ ] Schema.org markup

---

## Phase 5: Easy WordPress Publishing (Priority: HIGH)

### 5.1 WordPress Export Format
**Status:** Not Started
**Effort:** 2-3 days

**Requirements:**
- [ ] Single-click copy button in UI
- [ ] Pre-formatted for WordPress editor
- [ ] Include all metadata in copy
- [ ] Featured image handling instructions
- [ ] Categories and tags ready
- [ ] Option to export as `.md` or HTML
- [ ] Optional: Direct WordPress API integration

**UI Enhancement:**
```
[Copy for WordPress] [Download .md] [Preview]
```

### 5.2 Quality Checklist
**Status:** Not Started
**Effort:** 1 day

**Requirements:**
- [ ] Pre-publish checklist in UI:
  - [ ] 10+ citations present
  - [ ] Featured image generated
  - [ ] Internal links added
  - [ ] Tables included (if applicable)
  - [ ] SEO metadata complete
  - [ ] Word count 2000-3000+
  - [ ] Fact-checked

---

## Phase 6: Content Quality Improvements (Priority: MEDIUM)

### 6.1 Examples & Case Studies
**Status:** Partial (using real game names)
**Effort:** 2 days

**Requirements:**
- [ ] Minimum 3-5 real game examples per article
- [ ] Specific case studies with metrics
- [ ] Success/failure analysis
- [ ] Data-driven examples

### 6.2 Visual Elements
**Status:** Basic (markdown formatting)
**Effort:** 1-2 days

**Requirements:**
- [ ] Callout boxes for key insights
- [ ] Tip/warning/note blocks
- [ ] Step-by-step numbered processes
- [ ] Visual hierarchy with formatting

**Example:**
```markdown
> 💡 **Key Insight:** [Important takeaway]

> ⚠️ **Common Pitfall:** [Warning about mistake]
```

### 6.3 Actionable Takeaways
**Status:** Basic
**Effort:** 1 day

**Requirements:**
- [ ] "Key Takeaways" section at end of each article
- [ ] Bullet-point format
- [ ] 5-7 actionable items
- [ ] Developer/publisher-focused

---

## Phase 7: Advanced Features (Priority: LOW)

### 7.1 Multi-format Support
**Status:** Not Started
**Effort:** 3-5 days

**From SEObot reference:**
- [ ] Standard blog articles (current)
- [ ] Programmatic SEO (pSEO) pages
- [ ] Interactive tools/calculators
- [ ] Video-based articles
- [ ] Listicles
- [ ] Comparison articles

### 7.2 News Integration
**Status:** Not Started
**Effort:** 2-3 days

**From SEObot specs:**
- [ ] Monitor gamedeveloper.com for freemium news
- [ ] Suggest timely article topics
- [ ] Auto-generate news-based articles

### 7.3 YouTube Video Integration
**Status:** Not Started
**Effort:** 2-3 days

**From SEObot specs:**
- [ ] Search queries: "freemium game monetization", "mobile game product strategy", etc.
- [ ] Past month filter
- [ ] Embed relevant videos in articles
- [ ] Generate video-analysis articles

### 7.4 Competitor Analysis Awareness
**Status:** Not Started
**Effort:** 1 day

**From SEObot specs:**
- [ ] Exclude competitor mentions:
  - Department of Play
  - Mobile Game Doctor
  - AppTurbine
  - Mobile Free to Play
  - GameRefinery

### 7.5 CTA Integration
**Status:** Not Started
**Effort:** 1 day

**From SEObot specs:**
- [ ] Inline text & button CTA
- [ ] Title: "Optimize Your Freemium Game Profitability"
- [ ] Button: "Book a Free Consultation"
- [ ] Link: https://adriancrook.com/#contact-sec
- [ ] Auto-add to new articles

---

## Phase 8: Taxonomy & Topic Discovery (Priority: LOW)

### 8.1 Deep Topic Taxonomy
**Status:** Basic (using general topics)
**Effort:** 3-4 days

**From SEObot reference:** 20 top-level categories, 3-4 levels deep

**Categories to implement:**
1. Behavioral Design
2. Game Architecture
3. Game Balancing
4. Game Economy Design
5. Game Metrics
6. Gamification
7. Live Operations
8. Market Research
9. Monetization Strategy
10. Player Analytics
11. Player Engagement
12. Player Psychology
13. Product Management
14. Progression Systems
15. Purchase Optimization
16. Retention Systems
17. Soft Launch
18. User Acquisition
19. Virtual Economies
20. Web3 Gaming

**Implementation:**
- Create taxonomy database
- Update `TopicDiscoveryAgent` to use taxonomy
- Category-based article suggestions
- Tag generation from taxonomy

### 8.2 AI-Powered Topic Suggestions
**Status:** Basic
**Effort:** 2-3 days

**Requirements:**
- [ ] Suggest topics based on taxonomy
- [ ] Trend analysis for timely topics
- [ ] Gap analysis (what's not covered yet)
- [ ] Seasonal/event-based suggestions

---

## Technical Debt & Infrastructure

### Performance Optimization
- [ ] Cache Imagen 3 results to reduce regeneration costs
- [ ] Optimize Claude API calls (batch where possible)
- [ ] Database indexing for faster article retrieval
- [ ] Image compression before storage

### Testing
- [ ] End-to-end pipeline tests
- [ ] WordPress format validation tests
- [ ] Citation integrity tests
- [ ] Image generation tests
- [ ] Link validation tests

### Monitoring
- [ ] Cost tracking per article
- [ ] Agent performance metrics
- [ ] Error rate monitoring
- [ ] Quality score tracking

---

## Success Metrics

### Article Quality (SEObot Parity)
- [ ] 2000-3000+ word count
- [ ] 10-15+ citations per article
- [ ] 3-5 internal links
- [ ] 5-8 external links
- [ ] 1 featured image (16:9, photorealistic)
- [ ] 2-3 tables (where applicable)
- [ ] 3-5 real game examples
- [ ] SEO metadata complete
- [ ] WordPress-ready format

### Publishing Efficiency
- [ ] Single-click copy to WordPress
- [ ] <5 min manual edits per article
- [ ] Ready for immediate publishing
- [ ] Consistent formatting across all articles

### Cost per Article
- Current: ~$0.50-1.00 (estimated)
- Target: <$2.00 including images

---

## Next Steps (Immediate Priority)

1. **Phase 1.1:** WordPress-compatible markdown formatter (2-3 days)
2. **Phase 2.1:** Heavy citations & statistics (3-4 days)
3. **Phase 4.1:** Internal linking system (2-3 days)
4. **Phase 5.1:** Easy WordPress copy/export (2-3 days)
5. **Phase 2.2:** Tables & structured data (2-3 days)

**Estimated time to SEObot feature parity:** 3-4 weeks

---

## Notes

- All features should maintain mobile gaming industry focus
- Professional tone targeting game developers/publishers
- Real game examples: Candy Crush, Clash of Clans, Pokémon GO, Genshin Impact, PUBG Mobile, etc.
- Adrian Crook's voice: professional but practical, actionable, data-driven
- Cost-conscious: optimize API usage where possible
- Quality over quantity: better to have one excellent article than three mediocre ones

---

## References

- [SEObot Reference](docs/SEOBOT_REFERENCE.md) - adriancrook.com settings
- [Agents Documentation](docs/AGENTS.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Current Design](docs/NEW_DESIGN.md)
