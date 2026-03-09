import requests
# import pandas as pd
import io
import logging

logger = logging.getLogger(__name__)

class NSEScraper:
    """Utility to fetch and parse official NSE India asset listings."""
    
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": "https://www.nseindia.com/"
    }

    # Direct links to CSV mappings
    URLS = {
        "EQUITIES": "https://archives.nseindia.com/content/equities/EQUITY_L.csv",
        "ETFS": "https://archives.nseindia.com/content/equities/etf_annexure_1.csv" # Note: URL can be dynamic, this is a common static path
    }

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
        # Visit home page first to get cookies
        try:
            self.session.get("https://www.nseindia.com/", timeout=10)
        except Exception as e:
            logger.warning(f"Failed to initialize NSE session: {e}")

    def fetch_all_equities(self):
        import pandas as pd
        """Returns List of symbols for all NSE listed equities."""
        try:
            response = self.session.get(self.URLS["EQUITIES"], timeout=15)
            if response.status_code == 200:
                df = pd.read_csv(io.StringIO(response.text))
                # Normalize symbols with .NS for DataAgent compatibility
                symbols = [f"{s}.NS" for s in df['SYMBOL'].tolist()]
                logger.info(f"Successfully fetched {len(symbols)} equities from NSE")
                return symbols
            else:
                logger.error(f"Failed to fetch equities: HTTP {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"Error fetching NSE equities: {e}")
            return []

    def fetch_all_etfs(self):
        import pandas as pd
        """Returns List of symbols for all NSE listed ETFs."""
        try:
            # ETF URL often changes or is restricted; fallback to scraping if direct fails
            response = self.session.get(self.URLS["ETFS"], timeout=15)
            if response.status_code == 200:
                df = pd.read_csv(io.StringIO(response.text))
                # Columns vary: usually 'SYMBOL' or first column
                sym_col = df.columns[0]
                symbols = [f"{s}.NS" for s in df[sym_col].tolist() if isinstance(s, str)]
                logger.info(f"Successfully fetched {len(symbols)} ETFs from NSE")
                return symbols
            else:
                logger.warning(f"Direct ETF CSV failed (HTTP {response.status_code}). Attempting API fallback.")
                return self._fetch_etfs_via_api()
        except Exception as e:
            logger.error(f"Error fetching NSE ETFs: {e}")
            return self._fetch_etfs_via_api()

    def _fetch_etfs_via_api(self):
        """API Fallback for ETF data if CSV is not reachable."""
        api_url = "https://www.nseindia.com/api/etf"
        try:
            response = self.session.get(api_url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                symbols = [f"{item['symbol']}.NS" for item in data.get('data', [])]
                return symbols
            return []
        except:
            return []

if __name__ == "__main__":
    scraper = NSEScraper()
    equities = scraper.fetch_all_equities()
    print(f"Equities: {len(equities)}")
    etfs = scraper.fetch_all_etfs()
    print(f"ETFs: {len(etfs)}")
