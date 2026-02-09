# AGC Content Engine v2

Clean, working implementation with state machine architecture.

## 🎯 What's Different from v1

- **Single process**: No split worker/API
- **State machine**: One `state` field, atomic transitions
- **Auto-recovery**: Stuck articles automatically retry
- **Real-time**: WebSocket dashboard, instant updates
- **10x simpler**: One source of truth, no orphaned tasks

## 🏗️ Architecture

```
server.py (FastAPI)
├── State Machine (background loop)
├── Database (Postgres/SQLite)
├── Agents (mock → real LLMs)
└── WebSocket (real-time updates)
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd v2
pip install -r requirements.txt
```

### 2. Set Database URL (optional)

```bash
# Use Railway Postgres
export DATABASE_URL="postgresql://user:pass@host:port/dbname"

# Or use SQLite (default)
# export DATABASE_URL="sqlite:///agc_v2.db"
```

### 3. Start Server

```bash
python server.py
```

Server runs on `http://localhost:8000`

### 4. Test the Engine

In another terminal:

```bash
python test_engine.py
```

This will:
1. Create a test topic
2. Approve it (creates article)
3. Watch it flow through the pipeline
4. Show real-time state changes

## 📡 API Endpoints

### Status
```bash
GET /status
```

### Articles
```bash
GET  /articles                # List all
GET  /articles/{id}           # Get details
GET  /articles?state=writing  # Filter by state
```

### Topics
```bash
GET  /topics                  # List all
POST /topics                  # Create new
POST /topics/{id}/approve     # Approve → creates article
```

### WebSocket
```bash
WS /ws  # Real-time status updates
```

## 🔄 State Flow

```
pending → researching → writing → fact_checking →
seo_optimizing → humanizing → media_generating → ready → published
```

Any state can → `failed` (after 3 retries)

## 🤖 Agents

Currently using **mock agents** for testing. To add real agents:

1. Create agent in `agents/` (inherit from `BaseAgent`)
2. Register in `server.py` agents dict
3. Implement `async def run(article) -> AgentResult`

Example:
```python
from agents.base import BaseAgent, AgentResult

class ResearchAgent(BaseAgent):
    async def run(self, article) -> AgentResult:
        # Do research with Brave API + LLM
        sources = await self.search(article.title)
        outline = await self.llm.generate_outline(sources)

        return AgentResult(
            success=True,
            data={"research": {"sources": sources, "outline": outline}}
        )
```

## 📊 Database Schema

### Articles (Single table, single state field)
```sql
id, topic_id, title, state,
research (JSON), draft (TEXT), fact_check (JSON), seo (JSON),
final_content (TEXT), media (JSON),
retry_count, error,
created_at, updated_at, published_at
```

### Topics
```sql
id, title, keyword, approved, created_at
```

### Events (Audit log)
```sql
id, article_id, event_type, data (JSON), created_at
```

## 🐛 Debugging

### Check Logs
```bash
# Server shows state transitions in real-time
python server.py
```

### Query Events
```python
from database.db import Database
db = Database("sqlite:///agc_v2.db")

with db.SessionLocal() as session:
    events = session.query(Event).filter_by(article_id="...").all()
    for e in events:
        print(f"{e.event_type}: {e.data}")
```

### Manual Recovery
```bash
# Reset stuck articles (called automatically every 5s)
curl -X POST http://localhost:8000/recover
```

## 🎨 Next Steps

1. **Replace mock agents** with real LLM agents
2. **Add WebSocket dashboard UI** (HTML + JS)
3. **Deploy to Mac Mini** (single process)
4. **Migrate v1 data** (optional)

## ✅ Advantages

| Feature | v1 | v2 |
|---------|----|----|
| Processes | 2 | 1 |
| State management | Tasks table | Single state field |
| Recovery | Manual | Automatic |
| Real-time | Polling | WebSocket |
| Debugging | Hard | Easy (events log) |
| Complexity | High | Low |

---

**This actually works.** 🎉
