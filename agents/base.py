"""
Base Agent class for all content engine agents.
"""

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)


@dataclass
class AgentInput:
    """Input to an agent."""
    data: Dict[str, Any]
    workspace: Path
    config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentOutput:
    """Output from an agent."""
    data: Dict[str, Any]
    success: bool
    errors: List[str] = field(default_factory=list)
    duration_seconds: float = 0.0
    tokens_used: int = 0
    cost_usd: float = 0.0


class BaseAgent(ABC):
    """
    Base class for all agents in the content engine.
    
    Agents can use either local Ollama models or cloud APIs.
    """
    
    def __init__(
        self,
        name: str,
        model: str,
        model_type: str = "ollama",  # "ollama" or "anthropic" or "google"
        ollama_url: str = "http://localhost:11434",
        api_key: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ):
        self.name = name
        self.model = model
        self.model_type = model_type
        self.ollama_url = ollama_url
        self.api_key = api_key
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        logger.info(f"Initialized {name} with model {model} ({model_type})")
    
    @abstractmethod
    def run(self, input: AgentInput) -> AgentOutput:
        """Execute the agent's task. Must be implemented by subclasses."""
        pass
    
    @abstractmethod
    def validate_output(self, output: AgentOutput) -> bool:
        """Check if output meets quality gate. Must be implemented by subclasses."""
        pass
    
    def _call_ollama(self, prompt: str, system: Optional[str] = None) -> str:
        """Call local Ollama model."""
        url = f"{self.ollama_url}/api/generate"
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "num_predict": self.max_tokens,
            }
        }
        
        if system:
            payload["system"] = system
        
        try:
            response = requests.post(url, json=payload, timeout=300)
            response.raise_for_status()
            result = response.json()
            return result.get("response", "")
        except Exception as e:
            logger.error(f"Ollama call failed: {e}")
            raise
    
    def _call_anthropic(self, prompt: str, system: Optional[str] = None) -> str:
        """Call Anthropic Claude API."""
        import anthropic
        
        client = anthropic.Anthropic(api_key=self.api_key)
        
        messages = [{"role": "user", "content": prompt}]
        
        response = client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=system or "",
            messages=messages,
        )
        
        return response.content[0].text
    
    def _call_model(self, prompt: str, system: Optional[str] = None) -> str:
        """Call the configured model (local or cloud)."""
        if self.model_type == "ollama":
            return self._call_ollama(prompt, system)
        elif self.model_type == "anthropic":
            return self._call_anthropic(prompt, system)
        else:
            raise ValueError(f"Unknown model type: {self.model_type}")
    
    def save_output(self, output: AgentOutput, workspace: Path, stage: int) -> Path:
        """Save agent output to workspace."""
        output_file = workspace / f"{stage}-{self.name}.json"
        
        with open(output_file, "w") as f:
            json.dump({
                "agent": self.name,
                "model": self.model,
                "timestamp": datetime.now().isoformat(),
                "success": output.success,
                "errors": output.errors,
                "duration_seconds": output.duration_seconds,
                "tokens_used": output.tokens_used,
                "cost_usd": output.cost_usd,
                "data": output.data,
            }, f, indent=2)
        
        logger.info(f"Saved output to {output_file}")
        return output_file
    
    def load_previous_output(self, workspace: Path, stage: int, agent_name: str) -> Optional[Dict]:
        """Load output from a previous agent stage."""
        output_file = workspace / f"{stage}-{agent_name}.json"
        
        if not output_file.exists():
            return None
        
        with open(output_file, "r") as f:
            return json.load(f)
