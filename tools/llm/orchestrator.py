"""
Pipeline Orchestrator for the GOTCHA framework.
Routes tasks through agent chains defined in args/pipelines.yaml
Returns execution trace for Claude to review.
"""

import os
import sys
import warnings
import yaml
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

# Suppress deprecation warnings from google.generativeai
warnings.filterwarnings("ignore", category=FutureWarning, module="google.generativeai")

from dotenv import load_dotenv

# Load .env from project root
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

from base import LLMRequest, LLMResponse
from clients.codex_client import CodexClient
from clients.gemini_client import GeminiClient
from clients.grok_client import GrokClient
from clients.qwen_local import QwenLocalClient


@dataclass
class StageResult:
    """Result from a single pipeline stage."""
    agent: str
    role: str
    instruction: str
    prompt: str
    response: LLMResponse
    success: bool
    error: Optional[str] = None
    duration_ms: int = 0


@dataclass
class PipelineResult:
    """Full result from a pipeline execution."""
    pipeline_name: str
    task: str
    stages: list[StageResult] = field(default_factory=list)
    final_output: str = ""
    success: bool = True
    total_duration_ms: int = 0

    def to_review_format(self) -> str:
        """Format for Claude's review."""
        lines = [
            f"## Pipeline: {self.pipeline_name}",
            f"**Task:** {self.task}",
            f"**Status:** {'✓ Success' if self.success else '✗ Failed'}",
            f"**Duration:** {self.total_duration_ms}ms",
            "",
            "### Stage Results:",
        ]

        for i, stage in enumerate(self.stages, 1):
            status = "✓" if stage.success else "✗"
            lines.extend([
                f"\n**Stage {i}: {stage.agent} ({stage.role})** {status}",
                f"- Instruction: {stage.instruction}",
                f"- Duration: {stage.duration_ms}ms",
            ])
            if stage.error:
                lines.append(f"- Error: {stage.error}")
            else:
                # Truncate long outputs
                output = stage.response.content
                if len(output) > 500:
                    output = output[:500] + "... [truncated]"
                lines.append(f"- Output preview: {output}")

        lines.extend([
            "",
            "### Final Output:",
            self.final_output,
        ])

        return "\n".join(lines)


class Orchestrator:
    """Routes tasks through agent pipelines."""

    def __init__(self, config_dir: Optional[Path] = None):
        self.config_dir = config_dir or Path(__file__).parent.parent.parent / "args"
        self._load_config()
        self._init_clients()

    def _load_config(self):
        """Load configuration from args files."""
        llm_config_path = self.config_dir / "llm_config.yaml"
        pipelines_path = self.config_dir / "pipelines.yaml"

        with open(llm_config_path) as f:
            self.llm_config = yaml.safe_load(f)

        with open(pipelines_path) as f:
            self.pipelines_config = yaml.safe_load(f)

    def _init_clients(self):
        """Initialize available LLM clients."""
        self.clients = {}

        # Try to init each client, mark unavailable if fails
        try:
            self.clients["codex"] = CodexClient(
                model=self.llm_config["models"]["codex"]["model"]
            )
        except Exception as e:
            print(f"Warning: Codex client unavailable: {e}")

        try:
            self.clients["gemini"] = GeminiClient(
                model=self.llm_config["models"]["gemini"]["model"]
            )
        except Exception as e:
            print(f"Warning: Gemini client unavailable: {e}")

        try:
            self.clients["grok"] = GrokClient(
                model=self.llm_config["models"]["grok"]["model"]
            )
        except Exception as e:
            print(f"Warning: Grok client unavailable: {e}")

        try:
            self.clients["qwen"] = QwenLocalClient()
        except Exception as e:
            print(f"Warning: Qwen client unavailable: {e}")

    def list_pipelines(self) -> list[str]:
        """List available pipeline names."""
        return list(self.pipelines_config["pipelines"].keys())

    def get_pipeline_info(self, name: str) -> dict:
        """Get info about a specific pipeline."""
        return self.pipelines_config["pipelines"].get(name, {})

    def health_check(self) -> dict[str, bool]:
        """Check health of all clients."""
        return {
            name: client.health_check()
            for name, client in self.clients.items()
        }

    def run_pipeline(
        self,
        pipeline_name: str,
        task: str,
        context: Optional[str] = None,
    ) -> PipelineResult:
        """Execute a pipeline for the given task."""
        import time

        pipeline = self.pipelines_config["pipelines"].get(pipeline_name)
        if not pipeline:
            raise ValueError(f"Unknown pipeline: {pipeline_name}")

        result = PipelineResult(
            pipeline_name=pipeline_name,
            task=task,
        )

        start_time = time.time()
        previous_output = ""

        for stage_def in pipeline["stages"]:
            agent_name = stage_def["agent"]
            role = stage_def["role"]
            instruction = stage_def["instruction"]

            client = self.clients.get(agent_name)
            if not client:
                stage_result = StageResult(
                    agent=agent_name,
                    role=role,
                    instruction=instruction,
                    prompt="",
                    response=LLMResponse(content="", model=""),
                    success=False,
                    error=f"Client {agent_name} not available",
                )
                result.stages.append(stage_result)
                result.success = False
                continue

            # Build prompt for this stage
            prompt_parts = [f"Task: {task}"]
            if context:
                prompt_parts.append(f"Context: {context}")
            if previous_output:
                prompt_parts.append(f"Previous stage output:\n{previous_output}")
            prompt_parts.append(f"Your role: {role}")
            prompt_parts.append(f"Instruction: {instruction}")

            prompt = "\n\n".join(prompt_parts)

            # Get temperature from config
            temp = self.llm_config["models"].get(agent_name, {}).get("temperature", 0.7)

            stage_start = time.time()
            try:
                response = client.query(LLMRequest(
                    prompt=prompt,
                    temperature=temp,
                ))
                stage_result = StageResult(
                    agent=agent_name,
                    role=role,
                    instruction=instruction,
                    prompt=prompt,
                    response=response,
                    success=True,
                    duration_ms=int((time.time() - stage_start) * 1000),
                )
                previous_output = response.content
            except Exception as e:
                stage_result = StageResult(
                    agent=agent_name,
                    role=role,
                    instruction=instruction,
                    prompt=prompt,
                    response=LLMResponse(content="", model=""),
                    success=False,
                    error=str(e),
                    duration_ms=int((time.time() - stage_start) * 1000),
                )
                result.success = False

            result.stages.append(stage_result)

        result.final_output = previous_output
        result.total_duration_ms = int((time.time() - start_time) * 1000)

        return result

    def query_single(
        self,
        agent: str,
        prompt: str,
        system: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> LLMResponse:
        """Query a single agent directly (no pipeline)."""
        client = self.clients.get(agent)
        if not client:
            raise ValueError(f"Client {agent} not available")

        temp = temperature or self.llm_config["models"].get(agent, {}).get("temperature", 0.7)

        return client.query(LLMRequest(
            prompt=prompt,
            system=system,
            temperature=temp,
        ))


def main():
    """CLI interface for the orchestrator."""
    import argparse
    import json

    parser = argparse.ArgumentParser(description="LLM Pipeline Orchestrator")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Health check
    health_parser = subparsers.add_parser("health", help="Check agent health")

    # List pipelines
    list_parser = subparsers.add_parser("list", help="List available pipelines")

    # Run pipeline
    run_parser = subparsers.add_parser("run", help="Run a pipeline")
    run_parser.add_argument("pipeline", help="Pipeline name")
    run_parser.add_argument("task", help="Task description")
    run_parser.add_argument("--context", "-c", help="Additional context")
    run_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # Query single agent
    query_parser = subparsers.add_parser("query", help="Query single agent")
    query_parser.add_argument("agent", help="Agent name")
    query_parser.add_argument("prompt", help="Prompt")
    query_parser.add_argument("--system", "-s", help="System prompt")
    query_parser.add_argument("--temperature", "-t", type=float)

    args = parser.parse_args()

    orchestrator = Orchestrator()

    if args.command == "health":
        health = orchestrator.health_check()
        for agent, status in health.items():
            symbol = "✓" if status else "✗"
            print(f"{symbol} {agent}")

    elif args.command == "list":
        for name in orchestrator.list_pipelines():
            info = orchestrator.get_pipeline_info(name)
            print(f"- {name}: {info.get('description', '')}")

    elif args.command == "run":
        result = orchestrator.run_pipeline(
            args.pipeline,
            args.task,
            context=args.context,
        )
        if args.json:
            print(json.dumps({
                "pipeline": result.pipeline_name,
                "task": result.task,
                "success": result.success,
                "final_output": result.final_output,
                "duration_ms": result.total_duration_ms,
            }, indent=2))
        else:
            print(result.to_review_format())

    elif args.command == "query":
        response = orchestrator.query_single(
            args.agent,
            args.prompt,
            system=args.system,
            temperature=args.temperature,
        )
        print(response.content)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
