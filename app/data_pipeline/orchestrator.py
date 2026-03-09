import pandas as pd
import yfinance as yf
import ccxt
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class DataOrchestrator:
    """
    Centralized data ingestion layer handling yfinance for traditional assets
    and ccxt for crypto, returning normalized OHLCV DataFrames.
    """
    def __init__(self):
        self.binance = ccxt.binance()
        
        # Mapping to yfinance specific symbols
        self.yf_symbol_mapping = {
            "NIFTY": "^NSEI",
            "SENSEX": "^BSESN",
            "BANKNIFTY": "^NSEBANK",
            "BANKEX": "BSE-BANK.BO",
            "ETH": "ETH-USD",
            "GOLD": "GC=F",
            "SILVER": "SI=F",
            "CRUDEOIL": "CL=F",
            "EURUSD": "EURUSD=X",
            "GBPUSD": "GBPUSD=X",
            "USDJPY": "JPY=X",
            "BTC": "BTC-USD"
        }

    def _format_yf_symbol(self, symbol: str) -> str:
        sym = symbol.upper()
        if sym in self.yf_symbol_mapping:
            return self.yf_symbol_mapping[sym]
        return symbol

    def _format_ccxt_symbol(self, symbol: str) -> str:
        sym = symbol.upper()
        if sym in ['BTC', 'ETH', 'SOL', 'ADA', 'DOT', 'DOGE']:
            return f"{sym}/USDT"
            
        # If it's already perfectly formatted (BTC/USDT), return it
        if '/' in sym:
            return sym
            
        # If it ends with USDT but has no slash (BTCUSDT), inject the slash
        if sym.endswith('USDT'):
            return sym[:-4] + '/USDT'
            
        # If it ends with USD but has no slash (BTCUSD), inject the slash and convert to USDT
        if sym.endswith('USD'):
             return sym.replace('-USD', '').replace('USD', '') + '/USDT'
             
        # Fallback: append /USDT to whatever it is (e.g. injected "XRP")
        return f"{sym}/USDT"

    def fetch_ohlcv(self, symbol: str, asset_type: str = "stock", interval: str = "1h", limit: int = 500) -> pd.DataFrame:
        """
        Main entry point for pulling normalized OHLCV data.
        Returns cols: ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        """
        asset_type_lower = asset_type.lower()
        if asset_type_lower == "crypto":
            return self._fetch_crypto(symbol, interval, limit)
        else:
            return self._fetch_traditional(symbol, interval, limit)

    def _fetch_traditional(self, symbol: str, interval: str, limit: int) -> pd.DataFrame:
        yf_symbol = self._format_yf_symbol(symbol)
        try:
            # Map common periods based on limit to ensure we get enough data
            period = "1mo"
            if limit > 500 and interval in ["1h", "1d"]:
                period = "1y"
            elif limit > 1000:
                period = "2y"
            elif limit > 2000:
                period = "5y"
            
            # yf doesn't directly support limit, so we fetch period and tail
            ticker = yf.Ticker(yf_symbol)
            df = ticker.history(period=period, interval=interval)
            
            if df.empty:
                logger.warning(f"[DataOrchestrator] No data found for {yf_symbol}")
                return pd.DataFrame()
                
            df.reset_index(inplace=True)
            # Normalize column names
            rename_map = {
                "Date": "timestamp", 
                "Datetime": "timestamp", 
                "Open": "open", 
                "High": "high", 
                "Low": "low", 
                "Close": "close", 
                "Volume": "volume"
            }
            df.rename(columns=rename_map, inplace=True)
            # Keep only standard columns
            df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
            
            return df.tail(limit).reset_index(drop=True)
            
        except Exception as e:
            logger.error(f"[DataOrchestrator] Error fetching YF data for {yf_symbol}: {e}")
            return pd.DataFrame()

    def _fetch_crypto(self, symbol: str, interval: str, limit: int) -> pd.DataFrame:
        ccxt_symbol = self._format_ccxt_symbol(symbol)
        try:
            # map yf intervals to standard ccxt timeframe
            tf_map = {"1m": "1m", "5m": "5m", "15m": "15m", "1h": "1h", "1d": "1d"}
            timeframe = tf_map.get(interval, "1h")
            
            bars = self.binance.fetch_ohlcv(ccxt_symbol, timeframe=timeframe, limit=limit)
            df = pd.DataFrame(bars, columns=["timestamp", "open", "high", "low", "close", "volume"])
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
            
            return df
            
        except Exception as e:
            logger.error(f"[DataOrchestrator] Error fetching CCXT data for {ccxt_symbol}: {e}")
            return pd.DataFrame()
