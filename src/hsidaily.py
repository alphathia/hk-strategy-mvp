# hk_strategy_dashboard.py
# Hong Kong Equity Strategy Dashboard — Yahoo Finance edition
# Author: (Your desk)
# Last updated: 2025-08-27
#
# === MODIFICATION GUIDE ===
# This dashboard implements a momentum/breakout trading strategy for Hong Kong equities.
# It generates BUY/SELL/TRIM signals based on technical indicators and tracks performance
# against a baseline "hold" strategy from a reference date (H03).
#
# Key modification areas:
# 1. CONFIG section (lines ~24-89): Update portfolio positions, cash levels, trading rules
# 2. Signal thresholds (lines ~350-430): Adjust technical indicator conditions for A/B/C/D signals
# 3. Stock-specific rules (lines ~433-465): Add/modify individual stock trading overlays
# 4. Output formatting (lines ~520+): Customize dashboard display and reports
#
# Signal types:
# - A: Strong BUY (breakout above resistance with volume/momentum)
# - B: Strong BUY (oversold recovery with support reclaim)
# - C: Strong SELL (breakdown below support with weakness)
# - D: Strong TRIM (overbought reversal at target levels)
#
# To add a new stock: Update H03_BASELINE_QTY, CURRENT_QTY, optionally add to RAILS and stock-specific rules
# To modify strategy: Adjust technical indicator thresholds in evaluate_signals() function
# To add new indicators: Extend compute_indicators() and Indicators dataclass

import math
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone, date
from typing import Dict, Tuple, Optional, List

import numpy as np
import pandas as pd
from dateutil import tz
from tabulate import tabulate
import yfinance as yf

HK_TZ = tz.gettz("Asia/Hong_Kong")

# -----------------------------
# 0) CONFIG — edit as desired
# -----------------------------
# MODIFICATION GUIDE: Update these parameters to adjust portfolio tracking and data fetching
# - BASELINE_DATE: Reference date for H03 strategy comparison
# - BASELINE_CASH/DRY_POWDER: Cash positions for portfolio tracking
# - USE_LIVE_QUOTES: Toggle between historical close vs live market prices
# - LOOKBACK_DAYS: Historical data window for technical indicators (minimum ~50-60 for proper calculations)

BASELINE_DATE = date(2025, 8, 3)        # H03 anchor date - reference point for portfolio performance tracking
BASELINE_CASH = 200_000.0               # H03 cash position on baseline date
EXTERNAL_CASH_FLOWS = 0.0               # Net cash deposits(+)/withdrawals(-) since baseline date
DRY_POWDER = 420_000.0                  # Current actual cash position - UPDATE THIS REGULARLY

USE_LIVE_QUOTES = True                  # Use real-time prices when available, fallback to last close
LOOKBACK_DAYS = 90                      # Historical bars for indicators (90d provides good technical analysis window)

# Name-specific overlays & rails from your playbook (trim/add zones)
# MODIFICATION GUIDE: Add/modify stock-specific trading rules here
# - target_sell/trim_min: Price levels to trigger sell/trim signals
# - add_zone: (min, max) price range for accumulation
# - stop: Stop-loss levels for risk management
RAILS = {
    "0700.HK": {"target_sell": 660.0, "stop": 520.0},            # Tencent
    "9988.HK": {"trim_min": 132.0, "add_zone": (112.0, 115.0)},  # Alibaba-SW
    "0005.HK": {"target_sell": 111.0, "add_zone": (94.0, 96.0)}, # HSBC
    "0857.HK": {"target_sell": 8.40, "tactical_stop": 7.10},     # PetroChina H
    "2888.HK": {"trim_min": 152.0},
}

# H03 baseline (quantities at 03-Aug-2025)
# MODIFICATION GUIDE: This represents the reference portfolio for performance tracking
# Update these quantities to reflect the baseline position as of BASELINE_DATE
H03_BASELINE_QTY = {
    "0005.HK": 13428,
    "1211.HK": 0,
    "0316.HK": 100,
    "0388.HK": 600,
    "0522.HK": 0,
    "0700.HK": 3300,
    "0772.HK": 0,
    "0823.HK": 0,
    "0857.HK": 20000,
    "0939.HK": 26700,
    "0941.HK": 0,
    "1810.HK": 2000,
    "3690.HK": 340,
    "9618.HK": 133,
    "2888.HK": 348,
    "9988.HK": 2000,
    # 3750 (CATL A-share) excluded (not HK; baseline qty 0)
}

# Current portfolio (quantities now)
# MODIFICATION GUIDE: Update these quantities regularly to reflect actual current positions
# This drives the portfolio valuation and signal generation
CURRENT_QTY = {
    "0005.HK": 13428,
    "1211.HK": 0,
    "0316.HK": 100,
    "0388.HK": 300,
    "0522.HK": 0,
    "0700.HK": 3100,
    "0772.HK": 0,
    "0823.HK": 1300,
    "0857.HK": 0,          # appears as cost placeholder in your sheet
    "0939.HK": 26700,
    "0941.HK": 0,
    "1810.HK": 2000,
    "3690.HK": 340,
    "9618.HK": 133,
    "2888.HK": 348,
    "9988.HK": 2000,
}

WATCHLIST = sorted(set(H03_BASELINE_QTY) | set(CURRENT_QTY))

# Optional: manual veto (earnings/policy) by ticker->list of dates (YYYY-MM-DD)
# MODIFICATION GUIDE: Add earnings dates or policy events to prevent trading signals 2 days before
# Format: "TICKER": ["YYYY-MM-DD", "YYYY-MM-DD"] 
# If a date is within T-2 of 'today', B/A trades are vetoed.
MANUAL_VETO_DATES = {
    # "9988.HK": ["2025-08-29"],  # example earnings date → veto A/B 2 days before
}

# -----------------------------
# 1) Indicator functions
# -----------------------------
# MODIFICATION GUIDE: These are standard technical indicators used for signal generation
# Adjust periods/spans to fine-tune signal sensitivity

def ema(series: pd.Series, span: int) -> pd.Series:
    """Exponential Moving Average - more responsive to recent price changes than SMA"""
    return series.ewm(span=span, adjust=False, min_periods=span).mean()

def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Relative Strength Index (0-100) - momentum oscillator for overbought/oversold conditions
    RSI > 70 typically indicates overbought, RSI < 30 indicates oversold
    """
    delta = series.diff()
    gain = delta.clip(lower=0)  # Positive price changes
    loss = -delta.clip(upper=0)  # Negative price changes (made positive)
    avg_gain = gain.ewm(alpha=1/period, adjust=False, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1/period, adjust=False, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    out = 100 - (100 / (1 + rs))
    return out.fillna(0)

def macd(series: pd.Series, fast=12, slow=26, signal=9) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """MACD (Moving Average Convergence Divergence) - trend following momentum indicator
    Returns: (macd_line, signal_line, histogram)
    Buy signals when macd_line crosses above signal_line
    """
    ema_fast = ema(series, fast)
    ema_slow = ema(series, slow)
    macd_line = ema_fast - ema_slow
    signal_line = ema(macd_line, signal)
    hist = macd_line - signal_line  # Histogram shows momentum of MACD line
    return macd_line, signal_line, hist

def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Average True Range - measures market volatility
    Higher ATR = more volatile, used for position sizing and stop placement
    """
    high, low, close = df["High"], df["Low"], df["Close"]
    prev_close = close.shift(1)
    # True Range is the max of: H-L, |H-PC|, |L-PC| where PC = previous close
    tr1 = (high - low).abs()
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr_series = tr.ewm(alpha=1/period, adjust=False, min_periods=period).mean()
    return atr_series

# -----------------------------
# 2) Data helpers
# -----------------------------
# MODIFICATION GUIDE: These functions handle data fetching from Yahoo Finance
# Adjust fallback periods if you need longer historical data for analysis

def yf_history(ticker: str, days: int = LOOKBACK_DAYS) -> pd.DataFrame:
    """Fetch historical OHLCV data from Yahoo Finance with timezone handling
    Falls back to 6-month period if initial request returns insufficient data
    """
    tk = yf.Ticker(ticker)
    df = tk.history(period=f"{days}d", interval="1d", auto_adjust=False, actions=False)
    if df.empty or len(df) < 50:
        # Fallback: need minimum ~50 bars for meaningful technical analysis
        df = tk.history(period="6mo", interval="1d", auto_adjust=False, actions=False)
    df = df.rename_axis("Date").reset_index()
    # Ensure timezone-aware datetimes in HK timezone for proper market hours
    if df["Date"].dt.tz is None:
        # Timezone-naive: assume UTC and convert to HK
        df["Date"] = pd.to_datetime(df["Date"]).dt.tz_localize("UTC").dt.tz_convert(HK_TZ)
    elif str(df["Date"].dt.tz) != str(HK_TZ):
        # Already timezone-aware but not HK timezone
        df["Date"] = df["Date"].dt.tz_convert(HK_TZ)
    return df

def yf_live_quote(ticker: str) -> Tuple[Optional[float], Optional[int], Optional[datetime]]:
    """Attempt to fetch real-time price/volume data from Yahoo Finance
    Returns: (price, volume, timestamp) - any/all can be None if unavailable
    Used when USE_LIVE_QUOTES=True to get intraday pricing
    """
    tk = yf.Ticker(ticker)
    price, volume, ts = None, None, None
    try:
        # Try fast_info first (more reliable for real-time data)
        fi = getattr(tk, "fast_info", None)
        if fi:
            price = fi.get("last_price") or fi.get("regularMarketPrice")
            volume = fi.get("last_volume") or fi.get("regularMarketVolume")
        # Fallback to info dict
        info = tk.info or {}
        price = price or info.get("regularMarketPrice")
        volume = volume or info.get("regularMarketVolume")
        # Extract timestamp if available
        epoch = info.get("regularMarketTime")
        if epoch:
            ts = datetime.fromtimestamp(epoch, tz=timezone.utc).astimezone(HK_TZ)
    except Exception:
        pass  # Graceful degradation to historical data
    return price, volume, ts

def last_trading_close_on_or_before(df: pd.DataFrame, target: date) -> Optional[pd.Series]:
    """Find the most recent trading bar on or before a target date
    Used for baseline portfolio valuation on historical dates
    """
    if df.empty:
        return None
    # Find the last bar whose date <= target date
    dts = df["Date"].dt.date
    mask = dts <= target
    if mask.any():
        return df.loc[mask].iloc[-1]
    return None

# -----------------------------
# 3) Signals & overlays
# -----------------------------
# MODIFICATION GUIDE: Core data structures for signal generation
# Indicators class holds all calculated technical indicators for a single ticker

@dataclass
class Indicators:
    """Container for all technical indicators calculated for a single ticker
    Used as input to signal evaluation functions
    """
    price: float          # Current/live price (may be intraday if USE_LIVE_QUOTES=True)
    open_: float          # Last trading day's open price
    high: float           # Last trading day's high price
    low: float            # Last trading day's low price
    close: float          # Last trading day's close price
    volume: float         # Current/live volume
    rsi14: float          # 14-period RSI value
    ema5: float           # 5-period EMA (short-term trend)
    ema20: float          # 20-period EMA (medium-term trend)
    ema50: float          # 50-period EMA (long-term trend)
    macd: float           # MACD line (12-26 EMA difference)
    macd_prev: float      # Previous period MACD (for momentum direction)
    macd_signal: float    # MACD signal line (9-period EMA of MACD)
    atr14: float          # 14-period ATR (volatility measure)
    high20: float         # 20-period high (resistance level)
    low20: float          # 20-period low (support level)
    vol20_avg: float      # 20-period average volume
    dt: datetime          # Timestamp of data

def compute_indicators(df: pd.DataFrame, use_live: bool, ticker: str) -> Indicators:
    # compute studies
    df = df.copy()
    df["EMA5"] = ema(df["Close"], 5)
    df["EMA20"] = ema(df["Close"], 20)
    df["EMA50"] = ema(df["Close"], 50)
    df["RSI14"] = rsi(df["Close"], 14)
    macd_line, signal_line, hist = macd(df["Close"], 12, 26, 9)
    df["MACD"] = macd_line
    df["MACD_SIGNAL"] = signal_line
    df["ATR14"] = atr(df, 14)
    df["HIGH20"] = df["High"].rolling(20, min_periods=20).max()
    df["LOW20"] = df["Low"].rolling(20, min_periods=20).min()
    df["VOL20"] = df["Volume"].rolling(20, min_periods=20).mean()

    # last valid row for indicators
    last = df.iloc[-1]
    try:
        macd_prev = df["MACD"].iloc[-2] if len(df) > 1 else df["MACD"].iloc[-1]
    except (KeyError, IndexError):
        macd_prev = np.nan

    # price/volume/time: prefer live if requested and available
    price = float(last["Close"])
    volume = int(last["Volume"]) if not math.isnan(last["Volume"]) else 0
    dt = last["Date"]

    if use_live:
        live_price, live_vol, live_ts = yf_live_quote(ticker)
        if live_price is not None and isinstance(live_price, (int, float)):
            price = float(live_price)
        if live_vol is not None and isinstance(live_vol, (int, float)):
            volume = int(live_vol)
        if live_ts:
            dt = live_ts

    return Indicators(
        price=price,
        open_=float(last["Open"]),
        high=float(last["High"]),
        low=float(last["Low"]),
        close=float(last["Close"]),
        volume=volume,
        rsi14=float(last["RSI14"]) if not pd.isna(last["RSI14"]) else 50.0,
        ema5=float(last["EMA5"]) if not pd.isna(last["EMA5"]) else price,
        ema20=float(last["EMA20"]) if not pd.isna(last["EMA20"]) else price,
        ema50=float(last["EMA50"]) if not pd.isna(last["EMA50"]) else price,
        macd=float(last["MACD"]) if not pd.isna(last["MACD"]) else 0.0,
        macd_prev=float(macd_prev) if not pd.isna(macd_prev) else 0.0,
        macd_signal=float(last["MACD_SIGNAL"]) if not pd.isna(last["MACD_SIGNAL"]) else 0.0,
        atr14=float(last["ATR14"]) if not pd.isna(last["ATR14"]) else 1.0,
        high20=float(last["HIGH20"]) if not pd.isna(last["HIGH20"]) else price,
        low20=float(last["LOW20"]) if not pd.isna(last["LOW20"]) else price,
        vol20_avg=float(last["VOL20"]) if not pd.isna(last["VOL20"]) else volume,
        dt=dt,
    )

def within_T_minus_2(ticker: str, today_hk: date) -> bool:
    """Check if any manual veto dates are within 2 days of today
    Used to prevent trading signals before earnings/events
    """
    dates = MANUAL_VETO_DATES.get(ticker, [])
    for d in dates:
        try:
            ev = datetime.strptime(d, "%Y-%m-%d").date()
            if (ev - today_hk).days in (0, 1, 2):  # Event is T, T-1, or T-2
                return True
        except Exception:
            continue
    return False

@dataclass
class SignalResult:
    """Container for trading signal evaluation results
    A/B = Buy signals (A=breakout, B=oversold recovery)
    C/D = Sell signals (C=breakdown, D=overbought trim)
    """
    A: bool                 # Strong BUY - Breakout signal
    B: bool                 # Strong BUY - Oversold reclaim signal  
    C: bool                 # Strong SELL - Breakdown signal
    D: bool                 # Strong TRIM - Overbought reversal signal
    reasons: List[str]      # Detailed explanations for fired signals
    recommendation: str     # Summary recommendation (BUY/SELL/TRIM/HOLD)

def bullish_reversal_strength(close, low, high) -> float:
    """Measure where close price sits within the daily range (0.0 to 1.0)
    1.0 = closed at high of day (strong bullish), 0.0 = closed at low (weak)
    """
    rng = max(high - low, 1e-9)  # Avoid division by zero
    pos = (close - low) / rng
    return pos

def bearish_reversal_flag(prev_open, prev_close, open_, close) -> bool:
    """Detect bearish engulfing candlestick pattern
    Previous day green + current day red + current candle engulfs previous = bearish reversal
    """
    prev_green = prev_close > prev_open
    curr_red = close < open_
    # Current candle opens above and closes below previous candle's range
    engulf = (open_ >= max(prev_open, prev_close)) and (close <= min(prev_open, prev_close))
    return bool(prev_green and curr_red and engulf)

def evaluate_signals(ticker: str, df: pd.DataFrame, ind: Indicators, today_hk: date) -> SignalResult:
    """Core signal evaluation engine - generates BUY/SELL/TRIM signals based on technical indicators
    
    MODIFICATION GUIDE: Adjust signal thresholds here to fine-tune strategy
    - A signals: Breakout conditions (volume, momentum, trend alignment)
    - B signals: Oversold recovery conditions (RSI thresholds, support reclaim)
    - C signals: Breakdown conditions (trend breaks, momentum weakness)
    - D signals: Overbought trim conditions (resistance levels, reversal patterns)
    
    Stock-specific overlays are applied after base signal evaluation
    """
    reasons = []
    # Defensive guards for divisions/NaNs
    atr = ind.atr14 if ind.atr14 and not math.isnan(ind.atr14) else 0.0
    vol20 = ind.vol20_avg if ind.vol20_avg and not math.isnan(ind.vol20_avg) else 0.0
    vol_ratio = (ind.volume / vol20) if vol20 > 0 else 0.0

    # Previous candle for reversal checks
    prev = df.iloc[-2] if len(df) > 1 else None
    try:
        prev_rsi = float(rsi(df["Close"], 14).iloc[-2]) if len(df) > 1 else ind.rsi14
    except (KeyError, IndexError):
        prev_rsi = ind.rsi14
    try:
        prev_macd = float(df["MACD"].iloc[-2]) if len(df) > 1 else ind.macd
    except (KeyError, IndexError):
        prev_macd = ind.macd

    # --- A) Strong BUY — Breakout
    # MODIFICATION GUIDE: Adjust breakout thresholds here
    # - Change 0.35 multiplier for ATR breakout level
    # - Modify RSI threshold (currently 58) for momentum confirmation
    # - Adjust volume ratio threshold (currently 1.5x)
    A = False
    if (ind.ema5 > ind.ema20 and                                      # Trend alignment: short EMA above medium EMA
        not math.isnan(ind.high20) and ind.high20 > 0 and
        ind.price > (ind.high20 + 0.35 * atr) and                    # Price breakout above 20-day high + ATR buffer
        ((ind.rsi14 >= 58) or (ind.macd > 0 and ind.macd > ind.macd_prev)) and  # Momentum confirmation
        vol_ratio >= 1.5 and                                         # Volume surge (1.5x normal)
        not within_T_minus_2(ticker, today_hk)):                     # No earnings/events nearby
        A = True
        reasons.append("A: EMA5>EMA20, price>20D-H+0.35*ATR, momentum ok, vol≥1.5×, no T-2")

    # --- B) Strong BUY — Oversold Reclaim  
    # MODIFICATION GUIDE: Adjust oversold recovery thresholds here
    # - Modify RSI thresholds (currently 32-36 range) for oversold definition
    # - Change bullish_reversal_strength threshold (currently 0.70)
    # - Adjust volume confirmation (currently 1.3x)
    B = False
    if (prev_rsi <= 32 <= ind.rsi14 and ind.rsi14 >= 36 and          # RSI recovering from oversold (32) to neutral (36+)
        ind.price >= ind.ema20 and ind.price >= ind.ema5 and         # Price above key EMAs (support reclaim)
        bullish_reversal_strength(ind.price, ind.low, ind.high) >= 0.70 and  # Strong intraday close (top 30% of range)
        vol_ratio >= 1.3 and                                         # Volume confirmation
        not within_T_minus_2(ticker, today_hk)):                     # No earnings/events nearby
        B = True
        reasons.append("B: RSI up-cross, reclaimed EMA20 & ≥EMA5, bullish close, vol≥1.3×, no T-2")

    # --- C) Strong SELL / Reduce — Breakdown
    # MODIFICATION GUIDE: Adjust breakdown/sell thresholds here  
    # - Modify ATR multiplier (currently 0.35) for breakdown level below EMA50
    # - Change RSI threshold (currently 42) for weakness confirmation
    # - Adjust volume requirement (currently 1.5x) for conviction
    C = False
    c_level = ind.ema50 - 0.35 * atr                                 # Breakdown level below long-term EMA
    if (ind.price < c_level and                                      # Price breaks below EMA50 support with buffer
        ind.macd < 0 and ind.macd < ind.macd_prev and                # MACD negative and weakening
        ind.rsi14 <= 42 and                                          # RSI showing weakness (below neutral 50)
        vol_ratio >= 1.5):                                           # High volume confirms selling pressure
        C = True
        reasons.append(f"C: price<{c_level:.2f} (EMA50-0.35*ATR), MACD<0↓, RSI≤42, vol≥1.5×")

    # --- D) Strong TRIM — Overbought Reversal
    # MODIFICATION GUIDE: Adjust overbought trim conditions here
    # - Modify RSI overbought threshold (currently 68)
    # - Change reversal detection sensitivity (ATR multiplier 0.35)
    # - Update target price levels in RAILS configuration
    D = False
    rails = RAILS.get(ticker, {})                                    # Get stock-specific price targets
    target_sell = rails.get("target_sell") or rails.get("trim_min", None)

    # Reversal pattern detection
    rev_pulldown = (ind.high - ind.price) >= (0.35 * atr)           # Intraday pullback from high
    engulf = False
    if prev is not None:
        engulf = bearish_reversal_flag(prev["Open"], prev["Close"], ind.open_, ind.price)  # Bearish engulfing pattern

    if (target_sell is not None and ind.price >= target_sell and     # Price at/above target level
        ind.rsi14 >= 68 and                                          # Overbought conditions (RSI > 70 typical)
        (rev_pulldown or engulf) and                                 # Reversal signal present
        vol_ratio >= 1.3):                                           # Volume confirmation
        D = True
        reasons.append("D: RSI≥68 & ≥target, reversal (engulf/pullback≥0.35*ATR), vol≥1.3×")

    # --- Name-specific overlays
    # MODIFICATION GUIDE: Add new stock-specific rules here
    # Each stock can have custom conditions that override or refine base signals
    # Pattern: if ticker == "XXXX.HK": [custom logic]
    overlay_notes = []
    if ticker == "0700.HK":  # Tencent
        # Buy A preferred; B allowed if gap ≤1×ATR (manual verification required)
        if B:
            B = True  # Keep B but flag for manual gap check
            overlay_notes.append("0700: B requires open gap ≤1×ATR (manual intraday check)")
    elif ticker == "9988.HK":  # Alibaba-SW
        # Only B inside 112–115 add zone; Trim ≥132 only
        if B and not (112.0 <= ind.price <= 115.0):
            B = False
            overlay_notes.append("9988: B only allowed in 112–115 add zone")
        if D and ind.price < 132.0:
            D = False
            overlay_notes.append("9988: D (trim) only ≥132")
    elif ticker == "0388.HK":  # Hong Kong Exchanges
        # Prefer A/B at or above EMA20 for trend alignment
        if (A or B) and ind.price < ind.ema20:
            A = B = False
            overlay_notes.append("0388: A/B only at/above EMA20")
    elif ticker == "0005.HK":  # HSBC
        # B signals only when price near EMA20/50 convergence zone
        if B and not (min(ind.ema20, ind.ema50) * 0.99 <= ind.price <= max(ind.ema20, ind.ema50) * 1.01):
            B = False
            overlay_notes.append("0005: B only near EMA20/50 cluster")
    elif ticker == "0857.HK":  # PetroChina H
        # A signals require favorable oil market conditions (external confirmation needed)
        pass  # Oil tape condition cannot be programmatically verified
    elif ticker in ("3690.HK", "9618.HK", "2888.HK", "0823.HK", "0316.HK", "0939.HK", "1810.HK"):
        # These stocks use base rules with potential qualitative overlays for rates/commodities
        # Add specific conditions here as needed
        pass

    reasons.extend(overlay_notes)

    # Recommendation priority: if multiple fire, prefer risk controls (C/D) over buys; then A over B
    recommendation = "HOLD"
    if C:
        recommendation = "REDUCE (C)"
    elif D:
        recommendation = "TRIM (D)"
    elif A:
        recommendation = "BUY (A)"
    elif B:
        recommendation = "BUY (B)"

    return SignalResult(A=A, B=B, C=C, D=D, reasons=reasons, recommendation=recommendation)

# -----------------------------
# 4) Portfolio math
# -----------------------------
# MODIFICATION GUIDE: Portfolio tracking and valuation functions
# These functions calculate portfolio values and track performance vs baseline

@dataclass
class TickerState:
    """Complete state container for a single ticker including data, indicators, and signals"""
    ticker: str           # Stock symbol (e.g., "0700.HK")
    qty_now: int          # Current position quantity
    qty_h03: int          # Baseline (H03) position quantity for comparison
    ind: Indicators       # All calculated technical indicators
    df: pd.DataFrame      # Historical price data
    signals: SignalResult # Generated trading signals (A/B/C/D)

def value_portfolio(states: Dict[str, TickerState], qty_field: str) -> float:
    """Calculate total portfolio value using specified quantity field
    qty_field: 'qty_now' for current portfolio, 'qty_h03' for baseline comparison
    """
    total = 0.0
    for s in states.values():
        qty = getattr(s, qty_field)  # Get either current or baseline quantities
        total += qty * s.ind.price   # Value at current market prices
    return float(total)

def h03_cash_now() -> float:
    """Calculate what the H03 baseline cash position should be today
    Includes any external cash flows since baseline date
    """
    return BASELINE_CASH + EXTERNAL_CASH_FLOWS

# -----------------------------
# 5) Main orchestration
# -----------------------------
# MODIFICATION GUIDE: Main execution function - coordinates data fetching, signal generation, and reporting
# Modify output sections, add new analysis, or change display formatting here

def run_dashboard():
    """Main dashboard execution function
    1. Fetches market data for all tickers in watchlist
    2. Calculates technical indicators for each ticker
    3. Generates trading signals based on technical analysis
    4. Compiles portfolio performance vs H03 baseline
    5. Outputs formatted reports and recommendations
    """
    today_hk = datetime.now(HK_TZ).date()

    # Data collection and signal generation for all tickers
    states: Dict[str, TickerState] = {}
    for t in WATCHLIST:
        try:
            # Fetch historical price data
            df = yf_history(t, LOOKBACK_DAYS)
            if df.empty:
                print(f"[WARN] No data for {t}")
                continue
            # Calculate all technical indicators
            ind = compute_indicators(df, USE_LIVE_QUOTES, t)
            # Generate trading signals based on indicators
            signals = evaluate_signals(t, df, ind, today_hk)
            # Store complete state for this ticker
            states[t] = TickerState(
                ticker=t,
                qty_now=int(CURRENT_QTY.get(t, 0)),
                qty_h03=int(H03_BASELINE_QTY.get(t, 0)),
                ind=ind,
                df=df,
                signals=signals,
            )
        except Exception as e:
            print(f"[ERROR] {t}: {e}")
            continue

    # --- 4.1 Snapshot Table - Current market overview
    # MODIFICATION GUIDE: Customize table columns, formatting, or add new metrics here
    rows = []
    for t, s in states.items():
        # Calculate daily percentage change
        pct = np.nan
        try:
            last_close = s.ind.close
            if last_close and s.ind.price:
                pct = 100.0 * (s.ind.price / last_close - 1.0)
        except Exception:
            pass

        # Format 20-day range
        twenty_d = ""
        if not math.isnan(s.ind.low20) and not math.isnan(s.ind.high20):
            twenty_d = f"{s.ind.low20:.2f}..{s.ind.high20:.2f}"

        # Build row data for snapshot table
        rows.append({
            "Ticker": t,
            "Time": s.ind.dt.astimezone(HK_TZ).strftime("%Y-%m-%d %H:%M"),
            "Price": round(s.ind.price, 3),
            "%Δ Today": f"{pct:.2f}%",
            "RSI-14": round(s.ind.rsi14, 2),
            "EMA-5": round(s.ind.ema5, 2),
            "EMA-20": round(s.ind.ema20, 2),
            "EMA-50": round(s.ind.ema50, 2),
            "20D-L..H": twenty_d,
            "Vol/20D": round((s.ind.volume / s.ind.vol20_avg) if s.ind.vol20_avg else 0.0, 2),
            "ATR-14": round(s.ind.atr14, 3),
            "Recommendation": s.signals.recommendation
        })
    snap_df = pd.DataFrame(rows)
    if not snap_df.empty:
        snap_df = snap_df.sort_values(["Ticker"])

    # --- 4.6 Tracking vs H03 - Performance measurement
    # MODIFICATION GUIDE: Portfolio performance calculation vs baseline strategy
    # H03 value today = what we would have if we held baseline positions + baseline cash flows
    h03_equity_today = value_portfolio(states, "qty_h03")       # Baseline positions at current prices
    HHT = h03_equity_today + h03_cash_now()                     # Hold-Hold-Today total value

    # Actual value today (AVT) = current positions + current cash
    actual_equity_today = value_portfolio(states, "qty_now")    # Current positions at current prices
    AVT = actual_equity_today + DRY_POWDER                      # Actual-Value-Today total

    # Calculate alpha (outperformance vs baseline)
    alpha = AVT - HHT                                           # Absolute outperformance
    alpha_pct = (alpha / HHT * 100.0) if HHT != 0 else np.nan  # Percentage outperformance

    # Calculate baseline portfolio value on the anchor date (H03 reference)
    # This shows what the portfolio was worth when the H03 strategy began
    h03_bar_rows = []
    h03_equity_then = 0.0
    for t in WATCHLIST:
        if t not in H03_BASELINE_QTY or H03_BASELINE_QTY[t] == 0:
            continue
        # Get historical data to find price on baseline date
        df = states[t].df if t in states else yf_history(t, 200)
        bar = last_trading_close_on_or_before(df, BASELINE_DATE)
        if bar is None:
            continue
        px = float(bar["Close"])  # Price on baseline date
        q = H03_BASELINE_QTY[t]   # Baseline quantity
        h03_equity_then += q * px
        h03_bar_rows.append([t, q, px, q * px, bar["Date"].strftime("%Y-%m-%d")])

    H03_value_on_anchor = h03_equity_then + BASELINE_CASH  # Total baseline portfolio value

    # --- 4.5 Sector tilts - Portfolio allocation analysis
    # MODIFICATION GUIDE: Update SECTOR_MAP to reclassify stocks or add new tickers
    SECTOR_MAP = {
        "0700.HK": "Tech", "9988.HK": "Tech", "1810.HK": "Tech", "3690.HK": "Tech", "9618.HK": "Tech",
        "0388.HK": "Financials", "0005.HK": "Financials", "0939.HK": "Financials", "2888.HK": "Financials",
        "0823.HK": "REIT",
        "0857.HK": "Energy",
        "0316.HK": "Other", "1211.HK": "Other", "0522.HK": "Other", "0772.HK": "Other", "0941.HK": "Other"
    }
    # Calculate sector weights based on current positions
    by_sector = {}
    tot_now = actual_equity_today if actual_equity_today > 0 else 1.0
    for t, s in states.items():
        w = (s.ind.price * s.qty_now) / tot_now  # Weight = position value / total equity
        sec = SECTOR_MAP.get(t, "Other")
        by_sector[sec] = by_sector.get(sec, 0.0) + w
    sector_rows = [[k, f"{v*100:.1f}%"] for k, v in sorted(by_sector.items())]

    # --- 5) Print outputs
    print("\n=== 4.1 Snapshot Table ===")
    print(tabulate(snap_df, headers="keys", tablefmt="github", floatfmt=".3f"))

    print("\n=== 4.2 Fired Signals / Evidence ===")
    any_signals = False
    for t, s in states.items():
        sigs = []
        if s.signals.A: sigs.append("A")
        if s.signals.B: sigs.append("B")
        if s.signals.C: sigs.append("C")
        if s.signals.D: sigs.append("D")
        if sigs:
            any_signals = True
            print(f"- {t}: {','.join(sigs)} — " + " | ".join(s.signals.reasons))
    if not any_signals:
        print("NO ACTION — no certainty triggers today.")

    print("\n=== 4.5 Risk / Tilts ===")
    print(tabulate(sector_rows, headers=["Sector", "Weight (now)"], tablefmt="github"))

    print("\n=== 4.6 Tracking vs H03 (03-Aug-2025) ===")
    print(f"H03 value on 2025-08-03 (baseline): HK$ {H03_value_on_anchor:,.0f}")
    print(f"HHT (Hold, today) = Baseline equity (today) + H03 cash now: HK$ {HHT:,.0f}")
    print(f"AVT (Actual, today) = Current equity (today) + Actual cash now: HK$ {AVT:,.0f}")
    print(f"Alpha vs H03 = AVT − HHT = HK$ {alpha:,.0f} ({alpha_pct:.2f}%)")
    print(f"Did we beat the hold strategy? -> {'YES' if alpha > 0 else 'NO'}")

    # --- 5) Summary of recommended actions (concise)
    print("\n=== 4.7 Summary — Recommended Actions ===")
    summary_lines = []
    for t, s in states.items():
        if s.signals.C:
            lvl = s.ind.ema50 - 0.35 * s.ind.atr14
            summary_lines.append(f"REDUCE (C): {t} — Price<{lvl:.2f}, MACD<0↓, RSI≤42, Vol≥1.5×")
        elif s.signals.D:
            summary_lines.append(f"TRIM (D): {t} — RSI≥68 at/above target; reversal/pullback with Vol≥1.3×")
        elif s.signals.A:
            summary_lines.append(f"BUY (A): {t} — Breakout above 20D-H+0.35×ATR with Vol≥1.5× (EMA5>EMA20)")
        elif s.signals.B:
            summary_lines.append(f"BUY (B): {t} — Oversold reclaim (RSI up‑cross, EMA20 reclaimed, bullish close, Vol≥1.3×)")
    if summary_lines:
        for ln in summary_lines:
            print("-", ln)
    else:
        print("NO ACTION — hold and monitor watches.")

    # --- Optional: write snapshot to CSV for the desk
    out = snap_df.copy()
    out_file = f"hk_snapshot_{datetime.now(HK_TZ).strftime('%Y%m%d_%H%M')}.csv"
    out.to_csv(out_file, index=False)
    print(f"\nSnapshot saved → {out_file}")

if __name__ == "__main__":
    run_dashboard()
