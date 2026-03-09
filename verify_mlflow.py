import pandas as pd
import numpy as np
from app.models.train_xgb import XGBModelTrainer
from app.features.indicators import FeatureEngineer
from app.agents.data_agent import DataAgent
import logging
import os

logging.basicConfig(level=logging.INFO)

def test_mlflow_integration():
    data_agent = DataAgent()
    fe = FeatureEngineer()
    
    print("Fetching data for training test (AAPL)...")
    # Small period for fast test
    df = data_agent.fetch_stock_data("AAPL", period="1mo")
    df = fe.add_technical_indicators(df)
    
    trainer = XGBModelTrainer(model_path="app/models/xgboost_test_model.pkl")
    print("Starting training with MLflow tracking...")
    trainer.train(df)
    print("Training complete.")
    
    if os.path.exists("mlruns"):
        print("SUCCESS: 'mlruns' directory created.")
    else:
        print("FAILURE: 'mlruns' directory NOT found.")

if __name__ == "__main__":
    test_mlflow_integration()
