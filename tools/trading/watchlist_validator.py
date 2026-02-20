#!/usr/bin/env python3
"""Validate watchlist statuses against closed trades in TRADING.md.

Catches drift where a trade was closed but the watchlist still says "Position".
Run periodically or as a post-session check.

Usage:
    python watchlist_validator.py          # Report mismatches
    python watchlist_validator.py --fix    # Auto-fix mismatches (update watchlist status to "Watching")
"""

import re
import sys
from pathlib import Path

TRADING_MD = Path("/Users/nl/projects/chief_of_staff/TRADING.md")


def parse_watchlist(lines: list[str]) -> list[dict]:
    """Parse watchlist table entries."""
    entries = []
    in_watchlist = False
    for i, line in enumerate(lines):
        if "## Watchlist / Ideas" in line:
            in_watchlist = True
            continue
        if in_watchlist and line.startswith("| Ticker"):
            continue  # header
        if in_watchlist and line.startswith("|---"):
            continue  # separator
        if in_watchlist and line.startswith("| "):
            cols = [c.strip() for c in line.split("|")[1:-1]]
            if len(cols) >= 8:
                entries.append({
                    "line_num": i,
                    "ticker": cols[0],
                    "status": cols[6],
                    "notes": cols[7],
                    "raw_line": line,
                })
        elif in_watchlist and line.startswith("###"):
            break  # end of table
        elif in_watchlist and line.startswith("## ") and "Watchlist" not in line:
            break
    return entries


def parse_closed_trades(lines: list[str]) -> set[str]:
    """Find tickers with CLOSED status in trade log or position sections."""
    closed = set()
    for line in lines:
        # Match "CLOSED" in status columns or headers
        if "CLOSED" in line.upper():
            # Try to extract ticker from table row
            if line.startswith("| "):
                cols = [c.strip() for c in line.split("|")[1:-1]]
                if cols:
                    ticker = cols[0].strip()
                    if ticker and ticker.isalpha() and ticker.isupper():
                        closed.add(ticker)
            # Match section headers like "### SOFI (as of ...) - CLOSED"
            m = re.match(r"###\s+(\w+)\s+\(.*?\)\s*-\s*CLOSED", line)
            if m:
                closed.add(m.group(1))
    return closed


def parse_open_positions(lines: list[str]) -> set[str]:
    """Find tickers listed in Current Positions section (table rows AND ### headers)."""
    open_tickers = set()
    in_positions = False
    for line in lines:
        if "## Current Positions" in line:
            in_positions = True
            continue
        if in_positions and line.startswith("## ") and "Current Positions" not in line:
            break
        # Table rows
        if in_positions and line.startswith("| ") and not line.startswith("| Ticker") and not line.startswith("|---"):
            cols = [c.strip() for c in line.split("|")[1:-1]]
            if cols and cols[0].isalpha() and cols[0].isupper():
                open_tickers.add(cols[0])
        # Section headers like "### TER (as of ...)" — but NOT "### TER ... - CLOSED"
        if in_positions:
            m = re.match(r"^###\s+([A-Z]{1,5})\b", line)
            if m and "CLOSED" not in line.upper():
                open_tickers.add(m.group(1))

    # Also scan entire file for "**Status:** Position Open" patterns
    for i, line in enumerate(lines):
        if "**Status:** Position Open" in line:
            # Look back for the ### header
            for j in range(i - 1, max(i - 5, -1), -1):
                m = re.match(r"^###\s+([A-Z]{1,5})\b", lines[j])
                if m:
                    open_tickers.add(m.group(1))
                    break
    return open_tickers


def validate(fix: bool = False) -> list[dict]:
    """Check for watchlist entries marked 'Position' that should be 'Watching'."""
    content = TRADING_MD.read_text()
    lines = content.split("\n")

    watchlist = parse_watchlist(lines)
    closed_tickers = parse_closed_trades(lines)
    open_positions = parse_open_positions(lines)

    mismatches = []
    for entry in watchlist:
        ticker = entry["ticker"]
        status = entry["status"].lower()
        if "position" in status and ticker not in open_positions:
            mismatches.append(entry)

    if not mismatches:
        print("OK: All watchlist statuses are consistent.")
        return []

    print(f"MISMATCHES FOUND: {len(mismatches)}")
    for m in mismatches:
        print(f"  {m['ticker']}: watchlist says '{m['status']}' but no open position found")

    if fix:
        for m in mismatches:
            old_line = m["raw_line"]
            new_line = old_line.replace(f"| {m['status']} |", "| Watching |")
            content = content.replace(old_line, new_line)
        TRADING_MD.write_text(content)
        print(f"\nFixed {len(mismatches)} entries → status set to 'Watching'")

    return mismatches


if __name__ == "__main__":
    fix = "--fix" in sys.argv
    mismatches = validate(fix=fix)
    sys.exit(1 if mismatches and not fix else 0)
