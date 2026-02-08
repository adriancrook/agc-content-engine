# Agent Specifications

## Overview

Each agent is a standalone Python module that communicates with either a local Ollama model or cloud API. Agents receive structured inputs and produce structured outputs.

## Common Interface

All agents implement:

```python
class BaseAgent:
    def __init__(self, model: str, config: dict):
        """Initialize with model name and config."""
        pass
    
    def run(self, input: AgentInput) -> AgentOutput:
        """Execute the agent's task."""
        pass
    
    def validate_output(self, output: AgentOutput) -> bool:
        """Check if output meets quality gate."""
        pass
```

## Agent Definitions

### 1. Research Agent

**Model:** qwen2.5:14b (local)
**File:** `agents/research.py`

**Purpose:** Gather sources and create research bundle for a topic.

**Input:**
```json
{
  "topic": "How to Reduce Player Churn in Mobile Games",
  "keywords": ["player churn", "mobile game retention", "FTUE"],
  "max_sources": 20,
  "max_age_months": 12
}
```

**Output:**
```json
{
  "sources": [
    {
      "url": "https://...",
      "title": "...",
      "published_date": "2025-11-15",
      "key_stats": ["73% quit in 24h", "..."],
      "key_quotes": ["..."],
      "relevance_score": 0.92
    }
  ],
  "outline": {
    "title": "...",
    "sections": [
      {"h2": "...", "h3s": ["...", "..."], "key_points": ["..."]}
    ]
  },
  "competitor_gaps": ["..."]
}
```

**Quality Gate:**
- Minimum 10 sources
- At least 5 sources < 6 months old
- Outline has 4+ H2 sections

---

### 2. Writer Agent

**Model:** llama3.2:11b (local)
**File:** `agents/writer.py`

**Purpose:** Transform research into full article draft.

**Input:**
```json
{
  "research_bundle": { /* from Research Agent */ },
  "tone": "professional but accessible",
  "target_words": 2500,
  "template": "templates/article.md"
}
```

**Output:**
```json
{
  "draft": "# Title\n\n**Hook with stat**...",
  "word_count": 2450,
  "citation_placeholders": ["[SOURCE_1]", "[SOURCE_2]"],
  "sections_complete": true
}
```

**Quality Gate:**
- Word count 2000-3000
- All outline sections covered
- Hook includes compelling stat

---

### 3. Fact Checker Agent

**Model:** deepseek-r1:14b (local)
**File:** `agents/fact_checker.py`

**Purpose:** Verify all claims and format citations.

**Input:**
```json
{
  "draft": "...",
  "sources": [ /* from Research Agent */ ]
}
```

**Output:**
```json
{
  "verified_draft": "...",
  "citations": [
    {
      "claim": "73% of players quit within 24 hours",
      "source_url": "https://...",
      "source_date": "2025-08-12",
      "verified": true
    }
  ],
  "flagged_claims": [],
  "verification_rate": 1.0
}
```

**Quality Gate:**
- 100% claims verified or removed
- No sources older than 18 months for stats
- All citations properly formatted

---

### 4. Media Agent

**Model:** gemini-3-pro-image (cloud)
**File:** `agents/media.py`

**Purpose:** Generate images and curate multimedia.

**Input:**
```json
{
  "draft": "...",
  "topic": "...",
  "keywords": ["..."]
}
```

**Output:**
```json
{
  "header_image": {
    "path": "outputs/images/header-churn-reduction.png",
    "alt_text": "...",
    "prompt_used": "..."
  },
  "youtube_videos": [
    {
      "video_id": "xaLNqVdKDhE",
      "title": "...",
      "relevance_score": 0.89
    }
  ],
  "tables": [
    {
      "title": "Retention Benchmarks by Genre",
      "data": [...]
    }
  ]
}
```

**Quality Gate:**
- Header image generated
- At least 1 YouTube video found
- Videos are < 2 years old

---

### 5. SEO Agent

**Model:** qwen2.5:14b (local)
**File:** `agents/seo.py`

**Purpose:** Optimize content for search engines.

**Input:**
```json
{
  "draft": "...",
  "target_keywords": ["..."],
  "existing_articles": ["..."]  // for internal linking
}
```

**Output:**
```json
{
  "optimized_draft": "...",
  "meta": {
    "title": "How to Reduce Player Churn | Adrian Crook",
    "description": "...",
    "keywords": ["..."],
    "slug": "reduce-player-churn-mobile-games"
  },
  "internal_links": [
    {"anchor": "onboarding best practices", "url": "/best-practices-for-mobile-game-onboarding/"}
  ],
  "keyword_density": 0.018,
  "readability_score": 8.2
}
```

**Quality Gate:**
- Keyword density 1-2%
- Readability grade 8-10
- Meta description < 160 chars

---

### 6. Humanizer Agent

**Model:** claude-sonnet-4 (cloud)
**File:** `agents/humanizer.py`

**Purpose:** Make content pass AI detection.

**Input:**
```json
{
  "draft": "...",
  "voice_samples": ["..."],  // existing Adrian articles
  "detection_threshold": 0.2
}
```

**Output:**
```json
{
  "humanized_draft": "...",
  "ai_scores": {
    "gptzero": 0.12,
    "originality": 0.18
  },
  "changes_made": [
    {"original": "...", "revised": "...", "reason": "flagged by GPTZero"}
  ],
  "passed": true
}
```

**Quality Gate:**
- AI detection score < 20%
- Voice consistency with samples
- No robotic transitions

---

### 7. Supervisor Agent

**Model:** claude-opus-4-5 (cloud, minimal usage)
**File:** `agents/supervisor.py`

**Purpose:** Orchestrate pipeline, manage quality gates.

**Responsibilities:**
- Load pipeline configuration
- Execute agents in sequence
- Check quality gates between stages
- Handle errors and retries
- Present final output for human approval
- Manage state/checkpoints

**Input:**
```json
{
  "topic": "...",
  "config": "pipeline.yaml"
}
```

**Output:**
```json
{
  "status": "awaiting_approval",
  "article": { /* final article bundle */ },
  "pipeline_log": [
    {"stage": "research", "status": "passed", "duration_s": 45},
    ...
  ],
  "total_cost": 0.35
}
```

## Inter-Agent Communication

Agents communicate via JSON files in a shared workspace:

```
outputs/
└── article-{timestamp}/
    ├── 1-research.json
    ├── 2-draft.md
    ├── 3-verified.md
    ├── 4-media.json
    ├── 5-seo.md
    ├── 6-humanized.md
    ├── pipeline.log
    └── final/
        ├── article.md
        ├── meta.json
        └── images/
```

## Testing Agents

Each agent has unit tests:

```bash
pytest agents/test_research.py
pytest agents/test_writer.py
# etc.
```

Integration test runs full pipeline on sample topic:

```bash
python scripts/test_pipeline.py --topic "Test Topic"
```
