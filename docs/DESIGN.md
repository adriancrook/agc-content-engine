# AGC Content Engine - Design Document

## Overview

AGC (Automated Generated Content) Content Engine is an AI-powered content generation system designed to produce SEO-optimized blog articles for adriancrook.com using local LLMs (free) with cloud fallback for specific tasks.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         RAILWAY (Cloud)                          │
│  ┌─────────────────┐    ┌─────────────────┐                     │
│  │   Flask API     │────│   PostgreSQL    │                     │
│  │   (web/app.py)  │    │   (articles,    │                     │
│  │                 │    │    topics,      │                     │
│  │  /api/topics    │    │    tasks)       │                     │
│  │  /api/tasks     │    └─────────────────┘                     │
│  │  /api/articles  │                                            │
│  │  /dashboard     │                                            │
│  └────────┬────────┘                                            │
└───────────┼─────────────────────────────────────────────────────┘
            │ HTTPS
            │
┌───────────┼─────────────────────────────────────────────────────┐
│           │              MAC MINI (Local)                        │
│  ┌────────┴────────┐    ┌─────────────────┐                     │
│  │  Local Worker   │────│     Ollama      │                     │
│  │  (worker/       │    │  qwen2.5:14b    │                     │
│  │   local_worker  │    │  (14B params)   │                     │
│  │   .py)          │    │  FREE inference │                     │
│  └─────────────────┘    └─────────────────┘                     │
└─────────────────────────────────────────────────────────────────┘
```

## Pipeline Flow

### 1. Topic Discovery
- User clicks "Generate Topics" in dashboard
- TopicDiscoveryAgent uses Brave Search API + local LLM
- Generates 20 SEO-optimized topic ideas
- Topics saved to PostgreSQL with status="pending"

### 2. Topic Approval
- User reviews topics in dashboard
- Clicks "Approve" on promising topics
- API creates:
  - Article record (status="draft")
  - Research task (linked to article_id)
- Topic status changes to "processing"

### 3. Research Phase
- Local worker polls `/api/tasks/pending`
- Claims research task
- ResearchAgent:
  - Web search via Brave API (10+ sources)
  - LLM analyzes each source for stats/quotes
  - Generates article outline
  - Identifies competitor gaps
- Result: Research bundle with sources, outline, gaps

### 4. Write Phase
- Research completion triggers write task creation
- WriterAgent:
  - Uses research bundle + outline
  - Writes introduction, body sections, conclusion
  - Local LLM (qwen2.5:14b) - FREE
- Result: Draft article (2500+ words)

### 5. Fact Check Phase (TODO)
- Write completion triggers fact_check task
- FactCheckerAgent verifies claims against sources
- Flags unsupported statements

### 6. SEO Optimization Phase (TODO)
- SEOAgent optimizes:
  - Keyword density
  - Meta descriptions
  - Internal linking suggestions

### 7. Humanization Phase (TODO)
- HumanizerAgent (Claude Sonnet via OpenRouter)
- Makes content pass AI detection
- Adds natural voice, removes robotic patterns

## Current Issues (As of 2026-02-08)

### Issue 1: article_id Not Linked to Tasks
**Location:** `web/app.py` - `api_approve_topic()`
**Problem:** When topic is approved, article is created but task doesn't receive article_id properly
**Evidence:** Debug log shows `article_id=None` in worker
**Fix needed:** Verify `create_article()` returns dict with `id`, and `create_task()` receives it

### Issue 2: Task Chaining Not Working
**Location:** `web/app.py` - `api_complete_task()`
**Problem:** When research completes, write task should be auto-created. Not happening.
**Root cause:** The chaining code checks for `article_id` which is None
**Fix needed:** Fix Issue 1 first, then verify chaining logic

### Issue 3: Article Content Not Saved
**Location:** `web/app.py` - `api_complete_task()` and `worker/local_worker.py`
**Problem:** Write tasks complete but article content shows 0 chars
**Root cause:** Worker sends result to API, but API doesn't update article
**Fix needed:** Either:
  - Fix API to extract `draft` from result and save to article
  - Or have worker call PUT `/api/articles/{id}` directly

### Issue 4: JSON Parsing Failures
**Location:** `agents/research.py` - `_analyze_source()`
**Problem:** qwen2.5:14b generates malformed JSON (unquoted keys, trailing commas)
**Fix applied:** Added regex-based JSON repair in research.py
**Status:** Partially fixed, needs testing

## Agent Configurations

| Agent | Model | Type | Cost |
|-------|-------|------|------|
| TopicDiscoveryAgent | qwen2.5:14b | Local Ollama | $0.00 |
| ResearchAgent | qwen2.5:14b | Local Ollama | $0.00 |
| WriterAgent | qwen2.5:14b | Local Ollama | $0.00 |
| FactCheckerAgent | qwen2.5:14b | Local Ollama | $0.00 |
| SEOAgent | qwen2.5:14b | Local Ollama | $0.00 |
| MediaAgent | gemini-2.0-flash | Google API | ~$0.01/article |
| HumanizerAgent | claude-sonnet | OpenRouter | ~$0.10/article |

## Environment Variables

### Railway Service
- `DATABASE_URL` - PostgreSQL connection string (auto-set by Railway)
- `PORT` - HTTP port (default 8080)

### Local Worker
- `AGC_API_URL` - Railway API URL
- `BRAVE_API_KEY` - Brave Search API key
- `OLLAMA_URL` - Local Ollama endpoint (default http://localhost:11434)

## File Structure

```
agc-content-engine/
├── agents/
│   ├── base.py           # BaseAgent class
│   ├── research.py       # Web search + source analysis
│   ├── writer.py         # Article draft generation
│   ├── fact_checker.py   # Claim verification
│   ├── seo.py            # SEO optimization
│   ├── humanizer.py      # AI detection bypass
│   ├── media.py          # Image generation
│   ├── topic_discovery.py# Topic ideation
│   └── supervisor.py     # Pipeline orchestration
├── worker/
│   └── local_worker.py   # Polls Railway, runs local agents
├── web/
│   ├── app.py            # Flask API + routes
│   └── templates/        # Jinja2 templates
├── shared/
│   └── database.py       # SQLAlchemy models + queries
├── dashboard/            # Moltcraft-based pixel dashboard
│   ├── index.html
│   ├── css/
│   ├── js/
│   │   ├── app.js
│   │   └── agc-adapter.js
│   └── assets/
├── docs/
│   ├── DESIGN.md         # This file
│   ├── AGENTS.md
│   ├── ARCHITECTURE.md
│   └── SEOBOT_REFERENCE.md
├── Dockerfile
├── requirements.txt
└── README.md
```

## Dashboard

The pixel dashboard (Moltcraft-based) provides:
- Real-time agent status visualization
- 6 animated pixel characters representing agents
- Task queue monitoring
- Cost tracking
- Article progress view

**URL:** https://agc-content-engine-production.up.railway.app/dashboard

## Next Steps to Fix

1. **Fix article_id linking** in `api_approve_topic()`
2. **Verify task chaining** in `api_complete_task()`
3. **Add content saving** - either in API or worker
4. **Test full pipeline** with a fresh topic
5. **Add error handling** throughout
6. **Add logging** to Railway for debugging

## Original Requirements (from SEOBot reference)

- Beat SEObot quality
- Pass AI detectors
- Use fresh data (citations)
- Multi-modal content (images, videos, tables)
- SEO optimization
- Cost-effective (local LLMs where possible)
