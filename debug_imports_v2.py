import time
import sys
import logging
logging.basicConfig(level=logging.INFO)

modules = [
    ('fastapi', 'from fastapi import FastAPI'),
    ('DataAgent', 'from app.agents.data_agent import DataAgent'),
    ('XGBTrainer', 'from app.models.train_xgb import XGBModelTrainer'),
    ('LSTMTrainer', 'from app.models.train_lstm import LSTMModelTrainer'),
    ('EnsembleModel', 'from app.models.ensemble import EnsembleModel'),
    ('SentimentEngine', 'from app.sentiment.news_scraper import SentimentEngine'),
    ('OptionsAgent', 'from app.agents.options_agent import OptionsAgent'),
    ('RadarScheduler', 'from app.radar.scheduler import RadarScheduler')
]

for name, cmd in modules:
    print(f'Importing {name}...', end='', flush=True)
    start = time.time()
    try:
        exec(cmd)
        print(f' OK ({time.time()-start:.2f}s)')
    except Exception as e:
        print(f' FAIL: {e}')
