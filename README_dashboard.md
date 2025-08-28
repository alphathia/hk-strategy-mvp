# Portfolio Dashboard

A Streamlit-based portfolio dashboard that displays your stock holdings with real-time prices from Yahoo Finance.

## Features

- **Portfolio Overview**: View all your holdings in a comprehensive table
- **Real-time Prices**: Fetches current stock prices from Yahoo Finance
- **P&L Tracking**: Shows profit/loss for each position and overall portfolio
- **Interactive Charts**: Portfolio allocation pie chart and P&L bar chart
- **Detailed Stock View**: Historical price charts for individual stocks
- **Position Management**: Add, edit, or remove positions through the sidebar

## How to Run

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the dashboard:
   ```bash
   streamlit run dashboard.py
   ```

3. Open your browser to `http://localhost:8501`

## Dashboard Sections

### Portfolio Metrics
- **Portfolio Value**: Total market value of all positions
- **Total Cost**: Total cost basis of all positions  
- **Total P&L**: Overall profit/loss with percentage
- **Number of Positions**: Count of holdings

### Holdings Table
Displays for each position:
- Ticker symbol
- Quantity held
- Cost basis per share
- Current price
- Market value
- Total cost
- P&L amount and percentage

### Visualizations
- **Portfolio Allocation**: Pie chart showing position weights
- **P&L by Position**: Bar chart of gains/losses
- **Price History**: Interactive line chart for selected stocks

### Position Management
Use the sidebar to:
- Add new positions
- Update existing quantities and cost basis
- Remove positions from portfolio

## Sample Data
The dashboard comes pre-loaded with sample positions:
- AAPL: 100 shares at $150 cost basis
- GOOGL: 50 shares at $2,500 cost basis
- MSFT: 75 shares at $300 cost basis
- TSLA: 30 shares at $200 cost basis
- AMZN: 25 shares at $3,200 cost basis

## Data Source
- Stock prices are fetched from Yahoo Finance using the `yfinance` library
- Data is cached for 5 minutes to improve performance
- Historical data is available for various time periods (1 week to 1 year)

## Notes
- Prices may be delayed according to Yahoo Finance data policies
- Internet connection required for real-time price updates
- Portfolio positions are stored in session state (not persistent across browser sessions)