from fastapi import FastAPI, Body
import logging
import pandas as pd
from app.models.mf_forecaster import MFForecaster

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Forecasting-Service")

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "forecast-service"}
forecaster = MFForecaster()

@app.post("/forecast/nav")
def forecast_nav(data: list = Body(...), periods: int = 365):
    """Calculates future NAV projections for a mutual fund."""
    df = pd.DataFrame(data)
    if df.empty:
        return {"error": "Empty data received"}
    
    # Ensure date column is datetime
    df['date'] = pd.to_datetime(df['date'])
    
    result = forecaster.forecast_nav(df, periods_days=periods)
    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
