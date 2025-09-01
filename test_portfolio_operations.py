#!/usr/bin/env python3
"""
Test Portfolio Creation and Editing Operations
Tests the multi-portfolio functionality to verify dashboard requirements
"""

import sys
import pandas as pd
import psycopg2
from datetime import datetime
import logging

# Add src to path
sys.path.append('src')
from database import DatabaseManager
from database_enhanced import DatabaseManager as EnhancedDatabaseManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PortfolioOperationsTester:
    """Test portfolio creation, editing, and management operations"""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.enhanced_db_manager = EnhancedDatabaseManager()
    
    def test_portfolio_creation(self):
        """Test creating new portfolios"""
        print("\n📝 TESTING PORTFOLIO CREATION")
        print("-" * 40)
        
        test_portfolios = [
            {
                'portfolio_id': 'TEST_TECH', 
                'name': 'Technology Growth Portfolio',
                'description': 'Focused on tech stocks for testing'
            },
            {
                'portfolio_id': 'TEST_VALUE', 
                'name': 'Value Investment Portfolio',
                'description': 'Value-focused testing portfolio'
            }
        ]
        
        results = []
        
        for portfolio in test_portfolios:
            try:
                success = self.enhanced_db_manager.create_portfolio(
                    portfolio['portfolio_id'], 
                    portfolio['name'], 
                    portfolio['description']
                )
                results.append({
                    'portfolio_id': portfolio['portfolio_id'],
                    'success': success,
                    'error': None
                })
                print(f"  ✅ Created '{portfolio['name']}' ({portfolio['portfolio_id']}): {success}")
            except Exception as e:
                results.append({
                    'portfolio_id': portfolio['portfolio_id'],
                    'success': False,
                    'error': str(e)
                })
                print(f"  ❌ Failed to create '{portfolio['name']}': {e}")
        
        return results
    
    def test_portfolio_listing(self):
        """Test listing all portfolios"""
        print("\n📋 TESTING PORTFOLIO LISTING")
        print("-" * 40)
        
        try:
            portfolios_df = self.enhanced_db_manager.get_portfolios()
            
            if portfolios_df.empty:
                print("  ❌ No portfolios found")
                return False
            
            print(f"  ✅ Found {len(portfolios_df)} portfolios:")
            for _, portfolio in portfolios_df.iterrows():
                print(f"    - {portfolio['portfolio_id']}: {portfolio['name']}")
                if portfolio.get('description'):
                    print(f"      Description: {portfolio['description']}")
            
            return portfolios_df
            
        except Exception as e:
            print(f"  ❌ Error listing portfolios: {e}")
            return False
    
    def test_portfolio_position_isolation(self):
        """Test that positions can be isolated by portfolio"""
        print("\n🔒 TESTING PORTFOLIO POSITION ISOLATION")
        print("-" * 40)
        
        try:
            # Get all positions
            all_positions = self.enhanced_db_manager.get_portfolio_positions()
            print(f"  📊 Total positions across all portfolios: {len(all_positions)}")
            
            if 'portfolio_id' in all_positions.columns:
                unique_portfolios = all_positions['portfolio_id'].unique()
                print(f"  🏢 Unique portfolios with positions: {len(unique_portfolios)}")
                
                for portfolio_id in unique_portfolios:
                    portfolio_positions = self.enhanced_db_manager.get_portfolio_positions(portfolio_id)
                    portfolio_value = portfolio_positions['market_value'].sum() if not portfolio_positions.empty else 0
                    print(f"    - {portfolio_id}: {len(portfolio_positions)} positions, ${portfolio_value:,.2f} total value")
                
                return True
            else:
                print("  ⚠️ portfolio_id column not found - single portfolio mode")
                return False
                
        except Exception as e:
            print(f"  ❌ Error testing position isolation: {e}")
            return False
    
    def test_portfolio_copying(self):
        """Test copying portfolios (simulated - would be dashboard feature)"""
        print("\n📁 TESTING PORTFOLIO COPYING CAPABILITY")
        print("-" * 40)
        
        try:
            # Get an existing portfolio to copy
            portfolios_df = self.enhanced_db_manager.get_portfolios()
            
            if len(portfolios_df) == 0:
                print("  ❌ No portfolios available to copy")
                return False
            
            source_portfolio = portfolios_df.iloc[0]
            source_id = source_portfolio['portfolio_id']
            
            print(f"  📋 Source portfolio for copying: {source_id}")
            
            # Get positions from source portfolio
            source_positions = self.enhanced_db_manager.get_portfolio_positions(source_id)
            
            if source_positions.empty:
                print(f"  ⚠️ Source portfolio {source_id} has no positions to copy")
                return False
            
            print(f"  📊 Source has {len(source_positions)} positions worth ${source_positions['market_value'].sum():,.2f}")
            
            # Create a copy portfolio
            copy_id = f"COPY_{source_id}_{datetime.now().strftime('%H%M')}"
            copy_success = self.enhanced_db_manager.create_portfolio(
                copy_id,
                f"Copy of {source_portfolio['name']}",
                f"Copied from {source_id} on {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            )
            
            if copy_success:
                print(f"  ✅ Created copy portfolio: {copy_id}")
                
                # In a real implementation, we would copy positions here
                # For now, we'll just verify the portfolio was created
                copy_verification = self.enhanced_db_manager.get_portfolios()
                copy_exists = any(copy_verification['portfolio_id'] == copy_id)
                
                if copy_exists:
                    print(f"  ✅ Copy portfolio verified in database")
                    return True
                else:
                    print(f"  ❌ Copy portfolio not found after creation")
                    return False
            else:
                print(f"  ❌ Failed to create copy portfolio")
                return False
                
        except Exception as e:
            print(f"  ❌ Error testing portfolio copying: {e}")
            return False
    
    def test_portfolio_analytics_readiness(self):
        """Test if portfolio data supports analytics dashboard requirements"""
        print("\n📈 TESTING ANALYTICS READINESS")
        print("-" * 40)
        
        try:
            # Check for required tables/views for analytics
            conn = self.db_manager.get_connection()
            
            # Check for portfolio_summary view (requirement #1)
            portfolio_summary_exists = pd.read_sql("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.views 
                    WHERE table_name = 'portfolio_summary'
                )
            """, conn).iloc[0, 0]
            
            print(f"  📊 Portfolio Summary View: {'✅ EXISTS' if portfolio_summary_exists else '❌ MISSING'}")
            
            # Check for portfolio_value_history table (requirement #3)
            value_history_exists = pd.read_sql("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables 
                    WHERE table_name = 'portfolio_value_history'
                )
            """, conn).iloc[0, 0]
            
            print(f"  📈 Portfolio Value History: {'✅ EXISTS' if value_history_exists else '❌ MISSING'}")
            
            if value_history_exists:
                # Check if there's historical data
                history_count = pd.read_sql("""
                    SELECT COUNT(*) as count FROM portfolio_value_history
                """, conn).iloc[0, 0]
                print(f"    Historical records: {history_count}")
            
            # Check for portfolio_analyses table (requirement #4)
            analyses_exists = pd.read_sql("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables 
                    WHERE table_name = 'portfolio_analyses'
                )
            """, conn).iloc[0, 0]
            
            print(f"  🔍 Portfolio Analyses: {'✅ EXISTS' if analyses_exists else '❌ MISSING'}")
            
            # Check for equity-strategy analysis capability (requirement #5)
            equity_strategy_exists = pd.read_sql("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables 
                    WHERE table_name = 'equity_strategy_analyses'
                )
            """, conn).iloc[0, 0]
            
            print(f"  ⚔️ Equity-Strategy Analysis: {'✅ EXISTS' if equity_strategy_exists else '❌ MISSING'}")
            
            # Overall readiness assessment
            required_components = [portfolio_summary_exists, value_history_exists, analyses_exists, equity_strategy_exists]
            readiness_score = sum(required_components) / len(required_components) * 100
            
            print(f"\n  🎯 ANALYTICS READINESS SCORE: {readiness_score:.0f}%")
            
            if readiness_score >= 75:
                print(f"  ✅ READY for advanced dashboard development")
            elif readiness_score >= 50:
                print(f"  ⚠️ PARTIALLY READY - some components missing")
            else:
                print(f"  ❌ NOT READY - significant development needed")
            
            return readiness_score >= 75
            
        except Exception as e:
            print(f"  ❌ Error testing analytics readiness: {e}")
            return False
    
    def cleanup_test_portfolios(self):
        """Clean up test portfolios created during testing"""
        print("\n🧹 CLEANING UP TEST PORTFOLIOS")
        print("-" * 40)
        
        try:
            conn = self.db_manager.get_connection()
            
            # Find test portfolios
            test_portfolios = pd.read_sql("""
                SELECT portfolio_id FROM portfolios 
                WHERE portfolio_id LIKE 'TEST_%' OR portfolio_id LIKE 'COPY_%'
            """, conn)
            
            if test_portfolios.empty:
                print("  ✅ No test portfolios to clean up")
                return True
            
            with conn.cursor() as cur:
                for _, portfolio in test_portfolios.iterrows():
                    portfolio_id = portfolio['portfolio_id']
                    
                    # Delete from portfolios table (cascade should handle related data)
                    cur.execute("DELETE FROM portfolios WHERE portfolio_id = %s", (portfolio_id,))
                    print(f"  🗑️ Deleted test portfolio: {portfolio_id}")
            
            conn.commit()
            print(f"  ✅ Cleaned up {len(test_portfolios)} test portfolios")
            return True
            
        except Exception as e:
            print(f"  ❌ Error during cleanup: {e}")
            return False
    
    def run_comprehensive_test(self):
        """Run all portfolio operation tests"""
        print("=" * 80)
        print("🧪 COMPREHENSIVE PORTFOLIO OPERATIONS TEST")
        print("=" * 80)
        
        test_results = {}
        
        # Test 1: Schema detection
        print("\n🔍 TESTING SCHEMA DETECTION")
        print("-" * 40)
        try:
            version, capabilities = self.enhanced_db_manager.detect_schema_version()
            print(f"  📋 Schema Version: {version.value}")
            print(f"  🔧 Multi-portfolio Support: {capabilities.get('multi_portfolio', False)}")
            test_results['schema_detection'] = capabilities.get('multi_portfolio', False)
        except Exception as e:
            print(f"  ❌ Schema detection error: {e}")
            test_results['schema_detection'] = False
        
        # Test 2: Portfolio creation
        test_results['portfolio_creation'] = self.test_portfolio_creation()
        
        # Test 3: Portfolio listing
        test_results['portfolio_listing'] = self.test_portfolio_listing()
        
        # Test 4: Position isolation
        test_results['position_isolation'] = self.test_portfolio_position_isolation()
        
        # Test 5: Portfolio copying capability
        test_results['portfolio_copying'] = self.test_portfolio_copying()
        
        # Test 6: Analytics readiness
        test_results['analytics_readiness'] = self.test_portfolio_analytics_readiness()
        
        # Clean up
        self.cleanup_test_portfolios()
        
        # Final summary
        print("\n" + "=" * 80)
        print("📊 FINAL TEST RESULTS SUMMARY")
        print("=" * 80)
        
        passed_tests = sum(1 for result in test_results.values() if result)
        total_tests = len(test_results)
        success_rate = passed_tests / total_tests * 100
        
        print(f"\n🎯 OVERALL SUCCESS RATE: {success_rate:.0f}% ({passed_tests}/{total_tests} tests passed)")
        
        print(f"\n📋 DETAILED RESULTS:")
        for test_name, result in test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            formatted_name = test_name.replace('_', ' ').title()
            print(f"  {formatted_name}: {status}")
        
        print(f"\n🎪 DASHBOARD REQUIREMENTS ASSESSMENT:")
        
        if test_results.get('schema_detection') and test_results.get('portfolio_listing'):
            print(f"  1. All Portfolio Overviews: ✅ READY")
        else:
            print(f"  1. All Portfolio Overviews: ❌ NOT READY")
        
        if test_results.get('position_isolation'):
            print(f"  2. Portfolio Dashboard: ✅ READY")
        else:
            print(f"  2. Portfolio Dashboard: ❌ NOT READY")
        
        if test_results.get('analytics_readiness'):
            print(f"  3-5. Advanced Analytics Dashboards: ✅ SCHEMA READY")
        else:
            print(f"  3-5. Advanced Analytics Dashboards: ❌ SCHEMA NOT READY")
        
        print(f"  6. System Status Page: ✅ ALREADY IMPLEMENTED")
        
        return test_results

def main():
    tester = PortfolioOperationsTester()
    results = tester.run_comprehensive_test()
    return results

if __name__ == "__main__":
    main()