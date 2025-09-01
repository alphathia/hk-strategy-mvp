#!/usr/bin/env python3
"""
Test the trading days fix for Portfolio Total Value Over Time chart
"""

import sys
import os
sys.path.append('src')
from src.portfolio_analysis_manager import PortfolioAnalysisManager
from src.database import DatabaseManager
from src.hkex_calendar import get_hkex_trading_days
from datetime import date, timedelta
import pandas as pd

def test_trading_days_fix():
    """Test that the portfolio timeline now uses trading days only"""
    
    print('🧪 TESTING PORTFOLIO TOTAL VALUE CHART - TRADING DAYS ONLY')
    print('='*70)
    
    # Initialize managers
    db_manager = DatabaseManager()
    portfolio_manager = PortfolioAnalysisManager(db_manager)
    
    # Get a sample analysis to test
    conn = db_manager.get_connection()
    cur = conn.cursor()
    
    # Find recent analyses
    cur.execute("""
        SELECT id, analysis_name, start_date, end_date
        FROM portfolio_analyses 
        ORDER BY created_at DESC
        LIMIT 3
    """)
    
    analyses = cur.fetchall()
    
    if not analyses:
        print("❌ No portfolio analyses found to test")
        return
    
    print(f"Found {len(analyses)} portfolio analyses to test:")
    for analysis_id, name, start_date, end_date in analyses:
        print(f"  {analysis_id}: {name} ({start_date} to {end_date})")
    
    # Test with the first analysis
    test_analysis_id = analyses[0][0]
    test_name = analyses[0][1]
    test_start = analyses[0][2]
    test_end = analyses[0][3]
    
    print(f"\n🔬 TESTING ANALYSIS: {test_name} (ID: {test_analysis_id})")
    print(f"   Date Range: {test_start} to {test_end}")
    
    # Check HKEX trading days for comparison
    trading_days = get_hkex_trading_days(test_start, test_end)
    total_calendar_days = (test_end - test_start).days + 1
    
    print(f"   Calendar Days: {total_calendar_days}")
    print(f"   Trading Days: {len(trading_days)}")
    print(f"   Weekend/Holiday Days Excluded: {total_calendar_days - len(trading_days)}")
    
    # Test the timeline generation
    print(f"\n📊 GENERATING PORTFOLIO TIMELINE DATA...")
    timeline_df = portfolio_manager.get_analysis_timeline_data([test_analysis_id])
    
    if timeline_df.empty:
        print("❌ No timeline data generated")
        return
    
    print(f"✅ Generated timeline with {len(timeline_df)} data points")
    
    # Verify that all data points are on trading days
    print(f"\n🔍 VALIDATING TRADING DAYS ONLY...")
    
    if 'date' in timeline_df.columns:
        # Handle dates that might already be date objects
        dates_series = timeline_df['date']
        if hasattr(dates_series.iloc[0], 'date'):  # pandas datetime
            timeline_dates = dates_series.dt.date.unique()
        else:  # already date objects
            timeline_dates = dates_series.unique()
    else:
        timeline_dates = []
    
    weekend_count = 0
    non_trading_count = 0
    
    for timeline_date in timeline_dates:
        # Check if it's a weekend (Saturday=5, Sunday=6)
        if timeline_date.weekday() >= 5:
            weekend_count += 1
            print(f"⚠️  WARNING: Weekend date found in timeline: {timeline_date} ({timeline_date.strftime('%A')})")
        
        # Check if it's a trading day according to HKEX calendar
        if timeline_date not in trading_days:
            non_trading_count += 1
            print(f"⚠️  WARNING: Non-trading day found in timeline: {timeline_date}")
    
    # Summary
    print(f"\n📋 VALIDATION RESULTS:")
    print(f"   Total timeline data points: {len(timeline_dates)}")
    print(f"   Weekend dates in timeline: {weekend_count}")
    print(f"   Non-trading days in timeline: {non_trading_count}")
    
    if weekend_count == 0 and non_trading_count == 0:
        print(f"✅ SUCCESS: Timeline contains TRADING DAYS ONLY!")
        print(f"✅ Weekend zero-value issue should be FIXED!")
    else:
        print(f"❌ ISSUE: Timeline still contains non-trading days")
        
    # Check for zero equity values
    if 'equity_value' in timeline_df.columns:
        zero_equity_count = len(timeline_df[timeline_df['equity_value'] == 0])
        print(f"   Zero equity value entries: {zero_equity_count}")
        
        if zero_equity_count > 0:
            print(f"⚠️  WARNING: Still has zero equity values (may be due to no positions)")
        else:
            print(f"✅ No zero equity values found")
    
    # Show sample data
    print(f"\n📊 SAMPLE TIMELINE DATA:")
    print("-" * 80)
    if len(timeline_df) > 0:
        sample_data = timeline_df.head(10)
        for _, row in sample_data.iterrows():
            date_val = row['date'].date() if hasattr(row['date'], 'date') else row['date']
            total_val = row.get('total_value', 0)
            equity_val = row.get('equity_value', 0)
            cash_val = row.get('cash_position', 0)
            weekday = date_val.strftime('%A')
            print(f"   {date_val} ({weekday}): Total=${total_val:,.2f}, Equity=${equity_val:,.2f}, Cash=${cash_val:,.2f}")
    
    conn.close()
    
    print(f"\n🎉 TRADING DAYS FIX TEST COMPLETED!")
    
    if weekend_count == 0 and non_trading_count == 0:
        print(f"✅ Portfolio Total Value Over Time chart should now display properly")
        print(f"✅ No more weekend gaps with zero values")
        print(f"✅ Smooth chart progression showing only trading days")
    else:
        print(f"❌ Fix may need additional work")

if __name__ == "__main__":
    test_trading_days_fix()