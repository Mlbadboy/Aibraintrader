from fastapi import FastAPI, Body
import logging
import pandas as pd
from app.models.xgboost_model import XGBoostModel
from app.models.lstm_model import LSTMModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="ML-Inference-Service")

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "ml-service"}

# Load models on startup
xgb_model = XGBoostModel()
lstm_model = LSTMModel()

@app.post("/predict/ensemble")
def predict_ensemble(data: list = Body(...)):
    """Receives a list of price records and returns ensemble probabilities."""
    df = pd.DataFrame(data)
    if df.empty:
        return {"error": "Empty data received"}
    
    xgb_score = xgb_model.predict(df)
    lstm_score = lstm_model.predict(df)
    
    # Simple ensemble weights (0.6 XGB, 0.4 LSTM)
    prob_bull = (xgb_score * 0.6) + (lstm_score * 0.4)
    prob_bear = 1.0 - prob_bull
    
    return {
        "bull": round(float(prob_bull), 2),
        "bear": round(float(prob_bear), 2),
        "xgb_score": round(float(xgb_score), 2),
        "lstm_score": round(float(lstm_score), 2)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
