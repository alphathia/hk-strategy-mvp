#!/usr/bin/env python3
"""
Test the Portfolio Performance Comparison chart fix
"""

import sys
import os
sys.path.append('src')
from src.portfolio_analysis_manager import PortfolioAnalysisManager
from src.database import DatabaseManager
from datetime import date, timedelta
import pandas as pd

def test_portfolio_performance_fix():
    """Test that the portfolio performance chart now shows correct values"""
    
    print('🧪 TESTING PORTFOLIO PERFORMANCE CHART FIX')
    print('='*70)
    
    # Initialize managers
    db_manager = DatabaseManager()
    portfolio_manager = PortfolioAnalysisManager(db_manager)
    
    # Test with MyHKEXTechExpt1708 analysis (ID: 28)
    test_analysis_id = 28
    
    print(f'\n📊 TESTING ANALYSIS ID: {test_analysis_id} (MyHKEXTechExpt1708)')
    
    # Get timeline data for this analysis
    print(f'Generating timeline data...')
    timeline_df = portfolio_manager.get_analysis_timeline_data([test_analysis_id])
    
    if timeline_df.empty:
        print('❌ No timeline data generated')
        return
    
    print(f'✅ Generated timeline with {len(timeline_df)} data points')
    
    # Check the values - should be positive and match expected ranges
    print(f'\n📈 TIMELINE DATA ANALYSIS:')
    
    # Get first and last values
    first_row = timeline_df.iloc[0]
    last_row = timeline_df.iloc[-1]
    
    first_date = first_row['date']
    first_total = first_row['total_value']
    first_cash = first_row['cash_position']
    first_equity = first_row['equity_value']
    
    last_date = last_row['date']
    last_total = last_row['total_value']
    last_cash = last_row['cash_position']
    last_equity = last_row['equity_value']
    
    print(f'First trading day: {first_date}')
    print(f'  Total Value: ${first_total:,.2f}')
    print(f'  Cash Position: ${first_cash:,.2f}')
    print(f'  Equity Value: ${first_equity:,.2f}')
    
    print(f'\nLast trading day: {last_date}')
    print(f'  Total Value: ${last_total:,.2f}')
    print(f'  Cash Position: ${last_cash:,.2f}')
    print(f'  Equity Value: ${last_equity:,.2f}')
    
    # Calculate performance
    total_return = ((last_total - first_total) / first_total) * 100 if first_total != 0 else 0
    print(f'\nCalculated Performance:')
    print(f'  Total Return: {total_return:.2f}%')
    print(f'  Value Change: ${last_total - first_total:,.2f}')
    
    # Validation checks
    print(f'\n🔍 VALIDATION RESULTS:')
    
    issues = []
    
    # Check for negative total values (should be positive)
    if first_total < 0 or last_total < 0:
        issues.append("❌ ISSUE: Negative total values found")
    else:
        print(f'✅ Total values are positive')
    
    # Check if values are realistic (should be in millions, not near zero)
    if first_total < 1000000 or last_total < 1000000:
        issues.append("❌ ISSUE: Values too low (expected ~$2-3M)")
    else:
        print(f'✅ Values are in expected range (millions)')
    
    # Check if return matches expected (~43%)
    expected_return = 42.99
    if abs(total_return - expected_return) > 5:
        issues.append(f"⚠️  WARNING: Return {total_return:.2f}% differs from expected {expected_return}%")
    else:
        print(f'✅ Return matches expected value (~{expected_return}%)')
    
    # Check cash position consistency
    if first_cash != last_cash:
        issues.append(f"⚠️  WARNING: Cash changed from ${first_cash:,.2f} to ${last_cash:,.2f} (expected constant)")
    else:
        print(f'✅ Cash position remains constant')
    
    # Show sample data points to verify no double-processing
    print(f'\n📋 SAMPLE DATA POINTS (first 5):')
    print(f"{'Date':<12} {'Total Value':<15} {'Cash':<15} {'Equity':<15}")
    print(f"{'-'*12} {'-'*15} {'-'*15} {'-'*15}")
    
    for i in range(min(5, len(timeline_df))):
        row = timeline_df.iloc[i]
        date_str = str(row['date'])[:10]  # Just the date part
        print(f"{date_str:<12} ${row['total_value']:>13,.0f} ${row['cash_position']:>13,.0f} ${row['equity_value']:>13,.0f}")
    
    # Show last 5 data points
    if len(timeline_df) > 5:
        print(f'\n📋 SAMPLE DATA POINTS (last 5):')
        print(f"{'Date':<12} {'Total Value':<15} {'Cash':<15} {'Equity':<15}")
        print(f"{'-'*12} {'-'*15} {'-'*15} {'-'*15}")
        
        for i in range(max(0, len(timeline_df)-5), len(timeline_df)):
            row = timeline_df.iloc[i]
            date_str = str(row['date'])[:10]  # Just the date part
            print(f"{date_str:<12} ${row['total_value']:>13,.0f} ${row['cash_position']:>13,.0f} ${row['equity_value']:>13,.0f}")
    
    # Final assessment
    print(f'\n🎉 TEST RESULTS:')
    if not issues:
        print(f'✅ SUCCESS: Portfolio Performance Chart fix working correctly!')
        print(f'✅ Chart should now display values from ${first_total:,.0f} to ${last_total:,.0f}')
        print(f'✅ Expected positive growth of {total_return:.1f}%')
    else:
        print(f'❌ ISSUES FOUND:')
        for issue in issues:
            print(f'   {issue}')

if __name__ == "__main__":
    test_portfolio_performance_fix()