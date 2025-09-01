#!/usr/bin/env python3
"""
Debug position calculation issues
"""

import sys
import os
sys.path.append('src')
from src.database import DatabaseManager
from src.hkex_calendar import get_hkex_trading_days
from datetime import date

def debug_position_calculation():
    """Debug why positions are not being calculated"""
    
    print('🔍 DEBUGGING POSITION CALCULATION')
    print('='*60)
    
    # Simulate the exact logic from _calculate_daily_values_trading_days
    analysis_id = 28
    start_date = date(2025, 1, 2)
    end_date = date(2025, 8, 31)
    
    # Get trading days
    trading_days = get_hkex_trading_days(start_date, end_date)
    print(f'Trading days: {len(trading_days)} (from {trading_days[0]} to {trading_days[-1]})')
    
    # Get transactions (simulate the database query)
    db_manager = DatabaseManager()
    conn = db_manager.get_connection()
    cur = conn.cursor()
    
    trans_query = """
        SELECT id, analysis_id, transaction_date, symbol, transaction_type,
               quantity_change, cash_change
        FROM portfolio_analysis_state_changes 
        WHERE analysis_id = %s
        ORDER BY transaction_date, id
    """
    
    cur.execute(trans_query, (analysis_id,))
    transactions = cur.fetchall()
    
    print(f'\\nTransactions: {len(transactions)}')
    for i, trans in enumerate(transactions):
        print(f'  {i}: Date={trans[2]}, Symbol={trans[3]}, Type={trans[4]}, Qty={trans[5]}, Cash=${float(trans[6]):,.2f}')
    
    # Simulate the fixed logic
    print(f'\\n🧮 SIMULATING POSITION CALCULATION:')
    
    positions = {}
    current_cash = 888888.00  # start_cash
    processed_transactions = set()
    
    for day_idx, trading_day in enumerate(trading_days[:10]):  # Test first 10 days
        print(f'\\n--- Trading Day {day_idx+1}: {trading_day} ---')
        
        day_transactions = []
        
        # Apply transactions for this day
        for i, transaction in enumerate(transactions):
            trans_id = f"{analysis_id}_{i}"
            
            # Skip if already processed
            if trans_id in processed_transactions:
                continue
                
            trans_date = transaction[2]  # transaction_date
            symbol = transaction[3]
            trans_type = transaction[4]
            qty_change = transaction[5] or 0
            cash_change = transaction[6] or 0
            
            print(f'  Checking transaction {i}: {trans_date} vs {trading_day}')
            
            # FIXED: Only process transactions that occur exactly on this trading day
            if trans_date and trans_date == trading_day:
                print(f'    ✅ Processing: {symbol} {trans_type} qty={qty_change} cash=${float(cash_change):,.2f}')
                
                if symbol and trans_type:
                    # Update positions
                    if symbol not in positions:
                        positions[symbol] = 0
                    positions[symbol] += qty_change
                    
                    # Update cash
                    current_cash = float(current_cash) + float(cash_change or 0)
                    
                    # Mark transaction as processed
                    processed_transactions.add(trans_id)
                    day_transactions.append((symbol, trans_type, qty_change, cash_change))
        
        print(f'  Day transactions: {len(day_transactions)}')
        print(f'  Current cash: ${current_cash:,.2f}')
        print(f'  Current positions: {positions}')
        print(f'  Processed transactions: {len(processed_transactions)}/{len(transactions)}')
        
        if day_idx >= 2 and not day_transactions:  # Stop if no more transactions
            break
    
    print(f'\\n📊 FINAL SIMULATION RESULTS:')
    print(f'  Final Cash: ${current_cash:,.2f}')
    print(f'  Final Positions: {positions}')
    print(f'  Total Processed Transactions: {len(processed_transactions)}/{len(transactions)}')
    
    # Calculate expected equity value using current prices
    total_equity = 0
    print(f'\\n💎 EQUITY CALCULATION (using recent prices):')
    symbol_prices = {
        '0700.HK': 596.5,   # From previous validation
        '1810.HK': 12.30,
        '3690.HK': 95.00,
        '9618.HK': 125.00,
        '9988.HK': 115.00
    }
    
    for symbol, quantity in positions.items():
        if quantity > 0:
            price = symbol_prices.get(symbol, 0)
            equity_value = quantity * price
            total_equity += equity_value
            print(f'  {symbol}: {quantity} shares × ${price:.2f} = ${equity_value:,.2f}')
    
    expected_total = current_cash + total_equity
    print(f'\\nExpected Portfolio Value: ${current_cash:,.2f} (cash) + ${total_equity:,.2f} (equity) = ${expected_total:,.2f}')
    
    conn.close()

if __name__ == "__main__":
    debug_position_calculation()