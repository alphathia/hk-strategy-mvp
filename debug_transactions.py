#!/usr/bin/env python3
"""
Debug transaction processing issues
"""

import sys
import os
sys.path.append('src')
from src.database import DatabaseManager
from psycopg2.extras import RealDictCursor

def debug_transactions():
    """Debug transaction data for analysis 28"""
    
    print('🔍 DEBUGGING TRANSACTION DATA FOR ANALYSIS 28')
    print('='*60)
    
    db_manager = DatabaseManager()
    conn = db_manager.get_connection()
    
    # Check what transaction data exists
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        print('\n📊 CHECKING STATE CHANGES TABLE:')
        
        # Get transaction data exactly as the portfolio manager does
        trans_query = """
            SELECT 
                id, analysis_id, transaction_date, symbol, transaction_type,
                quantity_change, cash_change, created_at
            FROM portfolio_analysis_state_changes 
            WHERE analysis_id = %s
            ORDER BY transaction_date, id
        """
        
        cur.execute(trans_query, (28,))
        transactions = cur.fetchall()
        
        print(f'Found {len(transactions)} transactions:')
        
        total_cash_change = 0
        for i, trans in enumerate(transactions):
            print(f'\n  Transaction {i+1}:')
            print(f'    ID: {trans["id"]}')
            print(f'    Date: {trans["transaction_date"]}')
            print(f'    Symbol: {trans["symbol"]}')
            print(f'    Type: {trans["transaction_type"]}')
            print(f'    Qty Change: {trans["quantity_change"]}')
            print(f'    Cash Change: ${float(trans["cash_change"] or 0):,.2f}')
            
            total_cash_change += float(trans["cash_change"] or 0)
        
        print(f'\n💰 CASH ANALYSIS:')
        print(f'  Total Cash Change from Transactions: ${total_cash_change:,.2f}')
        
        # Get the start cash from the analysis
        cur.execute("SELECT start_cash FROM portfolio_analyses WHERE id = %s", (28,))
        analysis = cur.fetchone()
        if analysis:
            start_cash = float(analysis['start_cash'])
            print(f'  Analysis Start Cash: ${start_cash:,.2f}')
            expected_final_cash = start_cash + total_cash_change
            print(f'  Expected Final Cash: ${expected_final_cash:,.2f}')
            print(f'  Actual Result was: $-408,187.00')
            print(f'  Difference: ${expected_final_cash - (-408187):,.2f}')
        
        # Check if there's a mismatch in how we calculate start_cash
        print(f'\n🔍 CHECKING HOW START_CASH IS CALCULATED:')
        
        # This mimics the portfolio manager logic
        first_transaction = transactions[0] if transactions else None
        if first_transaction:
            # Check if start_cash comes from first transaction
            print(f'  First transaction cash_change: ${float(first_transaction["cash_change"] or 0):,.2f}')
            
            # In the old logic, they might be using different fields
            cur.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'portfolio_analysis_state_changes' 
                ORDER BY ordinal_position
            """)
            columns = cur.fetchall()
            print(f'  Available columns in state_changes:')
            for col in columns:
                print(f'    {col["column_name"]}: {col["data_type"]}')
    
    conn.close()

if __name__ == "__main__":
    debug_transactions()