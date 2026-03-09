import time
import sys

modules = [
    ('fastapi', 'from fastapi import FastAPI'),
    ('DataAgent', 'from app.agents.data_agent import DataAgent'),
    ('EnsembleModel', 'from app.models.ensemble import EnsembleModel'),
    ('SentimentEngine', 'from app.sentiment.news_scraper import SentimentEngine'),
    ('ClassificationAgent', 'from app.agents.classification_agent import ClassificationAgent'),
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
