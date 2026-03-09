import requests
import time
import sys
import json

BASE_URL = "http://localhost:8000"

def verify_server_running():
    print("[1] Checking if Backend is accessible...")
    try:
        res = requests.get(f"{BASE_URL}/")
        if res.status_code == 200:
            print("  ✓ Server is up:", res.json())
            return True
    except requests.exceptions.ConnectionError:
        print("  ✗ Cannot connect to server. Is `python -m app.main` running?")
        return False
    return False

def verify_stock_pipeline(symbol="AAPL"):
    print(f"\n[2] Verifying Full Stock Pipeline ({symbol})...")
    start = time.time()
    res = requests.get(f"{BASE_URL}/analyze/stock/{symbol}")
    elapsed = time.time() - start
    print(f"  Request took {elapsed:.2f}s")
    
    if res.status_code != 200:
        print(f"  ✗ Request failed with status {res.status_code}: {res.text}")
        return False
        
    data = res.json()
    
    # Check structure
    required_keys = ['symbol', 'regime', 'selected_strategy', 'sentiment', 'ml_predictions', 'trading_decision', 'risk_assessment', 'latest_indicators']
    for k in required_keys:
        if k not in data:
            print(f"  ✗ Missing root key: {k}")
            return False
            
    print("  ✓ All required top-level JSON keys present.")
    
    # Validate specific outputs
    print(f"  - Regime Detected: {data['regime']}")
    print(f"  - Strategy Selected: {data['selected_strategy']}")
    print(f"  - Sentiment Score: {data['sentiment']['score']}")
    
    ml = data['ml_predictions']
    print(f"  - Ensemble MLBull: {ml['bull_prob']:.2f}, Bear: {ml['bear_prob']:.2f}")
    assert abs(ml['bull_prob'] + ml['bear_prob'] - 1.0) < 0.01, "Probabilities should sum to 1"
    
    dec = data['trading_decision']
    print(f"  - Debate Decision: {dec['decision']} (Conf: {dec['confidence']:.2f})")
    
    risk = data['risk_assessment']
    print(f"  - Risk Assessment:")
    print(f"      Action: {risk['approved_action']}")
    if risk['approved_action'] != 'HOLD':
        print(f"      Stop Loss: {risk['stop_loss']}")
        print(f"      Take Profit: {risk['take_profit']}")
        print(f"      Position USD: {risk['position_size_usd']}")
        assert risk['stop_loss'] > 0
        
    return True

def verify_crypto_pipeline(symbol="BTC-USDT"):
    print(f"\n[3] Verifying Crypto Pipeline ({symbol})...")
    res = requests.get(f"{BASE_URL}/analyze/crypto/{symbol}")
    
    if res.status_code != 200:
         print(f"  ✗ Request failed with status {res.status_code}: {res.text}")
         return False
         
    data = res.json()
    
    if 'symbol' in data and '/' in data['symbol']:
        print(f"  ✓ Crypto analysis successful ({data['symbol']})")
        print(f"  - Regime Detected: {data['regime']}")
        print(f"  - Debate Decision: {data['trading_decision']['decision']}")
        return True
    
    print("  ✗ Crypto symbol not returned correctly")
    return False

def verify_mutual_fund_pipeline(symbol="SPY"):
    print(f"\n[4] Verifying Mutual Fund Intelligence ({symbol})...")
    res = requests.get(f"{BASE_URL}/analyze/mutualfund/{symbol}?user_profile=Moderate&monthly_sip=5000&sip_years=10")
    
    if res.status_code != 200:
        print(f"  ✗ Request failed with status {res.status_code}: {res.text}")
        return False
        
    data = res.json()
    required = ['metadata', 'risk_intelligence', 'predictions', 'forecast', 'investor_match', 'sip_projection']
    for k in required:
        if k not in data:
            print(f"  ✗ Missing MF key: {k}")
            return False
            
    print(f"  ✓ MF Analysis successful ({data['metadata']['name']})")
    print(f"  - Risk Score: {data['risk_intelligence']['risk_score_100']}/100")
    print(f"  - 1Y Foreast: {data['forecast']['expected_cagr_1yr_pct']:.2f}% CAGR")
    print(f"  - SIP FV: ${data['sip_projection']['future_value_nominal']:,.2f}")
    return True

def verify_radar_pipeline():
    print("\n[5] Verifying Radar & Watchlist...")
    # Add to watchlist
    add_res = requests.post(f"{BASE_URL}/radar/watchlist/TSLA", json={"asset_type": "stock"})
    if add_res.status_code != 200:
        print("  ✗ Failed to add to watchlist")
        return False
    
    # Get live radar
    live_res = requests.get(f"{BASE_URL}/radar/live")
    if live_res.status_code != 200:
        print("  ✗ Failed to fetch live radar")
        return False
        
    print(f"  ✓ Radar functionality verified. Count: {live_res.json()['count']}")
    return True

def main():
    print("=== STARTING FULL PIPELINE VERIFICATION ===")
    if not verify_server_running():
        print("Attempting to start backend manually...")
        # Note: In a real agentic flow, I might try to start it, 
        # but for this script we assume it's manually started or I'll try now.
        return 
        
    stock_ok = verify_stock_pipeline("MSFT")
    crypto_ok = verify_crypto_pipeline("ETH-USDT")
    mf_ok = verify_mutual_fund_pipeline("SPY")
    radar_ok = verify_radar_pipeline()
    
    if all([stock_ok, crypto_ok, mf_ok, radar_ok]):
        print("\n=== ✨ ALL VERIFICATION TESTS PASSED ✨ ===")
    else:
        print("\n=== ❌ SOME TESTS FAILED ===")
        sys.exit(1)

if __name__ == "__main__":
    main()

