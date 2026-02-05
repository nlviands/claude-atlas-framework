"""
Market Data Aggregator for GOTCHA Framework.
Pulls data from multiple sources and formats for pipeline consumption.

NOTE: This tool is designed to be called by Claude (the orchestrator) who has
access to MCP tools. The formatted output is then injected into pipelines.
"""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class MarketDataBundle:
    """Aggregated market data for a symbol."""
    symbol: str
    timestamp: str

    # Price data
    current_price: Optional[float] = None
    day_open: Optional[float] = None
    day_high: Optional[float] = None
    day_low: Optional[float] = None
    prev_close: Optional[float] = None
    day_change_pct: Optional[float] = None

    # Volume
    volume: Optional[int] = None
    avg_volume: Optional[int] = None

    # Historical context
    week_high: Optional[float] = None
    week_low: Optional[float] = None
    weekly_bars: Optional[str] = None

    # News
    news_headlines: Optional[str] = None

    # Corporate actions
    dividends: Optional[str] = None

    # Options sentiment
    options_summary: Optional[str] = None
    put_call_ratio: Optional[float] = None
    avg_iv: Optional[float] = None

    def to_context_string(self) -> str:
        """Format as context string for pipeline injection."""
        lines = [
            f"=== MARKET DATA FOR {self.symbol} ===",
            f"Data as of: {self.timestamp}",
            "",
            "## CURRENT PRICE",
            f"- Price: ${self.current_price:.2f}" if self.current_price else "- Price: N/A",
            f"- Day Open: ${self.day_open:.2f}" if self.day_open else "",
            f"- Day Range: ${self.day_low:.2f} - ${self.day_high:.2f}" if self.day_low and self.day_high else "",
            f"- Previous Close: ${self.prev_close:.2f}" if self.prev_close else "",
            f"- Day Change: {self.day_change_pct:+.2f}%" if self.day_change_pct else "",
            "",
        ]

        if self.volume:
            lines.extend([
                "## VOLUME",
                f"- Today: {self.volume:,}",
                f"- Average: {self.avg_volume:,}" if self.avg_volume else "",
                "",
            ])

        if self.weekly_bars:
            lines.extend([
                "## PRICE HISTORY (Weekly)",
                self.weekly_bars,
                "",
            ])

        if self.news_headlines:
            lines.extend([
                "## RECENT NEWS",
                self.news_headlines,
                "",
            ])

        if self.dividends:
            lines.extend([
                "## CORPORATE ACTIONS",
                self.dividends,
                "",
            ])

        if self.options_summary:
            lines.extend([
                "## OPTIONS SENTIMENT",
                f"- Average IV: {self.avg_iv:.1f}%" if self.avg_iv else "",
                f"- Put/Call Ratio: {self.put_call_ratio:.2f}" if self.put_call_ratio else "",
                self.options_summary,
                "",
            ])

        return "\n".join(filter(None, lines))


def format_news_for_context(news_data: str) -> str:
    """Format news search results for pipeline context."""
    # Extract key points from news
    lines = ["Key headlines:"]
    # Parse and summarize news_data
    lines.append(news_data[:1000])  # Truncate if needed
    return "\n".join(lines)


def calculate_options_sentiment(options_chain: str) -> dict:
    """Analyze options chain for sentiment signals."""
    # Count puts vs calls, calculate average IV
    lines = options_chain.split("\n")

    puts = 0
    calls = 0
    ivs = []

    for line in lines:
        if "Contract:" in line:
            if "P0" in line:
                puts += 1
            elif "C0" in line:
                calls += 1
        if "IV:" in line and "N/A" not in line:
            try:
                iv_str = line.split("IV:")[1].strip().replace("%", "")
                ivs.append(float(iv_str))
            except:
                pass

    put_call_ratio = puts / calls if calls > 0 else 0
    avg_iv = sum(ivs) / len(ivs) if ivs else 0

    return {
        "put_call_ratio": put_call_ratio,
        "avg_iv": avg_iv,
        "puts": puts,
        "calls": calls,
    }


# Template for Claude to use when gathering data
GATHER_DATA_TEMPLATE = """
To gather comprehensive market data for {symbol}, I will:

1. Get current snapshot (price, volume)
2. Get weekly price history (13 weeks)
3. Search for recent news
4. Get corporate actions (dividends, splits)
5. Get options chain for sentiment

Then format all data into a context bundle for the pipeline.
"""
