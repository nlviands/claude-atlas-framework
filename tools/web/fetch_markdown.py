#!/usr/bin/env python3
"""
fetch_markdown.py — Fetch any URL as clean markdown.

Strategy:
  1. Try Cloudflare Markdown for Agents (Accept: text/markdown header)
  2. Fall back to firecrawl CLI if CF doesn't return markdown

Usage:
  python fetch_markdown.py <url>
  python fetch_markdown.py <url> --output /tmp/output.md
  python fetch_markdown.py <url> --force-firecrawl
"""

import argparse
import subprocess
import sys
import urllib.request


def fetch_cf_markdown(url: str, timeout: int = 15) -> dict | None:
    """Try Cloudflare Markdown for Agents via Accept: text/markdown header."""
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "text/markdown",
            "User-Agent": "Atlas/1.0 (AI assistant)",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            content_type = resp.headers.get("Content-Type", "")
            if "text/markdown" in content_type:
                body = resp.read().decode("utf-8", errors="replace")
                token_count = resp.headers.get("x-markdown-tokens", "unknown")
                return {
                    "source": "cloudflare",
                    "content": body,
                    "tokens": token_count,
                    "content_type": content_type,
                }
    except Exception as e:
        print(f"[CF] Failed: {e}", file=sys.stderr)
    return None


def fetch_firecrawl(url: str) -> dict | None:
    """Fall back to firecrawl CLI."""
    try:
        result = subprocess.run(
            ["firecrawl", "scrape", "--only-main-content", url],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0 and result.stdout.strip():
            return {
                "source": "firecrawl",
                "content": result.stdout,
                "tokens": "unknown",
                "content_type": "text/markdown",
            }
        else:
            print(f"[firecrawl] Error: {result.stderr}", file=sys.stderr)
    except FileNotFoundError:
        print("[firecrawl] Not installed, skipping", file=sys.stderr)
    except Exception as e:
        print(f"[firecrawl] Failed: {e}", file=sys.stderr)
    return None


def fetch_markdown(url: str, force_firecrawl: bool = False) -> dict | None:
    """Fetch URL as markdown. CF first, firecrawl fallback."""
    if not force_firecrawl:
        result = fetch_cf_markdown(url)
        if result:
            return result
        print("[info] CF markdown not available, trying firecrawl...", file=sys.stderr)

    return fetch_firecrawl(url)


def main():
    parser = argparse.ArgumentParser(description="Fetch URL as clean markdown")
    parser.add_argument("url", help="URL to fetch")
    parser.add_argument("--output", "-o", help="Write to file instead of stdout")
    parser.add_argument(
        "--force-firecrawl", action="store_true", help="Skip CF, use firecrawl directly"
    )
    args = parser.parse_args()

    result = fetch_markdown(args.url, force_firecrawl=args.force_firecrawl)

    if not result:
        print("ERROR: Could not fetch markdown from any source", file=sys.stderr)
        sys.exit(1)

    header = f"<!-- Source: {result['source']} | Tokens: {result['tokens']} -->\n\n"
    content = header + result["content"]

    if args.output:
        with open(args.output, "w") as f:
            f.write(content)
        print(f"Saved to {args.output} ({len(content)} chars, source: {result['source']})")
    else:
        print(content)


if __name__ == "__main__":
    main()
