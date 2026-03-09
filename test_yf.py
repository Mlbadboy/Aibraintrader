import yfinance as yf
# Test hanging
targets = ['AAPL', 'TSLA', '^NSEI']
try:
    print('Starting download...')
    df = yf.download(targets, period='1d', interval='1m', progress=False, timeout=5, threads=False)
    print('Done yfinance download. Head:', df.head())
except Exception as e:
    print('Error:', e)
