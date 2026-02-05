"""
Gemini (Google AI) client for the GOTCHA framework.
Uses Google Generative AI API - configure model in args/llm_config.yaml
"""

import os
import sys
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
import google.generativeai as genai

# Load .env from project root
env_path = Path(__file__).parent.parent.parent.parent / ".env"
load_dotenv(env_path)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base import BaseLLMClient, LLMRequest, LLMResponse


class GeminiClient(BaseLLMClient):
    """Google Gemini API client for reasoning and synthesis."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gemini-2.0-flash",
    ):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment")

        genai.configure(api_key=self.api_key)
        self._model_name = model
        self._model = genai.GenerativeModel(model)

    @property
    def name(self) -> str:
        return "gemini"

    def health_check(self) -> bool:
        """Check if Gemini API is reachable."""
        try:
            # List models to verify API access
            list(genai.list_models())
            return True
        except Exception:
            return False

    def query(self, request: LLMRequest) -> LLMResponse:
        """Send a query to Gemini."""
        # Build the prompt with system instruction if provided
        if request.system:
            full_prompt = f"{request.system}\n\n{request.prompt}"
        else:
            full_prompt = request.prompt

        generation_config = {
            "temperature": request.temperature,
        }

        if request.max_tokens:
            generation_config["max_output_tokens"] = request.max_tokens

        if request.json_mode:
            generation_config["response_mime_type"] = "application/json"

        response = self._model.generate_content(
            full_prompt,
            generation_config=generation_config,
        )

        # Extract usage if available
        usage = None
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            usage = {
                "prompt_tokens": response.usage_metadata.prompt_token_count,
                "completion_tokens": response.usage_metadata.candidates_token_count,
                "total_tokens": response.usage_metadata.total_token_count,
            }

        return LLMResponse(
            content=response.text,
            model=self._model_name,
            usage=usage,
            raw_response=None,  # Gemini response objects aren't easily serializable
        )


def main():
    """CLI interface for testing."""
    import argparse

    parser = argparse.ArgumentParser(description="Query Google Gemini")
    parser.add_argument("prompt", nargs="?", help="The prompt to send")
    parser.add_argument("--system", "-s", help="System prompt")
    parser.add_argument("--model", "-m", default="gemini-2.0-flash", help="Model to use")
    parser.add_argument("--temperature", "-t", type=float, default=0.7)
    parser.add_argument("--json", action="store_true", help="Request JSON output")
    parser.add_argument("--stdin", action="store_true", help="Read prompt from stdin")
    parser.add_argument("--health", action="store_true", help="Check API health")

    args = parser.parse_args()

    client = GeminiClient(model=args.model)

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
