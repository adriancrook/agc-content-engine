"""
Database module - PostgreSQL via SQLAlchemy
Works with Railway's internal Postgres or external DATABASE_URL
"""

import os
import json
from datetime import datetime
from typing import Optional, List, Dict
from contextlib import contextmanager

from sqlalchemy import create_engine, Column, String, Text, Integer, Float, DateTime, JSON, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///agc.db")

# Debug: print what we got
print(f"DATABASE_URL: {DATABASE_URL[:50]}..." if len(DATABASE_URL) > 50 else f"DATABASE_URL: {DATABASE_URL}")

# Handle Railway's postgres:// vs postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Validate URL format before creating engine
if not DATABASE_URL.startswith(("postgresql://", "sqlite:///")):
    print(f"WARNING: Invalid DATABASE_URL format, falling back to SQLite")
    DATABASE_URL = "sqlite:///agc.db"

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


def generate_uuid():
    return str(uuid.uuid4())


class Topic(Base):
    __tablename__ = "topics"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    title = Column(Text, nullable=False)
    keyword = Column(String)
    status = Column(String, default="pending")  # pending, approved, declined, processing, completed
    priority = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    approved_at = Column(DateTime)


class Article(Base):
    __tablename__ = "articles"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    topic_id = Column(String, ForeignKey("topics.id"))
    title = Column(Text)
    status = Column(String, default="draft")  # draft, researching, writing, fact_checking, seo, humanizing, review, approved, published, failed
    stage = Column(String, default="research")
    research_data = Column(JSON)
    draft_content = Column(Text)
    final_content = Column(Text)
    seo_meta = Column(JSON)
    media = Column(JSON)
    ai_score = Column(Float)
    word_count = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at = Column(DateTime)


class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    type = Column(String, nullable=False)  # generate_topics, research, write, fact_check, seo, humanize, media
    payload = Column(JSON, default={})
    status = Column(String, default="pending")  # pending, processing, completed, failed
    result = Column(JSON)
    article_id = Column(String, ForeignKey("articles.id"))
    worker_id = Column(String)  # Which Mac Mini picked it up
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    error = Column(Text)


class Setting(Base):
    __tablename__ = "settings"
    
    key = Column(String, primary_key=True)
    value = Column(JSON)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


def init_db():
    """Create all tables"""
    Base.metadata.create_all(engine)
    
    # Insert default settings
    with get_session() as session:
        defaults = [
            ("topic_generation", {"max_pending": 20, "auto_generate": True, "focus_areas": ["mobile game monetization", "freemium game design", "game economy modeling"]}),
            ("pipeline", {"auto_process_approved": True, "require_human_review": True})
        ]
        for key, value in defaults:
            if not session.query(Setting).filter_by(key=key).first():
                session.add(Setting(key=key, value=value))
        session.commit()


@contextmanager
def get_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


# Topic functions
def get_topics(status: Optional[str] = None, limit: int = 50) -> List[Dict]:
    with get_session() as session:
        query = session.query(Topic)
        if status:
            query = query.filter(Topic.status == status)
        query = query.order_by(Topic.created_at.desc()).limit(limit)
        return [{"id": t.id, "title": t.title, "keyword": t.keyword, "status": t.status, 
                 "priority": t.priority, "created_at": t.created_at.isoformat() if t.created_at else None} 
                for t in query.all()]


def create_topic(title: str, keyword: str = None) -> Dict:
    with get_session() as session:
        topic = Topic(title=title, keyword=keyword or title.lower().replace(" ", "-"))
        session.add(topic)
        session.commit()
        return {"id": topic.id, "title": topic.title, "status": topic.status}


def update_topic(topic_id: str, updates: Dict) -> Optional[Dict]:
    with get_session() as session:
        topic = session.query(Topic).filter_by(id=topic_id).first()
        if topic:
            for key, value in updates.items():
                if hasattr(topic, key):
                    setattr(topic, key, value)
            session.commit()
            return {"id": topic.id, "title": topic.title, "status": topic.status}
        return None


def approve_topic(topic_id: str) -> Optional[Dict]:
    return update_topic(topic_id, {"status": "approved", "approved_at": datetime.utcnow()})


def decline_topic(topic_id: str) -> Optional[Dict]:
    return update_topic(topic_id, {"status": "declined"})


def delete_topic(topic_id: str) -> bool:
    with get_session() as session:
        topic = session.query(Topic).filter_by(id=topic_id).first()
        if topic:
            session.delete(topic)
            session.commit()
            return True
        return False


def count_topics_by_status() -> Dict[str, int]:
    with get_session() as session:
        topics = session.query(Topic).all()
        counts = {"pending": 0, "approved": 0, "declined": 0, "processing": 0, "completed": 0}
        for t in topics:
            counts[t.status] = counts.get(t.status, 0) + 1
        return counts


# Task functions
def create_task(task_type: str, payload: Dict, article_id: str = None) -> Dict:
    with get_session() as session:
        task = Task(type=task_type, payload=payload, article_id=article_id)
        session.add(task)
        session.commit()
        return {"id": task.id, "type": task.type, "status": task.status}


def get_pending_tasks(limit: int = 10) -> List[Dict]:
    with get_session() as session:
        tasks = session.query(Task).filter_by(status="pending").order_by(Task.created_at).limit(limit).all()
        return [{"id": t.id, "type": t.type, "payload": t.payload, "article_id": t.article_id} for t in tasks]


def claim_task(task_id: str, worker_id: str) -> Optional[Dict]:
    """Atomically claim a task for a worker"""
    with get_session() as session:
        task = session.query(Task).filter_by(id=task_id, status="pending").first()
        if task:
            task.status = "processing"
            task.worker_id = worker_id
            task.started_at = datetime.utcnow()
            session.commit()
            return {"id": task.id, "type": task.type, "payload": task.payload}
        return None


def complete_task(task_id: str, result: Dict) -> Optional[Dict]:
    with get_session() as session:
        task = session.query(Task).filter_by(id=task_id).first()
        if task:
            task.status = "completed"
            task.result = result
            task.completed_at = datetime.utcnow()
            session.commit()
            return {"id": task.id, "status": "completed"}
        return None


def fail_task(task_id: str, error: str) -> Optional[Dict]:
    with get_session() as session:
        task = session.query(Task).filter_by(id=task_id).first()
        if task:
            task.status = "failed"
            task.error = error
            task.completed_at = datetime.utcnow()
            session.commit()
            return {"id": task.id, "status": "failed"}
        return None


# Article functions  
def create_article(topic_id: str, title: str) -> Dict:
    with get_session() as session:
        article = Article(topic_id=topic_id, title=title)
        session.add(article)
        session.commit()
        return {"id": article.id, "title": article.title, "status": article.status}


def get_articles(status: Optional[str] = None, limit: int = 20) -> List[Dict]:
    with get_session() as session:
        query = session.query(Article)
        if status:
            query = query.filter(Article.status == status)
        query = query.order_by(Article.created_at.desc()).limit(limit)
        return [{"id": a.id, "title": a.title, "status": a.status, "stage": a.stage,
                 "word_count": a.word_count, "ai_score": a.ai_score} for a in query.all()]


def update_article(article_id: str, updates: Dict) -> Optional[Dict]:
    with get_session() as session:
        article = session.query(Article).filter_by(id=article_id).first()
        if article:
            for key, value in updates.items():
                if hasattr(article, key):
                    setattr(article, key, value)
            session.commit()
            return {"id": article.id, "status": article.status}
        return None


# Settings
def get_setting(key: str):
    with get_session() as session:
        setting = session.query(Setting).filter_by(key=key).first()
        return setting.value if setting else None


def set_setting(key: str, value: Dict):
    with get_session() as session:
        setting = session.query(Setting).filter_by(key=key).first()
        if setting:
            setting.value = value
        else:
            session.add(Setting(key=key, value=value))
        session.commit()
