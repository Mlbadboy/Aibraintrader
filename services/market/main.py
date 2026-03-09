from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
import logging
from app.agents.data_agent import DataAgent
from app.agents.mf_data_agent import MFDataAgent
import asyncio
import json
import random

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Market-Service")

data_agent = DataAgent()
mf_data_agent = MFDataAgent()

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/market/stock/{symbol}")
def get_stock_data(symbol: str, interval: str = "1h", period: str = "1mo"):
    df = data_agent.fetch_data(symbol, interval, period)
    if df.empty:
        raise HTTPException(status_code=404, detail="Stock data not found")
    return df.to_dict(orient="records")

@app.websocket("/ws/market/{symbol}")
async def websocket_endpoint(websocket: WebSocket, symbol: str):
    await websocket.accept()
    logger.info(f"WebSocket connection established for {symbol}")
    try:
        # Simulate live ticks for prototype (In prod, connect to a real-time feed)
        last_price = 150.0 # Default starting point if fetch fails
        df = data_agent.fetch_data(symbol, interval="1m", period="1d")
        if not df.empty:
            last_price = float(df['close'].iloc[-1])

        while True:
            # Generate a small random walk to simulate reality
            change = random.uniform(-0.1, 0.1)
            last_price += change
            
            payload = {
                "symbol": symbol,
                "price": round(last_price, 2),
                "timestamp": datetime.utcnow().isoformat(),
                "volume": random.randint(100, 1000)
            }
            await websocket.send_text(json.dumps(payload))
            await asyncio.sleep(1) # 1 second ticks
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for {symbol}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")

from datetime import datetime

@app.get("/market/mutualfund/{symbol}")
def get_mf_data(symbol: str, period: str = "5y"):
    df = mf_data_agent.fetch_nav_history(symbol, period)
    if df.empty:
        raise HTTPException(status_code=404, detail="Mutual Fund data not found")
    meta = mf_data_agent.fetch_fund_metadata(symbol)
    return {
        "metadata": meta,
        "history": df.to_dict(orient="records")
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
