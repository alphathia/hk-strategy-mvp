#!/usr/bin/env python3
"""
Investigate Portfolio Analysis Issues
"""

import sys
import os
sys.path.append('src')
from src.database import DatabaseManager

def investigate_portfolio_issues():
    """Investigate the portfolio analysis issues"""
    
    db = DatabaseManager()
    conn = db.get_connection()
    cur = conn.cursor()

    print('🔍 INVESTIGATING PORTFOLIO ANALYSIS ISSUES')
    print('='*60)

    # Check the portfolios table structure
    print('\n📊 PORTFOLIO TABLE STRUCTURE:')
    cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'portfolios' ORDER BY ordinal_position")
    columns = cur.fetchall()
    for col_name, col_type in columns:
        print(f'  {col_name}: {col_type}')

    print('\n📋 MY HKEX FULL PORTFOLIO DETAILS:')
    cur.execute("SELECT * FROM portfolios WHERE name = 'My HKEX Full Portfolio'")
    portfolio = cur.fetchone()
    if portfolio:
        print(f'  ID: {portfolio[0]}')
        print(f'  Name: {portfolio[1]}') 
        print(f'  Description: {portfolio[2]}')
        print(f'  Created: {portfolio[3]}')
        portfolio_id = portfolio[0]
    else:
        print('  ❌ Portfolio not found!')
        return
        
    print('\n📈 PORTFOLIO HOLDINGS:')
    cur.execute("""
        SELECT h.symbol, h.company_name, h.quantity, h.avg_cost, h.sector
        FROM portfolio_holdings h
        JOIN portfolios p ON h.portfolio_id = p.portfolio_id  
        WHERE p.name = 'My HKEX Full Portfolio'
        ORDER BY h.symbol
    """)
    holdings = cur.fetchall()
    print(f'  Total holdings in portfolio: {len(holdings)}')
    portfolio_symbols = []
    for symbol, company_name, qty, avg_cost, sector in holdings:
        portfolio_symbols.append(symbol)
        print(f'    {symbol}: {company_name} - {qty} shares @ ${float(avg_cost):.2f} ({sector})')

    print(f'\n🔍 CHECKING RECENT PORTFOLIO ANALYSES FOR "My HKEX Full Portfolio":')
    cur.execute("""
        SELECT id, analysis_name, start_date, end_date, created_at
        FROM portfolio_analyses 
        WHERE portfolio_id = %s
        ORDER BY created_at DESC
        LIMIT 5
    """, (portfolio_id,))
    
    analyses = cur.fetchall()
    print(f'Found {len(analyses)} analyses:')
    
    for analysis_id, analysis_name, start_date, end_date, created_at in analyses:
        print(f'\n  Analysis: {analysis_name} (ID: {analysis_id})')
        print(f'    Date Range: {start_date} to {end_date}')
        print(f'    Created: {created_at}')
        
        # Check which symbols are in portfolio_positions for this analysis
        cur.execute("""
            SELECT symbol, quantity, avg_cost, current_price, market_value
            FROM portfolio_positions
            WHERE portfolio_id = %s
            ORDER BY symbol
        """, (analysis_id,))
        
        copied_positions = cur.fetchall()
        symbols_copied = len(copied_positions)
        
        print(f'    Symbols in positions: {symbols_copied}/{len(portfolio_symbols)}')
        
        if symbols_copied < len(portfolio_symbols):
            print(f'    ⚠️  ISSUE: Missing {len(portfolio_symbols) - symbols_copied} symbols!')
            
            copied_symbols = [p[0] for p in copied_positions]
            missing_symbols = [s for s in portfolio_symbols if s not in copied_symbols]
            
            print(f'    Copied symbols: {copied_symbols}')
            print(f'    Missing symbols: {missing_symbols}')
            
            # Show the copied positions
            for symbol, qty, avg_cost, current_price, market_val in copied_positions:
                print(f'      {symbol}: {qty} @ ${float(avg_cost):.2f} = ${float(market_val):,.2f}')

    # Check portfolio_analysis_summary for performance issues
    print('\n💰 CHECKING PORTFOLIO ANALYSIS SUMMARY:')
    if analyses:
        latest_analysis_id = analyses[0][0]
        latest_analysis_name = analyses[0][1]
        
        print(f'Checking analysis summary: {latest_analysis_name} (ID: {latest_analysis_id})')
        
        cur.execute("""
            SELECT total_cost, total_current_value, total_pnl, cash_position,
                   start_equity, end_equity
            FROM portfolio_analysis_summary 
            WHERE analysis_id = %s
        """, (latest_analysis_id,))
        
        summary = cur.fetchone()
        if summary:
            total_cost, total_current_value, total_pnl, cash_position, start_equity, end_equity = summary
            print(f'  Summary data:')
            print(f'    Total Cost: ${float(total_cost):,.2f}')
            print(f'    Current Value: ${float(total_current_value):,.2f}')
            print(f'    Total P&L: ${float(total_pnl):,.2f}')
            print(f'    Cash Position: ${float(cash_position):,.2f}')
            print(f'    Start Equity: ${float(start_equity):,.2f}')
            print(f'    End Equity: ${float(end_equity):,.2f}')
            
            if float(end_equity) < 0:
                print(f'    ⚠️  WARNING: Negative end equity!')
        else:
            print(f'  ❌ No summary found for analysis {latest_analysis_id}')

    conn.close()

if __name__ == "__main__":
    investigate_portfolio_issues()