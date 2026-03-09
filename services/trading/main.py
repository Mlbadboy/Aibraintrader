from fastapi import FastAPI, BackgroundTasks, HTTPException
import logging
import httpx
from app.radar.database import RadarDB
from app.agents.risk_agent import RiskGuardian
import os
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Trading-Service")

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "trading-service"}

radar_db = RadarDB()
risk_guardian = RiskGuardian()

# Service URLs from environment (with docker-compose fallbacks)
ML_SERVICE_URL = os.getenv("ML_SERVICE_URL", "http://ml-service:8003")
MARKET_SERVICE_URL = os.getenv("MARKET_SERVICE_URL", "http://market-service:8002")

class CircuitBreaker:
    def __init__(self, name, failure_threshold=5, recovery_time=30):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_time = recovery_time
        self.failures = 0
        self.last_failure_time = 0
        self.state = "CLOSED" # CLOSED, OPEN, HALF-OPEN

    def record_failure(self):
        self.failures += 1
        self.last_failure_time = time.time()
        if self.failures >= self.failure_threshold:
            self.state = "OPEN"
            logger.error(f"Circuit Breaker [{self.name}] is now OPEN")

    def record_success(self):
        self.failures = 0
        self.state = "CLOSED"

    def can_execute(self):
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_time:
                self.state = "HALF-OPEN"
                return True
            return False
        return True

ml_cb = CircuitBreaker("ML-Service")
market_cb = CircuitBreaker("Market-Service")

@app.post("/trading/execute")
async def execute_trade(symbol: str, asset_type: str):
    """Orchestrates a trade by fetching data -> predicting -> assessing risk."""
    if not market_cb.can_execute() or not ml_cb.can_execute():
        raise HTTPException(status_code=503, detail="Downstream intelligence services are currently unavailable (Circuit Breaker OPEN)")

    async with httpx.AsyncClient() as client:
        try:
            # 1. Fetch data from Market-Service
            market_resp = await client.get(f"{MARKET_SERVICE_URL}/market/{asset_type}/{symbol}", timeout=5.0)
            market_data = market_resp.json()
            market_cb.record_success()
            
            # 2. Get AI Prediction from ML-Service
            ml_data_input = market_data if isinstance(market_data, list) else market_data.get('history', [])
            ml_resp = await client.post(f"{ML_SERVICE_URL}/predict/ensemble", json=ml_data_input, timeout=5.0)
            ml_data = ml_resp.json()
            ml_cb.record_success()
            
            # 3. Assess Risk
            return {
                "symbol": symbol,
                "signal": "BUY" if ml_data.get('bull', 0) > 0.6 else "SELL",
                "confidence": ml_data.get('bull', 0),
                "risk_assessment": "Safe"
            }
        except Exception as e:
            logger.warn(f"Service Call Failed: {e}")
            if "market" in str(e).lower(): market_cb.record_failure()
            if "ml" in str(e).lower(): ml_cb.record_failure()
            raise HTTPException(status_code=500, detail="Internal intelligence failure")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
