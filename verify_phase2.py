from app.agents.data_agent import DataAgent
from app.features.indicators import FeatureEngineer
from app.patterns.candle_patterns import CandlePatternEngine
from app.patterns.chart_patterns import ChartPatternEngine
from app.agents.regime_agent import RegimeAgent
from app.agents.strategy_agent import StrategyAgent
from app.sentiment.news_scraper import SentimentEngine
from app.models.train_xgb import XGBModelTrainer
from app.models.train_lstm import LSTMModelTrainer
from app.models.ensemble import EnsembleModel
from app.agents.debate_agent import DebateAgent
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO)

def test_phase2():
    print("--- Testing Phase 2 Components ---")
    
    # Init
    data_agent = DataAgent()
    feature_engineer = FeatureEngineer()
    candle_engine = CandlePatternEngine()
    chart_engine = ChartPatternEngine()
    regime_agent = RegimeAgent()
    strategy_agent = StrategyAgent()
    sentiment_engine = SentimentEngine()
    debate_agent = DebateAgent()
    
    # Fetch Data
    print("\n[0] Fetching initial data for modeling (AAPL)...")
    # Need enough data for LSTM (sequence_length=60) + features + train split
    df = data_agent.fetch_stock_data("AAPL", interval="1d", period="2y")
    
    if df.empty:
        print("Failed to fetch data. Verification aborted.")
        return
        
    df = feature_engineer.add_technical_indicators(df)
    df = candle_engine.add_patterns(df)
    df = chart_engine.add_patterns(df)
    
    # 1. Test Regime and Strategy
    print("\n[1] Testing Regime and Strategy Selection...")
    regime = regime_agent.analyze(df)
    strategy = strategy_agent.select_strategy(regime)
    print(f"Detected Regime: {regime}")
    print(f"Selected Strategy: {strategy}")
    
    # 2. Test Sentiment
    print("\n[2] Testing Sentiment Engine...")
    sentiment_data = sentiment_engine.analyze_sentiment("AAPL")
    headlines_count = sentiment_data.get('headlines_analyzed', 0)
    print(f"Sentiment Score: {sentiment_data['score']} (Based on {headlines_count} headlines)")
    
    # 3. Train Models
    print("\n[3] Training ML Models...")
    xgb_trainer = XGBModelTrainer()
    xgb_trainer.train(df)
    
    lstm_trainer = LSTMModelTrainer(sequence_length=60)
    lstm_trainer.train(df, epochs=5, batch_size=32)
    
    # 4. Test Ensemble Prediction
    print("\n[4] Testing Ensemble Prediction...")
    # Instantiate AFTER training so it loads the saved models (or uses the instances if we pass them)
    # Actually, EnsembleModel instantiates new trainers inside, which loads the saved .pkl / .h5
    ensemble = EnsembleModel()
    
    # Predict on the latest data
    preds = ensemble.predict(df, regime)
    print(f"Ensemble Probabilities: Bull {preds['bull_prob']:.2f}, Bear {preds['bear_prob']:.2f}")
    
    # 5. Test Debate Engine
    print("\n[5] Testing Debate (Final Decision)...")
    decision = debate_agent.debate(preds['bull_prob'], preds['bear_prob'], sentiment_data['score'])
    print(f"Final Decision: {decision['decision']} (Confidence: {decision['confidence']:.2f})")
    
    print("\n--- Phase 2 Verification Complete ---")

if __name__ == "__main__":
    test_phase2()
