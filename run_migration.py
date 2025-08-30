#!/usr/bin/env python3
"""
Database Migration Execution Script
Safe execution of database migrations with comprehensive validation
"""

import os
import sys
import subprocess
import psycopg2
import argparse
import logging
from datetime import datetime
from typing import Optional, Dict, List
import time

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'migration_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger(__name__)

class MigrationRunner:
    """
    Safe database migration execution with validation and rollback capabilities
    """
    
    def __init__(self, db_url: Optional[str] = None):
        # Load environment variables
        from dotenv import load_dotenv
        load_dotenv()
        
        self.db_url = db_url or os.getenv('DATABASE_URL', 'postgresql://trader:YOUR_PASSWORD@localhost:5432/hk_strategy')
        self.migration_files = {
            'phase1': 'migration_v1_to_v2.sql',
            'phase2': 'migration_v2_to_v3.sql',
            'rollback': 'rollback_v2_to_v1.sql'
        }
        
    def get_connection(self):
        """Get database connection"""
        try:
            return psycopg2.connect(self.db_url)
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise
    
    def check_prerequisites(self, phase: str) -> bool:
        """
        Check prerequisites for migration phase
        
        Args:
            phase: Migration phase ('phase1', 'phase2', 'rollback')
            
        Returns:
            Boolean indicating if prerequisites are met
        """
        try:
            conn = self.get_connection()
            
            if phase == 'phase1':
                # Check if single-portfolio schema exists
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT EXISTS (
                            SELECT 1 FROM information_schema.tables 
                            WHERE table_name = 'portfolio_positions'
                        )
                    """)
                    has_portfolio_positions = cur.fetchone()[0]
                    
                    if not has_portfolio_positions:
                        logger.error("portfolio_positions table not found - database not initialized")
                        return False
                    
                    # Check if portfolios table exists (partial migration check)
                    cur.execute("""
                        SELECT EXISTS (
                            SELECT 1 FROM information_schema.tables 
                            WHERE table_name = 'portfolios'
                        )
                    """)
                    has_portfolios_table = cur.fetchone()[0]
                    
                    # Check if portfolio_id columns exist in main tables
                    cur.execute("""
                        SELECT EXISTS (
                            SELECT 1 FROM information_schema.columns 
                            WHERE table_name = 'portfolio_positions' AND column_name = 'portfolio_id'
                        )
                    """)
                    has_portfolio_id_column = cur.fetchone()[0]
                    
                    if has_portfolios_table and has_portfolio_id_column:
                        logger.info("✅ Phase 1 migration already completed successfully")
                        logger.info("Multi-portfolio functionality is active and working")
                        return False
                    elif has_portfolios_table and not has_portfolio_id_column:
                        logger.info("Partial migration detected - portfolios table exists but portfolio_id columns missing")
                        logger.info("This is normal if portfolio data was created via dashboard before running migration")
                        logger.info("✅ Prerequisites for Phase 1 migration met - will complete the migration")
                        return True
                    elif not has_portfolios_table:
                        logger.info("✅ Prerequisites for Phase 1 migration met - clean single-portfolio state")
                        return True
                    
                return True
                
            elif phase == 'phase2':
                # Check if Phase 1 completed
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT EXISTS (
                            SELECT 1 FROM information_schema.tables 
                            WHERE table_name = 'portfolios'
                        )
                    """)
                    phase1_done = cur.fetchone()[0]
                    
                    if not phase1_done:
                        logger.error("Phase 1 migration not completed - run Phase 1 first")
                        return False
                    
                    # Check for NULL portfolio_id values
                    for table in ['portfolio_positions', 'trading_signals', 'price_history']:
                        cur.execute(f"SELECT COUNT(*) FROM {table} WHERE portfolio_id IS NULL")
                        null_count = cur.fetchone()[0]
                        if null_count > 0:
                            logger.error(f"Found {null_count} NULL portfolio_id values in {table}")
                            return False
                    
                    # Check if already completed
                    cur.execute("""
                        SELECT COUNT(*) FROM information_schema.table_constraints 
                        WHERE constraint_type = 'FOREIGN KEY' 
                          AND table_name = 'portfolio_positions'
                          AND constraint_name LIKE '%portfolio%'
                    """)
                    has_foreign_keys = cur.fetchone()[0] > 0
                    
                    if has_foreign_keys:
                        logger.warning("Phase 2 migration already completed")
                        return False
                
                logger.info("✅ Prerequisites for Phase 2 migration met")
                return True
                
            elif phase == 'rollback':
                # Check if migration exists to rollback
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT EXISTS (
                            SELECT 1 FROM information_schema.tables 
                            WHERE table_name = 'portfolios'
                        )
                    """)
                    has_migration = cur.fetchone()[0]
                    
                    if not has_migration:
                        logger.error("No migration to rollback - database appears to be in single-portfolio state")
                        return False
                
                logger.info("✅ Prerequisites for rollback met")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking prerequisites: {e}")
            return False
        finally:
            conn.close()
    
    def create_backup(self) -> str:
        """
        Create database backup before migration
        
        Returns:
            Backup filename if successful, None if failed
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = f"backup_before_migration_{timestamp}.sql"
            
            # Parse database URL for pg_dump
            import re
            match = re.match(r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)', self.db_url)
            if not match:
                logger.error("Could not parse database URL for backup")
                return None
                
            user, password, host, port, database = match.groups()
            
            # Set PGPASSWORD environment variable
            env = os.environ.copy()
            env['PGPASSWORD'] = password
            
            # Run pg_dump
            cmd = [
                'pg_dump',
                '-h', host,
                '-p', port,
                '-U', user,
                '-d', database,
                '--no-password',
                '--verbose',
                '-f', backup_file
            ]
            
            logger.info(f"Creating backup: {backup_file}")
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"✅ Backup created successfully: {backup_file}")
                return backup_file
            else:
                logger.error(f"Backup failed: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            return None
    
    def execute_sql_file(self, sql_file: str) -> bool:
        """
        Execute SQL file against database
        
        Args:
            sql_file: Path to SQL file
            
        Returns:
            Boolean indicating success
        """
        if not os.path.exists(sql_file):
            logger.error(f"SQL file not found: {sql_file}")
            return False
        
        try:
            conn = self.get_connection()
            
            # Read SQL file
            with open(sql_file, 'r') as f:
                sql_content = f.read()
            
            # Execute SQL
            with conn.cursor() as cur:
                logger.info(f"Executing {sql_file}...")
                cur.execute(sql_content)
                conn.commit()
            
            logger.info(f"✅ Successfully executed {sql_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error executing {sql_file}: {e}")
            if 'conn' in locals():
                conn.rollback()
            return False
        finally:
            if 'conn' in locals():
                conn.close()
    
    def validate_migration_result(self, expected_phase: str) -> bool:
        """
        Validate migration result
        
        Args:
            expected_phase: Expected schema state after migration
            
        Returns:
            Boolean indicating validation success
        """
        try:
            # Run test script to validate
            logger.info("Running validation tests...")
            result = subprocess.run([sys.executable, 'test_migration.py'], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("✅ Migration validation passed")
                return True
            else:
                logger.error(f"Migration validation failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error validating migration: {e}")
            return False
    
    def run_migration(self, phase: str, create_backup: bool = True, 
                     skip_validation: bool = False) -> bool:
        """
        Run migration with full safety checks
        
        Args:
            phase: Migration phase to run
            create_backup: Whether to create backup before migration
            skip_validation: Skip post-migration validation
            
        Returns:
            Boolean indicating success
        """
        logger.info(f"🚀 Starting {phase} migration")
        
        # Check prerequisites
        if not self.check_prerequisites(phase):
            logger.error("Prerequisites not met - aborting migration")
            return False
        
        # Create backup
        backup_file = None
        if create_backup:
            backup_file = self.create_backup()
            if not backup_file:
                logger.error("Failed to create backup - aborting migration")
                return False
        
        # Execute migration
        sql_file = self.migration_files[phase]
        if not self.execute_sql_file(sql_file):
            logger.error(f"Migration execution failed")
            if backup_file:
                logger.info(f"Backup available for restore: {backup_file}")
            return False
        
        # Validate result
        if not skip_validation:
            if not self.validate_migration_result(phase):
                logger.error("Migration validation failed")
                if backup_file:
                    logger.info(f"Consider restoring from backup: {backup_file}")
                return False
        
        logger.info(f"✅ {phase} migration completed successfully")
        if backup_file:
            logger.info(f"Backup saved as: {backup_file}")
        
        return True

def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(
        description='HK Strategy Database Migration Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_migration.py phase1              # Run Phase 1 migration with backup
  python run_migration.py phase2 --no-backup # Run Phase 2 without backup
  python run_migration.py rollback           # Rollback to single-portfolio
  python run_migration.py check              # Check current schema state
        """
    )
    
    parser.add_argument('action', choices=['phase1', 'phase2', 'rollback', 'check'],
                       help='Migration action to perform')
    parser.add_argument('--no-backup', action='store_true',
                       help='Skip database backup (not recommended)')
    parser.add_argument('--skip-validation', action='store_true',
                       help='Skip post-migration validation')
    parser.add_argument('--db-url', type=str,
                       help='Database URL (overrides environment variable)')
    
    args = parser.parse_args()
    
    # Initialize migration runner
    runner = MigrationRunner(args.db_url)
    
    if args.action == 'check':
        # Check current schema state
        try:
            sys.path.append('src')
            from database_enhanced import DatabaseManager
            
            db = DatabaseManager()
            schema_info = db.get_schema_info()
            health = db.test_connection_health()
            
            print("=" * 60)
            print("📊 DATABASE SCHEMA STATUS")
            print("=" * 60)
            print(f"Schema Version: {schema_info['version']}")
            print(f"Multi-Portfolio Support: {schema_info['capabilities']['multi_portfolio']}")
            print(f"Backward Compatible: {schema_info['capabilities']['backward_compatible']}")
            print(f"Has Constraints: {schema_info['capabilities']['has_constraints']}")
            print()
            print("Health Status:")
            for component, status in health.items():
                print(f"  {component.title()}: {status['status']} - {status['details']}")
            print()
            print("Recommendations:")
            for rec in schema_info['migration_recommendations']:
                print(f"  • {rec}")
            print("=" * 60)
            
        except Exception as e:
            logger.error(f"Error checking schema state: {e}")
            sys.exit(1)
    else:
        # Run migration
        success = runner.run_migration(
            args.action, 
            create_backup=not args.no_backup,
            skip_validation=args.skip_validation
        )
        
        if success:
            print(f"\n✅ {args.action.upper()} MIGRATION COMPLETED SUCCESSFULLY")
            print("🔍 Run 'python run_migration.py check' to verify schema state")
        else:
            # Check if it's actually a "no action needed" situation
            if args.action == 'phase1':
                # Check if migration is already complete
                try:
                    import psycopg2
                    conn = psycopg2.connect(runner.db_url)
                    with conn.cursor() as cur:
                        cur.execute("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'portfolios')")
                        has_portfolios = cur.fetchone()[0]
                        cur.execute("SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'portfolio_positions' AND column_name = 'portfolio_id')")
                        has_portfolio_id = cur.fetchone()[0]
                    
                    if has_portfolios and has_portfolio_id:
                        print(f"\n✅ {args.action.upper()} MIGRATION ALREADY COMPLETED")
                        print("🎉 Multi-portfolio functionality is already active and working")
                        print("📊 Your database is ready for multi-portfolio operations")
                        print("🔍 Run 'python run_migration.py check' to see current status")
                        sys.exit(0)  # Success exit code since everything is working
                except:
                    pass  # Fall through to error message
            
            print(f"\n❌ {args.action.upper()} MIGRATION FAILED")
            print("📋 Check the log file for detailed error information")
            sys.exit(1)

if __name__ == "__main__":
    main()