# Architecture

## Overview

AGC Content Engine uses a multi-agent swarm architecture where specialized agents handle different aspects of content creation. Local LLMs handle the bulk of processing to minimize API costs, with cloud models reserved for quality-critical steps.

## Design Principles

1. **Local-first** — 70%+ of work done by local models
2. **Quality gates** — Each stage must pass before proceeding
3. **Fact-verified** — No claim without a dated, verified source
4. **Human-passable** — Content must pass AI detection tools
5. **Adrian's voice** — Match tone from existing articles

## Agent Swarm Architecture

```
                    ┌─────────────────────────┐
                    │    SUPERVISOR AGENT     │
                    │  (Opus - cloud, sparingly)│
                    │                         │
                    │  • Orchestrates pipeline │
                    │  • Quality gates        │
                    │  • Final approval       │
                    │  • Error recovery       │
                    └───────────┬─────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
        ▼                       ▼                       ▼
┌───────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ RESEARCH AGENT│     │  WRITER AGENT   │     │  MEDIA AGENT    │
│ (Qwen 2.5 14B)│     │(Llama 3.2 11B)  │     │(Gemini 3 Pro)   │
│               │     │                 │     │                 │
│ • Keyword     │     │ • Outline       │     │ • Header image  │
│   research    │     │ • First draft   │     │ • YouTube search│
│ • Source      │     │ • Section       │     │ • Tables        │
│   gathering   │     │   expansion     │     │ • Infographics  │
│ • Competitor  │     │ • Voice match   │     │                 │
│   analysis    │     │                 │     │                 │
└───────┬───────┘     └────────┬────────┘     └────────┬────────┘
        │                      │                       │
        ▼                      ▼                       ▼
┌───────────────┐     ┌─────────────────┐     ┌─────────────────┐
│FACT CHECKER   │     │   SEO AGENT     │     │ HUMANIZER AGENT │
│(DeepSeek-R1)  │     │(Qwen 2.5 14B)   │     │ (Sonnet - cloud)│
│               │     │                 │     │                 │
│ • Verify stats│     │ • Keyword       │     │ • AI detection  │
│ • Check dates │     │   density       │     │   testing       │
│ • Find primary│     │ • Meta tags     │     │ • Rewrite       │
│   sources     │     │ • Internal      │     │   flagged text  │
│ • Format      │     │   linking       │     │ • Add voice     │
│   citations   │     │ • Readability   │     │ • Burstiness    │
└───────────────┘     └─────────────────┘     └─────────────────┘
```

## Pipeline Flow

```
┌─────────┐   ┌──────────┐   ┌────────┐   ┌──────────┐   ┌───────────┐
│  TOPIC  │──▶│ RESEARCH │──▶│ WRITE  │──▶│FACT CHECK│──▶│   MEDIA   │
└─────────┘   └──────────┘   └────────┘   └──────────┘   └───────────┘
                                                               │
┌─────────┐   ┌──────────┐   ┌────────┐   ┌──────────┐         │
│ PUBLISH │◀──│  HUMAN   │◀──│HUMANIZE│◀──│   SEO    │◀────────┘
└─────────┘   └──────────┘   └────────┘   └──────────┘
               (approval)
```

### Stage Details

#### 1. Research (Local: Qwen 2.5 14B)
**Input:** Topic/keyword
**Output:** Research bundle (sources.json, outline.md)

- Web search via Brave/Grok API
- Filter sources by date (<12 months preferred)
- Extract key stats, quotes, data points
- Identify content gaps vs competitors
- Generate initial outline

**Quality Gate:** Minimum 10 unique sources, 5 must be <6 months old

#### 2. Write (Local: Llama 3.2 11B)
**Input:** Research bundle
**Output:** First draft (draft.md)

- Expand outline into full article
- Include citation placeholders [SOURCE_1], [SOURCE_2]
- Match article structure from SEObot analysis
- Target 2000-3000 words

**Quality Gate:** All sections complete, word count met

#### 3. Fact Check (Local: DeepSeek-R1 14B)
**Input:** Draft with sources
**Output:** Verified draft with citations

- Verify each stat against source
- Check source publication dates
- Replace placeholders with proper citations
- Flag unverifiable claims for removal
- Find additional supporting sources if needed

**Quality Gate:** 100% of stats verified, no claims without sources

#### 4. Media (Cloud: Gemini 3 Pro Image)
**Input:** Verified draft
**Output:** Enhanced draft with media

- Generate header image via nano-banana-pro
- Search YouTube for 2-3 relevant videos
- Create data tables from stats
- Generate infographics if data supports

**Quality Gate:** Header image + at least 1 video embed

#### 5. SEO Optimization (Local: Qwen 2.5 14B)
**Input:** Media-enhanced draft
**Output:** SEO-optimized draft

- Keyword density check (1-2%)
- Meta title and description
- H2/H3 structure optimization
- Internal linking suggestions
- Readability scoring (target: Grade 8-10)

**Quality Gate:** Readability score, keyword density in range

#### 6. Humanize (Cloud: Sonnet)
**Input:** SEO-optimized draft
**Output:** Human-passable final draft

- Run through AI detectors (GPTZero, Originality)
- Rewrite flagged passages
- Add burstiness (sentence length variation)
- Inject Adrian's voice patterns
- Add opinions, rhetorical questions

**Quality Gate:** Pass AI detection (<20% AI score)

#### 7. Human Review
**Input:** Final draft
**Output:** Approved article

- Supervisor agent presents to Adrian via Telegram
- Adrian approves, requests changes, or declines
- Iterate if needed

#### 8. Publish
**Input:** Approved article
**Output:** Live on adriancrook.com

- WordPress REST API upload
- Set category, tags, featured image
- Schedule or publish immediately

## Model Specifications

### Local Models (via Ollama)

| Model | Size | RAM Usage | Purpose |
|-------|------|-----------|---------|
| qwen2.5:14b | 14B | ~10GB | Research, SEO |
| llama3.2:11b | 11B | ~8GB | Writing |
| deepseek-r1:14b | 14B | ~10GB | Fact-checking |

**Note:** 32GB Mac Mini can run 2-3 models concurrently.

### Cloud Models (API)

| Model | Provider | Purpose | When Used |
|-------|----------|---------|-----------|
| Gemini 3 Pro Image | Google | Image generation | Media stage |
| Claude Sonnet | Anthropic | Humanization | Humanize stage |
| Claude Opus | Anthropic | Supervision | Orchestration |

## Cost Optimization

**Per Article Estimate:**

| Stage | Model | Tokens | Cost |
|-------|-------|--------|------|
| Research | Local | ~5K | $0 |
| Write | Local | ~10K | $0 |
| Fact Check | Local | ~5K | $0 |
| SEO | Local | ~3K | $0 |
| Media | Gemini | 1 image | ~$0.05 |
| Humanize | Sonnet | ~5K | ~$0.10 |
| Supervisor | Opus | ~2K | ~$0.20 |

**Total: ~$0.35/article** (vs SEObot subscription)

## Error Handling

- Each agent retries 3x on failure
- Supervisor can reassign tasks between agents
- Failed stages trigger rollback to previous checkpoint
- Human escalation for persistent failures

## Monitoring

- Log all agent interactions
- Track quality gate pass/fail rates
- Monitor token usage per stage
- Alert on repeated failures
