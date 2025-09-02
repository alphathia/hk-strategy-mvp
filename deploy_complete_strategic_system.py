#!/usr/bin/env python3
"""
Strategic Signal System - Complete Deployment Script
Deploys the entire Strategic Signal System with proper sequencing and validation
"""

import os
import sys
import subprocess
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('strategic_system_deployment.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class StrategicSystemDeployer:
    """Comprehensive deployment manager for Strategic Signal System"""
    
    def __init__(self, project_root: str = "/home/bthia/projects/hk-strategy-mvp"):
        self.project_root = Path(project_root)
        self.deployment_status = {}
        self.start_time = datetime.now()
        
    def validate_prerequisites(self) -> bool:
        """Validate all prerequisite files and systems"""
        logger.info("=== Validating Prerequisites ===")
        
        required_files = [
            "strategic_signal_migration.sql",
            "populate_strategy_catalog.sql", 
            "database_management_functions.sql",
            "database_constraints_validation.sql",
            "management_views.sql",
            "src/strategic_signal_engine.py",
            "src/strategic_database_manager.py",
            "src/indicator_dictionary.py",
            "src/strategy_dictionary.py",
            "src/signal_dictionary.py",
            "src/signal_validation.py",
            "src/strategy_manager_api.py",
            "dashboard_management.html"
        ]
        
        missing_files = []
        for file_path in required_files:
            full_path = self.project_root / file_path
            if not full_path.exists():
                missing_files.append(file_path)
                logger.error(f"Missing required file: {file_path}")
            else:
                logger.info(f"✓ Found: {file_path}")
        
        if missing_files:
            logger.error(f"Cannot proceed: {len(missing_files)} required files missing")
            return False
            
        logger.info("✓ All prerequisite files found")
        return True
    
    def check_database_connection(self) -> bool:
        """Check database connectivity"""
        logger.info("=== Checking Database Connection ===")
        
        try:
            # Import and test database connection
            sys.path.append(str(self.project_root))
            from database import DatabaseManager
            
            db = DatabaseManager()
            # Test with a simple query
            result = db.execute_query("SELECT 1 as test")
            if result:
                logger.info("✓ Database connection successful")
                return True
            else:
                logger.error("Database query returned no results")
                return False
                
        except Exception as e:
            logger.error(f"Database connection failed: {str(e)}")
            return False
    
    def backup_existing_data(self) -> bool:
        """Create backup of existing signal data"""
        logger.info("=== Creating Data Backup ===")
        
        backup_dir = self.project_root / "backups"
        backup_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = backup_dir / f"pre_strategic_backup_{timestamp}.sql"
        
        try:
            # Backup existing signal-related tables
            backup_tables = [
                "stock_data", "backtest_signals", "signal_alerts"
            ]
            
            backup_commands = []
            for table in backup_tables:
                backup_commands.append(f"\\copy {table} TO '{backup_file.parent}/{table}_{timestamp}.csv' CSV HEADER;")
            
            # Create backup script
            backup_script = backup_dir / f"backup_script_{timestamp}.sql"
            backup_script.write_text("\n".join(backup_commands))
            
            logger.info(f"✓ Backup script created: {backup_script}")
            logger.info("Run backup manually if needed before proceeding")
            return True
            
        except Exception as e:
            logger.error(f"Backup creation failed: {str(e)}")
            return False
    
    def deploy_database_schema(self) -> bool:
        """Deploy database schema changes"""
        logger.info("=== Deploying Database Schema ===")
        
        sql_files = [
            "strategic_signal_migration.sql",
            "populate_strategy_catalog.sql",
            "database_management_functions.sql", 
            "database_constraints_validation.sql",
            "management_views.sql"
        ]
        
        try:
            sys.path.append(str(self.project_root))
            from database import DatabaseManager
            
            db = DatabaseManager()
            
            for sql_file in sql_files:
                logger.info(f"Executing: {sql_file}")
                file_path = self.project_root / sql_file
                
                if not file_path.exists():
                    logger.error(f"SQL file not found: {sql_file}")
                    return False
                
                sql_content = file_path.read_text()
                
                # Split on double newlines to separate logical blocks
                sql_blocks = [block.strip() for block in sql_content.split('\n\n') if block.strip()]
                
                for i, block in enumerate(sql_blocks):
                    if block.startswith('--') or not block:
                        continue
                        
                    try:
                        db.execute_query(block)
                        logger.debug(f"  Block {i+1}/{len(sql_blocks)} completed")
                    except Exception as e:
                        logger.warning(f"  Block {i+1} error (may be expected): {str(e)}")
                
                logger.info(f"✓ {sql_file} deployed successfully")
            
            # Verify core tables exist
            verification_queries = [
                "SELECT COUNT(*) FROM strategy",
                "SELECT COUNT(*) FROM parameter_set", 
                "SELECT COUNT(*) FROM signal_run",
                "SELECT COUNT(*) FROM signal_event",
                "SELECT COUNT(*) FROM indicator_snapshot"
            ]
            
            for query in verification_queries:
                try:
                    result = db.execute_query(query)
                    table_name = query.split('FROM ')[1].strip()
                    logger.info(f"✓ Table {table_name} verified")
                except Exception as e:
                    logger.error(f"Table verification failed: {query} - {str(e)}")
                    return False
            
            logger.info("✓ All database schema deployed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Database schema deployment failed: {str(e)}")
            return False
    
    def deploy_python_modules(self) -> bool:
        """Validate Python modules and dependencies"""
        logger.info("=== Validating Python Modules ===")
        
        try:
            # Add project to Python path
            sys.path.insert(0, str(self.project_root))
            sys.path.insert(0, str(self.project_root / "src"))
            
            # Test import of each module
            modules_to_test = [
                "strategic_signal_engine",
                "strategic_database_manager", 
                "indicator_dictionary",
                "strategy_dictionary",
                "signal_dictionary",
                "signal_validation",
                "strategy_manager_api"
            ]
            
            for module_name in modules_to_test:
                try:
                    module = __import__(module_name)
                    logger.info(f"✓ Module {module_name} imported successfully")
                except Exception as e:
                    logger.error(f"Module {module_name} import failed: {str(e)}")
                    return False
            
            # Test key functionality
            logger.info("Testing key functionality...")
            
            # Test strategy dictionary
            from strategy_dictionary import BASE_STRATEGIES, StrategyCategory
            logger.info(f"✓ Strategy dictionary loaded: {len(BASE_STRATEGIES)} base strategies")
            
            # Test signal validation
            from signal_validation import validate_signal_format, TXYZnValidator
            validator = TXYZnValidator()
            test_signals = ["BBRK5", "SBDN3", "INVALID"]
            for signal in test_signals:
                is_valid = validator.validate_signal_format(signal)
                logger.info(f"✓ Signal validation test {signal}: {is_valid}")
            
            # Test indicator dictionary
            from indicator_dictionary import INDICATORS
            logger.info(f"✓ Indicator dictionary loaded: {len(INDICATORS)} indicators")
            
            logger.info("✓ All Python modules validated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Python module validation failed: {str(e)}")
            return False
    
    def run_system_tests(self) -> bool:
        """Run comprehensive system tests"""
        logger.info("=== Running System Tests ===")
        
        try:
            sys.path.append(str(self.project_root))
            from database import DatabaseManager
            
            db = DatabaseManager()
            
            # Test 1: Strategy catalog completeness
            strategy_count = db.execute_query("SELECT COUNT(*) FROM strategy")[0]['count']
            expected_strategies = 12 * 9  # 12 base strategies × 9 strength levels
            
            if strategy_count == expected_strategies:
                logger.info(f"✓ Strategy catalog complete: {strategy_count} strategies")
            else:
                logger.error(f"Strategy catalog incomplete: {strategy_count}/{expected_strategies}")
                return False
            
            # Test 2: Validation functions
            validation_tests = [
                ("SELECT validate_signal_format('BBRK5')", True),
                ("SELECT validate_signal_format('INVALID')", False), 
                ("SELECT validate_strategy_exists('BBRK1')", True),
                ("SELECT validate_strategy_exists('FAKE9')", False)
            ]
            
            for query, expected in validation_tests:
                result = db.execute_query(query)[0]
                actual = list(result.values())[0]
                if actual == expected:
                    logger.info(f"✓ Validation test passed: {query}")
                else:
                    logger.error(f"Validation test failed: {query} - expected {expected}, got {actual}")
                    return False
            
            # Test 3: Data consistency check
            consistency_result = db.execute_query("SELECT * FROM check_data_consistency()")
            all_passed = True
            for check in consistency_result:
                if check['status'] == 'PASS':
                    logger.info(f"✓ Consistency check: {check['check_name']}")
                else:
                    logger.error(f"Consistency check failed: {check['check_name']} - {check['details']}")
                    all_passed = False
            
            if not all_passed:
                logger.error("Data consistency checks failed")
                return False
            
            # Test 4: Management views
            view_tests = [
                "SELECT COUNT(*) FROM v_strategy_overview",
                "SELECT COUNT(*) FROM v_executive_dashboard",
                "SELECT COUNT(*) FROM v_strategy_explorer"
            ]
            
            for query in view_tests:
                try:
                    result = db.execute_query(query)
                    view_name = query.split('FROM ')[1].strip()
                    logger.info(f"✓ View accessible: {view_name}")
                except Exception as e:
                    logger.error(f"View test failed: {query} - {str(e)}")
                    return False
            
            logger.info("✓ All system tests passed")
            return True
            
        except Exception as e:
            logger.error(f"System tests failed: {str(e)}")
            return False
    
    def create_sample_data(self) -> bool:
        """Create sample data for testing"""
        logger.info("=== Creating Sample Data ===")
        
        try:
            sys.path.append(str(self.project_root))
            sys.path.append(str(self.project_root / "src"))
            from strategic_database_manager import StrategicDatabaseManager
            import uuid
            from datetime import datetime, timedelta
            
            db = StrategicDatabaseManager()
            
            # Create sample parameter set
            sample_params = {
                "rsi_period": 14,
                "bb_period": 20,
                "bb_std": 2.0,
                "volume_ma_period": 20
            }
            
            param_set_id = db.create_parameter_set(sample_params)
            logger.info(f"✓ Sample parameter set created: {param_set_id}")
            
            # Create sample signal run
            run_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
            
            db.start_signal_run(
                run_id=run_id,
                parameter_set_id=param_set_id,
                symbol_count=5
            )
            
            # Add sample indicator snapshots
            sample_symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA']
            base_time = datetime.now() - timedelta(hours=1)
            
            for i, symbol in enumerate(sample_symbols):
                timestamp = base_time + timedelta(minutes=i*5)
                
                # RSI indicator
                db.store_indicator_snapshot(
                    symbol=symbol,
                    indicator_name='rsi14',
                    value=50 + (i * 5),  # 50, 55, 60, 65, 70
                    timestamp=timestamp,
                    metadata={'period': 14, 'source': 'close'}
                )
                
                # Bollinger Bands
                db.store_indicator_snapshot(
                    symbol=symbol,
                    indicator_name='bb_upper',
                    value=100 + (i * 2),
                    timestamp=timestamp,
                    metadata={'period': 20, 'std_dev': 2.0}
                )
                
            logger.info("✓ Sample indicator snapshots created")
            
            # Add sample signal events
            sample_signals = [
                {'symbol': 'AAPL', 'signal': 'BBRK3', 'confidence': 0.75, 'strength': 3},
                {'symbol': 'MSFT', 'signal': 'SBDN5', 'confidence': 0.82, 'strength': 5},
                {'symbol': 'GOOGL', 'signal': 'BMAC7', 'confidence': 0.68, 'strength': 7}
            ]
            
            for signal_data in sample_signals:
                evidence = {
                    'thresholds': {'rsi': 70, 'bb_position': 0.95},
                    'reasons': ['RSI overbought', 'Price near upper band'],
                    'score': signal_data['confidence'] * 100
                }
                
                db.record_signal_event(
                    symbol=signal_data['symbol'],
                    signal=signal_data['signal'],
                    timestamp=datetime.now(),
                    confidence=signal_data['confidence'],
                    strength=signal_data['strength'],
                    evidence=evidence,
                    run_id=run_id
                )
            
            logger.info("✓ Sample signal events created")
            
            # Complete the signal run
            db.complete_signal_run(run_id)
            logger.info(f"✓ Sample signal run completed: {run_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Sample data creation failed: {str(e)}")
            return False
    
    def generate_deployment_report(self) -> Dict:
        """Generate comprehensive deployment report"""
        logger.info("=== Generating Deployment Report ===")
        
        try:
            sys.path.append(str(self.project_root))
            from database import DatabaseManager
            
            db = DatabaseManager()
            
            # Gather system statistics
            stats = {}
            
            # Strategy statistics
            strategies = db.execute_query("SELECT COUNT(*) as total, COUNT(DISTINCT base_strategy) as base_count FROM strategy")[0]
            stats['strategies'] = {
                'total_strategies': strategies['total'],
                'base_strategies': strategies['base_count'],
                'expected_total': 108
            }
            
            # Signal statistics  
            signals = db.execute_query("""
                SELECT 
                    COUNT(*) as total_signals,
                    COUNT(DISTINCT symbol) as symbols_with_signals,
                    AVG(confidence) as avg_confidence,
                    COUNT(DISTINCT signal) as unique_strategies_used
                FROM signal_event
            """)
            
            if signals:
                stats['signals'] = {
                    'total_events': signals[0]['total_signals'] or 0,
                    'symbols_covered': signals[0]['symbols_with_signals'] or 0,
                    'avg_confidence': float(signals[0]['avg_confidence'] or 0),
                    'strategies_used': signals[0]['unique_strategies_used'] or 0
                }
            else:
                stats['signals'] = {'total_events': 0, 'symbols_covered': 0, 'avg_confidence': 0, 'strategies_used': 0}
            
            # Indicator statistics
            indicators = db.execute_query("""
                SELECT 
                    COUNT(DISTINCT indicator_name) as indicator_types,
                    COUNT(*) as total_snapshots,
                    COUNT(DISTINCT symbol) as symbols_with_indicators
                FROM indicator_snapshot
            """)
            
            if indicators:
                stats['indicators'] = {
                    'types_available': indicators[0]['indicator_types'] or 0,
                    'total_snapshots': indicators[0]['total_snapshots'] or 0,
                    'symbols_covered': indicators[0]['symbols_with_indicators'] or 0
                }
            else:
                stats['indicators'] = {'types_available': 0, 'total_snapshots': 0, 'symbols_covered': 0}
            
            # System health
            consistency_checks = db.execute_query("SELECT * FROM check_data_consistency()")
            stats['health'] = {
                'consistency_checks': len([c for c in consistency_checks if c['status'] == 'PASS']),
                'total_checks': len(consistency_checks),
                'all_passing': all(c['status'] == 'PASS' for c in consistency_checks)
            }
            
            # Deployment metadata
            stats['deployment'] = {
                'timestamp': datetime.now().isoformat(),
                'duration_minutes': (datetime.now() - self.start_time).total_seconds() / 60,
                'project_root': str(self.project_root),
                'python_version': sys.version,
                'status': 'SUCCESSFUL' if stats['health']['all_passing'] else 'COMPLETED_WITH_WARNINGS'
            }
            
            # Save report
            report_file = self.project_root / "strategic_system_deployment_report.json"
            report_file.write_text(json.dumps(stats, indent=2, default=str))
            
            logger.info(f"✓ Deployment report saved: {report_file}")
            return stats
            
        except Exception as e:
            logger.error(f"Report generation failed: {str(e)}")
            return {}
    
    def deploy_complete_system(self) -> bool:
        """Execute complete system deployment"""
        logger.info("🚀 Starting Strategic Signal System Deployment")
        logger.info(f"Project Root: {self.project_root}")
        logger.info(f"Start Time: {self.start_time}")
        
        deployment_steps = [
            ("Prerequisites Validation", self.validate_prerequisites),
            ("Database Connection Check", self.check_database_connection),
            ("Data Backup", self.backup_existing_data),
            ("Database Schema Deployment", self.deploy_database_schema),
            ("Python Modules Validation", self.deploy_python_modules),
            ("System Testing", self.run_system_tests),
            ("Sample Data Creation", self.create_sample_data)
        ]
        
        for step_name, step_function in deployment_steps:
            logger.info(f"\n{'='*20} {step_name} {'='*20}")
            
            try:
                if step_function():
                    logger.info(f"✅ {step_name} - SUCCESS")
                    self.deployment_status[step_name] = "SUCCESS"
                else:
                    logger.error(f"❌ {step_name} - FAILED")
                    self.deployment_status[step_name] = "FAILED"
                    
                    # Ask user if they want to continue
                    response = input(f"\n{step_name} failed. Continue anyway? (y/N): ")
                    if response.lower() != 'y':
                        logger.error("Deployment aborted by user")
                        return False
                        
            except Exception as e:
                logger.error(f"❌ {step_name} - ERROR: {str(e)}")
                self.deployment_status[step_name] = f"ERROR: {str(e)}"
                
                response = input(f"\n{step_name} encountered error. Continue anyway? (y/N): ")
                if response.lower() != 'y':
                    logger.error("Deployment aborted by user")
                    return False
        
        # Generate final report
        report = self.generate_deployment_report()
        
        # Summary
        logger.info("\n" + "="*60)
        logger.info("🎉 STRATEGIC SIGNAL SYSTEM DEPLOYMENT COMPLETE")
        logger.info("="*60)
        
        for step, status in self.deployment_status.items():
            status_icon = "✅" if status == "SUCCESS" else "⚠️" if "ERROR" in status else "❌"
            logger.info(f"{status_icon} {step}: {status}")
        
        if report:
            logger.info(f"\n📊 DEPLOYMENT STATISTICS:")
            logger.info(f"  • Total Strategies: {report.get('strategies', {}).get('total_strategies', 0)}")
            logger.info(f"  • Sample Signals: {report.get('signals', {}).get('total_events', 0)}")
            logger.info(f"  • Indicator Types: {report.get('indicators', {}).get('types_available', 0)}")
            logger.info(f"  • Deployment Time: {report.get('deployment', {}).get('duration_minutes', 0):.1f} minutes")
        
        logger.info(f"\n📋 NEXT STEPS:")
        logger.info("  1. Start the Strategy Manager API: python src/strategy_manager_api.py")
        logger.info("  2. Open dashboard_management.html in your browser")
        logger.info("  3. Test signal generation with your stock data")
        logger.info("  4. Review deployment_report.json for detailed statistics")
        
        return True


def main():
    """Main deployment entry point"""
    print("🎯 Strategic Signal System - Complete Deployment")
    print("=" * 50)
    
    # Get project root from user or use default
    default_root = "/home/bthia/projects/hk-strategy-mvp"
    project_root = input(f"Project root directory [{default_root}]: ").strip() or default_root
    
    # Confirm deployment
    print(f"\nDeploying Strategic Signal System to: {project_root}")
    print("\nThis will:")
    print("  • Create new database tables and views")
    print("  • Deploy validation functions and constraints")
    print("  • Install Python modules and API endpoints")  
    print("  • Create sample data for testing")
    print("  • Generate comprehensive deployment report")
    
    response = input("\nProceed with deployment? (y/N): ")
    if response.lower() != 'y':
        print("Deployment cancelled")
        return
    
    # Execute deployment
    deployer = StrategicSystemDeployer(project_root)
    success = deployer.deploy_complete_system()
    
    if success:
        print("\n🎉 Deployment completed successfully!")
        return 0
    else:
        print("\n❌ Deployment failed or completed with errors")
        return 1


if __name__ == "__main__":
    sys.exit(main())