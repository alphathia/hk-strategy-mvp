"""
Bollinger Bands Trading Strategies Implementation
Based on John Bollinger's methodology and Investopedia guidelines

Implements three main Bollinger Band strategies:
1. BBOL - Bollinger Bounce (Mean Reversion)
2. BBSQ - Bollinger Squeeze (Volatility Breakout)
3. BBWK - Bollinger Band Walking (Trend Following)
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

class BollingerSignalType(Enum):
    """Types of Bollinger Band signals"""
    BOUNCE_BUY = "BBOL"      # Buy on lower band bounce
    BOUNCE_SELL = "BBOS"     # Sell on upper band rejection
    SQUEEZE_BREAK_UP = "BBSU" # Squeeze breakout upward
    SQUEEZE_BREAK_DOWN = "BBSD" # Squeeze breakdown
    WALK_UP = "BBWU"         # Band walking upward
    WALK_DOWN = "BBWD"       # Band walking downward
    HOLD = "BBHO"            # Hold in consolidation

@dataclass
class BollingerSignal:
    """Bollinger Band signal result"""
    signal_type: BollingerSignalType
    signal_strength: int  # 1-9 magnitude
    confidence: float     # 0.0-1.0 confidence level
    price_position: str   # Position relative to bands
    volatility_state: str # Squeeze, Normal, Expansion
    reasons: List[str]    # Signal reasoning
    entry_price: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None

class BollingerBandAnalyzer:
    """Comprehensive Bollinger Band Analysis and Signal Generation"""
    
    def __init__(self, period: int = 20, std_dev: float = 2.0):
        self.period = period
        self.std_dev = std_dev
        
    def calculate_bollinger_bands(self, prices: pd.Series) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate Bollinger Bands"""
        sma = prices.rolling(window=self.period).mean()
        std = prices.rolling(window=self.period).std()
        
        upper_band = sma + (std * self.std_dev)
        lower_band = sma - (std * self.std_dev)
        
        return upper_band, sma, lower_band
    
    def calculate_percent_b(self, price: float, upper: float, lower: float) -> float:
        """%B indicator: (Price - Lower) / (Upper - Lower)"""
        if upper == lower:
            return 0.5
        return (price - lower) / (upper - lower)
    
    def calculate_band_width(self, upper: float, lower: float, middle: float) -> float:
        """Bollinger Band Width: (Upper - Lower) / Middle"""
        if middle == 0:
            return 0
        return (upper - lower) / middle
    
    def detect_squeeze(self, band_widths: pd.Series, lookback: int = 20) -> bool:
        """Detect Bollinger Squeeze (lowest band width in lookback period)"""
        if len(band_widths) < lookback:
            return False
        recent_widths = band_widths.tail(lookback)
        return band_widths.iloc[-1] == recent_widths.min()
    
    def analyze_bollinger_signal(self, 
                                df: pd.DataFrame, 
                                rsi: Optional[pd.Series] = None,
                                volume_ratio: Optional[pd.Series] = None) -> BollingerSignal:
        """
        Comprehensive Bollinger Band signal analysis
        
        Args:
            df: DataFrame with OHLCV data
            rsi: Optional RSI series for confirmation
            volume_ratio: Optional volume ratio for confirmation
        """
        if len(df) < self.period + 5:
            return self._no_signal("Insufficient data")
        
        # Calculate Bollinger Bands
        bb_upper, bb_middle, bb_lower = self.calculate_bollinger_bands(df['close'])
        
        # Current values
        current_price = df['close'].iloc[-1]
        current_upper = bb_upper.iloc[-1]
        current_middle = bb_middle.iloc[-1]
        current_lower = bb_lower.iloc[-1]
        
        # Calculate indicators
        percent_b = self.calculate_percent_b(current_price, current_upper, current_lower)
        band_widths = pd.Series([self.calculate_band_width(u, l, m) 
                               for u, l, m in zip(bb_upper, bb_lower, bb_middle)])
        
        # Analysis components
        price_position = self._analyze_price_position(current_price, current_upper, current_middle, current_lower)
        volatility_state = self._analyze_volatility_state(band_widths)
        is_squeeze = self.detect_squeeze(band_widths)
        
        # Generate signals based on strategy
        signals = []
        
        # 1. Bollinger Bounce Strategy (BBOL)
        bounce_signal = self._analyze_bounce_strategy(
            df, current_price, current_upper, current_middle, current_lower, 
            percent_b, rsi, volume_ratio
        )
        if bounce_signal:
            signals.append(bounce_signal)
        
        # 2. Bollinger Squeeze Strategy (BBSQ)
        if is_squeeze:
            squeeze_signal = self._analyze_squeeze_strategy(
                df, current_price, current_upper, current_middle, current_lower,
                band_widths, volume_ratio
            )
            if squeeze_signal:
                signals.append(squeeze_signal)
        
        # 3. Bollinger Band Walking Strategy (BBWK)
        walking_signal = self._analyze_walking_strategy(
            df, bb_upper, bb_lower, current_price, percent_b, rsi
        )
        if walking_signal:
            signals.append(walking_signal)
        
        # Return strongest signal or hold
        if signals:
            strongest_signal = max(signals, key=lambda s: s.confidence * s.signal_strength)
            strongest_signal.price_position = price_position
            strongest_signal.volatility_state = volatility_state
            return strongest_signal
        
        return self._hold_signal(price_position, volatility_state)
    
    def _analyze_bounce_strategy(self, df, current_price, upper, middle, lower, percent_b, rsi, volume_ratio) -> Optional[BollingerSignal]:
        """Analyze Bollinger Bounce (Mean Reversion) signals"""
        reasons = []
        
        # Buy signal: Price near lower band + oversold conditions
        if percent_b <= 0.2:  # Price at or below lower band
            reasons.append("Price touching lower Bollinger Band")
            
            signal_strength = 5  # Base strength
            confidence = 0.6     # Base confidence
            
            # RSI confirmation
            if rsi is not None and len(rsi) > 0:
                current_rsi = rsi.iloc[-1]
                if current_rsi < 30:
                    reasons.append(f"RSI oversold ({current_rsi:.1f})")
                    signal_strength += 2
                    confidence += 0.15
                elif current_rsi < 40:
                    reasons.append(f"RSI approaching oversold ({current_rsi:.1f})")
                    signal_strength += 1
                    confidence += 0.1
            
            # Volume confirmation
            if volume_ratio is not None and len(volume_ratio) > 0:
                vol_ratio = volume_ratio.iloc[-1]
                if vol_ratio > 1.3:
                    reasons.append(f"High volume confirmation ({vol_ratio:.1f}x avg)")
                    signal_strength += 1
                    confidence += 0.1
            
            # Price action confirmation (hammer/doji patterns would go here)
            prev_close = df['close'].iloc[-2] if len(df) > 1 else current_price
            if current_price > prev_close:
                reasons.append("Price bouncing off lower band")
                confidence += 0.1
            
            return BollingerSignal(
                signal_type=BollingerSignalType.BOUNCE_BUY,
                signal_strength=min(signal_strength, 9),
                confidence=min(confidence, 1.0),
                price_position="",
                volatility_state="",
                reasons=reasons,
                entry_price=current_price,
                stop_loss=lower * 0.995,  # Stop below lower band
                take_profit=middle        # Target middle band
            )
        
        # Sell signal: Price near upper band + overbought conditions
        elif percent_b >= 0.8:  # Price at or above upper band
            reasons.append("Price touching upper Bollinger Band")
            
            signal_strength = 5
            confidence = 0.6
            
            # RSI confirmation
            if rsi is not None and len(rsi) > 0:
                current_rsi = rsi.iloc[-1]
                if current_rsi > 70:
                    reasons.append(f"RSI overbought ({current_rsi:.1f})")
                    signal_strength += 2
                    confidence += 0.15
                elif current_rsi > 60:
                    reasons.append(f"RSI approaching overbought ({current_rsi:.1f})")
                    signal_strength += 1
                    confidence += 0.1
            
            # Volume confirmation
            if volume_ratio is not None and len(volume_ratio) > 0:
                vol_ratio = volume_ratio.iloc[-1]
                if vol_ratio > 1.3:
                    reasons.append(f"High volume confirmation ({vol_ratio:.1f}x avg)")
                    signal_strength += 1
                    confidence += 0.1
            
            return BollingerSignal(
                signal_type=BollingerSignalType.BOUNCE_SELL,
                signal_strength=min(signal_strength, 9),
                confidence=min(confidence, 1.0),
                price_position="",
                volatility_state="",
                reasons=reasons,
                entry_price=current_price,
                stop_loss=upper * 1.005,  # Stop above upper band
                take_profit=middle        # Target middle band
            )
        
        return None
    
    def _analyze_squeeze_strategy(self, df, current_price, upper, middle, lower, band_widths, volume_ratio) -> Optional[BollingerSignal]:
        """Analyze Bollinger Squeeze (Volatility Breakout) signals"""
        reasons = ["Bollinger Squeeze detected - low volatility"]
        
        # Look for breakout direction
        recent_closes = df['close'].tail(3)
        price_momentum = (recent_closes.iloc[-1] - recent_closes.iloc[0]) / recent_closes.iloc[0]
        
        signal_strength = 6  # Squeeze signals are generally strong
        confidence = 0.7
        
        # Volume confirmation
        if volume_ratio is not None and len(volume_ratio) > 0:
            vol_ratio = volume_ratio.iloc[-1]
            if vol_ratio > 1.5:
                reasons.append(f"High volume breakout ({vol_ratio:.1f}x avg)")
                signal_strength += 2
                confidence += 0.15
        
        # Upward breakout
        if current_price > middle and price_momentum > 0.01:
            reasons.append(f"Price breaking above middle band with {price_momentum:.1%} momentum")
            
            return BollingerSignal(
                signal_type=BollingerSignalType.SQUEEZE_BREAK_UP,
                signal_strength=min(signal_strength, 9),
                confidence=min(confidence, 1.0),
                price_position="",
                volatility_state="",
                reasons=reasons,
                entry_price=current_price,
                stop_loss=lower,
                take_profit=current_price * 1.05  # 5% target
            )
        
        # Downward breakout
        elif current_price < middle and price_momentum < -0.01:
            reasons.append(f"Price breaking below middle band with {price_momentum:.1%} momentum")
            
            return BollingerSignal(
                signal_type=BollingerSignalType.SQUEEZE_BREAK_DOWN,
                signal_strength=min(signal_strength, 9),
                confidence=min(confidence, 1.0),
                price_position="",
                volatility_state="",
                reasons=reasons,
                entry_price=current_price,
                stop_loss=upper,
                take_profit=current_price * 0.95  # 5% target down
            )
        
        return None
    
    def _analyze_walking_strategy(self, df, bb_upper, bb_lower, current_price, percent_b, rsi) -> Optional[BollingerSignal]:
        """Analyze Bollinger Band Walking (Trend Following) signals"""
        if len(df) < 10:
            return None
        
        recent_percent_b = [self.calculate_percent_b(price, upper, lower) 
                           for price, upper, lower in zip(df['close'].tail(5), bb_upper.tail(5), bb_lower.tail(5))]
        
        # Walking the upper band (strong uptrend)
        upper_walking = sum(1 for pb in recent_percent_b if pb > 0.8) >= 3
        if upper_walking and percent_b > 0.8:
            reasons = ["Price walking upper Bollinger Band - strong uptrend"]
            signal_strength = 7
            confidence = 0.8
            
            # RSI should not be extremely overbought for continuation
            if rsi is not None and len(rsi) > 0:
                current_rsi = rsi.iloc[-1]
                if current_rsi < 80:
                    reasons.append(f"RSI not extremely overbought ({current_rsi:.1f})")
                    confidence += 0.1
            
            return BollingerSignal(
                signal_type=BollingerSignalType.WALK_UP,
                signal_strength=min(signal_strength, 9),
                confidence=min(confidence, 1.0),
                price_position="",
                volatility_state="",
                reasons=reasons,
                entry_price=current_price,
                stop_loss=bb_lower.iloc[-1],
                take_profit=None  # Trend following - no specific target
            )
        
        # Walking the lower band (strong downtrend)
        lower_walking = sum(1 for pb in recent_percent_b if pb < 0.2) >= 3
        if lower_walking and percent_b < 0.2:
            reasons = ["Price walking lower Bollinger Band - strong downtrend"]
            signal_strength = 7
            confidence = 0.8
            
            # RSI should not be extremely oversold for continuation
            if rsi is not None and len(rsi) > 0:
                current_rsi = rsi.iloc[-1]
                if current_rsi > 20:
                    reasons.append(f"RSI not extremely oversold ({current_rsi:.1f})")
                    confidence += 0.1
            
            return BollingerSignal(
                signal_type=BollingerSignalType.WALK_DOWN,
                signal_strength=min(signal_strength, 9),
                confidence=min(confidence, 1.0),
                price_position="",
                volatility_state="",
                reasons=reasons,
                entry_price=current_price,
                stop_loss=bb_upper.iloc[-1],
                take_profit=None  # Trend following - no specific target
            )
        
        return None
    
    def _analyze_price_position(self, price, upper, middle, lower) -> str:
        """Analyze price position relative to Bollinger Bands"""
        if price > upper:
            return "Above Upper Band"
        elif price > middle:
            return "Above Middle Band"
        elif price > lower:
            return "Between Middle and Lower"
        else:
            return "Below Lower Band"
    
    def _analyze_volatility_state(self, band_widths) -> str:
        """Analyze current volatility state"""
        if len(band_widths) < 20:
            return "Insufficient Data"
        
        current_width = band_widths.iloc[-1]
        avg_width = band_widths.tail(20).mean()
        
        if current_width < avg_width * 0.7:
            return "Squeeze (Low Volatility)"
        elif current_width > avg_width * 1.3:
            return "Expansion (High Volatility)"
        else:
            return "Normal Volatility"
    
    def _no_signal(self, reason: str) -> BollingerSignal:
        """Return no signal result"""
        return BollingerSignal(
            signal_type=BollingerSignalType.HOLD,
            signal_strength=1,
            confidence=0.0,
            price_position="Unknown",
            volatility_state="Unknown",
            reasons=[reason],
            entry_price=0.0
        )
    
    def _hold_signal(self, price_position: str, volatility_state: str) -> BollingerSignal:
        """Return hold signal"""
        return BollingerSignal(
            signal_type=BollingerSignalType.HOLD,
            signal_strength=5,
            confidence=0.5,
            price_position=price_position,
            volatility_state=volatility_state,
            reasons=["No clear Bollinger Band signal - holding position"],
            entry_price=0.0
        )
    
    def format_txyzn_signal(self, signal: BollingerSignal) -> str:
        """Format signal as TXYZN string"""
        # Map signal types to TXYZN format
        signal_mapping = {
            BollingerSignalType.BOUNCE_BUY: f"BBOL{signal.signal_strength}",
            BollingerSignalType.BOUNCE_SELL: f"SBOS{signal.signal_strength}",
            BollingerSignalType.SQUEEZE_BREAK_UP: f"BBSU{signal.signal_strength}",
            BollingerSignalType.SQUEEZE_BREAK_DOWN: f"SBSD{signal.signal_strength}",
            BollingerSignalType.WALK_UP: f"BBWU{signal.signal_strength}",
            BollingerSignalType.WALK_DOWN: f"SBWD{signal.signal_strength}",
            BollingerSignalType.HOLD: f"HBOL{signal.signal_strength}"
        }
        
        return signal_mapping.get(signal.signal_type, f"HBOL{signal.signal_strength}")

# Example usage and testing
if __name__ == "__main__":
    # This would typically be called from the main strategy engine
    analyzer = BollingerBandAnalyzer(period=20, std_dev=2.0)
    print("Bollinger Band Strategy Analyzer initialized")
    print("Available strategies: BBOL (Bounce), BBSQ (Squeeze), BBWK (Walking)")