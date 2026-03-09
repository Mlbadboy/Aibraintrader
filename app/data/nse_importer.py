"""
NSE India Auto-Importer
=======================
Automatically downloads ALL instruments from NSE India every Sunday and adds them
to the radar watchlist. Covers:
  - All listed equities (3000+ stocks)
  - All F&O stocks (futures & options eligible)
  - NSE Indices (NIFTY 50, NIFTY 100, NIFTY Bank, Midcap, Smallcap, etc.)
  - ETFs listed on NSE
  - Currencies (USDINR, EURINR, etc.)
  - NSE Commodities (Gold, Silver, Crude Oil, etc.)
  - Top Crypto via Binance (BTC, ETH, SOL, etc.)

Data sources:
  - https://archives.nseindia.com/content/equities/EQUITY_L.csv   (all equities)
  - https://archives.nseindia.com/content/fo/fo_mktlots.csv        (F&O eligible)
  - https://archives.nseindia.com/content/indices/ind_nifty50list.csv
  - https://archives.nseindia.com/content/indices/ind_niftybanklist.csv
  - https://archives.nseindia.com/content/indices/ind_nifty100list.csv
  - https://archives.nseindia.com/content/indices/ind_niftymidcap50list.csv
  - https://archives.nseindia.com/content/etf/etflist.csv          (ETFs)
  - Binance public API for crypto list
"""

import requests
import pandas as pd
import io
import logging
import time
from datetime import datetime
from app.radar.database import RadarDB

logger = logging.getLogger(__name__)

# -------------------------------------------------------------------
# NSE Public CSV endpoints (no authentication needed)
# -------------------------------------------------------------------
NSE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Referer": "https://www.nseindia.com/",
}

NSE_EQUITY_CSV    = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
NSE_FO_CSV        = "https://archives.nseindia.com/content/fo/fo_mktlots.csv"
NSE_ETF_CSV       = "https://archives.nseindia.com/content/etf/etflist.csv"

NSE_INDEX_CSVS = {
    "ind_nifty50list.csv":       "https://archives.nseindia.com/content/indices/ind_nifty50list.csv",
    "ind_niftybanklist.csv":     "https://archives.nseindia.com/content/indices/ind_niftybanklist.csv",
    "ind_nifty100list.csv":      "https://archives.nseindia.com/content/indices/ind_nifty100list.csv",
    "ind_niftymidcap50list.csv": "https://archives.nseindia.com/content/indices/ind_niftymidcap50list.csv",
    "ind_niftymidcap150list.csv":"https://archives.nseindia.com/content/indices/ind_niftymidcap150list.csv",
    "ind_niftysmallcap50list.csv":"https://archives.nseindia.com/content/indices/ind_niftysmallcap50list.csv",
    "ind_niftyit.csv":           "https://archives.nseindia.com/content/indices/ind_niftyit.csv",
    "ind_niftypharma.csv":       "https://archives.nseindia.com/content/indices/ind_niftypharma.csv",
    "ind_niftyfinservice.csv":   "https://archives.nseindia.com/content/indices/ind_niftyfinservice.csv",
    "ind_niftyauto.csv":         "https://archives.nseindia.com/content/indices/ind_niftyauto.csv",
    "ind_niftyfmcg.csv":         "https://archives.nseindia.com/content/indices/ind_niftyfmcg.csv",
    "ind_niftymetal.csv":        "https://archives.nseindia.com/content/indices/ind_niftymetal.csv",
    "ind_niftyrealty.csv":       "https://archives.nseindia.com/content/indices/ind_niftyrealty.csv",
    "ind_niftyenergy.csv":       "https://archives.nseindia.com/content/indices/ind_niftyenergy.csv",
    "ind_niftyinfra.csv":        "https://archives.nseindia.com/content/indices/ind_niftyinfra.csv",
}

# Manually curated NSE indices (no CSV, added directly)
NSE_INDICES_MANUAL = [
    ("NIFTY",       "stock",     "INTRADAY"),
    ("BANKNIFTY",   "stock",     "INTRADAY"),
    ("SENSEX",      "stock",     "INTRADAY"),
    ("BANKEX",      "stock",     "SHORT"),
    ("FINNIFTY",    "stock",     "INTRADAY"),
    ("MIDCPNIFTY",  "stock",     "SHORT"),
    ("NIFTYIT",     "stock",     "SHORT"),
]

# NSE F&O commodities (traded via NSE commodity segment)
NSE_COMMODITIES = [
    ("GOLD",        "commodity", "SHORT"),
    ("SILVER",      "commodity", "SHORT"),
    ("CRUDEOIL",    "commodity", "SHORT"),
    ("NATURALGAS",  "commodity", "SHORT"),
    ("COPPER",      "commodity", "SHORT"),
    ("ZINC",        "commodity", "SHORT"),
    ("NICKEL",      "commodity", "SHORT"),
    ("ALUMINIUM",   "commodity", "SHORT"),
    ("LEAD",        "commodity", "SHORT"),
    ("COTTON",      "commodity", "LONG"),
    ("CASTORSEED",  "commodity", "SHORT"),
    ("MENTHAOIL",   "commodity", "SHORT"),
]

# NSE Currency pairs
NSE_CURRENCIES = [
    ("USDINR",  "stock", "SHORT"),
    ("EURINR",  "stock", "SHORT"),
    ("GBPINR",  "stock", "SHORT"),
    ("JPYINR",  "stock", "SHORT"),
]

# Top Crypto on Binance (24/7 coverage)
TOP_CRYPTO = [
    ("BTC",     "crypto", "SHORT"),
    ("ETH",     "crypto", "SHORT"),
    ("BNB",     "crypto", "SHORT"),
    ("SOL",     "crypto", "SHORT"),
    ("XRP",     "crypto", "SHORT"),
    ("ADA",     "crypto", "SHORT"),
    ("DOGE",    "crypto", "SHORT"),
    ("MATIC",   "crypto", "SHORT"),
    ("DOT",     "crypto", "SHORT"),
    ("AVAX",    "crypto", "SHORT"),
    ("LINK",    "crypto", "SHORT"),
    ("LTC",     "crypto", "SHORT"),
    ("ATOM",    "crypto", "SHORT"),
    ("UNI",     "crypto", "SHORT"),
    ("BTCUSDT", "crypto", "SHORT"),
    ("ETHUSDT", "crypto", "SHORT"),
    ("SOLUSDT", "crypto", "SHORT"),
    ("BNBUSDT", "crypto", "SHORT"),
]


# -------------------------------------------------------------------
# Helper: safe CSV download
# -------------------------------------------------------------------
def _fetch_csv(url: str, timeout: int = 20) -> pd.DataFrame:
    """Download a CSV from NSE archives and return as DataFrame."""
    try:
        # First hit the main NSE site to get cookies (NSE blocks direct CSV access)
        session = requests.Session()
        session.get("https://www.nseindia.com", headers=NSE_HEADERS, timeout=10)
        time.sleep(0.5)
        resp = session.get(url, headers=NSE_HEADERS, timeout=timeout)
        if resp.status_code == 200:
            content = resp.content.decode("utf-8", errors="ignore")
            df = pd.read_csv(io.StringIO(content))
            df.columns = [c.strip() for c in df.columns]  # trim whitespace
            return df
        else:
            logger.warning(f"NSE CSV {url} returned HTTP {resp.status_code}")
    except Exception as e:
        logger.error(f"Error downloading NSE CSV {url}: {e}")
    return pd.DataFrame()


# -------------------------------------------------------------------
# Import functions per category
# -------------------------------------------------------------------

def import_nse_equities(max_stocks: int = 500) -> int:
    """
    Import top NSE equities from the master equity list.
    Only imports EQ series (not BE, BL, BT etc) to focus on liquid stocks.
    Returns count of stocks added.
    """
    logger.info("NSE Import: Fetching all equities...")
    df = _fetch_csv(NSE_EQUITY_CSV)
    if df.empty:
        logger.warning("NSE equity CSV empty or download failed")
        return 0

    # Filter: EQ series only (main liquid stocks)
    symbol_col = "SYMBOL"
    series_col = " SERIES" if " SERIES" in df.columns else "SERIES"

    if symbol_col not in df.columns:
        logger.error(f"Unexpected CSV columns: {df.columns.tolist()}")
        return 0

    eq_stocks = df[df.get(series_col, pd.Series()).str.strip() == "EQ"][symbol_col].dropna()

    added = 0
    for sym in eq_stocks[:max_stocks]:
        sym = str(sym).strip().upper()
        if not sym or len(sym) > 20:
            continue
        # Append .NS for Yahoo Finance compatibility
        yf_symbol = f"{sym}.NS"
        RadarDB.add_to_watchlist(yf_symbol, "stock", "SHORT")
        added += 1

    logger.info(f"NSE Import: Added {added} equities")
    return added


def import_nse_fo_stocks() -> int:
    """
    Import all F&O eligible stocks. These are the most liquid large-cap NSE stocks.
    """
    logger.info("NSE Import: Fetching F&O eligible stocks...")
    df = _fetch_csv(NSE_FO_CSV)
    if df.empty:
        logger.warning("NSE F&O CSV empty or download failed")
        return 0

    # F&O CSV has SYMBOL in various columns depending on format
    symbol_col = None
    for col in ["Symbol", "SYMBOL", "Underlying", "UNDERLYING"]:
        if col in df.columns:
            symbol_col = col
            break

    if not symbol_col:
        logger.error(f"F&O CSV columns: {df.columns.tolist()}")
        return 0

    added = 0
    for sym in df[symbol_col].dropna().unique():
        sym = str(sym).strip().upper()
        if not sym or len(sym) > 20 or sym.startswith("SYMBOL"):
            continue
        yf_symbol = f"{sym}.NS"
        RadarDB.add_to_watchlist(yf_symbol, "fo", "INTRADAY")
        added += 1

    logger.info(f"NSE Import: Added {added} F&O stocks")
    return added


def import_nse_index_constituents() -> int:
    """
    Import stocks from all major NSE index lists (NIFTY 50, Bank, IT, etc.)
    These are the highest priority / most liquid stocks.
    """
    logger.info("NSE Import: Fetching index constituents...")
    added = 0
    for name, url in NSE_INDEX_CSVS.items():
        df = _fetch_csv(url)
        if df.empty:
            continue
        symbol_col = None
        for col in ["Symbol", "SYMBOL", "symbol"]:
            if col in df.columns:
                symbol_col = col
                break
        if not symbol_col:
            continue
        for sym in df[symbol_col].dropna():
            sym = str(sym).strip().upper()
            if not sym:
                continue
            yf_symbol = f"{sym}.NS"
            RadarDB.add_to_watchlist(yf_symbol, "stock", "SHORT")
            added += 1
        time.sleep(0.3)  # polite rate limiting

    logger.info(f"NSE Import: Added {added} index constituent stocks")
    return added


def import_nse_etfs(max_etfs: int = 100) -> int:
    """
    Import NSE-listed ETFs.
    """
    logger.info("NSE Import: Fetching ETFs...")
    df = _fetch_csv(NSE_ETF_CSV)
    if df.empty:
        logger.warning("NSE ETF CSV empty")
        return 0

    symbol_col = None
    for col in ["SYMBOL", "Symbol", "symbol"]:
        if col in df.columns:
            symbol_col = col
            break
    if not symbol_col:
        return 0

    added = 0
    for sym in df[symbol_col].dropna()[:max_etfs]:
        sym = str(sym).strip().upper()
        if not sym:
            continue
        yf_symbol = f"{sym}.NS"
        RadarDB.add_to_watchlist(yf_symbol, "etf", "LONG")
        added += 1

    logger.info(f"NSE Import: Added {added} ETFs")
    return added


def import_manual_instruments() -> int:
    """
    Add manually curated instruments: NSE indices, commodities,
    currency pairs, and top crypto.
    """
    added = 0
    all_instruments = (
        NSE_INDICES_MANUAL +
        NSE_COMMODITIES +
        NSE_CURRENCIES +
        TOP_CRYPTO
    )
    for sym, asset_type, horizon in all_instruments:
        RadarDB.add_to_watchlist(sym, asset_type, horizon)
        added += 1

    logger.info(f"NSE Import: Added {added} manual instruments (indices + commodities + crypto)")
    return added


# -------------------------------------------------------------------
# Master sync function — called by the weekly scheduler
# -------------------------------------------------------------------

def run_weekly_nse_sync(max_equities: int = 500) -> dict:
    """
    Full weekly NSE sync.
    Imports all instrument categories and returns a summary.
    Designed to run every Sunday before market opens.
    """
    logger.info("=" * 60)
    logger.info("WEEKLY NSE SYNC STARTED — " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    logger.info("=" * 60)

    summary = {
        "sync_time":    datetime.now().isoformat(),
        "equities":     0,
        "fo_stocks":    0,
        "index_stocks": 0,
        "etfs":         0,
        "manual":       0,
        "total":        0,
        "status":       "success"
    }

    try:
        # 1. Manually curated (always first — these are the most important)
        summary["manual"] = import_manual_instruments()

        # 2. Index constituents (high priority, liquid)
        summary["index_stocks"] = import_nse_index_constituents()

        # 3. F&O stocks (large-cap, high volume)
        summary["fo_stocks"] = import_nse_fo_stocks()

        # 4. All NSE equities (up to max_equities)
        summary["equities"] = import_nse_equities(max_equities)

        # 5. ETFs
        summary["etfs"] = import_nse_etfs()

        summary["total"] = (
            summary["equities"] + summary["fo_stocks"] +
            summary["index_stocks"] + summary["etfs"] + summary["manual"]
        )

    except Exception as e:
        logger.error(f"Weekly NSE sync error: {e}")
        summary["status"] = f"error: {e}"

    logger.info(f"WEEKLY NSE SYNC COMPLETE — Total instruments synced: {summary['total']}")
    logger.info(f"  Equities: {summary['equities']}  |  F&O: {summary['fo_stocks']}  |  "
                f"Index: {summary['index_stocks']}  |  ETFs: {summary['etfs']}  |  "
                f"Manual (Crypto+Commodities+Indices): {summary['manual']}")

    return summary
