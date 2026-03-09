import pandas as pd
import numpy as np
import xgboost as xgb
import logging
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import joblib
import os

logger = logging.getLogger(__name__)

class XGBoostRunner:
    """
    Handles training and inference for the XGBoost ensemble component.
    """
    def __init__(self, model_path: str = "app/models/saved_models/xgboost_v1.pkl"):
        self.model_path = model_path
        self.model = None
        self._ensure_dir()

    def _ensure_dir(self):
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)

    def load_model(self):
        if os.path.exists(self.model_path):
            try:
                self.model = joblib.load(self.model_path)
                logger.info(f"[XGBoost] Model loaded from {self.model_path}")
                return True
            except Exception as e:
                logger.error(f"[XGBoost] Failed to load model: {e}")
        return False

    def train(self, df: pd.DataFrame, target_col: str = "target"):
        """
        Train XGBoost model on structured features.
        target_col should be 1 if next candle goes up, 0 otherwise.
        """
        if df.empty or target_col not in df.columns:
            logger.error("[XGBoost] Invalid training data.")
            return

        # Prepare features (exclude timestamp, raw prices except if standardized, and target)
        exclude_cols = ['timestamp', 'open', 'high', 'low', 'close', 'volume', target_col, 'target_regime', 'symbol', 'date']
        feature_cols = [c for c in df.columns if c not in exclude_cols and pd.api.types.is_numeric_dtype(df[c])]
        
        # Drop rows with NaN in features
        df_clean = df.dropna(subset=feature_cols + [target_col]).copy()
        
        if len(df_clean) < 100:
            logger.warning("[XGBoost] Not enough rows after dropping NaNs to train robustly.")
            return

        X = df_clean[feature_cols]
        y = df_clean[target_col]

        # Time-series split (no shuffle)
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)

        logger.info(f"[XGBoost] Training on {len(X_train)} samples, testing on {len(X_test)} samples...")
        
        # XGBoost Classifier
        self.model = xgb.XGBClassifier(
            n_estimators=100,
            learning_rate=0.05,
            max_depth=5,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            eval_metric='logloss'
        )
        
        self.model.fit(X_train, y_train)
        
        # Evaluate
        preds = self.model.predict(X_test)
        acc = accuracy_score(y_test, preds)
        logger.info(f"[XGBoost] Training complete. Test Accuracy: {acc:.4f}")
        logger.info(f"\n{classification_report(y_test, preds)}")

        # Save model
        joblib.dump(self.model, self.model_path)
        logger.info(f"[XGBoost] Model saved to {self.model_path}")
        
    def predict(self, df: pd.DataFrame) -> dict:
        """
        Returns prediction probabilities for the LAST row in the dataframe.
        """
        if self.model is None:
            if not self.load_model():
                logger.warning("[XGBoost] Model not loaded, returning default.")
                return {'bull_prob': 0.5, 'bear_prob': 0.5}

        # Select matching feature cols
        feature_cols = [c for c in self.model.feature_names_in_ if c in df.columns]
        
        if len(feature_cols) != len(self.model.feature_names_in_):
            logger.warning("[XGBoost] Feature mismatch between df and model.")
        
        # Fill missing features with 0 just for inference
        X = df[feature_cols].copy()
        X = X.fillna(0)
        
        # Predict on last row
        last_row = X.iloc[[-1]]
        probas = self.model.predict_proba(last_row)[0]
        
        # Assumes binary classification where class 1 is Bullish
        return {
            'bull_prob': float(probas[1]),
            'bear_prob': float(probas[0])
        }

if __name__ == "__main__":
    # Test stub
    runner = XGBoostRunner(model_path="app/models/saved_models/test_xgb.pkl")
    print("XGBoost initialized.")
