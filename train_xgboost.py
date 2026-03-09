import sys
import os
import pandas as pd

# Add root to python path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.data_pipeline.orchestrator import DataOrchestrator
from app.features.indicators import FeatureEngineer
from app.models.xgboost_runner import XGBoostRunner

def create_initial_model():
    print("Initializing components...")
    orchestrator = DataOrchestrator()
    fe = FeatureEngineer()
    
    # 1. Fetch extensive history for a robust baseline model
    print("Fetching training data (SPY, QQQ, AAPL, MSFT) for the ensemble prototype...")
    dfs = []
    symbols = ["SPY", "QQQ", "AAPL", "MSFT"]
    
    for symbol in symbols:
        df = orchestrator.fetch_ohlcv(symbol, asset_type="stock", interval="1d", limit=2500)
        if not df.empty:
            df['symbol'] = symbol
            dfs.append(df)
            print(f"Loaded {len(df)} days for {symbol}")
            
    if not dfs:
        print("Failed to pull any training data. Exiting.")
        return
        
    master_df = pd.concat(dfs, ignore_index=True)
    
    # 2. Engineer features
    print("Engineering features...")
    # apply features per symbol to avoid bleed
    engineered_dfs = []
    for symbol in symbols:
        sub_df = master_df[master_df['symbol'] == symbol].copy()
        sub_df = fe.add_technical_indicators(sub_df)
        
        # Create Target (1 if next day goes up, else 0)
        sub_df['target'] = (sub_df['close'].shift(-1) > sub_df['close']).astype(int)
        
        # Drop the last row since its target is NaN
        sub_df.dropna(subset=['target'], inplace=True)
        engineered_dfs.append(sub_df)
        
    final_train_df = pd.concat(engineered_dfs, ignore_index=True)
    
    # 3. Train
    print("Training XGBoost Prototype...")
    runner = XGBoostRunner(model_path="app/models/saved_models/xgboost_baseline.pkl")
    runner.train(final_train_df, target_col="target")
    print("Done! Model exported.")

if __name__ == "__main__":
    create_initial_model()
