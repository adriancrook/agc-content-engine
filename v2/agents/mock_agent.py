"""
Mock agent for testing the state machine
Simulates processing without actual LLM calls
"""

import asyncio
from .base import BaseAgent, AgentResult


class MockAgent(BaseAgent):
    """Mock agent that simulates work"""

    async def run(self, article) -> AgentResult:
        """Simulate processing with delay"""
        # Simulate some work
        await asyncio.sleep(1)

        # Return mock data based on state
        state = article.state
        data = {}

        if state == "pending":
            data = {"research": {"mock": "research_data"}}
        elif state == "researching":
            data = {"draft": f"# {article.title}\n\nMock draft content..."}
        elif state == "writing":
            data = {"fact_check": {"verified": True}}
        elif state == "fact_checking":
            data = {"seo": {"keyword": "test", "score": 85}}
        elif state == "seo_optimizing":
            data = {"final_content": f"# {article.title}\n\nHumanized content..."}
        elif state == "humanizing":
            data = {"media": {"featured_image": "mock.jpg"}}

        return AgentResult(
            success=True,
            data=data,
            cost=0.0,
            tokens=100
        )
