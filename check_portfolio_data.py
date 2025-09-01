#!/usr/bin/env python3
import sys
sys.path.append('src')
from src.database import DatabaseManager

# Check actual values in the data
db = DatabaseManager()
conn = db.get_connection()
cur = conn.cursor()

print('Raw portfolio_value_history data check...')

cur.execute('''
    SELECT analysis_id, trade_date, portfolio_value, total_value, daily_change
    FROM portfolio_value_history 
    WHERE analysis_id = 3
    ORDER BY trade_date DESC
    LIMIT 5
''')

results = cur.fetchall()
print('Sample raw data for analysis_id = 3:')
for row in results:
    print(f'Row: {row}')
    if row[2] is not None:
        print(f'  Portfolio Value: {float(row[2]):.2f}')
    if row[3] is not None:
        print(f'  Total Value: {float(row[3]):.2f}')
    print()

# Check if portfolio values are actually zero
cur.execute('''
    SELECT 
        analysis_id,
        COUNT(*) as total_records,
        COUNT(CASE WHEN portfolio_value = 0 THEN 1 END) as zero_values,
        COUNT(CASE WHEN portfolio_value IS NULL THEN 1 END) as null_values,
        AVG(CASE WHEN portfolio_value != 0 AND portfolio_value IS NOT NULL THEN portfolio_value END) as avg_non_zero
    FROM portfolio_value_history 
    GROUP BY analysis_id
    ORDER BY analysis_id
    LIMIT 5
''')

print('Portfolio value statistics by analysis:')
print('Analysis | Total Records | Zero Values | Null Values | Avg Non-Zero Value')
print('-' * 75)
for row in cur.fetchall():
    analysis_id, total_records, zero_values, null_values, avg_non_zero = row
    avg_display = f'${float(avg_non_zero):,.2f}' if avg_non_zero else 'N/A'
    print(f'{analysis_id:<8} | {total_records:<13} | {zero_values:<11} | {null_values:<11} | {avg_display}')

conn.close()