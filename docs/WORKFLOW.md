# Content Pipeline Workflow

## Overview

This document describes the end-to-end workflow for generating a single article.

## Pre-requisites

1. Ollama installed and running
2. Local models pulled (see `scripts/setup_models.sh`)
3. API keys configured in `.config/secrets.yaml`
4. WordPress credentials configured

## Step-by-Step Workflow

### Step 1: Topic Selection

**Manual or automated topic selection.**

Options:
- Pick from SEObot's suggested topics
- Keyword gap analysis vs competitors
- Trending topics in mobile gaming

```bash
# Manual
python scripts/run_pipeline.py --topic "How to Reduce Player Churn"

# From keyword research
python scripts/suggest_topics.py --analyze-gaps
```

### Step 2: Research Phase

**Agent:** Research Agent (Qwen 2.5 14B)
**Duration:** ~2-5 minutes
**Cost:** $0 (local)

1. Web search for topic + related keywords
2. Filter results by recency (<12 months preferred)
3. Extract key stats, quotes, data points
4. Identify competitor content gaps
5. Generate article outline

**Output:** `outputs/article-{id}/1-research.json`

**Quality Check:**
- [ ] 10+ unique sources
- [ ] 5+ sources < 6 months old
- [ ] Outline has 4+ sections
- [ ] No broken URLs

### Step 3: Writing Phase

**Agent:** Writer Agent (Llama 3.2 11B)
**Duration:** ~5-10 minutes
**Cost:** $0 (local)

1. Load research bundle and template
2. Expand outline into full prose
3. Include citation placeholders
4. Match target word count (2000-3000)
5. Apply Adrian's tone/voice

**Output:** `outputs/article-{id}/2-draft.md`

**Quality Check:**
- [ ] 2000-3000 words
- [ ] All sections complete
- [ ] Compelling hook with stat
- [ ] Proper H2/H3 structure

### Step 4: Fact Verification

**Agent:** Fact Checker Agent (DeepSeek-R1 14B)
**Duration:** ~3-5 minutes
**Cost:** $0 (local)

1. Extract all claims from draft
2. Match claims to sources
3. Verify accuracy and recency
4. Format citations [1], [2], etc.
5. Flag or remove unverifiable claims

**Output:** `outputs/article-{id}/3-verified.md`

**Quality Check:**
- [ ] 100% claims verified
- [ ] No stats > 18 months old
- [ ] Citations properly formatted
- [ ] Sources list at bottom

### Step 5: Media Enrichment

**Agent:** Media Agent (Gemini 3 Pro Image)
**Duration:** ~2-3 minutes
**Cost:** ~$0.05

1. Generate header image with nano-banana-pro
2. Search YouTube for relevant videos
3. Create data tables from stats
4. (Optional) Generate infographics

**Output:** `outputs/article-{id}/4-media.json`

**Quality Check:**
- [ ] Header image generated
- [ ] Image alt text present
- [ ] 1-3 YouTube videos found
- [ ] Videos < 2 years old

### Step 6: SEO Optimization

**Agent:** SEO Agent (Qwen 2.5 14B)
**Duration:** ~2-3 minutes
**Cost:** $0 (local)

1. Check keyword density (1-2%)
2. Generate meta title/description
3. Suggest internal links
4. Score readability (target: grade 8-10)
5. Optimize H2/H3 keywords

**Output:** `outputs/article-{id}/5-seo.md`

**Quality Check:**
- [ ] Keyword density 1-2%
- [ ] Meta description < 160 chars
- [ ] Readability grade 8-10
- [ ] 2+ internal link opportunities

### Step 7: Humanization

**Agent:** Humanizer Agent (Claude Sonnet)
**Duration:** ~3-5 minutes
**Cost:** ~$0.10

1. Run through AI detectors
2. Identify flagged passages
3. Rewrite with burstiness
4. Add Adrian's voice patterns
5. Insert opinions/rhetorical questions

**Output:** `outputs/article-{id}/6-humanized.md`

**Quality Check:**
- [ ] AI score < 20% (GPTZero)
- [ ] AI score < 20% (Originality)
- [ ] Natural transitions
- [ ] Voice matches samples

### Step 8: Human Review

**Agent:** Supervisor Agent (Opus)
**Duration:** Depends on Adrian
**Cost:** ~$0.20

1. Compile final article bundle
2. Send preview to Adrian via Telegram
3. Wait for approval/feedback
4. Iterate if changes requested

**Commands:**
- "approve" → Proceed to publish
- "decline" → Archive, move to next topic
- "revise: [feedback]" → Re-run relevant stages

### Step 9: Publish

**Agent:** Supervisor Agent
**Duration:** ~1 minute
**Cost:** $0

1. Upload to WordPress via REST API
2. Set featured image
3. Apply category and tags
4. Schedule or publish immediately
5. Log to completion tracker

**Output:** Live article on adriancrook.com

## Full Pipeline Timing

| Stage | Duration | Cost |
|-------|----------|------|
| Research | 2-5 min | $0 |
| Write | 5-10 min | $0 |
| Fact Check | 3-5 min | $0 |
| Media | 2-3 min | $0.05 |
| SEO | 2-3 min | $0 |
| Humanize | 3-5 min | $0.10 |
| Review | Variable | $0.20 |
| Publish | 1 min | $0 |

**Total:** 20-35 minutes, ~$0.35/article

## Error Recovery

### Research fails
- Retry with broader keywords
- Fall back to cached similar research
- Escalate to human for manual sources

### Writing incomplete
- Re-run with smaller section chunks
- Try alternative model (Qwen as backup)

### Fact check fails
- Remove unverifiable claims
- Search for alternative sources
- Flag for human review

### AI detection fails
- Multiple rewrite passes
- Inject more voice samples
- Manual humanization as last resort

## Batch Processing

For multiple articles:

```bash
# Process topic queue
python scripts/batch_pipeline.py --topics topics.txt --parallel 2

# Resume failed batch
python scripts/batch_pipeline.py --resume
```

## Monitoring

View pipeline status:

```bash
# Current run
python scripts/status.py

# Historical runs
python scripts/status.py --history 10
```

Dashboard (future): Web UI showing pipeline status, costs, quality metrics.
