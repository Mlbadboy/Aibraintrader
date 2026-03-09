import logging
from app.models.train_xgb import XGBModelTrainer
from app.models.train_lstm import LSTMModelTrainer
import pandas as pd

logger = logging.getLogger(__name__)

class EnsembleModel:
    """
    Combines predictions from multiple trained models.
    """
    
    def __init__(self):
        # We try to load models upon initialization
        self.xgb_model = XGBModelTrainer()
        self.lstm_model = LSTMModelTrainer()
        
    def predict(self, df, regime: str) -> dict:
        """
        Returns combined bull/bear probabilities.
        """
        if df.empty:
            return {"bull_prob": 0.5, "bear_prob": 0.5}
            
        xgb_preds = self.xgb_model.predict(df)
        lstm_preds = self.lstm_model.predict(df)
        
        # Adaptive Weighting based on Regime (Simplified example)
        # Assuming XGBoost handles trends well, LSTM handles sequences/momentum well
        if "trending" in regime:
            w_xgb, w_lstm = 0.6, 0.4
        elif "ranging" in regime:
            w_xgb, w_lstm = 0.4, 0.6
        else:
             w_xgb, w_lstm = 0.5, 0.5
             
        final_bull = (w_xgb * xgb_preds['bull_prob']) + (w_lstm * lstm_preds['bull_prob'])
        final_bear = (w_xgb * xgb_preds['bear_prob']) + (w_lstm * lstm_preds['bear_prob'])
        
        # Normalize just in case weights drift
        total = final_bull + final_bear
        if total > 0:
            final_bull /= total
            final_bear /= total
            
        logger.info(f"Ensemble Prediction: Bull ({final_bull:.2f}), Bear ({final_bear:.2f}) [Weights: XGB {w_xgb}, LSTM {w_lstm}]")
        
        return {
            "bull_prob": final_bull,
            "bear_prob": final_bear,
            "xgb_prob": xgb_preds['bull_prob'],
            "lstm_prob": lstm_preds['bull_prob']
        }
