import yfinance as yf
ticker = yf.Ticker('AAPL')
print('Price:', ticker.fast_info['lastPrice'])
