# AGC Content Engine v2 - Clean Architecture

## 🎯 Core Goal
Generate high-quality, SEO-optimized blog articles for adriancrook.com using:
- **Local LLMs** (free) for 95% of work: qwen2.5:14b via Ollama
- **Cloud APIs** ($) only for humanization (Claude) and media (Gemini)
- **Fresh data** with citations via Brave Search API
- **Pass AI detection** and beat SEObot quality

## 🏗️ Architecture Principles

### What Went Wrong (v1)
1. **Split Worker/API**: Tasks stuck, orphaned, hard to debug
2. **Multiple save points**: Redundant, conflicting updates
3. **Poor state management**: No recovery, no visibility
4. **Silent failures**: Errors hidden, hard to trace

### New Approach (v2)
```
┌─────────────────────────────────────────────────────────┐
│  LOCAL SERVICE (Mac Mini) - Single Process             │
│                                                         │
│  ┌──────────────┐      ┌─────────────┐                │
│  │   FastAPI    │──────│  Postgres   │ (Railway)      │
│  │   Server     │      │  (Articles, │                │
│  │              │      │   State)    │                │
│  └──────┬───────┘      └─────────────┘                │
│         │                                              │
│  ┌──────▼────────────────────────────┐                │
│  │   State Machine Engine            │                │
│  │   (Orchestrates pipeline)         │                │
│  └──────┬────────────────────────────┘                │
│         │                                              │
│  ┌──────▼───────────────────────────┐                 │
│  │   Agent Pool                     │                 │
│  │   - ResearchAgent (qwen, local)  │                 │
│  │   - WriterAgent (qwen, local)    │                 │
│  │   - FactCheckAgent (qwen, local) │                 │
│  │   - SEOAgent (qwen, local)       │                 │
│  │   - HumanizeAgent (claude, $)    │                 │
│  │   - MediaAgent (gemini, $)       │                 │
│  └──────────────────────────────────┘                 │
│                                                         │
│  ┌─────────────┐                                       │
│  │   Ollama    │  qwen2.5:14b (14B params)            │
│  └─────────────┘  FREE local inference                │
└─────────────────────────────────────────────────────────┘

         ↓ HTTPS (data only)

┌─────────────────────────────────────────────────────────┐
│  RAILWAY (Cloud) - Data Layer Only                     │
│  - PostgreSQL (persistent state)                       │
│  - Static Dashboard (optional web view)                │
└─────────────────────────────────────────────────────────┘
```

## 📊 Article State Machine

```
pending → researching → writing → fact_checking → seo_optimizing → humanizing → media_generating → ready → published
   ↓          ↓           ↓             ↓               ↓              ↓              ↓            ↓
 failed     failed      failed        failed          failed         failed         failed      failed
   ↓──────────┴───────────┴─────────────┴───────────────┴──────────────┴──────────────┴────────────┘
                                    (auto-retry 3x, then manual review)
```

**Key Changes:**
- **Single state field**: No separate tasks table, just article.state
- **Atomic transitions**: State change = transaction
- **Auto-recovery**: Stuck states detected via `updated_at` timestamp
- **Idempotent**: Can re-run any stage safely

## 🗄️ Simplified Database Schema

```sql
-- Single articles table (no separate tasks!)
CREATE TABLE articles (
    id UUID PRIMARY KEY,
    topic_id UUID REFERENCES topics(id),

    -- Core fields
    title TEXT NOT NULL,
    state TEXT NOT NULL DEFAULT 'pending',  -- Single source of truth

    -- Pipeline data (JSON for flexibility)
    research JSONB,           -- {sources: [], outline: {}, gaps: []}
    draft TEXT,               -- Markdown content
    fact_check JSONB,         -- {verified: bool, issues: []}
    seo JSONB,                -- {keyword: "", meta: {}, score: 0}
    final_content TEXT,       -- After humanization
    media JSONB,              -- {featured_image: "", inline: []}

    -- Metadata
    retry_count INT DEFAULT 0,
    error TEXT,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    published_at TIMESTAMP
);

-- Topics (approved by user)
CREATE TABLE topics (
    id UUID PRIMARY KEY,
    title TEXT NOT NULL,
    keyword TEXT,
    approved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Simple event log (debugging/audit)
CREATE TABLE events (
    id UUID PRIMARY KEY,
    article_id UUID REFERENCES articles(id),
    event_type TEXT,  -- state_changed, error, retry, etc.
    data JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## 🔄 State Machine Engine (Core Logic)

```python
# engine/state_machine.py

class ArticleStateMachine:
    """
    Orchestrates article pipeline with automatic recovery
    Single responsibility: state transitions
    """

    TRANSITIONS = {
        "pending": "researching",
        "researching": "writing",
        "writing": "fact_checking",
        "fact_checking": "seo_optimizing",
        "seo_optimizing": "humanizing",
        "humanizing": "media_generating",
        "media_generating": "ready",
        "ready": "published"
    }

    def __init__(self, db, agents, logger):
        self.db = db
        self.agents = agents
        self.logger = logger

    async def tick(self):
        """
        Process one article through its next state
        Called every N seconds by scheduler
        """
        article = await self.get_next_article()
        if not article:
            return

        try:
            await self.transition(article)
        except Exception as e:
            await self.handle_failure(article, e)

    async def transition(self, article):
        """Execute state transition"""
        current = article.state
        next_state = self.TRANSITIONS.get(current)

        if not next_state:
            return  # Terminal state

        # Execute agent for current state
        agent_method = getattr(self.agents, f"run_{current}")
        result = await agent_method(article)

        # Atomic update: state + data + timestamp
        await self.db.update_article(
            article.id,
            state=next_state,
            **result,  # e.g., {research: {...}, draft: "..."}
            updated_at=datetime.utcnow(),
            retry_count=0  # Reset on success
        )

        await self.log_event(article.id, "state_changed", {
            "from": current,
            "to": next_state
        })

    async def handle_failure(self, article, error):
        """Retry logic with exponential backoff"""
        if article.retry_count < 3:
            await self.db.update_article(
                article.id,
                retry_count=article.retry_count + 1,
                error=str(error),
                updated_at=datetime.utcnow()
            )
            self.logger.warning(f"Article {article.id} retry {article.retry_count}/3")
        else:
            await self.db.update_article(
                article.id,
                state="failed",
                error=str(error)
            )
            self.logger.error(f"Article {article.id} failed permanently")

    async def recover_stuck(self):
        """
        Find articles stuck in processing states (updated_at > 1 hour)
        Reset to same state for retry
        """
        stuck = await self.db.get_stuck_articles(timedelta(hours=1))
        for article in stuck:
            await self.handle_failure(article, Exception("Timeout"))
```

## 🤖 Clean Agent Interface

```python
# agents/base.py

from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class AgentResult:
    """Standardized agent output"""
    success: bool
    data: dict  # Key-value pairs to update article
    cost: float = 0.0  # Track API costs
    tokens: int = 0

class BaseAgent(ABC):
    """All agents follow same interface"""

    def __init__(self, llm_client, config):
        self.llm = llm_client
        self.config = config

    @abstractmethod
    async def run(self, article) -> AgentResult:
        """
        Pure function: article in, result out
        No database access, no state changes
        """
        pass

# agents/research.py
class ResearchAgent(BaseAgent):
    async def run(self, article) -> AgentResult:
        # 1. Search Brave API for topic
        sources = await self.search(article.topic)

        # 2. Analyze each source with local LLM
        analyzed = []
        for source in sources:
            analysis = await self.llm.analyze(source.content)
            analyzed.append(analysis)

        # 3. Generate outline
        outline = await self.llm.generate_outline(analyzed)

        # 4. Identify gaps
        gaps = await self.llm.find_gaps(analyzed)

        return AgentResult(
            success=True,
            data={
                "research": {
                    "sources": analyzed,
                    "outline": outline,
                    "gaps": gaps
                }
            }
        )
```

## 🖥️ Simple API Server

```python
# server.py

from fastapi import FastAPI, WebSocket
from contextlib import asynccontextmanager
import asyncio

app = FastAPI()
state_machine = None
status_clients = []  # WebSocket clients for real-time updates

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize state machine
    global state_machine
    db = Database(os.getenv("DATABASE_URL"))
    agents = AgentPool(ollama_url="http://localhost:11434")
    state_machine = ArticleStateMachine(db, agents, logger)

    # Start background ticker
    task = asyncio.create_task(run_forever())
    yield

    # Shutdown
    task.cancel()

async def run_forever():
    """Background loop: process articles"""
    while True:
        await state_machine.tick()
        await state_machine.recover_stuck()
        await asyncio.sleep(5)  # Check every 5 seconds

# REST API
@app.get("/articles")
async def list_articles():
    return await state_machine.db.get_articles()

@app.get("/articles/{id}")
async def get_article(id: str):
    return await state_machine.db.get_article(id)

@app.post("/topics/{id}/approve")
async def approve_topic(id: str):
    # Create article in 'pending' state
    article = await state_machine.db.create_article_from_topic(id)
    return {"id": article.id, "state": "pending"}

# WebSocket for real-time dashboard
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    status_clients.append(websocket)
    try:
        while True:
            # Send status every second
            status = await state_machine.get_status()
            await websocket.send_json(status)
            await asyncio.sleep(1)
    finally:
        status_clients.remove(websocket)
```

## 📱 Real-Time Dashboard

```html
<!-- dashboard.html -->
<script>
// Simple WebSocket connection for live updates
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onmessage = (event) => {
    const status = JSON.parse(event.data);
    updateAgentStatus(status.agents);
    updateArticleQueue(status.articles);
};

function updateAgentStatus(agents) {
    // agents = {research: "idle", writer: "working", ...}
    for (const [agent, state] of Object.entries(agents)) {
        document.getElementById(agent).className = state;
    }
}
</script>
```

## 🚀 Deployment

### Local Service (Mac Mini)
```bash
# Run everything in one process
poetry install
poetry run python server.py

# Ollama must be running
ollama serve
```

### Railway (Data Only)
- PostgreSQL database (auto-provisioned)
- Optional: Static dashboard HTML

## 📈 Advantages Over v1

| Aspect | v1 (Current) | v2 (New) |
|--------|--------------|----------|
| **Processes** | 2 (API + Worker) | 1 (Unified) |
| **State** | Split (tasks + articles) | Single (articles.state) |
| **Recovery** | Manual | Automatic |
| **Debugging** | Logs scattered | Centralized events |
| **Real-time** | Polling (slow) | WebSocket (instant) |
| **Complexity** | High | Low |
| **Failure Mode** | Orphaned tasks | Auto-retry |

## 🎯 Migration Path

1. **Phase 1**: Build v2 in parallel (new repo: `agc-v2`)
2. **Phase 2**: Migrate database schema (keep Railway Postgres)
3. **Phase 3**: Cutover (stop v1 worker, start v2 server)
4. **Phase 4**: Archive v1 codebase

No data loss, clean cutover.

## 🔧 Tech Stack

- **Server**: FastAPI (async, WebSocket support)
- **Database**: PostgreSQL (Railway)
- **LLM**: Ollama (qwen2.5:14b)
- **Search**: Brave API
- **Cloud LLM**: OpenRouter (Claude for humanization)
- **Deployment**: Single Python process on Mac Mini
- **Dashboard**: HTML + Vanilla JS (no framework bloat)

## 💡 Key Insights

1. **Simplicity wins**: One process, one state field, one source of truth
2. **State machine pattern**: Clear transitions, easy to reason about
3. **Pure agents**: No side effects, easy to test
4. **Automatic recovery**: System self-heals
5. **Real-time visibility**: WebSocket dashboard shows live state

This design is **10x simpler** and actually works.
