import time
import logging

logging.basicConfig(level=logging.INFO)

from app.agents.data_agent import DataAgent
from app.agents.failsafe_agent import FailsafeAgent
from app.features.indicators import FeatureEngineer
from app.agents.regime_agent import RegimeAgent
from app.patterns.candle_patterns import CandlePatternEngine
from app.patterns.chart_patterns import ChartPatternEngine
from app.sentiment.news_scraper import SentimentEngine
from app.agents.strategy_agent import StrategyAgent
from app.models.ensemble import EnsembleModel
from app.agents.debate_agent import DebateAgent
from app.agents.risk_agent import RiskGuardian
from app.agents.classification_agent import ClassificationAgent
from app.agents.options_agent import OptionsAgent
from app.execution.paper_broker import PaperBroker

agents = [
    ("DataAgent", DataAgent),
    ("FailsafeAgent", FailsafeAgent),
    ("FeatureEngineer", FeatureEngineer),
    ("RegimeAgent", RegimeAgent),
    ("CandlePatternEngine", CandlePatternEngine),
    ("ChartPatternEngine", ChartPatternEngine),
    ("SentimentEngine", SentimentEngine),
    ("StrategyAgent", StrategyAgent),
    ("EnsembleModel", EnsembleModel),
    ("DebateAgent", DebateAgent),
    ("ClassificationAgent", ClassificationAgent),
    ("OptionsAgent", OptionsAgent),
    ("RiskGuardian", lambda: RiskGuardian(max_risk_per_trade_pct=0.02)),
    ("PaperBroker", PaperBroker)
]

print("Starting agent instantiation test...")
for name, cls in agents:
    print(f"Instantiating {name}...", end=" ", flush=True)
    start = time.time()
    try:
        instance = cls()
        print(f"OK ({time.time() - start:.2f}s)")
    except Exception as e:
        print(f"FAILED: {e}")

print("All agents instantiated successfully.")
