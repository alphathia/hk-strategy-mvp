#!/usr/bin/env python3
"""
Test Dashboard Integration with Portfolio Analysis
"""

import sys
sys.path.append('src')

from database import DatabaseManager
from portfolio_analysis_manager import PortfolioAnalysisManager
from datetime import date
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_dashboard_integration():
    """Test the integration between dashboard and portfolio analysis"""
    
    print("=" * 60)
    print("🧪 TESTING DASHBOARD INTEGRATION")
    print("=" * 60)
    
    # Initialize managers (same as dashboard would)
    db_manager = DatabaseManager()
    analysis_manager = PortfolioAnalysisManager(db_manager)
    
    print("\n✅ Managers initialized successfully")
    
    # Test the workflow that the dashboard would use
    portfolio_id = "My_HKEX_ALL"
    
    # Step 1: Create analysis (like dashboard create dialog)
    print(f"\n1️⃣ Creating analysis for portfolio: {portfolio_id}")
    
    success, message, analysis_id = analysis_manager.create_analysis(
        portfolio_id=portfolio_id,
        analysis_name="Dashboard Integration Test",
        start_date=date(2024, 1, 1),
        end_date=date(2024, 3, 31),
        start_cash=50000.0
    )
    
    if success:
        print(f"   ✅ {message} (ID: {analysis_id})")
    else:
        print(f"   ❌ {message}")
        return False
    
    # Step 2: Get analysis summary (like dashboard table display)
    print(f"\n2️⃣ Retrieving analysis summary")
    
    summary_df = analysis_manager.get_analysis_summary(portfolio_id)
    if not summary_df.empty:
        print(f"   ✅ Retrieved {len(summary_df)} analyses")
        latest = summary_df.iloc[0]
        print(f"   📊 Latest: {latest['name']}")
        print(f"   💰 Start Total: ${latest['start_total_value']:,.2f}")
        print(f"   📅 Period: {latest['start_date']} to {latest['end_date']}")
    else:
        print("   ❌ No analyses retrieved")
        return False
    
    # Step 3: Add transaction (like dashboard transaction management)
    print(f"\n3️⃣ Adding sample transaction")
    
    success, message = analysis_manager.add_transaction(
        analysis_id=analysis_id,
        symbol="0700.HK",
        transaction_type="BUY",
        quantity_change=200,
        price_per_share=300.00,
        transaction_date=date(2024, 2, 1),
        notes="Dashboard integration test transaction"
    )
    
    if success:
        print(f"   ✅ {message}")
    else:
        print(f"   ❌ {message}")
        return False
    
    # Step 4: Get updated summary
    print(f"\n4️⃣ Checking updated summary")
    
    updated_summary_df = analysis_manager.get_analysis_summary(portfolio_id)
    if not updated_summary_df.empty:
        updated = updated_summary_df.iloc[0]
        print(f"   ✅ Updated analysis retrieved")
        print(f"   💵 Updated End Cash: ${updated['end_cash']:,.2f}")
        print(f"   📈 Total Value Change: ${updated['total_value_gain_loss']:+,.2f}")
    else:
        print("   ❌ Could not retrieve updated summary")
        return False
    
    # Step 5: Get transaction history
    print(f"\n5️⃣ Retrieving transaction history")
    
    transactions_df = analysis_manager.get_analysis_transactions(analysis_id)
    if not transactions_df.empty:
        print(f"   ✅ Retrieved {len(transactions_df)} transactions")
        for _, txn in transactions_df.iterrows():
            print(f"   📝 {txn['transaction_date']}: {txn['transaction_type']} {txn['symbol']} ({txn['quantity_change']})")
    else:
        print("   ❌ No transactions retrieved")
        return False
    
    # Step 6: Test validation (like dashboard would)
    print(f"\n6️⃣ Testing validation")
    
    # Test duplicate name validation
    is_unique = analysis_manager.validate_analysis_name(portfolio_id, "Dashboard Integration Test")
    if not is_unique:
        print("   ✅ Correctly detected duplicate analysis name")
    else:
        print("   ❌ Failed to detect duplicate analysis name")
        return False
    
    # Test new name validation
    is_unique_new = analysis_manager.validate_analysis_name(portfolio_id, "New Unique Name")
    if is_unique_new:
        print("   ✅ Correctly validated unique analysis name")
    else:
        print("   ❌ Incorrectly rejected unique analysis name")
        return False
    
    # Step 7: Cleanup
    print(f"\n🧹 Cleaning up test analysis")
    
    success, message = analysis_manager.delete_analysis(analysis_id)
    if success:
        print(f"   ✅ {message}")
    else:
        print(f"   ❌ {message}")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 DASHBOARD INTEGRATION TEST PASSED!")
    print("=" * 60)
    
    print(f"\n📋 Integration Summary:")
    print(f"   ✅ Analysis Manager initialization")
    print(f"   ✅ Analysis creation workflow")
    print(f"   ✅ Summary retrieval and display")
    print(f"   ✅ Transaction management")
    print(f"   ✅ Real-time updates")
    print(f"   ✅ Transaction history")
    print(f"   ✅ Validation logic")
    print(f"   ✅ Cleanup operations")
    
    return True

if __name__ == "__main__":
    success = test_dashboard_integration()
    if not success:
        print("\n❌ Integration test failed!")
        sys.exit(1)
    else:
        print(f"\n🚀 Ready for dashboard testing!")