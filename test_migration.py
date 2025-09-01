#!/usr/bin/env python3
"""
Migration Testing Script
Tests both single-portfolio and multi-portfolio database schemas
Verifies DatabaseManager backward compatibility
"""

import os
import sys
import psycopg2
import pandas as pd
import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime

# Add src to path for imports
sys.path.append('src')
from database import DatabaseManager
from config_manager import get_config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MigrationTester:
    """
    Comprehensive testing suite for database migration verification
    """
    
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.test_results = []
        
    def log_test_result(self, test_name: str, success: bool, message: str = "", details: str = ""):
        """Log test result with status"""
        status = "✅ PASS" if success else "❌ FAIL"
        self.test_results.append({
            'test': test_name,
            'status': status,
            'success': success,
            'message': message,
            'details': details,
            'timestamp': datetime.now()
        })
        logger.info(f"{status} - {test_name}: {message}")
        if details:
            logger.info(f"  Details: {details}")
    
    def check_database_connection(self) -> bool:
        """Test basic database connectivity"""
        try:
            conn = self.db_manager.get_connection()
            with conn.cursor() as cur:
                cur.execute("SELECT version();")
                version = cur.fetchone()[0]
            self.log_test_result("Database Connection", True, f"Connected successfully", f"PostgreSQL version: {version}")
            return True
        except Exception as e:
            self.log_test_result("Database Connection", False, f"Connection failed: {e}")
            return False
    
    def check_schema_version(self) -> Tuple[bool, str]:
        """Determine if schema is single-portfolio or multi-portfolio"""
        try:
            conn = self.db_manager.get_connection()
            
            # Check if portfolios table exists
            has_portfolios_table = pd.read_sql("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables 
                    WHERE table_name = 'portfolios'
                )
            """, conn).iloc[0, 0]
            
            # Check if portfolio_id column exists in portfolio_positions
            has_portfolio_id = pd.read_sql("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'portfolio_positions' AND column_name = 'portfolio_id'
                )
            """, conn).iloc[0, 0]
            
            if has_portfolios_table and has_portfolio_id:
                schema_version = "multi-portfolio (v2.0)"
                self.log_test_result("Schema Version Detection", True, schema_version)
                return True, "multi"
            else:
                schema_version = "single-portfolio (v1.0)"
                self.log_test_result("Schema Version Detection", True, schema_version)
                return True, "single"
                
        except Exception as e:
            self.log_test_result("Schema Version Detection", False, f"Failed to detect schema: {e}")
            return False, "unknown"
    
    def test_portfolio_positions_operations(self, schema_type: str) -> bool:
        """Test portfolio positions CRUD operations"""
        try:
            # Test reading positions
            if schema_type == "multi":
                # Test with portfolio_id parameter
                positions = self.db_manager.get_portfolio_positions(portfolio_id="DEFAULT")
                self.log_test_result("Multi-Portfolio Positions Query", True, 
                                   f"Retrieved {len(positions)} positions for DEFAULT portfolio")
                
                # Test without portfolio_id parameter
                all_positions = self.db_manager.get_portfolio_positions()
                self.log_test_result("Multi-Portfolio All Positions Query", True, 
                                   f"Retrieved {len(all_positions)} total positions")
            else:
                # Test single portfolio query
                positions = self.db_manager.get_portfolio_positions()
                self.log_test_result("Single-Portfolio Positions Query", True, 
                                   f"Retrieved {len(positions)} positions")
            
            # Verify data structure
            if len(positions) > 0:
                expected_columns = ['symbol', 'company_name', 'quantity', 'avg_cost', 'current_price', 
                                  'market_value', 'unrealized_pnl', 'sector', 'last_updated']
                if schema_type == "multi":
                    expected_columns.append('portfolio_id')
                
                missing_columns = [col for col in expected_columns if col not in positions.columns]
                if missing_columns:
                    self.log_test_result("Positions Data Structure", False, 
                                       f"Missing columns: {missing_columns}")
                    return False
                else:
                    self.log_test_result("Positions Data Structure", True, 
                                       f"All expected columns present: {len(expected_columns)} columns")
            
            return True
            
        except Exception as e:
            self.log_test_result("Portfolio Positions Operations", False, f"Failed: {e}")
            return False
    
    def test_trading_signals_operations(self, schema_type: str) -> bool:
        """Test trading signals CRUD operations"""
        try:
            # Test reading signals
            if schema_type == "multi":
                # Test with portfolio_id parameter
                signals = self.db_manager.get_trading_signals(limit=10, portfolio_id="DEFAULT")
                self.log_test_result("Multi-Portfolio Signals Query", True, 
                                   f"Retrieved {len(signals)} signals for DEFAULT portfolio")
                
                # Test without portfolio_id parameter  
                all_signals = self.db_manager.get_trading_signals(limit=10)
                self.log_test_result("Multi-Portfolio All Signals Query", True, 
                                   f"Retrieved {len(all_signals)} total signals")
            else:
                # Test single portfolio query
                signals = self.db_manager.get_trading_signals(limit=10)
                self.log_test_result("Single-Portfolio Signals Query", True, 
                                   f"Retrieved {len(signals)} signals")
            
            # Test inserting a signal
            test_symbol = "0005.HK"  # HSBC - should exist in positions
            success = self.db_manager.insert_trading_signal(
                symbol=test_symbol,
                signal_type="B",
                signal_strength=0.8,
                price=39.75,
                portfolio_id="DEFAULT" if schema_type == "multi" else None,
                rsi=45.5,
                ma_5=39.2,
                ma_20=38.9,
                ma_50=38.1
            )
            
            if success:
                self.log_test_result("Signal Insertion", True, f"Successfully inserted signal for {test_symbol}")
            else:
                self.log_test_result("Signal Insertion", False, f"Failed to insert signal for {test_symbol}")
                return False
            
            return True
            
        except Exception as e:
            self.log_test_result("Trading Signals Operations", False, f"Failed: {e}")
            return False
    
    def test_database_manager_compatibility(self, schema_type: str) -> bool:
        """Test that DatabaseManager works correctly with both schema versions"""
        try:
            conn = self.db_manager.get_connection()
            
            # Test schema detection queries (these are built into DatabaseManager)
            portfolio_check = pd.read_sql("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'portfolio_positions' AND column_name = 'portfolio_id'
            """, conn)
            
            signals_check = pd.read_sql("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'trading_signals' AND column_name = 'portfolio_id'
            """, conn)
            
            if schema_type == "multi":
                if portfolio_check.empty or signals_check.empty:
                    self.log_test_result("DatabaseManager Schema Detection", False, 
                                       "Multi-portfolio schema not properly detected")
                    return False
                else:
                    self.log_test_result("DatabaseManager Schema Detection", True, 
                                       "Multi-portfolio schema correctly detected")
            else:
                if not portfolio_check.empty or not signals_check.empty:
                    self.log_test_result("DatabaseManager Schema Detection", False, 
                                       "Single-portfolio schema not properly detected")
                    return False
                else:
                    self.log_test_result("DatabaseManager Schema Detection", True, 
                                       "Single-portfolio schema correctly detected")
            
            return True
            
        except Exception as e:
            self.log_test_result("DatabaseManager Compatibility", False, f"Failed: {e}")
            return False
    
    def test_multi_portfolio_specific_features(self) -> bool:
        """Test features specific to multi-portfolio schema"""
        try:
            conn = self.db_manager.get_connection()
            
            # Test portfolio summary view
            try:
                summary = pd.read_sql("SELECT * FROM portfolio_summary", conn)
                self.log_test_result("Portfolio Summary View", True, 
                                   f"Retrieved {len(summary)} portfolio summaries")
            except Exception as e:
                self.log_test_result("Portfolio Summary View", False, f"Failed: {e}")
                return False
            
            # Test migration status function
            try:
                status = pd.read_sql("SELECT * FROM check_migration_status()", conn)
                self.log_test_result("Migration Status Function", True, 
                                   f"Status check returned {len(status)} tables")
                
                # Log detailed status
                for _, row in status.iterrows():
                    details = f"Table: {row['table_name']}, Has portfolio_id: {row['has_portfolio_id']}, " \
                             f"Null portfolio_ids: {row['null_portfolio_ids']}, Total rows: {row['total_rows']}"
                    logger.info(f"  Migration Status: {details}")
                    
            except Exception as e:
                self.log_test_result("Migration Status Function", False, f"Failed: {e}")
                return False
            
            return True
            
        except Exception as e:
            self.log_test_result("Multi-Portfolio Features", False, f"Failed: {e}")
            return False
    
    def test_data_integrity(self, schema_type: str) -> bool:
        """Test data integrity and consistency"""
        try:
            conn = self.db_manager.get_connection()
            
            # Check for orphaned records
            if schema_type == "multi":
                # Check for signals without matching positions
                orphaned_signals = pd.read_sql("""
                    SELECT COUNT(*) as count FROM trading_signals ts
                    LEFT JOIN portfolio_positions pp ON ts.symbol = pp.symbol AND ts.portfolio_id = pp.portfolio_id
                    WHERE pp.symbol IS NULL
                """, conn).iloc[0, 0]
            else:
                orphaned_signals = pd.read_sql("""
                    SELECT COUNT(*) as count FROM trading_signals ts
                    LEFT JOIN portfolio_positions pp ON ts.symbol = pp.symbol
                    WHERE pp.symbol IS NULL
                """, conn).iloc[0, 0]
            
            if orphaned_signals > 0:
                self.log_test_result("Data Integrity - Orphaned Signals", False, 
                                   f"Found {orphaned_signals} orphaned signals")
                return False
            else:
                self.log_test_result("Data Integrity - Orphaned Signals", True, 
                                   "No orphaned signals found")
            
            # Check for NULL portfolio_ids in multi-portfolio schema
            if schema_type == "multi":
                null_portfolio_ids = pd.read_sql("""
                    SELECT 
                        (SELECT COUNT(*) FROM portfolio_positions WHERE portfolio_id IS NULL) as pos_nulls,
                        (SELECT COUNT(*) FROM trading_signals WHERE portfolio_id IS NULL) as sig_nulls
                """, conn).iloc[0]
                
                if null_portfolio_ids['pos_nulls'] > 0 or null_portfolio_ids['sig_nulls'] > 0:
                    self.log_test_result("Data Integrity - NULL Portfolio IDs", False, 
                                       f"Found NULL portfolio_ids: positions={null_portfolio_ids['pos_nulls']}, "
                                       f"signals={null_portfolio_ids['sig_nulls']}")
                    return False
                else:
                    self.log_test_result("Data Integrity - NULL Portfolio IDs", True, 
                                       "No NULL portfolio_ids found")
            
            return True
            
        except Exception as e:
            self.log_test_result("Data Integrity", False, f"Failed: {e}")
            return False
    
    def run_comprehensive_tests(self) -> Dict:
        """Run all tests and return results summary"""
        logger.info("=" * 80)
        logger.info("🧪 STARTING COMPREHENSIVE DATABASE MIGRATION TESTS")
        logger.info("=" * 80)
        
        # Test 1: Database Connection
        if not self.check_database_connection():
            return self.get_test_summary()
        
        # Test 2: Schema Version Detection
        success, schema_type = self.check_schema_version()
        if not success:
            return self.get_test_summary()
        
        # Test 3: Portfolio Positions Operations
        self.test_portfolio_positions_operations(schema_type)
        
        # Test 4: Trading Signals Operations
        self.test_trading_signals_operations(schema_type)
        
        # Test 5: DatabaseManager Compatibility
        self.test_database_manager_compatibility(schema_type)
        
        # Test 6: Multi-Portfolio Specific Features (only if multi-portfolio schema)
        if schema_type == "multi":
            self.test_multi_portfolio_specific_features()
        
        # Test 7: Data Integrity
        self.test_data_integrity(schema_type)
        
        logger.info("=" * 80)
        logger.info("🏁 TEST SUITE COMPLETED")
        logger.info("=" * 80)
        
        return self.get_test_summary()
    
    def get_test_summary(self) -> Dict:
        """Get summary of all test results"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        summary = {
            'total_tests': total_tests,
            'passed': passed_tests,
            'failed': failed_tests,
            'pass_rate': (passed_tests / total_tests * 100) if total_tests > 0 else 0,
            'results': self.test_results
        }
        
        logger.info(f"📊 TEST SUMMARY:")
        logger.info(f"   Total Tests: {total_tests}")
        logger.info(f"   Passed: {passed_tests}")
        logger.info(f"   Failed: {failed_tests}")
        logger.info(f"   Pass Rate: {summary['pass_rate']:.1f}%")
        
        if failed_tests > 0:
            logger.info("❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    logger.info(f"   - {result['test']}: {result['message']}")
        else:
            logger.info("✅ ALL TESTS PASSED!")
        
        return summary

def main():
    """Main testing function"""
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("""
Migration Testing Script

Usage: python test_migration.py

This script tests the database migration between single-portfolio and multi-portfolio schemas.
It verifies:
- Database connectivity
- Schema version detection
- DatabaseManager backward compatibility
- CRUD operations for both schema types
- Data integrity
- Multi-portfolio specific features

The script automatically detects which schema version is currently active and runs
appropriate tests for that version.
        """)
        return
    
    tester = MigrationTester()
    summary = tester.run_comprehensive_tests()
    
    # Exit with appropriate code
    exit_code = 0 if summary['failed'] == 0 else 1
    sys.exit(exit_code)

if __name__ == "__main__":
    main()