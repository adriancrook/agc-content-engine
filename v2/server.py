"""
FastAPI server for AGC v2
Single process: state machine + API + WebSocket
"""

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from typing import List

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

# Load .env file
load_dotenv()

from database.db import Database
from database.models import Article, Topic, ArticleState
from engine.state_machine import StateMachineEngine
from agents.mock_agent import MockAgent
from agents.research import ResearchAgent
from agents.writer import WriterAgent
from agents.data_enrichment import DataEnrichmentAgent
from agents.fact_checker import FactCheckerAgent
from agents.seo import SEOAgent
from agents.humanizer import HumanizerAgent
from agents.media import MediaAgent

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global state
state_machine: StateMachineEngine = None
state_machine_task = None
ws_clients = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown logic"""
    global state_machine, state_machine_task

    # Startup
    logger.info("🚀 AGC v2 Server starting...")

    # Initialize database
    database_url = os.getenv("DATABASE_URL", "sqlite:///agc_v2.db")
    db = Database(database_url)
    db.init_db()
    logger.info(f"✓ Database connected: {database_url[:50]}...")

    # Initialize agents
    brave_api_key = os.getenv("BRAVE_API_KEY")
    openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
    google_api_key = os.getenv("GOOGLE_API_KEY")
    use_real_agents = os.getenv("USE_REAL_AGENTS", "false").lower() == "true"

    if use_real_agents and brave_api_key and openrouter_api_key:
        # Real agents configuration (requires Brave + OpenRouter)
        logger.info("Initializing REAL agents...")

        # Core agents (Brave for research, Claude for writing, enrichment, revision)
        agents = {
            ArticleState.RESEARCHING: ResearchAgent({"brave_api_key": brave_api_key}),
            ArticleState.WRITING: WriterAgent({"openrouter_api_key": openrouter_api_key, "pass_type": "draft"}),
            ArticleState.ENRICHING: DataEnrichmentAgent({"brave_api_key": brave_api_key, "openrouter_api_key": openrouter_api_key}),
            ArticleState.REVISING: WriterAgent({"openrouter_api_key": openrouter_api_key, "pass_type": "revision"}),
            ArticleState.FACT_CHECKING: FactCheckerAgent(),
            ArticleState.SEO_OPTIMIZING: SEOAgent(),
        }

        # Paid agents (optional)
        if openrouter_api_key:
            agents[ArticleState.SEO_OPTIMIZING] = HumanizerAgent({"openrouter_api_key": openrouter_api_key})
            logger.info("  + HumanizeAgent (Claude via OpenRouter)")
        else:
            agents[ArticleState.SEO_OPTIMIZING] = MockAgent()
            logger.info("  - HumanizeAgent (no OpenRouter key)")

        if google_api_key:
            agents[ArticleState.HUMANIZING] = MediaAgent({"google_api_key": google_api_key})
            logger.info("  + MediaAgent (Gemini)")
        else:
            agents[ArticleState.HUMANIZING] = MockAgent()
            logger.info("  - MediaAgent (no Google key)")

        agents[ArticleState.MEDIA_GENERATING] = MockAgent()

        # Count paid agents: Writer (Claude) + Humanizer (Claude) + Media (Gemini if available)
        paid_count = 2  # Writer + Humanizer
        if google_api_key:
            paid_count += 1
        logger.info(f"✓ Agents ready: Research (Brave) + Writer (Claude) + Fact/SEO (Ollama) + Humanizer (Claude) + Media ({'Gemini' if google_api_key else 'Mock'})")
    else:
        # Mock agents for testing
        agents = {
            ArticleState.RESEARCHING: MockAgent(),
            ArticleState.WRITING: MockAgent(),
            ArticleState.ENRICHING: MockAgent(),
            ArticleState.REVISING: MockAgent(),
            ArticleState.FACT_CHECKING: MockAgent(),
            ArticleState.SEO_OPTIMIZING: MockAgent(),
            ArticleState.HUMANIZING: MockAgent(),
            ArticleState.MEDIA_GENERATING: MockAgent(),
        }
        logger.info("✓ Mock agents initialized (set USE_REAL_AGENTS=true for real LLMs)")

    # Initialize state machine
    state_machine = StateMachineEngine(db, agents, logger)

    # Start state machine loop in background
    state_machine_task = asyncio.create_task(state_machine.start(interval=5))
    logger.info("✓ State machine started (5s interval)")

    logger.info("✅ Server ready!")

    yield

    # Shutdown
    logger.info("Shutting down...")
    await state_machine.stop()
    if state_machine_task:
        state_machine_task.cancel()


app = FastAPI(title="AGC v2", lifespan=lifespan)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# Pydantic models for API
class TopicCreate(BaseModel):
    title: str
    keyword: str = None


class ArticleResponse(BaseModel):
    id: str
    title: str
    state: str
    retry_count: int
    created_at: str

    class Config:
        from_attributes = True


# Web UI Endpoints

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Web dashboard"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/article/{article_id}", response_class=HTMLResponse)
async def view_article_page(request: Request, article_id: str):
    """Article detail page"""
    article = state_machine.db.get_article(article_id)
    if not article:
        return HTMLResponse(content="<h1>Article not found</h1>", status_code=404)

    return templates.TemplateResponse("article.html", {
        "request": request,
        "article": article
    })


# REST API Endpoints

@app.get("/api")
async def root():
    return {"status": "ok", "version": "2.0"}


@app.get("/status")
async def get_status():
    """Get current system status"""
    return state_machine.get_status()


@app.get("/articles", response_model=List[ArticleResponse])
async def list_articles(state: str = None):
    """List all articles, optionally filtered by state"""
    articles = state_machine.db.get_articles(state=state, limit=100)
    return [ArticleResponse(
        id=a.id,
        title=a.title,
        state=a.state,
        retry_count=a.retry_count,
        created_at=a.created_at.isoformat()
    ) for a in articles]


@app.get("/articles/{article_id}")
async def get_article(article_id: str):
    """Get full article details"""
    article = state_machine.db.get_article(article_id)
    if not article:
        return JSONResponse(status_code=404, content={"error": "Not found"})

    return {
        "id": article.id,
        "title": article.title,
        "state": article.state,
        "research": article.research,
        "draft": article.draft,
        "enrichment": article.enrichment,  # Added for DataEnrichment
        "revised_draft": article.revised_draft,  # Added for Writer Pass 2
        "fact_check": article.fact_check,
        "seo": article.seo,
        "final_content": article.final_content,
        "media": article.media,
        "retry_count": article.retry_count,
        "error": article.error,
        "created_at": article.created_at.isoformat(),
        "updated_at": article.updated_at.isoformat()
    }


@app.get("/topics")
async def list_topics(approved: bool = None):
    """List topics"""
    topics = state_machine.db.get_topics(approved=approved)
    return [{"id": t.id, "title": t.title, "keyword": t.keyword, "approved": t.approved} for t in topics]


@app.post("/topics")
async def create_topic(topic: TopicCreate):
    """Create a new topic"""
    from database.models import Topic
    with state_machine.db.SessionLocal() as session:
        new_topic = Topic(title=topic.title, keyword=topic.keyword)
        session.add(new_topic)
        session.commit()
        session.refresh(new_topic)
        return {"id": new_topic.id, "title": new_topic.title}


@app.post("/topics/{topic_id}/approve")
async def approve_topic(topic_id: str):
    """Approve topic and create article"""
    success = state_machine.db.approve_topic(topic_id)
    if not success:
        return JSONResponse(status_code=404, content={"error": "Topic not found"})

    article = state_machine.db.create_article_from_topic(topic_id)
    if not article:
        return JSONResponse(status_code=400, content={"error": "Failed to create article"})

    return {"article_id": article.id, "state": article.state}


# WebSocket for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Real-time status updates"""
    await websocket.accept()
    ws_clients.append(websocket)

    try:
        while True:
            # Send status every second
            status = state_machine.get_status()
            await websocket.send_json(status)
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        ws_clients.remove(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        if websocket in ws_clients:
            ws_clients.remove(websocket)


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
