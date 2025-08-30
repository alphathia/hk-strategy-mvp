#!/usr/bin/env python3
"""
Complete Implementation Validation
Validates all components of the new Portfolio Analysis system
"""

import sys
import os
sys.path.append('src')

from database import DatabaseManager
from portfolio_analysis_manager import PortfolioAnalysisManager
from datetime import date, datetime
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def validate_database_schema():
    """Validate that all required tables and functions exist"""
    print("🗄️  VALIDATING DATABASE SCHEMA")
    print("-" * 40)
    
    db_manager = DatabaseManager()
    try:
        conn = db_manager.get_connection()
        
        # Check required tables
        required_tables = ['portfolio_analyses', 'portfolio_analysis_state_changes']
        
        with conn.cursor() as cur:
            cur.execute("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """)
            existing_tables = [row[0] for row in cur.fetchall()]
            
            print(f"📋 Existing tables: {len(existing_tables)}")
            
            all_tables_exist = True
            for table in required_tables:
                if table in existing_tables:
                    print(f"   ✅ {table}")
                else:
                    print(f"   ❌ {table} MISSING")
                    all_tables_exist = False
            
            # Check functions
            cur.execute("""
                SELECT routine_name FROM information_schema.routines 
                WHERE routine_schema = 'public' AND routine_type = 'FUNCTION'
                AND routine_name LIKE '%analysis%' OR routine_name LIKE 'get_current%'
                ORDER BY routine_name
            """)
            functions = [row[0] for row in cur.fetchall()]
            
            print(f"🔧 Database functions: {len(functions)}")
            for func in functions:
                print(f"   ✅ {func}()")
            
            # Check view
            cur.execute("""
                SELECT table_name FROM information_schema.views 
                WHERE table_schema = 'public' AND table_name LIKE '%analysis%'
            """)
            views = [row[0] for row in cur.fetchall()]
            
            print(f"👁️  Database views: {len(views)}")
            for view in views:
                print(f"   ✅ {view}")
        
        conn.close()
        return all_tables_exist and len(functions) >= 3 and len(views) >= 1
        
    except Exception as e:
        print(f"❌ Database validation error: {e}")
        return False

def validate_backend_functionality():
    """Validate that backend manager works correctly"""
    print("\n⚙️  VALIDATING BACKEND FUNCTIONALITY")
    print("-" * 40)
    
    try:
        db_manager = DatabaseManager()
        analysis_manager = PortfolioAnalysisManager(db_manager)
        
        print("✅ Managers instantiated successfully")
        
        # Test basic operations
        portfolio_id = "My_HKEX_ALL"
        
        # Create test analysis
        success, message, analysis_id = analysis_manager.create_analysis(
            portfolio_id=portfolio_id,
            analysis_name="Validation Test Analysis",
            start_date=date(2024, 6, 1),
            end_date=date(2024, 8, 31),
            start_cash=75000.0
        )
        
        if not success:
            print(f"❌ Analysis creation failed: {message}")
            return False
        
        print(f"✅ Analysis created: {analysis_id}")
        
        # Test summary retrieval
        summary_df = analysis_manager.get_analysis_summary(portfolio_id)
        if summary_df.empty:
            print("❌ Failed to retrieve analysis summary")
            return False
        
        print(f"✅ Summary retrieved: {len(summary_df)} analyses")
        
        # Test transaction addition
        success, message = analysis_manager.add_transaction(
            analysis_id=analysis_id,
            symbol="0005.HK",
            transaction_type="SELL",
            quantity_change=-100,
            price_per_share=40.0,
            transaction_date=date(2024, 7, 15),
            notes="Validation test transaction"
        )
        
        if not success:
            print(f"❌ Transaction failed: {message}")
            # Clean up and return
            analysis_manager.delete_analysis(analysis_id)
            return False
        
        print("✅ Transaction recorded successfully")
        
        # Test validation
        is_unique = analysis_manager.validate_analysis_name(portfolio_id, "Validation Test Analysis")
        if is_unique:
            print("❌ Validation failed: should detect duplicate name")
            analysis_manager.delete_analysis(analysis_id)
            return False
        
        print("✅ Name validation works correctly")
        
        # Clean up
        success, message = analysis_manager.delete_analysis(analysis_id)
        if not success:
            print(f"❌ Cleanup failed: {message}")
            return False
        
        print("✅ Cleanup successful")
        return True
        
    except Exception as e:
        print(f"❌ Backend validation error: {e}")
        return False

def validate_ui_integration():
    """Validate UI integration components"""
    print("\n🖥️  VALIDATING UI INTEGRATION")
    print("-" * 40)
    
    try:
        # Check that dashboard.py contains the new implementation
        with open('dashboard.py', 'r') as f:
            dashboard_content = f.read()
        
        required_elements = [
            'Portfolio Analysis Dashboard',
            'portfolio_analysis_manager',
            'PortfolioAnalysisManager',
            'Create New Portfolio Analysis',
            'Load Portfolio'
        ]
        
        all_elements_found = True
        for element in required_elements:
            if element in dashboard_content:
                print(f"   ✅ {element}")
            else:
                print(f"   ❌ {element} NOT FOUND")
                all_elements_found = False
        
        # Check sidebar navigation
        if '📈 Portfolio Analysis Dashboard' in dashboard_content:
            print("   ✅ Navigation updated correctly")
        else:
            print("   ❌ Navigation not updated")
            all_elements_found = False
        
        return all_elements_found
        
    except Exception as e:
        print(f"❌ UI validation error: {e}")
        return False

def validate_file_organization():
    """Validate that all necessary files are present and organized"""
    print("\n📁 VALIDATING FILE ORGANIZATION")
    print("-" * 40)
    
    required_files = [
        'src/portfolio_analysis_manager.py',
        'create_new_analysis_schema.sql',
        'remove_old_analysis_tables.sql',
        'test_analysis_manager.py',
        'test_dashboard_integration.py'
    ]
    
    all_files_exist = True
    for file_path in required_files:
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            print(f"   ✅ {file_path} ({size:,} bytes)")
        else:
            print(f"   ❌ {file_path} MISSING")
            all_files_exist = False
    
    # Check for sensitive information in source files
    print(f"\n🔒 SECURITY CHECK")
    sensitive_patterns = ['TBSG00dluck', 'trader:TBSG', 'password=TBSG', 'secret_key', 'api_key']
    files_to_check = ['dashboard.py', 'src/portfolio_analysis_manager.py']
    
    security_issues = []
    for file_path in files_to_check:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                content = f.read()
                for pattern in sensitive_patterns:
                    if pattern in content:
                        security_issues.append(f"{file_path} contains '{pattern}'")
    
    if security_issues:
        print("   ⚠️ Potential security issues found:")
        for issue in security_issues:
            print(f"      - {issue}")
    else:
        print("   ✅ No hardcoded credentials found")
    
    return all_files_exist and len(security_issues) == 0

def main():
    """Run complete validation"""
    print("=" * 60)
    print("🔍 COMPLETE IMPLEMENTATION VALIDATION")
    print("=" * 60)
    
    validations = [
        ("Database Schema", validate_database_schema),
        ("Backend Functionality", validate_backend_functionality), 
        ("UI Integration", validate_ui_integration),
        ("File Organization", validate_file_organization)
    ]
    
    results = {}
    
    for name, validator in validations:
        try:
            results[name] = validator()
        except Exception as e:
            print(f"\n❌ {name} validation failed with exception: {e}")
            results[name] = False
    
    # Final summary
    print("\n" + "=" * 60)
    print("📊 VALIDATION SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {name}: {status}")
        if result:
            passed += 1
    
    success_rate = (passed / total) * 100
    print(f"\n🎯 OVERALL RESULT: {success_rate:.0f}% ({passed}/{total} validations passed)")
    
    if success_rate == 100:
        print("🎉 ALL VALIDATIONS PASSED - IMPLEMENTATION IS COMPLETE!")
        return True
    else:
        print("⚠️ Some validations failed - please address issues before deployment")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)