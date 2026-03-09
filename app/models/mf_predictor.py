import pandas as pd
import numpy as np
import xgboost as xgb
import logging

logger = logging.getLogger(__name__)

class MFPredictor:
    """
    Simulates a trained XGBoost probability engine. 
    Predicts the likelihood of positive returns and beating the benchmark.
    Includes Explainable AI (Top Factors).
    """
    
    def __init__(self):
        # In a full prod system, we load a pre-trained .bin model.
        # For phase 7 deployment simulation, we are instantiating dynamic heuristics 
        # backed by the feature set if the model file is not present, simulating XGB outputs.
        pass
        
    def _create_features(self, df: pd.DataFrame) -> dict:
        """Extract current snapshot features for the model."""
        features = {}
        features['momentum_3m'] = df['nav'].pct_change(periods=63).iloc[-1]
        features['momentum_6m'] = df['nav'].pct_change(periods=126).iloc[-1]
        features['momentum_1y'] = df['nav'].pct_change(periods=252).iloc[-1]
        features['volatility_3m'] = df['nav'].pct_change().tail(63).std() * np.sqrt(252)
        features['distance_from_ath'] = (df['nav'].iloc[-1] / df['nav'].max()) - 1
        return features

    def predict_probabilities(self, df: pd.DataFrame, risk_metrics: dict) -> dict:
        """
        Returns probabilities and top influencing factors (Explainable AI).
        """
        if df.empty or len(df) < 252:
            return {"error": "Insufficient data"}
            
        features = self._create_features(df)
        
        # --- Simulated XGBoost Probability Logic ---
        # Highly influenced by momentum and contained volatility.
        base_positive_prob = 0.55 # Market generally goes up
        
        # Adjust based on momentum
        if features['momentum_6m'] > 0:
            base_positive_prob += 0.15 * min(features['momentum_6m'] / 0.1, 1.0)
        else:
            base_positive_prob -= 0.10
            
        # Adjust based on volatility
        if risk_metrics.get('annual_volatility_pct', 20) < 15:
            base_positive_prob += 0.10 # Lower risk funds have higher absolute probability of positive return (though maybe lower magnitude)
            
        prob_positive = max(min(base_positive_prob, 0.95), 0.10)
        
        # Benchmark logic (Simplified alpha proxy)
        prob_beat_bench = 0.50
        if risk_metrics.get('sharpe_ratio', 0) > 1.0:
            prob_beat_bench += 0.20
            
        prob_beat_bench = max(min(prob_beat_bench, 0.85), 0.15)
        
        # --- Explainable AI Layer ---
        factors = []
        if features['momentum_6m'] > 0:
             factors.append({"factor": "6-Month Momentum", "impact": "Positive", "icon": "trending-up"})
        else:
             factors.append({"factor": "6-Month Momentum", "impact": "Negative", "icon": "trending-down"})
             
        if risk_metrics.get('annual_volatility_pct', 20) < 18:
             factors.append({"factor": "Risk / Volatility", "impact": "Positive (Low Risk)", "icon": "shield-check"})
        else:
             factors.append({"factor": "Risk / Volatility", "impact": "Negative (High Risk)", "icon": "alert-triangle"})
             
        if risk_metrics.get('sharpe_ratio', 0) > 1.0:
             factors.append({"factor": "Risk-Adjusted Return (Sharpe)", "impact": "Positive", "icon": "award"})

        return {
            "prob_positive_1y": round(prob_positive * 100, 1),
            "prob_beat_benchmark": round(prob_beat_bench * 100, 1),
            "downside_risk_prob": round((1 - prob_positive) * 100, 1),
            "explainability": factors
        }

if __name__ == "__main__":
    from app.agents.mf_data_agent import MFDataAgent
    from app.features.mf_indicators import MFRiskEngine
    d_agent = MFDataAgent()
    df = d_agent.fetch_nav_history("SPY", "3y")
    r_engine = MFRiskEngine()
    risk = r_engine.analyze_risk(df)
    
    predictor = MFPredictor()
    res = predictor.predict_probabilities(df, risk)
    print(res)
