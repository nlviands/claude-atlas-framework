#!/usr/bin/env python3
"""
Conversation Logger for Claude Code Hooks

Captures user prompts and assistant responses to daily transcript files.
Triggered automatically via Claude Code hooks (UserPromptSubmit, Stop).

Usage (called by hooks, not directly):
    echo '{"hook_event_name":"UserPromptSubmit","prompt":"hello"}' | python3 conversation_logger.py
    echo '{"hook_event_name":"Stop","transcript_path":"/path/to/transcript.jsonl"}' | python3 conversation_logger.py
"""

import json
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

# Transcript output directory
TRANSCRIPT_DIR = Path(__file__).resolve().parent.parent.parent / "memory" / "transcripts"

# Slack poll tracking
SLACK_POLL_FILE = Path(__file__).resolve().parent / ".last_slack_poll"
SLACK_POLL_INTERVAL_MINUTES = 30


def get_transcript_path():
    """Get today's transcript file path."""
    today = datetime.now().strftime("%Y-%m-%d")
    return TRANSCRIPT_DIR / f"{today}.md"


def init_transcript(filepath):
    """Initialize a new transcript file if it doesn't exist."""
    if not filepath.exists():
        TRANSCRIPT_DIR.mkdir(parents=True, exist_ok=True)
        today = datetime.now().strftime("%Y-%m-%d")
        filepath.write_text(f"# Transcript: {today}\n\n---\n\n")


def log_user_prompt(prompt):
    """Append a user message to today's transcript."""
    filepath = get_transcript_path()
    init_transcript(filepath)

    timestamp = datetime.now().strftime("%H:%M")

    entry = f"## User ({timestamp})\n\n{prompt}\n\n---\n\n"

    with open(filepath, "a") as f:
        f.write(entry)


def log_assistant_response(transcript_path):
    """Extract the last assistant response from Claude's transcript and log it."""
    filepath = get_transcript_path()
    init_transcript(filepath)

    if not transcript_path or not Path(transcript_path).exists():
        return

    # Claude Code transcript is JSONL - read last lines to find assistant message
    response_parts = []
    try:
        with open(transcript_path, "r") as f:
            lines = f.readlines()

        # Walk backwards through JSONL to find the last assistant turn
        for line in reversed(lines):
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            # Look for assistant message type
            if entry.get("type") == "assistant":
                message = entry.get("message", {})
                content = message.get("content", [])
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        response_parts.append(block.get("text", ""))
                break

    except Exception:
        return

    if not response_parts:
        return

    response_text = "\n".join(response_parts)
    timestamp = datetime.now().strftime("%H:%M")

    entry = f"## Claude ({timestamp})\n\n{response_text}\n\n---\n\n"

    with open(filepath, "a") as f:
        f.write(entry)


LAST_PROMPT_FILE = Path(__file__).resolve().parent / ".last_prompt"


def check_slack_poll_due():
    """Check if Slack inbox poll is overdue and print reminder if so.

    Suppressed during active sessions — if user sent a message < 30 min ago,
    they're here and don't need Slack checked.
    """
    try:
        # Track prompt timestamps to detect active sessions
        now = datetime.now()
        if LAST_PROMPT_FILE.exists():
            last_prompt = datetime.fromisoformat(LAST_PROMPT_FILE.read_text().strip())
            if (now - last_prompt) < timedelta(minutes=30):
                # Active session — user is here, skip Slack check
                LAST_PROMPT_FILE.write_text(now.isoformat())
                return
        # Update last prompt time (first prompt of session or after long gap)
        LAST_PROMPT_FILE.write_text(now.isoformat())

        if SLACK_POLL_FILE.exists():
            last_poll = datetime.fromisoformat(SLACK_POLL_FILE.read_text().strip())
            elapsed = now - last_poll
            if elapsed < timedelta(minutes=SLACK_POLL_INTERVAL_MINUTES):
                return  # Not due yet
        # Either no file (never polled) or overdue
        minutes_ago = "never"
        if SLACK_POLL_FILE.exists():
            minutes_ago = f"{int(elapsed.total_seconds() / 60)}m ago"
        print(f"SLACK_POLL_DUE: Last poll: {minutes_ago}. Run mcp__slack__conversations_history on #sb-inbox now.")
    except Exception:
        pass  # Don't break the hook over this


DISCORD_ANALYSIS_FLAG = Path(__file__).resolve().parent.parent / "discord" / ".needs_analysis"
DISCORD_ANALYSIS_DONE = Path(__file__).resolve().parent / ".last_discord_analysis"


def check_discord_analysis():
    """Check if there's a fresh Discord pull that needs analysis."""
    try:
        if not DISCORD_ANALYSIS_FLAG.exists():
            return
        pull_date = DISCORD_ANALYSIS_FLAG.read_text().strip()
        # Check if we already analyzed this date
        if DISCORD_ANALYSIS_DONE.exists():
            last_done = DISCORD_ANALYSIS_DONE.read_text().strip()
            if last_done >= pull_date:
                return  # Already analyzed
        print(f"DISCORD_ANALYSIS_DUE: Fresh pull from {pull_date} ready. Analyze tools/discord/daily/{pull_date}.json and deliver digest.")
    except Exception:
        pass


OPS_LOG_FILE = Path("/Users/nl/projects/chief_of_staff/logs/ops.log")
OPS_ERROR_ACK_FILE = Path(__file__).resolve().parent / ".last_ops_error_check"


def check_ops_errors():
    """Check ops.log for recent errors and surface them."""
    try:
        if not OPS_LOG_FILE.exists():
            return

        # Get the time we last checked
        last_check = datetime.min
        if OPS_ERROR_ACK_FILE.exists():
            last_check = datetime.fromisoformat(OPS_ERROR_ACK_FILE.read_text().strip())

        # Read ops.log for errors since last check
        errors = []
        with open(OPS_LOG_FILE) as f:
            for line in f:
                if "[error]" not in line.lower():
                    continue
                # Parse timestamp from line: [2026-02-14 14:18:36] [source] [error] msg
                try:
                    ts_str = line.split("]")[0].lstrip("[")
                    ts = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
                    if ts > last_check:
                        errors.append(line.strip())
                except (ValueError, IndexError):
                    continue

        if errors:
            # Only show last 5 to avoid flooding
            recent = errors[-5:]
            print(f"OPS_ERRORS ({len(errors)} new): " + " | ".join(recent))

        # Update ack timestamp
        OPS_ERROR_ACK_FILE.parent.mkdir(parents=True, exist_ok=True)
        OPS_ERROR_ACK_FILE.write_text(datetime.now().isoformat())

    except Exception:
        pass


def mark_slack_polled():
    """Update the last poll timestamp. Call this after a successful Slack poll."""
    try:
        SLACK_POLL_FILE.parent.mkdir(parents=True, exist_ok=True)
        SLACK_POLL_FILE.write_text(datetime.now().isoformat())
        ops_log("atlas", "slack_poll", "Polled #sb-inbox")
    except Exception:
        pass


def ops_log(source, category, message):
    """Write to the shared Atlas/Chief operations log."""
    try:
        log_file = Path("/Users/nl/projects/chief_of_staff/logs/ops.log")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"[{timestamp}] [{source}] [{category}] {message}\n"
        log_file.parent.mkdir(exist_ok=True)
        with open(log_file, "a") as f:
            f.write(entry)
    except Exception:
        pass


def main():
    """Read hook input from stdin and route to appropriate handler."""
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            sys.exit(0)

        data = json.loads(raw)
    except (json.JSONDecodeError, Exception):
        sys.exit(0)

    event = data.get("hook_event_name", "")

    if event == "UserPromptSubmit":
        prompt = data.get("prompt", "")
        if prompt:
            log_user_prompt(prompt)
        # Check if Slack poll is overdue
        check_slack_poll_due()
        # Check if Discord pull needs analysis
        check_discord_analysis()
        # Check ops.log for errors to surface
        check_ops_errors()

    elif event == "Stop":
        # Check for stop_hook_active to prevent infinite loops
        if data.get("stop_hook_active", False):
            sys.exit(0)
        transcript_path = data.get("transcript_path", "")
        if transcript_path:
            log_assistant_response(transcript_path)

    sys.exit(0)


if __name__ == "__main__":
    main()
