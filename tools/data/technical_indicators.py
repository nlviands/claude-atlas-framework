"""
Technical Indicators Calculator for GOTCHA Framework.
Calculates RSI, MACD, Moving Averages, Bollinger Bands from price data.
"""

from dataclasses import dataclass
from typing import Optional
import re


@dataclass
class TechnicalIndicators:
    """Technical analysis indicators for a symbol."""
    symbol: str
    current_price: float

    # Moving Averages
    sma_10: Optional[float] = None
    sma_20: Optional[float] = None
    sma_50: Optional[float] = None
    ema_12: Optional[float] = None
    ema_26: Optional[float] = None

    # RSI
    rsi_14: Optional[float] = None

    # MACD
    macd_line: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_histogram: Optional[float] = None

    # Bollinger Bands
    bb_upper: Optional[float] = None
    bb_middle: Optional[float] = None
    bb_lower: Optional[float] = None

    # Volume
    volume_sma_20: Optional[float] = None
    current_volume: Optional[float] = None
    volume_ratio: Optional[float] = None

    # Support/Resistance
    recent_high: Optional[float] = None
    recent_low: Optional[float] = None

    def get_signals(self) -> dict:
        """Generate trading signals from indicators."""
        signals = {}

        # RSI signals
        if self.rsi_14:
            if self.rsi_14 < 30:
                signals["rsi"] = "OVERSOLD (Bullish)"
            elif self.rsi_14 > 70:
                signals["rsi"] = "OVERBOUGHT (Bearish)"
            else:
                signals["rsi"] = "NEUTRAL"

        # Price vs Moving Averages
        if self.sma_20 and self.current_price:
            if self.current_price > self.sma_20:
                signals["trend_short"] = "ABOVE 20-SMA (Bullish)"
            else:
                signals["trend_short"] = "BELOW 20-SMA (Bearish)"

        if self.sma_50 and self.current_price:
            if self.current_price > self.sma_50:
                signals["trend_medium"] = "ABOVE 50-SMA (Bullish)"
            else:
                signals["trend_medium"] = "BELOW 50-SMA (Bearish)"

        # MACD signals
        if self.macd_histogram:
            if self.macd_histogram > 0:
                signals["macd"] = "BULLISH (Above signal)"
            else:
                signals["macd"] = "BEARISH (Below signal)"

        # Bollinger Band signals
        if self.bb_lower and self.bb_upper and self.current_price:
            if self.current_price < self.bb_lower:
                signals["bollinger"] = "BELOW LOWER BAND (Oversold)"
            elif self.current_price > self.bb_upper:
                signals["bollinger"] = "ABOVE UPPER BAND (Overbought)"
            else:
                signals["bollinger"] = "WITHIN BANDS (Normal)"

        # Volume signals
        if self.volume_ratio:
            if self.volume_ratio > 1.5:
                signals["volume"] = f"HIGH VOLUME ({self.volume_ratio:.1f}x avg)"
            elif self.volume_ratio < 0.5:
                signals["volume"] = f"LOW VOLUME ({self.volume_ratio:.1f}x avg)"
            else:
                signals["volume"] = f"NORMAL VOLUME ({self.volume_ratio:.1f}x avg)"

        return signals

    def to_context_string(self) -> str:
        """Format as context string for pipeline injection."""
        signals = self.get_signals()

        lines = [
            f"## TECHNICAL INDICATORS FOR {self.symbol}",
            f"Current Price: ${self.current_price:.2f}",
            "",
            "### Moving Averages",
            f"- 10-day SMA: ${self.sma_10:.2f}" if self.sma_10 else "",
            f"- 20-day SMA: ${self.sma_20:.2f}" if self.sma_20 else "",
            f"- 50-day SMA: ${self.sma_50:.2f} (limited data)" if self.sma_50 else "",
            "",
            "### RSI (14-period)",
            f"- RSI: {self.rsi_14:.1f}" if self.rsi_14 else "",
            f"- Signal: {signals.get('rsi', 'N/A')}",
            "",
            "### MACD (12, 26, 9)",
            f"- MACD Line: {self.macd_line:.3f}" if self.macd_line else "",
            f"- Signal Line: {self.macd_signal:.3f}" if self.macd_signal else "",
            f"- Histogram: {self.macd_histogram:.3f}" if self.macd_histogram else "",
            f"- Signal: {signals.get('macd', 'N/A')}",
            "",
            "### Bollinger Bands (20, 2)",
            f"- Upper: ${self.bb_upper:.2f}" if self.bb_upper else "",
            f"- Middle: ${self.bb_middle:.2f}" if self.bb_middle else "",
            f"- Lower: ${self.bb_lower:.2f}" if self.bb_lower else "",
            f"- Signal: {signals.get('bollinger', 'N/A')}",
            "",
            "### Volume Analysis",
            f"- Current Volume: {self.current_volume:,.0f}" if self.current_volume else "",
            f"- 20-day Avg: {self.volume_sma_20:,.0f}" if self.volume_sma_20 else "",
            f"- Signal: {signals.get('volume', 'N/A')}",
            "",
            "### Support/Resistance (40-day)",
            f"- Recent High: ${self.recent_high:.2f}" if self.recent_high else "",
            f"- Recent Low: ${self.recent_low:.2f}" if self.recent_low else "",
            "",
            "### SUMMARY SIGNALS",
        ]

        for key, value in signals.items():
            lines.append(f"- {key.upper()}: {value}")

        return "\n".join(filter(None, lines))


def parse_alpaca_bars(bars_text: str) -> list[dict]:
    """Parse Alpaca bars output into list of price data."""
    bars = []
    lines = bars_text.strip().split("\n")

    for line in lines:
        if line.startswith("Time:"):
            # Parse: Time: 2026-02-04, Open: $179.46, High: $179.58, Low: $171.91, Close: $174.19, Volume: 206655687.0
            match = re.search(
                r"Time: ([\d-]+), Open: \$([\d.]+), High: \$([\d.]+), Low: \$([\d.]+), Close: \$([\d.]+), Volume: ([\d.]+)",
                line
            )
            if match:
                bars.append({
                    "date": match.group(1),
                    "open": float(match.group(2)),
                    "high": float(match.group(3)),
                    "low": float(match.group(4)),
                    "close": float(match.group(5)),
                    "volume": float(match.group(6)),
                })

    return bars


def calculate_sma(prices: list[float], period: int) -> Optional[float]:
    """Calculate Simple Moving Average."""
    if len(prices) < period:
        return None
    return sum(prices[-period:]) / period


def calculate_ema(prices: list[float], period: int) -> Optional[float]:
    """Calculate Exponential Moving Average."""
    if len(prices) < period:
        return None

    multiplier = 2 / (period + 1)
    ema = sum(prices[:period]) / period  # Start with SMA

    for price in prices[period:]:
        ema = (price - ema) * multiplier + ema

    return ema


def calculate_rsi(prices: list[float], period: int = 14) -> Optional[float]:
    """Calculate Relative Strength Index."""
    if len(prices) < period + 1:
        return None

    gains = []
    losses = []

    for i in range(1, len(prices)):
        change = prices[i] - prices[i - 1]
        if change > 0:
            gains.append(change)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(change))

    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period

    if avg_loss == 0:
        return 100

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    return rsi


def calculate_macd(prices: list[float]) -> tuple[Optional[float], Optional[float], Optional[float]]:
    """Calculate MACD (12, 26, 9)."""
    if len(prices) < 26:
        return None, None, None

    ema_12 = calculate_ema(prices, 12)
    ema_26 = calculate_ema(prices, 26)

    if ema_12 is None or ema_26 is None:
        return None, None, None

    macd_line = ema_12 - ema_26

    # Calculate signal line (9-period EMA of MACD)
    # Simplified: just return current MACD and estimate
    macd_values = []
    for i in range(26, len(prices) + 1):
        e12 = calculate_ema(prices[:i], 12)
        e26 = calculate_ema(prices[:i], 26)
        if e12 and e26:
            macd_values.append(e12 - e26)

    if len(macd_values) >= 9:
        signal_line = calculate_ema(macd_values, 9)
    else:
        signal_line = macd_line

    histogram = macd_line - signal_line if signal_line else 0

    return macd_line, signal_line, histogram


def calculate_bollinger_bands(prices: list[float], period: int = 20, std_dev: int = 2) -> tuple[Optional[float], Optional[float], Optional[float]]:
    """Calculate Bollinger Bands."""
    if len(prices) < period:
        return None, None, None

    sma = calculate_sma(prices, period)
    if sma is None:
        return None, None, None

    # Calculate standard deviation
    variance = sum((p - sma) ** 2 for p in prices[-period:]) / period
    std = variance ** 0.5

    upper = sma + (std_dev * std)
    lower = sma - (std_dev * std)

    return upper, sma, lower


def calculate_indicators(symbol: str, bars_text: str) -> TechnicalIndicators:
    """Calculate all technical indicators from Alpaca bars data."""
    bars = parse_alpaca_bars(bars_text)

    if not bars:
        return TechnicalIndicators(symbol=symbol, current_price=0)

    closes = [b["close"] for b in bars]
    volumes = [b["volume"] for b in bars]
    highs = [b["high"] for b in bars]
    lows = [b["low"] for b in bars]

    current_price = closes[-1]
    current_volume = volumes[-1]

    # Moving Averages
    sma_10 = calculate_sma(closes, 10)
    sma_20 = calculate_sma(closes, 20)
    sma_50 = calculate_sma(closes, 50) if len(closes) >= 50 else calculate_sma(closes, len(closes))

    # RSI
    rsi_14 = calculate_rsi(closes, 14)

    # MACD
    macd_line, macd_signal, macd_histogram = calculate_macd(closes)

    # Bollinger Bands
    bb_upper, bb_middle, bb_lower = calculate_bollinger_bands(closes, 20, 2)

    # Volume
    volume_sma_20 = calculate_sma(volumes, 20)
    volume_ratio = current_volume / volume_sma_20 if volume_sma_20 else None

    # Support/Resistance
    recent_high = max(highs)
    recent_low = min(lows)

    return TechnicalIndicators(
        symbol=symbol,
        current_price=current_price,
        sma_10=sma_10,
        sma_20=sma_20,
        sma_50=sma_50,
        rsi_14=rsi_14,
        macd_line=macd_line,
        macd_signal=macd_signal,
        macd_histogram=macd_histogram,
        bb_upper=bb_upper,
        bb_middle=bb_middle,
        bb_lower=bb_lower,
        volume_sma_20=volume_sma_20,
        current_volume=current_volume,
        volume_ratio=volume_ratio,
        recent_high=recent_high,
        recent_low=recent_low,
    )


def main():
    """CLI for testing."""
    import argparse

    parser = argparse.ArgumentParser(description="Calculate technical indicators")
    parser.add_argument("--symbol", "-s", required=True, help="Stock symbol")
    parser.add_argument("--bars", "-b", required=True, help="Path to file with Alpaca bars data")

    args = parser.parse_args()

    with open(args.bars) as f:
        bars_text = f.read()

    indicators = calculate_indicators(args.symbol, bars_text)
    print(indicators.to_context_string())


if __name__ == "__main__":
    main()
