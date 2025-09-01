#!/usr/bin/env python3
"""
Test the exact same flow as the dashboard symbol validation
"""

import yfinance as yf

def test_dashboard_symbol_flow():
    """Simulate the exact dashboard flow"""
    
    print('🧪 TESTING DASHBOARD SYMBOL VALIDATION FLOW')
    print('='*60)
    
    # Test symbols that user might try
    test_symbols = ['0700.HK', '0700.hk', '0700', 'TENCENT']
    
    for symbol_input in test_symbols:
        print(f'\n📊 TESTING USER INPUT: "{symbol_input}"')
        
        # Simulate dashboard logic exactly
        if symbol_input.strip():
            trimmed_symbol = symbol_input.strip().upper()
            print(f'  Trimmed symbol: "{trimmed_symbol}"')
            
            # Try to get company info from Yahoo Finance
            try:
                stock = yf.Ticker(trimmed_symbol)
                print(f'  ✅ Ticker created')
                
                info = stock.info
                print(f'  Info retrieved, keys: {len(info) if info else 0}')
                
                if info and len(info) > 1:
                    company_name = info.get('longName', info.get('shortName', 'Unknown Company'))
                    
                    # Check the individual gets
                    long_name = info.get('longName')
                    short_name = info.get('shortName')
                    print(f'  longName: "{long_name}"')
                    print(f'  shortName: "{short_name}"')
                    print(f'  🎯 Final company_name: "{company_name}"')
                    
                    # Try to determine sector
                    sector = info.get('sector', 'Other')
                    if sector in ["Technology", "Information Technology"]:
                        sector = "Tech"
                    elif sector in ["Financials", "Financial Services"]:
                        sector = "Financials"
                    elif sector in ["Real Estate"]:
                        sector = "REIT"
                    elif sector in ["Energy"]:
                        sector = "Energy"
                    else:
                        sector = "Other"
                    
                    print(f'  Raw sector: "{info.get("sector", "Other")}"')
                    print(f'  Mapped sector: "{sector}"')
                    
                    print(f'  ✅ SUCCESS: Would display "Found: {company_name}"')
                else:
                    print(f'  ❌ FAIL: Info data insufficient (len={len(info) if info else 0})')
                    print(f'  Would display "Symbol not found on Yahoo Finance"')
                    
            except Exception as e:
                print(f'  ❌ EXCEPTION: {str(e)}')
                print(f'  Would display "Error validating symbol: {str(e)}"')
        else:
            print(f'  ❌ Empty input - would display "Please enter a symbol"')

def test_problematic_symbols():
    """Test symbols that might cause issues"""
    
    print(f'\n🔍 TESTING POTENTIALLY PROBLEMATIC SYMBOLS')
    print('='*60)
    
    # Test edge cases
    edge_cases = ['', '   ', 'INVALID.HK', '9999.HK', '0000.HK', 'ABC']
    
    for symbol in edge_cases:
        print(f'\n📊 TESTING EDGE CASE: "{symbol}"')
        
        try:
            if symbol.strip():
                trimmed_symbol = symbol.strip().upper()
                stock = yf.Ticker(trimmed_symbol)
                info = stock.info
                
                print(f'  Info keys: {len(info) if info else 0}')
                
                if info and len(info) > 1:
                    company_name = info.get('longName', info.get('shortName', 'Unknown Company'))
                    print(f'  ✅ Found: "{company_name}"')
                else:
                    print(f'  ❌ Not found or limited data')
                    if info:
                        # Show what's in info for debugging
                        print(f'  Info contents: {list(info.keys())[:10]}...')  # First 10 keys
            else:
                print(f'  Empty/whitespace input')
                
        except Exception as e:
            print(f'  ❌ Exception: {str(e)}')

if __name__ == "__main__":
    test_dashboard_symbol_flow()
    test_problematic_symbols()