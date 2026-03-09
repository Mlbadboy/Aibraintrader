import logging
logging.basicConfig(level=logging.INFO)
from app.agents.data_agent import DataAgent
from app.radar.database import RadarDB

agent = DataAgent()
watchlist = RadarDB.get_watchlist()
print('Watchlist:', len(watchlist))
symbols = [item['symbol'] for item in watchlist]
types = [item['asset_type'] for item in watchlist]

try:
    prices = agent.fetch_batch_prices(symbols, types)
    print('Fetched prices:', prices)
except Exception as e:
    print('Error:', e)
