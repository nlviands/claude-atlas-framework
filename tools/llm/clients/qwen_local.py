"""
Qwen (local MLX) client for the GOTCHA framework.
Connects to local MLX server - start with: ./start_server.sh in MLX-LLM project
"""

import os
import re
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


class QwenLocalClient(BaseLLMClient):
    """Local Qwen client via MLX server - fast, free, good for drafts."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: str = "default_model",  # MLX server uses this literal name
    ):
        self.base_url = base_url or os.getenv("QWEN_BASE_URL", "http://localhost:8080/v1")
        self.model = model
        self._client = OpenAI(
            api_key="not-needed",  # Local server doesn't require auth
            base_url=self.base_url,
        )

    @property
    def name(self) -> str:
        return "qwen"

    def health_check(self) -> bool:
        """Check if local MLX server is running."""
        try:
            self._client.models.list()
            return True
        except Exception:
            return False

    def _clean_response(self, text: str) -> str:
        """Remove MLX/Qwen output artifacts."""
        # Remove special tokens that Qwen sometimes includes
        text = text.replace("<|im_end|>", "")
        text = text.replace("<|im_start|>", "")
        text = text.strip()
        return text

    def _extract_json(self, text: str) -> Optional[str]:
        """Extract JSON from response if present."""
        json_match = re.search(r'\{[\s\S]*\}', text)
        if json_match:
            return json_match.group()
        return None

    def query(self, request: LLMRequest) -> LLMResponse:
        """Send a query to local Qwen."""
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

        # Note: Local MLX server may not support response_format
        # For JSON mode, we rely on prompt engineering

        response = self._client.chat.completions.create(**kwargs)

        content = self._clean_response(response.choices[0].message.content)

        # Extract JSON if requested
        if request.json_mode:
            extracted = self._extract_json(content)
            if extracted:
                content = extracted

        # Usage may not be available from local server
        usage = None
        if response.usage:
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }

        return LLMResponse(
            content=content,
            model=self.model,
            usage=usage,
            raw_response=response.model_dump() if hasattr(response, "model_dump") else None,
        )


def main():
    """CLI interface for testing."""
    import argparse

    parser = argparse.ArgumentParser(description="Query local Qwen via MLX")
    parser.add_argument("prompt", nargs="?", help="The prompt to send")
    parser.add_argument("--system", "-s", help="System prompt")
    parser.add_argument("--temperature", "-t", type=float, default=0.7)
    parser.add_argument("--json", action="store_true", help="Extract JSON from output")
    parser.add_argument("--stdin", action="store_true", help="Read prompt from stdin")
    parser.add_argument("--health", action="store_true", help="Check server health")

    args = parser.parse_args()

    client = QwenLocalClient()

    if args.health:
        healthy = client.health_check()
        if healthy:
            print("MLX server is running")
        else:
            print("MLX server not reachable - start it with ./start_server.sh")
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
