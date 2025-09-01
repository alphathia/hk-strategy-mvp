import sys
sys.path.append('src')
from database import DatabaseManager
import pandas as pd

db_manager = DatabaseManager()
try:
    conn = db_manager.get_connection()
    
    # Check if portfolio exists and has positions
    positions = pd.read_sql('''
        SELECT symbol, company_name, quantity, avg_cost, current_price
        FROM portfolio_positions
        WHERE portfolio_id = %s AND quantity > 0
    ''', conn, params=['My_HKEX_ALL'])
    
    print('Portfolio My_HKEX_ALL has {} positions:'.format(len(positions)))
    for _, pos in positions.iterrows():
        print('  - {}: {} shares @ ${:.2f}'.format(pos['symbol'], pos['quantity'], pos['avg_cost']))
    
    conn.close()
except Exception as e:
    print('Error: {}'.format(e))