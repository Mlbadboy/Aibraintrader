import yfinance as yf
import pandas as pd
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class MFDataAgent:
    """
    Handles fetching historical NAV data for Mutual Funds.
    Standardizes the data for the prediction and risk engines.
    """
    
    def __init__(self):
        pass

    def fetch_nav_history(self, symbol: str, period: str = "5y") -> pd.DataFrame:
        """
        Fetches historical daily NAV data.
        Many Indian/Global MFs are available on Yahoo Finance (e.g., '0P00005WLZ.BO' for Parag Parikh Flexi Cap).
        """
        try:
            fund = yf.Ticker(symbol)
            df = fund.history(period=period)
            
            if df.empty:
                logger.warning(f"No NAV data found for {symbol}")
                return pd.DataFrame()

            # Clean and standardize columns
            df.reset_index(inplace=True)
            # YF sometimes returns 'Date' or 'Datetime'
            date_col = 'Date' if 'Date' in df.columns else 'Datetime'
            
            # For MFs, 'Close' is the NAV
            mf_df = pd.DataFrame({
                'date': pd.to_datetime(df[date_col]).dt.tz_localize(None),
                'nav': df['Close']
            })
            
            # Sort chronologically
            mf_df.sort_values('date', inplace=True)
            mf_df.dropna(inplace=True)
            
            return mf_df

        except Exception as e:
            logger.error(f"Error fetching MF data for {symbol}: {e}")
            return pd.DataFrame()

    def fetch_fund_metadata(self, symbol: str) -> dict:
        """
        Attempts to fetch basic ETF/MF metadata.
        Warning: yfinance coverage for MF metadata (like expense ratio) can be spotty.
        """
        try:
            fund = yf.Ticker(symbol)
            info = fund.info
            
            return {
                "name": info.get("shortName", symbol),
                "category": info.get("category", "Unknown"),
                "expense_ratio": info.get("annualReportExpenseRatio", None),
                "yield": info.get("yield", None),
                "total_assets": info.get("totalAssets", None)
            }
        except Exception as e:
            logger.warning(f"Could not fetch metadata for {symbol}: {e}")
            return {"name": symbol}

if __name__ == "__main__":
    # Test with a known ETF/Fund if available
    agent = MFDataAgent()
    # SPY as a proxy test if specific MF tickers aren't known yet
    df = agent.fetch_nav_history("SPY", period="1y") 
    print(df.head())
    print(agent.fetch_fund_metadata("SPY"))
