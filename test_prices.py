#!/usr/bin/env python3
"""
Test script to verify HKEX price fetching from Yahoo Finance
"""
import yfinance as yf

def get_stock_price(hk_symbol):
    """Fetch current price for Hong Kong stock from Yahoo Finance"""
    try:
        print(f"🔍 Fetching price for: {hk_symbol}")
        stock = yf.Ticker(hk_symbol)
        
        # Try historical data first (most reliable)
        hist = stock.history(period="2d")
        if not hist.empty:
            price = float(hist['Close'].iloc[-1])
            print(f"✅ Got price for {hk_symbol}: HK${price:.2f}")
            return price
        
        # Try info method as backup
        info = stock.info
        current_price = info.get('currentPrice', info.get('regularMarketPrice', info.get('previousClose')))
        if current_price and current_price > 0:
            price = float(current_price)
            print(f"📈 Got info price for {hk_symbol}: HK${price:.2f}")
            return price
            
        print(f"❌ No price data found for {hk_symbol}")
        return 50.0
        
    except Exception as e:
        print(f"💥 Error fetching {hk_symbol}: {str(e)}")
        return 50.0

# Test all portfolio symbols
portfolio_symbols = [
    '0005.HK', '0316.HK', '0388.HK', '0700.HK', '0823.HK', '0857.HK',
    '0939.HK', '1810.HK', '2888.HK', '3690.HK', '9618.HK', '9988.HK'
]

print("🏦 Testing HKEX Price Fetching for Portfolio")
print("=" * 50)

total_value = 0
working_count = 0

for symbol in portfolio_symbols:
    price = get_stock_price(symbol)
    if price > 50.0:  # Not default fallback price
        working_count += 1
    total_value += price
    print()

print("=" * 50)
print(f"📊 Results:")
print(f"Working symbols: {working_count}/{len(portfolio_symbols)}")
print(f"Average price: HK${total_value/len(portfolio_symbols):.2f}")
print(f"Total test value: HK${total_value:.2f}")

if working_count == len(portfolio_symbols):
    print("🎯 ✅ ALL PRICES WORKING - Dashboard should display correctly!")
else:
    print(f"⚠️ {len(portfolio_symbols)-working_count} symbols falling back to default prices")