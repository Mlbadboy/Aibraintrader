import pandas as pd
import numpy as np
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import joblib
import os
import logging

logger = logging.getLogger(__name__)

class XGBModelTrainer:
    """
    Trains and predictions an XGBoost model for directional price movement.
    """
    
    def __init__(self, model_path="app/models/xgboost_model.pkl"):
        self.model_path = model_path
        self.model = None
        self.feature_columns = ['rsi', 'macd', 'macd_signal', 'ema_9', 'ema_21', 'ema_50', 'ema_200', 'atr', 'bb_high', 'bb_low', 'vwap']
        
        # Load model if exists
        self.load_model()

    def _prepare_data(self, df: pd.DataFrame):
        """
        Creates target variable and shifts features for prediction.
        Target: 1 if next candle close is higher, 0 otherwise.
        """
        if df.empty or len(df) < 50:
            return None, None
            
        data = df.copy()
        
        # Target: Next close > Current close
        data['target'] = (data['close'].shift(-1) > data['close']).astype(int)
        
        # Drop the last row as it doesn't have a future target
        data = data.dropna(subset=self.feature_columns + ['target'])
        
        X = data[self.feature_columns]
        y = data['target']
        
        return X, y

    def train(self, df: pd.DataFrame):
        """
        Trains the XGBoost model with MLflow tracking.
        """
        import mlflow
        import mlflow.xgboost

        # Set tracking URI if environment variable is set
        tracking_uri = os.getenv("MLFLOW_TRACKING_URI")
        if tracking_uri:
            mlflow.set_tracking_uri(tracking_uri)
        
        mlflow.set_experiment("XGBoost_Price_Prediction")

        logger.info("Preparing data for XGBoost training...")
        X, y = self._prepare_data(df)
        
        if X is None or len(X) < 100:
            logger.warning("Insufficient data for training. Need at least 100 rows.")
            return

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        with mlflow.start_run():
            logger.info("Training XGBClassifier...")
            params = {
                "n_estimators": 100,
                "max_depth": 6,
                "learning_rate": 0.3,
                "use_label_encoder": False,
                "eval_metric": 'logloss'
            }
            mlflow.log_params(params)
            
            self.model = XGBClassifier(**params)
            self.model.fit(X_train, y_train)
            
            y_pred = self.model.predict(X_test)
            acc = accuracy_score(y_test, y_pred)
            mlflow.log_metric("accuracy", acc)
            
            logger.info(f"Model trained. Test Accuracy: {acc:.2f}")
            
            # Log model to MLflow
            mlflow.xgboost.log_model(self.model, "model", registered_model_name="XGBoost_Price_Model")
            
            # Save Local Model for simple inference service
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            joblib.dump(self.model, self.model_path)
            logger.info(f"Model saved locally to {self.model_path}")

    def load_model(self):
        """
        Loads a pre-trained model.
        """
        if os.path.exists(self.model_path):
            self.model = joblib.load(self.model_path)
            logger.info("XGBoost model loaded successfully.")

    def predict(self, df: pd.DataFrame) -> dict:
        """
        Predicts the direction of the next candle based on the last row's features.
        Returns bull and bear probabilities.
        """
        if self.model is None:
            logger.warning("No model trained or loaded. Defaulting to 0.5 probabilities.")
            return {"bull_prob": 0.5, "bear_prob": 0.5}
            
        try:
            # Need to ensure all features exist. If they have NaNs, prediction fails.
            # Using the last non-NaN row for prediction.
            latest_features = df[self.feature_columns].dropna().iloc[[-1]] 
            
            if latest_features.empty:
                return {"bull_prob": 0.5, "bear_prob": 0.5}
                
            probs = self.model.predict_proba(latest_features)[0]
            # probs[0] is probability of class 0 (Bearish), probs[1] is class 1 (Bullish)
            
            return {
                "bull_prob": float(probs[1]),
                "bear_prob": float(probs[0])
            }
        except Exception as e:
            logger.error(f"XGB Prediction error: {e}")
            return {"bull_prob": 0.5, "bear_prob": 0.5}

if __name__ == "__main__":
    # Test script will only work if indicators are calculated
    print("Run verify_phase2.py to test the model pipeline.")
