#!/usr/bin/env python3
"""
Test Portfolio Analysis Manager
"""

import sys
sys.path.append('src')

from database import DatabaseManager
from portfolio_analysis_manager import PortfolioAnalysisManager
from datetime import date
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_analysis_manager():
    """Test the portfolio analysis manager functionality"""
    
    print("=" * 60)
    print("🧪 TESTING PORTFOLIO ANALYSIS MANAGER")
    print("=" * 60)
    
    # Initialize managers
    db_manager = DatabaseManager()
    analysis_manager = PortfolioAnalysisManager(db_manager)
    
    # Test portfolio - use existing portfolio
    portfolio_id = "My_HKEX_ALL"
    
    print(f"\n📊 Testing with portfolio: {portfolio_id}")
    
    # Test 1: Create a new analysis
    print("\n1️⃣ Testing: Create New Analysis")
    success, message, analysis_id = analysis_manager.create_analysis(
        portfolio_id=portfolio_id,
        analysis_name="Test Analysis Q1 2024",
        start_date=date(2024, 1, 1),
        end_date=date(2024, 3, 31),
        start_cash=100000.00
    )
    
    if success:
        print(f"   ✅ {message} (ID: {analysis_id})")
    else:
        print(f"   ❌ {message}")
        return
    
    # Test 2: Get analysis summary
    print("\n2️⃣ Testing: Get Analysis Summary")
    summary_df = analysis_manager.get_analysis_summary(portfolio_id)
    if not summary_df.empty:
        print(f"   ✅ Retrieved {len(summary_df)} analyses")
        latest = summary_df.iloc[0]
        print(f"   📋 Latest: {latest['name']} (${latest['start_total_value']:,.2f} start value)")
    else:
        print("   ❌ No analyses found")
    
    # Test 3: Add a buy transaction
    print("\n3️⃣ Testing: Add Buy Transaction")
    success, message = analysis_manager.add_transaction(
        analysis_id=analysis_id,
        symbol="0700.HK",
        transaction_type="BUY",
        quantity_change=100,
        price_per_share=320.00,
        transaction_date=date(2024, 2, 15),
        notes="Additional Tencent purchase"
    )
    
    if success:
        print(f"   ✅ {message}")
    else:
        print(f"   ❌ {message}")
    
    # Test 4: Add a sell transaction
    print("\n4️⃣ Testing: Add Sell Transaction")
    success, message = analysis_manager.add_transaction(
        analysis_id=analysis_id,
        symbol="0005.HK",
        transaction_type="SELL",
        quantity_change=-500,
        price_per_share=40.00,
        transaction_date=date(2024, 3, 10),
        notes="Partial HSBC sale"
    )
    
    if success:
        print(f"   ✅ {message}")
    else:
        print(f"   ❌ {message}")
    
    # Test 5: Add dividend
    print("\n5️⃣ Testing: Add Dividend")
    success, message = analysis_manager.add_transaction(
        analysis_id=analysis_id,
        symbol="0700.HK",
        transaction_type="DIVIDEND",
        quantity_change=0,
        price_per_share=2.50,  # Dividend per share
        transaction_date=date(2024, 3, 1),
        notes="Tencent dividend payment"
    )
    
    if success:
        print(f"   ✅ {message}")
    else:
        print(f"   ❌ {message}")
    
    # Test 6: Get transactions
    print("\n6️⃣ Testing: Get All Transactions")
    transactions_df = analysis_manager.get_analysis_transactions(analysis_id)
    if not transactions_df.empty:
        print(f"   ✅ Retrieved {len(transactions_df)} transactions")
        for _, txn in transactions_df.iterrows():
            print(f"   📝 {txn['transaction_date']}: {txn['transaction_type']} {txn['symbol']} ({txn['quantity_change']} shares)")
    else:
        print("   ❌ No transactions found")
    
    # Test 7: Get current positions
    print("\n7️⃣ Testing: Get Current Positions")
    positions_df = analysis_manager.get_current_positions(analysis_id)
    if not positions_df.empty:
        print(f"   ✅ Retrieved {len(positions_df)} positions")
        for _, pos in positions_df.iterrows():
            print(f"   💰 {pos['symbol']}: {pos['current_quantity']} shares @ ${pos['avg_cost']:.2f}")
    else:
        print("   ❌ No positions found")
    
    # Test 8: Updated summary
    print("\n8️⃣ Testing: Updated Analysis Summary")
    summary_df = analysis_manager.get_analysis_summary(portfolio_id)
    if not summary_df.empty:
        latest = summary_df.iloc[0]
        print(f"   ✅ Analysis Updated:")
        print(f"   💰 Start Total: ${latest['start_total_value']:,.2f}")
        print(f"   💰 End Total: ${latest['end_total_value']:,.2f}")
        print(f"   📈 Total Gain/Loss: ${latest['total_value_gain_loss']:,.2f}")
        print(f"   💵 End Cash: ${latest['end_cash']:,.2f}")
    
    # Test 9: Error handling - try negative quantity
    print("\n9️⃣ Testing: Error Handling (Negative Quantity)")
    success, message = analysis_manager.add_transaction(
        analysis_id=analysis_id,
        symbol="0005.HK",
        transaction_type="SELL",
        quantity_change=-50000,  # More than we have
        price_per_share=40.00,
        transaction_date=date(2024, 3, 20),
        notes="Should fail - too many shares"
    )
    
    if not success:
        print(f"   ✅ Correctly rejected: {message}")
    else:
        print(f"   ❌ Should have failed: {message}")
    
    # Test 10: Cleanup
    print("\n🧹 Cleaning Up: Delete Test Analysis")
    success, message = analysis_manager.delete_analysis(analysis_id)
    if success:
        print(f"   ✅ {message}")
    else:
        print(f"   ❌ {message}")
    
    print("\n" + "=" * 60)
    print("🎉 PORTFOLIO ANALYSIS MANAGER TESTING COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    test_analysis_manager()