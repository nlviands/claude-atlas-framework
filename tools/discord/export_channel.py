#!/usr/bin/env python3
"""
Discord Channel Exporter

Exports full message history from a Discord channel using a user token.
No bot required — uses the user's own authentication.

Usage:
    python export_channel.py --token YOUR_TOKEN --channel CHANNEL_ID [--output output.json]
    python export_channel.py --token YOUR_TOKEN --list-guilds
    python export_channel.py --token YOUR_TOKEN --list-channels GUILD_ID
"""

import argparse
import json
import time
import sys
from datetime import datetime
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError

API_BASE = "https://discord.com/api/v9"
RATE_LIMIT_PAUSE = 1.0  # seconds between requests


def api_get(endpoint, token):
    """Make an authenticated GET request to Discord API."""
    url = f"{API_BASE}{endpoint}"
    req = Request(url)
    req.add_header("Authorization", token)
    req.add_header("Content-Type", "application/json")
    req.add_header("User-Agent", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
    try:
        with urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except HTTPError as e:
        if e.code == 429:
            retry_after = json.loads(e.read().decode()).get("retry_after", 5)
            print(f"  Rate limited, waiting {retry_after}s...")
            time.sleep(retry_after)
            return api_get(endpoint, token)
        raise


def list_guilds(token):
    """List all servers the user is in."""
    guilds = api_get("/users/@me/guilds", token)
    print(f"\nServers ({len(guilds)}):")
    for g in guilds:
        print(f"  {g['id']}  {g['name']}")
    return guilds


def list_channels(token, guild_id):
    """List all text channels in a server."""
    channels = api_get(f"/guilds/{guild_id}/channels", token)
    text_channels = [c for c in channels if c.get("type") in (0, 5)]  # text + announcements
    text_channels.sort(key=lambda c: (c.get("parent_id") or "", c.get("position", 0)))

    print(f"\nText channels ({len(text_channels)}):")
    current_category = None
    for c in text_channels:
        cat_id = c.get("parent_id")
        if cat_id != current_category:
            current_category = cat_id
            cat_name = next((ch["name"] for ch in channels if ch["id"] == cat_id), "uncategorized") if cat_id else "uncategorized"
            print(f"\n  [{cat_name}]")
        print(f"    {c['id']}  #{c['name']}")
    return text_channels


def export_channel(token, channel_id, output_path=None):
    """Export all messages from a channel."""
    all_messages = []
    before = None
    batch = 0

    print(f"\nExporting channel {channel_id}...")

    while True:
        endpoint = f"/channels/{channel_id}/messages?limit=100"
        if before:
            endpoint += f"&before={before}"

        messages = api_get(endpoint, token)
        if not messages:
            break

        all_messages.extend(messages)
        before = messages[-1]["id"]
        batch += 1
        print(f"  Batch {batch}: {len(all_messages)} messages so far...")

        time.sleep(RATE_LIMIT_PAUSE)

    # Reverse to chronological order
    all_messages.reverse()

    # Save
    if not output_path:
        output_path = Path(f"discord_export_{channel_id}_{datetime.now().strftime('%Y%m%d')}.json")

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(all_messages, f, indent=2)

    print(f"\nExported {len(all_messages)} messages to {output_path}")
    return all_messages


def main():
    parser = argparse.ArgumentParser(description="Export Discord channel history")
    parser.add_argument("--token", required=True, help="Discord user token")
    parser.add_argument("--channel", help="Channel ID to export")
    parser.add_argument("--output", help="Output file path (default: discord_export_<id>_<date>.json)")
    parser.add_argument("--list-guilds", action="store_true", help="List all servers")
    parser.add_argument("--list-channels", metavar="GUILD_ID", help="List channels in a server")

    args = parser.parse_args()

    if args.list_guilds:
        list_guilds(args.token)
    elif args.list_channels:
        list_channels(args.token, args.list_channels)
    elif args.channel:
        export_channel(args.token, args.channel, args.output)
    else:
        # Default: list guilds to help user find what they need
        list_guilds(args.token)


if __name__ == "__main__":
    main()
