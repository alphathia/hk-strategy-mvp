# Integrated HK Strategy for Streamlit MVP
# Based on original hsidaily.py with database integration

import math
import json
import pickle
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone, date
from typing import Dict, Tuple, Optional, List

import numpy as np
import pandas as pd
from dateutil import tz
import yfinance as yf

try:
    from database import DatabaseManager
except ImportError:
    from database_local import DatabaseManager

HK_TZ = tz.gettz("Asia/Hong_Kong")

# Configuration from original strategy
BASELINE_DATE = date(2025, 8, 3)
BASELINE_CASH = 200_000.0
EXTERNAL_CASH_FLOWS = 0.0
DRY_POWDER = 420_000.0

USE_LIVE_QUOTES = True
LOOKBACK_DAYS = 90

# Stock-specific trading rules (RAILS)
RAILS = {
    "0700.HK": {"target_sell": 660.0, "stop": 520.0},
    "9988.HK": {"trim_min": 132.0, "add_zone": (112.0, 115.0)},
    "0005.HK": {"target_sell": 111.0, "add_zone": (94.0, 96.0)},
    "0857.HK": {"target_sell": 8.40, "tactical_stop": 7.10},
    "2888.HK": {"trim_min": 152.0},
}

# Portfolio quantities
H03_BASELINE_QTY = {
    "0005.HK": 13428, "1211.HK": 0, "0316.HK": 100, "0388.HK": 600, "0522.HK": 0,
    "0700.HK": 3300, "0772.HK": 0, "0823.HK": 0, "0857.HK": 20000, "0939.HK": 26700,
    "0941.HK": 0, "1810.HK": 2000, "3690.HK": 340, "9618.HK": 133, "2888.HK": 348, "9988.HK": 2000,
}

CURRENT_QTY = {
    "0005.HK": 13428, "1211.HK": 0, "0316.HK": 100, "0388.HK": 300, "0522.HK": 0,
    "0700.HK": 3100, "0772.HK": 0, "0823.HK": 1300, "0857.HK": 0, "0939.HK": 26700,
    "0941.HK": 0, "1810.HK": 2000, "3690.HK": 340, "9618.HK": 133, "2888.HK": 348, "9988.HK": 2000,
}

WATCHLIST = sorted(set(H03_BASELINE_QTY) | set(CURRENT_QTY))

MANUAL_VETO_DATES = {}

class HKStrategy:
    def __init__(self):
        self.db = DatabaseManager()
    
    def get_cached_data(self, ticker: str, days: int = LOOKBACK_DAYS) -> Optional[pd.DataFrame]:
        """Get cached Yahoo Finance data from Redis"""
        cache_key = f"yf_data:{ticker}:{days}"
        cached = self.db.get_cache(cache_key)
        if cached:
            try:
                return pd.read_json(cached)
            except:
                pass
        return None
    
    def cache_data(self, ticker: str, df: pd.DataFrame, days: int = LOOKBACK_DAYS):
        """Cache Yahoo Finance data in Redis"""
        cache_key = f"yf_data:{ticker}:{days}"
        try:
            json_data = df.to_json()
            self.db.set_cache(cache_key, json_data, expiry=3600)  # 1 hour cache
        except Exception:
            pass
    
    def yf_history(self, ticker: str, days: int = LOOKBACK_DAYS) -> pd.DataFrame:
        """Fetch historical data with Redis caching"""
        # Try cache first
        cached_df = self.get_cached_data(ticker, days)
        if cached_df is not None and len(cached_df) >= 50:
            return cached_df
        
        # Fetch from Yahoo Finance
        tk = yf.Ticker(ticker)
        df = tk.history(period=f"{days}d", interval="1d", auto_adjust=False, actions=False)
        if df.empty or len(df) < 50:
            df = tk.history(period="6mo", interval="1d", auto_adjust=False, actions=False)
        
        df = df.rename_axis("Date").reset_index()
        if df["Date"].dt.tz is None:
            df["Date"] = pd.to_datetime(df["Date"]).dt.tz_localize("UTC").dt.tz_convert(HK_TZ)
        elif str(df["Date"].dt.tz) != str(HK_TZ):
            df["Date"] = df["Date"].dt.tz_convert(HK_TZ)
        
        # Cache the result
        self.cache_data(ticker, df, days)
        return df

    def yf_live_quote(self, ticker: str) -> Tuple[Optional[float], Optional[int], Optional[datetime]]:
        """Get live quote with Redis caching"""
        cache_key = f"live_quote:{ticker}"
        cached = self.db.get_cache(cache_key)
        if cached:
            try:
                data = json.loads(cached)
                return data.get('price'), data.get('volume'), datetime.fromisoformat(data['timestamp']) if data.get('timestamp') else None
            except:
                pass
        
        # Fetch live data
        tk = yf.Ticker(ticker)
        price, volume, ts = None, None, None
        try:
            fi = getattr(tk, "fast_info", None)
            if fi:
                price = fi.get("last_price") or fi.get("regularMarketPrice")
                volume = fi.get("last_volume") or fi.get("regularMarketVolume")
            info = tk.info or {}
            price = price or info.get("regularMarketPrice")
            volume = volume or info.get("regularMarketVolume")
            epoch = info.get("regularMarketTime")
            if epoch:
                ts = datetime.fromtimestamp(epoch, tz=timezone.utc).astimezone(HK_TZ)
        except Exception:
            pass
        
        # Cache live quote for 60 seconds
        if price is not None:
            cache_data = {
                'price': price,
                'volume': volume,
                'timestamp': ts.isoformat() if ts else None
            }
            self.db.set_cache(cache_key, json.dumps(cache_data), expiry=60)
        
        return price, volume, ts

# Technical indicator functions (preserved exactly)
def ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False, min_periods=span).mean()

def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1/period, adjust=False, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1/period, adjust=False, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    out = 100 - (100 / (1 + rs))
    return out.fillna(0)

def macd(series: pd.Series, fast=12, slow=26, signal=9) -> Tuple[pd.Series, pd.Series, pd.Series]:
    ema_fast = ema(series, fast)
    ema_slow = ema(series, slow)
    macd_line = ema_fast - ema_slow
    signal_line = ema(macd_line, signal)
    hist = macd_line - signal_line
    return macd_line, signal_line, hist

def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high, low, close = df["High"], df["Low"], df["Close"]
    prev_close = close.shift(1)
    tr1 = (high - low).abs()
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr_series = tr.ewm(alpha=1/period, adjust=False, min_periods=period).mean()
    return atr_series

@dataclass
class Indicators:
    price: float
    open_: float
    high: float
    low: float
    close: float
    volume: float
    rsi14: float
    ema5: float
    ema20: float
    ema50: float
    macd: float
    macd_prev: float
    macd_signal: float
    atr14: float
    high20: float
    low20: float
    vol20_avg: float
    dt: datetime

@dataclass 
class SignalResult:
    A: bool
    B: bool
    C: bool
    D: bool
    reasons: List[str]
    recommendation: str

class HKStrategyEngine(HKStrategy):
    def compute_indicators(self, df: pd.DataFrame, use_live: bool, ticker: str) -> Indicators:
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

        last = df.iloc[-1]
        try:
            macd_prev = df["MACD"].iloc[-2] if len(df) > 1 else df["MACD"].iloc[-1]
        except (KeyError, IndexError):
            macd_prev = np.nan

        price = float(last["Close"])
        volume = int(last["Volume"]) if not math.isnan(last["Volume"]) else 0
        dt = last["Date"]

        if use_live:
            live_price, live_vol, live_ts = self.yf_live_quote(ticker)
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

    def within_T_minus_2(self, ticker: str, today_hk: date) -> bool:
        dates = MANUAL_VETO_DATES.get(ticker, [])
        for d in dates:
            try:
                ev = datetime.strptime(d, "%Y-%m-%d").date()
                if (ev - today_hk).days in (0, 1, 2):
                    return True
            except Exception:
                continue
        return False

    def bullish_reversal_strength(self, close, low, high) -> float:
        rng = max(high - low, 1e-9)
        pos = (close - low) / rng
        return pos

    def bearish_reversal_flag(self, prev_open, prev_close, open_, close) -> bool:
        prev_green = prev_close > prev_open
        curr_red = close < open_
        engulf = (open_ >= max(prev_open, prev_close)) and (close <= min(prev_open, prev_close))
        return bool(prev_green and curr_red and engulf)

    def evaluate_signals(self, ticker: str, df: pd.DataFrame, ind: Indicators, today_hk: date) -> SignalResult:
        """EXACT PRESERVATION of original A/B/C/D signal logic"""
        reasons = []
        atr = ind.atr14 if ind.atr14 and not math.isnan(ind.atr14) else 0.0
        vol20 = ind.vol20_avg if ind.vol20_avg and not math.isnan(ind.vol20_avg) else 0.0
        vol_ratio = (ind.volume / vol20) if vol20 > 0 else 0.0

        prev = df.iloc[-2] if len(df) > 1 else None
        try:
            prev_rsi = float(rsi(df["Close"], 14).iloc[-2]) if len(df) > 1 else ind.rsi14
        except (KeyError, IndexError):
            prev_rsi = ind.rsi14
        try:
            prev_macd = float(df["MACD"].iloc[-2]) if len(df) > 1 else ind.macd
        except (KeyError, IndexError):
            prev_macd = ind.macd

        # A) Strong BUY — Breakout (EXACT PRESERVATION)
        A = False
        if (ind.ema5 > ind.ema20 and
            not math.isnan(ind.high20) and ind.high20 > 0 and
            ind.price > (ind.high20 + 0.35 * atr) and
            ((ind.rsi14 >= 58) or (ind.macd > 0 and ind.macd > ind.macd_prev)) and
            vol_ratio >= 1.5 and
            not self.within_T_minus_2(ticker, today_hk)):
            A = True
            reasons.append("A: EMA5>EMA20, price>20D-H+0.35*ATR, momentum ok, vol≥1.5×, no T-2")

        # B) Strong BUY — Oversold Reclaim (EXACT PRESERVATION)
        B = False
        if (prev_rsi <= 32 <= ind.rsi14 and ind.rsi14 >= 36 and
            ind.price >= ind.ema20 and ind.price >= ind.ema5 and
            self.bullish_reversal_strength(ind.price, ind.low, ind.high) >= 0.70 and
            vol_ratio >= 1.3 and
            not self.within_T_minus_2(ticker, today_hk)):
            B = True
            reasons.append("B: RSI up-cross, reclaimed EMA20 & ≥EMA5, bullish close, vol≥1.3×, no T-2")

        # C) Strong SELL / Reduce — Breakdown (EXACT PRESERVATION)
        C = False
        c_level = ind.ema50 - 0.35 * atr
        if (ind.price < c_level and
            ind.macd < 0 and ind.macd < ind.macd_prev and
            ind.rsi14 <= 42 and
            vol_ratio >= 1.5):
            C = True
            reasons.append(f"C: price<{c_level:.2f} (EMA50-0.35*ATR), MACD<0↓, RSI≤42, vol≥1.5×")

        # D) Strong TRIM — Overbought Reversal (EXACT PRESERVATION)
        D = False
        rails = RAILS.get(ticker, {})
        target_sell = rails.get("target_sell") or rails.get("trim_min", None)

        rev_pulldown = (ind.high - ind.price) >= (0.35 * atr)
        engulf = False
        if prev is not None:
            engulf = self.bearish_reversal_flag(prev["Open"], prev["Close"], ind.open_, ind.price)

        if (target_sell is not None and ind.price >= target_sell and
            ind.rsi14 >= 68 and
            (rev_pulldown or engulf) and
            vol_ratio >= 1.3):
            D = True
            reasons.append("D: RSI≥68 & ≥target, reversal (engulf/pullback≥0.35*ATR), vol≥1.3×")

        # Stock-specific overlays (EXACT PRESERVATION)
        overlay_notes = []
        if ticker == "0700.HK":
            if B:
                B = True
                overlay_notes.append("0700: B requires open gap ≤1×ATR (manual intraday check)")
        elif ticker == "9988.HK":
            if B and not (112.0 <= ind.price <= 115.0):
                B = False
                overlay_notes.append("9988: B only allowed in 112–115 add zone")
            if D and ind.price < 132.0:
                D = False
                overlay_notes.append("9988: D (trim) only ≥132")
        elif ticker == "0388.HK":
            if (A or B) and ind.price < ind.ema20:
                A = B = False
                overlay_notes.append("0388: A/B only at/above EMA20")
        elif ticker == "0005.HK":
            if B and not (min(ind.ema20, ind.ema50) * 0.99 <= ind.price <= max(ind.ema20, ind.ema50) * 1.01):
                B = False
                overlay_notes.append("0005: B only near EMA20/50 cluster")

        reasons.extend(overlay_notes)

        # Recommendation priority (EXACT PRESERVATION)
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

    def save_signal_to_db(self, ticker: str, signals: SignalResult, indicators: Indicators):
        """Save signals to PostgreSQL"""
        # Determine primary signal type using new TXYZN convention
        if signals.A:
            signal_type = 'BBRK9'  # Strong Buy Breakout, strength 9
            signal_strength = 0.9
        elif signals.B:
            signal_type = 'BRSV7'  # Buy RSI Reversal, strength 7 
            signal_strength = 0.8
        elif signals.C:
            signal_type = 'SBRK3'  # Sell Breakdown, strength 3
            signal_strength = 0.7
        elif signals.D:
            signal_type = 'SOVB1'  # Sell Overbought, strength 1
            signal_strength = 0.6
        else:
            signal_type = 'HMOM5'  # Hold Momentum, strength 5 (default)
            signal_strength = 0.5

        self.db.insert_trading_signal(
            symbol=ticker,
            signal_type=signal_type,
            signal_strength=signal_strength,
            price=indicators.price,
            rsi=indicators.rsi14,
            ma_5=indicators.ema5,
            ma_20=indicators.ema20,
            ma_50=indicators.ema50,
            volume=indicators.volume
        )

    def generate_signals_for_watchlist(self) -> Dict:
        """Generate signals for all watchlist tickers"""
        today_hk = datetime.now(HK_TZ).date()
        results = {}
        
        for ticker in WATCHLIST:
            try:
                df = self.yf_history(ticker, LOOKBACK_DAYS)
                if df.empty:
                    continue
                
                indicators = self.compute_indicators(df, USE_LIVE_QUOTES, ticker)
                signals = self.evaluate_signals(ticker, df, indicators, today_hk)
                
                # Save to database
                self.save_signal_to_db(ticker, signals, indicators)
                
                results[ticker] = {
                    'indicators': indicators,
                    'signals': signals,
                    'df': df
                }
                
            except Exception as e:
                print(f"Error processing {ticker}: {e}")
                continue
        
        return results

    def get_portfolio_performance(self, results: Dict) -> Dict:
        """Calculate portfolio performance vs H03 baseline"""
        h03_equity_today = sum(
            H03_BASELINE_QTY.get(ticker, 0) * results[ticker]['indicators'].price
            for ticker in results if ticker in H03_BASELINE_QTY
        )
        HHT = h03_equity_today + BASELINE_CASH + EXTERNAL_CASH_FLOWS
        
        actual_equity_today = sum(
            CURRENT_QTY.get(ticker, 0) * results[ticker]['indicators'].price
            for ticker in results if ticker in CURRENT_QTY
        )
        AVT = actual_equity_today + DRY_POWDER
        
        alpha = AVT - HHT
        alpha_pct = (alpha / HHT * 100.0) if HHT != 0 else 0.0
        
        return {
            'h03_value': HHT,
            'actual_value': AVT,
            'alpha': alpha,
            'alpha_pct': alpha_pct,
            'h03_equity': h03_equity_today,
            'actual_equity': actual_equity_today
        }