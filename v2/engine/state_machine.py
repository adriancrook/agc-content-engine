"""
State Machine Engine - Orchestrates article pipeline
Core logic: state transitions with automatic recovery
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional

from database.db import Database
from database.models import ArticleState, Article
from agents.base import BaseAgent, AgentResult


class StateMachineEngine:
    """
    Orchestrates article pipeline
    Single responsibility: manage state transitions
    """

    # State transition map
    TRANSITIONS = {
        ArticleState.PENDING: ArticleState.RESEARCHING,
        ArticleState.RESEARCHING: ArticleState.WRITING,
        ArticleState.WRITING: ArticleState.ENRICHING,
        ArticleState.ENRICHING: ArticleState.REVISING,
        ArticleState.REVISING: ArticleState.FACT_CHECKING,
        ArticleState.FACT_CHECKING: ArticleState.SEO_OPTIMIZING,
        ArticleState.SEO_OPTIMIZING: ArticleState.HUMANIZING,
        ArticleState.HUMANIZING: ArticleState.INTERNAL_LINKING,
        ArticleState.INTERNAL_LINKING: ArticleState.MEDIA_GENERATING,
        ArticleState.MEDIA_GENERATING: ArticleState.WORDPRESS_FORMATTING,
        ArticleState.WORDPRESS_FORMATTING: ArticleState.READY,
        ArticleState.READY: ArticleState.PUBLISHED,
    }

    # Max retries before permanent failure
    MAX_RETRIES = 3

    # Timeout for stuck articles
    STUCK_TIMEOUT = timedelta(hours=1)

    def __init__(self, db: Database, agents: Dict[str, BaseAgent], logger: logging.Logger):
        self.db = db
        self.agents = agents
        self.logger = logger
        self.running = False

    async def start(self, interval: int = 5):
        """
        Start the state machine loop
        Processes articles every `interval` seconds
        """
        self.running = True
        self.logger.info("State machine started")

        while self.running:
            try:
                # Process one article
                await self.tick()

                # Recover stuck articles
                await self.recover_stuck()

                # Wait before next iteration
                await asyncio.sleep(interval)

            except Exception as e:
                self.logger.error(f"State machine error: {e}")
                await asyncio.sleep(interval)

    async def stop(self):
        """Stop the state machine loop"""
        self.running = False
        self.logger.info("State machine stopped")

    async def tick(self):
        """
        Process one article through its next state
        Called repeatedly by the main loop
        """
        article = self.db.get_next_article()
        if not article:
            return  # No articles to process

        try:
            await self.transition(article)
        except Exception as e:
            self.logger.error(f"Transition error for article {article.id}: {e}")
            await self.handle_failure(article, e)

    async def transition(self, article: Article):
        """
        Execute state transition for article
        1. Run agent for current state
        2. Update article with result
        3. Move to next state
        """
        current_state = article.state
        next_state = self.TRANSITIONS.get(current_state)

        if not next_state:
            # Terminal state (ready, published, failed)
            return

        self.logger.info(f"Article {article.id[:8]}: {current_state} → {next_state}")

        # Get agent for current state
        agent = self.agents.get(current_state)
        if not agent:
            raise ValueError(f"No agent configured for state: {current_state}")

        # Run agent (pure function)
        result = await agent.run(article)

        if not result.success:
            raise Exception(result.error or "Agent failed without error message")

        # Atomic update: state + data + timestamp + reset retry
        update_data = {
            "state": next_state,
            "retry_count": 0,
            "error": None,
            **result.data
        }

        success = self.db.update_article(article.id, **update_data)
        if not success:
            raise Exception("Failed to update article in database")

        # Log event
        self.db.log_event(article.id, "state_changed", {
            "from": current_state,
            "to": next_state,
            "cost": result.cost,
            "tokens": result.tokens
        })

        self.logger.info(f"✓ Article {article.id[:8]} transitioned to {next_state}")

    async def handle_failure(self, article: Article, error: Exception):
        """
        Handle agent failure with retry logic
        Retry up to MAX_RETRIES, then mark as failed
        """
        if article.retry_count < self.MAX_RETRIES:
            # Retry: increment counter, log error
            self.db.update_article(
                article.id,
                retry_count=article.retry_count + 1,
                error=str(error)
            )

            self.db.log_event(article.id, "retry", {
                "attempt": article.retry_count + 1,
                "error": str(error)
            })

            self.logger.warning(
                f"Article {article.id[:8]} retry {article.retry_count + 1}/{self.MAX_RETRIES}: {error}"
            )

        else:
            # Permanent failure
            self.db.update_article(
                article.id,
                state=ArticleState.FAILED,
                error=str(error)
            )

            self.db.log_event(article.id, "failed", {
                "error": str(error),
                "final_state": article.state
            })

            self.logger.error(f"✗ Article {article.id[:8]} failed permanently: {error}")

    async def recover_stuck(self):
        """
        Find and recover stuck articles
        Articles stuck in processing states (updated_at > STUCK_TIMEOUT)
        """
        stuck_articles = self.db.get_stuck_articles(self.STUCK_TIMEOUT)

        for article in stuck_articles:
            self.logger.warning(
                f"Recovering stuck article {article.id[:8]} in state {article.state}"
            )

            # Treat as timeout failure
            await self.handle_failure(article, Exception("Timeout: no progress"))

    def get_status(self) -> Dict:
        """
        Get current status for dashboard
        Returns agent states and article counts
        """
        articles = self.db.get_articles()

        state_counts = {}
        for state in ArticleState:
            state_counts[state.value] = sum(1 for a in articles if a.state == state.value)

        # Determine which agents are "working"
        agent_states = {}
        for state, _ in self.TRANSITIONS.items():
            count = state_counts.get(state.value, 0)
            agent_states[state.value] = "working" if count > 0 else "idle"

        return {
            "agents": agent_states,
            "articles": state_counts,
            "total": len(articles)
        }
