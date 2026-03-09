from app.agents.data_agent import DataAgent
from app.features.indicators import FeatureEngineer
from app.agents.risk_agent import RiskGuardian
from app.backtesting.engine import BacktestEngine
import logging
import pandas as pd

logging.basicConfig(level=logging.INFO)

def test_phase3():
    print("--- Testing Phase 3 Components ---")
    
    # Init
    data_agent = DataAgent()
    feature_engineer = FeatureEngineer()
    risk_guardian = RiskGuardian(max_risk_per_trade_pct=0.02)
    backtest_engine = BacktestEngine(initial_capital=10000.0)
    
    # 1. Test Risk Guardian Logic
    print("\n[1] Testing Risk Guardian isolated...")
    decision_buy = {"decision": "BUY", "confidence": 0.8}
    current_price = 150.0
    atr = 3.5
    capital = 10000.0
    
    risk_res = risk_guardian.assess_trade(decision_buy, current_price, atr, capital)
    print(f"Risk Assessment for BUY @ 150, ATR 3.5:")
    for k, v in risk_res.items():
        print(f"  {k}: {v}")
        
    # Verify math: SL should be 150 - (3.5 * 2) = 143.0
    # Risk USD should be 10000 * 0.02 = 200.0
    # Pos Size Units should be 200 / 7 = 28.57
    assert risk_res['stop_loss'] == 143.0
    assert risk_res['risk_amount_usd'] == 200.0
    assert round(risk_res['position_size_units'], 2) == 28.57
    print("✓ Risk math verified.")

    # 2. Test Backtesting Engine
    print("\n[2] Testing Backtest Engine...")
    # Fetch a small dataset
    df = data_agent.fetch_stock_data("AAPL", interval="1d", period="3mo")
    df = feature_engineer.add_technical_indicators(df)
    
    if df.empty or len(df) < 50:
         print("Not enough data for backtest simulation.")
         return
         
    # Mock some decisions and risks for the backtest
    decisions = []
    risks = []
    
    # Create an alternating buy/sell pattern for testing
    for i in range(len(df)):
        price = df['close'].iloc[i]
        atr_val = df['atr'].iloc[i] if not pd.isna(df['atr'].iloc[i]) else 1.0
        
        # Every 10 days, generate a BUY or SELL
        if i % 20 == 0:
            d = {"decision": "BUY", "confidence": 0.7}
        elif i % 10 == 0:
            d = {"decision": "SELL", "confidence": 0.7}
        else:
            d = {"decision": "HOLD", "confidence": 0.0}
            
        decisions.append(d)
        risks.append(risk_guardian.assess_trade(d, price, atr_val, backtest_engine.capital))
        
    report = backtest_engine.run(df, decisions, risks)
    print("\nBacktest Report:")
    for k, v in report.items():
        print(f"  {k}: {v}")
        
    if report['total_trades'] > 0:
        print("✓ Backtest engine executed trades successfully.")

    print("\n--- Phase 3 Verification Complete ---")

if __name__ == "__main__":
    test_phase3()
