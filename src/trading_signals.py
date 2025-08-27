import numpy as np
import pandas as pd
from typing import Dict, Tuple
import random
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class TradingSignalGenerator:
    def __init__(self):
        self.signal_weights = {
            'rsi': 0.25,
            'ma_crossover': 0.30,
            'bollinger': 0.20,
            'volume': 0.15,
            'momentum': 0.10
        }

    def calculate_rsi(self, prices: list, period: int = 14) -> float:
        if len(prices) < period:
            return 50.0
        
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def calculate_moving_averages(self, prices: list) -> Dict[str, float]:
        if len(prices) < 50:
            prices.extend([prices[-1]] * (50 - len(prices)))
        
        return {
            'ma_5': np.mean(prices[-5:]),
            'ma_20': np.mean(prices[-20:]),
            'ma_50': np.mean(prices[-50:])
        }

    def calculate_bollinger_bands(self, prices: list, period: int = 20, std_dev: int = 2) -> Dict[str, float]:
        if len(prices) < period:
            prices.extend([prices[-1]] * (period - len(prices)))
        
        recent_prices = prices[-period:]
        sma = np.mean(recent_prices)
        std = np.std(recent_prices)
        
        return {
            'bollinger_upper': sma + (std_dev * std),
            'bollinger_lower': sma - (std_dev * std),
            'bollinger_middle': sma
        }

    def generate_signal_for_stock(self, symbol: str, current_price: float, 
                                volume: int = None) -> Tuple[str, float, Dict]:
        
        price_history = self._simulate_price_history(current_price)
        
        rsi = self.calculate_rsi(price_history)
        mas = self.calculate_moving_averages(price_history)
        bollinger = self.calculate_bollinger_bands(price_history)
        
        indicators = {
            'rsi': rsi,
            **mas,
            **bollinger,
            'volume': volume or random.randint(100000, 2000000)
        }
        
        signal_score = self._calculate_signal_score(current_price, indicators)
        signal_type = self._determine_signal_type(signal_score)
        signal_strength = abs(signal_score)
        
        return signal_type, signal_strength, indicators

    def _simulate_price_history(self, current_price: float, days: int = 50) -> list:
        prices = []
        price = current_price * 0.95
        
        for i in range(days):
            change = random.uniform(-0.05, 0.05)
            price = price * (1 + change)
            prices.append(price)
        
        prices[-1] = current_price
        return prices

    def _calculate_signal_score(self, current_price: float, indicators: Dict) -> float:
        score = 0.0
        
        rsi = indicators['rsi']
        if rsi > 70:
            score -= 0.3
        elif rsi < 30:
            score += 0.3
        else:
            score += (50 - rsi) / 100
        
        ma_5, ma_20, ma_50 = indicators['ma_5'], indicators['ma_20'], indicators['ma_50']
        
        if ma_5 > ma_20 > ma_50:
            score += 0.4
        elif ma_5 < ma_20 < ma_50:
            score -= 0.4
        
        if current_price > ma_20:
            score += 0.2
        else:
            score -= 0.2
        
        bollinger_upper = indicators['bollinger_upper']
        bollinger_lower = indicators['bollinger_lower']
        
        if current_price > bollinger_upper:
            score -= 0.3
        elif current_price < bollinger_lower:
            score += 0.3
        
        volume_factor = min(indicators['volume'] / 1000000, 2.0)
        score *= volume_factor
        
        return np.clip(score, -1.0, 1.0)

    def _determine_signal_type(self, score: float) -> str:
        if score > 0.6:
            return 'A'
        elif score > 0.2:
            return 'B' 
        elif score > -0.2:
            return 'C'
        else:
            return 'D'

    def get_signal_description(self, signal_type: str) -> str:
        descriptions = {
            'A': 'Strong Buy - High conviction bullish signal',
            'B': 'Buy - Moderate bullish signal', 
            'C': 'Hold - Neutral/weak signal',
            'D': 'Sell - Bearish signal'
        }
        return descriptions.get(signal_type, 'Unknown signal')

    def get_signal_color(self, signal_type: str) -> str:
        colors = {
            'A': '#00C851',  # Green
            'B': '#33B679',  # Light Green  
            'C': '#FFB300',  # Orange
            'D': '#FF4444'   # Red
        }
        return colors.get(signal_type, '#666666')