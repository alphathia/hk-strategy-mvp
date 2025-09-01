"""
HKEX Trading Calendar Service

Handles Hong Kong Exchange trading days, holidays, and date validation
for portfolio analysis period selection.
"""

import pandas as pd
from datetime import datetime, date, timedelta
from typing import List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

# HKEX Public Holidays (2024-2026) - Update annually
HKEX_HOLIDAYS = {
    # 2024
    date(2024, 1, 1): "New Year's Day",
    date(2024, 2, 10): "Chinese New Year",
    date(2024, 2, 12): "Chinese New Year",
    date(2024, 2, 13): "Chinese New Year",
    date(2024, 3, 29): "Good Friday",
    date(2024, 4, 1): "Easter Monday",
    date(2024, 4, 4): "Ching Ming Festival",
    date(2024, 5, 1): "Labour Day",
    date(2024, 5, 15): "Buddha's Birthday",
    date(2024, 6, 10): "Dragon Boat Festival",
    date(2024, 7, 1): "HKSAR Establishment Day",
    date(2024, 9, 18): "Day after Mid-Autumn Festival",
    date(2024, 10, 1): "National Day",
    date(2024, 10, 11): "Chung Yeung Festival",
    date(2024, 12, 25): "Christmas Day",
    date(2024, 12, 26): "Boxing Day",
    
    # 2025
    date(2025, 1, 1): "New Year's Day",
    date(2025, 1, 29): "Chinese New Year",
    date(2025, 1, 30): "Chinese New Year",
    date(2025, 1, 31): "Chinese New Year",
    date(2025, 4, 4): "Ching Ming Festival",
    date(2025, 4, 18): "Good Friday",
    date(2025, 4, 21): "Easter Monday",
    date(2025, 5, 1): "Labour Day",
    date(2025, 5, 5): "Buddha's Birthday",
    date(2025, 5, 31): "Dragon Boat Festival",
    date(2025, 7, 1): "HKSAR Establishment Day",
    date(2025, 10, 1): "National Day",
    date(2025, 10, 6): "Day after Mid-Autumn Festival",
    date(2025, 10, 11): "Chung Yeung Festival",
    date(2025, 12, 25): "Christmas Day",
    date(2025, 12, 26): "Boxing Day",
    
    # 2026 (partial - update as official calendar is released)
    date(2026, 1, 1): "New Year's Day",
    date(2026, 2, 17): "Chinese New Year",
    date(2026, 2, 18): "Chinese New Year",
    date(2026, 2, 19): "Chinese New Year",
    date(2026, 4, 4): "Ching Ming Festival",
    date(2026, 4, 3): "Good Friday",
    date(2026, 4, 6): "Easter Monday",
    date(2026, 5, 1): "Labour Day",
    date(2026, 5, 24): "Buddha's Birthday",
    date(2026, 6, 19): "Dragon Boat Festival",
    date(2026, 7, 1): "HKSAR Establishment Day",
    date(2026, 10, 1): "National Day",
    date(2026, 10, 25): "Day after Mid-Autumn Festival",
    date(2026, 10, 29): "Chung Yeung Festival",
    date(2026, 12, 25): "Christmas Day",
    date(2026, 12, 26): "Boxing Day",
}

class HKEXTradingCalendar:
    """Hong Kong Exchange trading calendar and date utilities."""
    
    def __init__(self):
        self.holidays = HKEX_HOLIDAYS
    
    def is_trading_day(self, check_date: date) -> bool:
        """
        Check if a given date is a HKEX trading day.
        
        Args:
            check_date: Date to check
            
        Returns:
            True if it's a trading day, False otherwise
        """
        # Weekend check
        if check_date.weekday() >= 5:  # Saturday = 5, Sunday = 6
            return False
        
        # Holiday check
        if check_date in self.holidays:
            return False
            
        return True
    
    def get_next_trading_day(self, from_date: date) -> date:
        """
        Get the next trading day on or after the given date.
        
        Args:
            from_date: Starting date
            
        Returns:
            Next trading day (could be same day if it's already a trading day)
        """
        current = from_date
        while not self.is_trading_day(current):
            current += timedelta(days=1)
        return current
    
    def get_previous_trading_day(self, from_date: date) -> date:
        """
        Get the previous trading day on or before the given date.
        
        Args:
            from_date: Starting date
            
        Returns:
            Previous trading day (could be same day if it's already a trading day)
        """
        current = from_date
        while not self.is_trading_day(current):
            current -= timedelta(days=1)
        return current
    
    def get_trading_days_between(self, start_date: date, end_date: date) -> List[date]:
        """
        Get all trading days between start_date and end_date (inclusive).
        
        Args:
            start_date: Start date
            end_date: End date
            
        Returns:
            List of trading days
        """
        if start_date > end_date:
            return []
        
        trading_days = []
        current = start_date
        
        while current <= end_date:
            if self.is_trading_day(current):
                trading_days.append(current)
            current += timedelta(days=1)
        
        return trading_days
    
    def validate_analysis_period(self, start_date: date, end_date: date) -> Tuple[bool, str, date, date]:
        """
        Validate and adjust analysis period for portfolio analysis.
        
        Args:
            start_date: Requested start date
            end_date: Requested end date
            
        Returns:
            Tuple of (is_valid, message, adjusted_start_date, adjusted_end_date)
        """
        # Check date order
        if start_date > end_date:
            return False, "Start date must be before end date", start_date, end_date
        
        # Check 18-month limit
        max_end_date = start_date + timedelta(days=18 * 30)  # Approximate 18 months
        if end_date > max_end_date:
            return False, f"Date range exceeds 18 months limit. Maximum end date: {max_end_date}", start_date, end_date
        
        # Adjust to trading days
        adjusted_start = self.get_next_trading_day(start_date)
        adjusted_end = self.get_previous_trading_day(end_date)
        
        # Check if adjusted dates are valid
        if adjusted_start > adjusted_end:
            return False, "No trading days found in the selected period", start_date, end_date
        
        # Check if dates were adjusted
        message = "Valid period"
        if adjusted_start != start_date or adjusted_end != end_date:
            message = f"Dates adjusted to trading days: {adjusted_start} to {adjusted_end}"
        
        return True, message, adjusted_start, adjusted_end
    
    def get_analysis_data_start_date(self, analysis_start_date: date) -> date:
        """
        Get the data collection start date (1 month prior to analysis start).
        
        Args:
            analysis_start_date: Analysis start date
            
        Returns:
            Data collection start date (1 month prior)
        """
        data_start = analysis_start_date - timedelta(days=30)  # 1 month prior
        return self.get_next_trading_day(data_start)
    
    def count_trading_days(self, start_date: date, end_date: date) -> int:
        """
        Count trading days between start and end date (inclusive).
        
        Args:
            start_date: Start date
            end_date: End date
            
        Returns:
            Number of trading days
        """
        return len(self.get_trading_days_between(start_date, end_date))
    
    def get_trading_day_info(self, check_date: date) -> dict:
        """
        Get detailed information about a trading day.
        
        Args:
            check_date: Date to check
            
        Returns:
            Dictionary with trading day information
        """
        is_trading = self.is_trading_day(check_date)
        info = {
            "date": check_date,
            "is_trading_day": is_trading,
            "day_of_week": check_date.strftime("%A"),
            "is_weekend": check_date.weekday() >= 5,
            "is_holiday": check_date in self.holidays,
            "holiday_name": self.holidays.get(check_date, None)
        }
        
        if not is_trading:
            info["next_trading_day"] = self.get_next_trading_day(check_date + timedelta(days=1))
            info["previous_trading_day"] = self.get_previous_trading_day(check_date - timedelta(days=1))
        
        return info

# Global instance for easy import
hkex_calendar = HKEXTradingCalendar()

# Convenience functions
def is_hkex_trading_day(check_date: date) -> bool:
    """Check if date is a HKEX trading day."""
    return hkex_calendar.is_trading_day(check_date)

def get_hkex_trading_days(start_date: date, end_date: date) -> List[date]:
    """Get all HKEX trading days between dates."""
    return hkex_calendar.get_trading_days_between(start_date, end_date)

def validate_hkex_analysis_period(start_date: date, end_date: date) -> Tuple[bool, str, date, date]:
    """Validate analysis period for HKEX trading days."""
    return hkex_calendar.validate_analysis_period(start_date, end_date)