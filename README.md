# AGC Content Engine

Automated SEO content generation system for adriancrook.com using local LLMs and agent swarms.

**Goal:** Beat SEObot on quality, currency, and multi-modal richness.

## Quality Targets

1. **Currency** — No stale data. Real-time web search, date filtering (<12 months)
2. **Citations** — Every fact verified and linked to primary sources
3. **Multi-modal** — YouTube videos, custom AI images, data tables, infographics
4. **Human** — Pass AI detection, match Adrian's voice

## Architecture

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for full system design.

```
┌─────────────────────────────────────────────────────────┐
│                    SUPERVISOR AGENT                      │
│              (Opus - orchestration + QA)                 │
└─────────────────────┬───────────────────────────────────┘
                      │
    ┌────────┬────────┼────────┬────────┬────────┐
    ▼        ▼        ▼        ▼        ▼        ▼
┌────────┐┌───────┐┌──────┐┌───────┐┌──────┐┌──────────┐
│RESEARCH││WRITER ││ FACT ││ MEDIA ││ SEO  ││HUMANIZER │
│ (local)││(local)││CHECK ││(cloud)││(local)││ (cloud)  │
└────────┘└───────┘└──────┘└───────┘└──────┘└──────────┘
```

## Tech Stack

### Local Models (32GB Mac Mini M4)
- **Qwen 2.5 14B** — Research, SEO optimization
- **Llama 3.2 11B** — Writing drafts
- **DeepSeek-R1 14B** — Reasoning, fact verification

### Cloud APIs (used sparingly)
- **Gemini 3 Pro Image** — Header image generation
- **Sonnet** — Humanization pass
- **Opus** — Supervisor/QA only
- **Brave/Grok** — Web search

### Infrastructure
- **Ollama** — Local model serving
- **Python** — Agent orchestration
- **WordPress REST API** — Publishing

## Quick Start

```bash
# 1. Install Ollama
brew install ollama
brew services start ollama

# 2. Pull required model
ollama pull qwen2.5:14b

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Set up API keys (for cloud agents)
export ANTHROPIC_API_KEY=xxx
export BRAVE_API_KEY=xxx

# 5. Run the pipeline
python pipeline.py "Your Topic Here" --keywords "keyword1" "keyword2"
```

## Usage

```bash
# Basic usage
python pipeline.py "Best Free-to-Play Mobile Games 2025"

# With keywords and SEO target
python pipeline.py "Mobile Game Monetization Guide" \
    --keywords "gacha" "battle pass" "IAP" \
    --primary-keyword "mobile game monetization"

# With custom config
python pipeline.py "Topic" --config .config/custom.json --output-dir ./my-articles
```

## Directory Structure

```
agc-content-engine/
├── README.md
├── docs/
│   ├── ARCHITECTURE.md    # System design
│   ├── AGENTS.md          # Agent specifications
│   └── WORKFLOW.md        # Pipeline steps
├── agents/
│   ├── research.py        # Research agent
│   ├── writer.py          # Writer agent
│   ├── fact_checker.py    # Fact checking agent
│   ├── seo.py             # SEO optimization agent
│   ├── humanizer.py       # AI detection bypass
│   ├── media.py           # Image/video curation
│   └── supervisor.py      # Orchestration
├── scripts/
│   ├── run_pipeline.py    # Main entry point
│   ├── setup_models.sh    # Model installation
│   └── publish.py         # WordPress publishing
├── templates/
│   ├── article.md         # Article template
│   └── outline.md         # Outline template
├── outputs/
│   └── [generated articles]
└── .config/
    ├── models.yaml        # Model configurations
    └── wordpress.yaml     # Publishing config
```

## Roadmap

- [x] Phase 0: System design & architecture docs
- [x] Phase 1: Core agent framework (all 7 agents implemented)
- [ ] Phase 2: First test run - generate real article
- [ ] Phase 3: Quality tuning - AI detection, SEO scores
- [ ] Phase 4: WordPress integration & approval workflow
- [ ] Phase 5: Batch processing & scheduling

## License

Private — Adrian Crook & Associates
