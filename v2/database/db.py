"""
Database connection and operations
"""

import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from sqlalchemy import create_engine, select, update, and_
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker

from .models import Base, Article, Topic, Event, ArticleState


class Database:
    """Async database operations"""

    def __init__(self, database_url: str):
        # Convert postgres:// to postgresql:// for SQLAlchemy
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)

        self.engine = create_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine, expire_on_commit=False)

    def init_db(self):
        """Create all tables"""
        Base.metadata.create_all(self.engine)

    @asynccontextmanager
    async def session(self):
        """Context manager for database sessions"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    # Article operations

    def get_next_article(self) -> Optional[Article]:
        """
        Get next article to process
        Returns article in earliest pipeline state with lowest retry count
        """
        with self.SessionLocal() as session:
            # Order by state priority, then retry count, then created time
            state_order = [
                ArticleState.PENDING,
                ArticleState.RESEARCHING,
                ArticleState.WRITING,
                ArticleState.ENRICHING,
                ArticleState.REVISING,
                ArticleState.FACT_CHECKING,
                ArticleState.SEO_OPTIMIZING,
                ArticleState.HUMANIZING,
                ArticleState.MEDIA_GENERATING
            ]

            for state in state_order:
                article = session.query(Article).filter(
                    Article.state == state
                ).order_by(
                    Article.retry_count.asc(),
                    Article.created_at.asc()
                ).first()

                if article:
                    return article

            return None

    def get_stuck_articles(self, timeout: timedelta) -> List[Article]:
        """Find articles stuck in processing (updated_at > timeout)"""
        with self.SessionLocal() as session:
            cutoff = datetime.utcnow() - timeout
            processing_states = [
                ArticleState.RESEARCHING,
                ArticleState.WRITING,
                ArticleState.FACT_CHECKING,
                ArticleState.SEO_OPTIMIZING,
                ArticleState.HUMANIZING,
                ArticleState.MEDIA_GENERATING
            ]

            return session.query(Article).filter(
                Article.state.in_(processing_states),
                Article.updated_at < cutoff
            ).all()

    def update_article(self, article_id: str, **kwargs) -> bool:
        """
        Update article fields atomically
        Always updates updated_at timestamp
        """
        with self.SessionLocal() as session:
            kwargs['updated_at'] = datetime.utcnow()

            result = session.query(Article).filter(
                Article.id == article_id
            ).update(kwargs)

            session.commit()
            return result > 0

    def create_article_from_topic(self, topic_id: str) -> Optional[Article]:
        """Create new article from approved topic"""
        with self.SessionLocal() as session:
            topic = session.query(Topic).filter(Topic.id == topic_id).first()
            if not topic or not topic.approved:
                return None

            article = Article(
                topic_id=topic_id,
                title=topic.title,
                state=ArticleState.RESEARCHING  # Start directly in RESEARCHING
            )
            session.add(article)
            session.commit()
            session.refresh(article)
            return article

    def get_article(self, article_id: str) -> Optional[Article]:
        """Get article by ID"""
        with self.SessionLocal() as session:
            return session.query(Article).filter(Article.id == article_id).first()

    def get_articles(self, state: Optional[str] = None, limit: int = 50) -> List[Article]:
        """Get articles, optionally filtered by state"""
        with self.SessionLocal() as session:
            query = session.query(Article)
            if state:
                query = query.filter(Article.state == state)
            return query.order_by(Article.created_at.desc()).limit(limit).all()

    # Event logging

    def log_event(self, article_id: str, event_type: str, data: Dict[str, Any] = None):
        """Log event for debugging/audit"""
        with self.SessionLocal() as session:
            event = Event(
                article_id=article_id,
                event_type=event_type,
                data=data or {}
            )
            session.add(event)
            session.commit()

    # Topic operations

    def get_topics(self, approved: Optional[bool] = None) -> List[Topic]:
        """Get topics, optionally filtered by approval status"""
        with self.SessionLocal() as session:
            query = session.query(Topic)
            if approved is not None:
                query = query.filter(Topic.approved == approved)
            return query.order_by(Topic.created_at.desc()).all()

    def approve_topic(self, topic_id: str) -> bool:
        """Approve a topic"""
        with self.SessionLocal() as session:
            result = session.query(Topic).filter(
                Topic.id == topic_id
            ).update({"approved": True})
            session.commit()
            return result > 0
