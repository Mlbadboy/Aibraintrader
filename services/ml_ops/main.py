from fastapi import FastAPI, BackgroundTasks
import logging
import pandas as pd
from sqlalchemy import create_engine, text
import os
from datetime import datetime, timedelta
from app.models.train_xgb import XGBModelTrainer
from app.models.train_lstm import LSTMModelTrainer
from app.agents.data_agent import DataAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="ML-Ops-Service")

DB_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgress_secure_pwd@postgres:5432/trading_db")
engine = create_engine(DB_URL)

data_agent = DataAgent()
xgb_trainer = XGBModelTrainer()
lstm_trainer = LSTMModelTrainer()

@app.get("/health")
def health():
    return {"status": "healthy", "service": "ml_ops"}

@app.post("/monitor/drift")
def monitor_drift(background_tasks: BackgroundTasks):
    """
    Checks for model drift by comparing predictions to actual price movement.
    """
    background_tasks.add_task(perform_drift_analysis)
    return {"status": "Drift analysis started in background"}

def perform_drift_analysis():
    logger.info("Starting Drift Analysis...")
    try:
        # 1. Fetch recent predictions from Postgres
        query = """
            SELECT p.symbol, p.decision, p.created_at, p.entry_price
            FROM predictions p
            WHERE p.created_at > NOW() - INTERVAL '7 days'
            AND p.decision != 'HOLD'
        """
        with engine.connect() as conn:
            preds_df = pd.read_sql(query, conn)
        
        if preds_df.empty:
            logger.info("No recent predictions to analyze.")
            return

        # 2. Verify outcomes (Simplified: check if price moved in predicted direction)
        total_correct = 0
        total_evaluated = 0
        
        for idx, row in preds_df.iterrows():
            symbol = row['symbol']
            # Fetch actual price data for that time
            df = data_agent.fetch_stock_data(symbol, period="5d")
            if df.empty: continue
            
            current_price = df['close'].iloc[-1]
            entry_price = row['entry_price']
            decision = row['decision']
            
            is_correct = False
            if decision == 'BUY' and current_price > entry_price:
                is_correct = True
            elif decision == 'SELL' and current_price < entry_price:
                is_correct = True
                
            total_correct += 1 if is_correct else 0
            total_evaluated += 1
            
        if total_evaluated > 0:
            accuracy = total_correct / total_evaluated
            logger.info(f"Drift Analysis Result: Accuracy={accuracy:.2f} over {total_evaluated} trades.")
            
            # 3. Trigger retraining if accuracy below 55%
            if accuracy < 0.55:
                logger.warning("Drift detected (Accuracy < 55%). Triggering automated retraining...")
                trigger_retraining()
        
    except Exception as e:
        logger.error(f"Drift analysis failed: {e}")

@app.post("/retrain")
def trigger_retrain_endpoint(background_tasks: BackgroundTasks):
    background_tasks.add_task(trigger_retraining)
    return {"status": "Retraining started in background"}

def trigger_retraining():
    logger.info("Starting Automated Retraining Pipeline...")
    try:
        # For prototype, we retrain on a few key symbols to refresh the models
        test_symbols = ["AAPL", "TSLA", "BTC-USD", "ETH-USD"]
        
        combined_df = pd.DataFrame()
        for sym in test_symbols:
            if "-" in sym:
                df = data_agent.fetch_crypto_data(sym.replace("-", "/"), interval="1h", limit=1000)
            else:
                df = data_agent.fetch_stock_data(sym, interval="1h", period="2y")
            
            if not df.empty:
                # Add indicators for training
                from app.features.indicators import FeatureEngineer
                fe = FeatureEngineer()
                df = fe.add_technical_indicators(df)
                combined_df = pd.concat([combined_df, df])
        
        if not combined_df.empty:
            logger.info(f"Retraining models on {len(combined_df)} rows of data...")
            xgb_trainer.train(combined_df)
            lstm_trainer.train(combined_df)
            logger.info("Models retrained and registered in MLflow.")
        else:
            logger.error("Retraining failed: No data fetched.")
            
    except Exception as e:
        logger.error(f"Retraining failed: {e}")

# --- Scheduler Integration ---
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()
# Run drift analysis once a day at midnight
scheduler.add_job(perform_drift_analysis, 'cron', hour=0, minute=0)
# Run weekly retraining on Sundays
scheduler.add_job(trigger_retraining, 'cron', day_of_week='sun', hour=2, minute=0)

@app.on_event("startup")
def startup_event():
    scheduler.start()
    logger.info("ML Ops Scheduler Started.")

@app.on_event("shutdown")
def shutdown_event():
    scheduler.stop()
    logger.info("ML Ops Scheduler Stopped.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006)
