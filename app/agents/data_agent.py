# import yfinance as yf
# import ccxt
# import pandas as pd
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataAgent:
    def __init__(self):
        import ccxt
        self.binance = ccxt.binance()
        # Symbol mapping for Yahoo Finance / CCXT data fetching
        self.symbol_mapping = {
            "NIFTY": "^NSEI",
            "SENSEX": "^BSESN",
            "BANKNIFTY": "^NSEBANK",
            "BANKEX": "BSE-BANK.BO",
            "FINNIFTY": "NIFTY_FIN_SERVICE.NS",
            "GOLDBEES": "GOLDBEES.NS",
            "ETH": "ETH-USD",
            "GOLD": "GC=F",
            "SILVER": "SI=F",
            "EURUSD": "EURUSD=X",
            "GBPUSD": "GBPUSD=X",
            "USDJPY": "JPY=X",
            "BTC": "BTC-USD",
            "RELIANCE.NS": "RELIANCE.NS",
            "CRUDEOIL": "CL=F",
            "NATURALGAS": "NG=F",
            "BRENT": "BZ=F",
            "COPPER": "HG=F",
            "PLATINUM": "PL=F"
        }
        
        # Explicit mapping to TradingView symbols to ensure frontend chart matches backend data
        self.tv_symbol_mapping = {
            "NIFTY": "NSE:NIFTY",  # Note: Often restricted in free widget
            "SENSEX": "BSE:SENSEX",
            "BANKNIFTY": "NSE:BANKNIFTY",
            "BANKEX": "BSE:BANKEX",
            "FINNIFTY": "NSE:FINNIFTY",
            "MIDCPNIFTY": "NSE:MIDCPNIFTY",
            "GOLDBEES": "NSE:GOLDBEES",
            "LIQUIDBEES": "NSE:LIQUIDBEES",
            "GOLD": "OANDA:XAUUSD",
            "SILVER": "OANDA:XAGUSD",
            "EURUSD": "FX:EURUSD",
            "GBPUSD": "FX:GBPUSD",
            "USDJPY": "FX:USDJPY",
            "BTC": "BINANCE:BTCUSDT",
            "ETH": "BINANCE:ETHUSDT",
            "RELIANCE.NS": "BSE:RELIANCE", # Map NSE ticker to BSE chart for free widget compatibility
            "HDFCBANK.NS": "BSE:HDFCBANK",
            "TATASTEEL.NS": "BSE:TATASTEEL",
            "CRUDEOIL": "TVC:USOIL",
            "NATURALGAS": "TVC:NATURALGAS",
            "BRENT": "TVC:UKOIL"
        }

    def _format_symbol(self, symbol: str) -> str:
        """Maps common aliases to data provider-specific symbols."""
        sym = symbol.upper()
        if sym in self.symbol_mapping:
            return self.symbol_mapping[sym]
        return sym

    def get_tv_symbol(self, symbol: str) -> str:
        """Returns the exact TradingView symbol for the frontend chart."""
        sym = symbol.upper()
        if sym in self.tv_symbol_mapping:
            return self.tv_symbol_mapping[sym]
        # For Indian stocks, default to BSE to bypass free widget's NSE restrictions
        if sym.endswith('.NS'):
            return f"BSE:{sym.split('.')[0]}"
        if sym.endswith('.BO'):
            return f"BSE:{sym.split('.')[0]}"
        # Crypto fallback
        if '/' in sym or sym in ['SOL', 'DOGE', 'ADA', 'DOT']:
            clean = sym.replace('/', '').replace('USDT', '')
            return f"BINANCE:{clean}USDT"
        # US Stocks / ETFs fallback
        if sym in ['SPY', 'QQQ', 'DIA', 'IWM']:
            return f"AMEX:{sym}"
        return sym

    def fetch_stock_data(self, symbol: str, interval: str = "1h", period: str = "1mo"):
        """
        Fetch stock data from Yahoo Finance.
        :param symbol: Stock symbol (e.g., AAPL, RELIANCE.NS, NIFTY)
        :param interval: Data interval (1m, 5m, 1h, 1d)
        :param period: Data period (1d, 5d, 1mo, 1y)
        """
        import pandas as pd
        import yfinance as yf
        symbol = self._format_symbol(symbol)
        try:
            logger.info(f"Fetching stock data for {symbol} with interval {interval}")
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period, interval=interval)
            if df.empty:
                logger.warning(f"No data found for {symbol}")
                return pd.DataFrame()
            df.reset_index(inplace=True)
            df.rename(columns={"Date": "timestamp", "Datetime": "timestamp", "Open": "open", "High": "high", "Low": "low", "Close": "close", "Volume": "volume"}, inplace=True)
            return df
        except Exception as e:
            logger.error(f"Error fetching stock data for {symbol}: {e}")
            return pd.DataFrame()

    def fetch_crypto_data(self, symbol: str = "BTC/USDT", interval: str = "1h", limit: int = 500):
        """
        Fetch crypto data from Binance via CCXT.
        :param symbol: Crypto pair (e.g., BTC/USDT or just BTC)
        :param interval: Data interval (1m, 5m, 1h, 1d)
        :param limit: Number of candles
        """
        import pandas as pd
        # Ensure Binance pair formatting
        formatted_symbol = symbol.upper()
        if '/' not in formatted_symbol and not formatted_symbol.endswith('USDT') and not formatted_symbol.endswith('USD'):
            formatted_symbol = f"{formatted_symbol}/USDT"
        elif formatted_symbol.endswith('USD') and '-' in formatted_symbol:
             # Convert BTC-USD to BTC/USDT for Binance
             formatted_symbol = formatted_symbol.replace('-USD', '/USDT')
        elif formatted_symbol.endswith('USD') and '-' not in formatted_symbol:
             formatted_symbol = formatted_symbol.replace('USD', '/USDT')
        try:
            logger.info(f"Fetching crypto data for {formatted_symbol} with interval {interval}")
            bars = self.binance.fetch_ohlcv(formatted_symbol, timeframe=interval, limit=limit)
            df = pd.DataFrame(bars, columns=["timestamp", "open", "high", "low", "close", "volume"])
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
            return df
        except Exception as e:
            logger.error(f"Error fetching crypto data for {symbol}: {e}")
            return pd.DataFrame()

    def fetch_batch_prices(self, symbols: list, asset_types: list) -> dict:
        """
        Fetches live prices in bulk. Returns dict: { 'AAPL': 150.5, 'BTC': 69000.0 }
        """
        results = {}
        
        import concurrent.futures

        # 1. Separate into Crypto and Non-Crypto
        crypto_symbols = []
        stock_symbols = []
        
        for sym, atype in zip(symbols, asset_types):
            if atype == 'crypto':
                formatted = sym.upper()
                if '/' not in formatted and not formatted.endswith('USDT') and not formatted.endswith('USD'):
                    formatted = f"{formatted}/USDT"
                elif formatted.endswith('USD') and '-' in formatted:
                     formatted = formatted.replace('-USD', '/USDT')
                elif formatted.endswith('USD') and '-' not in formatted:
                     formatted = formatted.replace('USD', '/USDT')
                crypto_symbols.append((sym, formatted))
            else:
                stock_symbols.append((sym, self._format_symbol(sym)))

        # 2. Bulk Fetch Crypto
        def fetch_crypto():
            try:
                targets = [c[1] for c in crypto_symbols]
                tickers = self.binance.fetch_tickers(targets)
                for original_sym, target_sym in crypto_symbols:
                    if target_sym in tickers and 'last' in tickers[target_sym]:
                        results[original_sym] = tickers[target_sym]['last']
            except Exception as e:
                logger.error(f"Batch Crypto Fetch Error: {e}")

        # 3. Bulk Fetch Stocks
        def fetch_stocks():
            import yfinance as yf
            try:
                targets = [s[1] for s in stock_symbols]
                if targets:
                    df = yf.download(targets, period="1d", interval="1m", progress=False, threads=False)
                    if not df.empty and 'Close' in df:
                        if len(targets) == 1:
                            results[stock_symbols[0][0]] = float(df['Close'].iloc[-1])
                        else:
                            for original_sym, target_sym in stock_symbols:
                                if target_sym in df['Close'] and not pd.isna(df['Close'][target_sym].iloc[-1]):
                                    results[original_sym] = float(df['Close'][target_sym].iloc[-1])
            except Exception as e:
                logger.error(f"Batch Stock Fetch Error: {e}")

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            futures = []
            if crypto_symbols:
                futures.append(executor.submit(fetch_crypto))
            if stock_symbols:
                futures.append(executor.submit(fetch_stocks))
                
        for future in futures:
            try:
                future.result(timeout=8) # strict 8 second timeout
            except concurrent.futures.TimeoutError:
                logger.warning("Batch fetch timed out after 8s")
            except Exception as e:
                logger.error(f"Batch fetch future error: {e}")

        return results

    def fetch_rapid_price(self, symbol: str) -> float:
        """
        Ultra-lightweight price fetcher using pure requests.
        Bypasses yfinance library to avoid deadlock.
        """
        import requests
        from bs4 import BeautifulSoup
        
        # 1. Try Crypto via direct Binance API (fast & no pandas)
        sym_upper = symbol.upper()
        if "/" in sym_upper or "-" in sym_upper or "USDT" in sym_upper or sym_upper in ['BTC', 'ETH', 'SOL', 'DOGE']:
            try:
                # Map common crypto tickers to Binance pairs
                crypto_map = {"BTC": "BTCUSDT", "ETH": "ETHUSDT", "SOL": "SOLUSDT", "DOGE": "DOGEUSDT"}
                clean_sym = sym_upper.replace("/", "").replace("-", "")
                if clean_sym in crypto_map:
                    clean_sym = crypto_map[clean_sym]
                
                res = requests.get(f"https://api.binance.com/api/v3/ticker/price?symbol={clean_sym}", timeout=3)
                if res.status_code == 200:
                    return float(res.json()['price'])
            except:
                pass

        # 2. Try Stocks/Indices via Yahoo JSON API
        try:
            target_sym = self._format_symbol(symbol)
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{target_sym}"
            headers = {"User-Agent": "Mozilla/5.0"}
            res = requests.get(url, headers=headers, timeout=3)
            if res.status_code == 200:
                data = res.json()
                result = data.get('chart', {}).get('result')
                if result and len(result) > 0:
                    price = result[0].get('meta', {}).get('regularMarketPrice')
                    if price is not None:
                        return float(price)
        except Exception as e:
            logger.error(f"Rapid fetch failed for {symbol}: {e}")
            
        return 0.0

if __name__ == "__main__":
    # Test
    agent = DataAgent()
    print("Testing Stock Data Fetch (AAPL):")
    print(agent.fetch_stock_data("AAPL").head())
    print("\nTesting Crypto Data Fetch (BTC/USDT):")
    print(agent.fetch_crypto_data("BTC/USDT").head())
