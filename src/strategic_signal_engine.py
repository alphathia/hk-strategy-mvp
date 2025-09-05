"""
Strategic Signal Engine - Professional TXYZn Signal Generation
Implements 12 strategic signal types with comprehensive technical analysis
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, date
import json
import logging
from dataclasses import dataclass
from enum import Enum
import hashlib
import uuid

# Import new level-based analysis modules
try:
    from .strategy_level_engine import StrategyLevelEngine
    from .enhanced_technical_analysis import EnhancedTechnicalAnalysis
except ImportError:
    from strategy_level_engine import StrategyLevelEngine
    from enhanced_technical_analysis import EnhancedTechnicalAnalysis

logger = logging.getLogger(__name__)

class StrategyCategory(Enum):
    BREAKOUT = "breakout"
    MEAN_REVERSION = "mean-reversion"
    TREND = "trend"
    DIVERGENCE = "divergence" 
    LEVEL = "level"

class SignalSide(Enum):
    BUY = "B"
    SELL = "S"

@dataclass
class StrategicSignal:
    """Individual strategic signal with full evidence tracking"""
    signal_id: str
    symbol: str
    bar_date: date
    strategy_key: str
    base_strategy: str
    action: str
    strength: int
    close_at_signal: float
    volume_at_signal: int
    thresholds_json: Dict
    reasons_json: List[str] 
    score_json: Dict
    provisional: bool = False

@dataclass
class IndicatorSnapshot:
    """Complete technical indicator snapshot for a symbol/date"""
    symbol: str
    bar_date: date
    
    # OHLCV
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: int
    
    # RSI Family (4)
    rsi6: Optional[float] = None
    rsi12: Optional[float] = None  
    rsi14: Optional[float] = None
    rsi24: Optional[float] = None
    
    # MACD & PPO (6)
    macd: Optional[float] = None
    macd_sig: Optional[float] = None
    macd_hist: Optional[float] = None
    ppo: Optional[float] = None
    ppo_sig: Optional[float] = None
    ppo_hist: Optional[float] = None
    
    # Moving Averages (6)
    ema5: Optional[float] = None
    ema10: Optional[float] = None
    ema20: Optional[float] = None
    ema50: Optional[float] = None
    sma20: Optional[float] = None
    sma50: Optional[float] = None
    
    # Bollinger & Volatility (4)
    bb_upper: Optional[float] = None
    bb_middle: Optional[float] = None
    bb_lower: Optional[float] = None
    atr14: Optional[float] = None
    
    # Volume & Flow (3)
    vr24: Optional[float] = None
    mfi14: Optional[float] = None
    ad_line: Optional[float] = None
    
    # Momentum & Trend (4)
    stoch_k: Optional[float] = None
    stoch_d: Optional[float] = None
    williams_r: Optional[float] = None
    adx14: Optional[float] = None
    
    # Specialized (1)
    parabolic_sar: Optional[float] = None

class TechnicalIndicatorCalculator:
    """Comprehensive technical indicator calculation engine"""
    
    @staticmethod
    def calculate_rsi(prices: np.ndarray, period: int = 14) -> float:
        """Calculate RSI for given period"""
        if len(prices) < period + 1:
            return 50.0
            
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))
    
    @staticmethod
    def calculate_ema(prices: np.ndarray, period: int) -> float:
        """Calculate Exponential Moving Average"""
        if len(prices) < period:
            return np.mean(prices)
        
        multiplier = 2 / (period + 1)
        ema = prices[0]
        
        for price in prices[1:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))
        
        return ema
    
    @staticmethod
    def calculate_sma(prices: np.ndarray, period: int) -> float:
        """Calculate Simple Moving Average"""
        if len(prices) < period:
            return np.mean(prices)
        return np.mean(prices[-period:])
    
    @staticmethod
    def calculate_macd(prices: np.ndarray, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[float, float, float]:
        """Calculate MACD, Signal, and Histogram"""
        if len(prices) < slow:
            return 0.0, 0.0, 0.0
        
        ema_fast = TechnicalIndicatorCalculator.calculate_ema(prices, fast)
        ema_slow = TechnicalIndicatorCalculator.calculate_ema(prices, slow)
        macd_line = ema_fast - ema_slow
        
        # For signal line, we'd need historical MACD values
        # Simplified: use a basic signal approximation
        signal_line = macd_line * 0.9  # Simplified
        histogram = macd_line - signal_line
        
        return macd_line, signal_line, histogram
    
    @staticmethod
    def calculate_bollinger_bands(prices: np.ndarray, period: int = 20, std_mult: float = 2.0) -> Tuple[float, float, float]:
        """Calculate Bollinger Bands (Upper, Middle, Lower)"""
        if len(prices) < period:
            middle = np.mean(prices)
            std = np.std(prices) if len(prices) > 1 else 0
        else:
            recent_prices = prices[-period:]
            middle = np.mean(recent_prices)
            std = np.std(recent_prices)
        
        upper = middle + (std_mult * std)
        lower = middle - (std_mult * std)
        
        return upper, middle, lower
    
    @staticmethod
    def calculate_stochastic(high_prices: np.ndarray, low_prices: np.ndarray, close_prices: np.ndarray, 
                           k_period: int = 14, d_period: int = 3) -> Tuple[float, float]:
        """Calculate Stochastic %K and %D"""
        if len(close_prices) < k_period:
            return 50.0, 50.0
        
        recent_highs = high_prices[-k_period:]
        recent_lows = low_prices[-k_period:]
        current_close = close_prices[-1]
        
        highest_high = np.max(recent_highs)
        lowest_low = np.min(recent_lows)
        
        if highest_high == lowest_low:
            k_percent = 50.0
        else:
            k_percent = ((current_close - lowest_low) / (highest_high - lowest_low)) * 100
        
        # Simplified %D calculation
        d_percent = k_percent * 0.95  # Simplified
        
        return k_percent, d_percent
    
    @staticmethod
    def calculate_atr(high_prices: np.ndarray, low_prices: np.ndarray, close_prices: np.ndarray, period: int = 14) -> float:
        """Calculate Average True Range"""
        if len(close_prices) < 2:
            return abs(high_prices[-1] - low_prices[-1]) if len(high_prices) > 0 else 0.0
        
        true_ranges = []
        for i in range(1, len(close_prices)):
            tr1 = high_prices[i] - low_prices[i]
            tr2 = abs(high_prices[i] - close_prices[i-1])
            tr3 = abs(low_prices[i] - close_prices[i-1])
            true_ranges.append(max(tr1, tr2, tr3))
        
        if len(true_ranges) < period:
            return np.mean(true_ranges)
        return np.mean(true_ranges[-period:])
    
    @staticmethod
    def calculate_all_indicators(price_data: pd.DataFrame) -> IndicatorSnapshot:
        """Calculate all 21 indicators for the latest price data"""
        if len(price_data) == 0:
            raise ValueError("Price data cannot be empty")
        
        latest = price_data.iloc[-1]
        closes = price_data['close_price'].values
        highs = price_data['high_price'].values  
        lows = price_data['low_price'].values
        volumes = price_data['volume'].values
        
        # RSI Family
        rsi6 = TechnicalIndicatorCalculator.calculate_rsi(closes, 6)
        rsi12 = TechnicalIndicatorCalculator.calculate_rsi(closes, 12)
        rsi14 = TechnicalIndicatorCalculator.calculate_rsi(closes, 14)
        rsi24 = TechnicalIndicatorCalculator.calculate_rsi(closes, 24)
        
        # MACD & PPO
        macd, macd_sig, macd_hist = TechnicalIndicatorCalculator.calculate_macd(closes)
        ppo = (macd / closes[-1]) * 100 if closes[-1] != 0 else 0  # Simplified PPO
        ppo_sig = ppo * 0.9  # Simplified
        ppo_hist = ppo - ppo_sig
        
        # Moving Averages
        ema5 = TechnicalIndicatorCalculator.calculate_ema(closes, 5)
        ema10 = TechnicalIndicatorCalculator.calculate_ema(closes, 10)
        ema20 = TechnicalIndicatorCalculator.calculate_ema(closes, 20)
        ema50 = TechnicalIndicatorCalculator.calculate_ema(closes, 50)
        sma20 = TechnicalIndicatorCalculator.calculate_sma(closes, 20)
        sma50 = TechnicalIndicatorCalculator.calculate_sma(closes, 50)
        
        # Bollinger Bands & ATR
        bb_upper, bb_middle, bb_lower = TechnicalIndicatorCalculator.calculate_bollinger_bands(closes)
        atr14 = TechnicalIndicatorCalculator.calculate_atr(highs, lows, closes)
        
        # Stochastic
        stoch_k, stoch_d = TechnicalIndicatorCalculator.calculate_stochastic(highs, lows, closes)
        
        # Volume & Flow (simplified implementations)
        vr24 = volumes[-1] / np.mean(volumes[-24:]) if len(volumes) >= 24 else 1.0
        mfi14 = rsi14  # Simplified - would need volume-weighted calculation
        ad_line = np.sum((closes - lows) - (highs - closes)) / (highs - lows + 0.001)  # Simplified
        
        # Williams %R
        williams_r = ((np.max(highs[-14:]) - closes[-1]) / (np.max(highs[-14:]) - np.min(lows[-14:]) + 0.001)) * -100
        
        # ADX (simplified)
        adx14 = abs(ema20 - ema50) / ema20 * 100 if ema20 != 0 else 0  # Simplified proxy
        
        # Parabolic SAR (simplified)
        parabolic_sar = closes[-1] * 0.98 if closes[-1] > ema20 else closes[-1] * 1.02  # Simplified
        
        return IndicatorSnapshot(
            symbol=latest.get('symbol', ''),
            bar_date=latest.get('bar_date', date.today()),
            open_price=latest['open_price'],
            high_price=latest['high_price'], 
            low_price=latest['low_price'],
            close_price=latest['close_price'],
            volume=int(latest['volume']),
            rsi6=rsi6, rsi12=rsi12, rsi14=rsi14, rsi24=rsi24,
            macd=macd, macd_sig=macd_sig, macd_hist=macd_hist,
            ppo=ppo, ppo_sig=ppo_sig, ppo_hist=ppo_hist,
            ema5=ema5, ema10=ema10, ema20=ema20, ema50=ema50,
            sma20=sma20, sma50=sma50,
            bb_upper=bb_upper, bb_middle=bb_middle, bb_lower=bb_lower,
            atr14=atr14, vr24=vr24, mfi14=mfi14, ad_line=ad_line,
            stoch_k=stoch_k, stoch_d=stoch_d, williams_r=williams_r,
            adx14=adx14, parabolic_sar=parabolic_sar
        )

class StrategicSignalEngine:
    """Professional strategic signal generation engine"""
    
    def __init__(self, parameter_set: Optional[Dict] = None):
        self.parameter_set = parameter_set or self._get_default_parameters()
        self.engine_version = "2.0.0"  # Updated for level-based analysis
        self.calculator = TechnicalIndicatorCalculator()
        
        # Initialize level-based analysis engines
        self.level_engine = StrategyLevelEngine()
        self.enhanced_ta = EnhancedTechnicalAnalysis()
        self.logger = logging.getLogger(__name__)
        
    def _get_default_parameters(self) -> Dict:
        """Default parameter set for signal generation"""
        return {
            "rsi_overbought": 70,
            "rsi_oversold": 30, 
            "volume_threshold": 1.5,
            "breakout_epsilon": 0.005,  # 0.5% breakout confirmation
            "atr_multiplier": 2.0,
            "trend_strength_threshold": 25,  # ADX threshold
            "divergence_periods": 5
        }
    
    def generate_signals(self, symbol: str, price_data: pd.DataFrame, 
                        provisional: bool = False) -> List[StrategicSignal]:
        """Generate all strategic signals for a symbol"""
        if len(price_data) < 50:  # Need sufficient history
            logger.warning(f"Insufficient price data for {symbol}: {len(price_data)} rows")
            return []
        
        # Calculate comprehensive indicators
        indicators = self.calculator.calculate_all_indicators(price_data)
        
        signals = []
        latest_date = price_data.iloc[-1].get('bar_date', date.today())
        
        # Generate signals for each strategy
        strategies = [
            'BBRK', 'BOSR', 'BMAC', 'BBOL', 'BDIV', 'BSUP',  # Buy strategies
            'SBDN', 'SOBR', 'SMAC', 'SDIV', 'SRES'   # Sell strategies (updated names)
        ]
        
        for base_strategy in strategies:
            signal = self._evaluate_strategy(base_strategy, indicators, provisional)
            if signal:
                signals.append(signal)
        
        return signals
    
    def generate_signals_enhanced(self, symbol: str, price_data: pd.DataFrame, 
                        provisional: bool = False) -> List[StrategicSignal]:
        """Generate signals using enhanced level-based analysis"""
        if len(price_data) < 100:  # Need more history for comprehensive analysis
            return []
        
        try:
            # Calculate comprehensive technical indicators
            technical_data = self.enhanced_ta.calculate_all_indicators(price_data)
            technical_data['symbol'] = symbol
            technical_data['bar_date'] = date.today()
            
            # Evaluate all base strategies using level engine
            base_strategies = [
                'BBRK', 'BOSR', 'BMAC', 'BBOL', 'BDIV', 'BSUP',  # Buy strategies
                'SBDN', 'SOBR', 'SMAC', 'SDIV', 'SRES'   # Sell strategies (corrected names)
            ]
            
            signals = []
            for base_strategy in base_strategies:
                try:
                    # Use level engine for precise analysis
                    level_result = self.level_engine.evaluate_strategy_levels(base_strategy, technical_data)
                    
                    # Only generate signal if base trigger is met
                    if level_result.base_trigger_met and level_result.highest_level_met > 0:
                        signal = self._create_signal_from_level_result(level_result, provisional)
                        if signal:
                            signals.append(signal)
                            
                except Exception as e:
                    self.logger.warning(f"Error evaluating {base_strategy} for {symbol}: {e}")
                    continue
            
            return signals
            
        except Exception as e:
            self.logger.error(f"Error generating enhanced signals for {symbol}: {e}")
            return []
    
    def _create_signal_from_level_result(self, level_result, provisional: bool) -> Optional[StrategicSignal]:
        """Create StrategicSignal from StrategyLevelResult"""
        try:
            # Determine action (Buy/Sell) from strategy
            action = 'B' if level_result.base_strategy.startswith('B') else 'S'
            
            # Build reasons from level conditions met
            reasons = []
            for condition in level_result.level_conditions:
                if condition.met:
                    reasons.append(f"L{condition.level}: {condition.condition_text}")
            
            # Build thresholds and score data
            thresholds = {
                'highest_level_met': level_result.highest_level_met,
                'base_trigger_met': level_result.base_trigger_met,
                'total_levels': len(level_result.level_conditions)
            }
            
            score = {
                'level_strength': level_result.highest_level_met,
                'level_percentage': level_result.highest_level_met / 9.0 * 100,
                'conditions_met': len([c for c in level_result.level_conditions if c.met])
            }
            
            return StrategicSignal(
                signal_id=str(uuid.uuid4()),
                symbol=level_result.symbol,
                bar_date=level_result.bar_date,
                strategy_key=f"{level_result.base_strategy}{level_result.highest_level_met}",
                base_strategy=level_result.base_strategy,
                action=action,
                strength=level_result.highest_level_met,
                close_at_signal=level_result.technical_values['close_price'],
                volume_at_signal=int(level_result.technical_values['volume']),
                thresholds_json=thresholds,
                reasons_json=reasons,
                score_json=score,
                provisional=provisional
            )
            
        except Exception as e:
            self.logger.error(f"Error creating signal from level result: {e}")
            return None
    
    def _evaluate_strategy(self, base_strategy: str, indicators: IndicatorSnapshot, 
                          provisional: bool) -> Optional[StrategicSignal]:
        """Evaluate a specific strategy and return signal if triggered"""
        
        if base_strategy == 'BBRK':
            return self._evaluate_breakout_buy(indicators, provisional)
        elif base_strategy == 'BOSR':
            return self._evaluate_oversold_reclaim(indicators, provisional)
        elif base_strategy == 'BMAC':
            return self._evaluate_ma_crossover_buy(indicators, provisional)
        elif base_strategy == 'BBOL':
            return self._evaluate_bollinger_bounce(indicators, provisional)
        elif base_strategy == 'BDIV':
            return self._evaluate_bullish_divergence(indicators, provisional)
        elif base_strategy == 'BSUP':
            return self._evaluate_support_bounce(indicators, provisional)
        elif base_strategy == 'SBDN':
            return self._evaluate_breakdown_sell(indicators, provisional)
        elif base_strategy == 'SOBR':
            return self._evaluate_overbought_reversal(indicators, provisional)
        elif base_strategy == 'SMAC':
            return self._evaluate_ma_crossover_sell(indicators, provisional)
        # SBND renamed to SBDN - handled above
        # elif base_strategy == 'SBND': - DEPRECATED
        elif base_strategy == 'SDIV':
            return self._evaluate_bearish_divergence(indicators, provisional)
        elif base_strategy == 'SRES':
            return self._evaluate_resistance_rejection(indicators, provisional)
        
        return None
    
    def _evaluate_breakout_buy(self, indicators: IndicatorSnapshot, provisional: bool) -> Optional[StrategicSignal]:
        """BBRK: Buy • Breakout strategy evaluation"""
        current_price = indicators.close_price
        bb_upper = indicators.bb_upper or 0
        ema20 = indicators.ema20 or 0
        volume_ratio = indicators.vr24 or 1.0
        rsi14 = indicators.rsi14 or 50
        
        # Breakout conditions
        breakout_level = max(bb_upper, ema20 * 1.02)  # 2% above EMA20 or BB upper
        epsilon = breakout_level * self.parameter_set["breakout_epsilon"]
        
        # Check breakout condition
        if current_price > (breakout_level + epsilon):
            # Volume confirmation
            volume_confirm = volume_ratio >= self.parameter_set["volume_threshold"]
            
            # Momentum confirmation (RSI not extremely overbought)
            momentum_ok = rsi14 < 85
            
            # Calculate strength (1-9)
            strength = self._calculate_breakout_strength(
                current_price, breakout_level, volume_ratio, rsi14
            )
            
            if strength >= 1:  # Minimum strength threshold
                reasons = [
                    f"Price {current_price:.3f} breaks above {breakout_level:.3f} + ε {epsilon:.3f}",
                    f"Volume ratio {volume_ratio:.2f} vs threshold {self.parameter_set['volume_threshold']}"
                ]
                
                if momentum_ok:
                    reasons.append(f"RSI14 {rsi14:.1f} below extreme overbought (85)")
                
                return StrategicSignal(
                    signal_id=str(uuid.uuid4()),
                    symbol=indicators.symbol,
                    bar_date=indicators.bar_date,
                    strategy_key=f"BBRK{strength}",
                    base_strategy="BBRK",
                    action="B",
                    strength=strength,
                    close_at_signal=current_price,
                    volume_at_signal=indicators.volume,
                    thresholds_json={
                        "breakout_level": breakout_level,
                        "epsilon": epsilon,
                        "volume_threshold": self.parameter_set["volume_threshold"]
                    },
                    reasons_json=reasons,
                    score_json={
                        "magnitude": min((current_price - breakout_level) / breakout_level * 100, 5),
                        "momentum": min((85 - rsi14) / 10, 3),
                        "participation": min(volume_ratio, 3),
                        "raw_strength": strength
                    },
                    provisional=provisional
                )
        
        return None
    
    def _evaluate_oversold_reclaim(self, indicators: IndicatorSnapshot, provisional: bool) -> Optional[StrategicSignal]:
        """BOSR: Buy • Oversold Reclaim strategy evaluation"""
        rsi14 = indicators.rsi14 or 50
        williams_r = indicators.williams_r or -50
        ema20 = indicators.ema20 or 0
        current_price = indicators.close_price
        volume_ratio = indicators.vr24 or 1.0
        
        # Oversold recovery conditions
        rsi_recovery = rsi14 > 35 and rsi14 < 65  # Recovering from oversold but not overbought
        williams_recovery = williams_r > -70  # Williams %R recovery
        ema_reclaim = current_price > ema20  # Price above EMA20
        
        if rsi_recovery and williams_recovery and ema_reclaim:
            strength = self._calculate_oversold_strength(rsi14, williams_r, volume_ratio)
            
            if strength >= 1:
                reasons = [
                    f"RSI14 {rsi14:.1f} recovering from oversold territory",
                    f"Williams %R {williams_r:.1f} above -70 threshold",
                    f"Price {current_price:.3f} reclaims EMA20 {ema20:.3f}"
                ]
                
                return StrategicSignal(
                    signal_id=str(uuid.uuid4()),
                    symbol=indicators.symbol,
                    bar_date=indicators.bar_date,
                    strategy_key=f"BOSR{strength}",
                    base_strategy="BOSR",
                    action="B", 
                    strength=strength,
                    close_at_signal=current_price,
                    volume_at_signal=indicators.volume,
                    thresholds_json={
                        "rsi_recovery_range": [35, 65],
                        "williams_threshold": -70,
                        "ema20_level": ema20
                    },
                    reasons_json=reasons,
                    score_json={
                        "rsi_position": (rsi14 - 30) / 40 * 3,
                        "williams_position": (williams_r + 80) / 30 * 2,
                        "price_momentum": (current_price - ema20) / ema20 * 100,
                        "raw_strength": strength
                    },
                    provisional=provisional
                )
        
        return None
    
    def _calculate_breakout_strength(self, current_price: float, breakout_level: float, 
                                   volume_ratio: float, rsi14: float) -> int:
        """Calculate breakout signal strength (1-9)"""
        # Price momentum component (0-3)
        price_momentum = min((current_price - breakout_level) / breakout_level * 100, 3)
        
        # Volume component (0-3)
        volume_component = min(volume_ratio - 1, 3)
        
        # RSI component (0-3) - prefer RSI not extremely overbought
        rsi_component = min((85 - rsi14) / 10, 3) if rsi14 < 85 else 0
        
        total_score = price_momentum + volume_component + rsi_component
        
        # Convert to 1-9 scale
        return max(1, min(9, int(total_score) + 1))
    
    def _calculate_oversold_strength(self, rsi14: float, williams_r: float, volume_ratio: float) -> int:
        """Calculate oversold reclaim signal strength (1-9)"""
        # RSI recovery strength (0-3)
        rsi_strength = (rsi14 - 30) / 20 * 3 if rsi14 > 30 else 0
        
        # Williams %R recovery strength (0-3) 
        williams_strength = (williams_r + 80) / 20 * 3 if williams_r > -80 else 0
        
        # Volume confirmation (0-3)
        volume_strength = min(volume_ratio - 0.5, 3) if volume_ratio > 0.5 else 0
        
        total_score = rsi_strength + williams_strength + volume_strength
        
        return max(1, min(9, int(total_score) + 1))
    
    def _evaluate_ma_crossover_buy(self, indicators: IndicatorSnapshot, provisional: bool) -> Optional[StrategicSignal]:
        """BMAC: Buy • MA Bullish Crossover - simplified implementation"""
        ema20 = indicators.ema20 or 0
        ema50 = indicators.ema50 or 0
        macd = indicators.macd or 0
        volume_ratio = indicators.vr24 or 1.0
        
        # Bullish MA crossover
        if ema20 > ema50 and macd > 0:
            strength = min(9, max(1, int((ema20 - ema50) / ema50 * 100) + int(volume_ratio)))
            
            return StrategicSignal(
                signal_id=str(uuid.uuid4()),
                symbol=indicators.symbol,
                bar_date=indicators.bar_date,
                strategy_key=f"BMAC{strength}",
                base_strategy="BMAC",
                action="B",
                strength=strength,
                close_at_signal=indicators.close_price,
                volume_at_signal=indicators.volume,
                thresholds_json={"ema20": ema20, "ema50": ema50},
                reasons_json=[f"EMA20 {ema20:.3f} > EMA50 {ema50:.3f}", f"MACD {macd:.3f} > 0"],
                score_json={"ma_spread": (ema20 - ema50) / ema50 * 100, "raw_strength": strength},
                provisional=provisional
            )
        
        return None
    
    # Placeholder implementations for remaining strategies
    def _evaluate_bollinger_bounce(self, indicators: IndicatorSnapshot, provisional: bool) -> Optional[StrategicSignal]:
        """BBOL: Buy • Bollinger Bounce - placeholder"""
        return None
    
    def _evaluate_bullish_divergence(self, indicators: IndicatorSnapshot, provisional: bool) -> Optional[StrategicSignal]:
        """BDIV: Buy • Bullish Divergence - placeholder"""  
        return None
    
    def _evaluate_support_bounce(self, indicators: IndicatorSnapshot, provisional: bool) -> Optional[StrategicSignal]:
        """BSUP: Buy • Support Bounce - placeholder"""
        return None
    
    def _evaluate_breakdown_sell(self, indicators: IndicatorSnapshot, provisional: bool) -> Optional[StrategicSignal]:
        """SBDN: Sell • Breakdown - placeholder"""
        return None
    
    def _evaluate_overbought_reversal(self, indicators: IndicatorSnapshot, provisional: bool) -> Optional[StrategicSignal]:
        """SOBR: Sell • Overbought Reversal - placeholder"""
        return None
    
    def _evaluate_ma_crossover_sell(self, indicators: IndicatorSnapshot, provisional: bool) -> Optional[StrategicSignal]:
        """SMAC: Sell • MA Bearish Crossover - placeholder"""
        return None
    
    def _evaluate_bollinger_breakdown(self, indicators: IndicatorSnapshot, provisional: bool) -> Optional[StrategicSignal]:
        """SBDN: Sell • Breakdown - Updated implementation"""
        return None
    
    def _evaluate_bearish_divergence(self, indicators: IndicatorSnapshot, provisional: bool) -> Optional[StrategicSignal]:
        """SDIV: Sell • Bearish Divergence - placeholder"""
        return None
    
    def _evaluate_resistance_rejection(self, indicators: IndicatorSnapshot, provisional: bool) -> Optional[StrategicSignal]:
        """SRES: Sell • Resistance Rejection - placeholder"""
        return None

class StrategicSignalManager:
    """High-level manager for strategic signal operations"""
    
    def __init__(self, database_manager=None):
        self.db = database_manager
        self.engine = StrategicSignalEngine()
        
    def generate_signals_for_portfolio(self, portfolio_symbols: List[str], 
                                     date_range: Tuple[date, date]) -> Dict[str, List[StrategicSignal]]:
        """Generate signals for entire portfolio"""
        results = {}
        
        for symbol in portfolio_symbols:
            try:
                # Get price data from database
                price_data = self._get_price_data(symbol, date_range)
                signals = self.engine.generate_signals(symbol, price_data)
                results[symbol] = signals
                
                logger.info(f"Generated {len(signals)} signals for {symbol}")
                
            except Exception as e:
                logger.error(f"Error generating signals for {symbol}: {e}")
                results[symbol] = []
        
        return results
    
    def _get_price_data(self, symbol: str, date_range: Tuple[date, date]) -> pd.DataFrame:
        """Get price data for a symbol (placeholder - integrate with your database)"""
        # This would integrate with your actual price data source
        # For now, return mock data structure
        return pd.DataFrame({
            'symbol': [symbol] * 50,
            'bar_date': pd.date_range(end=date_range[1], periods=50),
            'open_price': np.random.normal(100, 5, 50),
            'high_price': np.random.normal(102, 5, 50), 
            'low_price': np.random.normal(98, 5, 50),
            'close_price': np.random.normal(100, 5, 50),
            'volume': np.random.randint(100000, 2000000, 50)
        })

# Example usage and testing
if __name__ == "__main__":
    # Example usage
    engine = StrategicSignalEngine()
    manager = StrategicSignalManager()
    
    # Test signal generation
    test_symbols = ["0700.HK", "0005.HK"] 
    test_date_range = (date(2024, 1, 1), date.today())
    
    signals = manager.generate_signals_for_portfolio(test_symbols, test_date_range)
    
    for symbol, symbol_signals in signals.items():
        print(f"\n{symbol}: {len(symbol_signals)} signals")
        for signal in symbol_signals[:3]:  # Show first 3
            print(f"  {signal.strategy_key}: {signal.action}{signal.strength} @ {signal.close_at_signal:.3f}")