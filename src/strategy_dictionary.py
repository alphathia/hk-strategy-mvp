"""
Strategy Dictionary - Centralized Strategy Management System
Comprehensive metadata and management for all TXYZn strategic signals
"""

from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
import re
import json

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
class StrategyMetadata:
    """Complete metadata for a strategic signal strategy"""
    base_strategy: str
    side: SignalSide
    name_template: str
    description_template: str
    category: StrategyCategory
    
    # Technical requirements
    required_indicators: List[str]
    optional_indicators: List[str]
    
    # Parameter requirements
    default_parameters: Dict[str, Any]
    parameter_ranges: Dict[str, Tuple[float, float]]
    
    # Validation rules
    min_price_history_days: int
    supports_provisional: bool
    
    # Documentation
    detailed_explanation: str
    usage_guidelines: str
    risk_considerations: str
    market_conditions: List[str]  # ["trending", "ranging", "volatile", "stable"]
    
    # Implementation details
    implementation_complexity: str  # "simple", "moderate", "complex"
    computational_cost: str  # "low", "medium", "high"
    
    # Display properties
    color_scheme: Dict[str, str]  # Colors for different strength levels
    icon: str  # Icon identifier for UI
    priority: int  # Display priority (1=highest)

class StrategyDictionary:
    """
    Centralized strategy dictionary with comprehensive metadata
    for all TXYZn strategic signals
    """
    
    # ==============================================
    # Base Strategy Definitions
    # ==============================================
    
    BASE_STRATEGIES = {
        "BBRK": StrategyMetadata(
            base_strategy="BBRK",
            side=SignalSide.BUY,
            name_template="Buy • Breakout ({strength})",
            description_template="Break above {level} with {volume} volume {momentum}",
            category=StrategyCategory.BREAKOUT,
            
            required_indicators=["bb_upper", "ema20", "close_price", "volume"],
            optional_indicators=["rsi14", "adx14", "atr14", "vr24"],
            
            default_parameters={
                "breakout_epsilon": 0.005,  # 0.5% breakout confirmation
                "volume_threshold": 1.5,    # 1.5x average volume
                "rsi_max": 85,             # Max RSI to avoid extreme overbought
                "atr_multiplier": 2.0      # ATR multiplier for dynamic stops
            },
            
            parameter_ranges={
                "breakout_epsilon": (0.001, 0.02),   # 0.1% to 2%
                "volume_threshold": (1.0, 5.0),      # 1x to 5x volume
                "rsi_max": (70, 95),                  # 70 to 95 RSI
                "atr_multiplier": (1.0, 4.0)         # 1x to 4x ATR
            },
            
            min_price_history_days=50,
            supports_provisional=True,
            
            detailed_explanation="""
            Breakout strategy identifies when price breaks above key resistance levels 
            with confirmation from volume and momentum indicators. Looks for breaks 
            above 20-day highs, Bollinger Band upper, or EMA20 resistance.
            
            Strength scoring considers:
            - Magnitude of breakout above resistance
            - Volume confirmation (VR > threshold)
            - Momentum confirmation (RSI not extremely overbought)
            - Multiple timeframe alignment
            """,
            
            usage_guidelines="""
            Best used in:
            - Trending markets with clear resistance levels
            - After consolidation periods
            - With volume confirmation
            
            Avoid in:
            - Choppy, ranging markets
            - When volume is very low
            - During major news events without confirmation
            """,
            
            risk_considerations="""
            - False breakouts are common
            - Requires volume confirmation
            - Can give late signals in fast moves
            - Use proper stop losses (ATR-based)
            """,
            
            market_conditions=["trending", "volatile"],
            
            implementation_complexity="moderate",
            computational_cost="medium",
            
            color_scheme={
                "1-3": "#90EE90",  # Light green for weak
                "4-6": "#32CD32",  # Lime green for moderate  
                "7-9": "#006400"   # Dark green for strong
            },
            
            icon="trend-up",
            priority=1
        ),
        
        "BOSR": StrategyMetadata(
            base_strategy="BOSR",
            side=SignalSide.BUY,
            name_template="Buy • Oversold Reclaim ({strength})",
            description_template="RSI/Williams recovery with EMA20 reclaim {confirmation}",
            category=StrategyCategory.MEAN_REVERSION,
            
            required_indicators=["rsi14", "williams_r", "ema20", "close_price"],
            optional_indicators=["rsi6", "rsi12", "stoch_k", "stoch_d", "volume"],
            
            default_parameters={
                "rsi_oversold": 30,
                "rsi_recovery_min": 35,
                "rsi_recovery_max": 65,
                "williams_threshold": -70,
                "volume_confirmation": 1.2
            },
            
            parameter_ranges={
                "rsi_oversold": (20, 35),
                "rsi_recovery_min": (30, 40),
                "rsi_recovery_max": (60, 75),
                "williams_threshold": (-80, -60),
                "volume_confirmation": (0.8, 3.0)
            },
            
            min_price_history_days=30,
            supports_provisional=True,
            
            detailed_explanation="""
            Mean reversion strategy that identifies oversold conditions followed by
            recovery signals. Looks for RSI and Williams %R crossing back above
            oversold levels while price reclaims key moving averages.
            
            Strength scoring considers:
            - Depth of oversold condition
            - Speed of recovery
            - Moving average reclaim
            - Volume confirmation
            """,
            
            usage_guidelines="""
            Best used in:
            - Ranging or sideways markets
            - After sharp selloffs
            - Near support levels
            
            Avoid in:
            - Strong downtrends
            - During fundamental deterioration
            - Without clear support levels
            """,
            
            risk_considerations="""
            - Can catch falling knives
            - May signal too early in strong downtrends
            - Requires confirmation from multiple indicators
            - Use tight stops below support
            """,
            
            market_conditions=["ranging", "stable"],
            
            implementation_complexity="moderate",
            computational_cost="low",
            
            color_scheme={
                "1-3": "#FFB6C1",  # Light pink for weak
                "4-6": "#FF69B4",  # Hot pink for moderate
                "7-9": "#DC143C"   # Crimson for strong
            },
            
            icon="arrow-up-circle",
            priority=2
        ),
        
        "BMAC": StrategyMetadata(
            base_strategy="BMAC", 
            side=SignalSide.BUY,
            name_template="Buy • MA Crossover ({strength})",
            description_template="EMA20 crosses above EMA50 with {momentum} momentum",
            category=StrategyCategory.TREND,
            
            required_indicators=["ema20", "ema50", "macd", "close_price"],
            optional_indicators=["ema5", "ema10", "ppo", "adx14", "volume"],
            
            default_parameters={
                "ma_separation_min": 0.01,  # 1% minimum separation
                "macd_confirmation": True,
                "volume_threshold": 1.2,
                "trend_strength_min": 20    # ADX minimum
            },
            
            parameter_ranges={
                "ma_separation_min": (0.005, 0.03),
                "volume_threshold": (0.8, 2.5),
                "trend_strength_min": (15, 30)
            },
            
            min_price_history_days=60,
            supports_provisional=True,
            
            detailed_explanation="""
            Classic trend-following strategy based on moving average crossovers.
            Generates buy signals when faster EMA crosses above slower EMA with
            momentum confirmation from MACD and volume.
            
            Strength scoring considers:
            - Speed and magnitude of crossover
            - MACD confirmation
            - Volume participation
            - Trend strength (ADX)
            """,
            
            usage_guidelines="""
            Best used in:
            - Trending markets
            - After consolidation breakouts
            - With clear directional bias
            
            Avoid in:
            - Choppy, whipsaw markets
            - During major reversals
            - Without volume confirmation
            """,
            
            risk_considerations="""
            - Can give late signals
            - Prone to whipsaws in ranging markets
            - Requires trend confirmation
            - Use trend-following stops
            """,
            
            market_conditions=["trending"],
            
            implementation_complexity="simple",
            computational_cost="low",
            
            color_scheme={
                "1-3": "#87CEEB",  # Sky blue for weak
                "4-6": "#4169E1",  # Royal blue for moderate
                "7-9": "#000080"   # Navy for strong
            },
            
            icon="trending-up",
            priority=3
        ),
        
        "BBOL": StrategyMetadata(
            base_strategy="BBOL",
            side=SignalSide.BUY,
            name_template="Buy • Bollinger Bounce ({strength})",
            description_template="Bounce from lower Bollinger Band with {momentum}",
            category=StrategyCategory.MEAN_REVERSION,
            
            required_indicators=["bb_lower", "bb_middle", "close_price", "rsi14"],
            optional_indicators=["bb_upper", "stoch_k", "williams_r", "volume"],
            
            default_parameters={
                "bb_touch_tolerance": 0.002,  # 0.2% tolerance for "touching" band
                "rsi_oversold_threshold": 35,
                "bounce_confirmation": 0.005, # 0.5% bounce confirmation
                "volume_threshold": 1.1
            },
            
            parameter_ranges={
                "bb_touch_tolerance": (0.001, 0.01),
                "rsi_oversold_threshold": (25, 40),
                "bounce_confirmation": (0.002, 0.02),
                "volume_threshold": (0.8, 2.0)
            },
            
            min_price_history_days=25,
            supports_provisional=True,
            
            detailed_explanation="""
            Mean reversion strategy focusing on Bollinger Band dynamics. Identifies
            when price touches or penetrates the lower band and then shows signs
            of bouncing back toward the middle band.
            
            Strength scoring considers:
            - Distance below lower band
            - Speed of bounce recovery
            - RSI oversold confirmation
            - Volume on bounce
            """,
            
            usage_guidelines="""
            Best used in:
            - Ranging, sideways markets
            - Normal volatility environments
            - With RSI oversold confirmation
            
            Avoid in:
            - Strong trending markets
            - High volatility periods
            - During breakdown scenarios
            """,
            
            risk_considerations="""
            - Bands can expand during volatility
            - May signal too early in downtrends
            - Requires volatility context
            - Use BB middle as initial target
            """,
            
            market_conditions=["ranging", "stable"],
            
            implementation_complexity="simple",
            computational_cost="low",
            
            color_scheme={
                "1-3": "#DDA0DD",  # Plum for weak
                "4-6": "#9370DB",  # Medium orchid for moderate  
                "7-9": "#4B0082"   # Indigo for strong
            },
            
            icon="arrow-bounce-up",
            priority=4
        ),
        
        "BDIV": StrategyMetadata(
            base_strategy="BDIV",
            side=SignalSide.BUY,
            name_template="Buy • Bullish Divergence ({strength})",
            description_template="Price vs {indicator} bullish divergence with {confirmation}",
            category=StrategyCategory.DIVERGENCE,
            
            required_indicators=["rsi14", "macd", "close_price"],
            optional_indicators=["rsi12", "ppo", "stoch_k", "mfi14"],
            
            default_parameters={
                "lookback_periods": 5,
                "divergence_threshold": 0.02,  # 2% price vs indicator divergence
                "confirmation_periods": 3,
                "multiple_indicator_bonus": 1.5
            },
            
            parameter_ranges={
                "lookback_periods": (3, 10),
                "divergence_threshold": (0.01, 0.05),
                "confirmation_periods": (1, 5),
                "multiple_indicator_bonus": (1.0, 2.0)
            },
            
            min_price_history_days=40,
            supports_provisional=False,  # Requires historical confirmation
            
            detailed_explanation="""
            Advanced pattern recognition strategy that identifies divergences between
            price action and momentum indicators. Looks for lower lows in price
            accompanied by higher lows in RSI, MACD, or other oscillators.
            
            Strength scoring considers:
            - Magnitude of divergence
            - Multiple indicator confirmation
            - Duration of divergence pattern
            - Subsequent price confirmation
            """,
            
            usage_guidelines="""
            Best used in:
            - Established trends showing fatigue
            - After significant moves
            - With multiple indicator confirmation
            
            Avoid in:
            - Strong trending environments
            - Without clear divergence patterns
            - In highly volatile conditions
            """,
            
            risk_considerations="""
            - Divergences can continue longer than expected
            - Requires patience and confirmation
            - May signal early in strong trends
            - Use conservative position sizing
            """,
            
            market_conditions=["ranging", "volatile"],
            
            implementation_complexity="complex",
            computational_cost="high",
            
            color_scheme={
                "1-3": "#F0E68C",  # Khaki for weak
                "4-6": "#FFD700",  # Gold for moderate
                "7-9": "#FF8C00"   # Dark orange for strong
            },
            
            icon="git-branch",
            priority=5
        ),
        
        "BSUP": StrategyMetadata(
            base_strategy="BSUP",
            side=SignalSide.BUY, 
            name_template="Buy • Support Bounce ({strength})",
            description_template="Bounce from {support_level} support with {confirmation}",
            category=StrategyCategory.LEVEL,
            
            required_indicators=["close_price", "low_price", "volume"],
            optional_indicators=["sma20", "sma50", "rsi14", "atr14"],
            
            default_parameters={
                "support_touch_tolerance": 0.01,   # 1% tolerance for support test
                "bounce_confirmation": 0.005,      # 0.5% bounce to confirm
                "volume_threshold": 1.3,           # Volume confirmation
                "support_strength_periods": 20     # Periods to determine support strength
            },
            
            parameter_ranges={
                "support_touch_tolerance": (0.005, 0.02),
                "bounce_confirmation": (0.002, 0.015),
                "volume_threshold": (1.0, 3.0),
                "support_strength_periods": (10, 50)
            },
            
            min_price_history_days=60,
            supports_provisional=True,
            
            detailed_explanation="""
            Level-based strategy that identifies bounces from established support
            levels. Calculates dynamic support based on recent lows and identifies
            when price tests and bounces from these levels with volume confirmation.
            
            Strength scoring considers:
            - Number of previous tests at support level
            - Volume on bounce vs average
            - Speed and magnitude of bounce
            - Distance from support when signal triggers
            """,
            
            usage_guidelines="""
            Best used in:
            - Markets with clear support/resistance structure
            - After pullbacks in uptrends
            - With volume confirmation on bounce
            
            Avoid in:
            - Markets without clear levels
            - During breakdown scenarios
            - Without volume participation
            """,
            
            risk_considerations="""
            - Support levels can break
            - Requires strict stop below support
            - May give false signals on weak bounces
            - Consider market context and trend
            """,
            
            market_conditions=["ranging", "trending"],
            
            implementation_complexity="moderate",
            computational_cost="medium",
            
            color_scheme={
                "1-3": "#98FB98",  # Pale green for weak
                "4-6": "#32CD32",  # Lime green for moderate
                "7-9": "#228B22"   # Forest green for strong
            },
            
            icon="arrow-up-from-line",
            priority=6
        ),
        
        # SELL STRATEGIES
        
        "SBDN": StrategyMetadata(
            base_strategy="SBDN",
            side=SignalSide.SELL,
            name_template="Sell • Breakdown ({strength})",
            description_template="Break below {level} with {volume} volume {momentum}",
            category=StrategyCategory.BREAKOUT,
            
            required_indicators=["bb_lower", "ema20", "close_price", "volume"],
            optional_indicators=["rsi14", "adx14", "atr14", "vr24"],
            
            default_parameters={
                "breakdown_epsilon": 0.005,
                "volume_threshold": 1.5,
                "rsi_min": 15,
                "atr_multiplier": 2.0
            },
            
            parameter_ranges={
                "breakdown_epsilon": (0.001, 0.02),
                "volume_threshold": (1.0, 5.0),
                "rsi_min": (5, 30),
                "atr_multiplier": (1.0, 4.0)
            },
            
            min_price_history_days=50,
            supports_provisional=True,
            
            detailed_explanation="""
            Bearish breakout strategy identifying breaks below key support levels.
            Mirror image of BBRK strategy, looking for breaks below 20-day lows,
            Bollinger Band lower, or EMA20 support with volume confirmation.
            """,
            
            usage_guidelines="""Best used in downtrends, after distribution, with volume confirmation""",
            risk_considerations="""False breakdowns possible, use volume confirmation, tight stops above resistance""",
            market_conditions=["trending", "volatile"],
            
            implementation_complexity="moderate",
            computational_cost="medium",
            
            color_scheme={
                "1-3": "#FFB6C1",  # Light pink for weak
                "4-6": "#FF1493",  # Deep pink for moderate
                "7-9": "#DC143C"   # Crimson for strong
            },
            
            icon="trend-down",
            priority=7
        ),
        
        "SOBR": StrategyMetadata(
            base_strategy="SOBR",
            side=SignalSide.SELL,
            name_template="Sell • Overbought Reversal ({strength})",  
            description_template="Reversal from overbought with {confirmation}",
            category=StrategyCategory.MEAN_REVERSION,
            
            required_indicators=["rsi14", "close_price", "ema20"],
            optional_indicators=["williams_r", "stoch_k", "mfi14"],
            
            default_parameters={
                "rsi_overbought": 70,
                "rsi_reversal_max": 65,
                "volume_threshold": 1.2
            },
            
            parameter_ranges={
                "rsi_overbought": (65, 80),
                "rsi_reversal_max": (60, 70),
                "volume_threshold": (0.8, 2.0)
            },
            
            min_price_history_days=30,
            supports_provisional=True,
            
            detailed_explanation="""Mean reversion sell strategy for overbought reversals""",
            usage_guidelines="""Best in ranging markets, at resistance, with momentum confirmation""",
            risk_considerations="""Can fight strong uptrends, requires confirmation, use resistance as stops""",
            market_conditions=["ranging", "stable"],
            
            implementation_complexity="moderate", 
            computational_cost="low",
            
            color_scheme={
                "1-3": "#FFA07A",  # Light salmon
                "4-6": "#FF6347",  # Tomato  
                "7-9": "#B22222"   # Fire brick
            },
            
            icon="arrow-down-circle",
            priority=8
        ),
        
        "SMAC": StrategyMetadata(
            base_strategy="SMAC",
            side=SignalSide.SELL,
            name_template="Sell • MA Crossover ({strength})",
            description_template="EMA20 crosses below EMA50 with {momentum}",
            category=StrategyCategory.TREND,
            
            required_indicators=["ema20", "ema50", "macd"],
            optional_indicators=["ppo", "adx14", "volume"],
            
            default_parameters={
                "ma_separation_min": 0.01,
                "macd_confirmation": True,
                "volume_threshold": 1.2
            },
            
            parameter_ranges={
                "ma_separation_min": (0.005, 0.03),
                "volume_threshold": (0.8, 2.5)
            },
            
            min_price_history_days=60,
            supports_provisional=True,
            
            detailed_explanation="""Trend-following sell strategy based on bearish MA crossover""",
            usage_guidelines="""Best in downtrending markets, with MACD confirmation""",
            risk_considerations="""Late signals, whipsaws in ranging markets""",
            market_conditions=["trending"],
            
            implementation_complexity="simple",
            computational_cost="low",
            
            color_scheme={
                "1-3": "#CD5C5C",  # Indian red
                "4-6": "#B22222",  # Fire brick
                "7-9": "#800000"   # Maroon
            },
            
            icon="trending-down", 
            priority=9
        ),
        
        "SBND": StrategyMetadata(
            base_strategy="SBND",
            side=SignalSide.SELL,
            name_template="Sell • Bollinger Breakdown ({strength})",
            description_template="Break below lower Bollinger with {momentum}",
            category=StrategyCategory.BREAKOUT,
            
            required_indicators=["bb_lower", "close_price", "volume"],
            optional_indicators=["bb_middle", "rsi14", "atr14"],
            
            default_parameters={
                "breakdown_confirmation": 0.005,
                "volume_threshold": 1.3,
                "rsi_threshold": 45
            },
            
            parameter_ranges={
                "breakdown_confirmation": (0.002, 0.015),
                "volume_threshold": (1.0, 3.0),
                "rsi_threshold": (35, 55)
            },
            
            min_price_history_days=25,
            supports_provisional=True,
            
            detailed_explanation="""Breakdown strategy below lower Bollinger Band""",
            usage_guidelines="""Best with volume confirmation, in trending down markets""",
            risk_considerations="""Bands can contract, may reverse quickly""",
            market_conditions=["trending", "volatile"],
            
            implementation_complexity="simple",
            computational_cost="low",
            
            color_scheme={
                "1-3": "#DDA0DD",  # Plum (inverted)
                "4-6": "#8B008B",  # Dark magenta
                "7-9": "#4B0082"   # Indigo
            },
            
            icon="arrow-down-through-line",
            priority=10
        ),
        
        "SDIV": StrategyMetadata(
            base_strategy="SDIV", 
            side=SignalSide.SELL,
            name_template="Sell • Bearish Divergence ({strength})",
            description_template="Price vs {indicator} bearish divergence",
            category=StrategyCategory.DIVERGENCE,
            
            required_indicators=["rsi14", "macd", "close_price"],
            optional_indicators=["ppo", "stoch_k", "mfi14"],
            
            default_parameters={
                "lookback_periods": 5,
                "divergence_threshold": 0.02,
                "confirmation_periods": 3
            },
            
            parameter_ranges={
                "lookback_periods": (3, 10),
                "divergence_threshold": (0.01, 0.05),
                "confirmation_periods": (1, 5)
            },
            
            min_price_history_days=40,
            supports_provisional=False,
            
            detailed_explanation="""Bearish divergence pattern recognition""",
            usage_guidelines="""Best after significant up moves, with confirmation""",
            risk_considerations="""Divergences can persist, requires patience""",
            market_conditions=["ranging", "volatile"],
            
            implementation_complexity="complex",
            computational_cost="high",
            
            color_scheme={
                "1-3": "#F4A460",  # Sandy brown
                "4-6": "#CD853F",  # Peru
                "7-9": "#A0522D"   # Sienna
            },
            
            icon="git-merge",
            priority=11
        ),
        
        "SRES": StrategyMetadata(
            base_strategy="SRES",
            side=SignalSide.SELL,
            name_template="Sell • Resistance Rejection ({strength})", 
            description_template="Rejection at {resistance_level} with {confirmation}",
            category=StrategyCategory.LEVEL,
            
            required_indicators=["close_price", "high_price", "volume"],
            optional_indicators=["sma20", "sma50", "rsi14"],
            
            default_parameters={
                "resistance_touch_tolerance": 0.01,
                "rejection_confirmation": 0.005,
                "volume_threshold": 1.3
            },
            
            parameter_ranges={
                "resistance_touch_tolerance": (0.005, 0.02),
                "rejection_confirmation": (0.002, 0.015),
                "volume_threshold": (1.0, 3.0)
            },
            
            min_price_history_days=60,
            supports_provisional=True,
            
            detailed_explanation="""Resistance level rejection strategy""",
            usage_guidelines="""Best at established resistance with volume""",
            risk_considerations="""Resistance can break, use stops above resistance""",
            market_conditions=["ranging", "trending"],
            
            implementation_complexity="moderate",
            computational_cost="medium",
            
            color_scheme={
                "1-3": "#F08080",  # Light coral
                "4-6": "#DC143C",  # Crimson
                "7-9": "#8B0000"   # Dark red
            },
            
            icon="arrow-down-to-line",
            priority=12
        )
    }
    
    # ==============================================
    # Strategy Management Methods
    # ==============================================
    
    @classmethod
    def get_strategy_metadata(cls, base_strategy: str) -> Optional[StrategyMetadata]:
        """Get metadata for a specific base strategy"""
        return cls.BASE_STRATEGIES.get(base_strategy)
    
    @classmethod
    def get_all_strategies(cls) -> Dict[str, StrategyMetadata]:
        """Get all strategy metadata"""
        return cls.BASE_STRATEGIES.copy()
    
    @classmethod
    def get_strategies_by_category(cls, category: StrategyCategory) -> Dict[str, StrategyMetadata]:
        """Get strategies filtered by category"""
        return {
            key: strategy for key, strategy in cls.BASE_STRATEGIES.items()
            if strategy.category == category
        }
    
    @classmethod
    def get_strategies_by_side(cls, side: SignalSide) -> Dict[str, StrategyMetadata]:
        """Get strategies filtered by side (Buy/Sell)"""
        return {
            key: strategy for key, strategy in cls.BASE_STRATEGIES.items()
            if strategy.side == side
        }
    
    @classmethod
    def validate_strategy_key(cls, strategy_key: str) -> bool:
        """Validate TXYZn strategy key format"""
        pattern = r'^[BS][A-Z]{3}[1-9]$'
        if not re.match(pattern, strategy_key):
            return False
        
        base_strategy = strategy_key[:4]
        return base_strategy in cls.BASE_STRATEGIES
    
    @classmethod
    def parse_strategy_key(cls, strategy_key: str) -> Optional[Dict[str, Any]]:
        """Parse strategy key into components"""
        if not cls.validate_strategy_key(strategy_key):
            return None
        
        return {
            'side': strategy_key[0],
            'base_strategy': strategy_key[:4], 
            'strength': int(strategy_key[4])
        }
    
    @classmethod
    def generate_strategy_key(cls, base_strategy: str, strength: int) -> Optional[str]:
        """Generate strategy key from base strategy and strength"""
        if base_strategy not in cls.BASE_STRATEGIES:
            return None
        
        if not (1 <= strength <= 9):
            return None
        
        return f"{base_strategy}{strength}"
    
    @classmethod
    def get_strategy_display_name(cls, strategy_key: str) -> str:
        """Get display name for strategy key"""
        parsed = cls.parse_strategy_key(strategy_key)
        if not parsed:
            return strategy_key
        
        metadata = cls.get_strategy_metadata(parsed['base_strategy'])
        if not metadata:
            return strategy_key
        
        strength_names = {
            1: "Weak", 2: "Very Light", 3: "Light", 
            4: "Moderate-", 5: "Moderate", 6: "Moderate+",
            7: "Strong", 8: "Very Strong", 9: "Extreme"
        }
        
        strength_name = strength_names.get(parsed['strength'], str(parsed['strength']))
        return metadata.name_template.format(strength=strength_name)
    
    @classmethod
    def get_required_indicators(cls, base_strategy: str) -> List[str]:
        """Get required indicators for a strategy"""
        metadata = cls.get_strategy_metadata(base_strategy)
        return metadata.required_indicators if metadata else []
    
    @classmethod
    def get_strategy_parameters(cls, base_strategy: str) -> Dict[str, Any]:
        """Get default parameters for a strategy"""
        metadata = cls.get_strategy_metadata(base_strategy)
        return metadata.default_parameters.copy() if metadata else {}
    
    @classmethod
    def validate_strategy_parameters(cls, base_strategy: str, parameters: Dict[str, Any]) -> List[str]:
        """Validate strategy parameters, return list of errors"""
        metadata = cls.get_strategy_metadata(base_strategy)
        if not metadata:
            return [f"Unknown strategy: {base_strategy}"]
        
        errors = []
        
        for param, value in parameters.items():
            if param in metadata.parameter_ranges:
                min_val, max_val = metadata.parameter_ranges[param]
                if not (min_val <= value <= max_val):
                    errors.append(f"{param} must be between {min_val} and {max_val}, got {value}")
        
        return errors
    
    @classmethod
    def get_category_summary(cls) -> Dict[str, Dict[str, Any]]:
        """Get summary of strategies by category"""
        summary = {}
        
        for category in StrategyCategory:
            strategies = cls.get_strategies_by_category(category)
            buy_strategies = [k for k, v in strategies.items() if v.side == SignalSide.BUY]
            sell_strategies = [k for k, v in strategies.items() if v.side == SignalSide.SELL]
            
            summary[category.value] = {
                'total': len(strategies),
                'buy_strategies': buy_strategies,
                'sell_strategies': sell_strategies,
                'description': cls._get_category_description(category)
            }
        
        return summary
    
    @classmethod
    def _get_category_description(cls, category: StrategyCategory) -> str:
        """Get description for strategy category"""
        descriptions = {
            StrategyCategory.BREAKOUT: "Price breaking through key support/resistance levels",
            StrategyCategory.MEAN_REVERSION: "Price reversing from overbought/oversold extremes", 
            StrategyCategory.TREND: "Following established market trends via moving averages",
            StrategyCategory.DIVERGENCE: "Price vs indicator divergence patterns",
            StrategyCategory.LEVEL: "Trading bounces/rejections at support/resistance levels"
        }
        return descriptions.get(category, "")
    
    @classmethod
    def get_dashboard_config(cls) -> Dict[str, Any]:
        """Get configuration for dashboard management interface"""
        return {
            'categories': [cat.value for cat in StrategyCategory],
            'sides': [side.value for side in SignalSide],
            'strength_levels': list(range(1, 10)),
            'complexity_levels': ['simple', 'moderate', 'complex'],
            'computational_costs': ['low', 'medium', 'high'],
            'market_conditions': ['trending', 'ranging', 'volatile', 'stable'],
            'total_base_strategies': len(cls.BASE_STRATEGIES),
            'total_strategy_combinations': len(cls.BASE_STRATEGIES) * 9
        }

# Usage example
if __name__ == "__main__":
    # Example usage
    strategy_dict = StrategyDictionary()
    
    # Get strategy metadata
    bbrk_metadata = strategy_dict.get_strategy_metadata("BBRK")
    print(f"BBRK Category: {bbrk_metadata.category.value}")
    print(f"BBRK Required Indicators: {bbrk_metadata.required_indicators}")
    
    # Validate strategy key
    is_valid = strategy_dict.validate_strategy_key("BBRK7")
    print(f"BBRK7 valid: {is_valid}")
    
    # Get display name
    display_name = strategy_dict.get_strategy_display_name("BBRK7")
    print(f"BBRK7 display: {display_name}")
    
    # Get category summary
    summary = strategy_dict.get_category_summary()
    print(f"Categories: {list(summary.keys())}")