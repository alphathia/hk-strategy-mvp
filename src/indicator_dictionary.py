"""
Strategic Signal Indicator Dictionary
Comprehensive documentation and UI integration for all 21 technical indicators
"""

from typing import Dict, List, Any
from enum import Enum

class IndicatorCategory(Enum):
    RSI_FAMILY = "RSI Family"
    TREND_FOLLOWING = "Trend Following"
    VOLUME_ANALYSIS = "Volume Analysis" 
    VOLATILITY = "Volatility"
    MOMENTUM = "Momentum"
    MOVING_AVERAGES = "Moving Averages"

class IndicatorDictionary:
    """
    Complete indicator dictionary with explanations, usage guidelines,
    and UI integration helpers for the Strategic Signal system.
    """
    
    # ==============================================
    # Main Indicator Dictionary
    # ==============================================
    
    INDICATORS = {
        # RSI Family (4 indicators)
        "rsi6": {
            "name": "RSI-6",
            "full_name": "6-day Relative Strength Index",
            "category": IndicatorCategory.RSI_FAMILY,
            "description": "Ultra-sensitive overbought/oversold signals",
            "detailed_explanation": "Very short-term momentum oscillator. Above 70 = overbought, below 30 = oversold. Highly responsive to price changes, good for day trading signals but prone to whipsaws.",
            "usage": "Use for quick reversal signals in trending markets. Best combined with longer RSI periods for confirmation.",
            "overbought_level": 70,
            "oversold_level": 30,
            "optimal_range": [30, 70],
            "signal_interpretation": {
                ">80": "Extremely overbought - strong sell signal",
                "70-80": "Overbought - potential sell signal", 
                "30-70": "Normal range - no clear signal",
                "20-30": "Oversold - potential buy signal",
                "<20": "Extremely oversold - strong buy signal"
            }
        },
        
        "rsi12": {
            "name": "RSI-12", 
            "full_name": "12-day Relative Strength Index",
            "category": IndicatorCategory.RSI_FAMILY,
            "description": "Short-term momentum shifts and reversal signals",
            "detailed_explanation": "Medium-sensitivity momentum oscillator balancing responsiveness with stability. Good for swing trading entries and exits.",
            "usage": "Primary RSI for swing trading. Look for divergences and overbought/oversold extremes.",
            "overbought_level": 70,
            "oversold_level": 30,
            "optimal_range": [30, 70],
            "signal_interpretation": {
                ">75": "Very overbought - consider selling",
                "70-75": "Overbought - caution on longs",
                "30-70": "Normal range - trend following",
                "25-30": "Oversold - consider buying", 
                "<25": "Very oversold - strong buy opportunity"
            }
        },
        
        "rsi14": {
            "name": "RSI-14",
            "full_name": "14-day Relative Strength Index", 
            "category": IndicatorCategory.RSI_FAMILY,
            "description": "Classic overbought (>70) / oversold (<30) momentum indicator",
            "detailed_explanation": "The standard RSI period used by most traders. Most reliable for identifying overbought and oversold conditions. Best balance of sensitivity and stability.",
            "usage": "Primary momentum gauge. >70 suggests potential selling pressure, <30 suggests buying opportunity. Most effective in ranging markets.",
            "overbought_level": 70,
            "oversold_level": 30, 
            "optimal_range": [30, 70],
            "signal_interpretation": {
                ">70": "Overbought - potential reversal down",
                "50-70": "Bullish momentum - uptrend intact",
                "30-50": "Bearish momentum - downtrend intact", 
                "<30": "Oversold - potential reversal up"
            }
        },
        
        "rsi24": {
            "name": "RSI-24",
            "full_name": "24-day Relative Strength Index",
            "category": IndicatorCategory.RSI_FAMILY, 
            "description": "Intermediate-term momentum trends and major reversals",
            "detailed_explanation": "Longer-period RSI that filters out short-term noise. Best for identifying major trend changes and confirming longer-term momentum shifts.",
            "usage": "Use for trend confirmation and major reversal identification. Less prone to false signals but slower to react.",
            "overbought_level": 75,
            "oversold_level": 25,
            "optimal_range": [25, 75],
            "signal_interpretation": {
                ">75": "Extended uptrend - potential exhaustion",
                "50-75": "Strong bullish trend",
                "25-50": "Strong bearish trend",
                "<25": "Extended downtrend - potential reversal"
            }
        },
        
        # MACD & PPO (6 indicators)
        "macd": {
            "name": "MACD Line",
            "full_name": "Moving Average Convergence Divergence",
            "category": IndicatorCategory.TREND_FOLLOWING,
            "description": "12EMA minus 26EMA - primary trend direction indicator", 
            "detailed_explanation": "Difference between fast and slow EMAs. Positive values indicate upward momentum, negative values indicate downward momentum. Crossovers with signal line generate buy/sell signals.",
            "usage": "Track trend direction and momentum changes. MACD above zero = bullish bias, below zero = bearish bias.",
            "signal_interpretation": {
                "Above 0 & Rising": "Strong bullish momentum",
                "Above 0 & Falling": "Weakening bullish momentum", 
                "Below 0 & Falling": "Strong bearish momentum",
                "Below 0 & Rising": "Weakening bearish momentum"
            }
        },
        
        "macd_sig": {
            "name": "MACD Signal",
            "full_name": "MACD Signal Line",
            "category": IndicatorCategory.TREND_FOLLOWING,
            "description": "9EMA of MACD line - generates entry/exit signals",
            "detailed_explanation": "Smoothed version of MACD line. When MACD crosses above signal line = bullish crossover. When MACD crosses below = bearish crossover.",
            "usage": "Primary signal generator. MACD crossing above signal = buy signal, crossing below = sell signal.",
            "signal_interpretation": {
                "MACD > Signal": "Bullish signal - consider buying",
                "MACD < Signal": "Bearish signal - consider selling",
                "Convergence": "Momentum weakening",
                "Divergence": "Momentum strengthening"
            }
        },
        
        "macd_hist": {
            "name": "MACD Histogram", 
            "full_name": "MACD Histogram",
            "category": IndicatorCategory.TREND_FOLLOWING,
            "description": "MACD minus Signal line - momentum acceleration/deceleration",
            "detailed_explanation": "Measures the distance between MACD and its signal line. Positive histogram = MACD above signal (bullish), negative = MACD below signal (bearish). Changes in histogram slope predict crossovers.",
            "usage": "Early warning system for MACD crossovers. Rising histogram = increasing bullish momentum, falling = increasing bearish momentum.",
            "signal_interpretation": {
                "Positive & Expanding": "Accelerating bullish momentum",
                "Positive & Contracting": "Decelerating bullish momentum",
                "Negative & Expanding": "Accelerating bearish momentum", 
                "Negative & Contracting": "Decelerating bearish momentum"
            }
        },
        
        "ppo": {
            "name": "PPO",
            "full_name": "Price Percentage Oscillator",
            "category": IndicatorCategory.TREND_FOLLOWING,
            "description": "Percentage-based MACD alternative for cross-stock comparison",
            "detailed_explanation": "Similar to MACD but expressed as percentage, making it useful for comparing stocks with different price levels. More stable than MACD for long-term analysis.",
            "usage": "Use like MACD but better for portfolio comparison. Positive PPO = uptrend, negative = downtrend.",
            "signal_interpretation": {
                ">2%": "Strong bullish momentum",
                "0% to 2%": "Mild bullish momentum",
                "-2% to 0%": "Mild bearish momentum",
                "<-2%": "Strong bearish momentum"
            }
        },
        
        "ppo_sig": {
            "name": "PPO Signal",
            "full_name": "PPO Signal Line", 
            "category": IndicatorCategory.TREND_FOLLOWING,
            "description": "9EMA of PPO - generates crossover signals",
            "detailed_explanation": "Smoothed PPO for signal generation. PPO crossing above signal = buy, below = sell. More reliable than raw PPO.",
            "usage": "Primary PPO signal generator. Use crossovers for entry/exit timing.",
            "signal_interpretation": {
                "PPO > Signal": "Bullish crossover - buy signal",
                "PPO < Signal": "Bearish crossover - sell signal"
            }
        },
        
        "ppo_hist": {
            "name": "PPO Histogram",
            "full_name": "PPO Histogram",
            "category": IndicatorCategory.TREND_FOLLOWING, 
            "description": "PPO minus PPO Signal - momentum acceleration indicator",
            "detailed_explanation": "Distance between PPO and its signal line. Predicts PPO crossovers and measures momentum strength.",
            "usage": "Early warning for PPO crossovers. Rising histogram = strengthening trend, falling = weakening trend.",
            "signal_interpretation": {
                "Rising from Negative": "Bullish momentum building",
                "Falling from Positive": "Bearish momentum building"
            }
        },
        
        # Moving Averages (6 indicators)
        "ema5": {
            "name": "EMA-5",
            "full_name": "5-day Exponential Moving Average",
            "category": IndicatorCategory.MOVING_AVERAGES,
            "description": "Very short-term dynamic support/resistance",
            "detailed_explanation": "Fast-reacting moving average that closely follows price. Good for identifying very short-term trends and quick support/resistance levels.",
            "usage": "Price above EMA5 = short-term bullish, below = bearish. Use for quick trend identification and dynamic stops.",
            "signal_interpretation": {
                "Price > EMA5": "Short-term bullish bias",
                "Price < EMA5": "Short-term bearish bias",
                "EMA5 Slope Up": "Accelerating uptrend", 
                "EMA5 Slope Down": "Accelerating downtrend"
            }
        },
        
        "ema10": {
            "name": "EMA-10",
            "full_name": "10-day Exponential Moving Average",
            "category": IndicatorCategory.MOVING_AVERAGES,
            "description": "Short-term trend direction and dynamic support/resistance",
            "detailed_explanation": "Balanced short-term moving average. Less noisy than EMA5 but still responsive. Good for swing trading entries and trend following.",
            "usage": "Key short-term trend gauge. Price holding above EMA10 = bullish structure, below = bearish structure.",
            "signal_interpretation": {
                "Strong Bounce off EMA10": "Trend continuation signal",
                "Break below EMA10": "Potential trend change",
                "EMA10 > EMA20": "Short-term bullish alignment",
                "EMA10 < EMA20": "Short-term bearish alignment"
            }
        },
        
        "ema20": {
            "name": "EMA-20", 
            "full_name": "20-day Exponential Moving Average",
            "category": IndicatorCategory.MOVING_AVERAGES,
            "description": "Primary dynamic support/resistance and trend gauge",
            "detailed_explanation": "Most important short-to-medium term moving average. Strong support in uptrends, resistance in downtrends. Key level for trend determination.",
            "usage": "Primary trend gauge. Above EMA20 = uptrend bias, below = downtrend bias. Critical level for breakout/breakdown signals.",
            "signal_interpretation": {
                "Strong Hold above EMA20": "Uptrend intact - buy dips",
                "Break below EMA20": "Uptrend in question - caution",
                "Reclaim EMA20": "Potential trend resumption",
                "Reject at EMA20": "Resistance confirmed"
            }
        },
        
        "ema50": {
            "name": "EMA-50",
            "full_name": "50-day Exponential Moving Average", 
            "category": IndicatorCategory.MOVING_AVERAGES,
            "description": "Medium-term trend direction and major support/resistance",
            "detailed_explanation": "Important medium-term trend indicator. Strong support in bull markets, resistance in bear markets. EMA20/EMA50 crossovers signal trend changes.",
            "usage": "Medium-term trend filter. Above EMA50 = intermediate bullish, below = intermediate bearish. Key level for position sizing decisions.",
            "signal_interpretation": {
                "EMA20 > EMA50": "Bullish trend structure",
                "EMA20 < EMA50": "Bearish trend structure", 
                "Price at EMA50": "Critical support/resistance test",
                "EMA50 Slope": "Primary trend direction"
            }
        },
        
        "sma20": {
            "name": "SMA-20",
            "full_name": "20-day Simple Moving Average",
            "category": IndicatorCategory.MOVING_AVERAGES,
            "description": "Classic 20-day average - Bollinger Band middle line",
            "detailed_explanation": "Standard 20-day moving average, also serves as Bollinger Band middle line. Less responsive than EMA20 but more stable. Good for identifying true trend changes.",
            "usage": "Trend confirmation and Bollinger Band reference. Price above SMA20 = bullish bias, below = bearish bias.",
            "signal_interpretation": {
                "Price > SMA20 & Rising": "Confirmed uptrend",
                "Price < SMA20 & Falling": "Confirmed downtrend",
                "SMA20 Flattening": "Trend losing momentum",
                "Distance from SMA20": "Overbought/oversold gauge"
            }
        },
        
        "sma50": {
            "name": "SMA-50",
            "full_name": "50-day Simple Moving Average",
            "category": IndicatorCategory.MOVING_AVERAGES,
            "description": "Major medium-term trend line and support/resistance",
            "detailed_explanation": "Critical medium-term moving average watched by institutional investors. Strong psychological support/resistance level. SMA20/SMA50 relationship defines trend character.",
            "usage": "Major trend determinant. Above SMA50 = bull market bias, below = bear market bias. Key level for long-term position decisions.",
            "signal_interpretation": {
                "SMA20 > SMA50": "Bullish trend confirmed",
                "SMA20 < SMA50": "Bearish trend confirmed",
                "Price testing SMA50": "Major decision point",
                "SMA50 as Dynamic S/R": "Institution support/resistance"
            }
        },
        
        # Bollinger Bands & Volatility (4 indicators)
        "bb_upper": {
            "name": "Bollinger Upper",
            "full_name": "Bollinger Band Upper",
            "category": IndicatorCategory.VOLATILITY,
            "description": "Price ceiling - SMA20 + 2 standard deviations",
            "detailed_explanation": "Upper volatility band calculated as 20-day SMA + (2 × standard deviation). Represents overbought levels and potential resistance. Price touching upper band suggests high momentum or overbought condition.",
            "usage": "Overbought indicator and resistance level. Price above upper band = extended/overbought. Use for profit-taking signals.",
            "signal_interpretation": {
                "Price touches Upper BB": "Overbought - consider selling",
                "Price above Upper BB": "Very extended - strong sell signal",
                "Upper BB expanding": "Increasing volatility",
                "Upper BB contracting": "Decreasing volatility"
            }
        },
        
        "bb_middle": {
            "name": "Bollinger Middle",
            "full_name": "Bollinger Band Middle (SMA-20)",
            "category": IndicatorCategory.VOLATILITY,
            "description": "Dynamic equilibrium price - 20-day simple moving average",
            "detailed_explanation": "The middle line of Bollinger Bands, identical to 20-day SMA. Represents fair value and dynamic support/resistance. Price tends to revert to this level.",
            "usage": "Mean reversion target and trend indicator. Price above middle = bullish bias, below = bearish bias.",
            "signal_interpretation": {
                "Price > BB Middle": "Above fair value - bullish",
                "Price < BB Middle": "Below fair value - bearish",
                "Bounce off BB Middle": "Mean reversion working",
                "Break of BB Middle": "Trend change potential"
            }
        },
        
        "bb_lower": {
            "name": "Bollinger Lower", 
            "full_name": "Bollinger Band Lower",
            "category": IndicatorCategory.VOLATILITY,
            "description": "Price floor - SMA20 - 2 standard deviations",
            "detailed_explanation": "Lower volatility band calculated as 20-day SMA - (2 × standard deviation). Represents oversold levels and potential support. Price touching lower band suggests oversold condition or strong momentum down.",
            "usage": "Oversold indicator and support level. Price at lower band = potential buying opportunity. Use for entry signals in uptrends.",
            "signal_interpretation": {
                "Price touches Lower BB": "Oversold - consider buying",
                "Price below Lower BB": "Very oversold - strong buy signal", 
                "Bounce off Lower BB": "Oversold bounce - bullish",
                "Lower BB as Support": "Dynamic support level"
            }
        },
        
        "atr14": {
            "name": "ATR-14",
            "full_name": "14-day Average True Range",
            "category": IndicatorCategory.VOLATILITY,
            "description": "Volatility measurement for stop-loss and position sizing",
            "detailed_explanation": "Measures average price volatility over 14 days. Higher ATR = more volatile stock requiring wider stops. Lower ATR = less volatile, can use tighter stops. Essential for risk management.",
            "usage": "Risk management tool. Use for setting stop-losses (1-2x ATR), position sizing, and breakout confirmation. High ATR = high risk/reward.",
            "signal_interpretation": {
                "Rising ATR": "Increasing volatility - expand stops",
                "Falling ATR": "Decreasing volatility - tighten stops",
                "High ATR": "High volatility - reduce position size",
                "Low ATR": "Low volatility - potential for expansion"
            }
        },
        
        # Volume & Flow Analysis (3 indicators)
        "vr24": {
            "name": "VR-24",
            "full_name": "24-day Volume Ratio",
            "category": IndicatorCategory.VOLUME_ANALYSIS,
            "description": "Current volume vs 24-day average volume",
            "detailed_explanation": "Ratio of current volume to 24-day average volume. VR > 1.0 = above average volume, VR < 1.0 = below average. High VR confirms price moves, low VR suggests weak moves.",
            "usage": "Volume confirmation tool. VR > 1.5 = strong volume confirmation. VR < 0.5 = weak volume, question the move.",
            "signal_interpretation": {
                "VR > 2.0": "Extremely high volume - strong conviction",
                "VR 1.5-2.0": "High volume - good confirmation",
                "VR 0.8-1.5": "Normal volume - average conviction",
                "VR < 0.8": "Low volume - weak conviction"
            }
        },
        
        "mfi14": {
            "name": "MFI-14",
            "full_name": "14-day Money Flow Index", 
            "category": IndicatorCategory.VOLUME_ANALYSIS,
            "description": "Volume-weighted RSI for buying/selling pressure",
            "detailed_explanation": "RSI calculation that incorporates volume to measure buying and selling pressure. MFI > 80 = overbought with heavy volume, MFI < 20 = oversold with heavy volume. More reliable than RSI in trending markets.",
            "usage": "Volume-confirmed momentum indicator. Use like RSI but with volume confirmation. Divergences more significant than RSI divergences.",
            "signal_interpretation": {
                "MFI > 80": "Overbought with volume - strong sell signal",
                "MFI 60-80": "Volume-confirmed uptrend",
                "MFI 20-60": "Balanced buying/selling pressure",
                "MFI < 20": "Oversold with volume - strong buy signal"
            }
        },
        
        "ad_line": {
            "name": "A/D Line",
            "full_name": "Accumulation/Distribution Line",
            "category": IndicatorCategory.VOLUME_ANALYSIS,
            "description": "Cumulative volume-price flow to detect accumulation vs distribution",
            "detailed_explanation": "Running total of money flow based on where price closes within the day's range. Rising A/D = accumulation (buying pressure), falling A/D = distribution (selling pressure). Used to confirm trends and spot divergences.",
            "usage": "Trend confirmation and divergence detection. Rising A/D confirms uptrends, falling A/D confirms downtrends. Divergences predict reversals.",
            "signal_interpretation": {
                "A/D Rising + Price Rising": "Confirmed uptrend - accumulation",
                "A/D Falling + Price Falling": "Confirmed downtrend - distribution", 
                "A/D Rising + Price Falling": "Bullish divergence - accumulation on weakness",
                "A/D Falling + Price Rising": "Bearish divergence - distribution on strength"
            }
        },
        
        # Momentum & Trend Indicators (4 indicators)
        "stoch_k": {
            "name": "Stochastic %K",
            "full_name": "Stochastic %K", 
            "category": IndicatorCategory.MOMENTUM,
            "description": "Raw momentum oscillator for turn points in ranges",
            "detailed_explanation": "Measures where current price sits relative to recent high-low range. %K > 80 = overbought, %K < 20 = oversold. Fast-moving indicator good for timing entries in ranging markets.",
            "usage": "Momentum timing tool. Best in sideways markets. %K crossing above 20 = buy signal, crossing below 80 = sell signal.",
            "signal_interpretation": {
                "%K > 80": "Overbought - potential reversal down",
                "%K 20-80": "Normal range - follow trend",
                "%K < 20": "Oversold - potential reversal up",
                "%K crossing levels": "Entry/exit timing signals"
            }
        },
        
        "stoch_d": {
            "name": "Stochastic %D",
            "full_name": "Stochastic %D (Signal Line)",
            "category": IndicatorCategory.MOMENTUM,
            "description": "Smoothed %K for signal confirmation and timing",
            "detailed_explanation": "3-day SMA of %K, providing smoother signals with fewer false positives. %K crossing above %D = bullish signal, %K crossing below %D = bearish signal.",
            "usage": "Signal confirmation for Stochastic. %K > %D = bullish momentum, %K < %D = bearish momentum. Use crossovers for timing.",
            "signal_interpretation": {
                "%K > %D": "Bullish momentum - consider buying",
                "%K < %D": "Bearish momentum - consider selling",
                "Both in oversold": "Strong buy setup when crossing up",
                "Both in overbought": "Strong sell setup when crossing down"
            }
        },
        
        "williams_r": {
            "name": "Williams %R", 
            "full_name": "Williams Percent Range",
            "category": IndicatorCategory.MOMENTUM,
            "description": "Momentum oscillator with overbought/oversold levels",
            "detailed_explanation": "Inverse of Stochastic %K, scaled from 0 to -100. %R above -20 = overbought, %R below -80 = oversold. Good for identifying short-term reversal points.",
            "usage": "Reversal timing indicator. %R crossing above -80 = buy signal, %R crossing below -20 = sell signal. Best used with trend confirmation.",
            "signal_interpretation": {
                "%R > -20": "Overbought - potential sell signal",
                "%R -20 to -80": "Normal range - trend following",
                "%R < -80": "Oversold - potential buy signal",
                "Divergence": "Strong reversal signal"
            }
        },
        
        "adx14": {
            "name": "ADX-14",
            "full_name": "14-day Average Directional Index", 
            "category": IndicatorCategory.MOMENTUM,
            "description": "Trend strength filter (>25 = trending, <25 = ranging)",
            "detailed_explanation": "Measures trend strength regardless of direction. ADX > 25 = trending market (use trend-following strategies), ADX < 25 = ranging market (use mean-reversion strategies). Does not indicate direction, only strength.",
            "usage": "Strategy filter. ADX > 25 = use trend strategies, ADX < 25 = use range strategies. Rising ADX = strengthening trend, falling ADX = weakening trend.",
            "signal_interpretation": {
                "ADX > 40": "Very strong trend - trend following optimal",
                "ADX 25-40": "Trending market - favor trend strategies", 
                "ADX < 25": "Ranging market - favor mean reversion",
                "ADX Rising": "Trend strengthening",
                "ADX Falling": "Trend weakening"
            }
        },
        
        # Specialized Indicators (1 indicator)
        "parabolic_sar": {
            "name": "Parabolic SAR",
            "full_name": "Parabolic Stop and Reverse",
            "category": IndicatorCategory.MOMENTUM,
            "description": "Trailing stop system and trend direction indicator",
            "detailed_explanation": "Provides trailing stop levels that accelerate as trend continues. SAR below price = uptrend (dots below), SAR above price = downtrend (dots above). Price crossing SAR = trend reversal signal.",
            "usage": "Trailing stop system and trend indicator. Use SAR as stop-loss level. SAR crossover = exit current position and potentially reverse.",
            "signal_interpretation": {
                "Price > SAR": "Uptrend - hold long positions",
                "Price < SAR": "Downtrend - hold short positions", 
                "Price crosses SAR": "Trend reversal - exit/reverse positions",
                "SAR acceleration": "Trend gaining momentum"
            }
        }
    }
    
    # ==============================================
    # Category Groupings
    # ==============================================
    
    @classmethod
    def get_indicators_by_category(cls, category: IndicatorCategory) -> Dict[str, Dict]:
        """Get all indicators in a specific category"""
        return {
            key: value for key, value in cls.INDICATORS.items() 
            if value["category"] == category
        }
    
    @classmethod
    def get_category_summary(cls) -> Dict[str, int]:
        """Get count of indicators per category"""
        summary = {}
        for indicator in cls.INDICATORS.values():
            category_name = indicator["category"].value
            summary[category_name] = summary.get(category_name, 0) + 1
        return summary
    
    # ==============================================
    # UI Integration Helpers
    # ==============================================
    
    @classmethod
    def get_chart_overlay_indicators(cls) -> List[str]:
        """Get list of indicators suitable for chart overlays"""
        overlay_indicators = [
            "ema5", "ema10", "ema20", "ema50", "sma20", "sma50",
            "bb_upper", "bb_middle", "bb_lower", "parabolic_sar"
        ]
        return overlay_indicators
    
    @classmethod
    def get_oscillator_indicators(cls) -> List[str]:
        """Get list of oscillator indicators for separate panels"""
        oscillators = [
            "rsi6", "rsi12", "rsi14", "rsi24", "macd", "macd_sig", "macd_hist",
            "ppo", "ppo_sig", "ppo_hist", "stoch_k", "stoch_d", "williams_r",
            "mfi14", "adx14"
        ]
        return oscillators
    
    @classmethod
    def get_volume_indicators(cls) -> List[str]:
        """Get list of volume-based indicators"""
        volume_indicators = ["vr24", "mfi14", "ad_line"]
        return volume_indicators
    
    @classmethod
    def get_indicator_explanation(cls, indicator_key: str, context: str = "basic") -> str:
        """Get contextual explanation for an indicator"""
        if indicator_key not in cls.INDICATORS:
            return f"Unknown indicator: {indicator_key}"
        
        indicator = cls.INDICATORS[indicator_key]
        
        if context == "basic":
            return indicator["description"]
        elif context == "detailed":
            return indicator["detailed_explanation"]
        elif context == "usage":
            return indicator["usage"]
        else:
            return indicator["description"]
    
    @classmethod
    def get_signal_interpretation(cls, indicator_key: str, value: float) -> str:
        """Get signal interpretation for a specific indicator value"""
        if indicator_key not in cls.INDICATORS:
            return "Unknown indicator"
        
        indicator = cls.INDICATORS[indicator_key]
        interpretations = indicator.get("signal_interpretation", {})
        
        # Simple range-based interpretation for RSI-type indicators
        if "rsi" in indicator_key:
            if value > 70:
                return interpretations.get(">70", "Overbought")
            elif value < 30:
                return interpretations.get("<30", "Oversold")
            else:
                return interpretations.get("30-70", "Normal range")
        
        # Return first matching interpretation or default
        return list(interpretations.values())[0] if interpretations else "No interpretation available"
    
    @classmethod
    def get_ui_display_config(cls, indicator_key: str) -> Dict[str, Any]:
        """Get UI configuration for displaying an indicator"""
        if indicator_key not in cls.INDICATORS:
            return {}
        
        indicator = cls.INDICATORS[indicator_key]
        
        config = {
            "name": indicator["name"],
            "full_name": indicator["full_name"], 
            "category": indicator["category"].value,
            "description": indicator["description"],
            "chart_type": "overlay" if indicator_key in cls.get_chart_overlay_indicators() else "oscillator"
        }
        
        # Add specific configuration for different indicator types
        if "rsi" in indicator_key or indicator_key in ["mfi14", "stoch_k", "stoch_d", "williams_r"]:
            config["scale"] = [0, 100]
            config["overbought"] = indicator.get("overbought_level", 70)
            config["oversold"] = indicator.get("oversold_level", 30)
        
        elif indicator_key in ["macd", "macd_sig", "macd_hist", "ppo", "ppo_sig", "ppo_hist"]:
            config["scale"] = "auto"
            config["zero_line"] = True
        
        elif indicator_key == "adx14":
            config["scale"] = [0, 100] 
            config["trend_threshold"] = 25
        
        return config

# ==============================================
# Usage Examples and Integration Notes
# ==============================================

"""
Example Usage:

# Get indicator explanation for UI tooltip
explanation = IndicatorDictionary.get_indicator_explanation("rsi14", "detailed")

# Get all RSI family indicators
rsi_indicators = IndicatorDictionary.get_indicators_by_category(IndicatorCategory.RSI_FAMILY)

# Get chart overlay indicators for UI selection
overlay_options = IndicatorDictionary.get_chart_overlay_indicators()

# Get UI display configuration
ui_config = IndicatorDictionary.get_ui_display_config("rsi14")

# Get signal interpretation for current value
signal = IndicatorDictionary.get_signal_interpretation("rsi14", 75.2)  # Returns "Overbought"

Integration with Chart UI:
1. Use get_chart_overlay_indicators() for main chart overlay options
2. Use get_oscillator_indicators() for separate oscillator panels  
3. Use get_ui_display_config() for proper scaling and display
4. Use get_indicator_explanation() for tooltips and help text
5. Use get_signal_interpretation() for real-time signal explanations
"""