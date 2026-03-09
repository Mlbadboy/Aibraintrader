import time
import sys

# Flush everything
def log(msg):
    print(msg, flush=True)

log("Starting Granular Agent Test...")

modules = [
    ("fastapi", "fastapi", None),
    ("DataAgent", "app.agents.data_agent", "DataAgent"),
    ("FailsafeAgent", "app.agents.failsafe_agent", "FailsafeAgent"),
    ("FeatureEngineer", "app.features.indicators", "FeatureEngineer"),
    ("RegimeAgent", "app.agents.regime_agent", "RegimeAgent"),
    ("CandlePatternEngine", "app.patterns.candle_patterns", "CandlePatternEngine"),
    ("ChartPatternEngine", "app.patterns.chart_patterns", "ChartPatternEngine"),
    ("SentimentEngine", "app.sentiment.news_scraper", "SentimentEngine"),
    ("StrategyAgent", "app.agents.strategy_agent", "StrategyAgent"),
    ("EnsembleModel", "app.models.ensemble", "EnsembleModel"),
    ("DebateAgent", "app.agents.debate_agent", "DebateAgent"),
    ("ClassificationAgent", "app.agents.classification_agent", "ClassificationAgent"),
    ("OptionsAgent", "app.agents.options_agent", "OptionsAgent"),
    ("PaperBroker", "app.execution.paper_broker", "PaperBroker")
]

import importlib

for name, mod_path, class_name in modules:
    log(f"Testing {name}...")
    
    log(f"  Importing {mod_path}...")
    start = time.time()
    try:
        mod = importlib.import_module(mod_path)
        log(f"  OK ({time.time() - start:.2f}s)")
        
        if class_name:
            log(f"  Instantiating {class_name}...")
            start = time.time()
            cls = getattr(mod, class_name)
            instance = cls()
            log(f"  OK ({time.time() - start:.2f}s)")
            
    except Exception as e:
        log(f"  FAILED: {e}")

log("All tests completed.")
