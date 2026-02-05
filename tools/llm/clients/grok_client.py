"""
Grok (xAI) client for the GOTCHA framework.
Uses xAI's OpenAI-compatible API - configure model in args/llm_config.yaml
"""

import os
import sys
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from openai import OpenAI

# Load .env from project root
env_path = Path(__file__).parent.parent.parent.parent / ".env"
load_dotenv(env_path)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base import BaseLLMClient, LLMRequest, LLMResponse


class GrokClient(BaseLLMClient):
    """xAI Grok client for social sentiment and creative tasks."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "grok-3",
    ):
        self.api_key = api_key or os.getenv("GROK_API_KEY")
        if not self.api_key:
            raise ValueError("GROK_API_KEY not found in environment")

        self.model = model
        self._client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.x.ai/v1",
        )

    @property
    def name(self) -> str:
        return "grok"

    def health_check(self) -> bool:
        """Check if xAI API is reachable."""
        try:
            self._client.models.list()
            return True
        except Exception:
            return False

    def query(self, request: LLMRequest) -> LLMResponse:
        """Send a query to Grok."""
        messages = []

        if request.system:
            messages.append({"role": "system", "content": request.system})

        messages.append({"role": "user", "content": request.prompt})

        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": request.temperature,
        }

        if request.max_tokens:
            kwargs["max_tokens"] = request.max_tokens

        if request.json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        response = self._client.chat.completions.create(**kwargs)

        return LLMResponse(
            content=response.choices[0].message.content,
            model=response.model,
            usage={
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            },
            raw_response=response.model_dump(),
        )


def main():
    """CLI interface for testing."""
    import argparse

    parser = argparse.ArgumentParser(description="Query xAI Grok")
    parser.add_argument("prompt", nargs="?", help="The prompt to send")
    parser.add_argument("--system", "-s", help="System prompt")
    parser.add_argument("--model", "-m", default="grok-3", help="Model to use")
    parser.add_argument("--temperature", "-t", type=float, default=0.7)
    parser.add_argument("--json", action="store_true", help="Request JSON output")
    parser.add_argument("--stdin", action="store_true", help="Read prompt from stdin")
    parser.add_argument("--health", action="store_true", help="Check API health")

    args = parser.parse_args()

    client = GrokClient(model=args.model)

    if args.health:
        healthy = client.health_check()
        print(f"API healthy: {healthy}")
        return

    prompt = sys.stdin.read().strip() if args.stdin else args.prompt

    if not prompt:
        parser.print_help()
        return

    response = client.query(LLMRequest(
        prompt=prompt,
        system=args.system,
        temperature=args.temperature,
        json_mode=args.json,
    ))

    print(response.content)


if __name__ == "__main__":
    main()
