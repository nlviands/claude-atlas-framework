#!/usr/bin/env python3
"""
Daily Discord Pull — runs on schedule via Chief.
Exports last 24 hours from Hans's key channels.
No Claude needed — pure Python/API.

Channels pulled:
  - leaps-alerts, leaps-commentary, trades
  - technical-analysis, cash-machine, general-chat

Output: tools/discord/daily/YYYY-MM-DD.json (combined)
"""

import json
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

# Add parent for imports
sys.path.insert(0, str(Path(__file__).resolve().parent))
from export_channel import api_get

TOKEN_FILE = Path(__file__).resolve().parent / ".discord_token"
OUTPUT_DIR = Path(__file__).resolve().parent / "daily"
ANALYSIS_FLAG = Path(__file__).resolve().parent / ".needs_analysis"
STATE_FILE = Path(__file__).resolve().parent / ".pull_state.json"

CHANNELS = {
    "1397990964764610601": "leaps-alerts",
    "1397992080126509066": "leaps-commentary",
    "1255539744193118269": "trades",
    "1252960422961745961": "technical-analysis",
    "1255899141217845248": "cash-machine",
    "1252204874821664771": "general-chat",
}


def get_token():
    """Read token from file."""
    if not TOKEN_FILE.exists():
        print("ERROR: No token file. Save token to tools/discord/.discord_token")
        sys.exit(1)
    return TOKEN_FILE.read_text().strip()


def load_state():
    """Load last-pulled message IDs per channel."""
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def save_state(state):
    """Persist last-pulled message IDs per channel."""
    STATE_FILE.write_text(json.dumps(state, indent=2))


def pull_since(token, channel_id, after_snowflake):
    """Pull messages from a channel after a snowflake ID."""
    all_messages = []
    after = after_snowflake

    while True:
        endpoint = f"/channels/{channel_id}/messages?limit=100&after={after}"
        messages = api_get(endpoint, token)
        if not messages:
            break
        messages.sort(key=lambda m: int(m["id"]))
        all_messages.extend(messages)
        after = messages[-1]["id"]
        time.sleep(1.0)

    return all_messages


def datetime_to_snowflake(dt):
    """Convert a datetime to a Discord snowflake ID."""
    unix_ms = int(dt.timestamp() * 1000)
    return str((unix_ms - 1420070400000) << 22)


def main():
    token = get_token()
    today = datetime.now().strftime("%Y-%m-%d")
    state = load_state()

    # Fallback: if no state for a channel, pull last 25 hours
    fallback_snowflake = datetime_to_snowflake(
        datetime.utcnow() - timedelta(hours=25)
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_DIR / f"{today}.json"

    combined = {}
    total = 0
    new_state = {}

    for channel_id, name in CHANNELS.items():
        # Use last-pulled snowflake if available, otherwise fallback
        after = state.get(channel_id, fallback_snowflake)
        messages = pull_since(token, channel_id, after)
        combined[name] = messages
        total += len(messages)

        # Track the highest message ID we've seen for next pull
        if messages:
            new_state[channel_id] = messages[-1]["id"]
        else:
            # No new messages — keep the previous state
            new_state[channel_id] = after

        print(f"  #{name}: {len(messages)} new messages")
        time.sleep(0.5)

    with open(output_file, "w") as f:
        json.dump(combined, f, indent=2)

    # Save state for next run
    save_state(new_state)

    print(f"\nTotal: {total} new messages saved to {output_file}")

    # Flag for Atlas to analyze
    ANALYSIS_FLAG.write_text(today)

    # Log to ops.log
    try:
        ops_log = Path("/Users/nl/projects/chief_of_staff/logs/ops.log")
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(ops_log, "a") as f:
            f.write(f"[{ts}] [chief] [discord_pull] Pulled {total} new messages from {len(CHANNELS)} channels\n")
    except Exception:
        pass


if __name__ == "__main__":
    main()
