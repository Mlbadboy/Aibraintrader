from app.agents.data_agent import DataAgent
from app.agents.failsafe_agent import FailsafeAgent
from app.features.indicators import FeatureEngineer
import pandas as pd

def test_phase1():
    print("--- Testing Phase 1 Components ---")
    
    data_agent = DataAgent()
    failsafe_agent = FailsafeAgent()
    feature_engineer = FeatureEngineer()

    # 1. Test Stock Data
    print("\n[1] Testing Stock Data Fetch (RELIANCE.NS)...")
    df_stock = data_agent.fetch_stock_data("RELIANCE.NS", interval="1d", period="3mo")
    if not df_stock.empty:
        print(f"Success! Fetched {len(df_stock)} rows.")
        df_stock_feat = feature_engineer.add_technical_indicators(df_stock)
        rsi_val = df_stock_feat['rsi'].iloc[-1]
        print(f"Indicators added. Latest RSI: {rsi_val:.2f}" if not pd.isna(rsi_val) else "Indicators added. RSI is NaN (insufficient data).")
    else:
        print("Failed to fetch stock data.")

    # 2. Test Crypto Data
    print("\n[2] Testing Crypto Data Fetch (ETH/USDT)...")
    df_crypto = data_agent.fetch_crypto_data("ETH/USDT", interval="1h", limit=100)
    if not df_crypto.empty:
        print(f"Success! Fetched {len(df_crypto)} rows.")
        df_crypto_feat = feature_engineer.add_technical_indicators(df_crypto)
        print(f"Indicators added. Latest MACD: {df_crypto_feat['macd'].iloc[-1]:.4f}")
    else:
        print("Failed to fetch crypto data.")

    # 3. Test Failsafe Scraper
    print("\n[3] Testing Failsafe Scraper (AAPL)...")
    scrape_result = failsafe_agent.scrape_yahoo_finance("AAPL")
    if scrape_result:
        print(f"Success! Scraped price: {scrape_result['price']}")
    else:
        print("Scraper failed (Note: This is brittle and depends on Yahoo Finance UI).")

    print("\n--- Phase 1 Verification Complete ---")

if __name__ == "__main__":
    test_phase1()
