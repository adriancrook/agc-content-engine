"""
Database models for AGC v2 - Simplified schema
Single source of truth: articles.state
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from sqlalchemy import Column, String, Text, Integer, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
import uuid

Base = declarative_base()


class ArticleState(str, Enum):
    """Article pipeline states"""
    PENDING = "pending"
    RESEARCHING = "researching"
    WRITING = "writing"
    FACT_CHECKING = "fact_checking"
    SEO_OPTIMIZING = "seo_optimizing"
    HUMANIZING = "humanizing"
    MEDIA_GENERATING = "media_generating"
    READY = "ready"
    PUBLISHED = "published"
    FAILED = "failed"


class Topic(Base):
    """Topics for article generation"""
    __tablename__ = "topics_v2"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(Text, nullable=False)
    keyword = Column(String)
    approved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Article(Base):
    """
    Single table for entire pipeline
    State field is source of truth
    """
    __tablename__ = "articles_v2"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    topic_id = Column(String, ForeignKey("topics_v2.id"))

    # Core fields
    title = Column(Text, nullable=False)
    state = Column(String, nullable=False, default=ArticleState.PENDING)

    # Pipeline data (JSON for flexibility)
    research = Column(JSON)           # {sources: [], outline: {}, gaps: []}
    draft = Column(Text)               # Markdown content from writer
    fact_check = Column(JSON)          # {verified: bool, issues: []}
    seo = Column(JSON)                 # {keyword: "", meta: {}, score: 0}
    final_content = Column(Text)       # After humanization
    media = Column(JSON)               # {featured_image: "", inline: []}

    # Metadata
    retry_count = Column(Integer, default=0)
    error = Column(Text)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at = Column(DateTime)


class Event(Base):
    """Event log for debugging and audit"""
    __tablename__ = "events_v2"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    article_id = Column(String, ForeignKey("articles_v2.id"))
    event_type = Column(String, nullable=False)  # state_changed, error, retry
    data = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
