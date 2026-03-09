import pandas as pd
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import LSTM, Dense, Dropout
from sklearn.preprocessing import MinMaxScaler
import os
import logging

logger = logging.getLogger(__name__)

class LSTMModelTrainer:
    """
    Trains and predicts using an LSTM neural network for directional movement.
    """
    
    def __init__(self, sequence_length=60, model_path="app/models/lstm_model.h5"):
        self.sequence_length = sequence_length
        self.model_path = model_path
        self.model = None
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        # Keep features simple for LSTM initial implementation
        self.feature_columns = ['close', 'volume', 'rsi', 'macd'] 
        
        self.load_model()

    def _prepare_data(self, df: pd.DataFrame):
        data = df.copy().dropna(subset=self.feature_columns)
        if len(data) < self.sequence_length * 2:
            return None, None, None
            
        # Target: 1 if next day's close > current close
        target = (data['close'].shift(-1) > data['close']).astype(int).values[:-1]
        
        # Scale features
        scaled_features = self.scaler.fit_transform(data[self.feature_columns].values[:-1])
        
        X, y = [], []
        for i in range(self.sequence_length, len(scaled_features)):
            X.append(scaled_features[i-self.sequence_length:i])
            y.append(target[i])
            
        X, y = np.array(X), np.array(y)
        return X, y, data

    def train(self, df: pd.DataFrame, epochs=10, batch_size=32):
        """
        Trains the LSTM model with MLflow tracking.
        """
        import mlflow
        import mlflow.tensorflow

        # Set tracking URI if environment variable is set
        tracking_uri = os.getenv("MLFLOW_TRACKING_URI")
        if tracking_uri:
            mlflow.set_tracking_uri(tracking_uri)
            
        mlflow.set_experiment("LSTM_Sequential_Prediction")

        logger.info("Preparing data for LSTM training...")
        X, y, data = self._prepare_data(df)
        
        if X is None or len(X) < 100:
             logger.warning(f"Insufficient data for LSTM training. Need > {self.sequence_length * 2} rows.")
             return

        # Train/Test split (time series aware)
        split = int(len(X) * 0.8)
        X_train, X_test = X[:split], X[split:]
        y_train, y_test = y[:split], y[split:]
        
        with mlflow.start_run():
            logger.info("Building LSTM model...")
            self.model = Sequential([
                LSTM(units=50, return_sequences=True, input_shape=(X_train.shape[1], X_train.shape[2])),
                Dropout(0.2),
                LSTM(units=50, return_sequences=False),
                Dropout(0.2),
                Dense(units=25),
                Dense(units=1, activation='sigmoid') 
            ])
            
            self.model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
            
            mlflow.log_params({
                "epochs": epochs,
                "batch_size": batch_size,
                "sequence_length": self.sequence_length,
                "units": 50,
                "dropout": 0.2
            })

            logger.info("Training LSTM model...")
            history = self.model.fit(
                X_train, y_train, 
                epochs=epochs, 
                batch_size=batch_size, 
                validation_data=(X_test, y_test), 
                verbose=0
            )
            
            # Log metrics
            avg_acc = np.mean(history.history['accuracy'])
            mlflow.log_metric("avg_accuracy", avg_acc)
            
            # Save Model to MLflow
            mlflow.tensorflow.log_model(self.model, "model", registered_model_name="LSTM_Sequential_Model")
            
            # Save Local Model
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            self.model.save(self.model_path)
            logger.info(f"LSTM model saved locally to {self.model_path}")

    def load_model(self):
        if os.path.exists(self.model_path):
            self.model = load_model(self.model_path)
            logger.info("LSTM model loaded successfully.")

    def predict(self, df: pd.DataFrame) -> dict:
        """
        Returns probability of next close being higher.
        """
        if self.model is None:
            return {"bull_prob": 0.5, "bear_prob": 0.5}
            
        data = df.copy().dropna(subset=self.feature_columns)
        if len(data) < self.sequence_length:
             return {"bull_prob": 0.5, "bear_prob": 0.5}
             
        # Need to fit scaler on history before transforming the last window.
        # In a robust production system, the scaler params should be saved alongside the model.
        # For this prototype, we re-fit on the provided history.
        scaled_features = self.scaler.fit_transform(data[self.feature_columns].values)
        
        # Get the last sequence
        last_sequence = scaled_features[-self.sequence_length:]
        X = last_sequence.reshape(1, self.sequence_length, len(self.feature_columns))
        
        bull_prob = float(self.model.predict(X, verbose=0)[0][0])
        bear_prob = 1.0 - bull_prob
        
        return {
            "bull_prob": bull_prob,
            "bear_prob": bear_prob
        }
