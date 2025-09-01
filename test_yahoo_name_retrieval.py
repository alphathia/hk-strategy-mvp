#!/usr/bin/env python3
"""
Test Yahoo Finance name retrieval for equity symbols
"""

import yfinance as yf
import sys

def test_yahoo_name_retrieval():
    """Test Yahoo Finance name retrieval for various HK symbols"""
    
    print('🧪 TESTING YAHOO FINANCE NAME RETRIEVAL')
    print('='*60)
    
    # Test with common HK symbols
    test_symbols = ['0700.HK', '0005.HK', '1810.HK', '3690.HK', '9618.HK', '9988.HK', '0001.HK']
    
    for symbol in test_symbols:
        print(f'\n📊 TESTING SYMBOL: {symbol}')
        
        try:
            # Create ticker
            stock = yf.Ticker(symbol)
            print(f'  ✅ Ticker created successfully')
            
            # Get info
            info = stock.info
            print(f'  Info keys count: {len(info) if info else 0}')
            
            if info and len(info) > 1:
                # Check available name fields
                long_name = info.get('longName')
                short_name = info.get('shortName')
                display_name = info.get('displayName')
                quote_type = info.get('quoteType')
                symbol_info = info.get('symbol')
                
                print(f'  longName: "{long_name}"')
                print(f'  shortName: "{short_name}"')
                print(f'  displayName: "{display_name}"')
                print(f'  quoteType: "{quote_type}"')
                print(f'  symbol: "{symbol_info}"')
                
                # Apply current logic
                company_name = info.get('longName', info.get('shortName', 'Unknown Company'))
                print(f'  🎯 Current logic result: "{company_name}"')
                
                # Try alternative approaches
                if not long_name and not short_name:
                    print('  ⚠️  Both longName and shortName are empty!')
                    
                    # Check other possible name fields
                    other_fields = ['name', 'companyName', 'description']
                    for field in other_fields:
                        if field in info:
                            print(f'  Alternative field {field}: "{info[field]}"')
                
            else:
                print(f'  ❌ Info data is empty or limited')
                print(f'  Info content: {info}')
                
        except Exception as e:
            print(f'  ❌ Error: {str(e)}')
            import traceback
            print(f'  Traceback: {traceback.format_exc()}')

def test_improved_name_retrieval():
    """Test improved name retrieval logic"""
    
    print(f'\n🔧 TESTING IMPROVED NAME RETRIEVAL LOGIC')
    print('='*60)
    
    def get_company_name_improved(symbol):
        """Improved company name retrieval"""
        try:
            stock = yf.Ticker(symbol)
            info = stock.info
            
            if not info or len(info) <= 1:
                return 'Unknown Company'
            
            # Try multiple name fields in order of preference
            name_fields = ['longName', 'shortName', 'displayName', 'name']
            
            for field in name_fields:
                name = info.get(field)
                if name and name.strip() and name.strip() != '':
                    return name.strip()
            
            # If no standard name fields work, try getting from symbol info
            if info.get('symbol') == symbol:
                # At least we know the symbol is valid, try to parse it
                if symbol.endswith('.HK'):
                    code = symbol.replace('.HK', '')
                    return f"HK Stock {code}"
            
            return 'Unknown Company'
            
        except Exception as e:
            print(f"Error fetching name for {symbol}: {e}")
            return 'Unknown Company'
    
    # Test improved logic
    test_symbols = ['0700.HK', '0001.HK', '1810.HK']
    
    for symbol in test_symbols:
        print(f'\n📊 TESTING IMPROVED LOGIC: {symbol}')
        result = get_company_name_improved(symbol)
        print(f'  🎯 Improved result: "{result}"')

if __name__ == "__main__":
    test_yahoo_name_retrieval()
    test_improved_name_retrieval()