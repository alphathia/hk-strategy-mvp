#!/usr/bin/env python3
"""
Database State Investigation Script
Detailed analysis of current database schema to identify inconsistencies
"""

import sys
import pandas as pd
import psycopg2
import logging
from typing import Dict, List, Any

# Add src to path
sys.path.append('src')
from database import DatabaseManager
from database_enhanced import DatabaseManager as EnhancedDatabaseManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseInvestigator:
    """Detailed database schema investigation"""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.enhanced_db_manager = EnhancedDatabaseManager()
    
    def get_raw_database_info(self) -> Dict[str, Any]:
        """Get raw database information without interpretation"""
        try:
            conn = self.db_manager.get_connection()
            
            # Check all tables that exist
            tables_query = """
                SELECT table_name, table_type 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """
            tables = pd.read_sql(tables_query, conn)
            
            # Check columns for key tables
            columns_info = {}
            key_tables = ['portfolios', 'portfolio_positions', 'trading_signals', 'price_history']
            
            for table in key_tables:
                # Check if table exists first
                table_exists = pd.read_sql(f"""
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.tables 
                        WHERE table_name = '{table}'
                    )
                """, conn).iloc[0, 0]
                
                if table_exists:
                    columns_query = f"""
                        SELECT column_name, data_type, is_nullable, column_default
                        FROM information_schema.columns 
                        WHERE table_name = '{table}'
                        ORDER BY ordinal_position;
                    """
                    columns_info[table] = pd.read_sql(columns_query, conn)
                else:
                    columns_info[table] = None
            
            # Check constraints
            constraints_query = """
                SELECT 
                    constraint_name, 
                    constraint_type, 
                    table_name,
                    constraint_schema
                FROM information_schema.table_constraints 
                WHERE table_schema = 'public'
                  AND table_name IN ('portfolios', 'portfolio_positions', 'trading_signals', 'price_history')
                ORDER BY table_name, constraint_type;
            """
            constraints = pd.read_sql(constraints_query, conn)
            
            # Check foreign keys specifically
            foreign_keys_query = """
                SELECT 
                    tc.constraint_name,
                    tc.table_name,
                    kcu.column_name,
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name 
                FROM 
                    information_schema.table_constraints AS tc 
                    JOIN information_schema.key_column_usage AS kcu
                      ON tc.constraint_name = kcu.constraint_name
                      AND tc.table_schema = kcu.table_schema
                    JOIN information_schema.constraint_column_usage AS ccu
                      ON ccu.constraint_name = tc.constraint_name
                      AND ccu.table_schema = tc.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY' 
                  AND tc.table_schema='public';
            """
            foreign_keys = pd.read_sql(foreign_keys_query, conn)
            
            # Check indexes
            indexes_query = """
                SELECT 
                    tablename, 
                    indexname, 
                    indexdef
                FROM pg_indexes 
                WHERE schemaname = 'public'
                  AND tablename IN ('portfolios', 'portfolio_positions', 'trading_signals', 'price_history')
                ORDER BY tablename, indexname;
            """
            indexes = pd.read_sql(indexes_query, conn)
            
            # Check views
            views_query = """
                SELECT table_name, view_definition
                FROM information_schema.views 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """
            views = pd.read_sql(views_query, conn)
            
            # Check functions
            functions_query = """
                SELECT routine_name, routine_type
                FROM information_schema.routines 
                WHERE routine_schema = 'public'
                ORDER BY routine_name;
            """
            functions = pd.read_sql(functions_query, conn)
            
            return {
                'tables': tables,
                'columns': columns_info,
                'constraints': constraints,
                'foreign_keys': foreign_keys,
                'indexes': indexes,
                'views': views,
                'functions': functions
            }
            
        except Exception as e:
            logger.error(f"Error getting database info: {e}")
            return {}
    
    def compare_detection_methods(self) -> Dict[str, Any]:
        """Compare detection results from both database managers"""
        
        # Standard database manager detection
        try:
            conn = self.db_manager.get_connection()
            
            # Mimic the detection logic from database.py
            portfolio_id_check = pd.read_sql("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'portfolio_positions' AND column_name = 'portfolio_id'
            """, conn)
            standard_has_portfolio_id = not portfolio_id_check.empty
            
            standard_result = {
                'method': 'Standard (database.py)',
                'has_portfolio_id_column': standard_has_portfolio_id,
                'schema_version': 'multi-portfolio' if standard_has_portfolio_id else 'single-portfolio'
            }
        except Exception as e:
            standard_result = {
                'method': 'Standard (database.py)',
                'error': str(e)
            }
        
        # Enhanced database manager detection
        try:
            enhanced_version, enhanced_capabilities = self.enhanced_db_manager.detect_schema_version(force_refresh=True)
            enhanced_result = {
                'method': 'Enhanced (database_enhanced.py)',
                'schema_version': enhanced_version.value,
                'capabilities': enhanced_capabilities
            }
        except Exception as e:
            enhanced_result = {
                'method': 'Enhanced (database_enhanced.py)',
                'error': str(e)
            }
        
        return {
            'standard': standard_result,
            'enhanced': enhanced_result
        }
    
    def analyze_data_content(self) -> Dict[str, Any]:
        """Analyze actual data content in tables"""
        try:
            conn = self.db_manager.get_connection()
            
            analysis = {}
            
            # Check portfolio_positions data
            if self.table_exists('portfolio_positions'):
                pos_query = """
                    SELECT 
                        COUNT(*) as total_positions,
                        COUNT(DISTINCT symbol) as unique_symbols
                    FROM portfolio_positions
                """
                pos_data = pd.read_sql(pos_query, conn)
                analysis['portfolio_positions'] = pos_data.iloc[0].to_dict()
                
                # Check if portfolio_id column exists and has data
                try:
                    portfolio_id_query = """
                        SELECT 
                            COUNT(*) as total_with_portfolio_id,
                            COUNT(DISTINCT portfolio_id) as unique_portfolio_ids,
                            array_agg(DISTINCT portfolio_id) as portfolio_id_values
                        FROM portfolio_positions 
                        WHERE portfolio_id IS NOT NULL
                    """
                    portfolio_id_data = pd.read_sql(portfolio_id_query, conn)
                    analysis['portfolio_positions_portfolio_id'] = portfolio_id_data.iloc[0].to_dict()
                except:
                    analysis['portfolio_positions_portfolio_id'] = {'error': 'portfolio_id column does not exist'}
            
            # Check portfolios table if it exists
            if self.table_exists('portfolios'):
                portfolios_query = """
                    SELECT 
                        COUNT(*) as total_portfolios,
                        array_agg(portfolio_id) as portfolio_ids,
                        array_agg(name) as portfolio_names
                    FROM portfolios
                """
                portfolios_data = pd.read_sql(portfolios_query, conn)
                analysis['portfolios'] = portfolios_data.iloc[0].to_dict()
            else:
                analysis['portfolios'] = {'exists': False}
            
            # Check trading_signals
            if self.table_exists('trading_signals'):
                signals_query = """
                    SELECT 
                        COUNT(*) as total_signals,
                        COUNT(DISTINCT symbol) as unique_symbols_with_signals
                    FROM trading_signals
                """
                signals_data = pd.read_sql(signals_query, conn)
                analysis['trading_signals'] = signals_data.iloc[0].to_dict()
                
                # Check portfolio_id in signals
                try:
                    signals_portfolio_query = """
                        SELECT 
                            COUNT(*) as signals_with_portfolio_id,
                            COUNT(DISTINCT portfolio_id) as unique_portfolio_ids_signals,
                            array_agg(DISTINCT portfolio_id) as portfolio_id_values_signals
                        FROM trading_signals 
                        WHERE portfolio_id IS NOT NULL
                    """
                    signals_portfolio_data = pd.read_sql(signals_portfolio_query, conn)
                    analysis['trading_signals_portfolio_id'] = signals_portfolio_data.iloc[0].to_dict()
                except:
                    analysis['trading_signals_portfolio_id'] = {'error': 'portfolio_id column does not exist'}
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing data content: {e}")
            return {'error': str(e)}
    
    def table_exists(self, table_name: str) -> bool:
        """Check if a table exists"""
        try:
            conn = self.db_manager.get_connection()
            result = pd.read_sql(f"""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables 
                    WHERE table_name = '{table_name}'
                )
            """, conn)
            return result.iloc[0, 0]
        except:
            return False
    
    def run_full_investigation(self) -> None:
        """Run complete database investigation"""
        print("=" * 80)
        print("🔍 COMPREHENSIVE DATABASE STATE INVESTIGATION")
        print("=" * 80)
        
        # Raw database information
        print("\n📊 RAW DATABASE SCHEMA INFORMATION")
        print("-" * 50)
        
        db_info = self.get_raw_database_info()
        
        if 'tables' in db_info:
            print(f"Tables found: {len(db_info['tables'])}")
            for _, table in db_info['tables'].iterrows():
                print(f"  - {table['table_name']} ({table['table_type']})")
        
        print("\n📋 COLUMN INFORMATION FOR KEY TABLES")
        print("-" * 50)
        
        for table, columns in db_info.get('columns', {}).items():
            if columns is not None:
                print(f"\n{table}:")
                for _, col in columns.iterrows():
                    nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                    print(f"  - {col['column_name']}: {col['data_type']} {nullable}")
            else:
                print(f"\n{table}: TABLE DOES NOT EXIST")
        
        print(f"\n🔗 FOREIGN KEYS")
        print("-" * 50)
        foreign_keys = db_info.get('foreign_keys', pd.DataFrame())
        if not foreign_keys.empty:
            for _, fk in foreign_keys.iterrows():
                print(f"  - {fk['table_name']}.{fk['column_name']} → {fk['foreign_table_name']}.{fk['foreign_column_name']}")
        else:
            print("  No foreign keys found")
        
        print(f"\n🔍 VIEWS")
        print("-" * 50)
        views = db_info.get('views', pd.DataFrame())
        if not views.empty:
            for _, view in views.iterrows():
                print(f"  - {view['table_name']}")
        else:
            print("  No views found")
        
        print(f"\n⚙️ FUNCTIONS")
        print("-" * 50)
        functions = db_info.get('functions', pd.DataFrame())
        if not functions.empty:
            for _, func in functions.iterrows():
                print(f"  - {func['routine_name']} ({func['routine_type']})")
        else:
            print("  No custom functions found")
        
        # Detection method comparison
        print(f"\n🔍 DETECTION METHOD COMPARISON")
        print("-" * 50)
        
        detection_comparison = self.compare_detection_methods()
        
        for key, result in detection_comparison.items():
            print(f"\n{result['method']}:")
            if 'error' in result:
                print(f"  ❌ Error: {result['error']}")
            else:
                if key == 'standard':
                    print(f"  Has portfolio_id column: {result.get('has_portfolio_id_column', 'unknown')}")
                    print(f"  Detected schema: {result.get('schema_version', 'unknown')}")
                else:  # enhanced
                    print(f"  Detected schema version: {result.get('schema_version', 'unknown')}")
                    capabilities = result.get('capabilities', {})
                    print(f"  Multi-portfolio support: {capabilities.get('multi_portfolio', 'unknown')}")
                    print(f"  Backward compatible: {capabilities.get('backward_compatible', 'unknown')}")
                    if 'warning' in capabilities:
                        print(f"  ⚠️ Warning: {capabilities['warning']}")
        
        # Data content analysis
        print(f"\n📊 DATA CONTENT ANALYSIS")
        print("-" * 50)
        
        data_analysis = self.analyze_data_content()
        
        for table, info in data_analysis.items():
            if isinstance(info, dict):
                print(f"\n{table}:")
                if 'error' in info:
                    print(f"  ❌ Error: {info['error']}")
                elif 'exists' in info and not info['exists']:
                    print(f"  ❌ Table does not exist")
                else:
                    for key, value in info.items():
                        if key != 'error':
                            print(f"  {key}: {value}")
        
        # Final diagnosis
        print(f"\n🏥 DIAGNOSIS AND RECOMMENDATIONS")
        print("=" * 80)
        
        # Determine the actual state
        has_portfolios_table = self.table_exists('portfolios')
        has_portfolio_id_in_positions = False
        
        try:
            conn = self.db_manager.get_connection()
            portfolio_id_check = pd.read_sql("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'portfolio_positions' AND column_name = 'portfolio_id'
                )
            """, conn)
            has_portfolio_id_in_positions = portfolio_id_check.iloc[0, 0]
        except:
            has_portfolio_id_in_positions = False
        
        print(f"📋 ACTUAL DATABASE STATE:")
        print(f"  - portfolios table exists: {has_portfolios_table}")
        print(f"  - portfolio_positions has portfolio_id: {has_portfolio_id_in_positions}")
        
        if has_portfolios_table and has_portfolio_id_in_positions:
            print(f"  🎯 ACTUAL SCHEMA: Multi-Portfolio (Phase 1 completed)")
            print(f"  📝 ISSUE: Enhanced detector is correct, standard detector is wrong")
            print(f"  🔧 SOLUTION: Update migration logic to handle existing multi-portfolio state")
        elif has_portfolios_table or has_portfolio_id_in_positions:
            print(f"  🎯 ACTUAL SCHEMA: Partial Migration State (Inconsistent)")
            print(f"  📝 ISSUE: Database in partial migration state")
            print(f"  🔧 SOLUTION: Clean up partial state or complete migration")
        else:
            print(f"  🎯 ACTUAL SCHEMA: Single-Portfolio (Original)")
            print(f"  📝 ISSUE: Enhanced detector giving false positive")
            print(f"  🔧 SOLUTION: Fix enhanced detector logic")

def main():
    investigator = DatabaseInvestigator()
    investigator.run_full_investigation()

if __name__ == "__main__":
    main()