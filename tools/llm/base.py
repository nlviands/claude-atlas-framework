"""
Base interface for all LLM clients.
All clients implement this protocol for consistent orchestration.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class LLMResponse:
    """Standard response format from any LLM client."""
    content: str
    model: str
    usage: Optional[dict] = None
    raw_response: Optional[dict] = None


@dataclass
class LLMRequest:
    """Standard request format for any LLM client."""
    prompt: str
    system: Optional[str] = None
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    json_mode: bool = False


class BaseLLMClient(ABC):
    """Abstract base class for LLM clients."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Client identifier (e.g., 'codex', 'gemini', 'grok', 'qwen')."""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Check if the service is available."""
        pass

    @abstractmethod
    def query(self, request: LLMRequest) -> LLMResponse:
        """Send a query and return the response."""
        pass

    def query_simple(self, prompt: str, **kwargs) -> str:
        """Convenience method - just prompt in, text out."""
        request = LLMRequest(prompt=prompt, **kwargs)
        response = self.query(request)
        return response.content
