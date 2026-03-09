import pandas as pd
import threading
import logging
from typing import Optional, Dict

logger = logging.getLogger(__name__)

class FeatureStore:
    """
    A local, thread-safe memory store for cached feature DataFrames.
    In a scalable production setup, this would wrap Redis or Cassandra.
    For local development and latency minimization, we use an in-memory dictionary.
    """
    
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        # Singleton pattern across the application
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(FeatureStore, cls).__new__(cls)
                cls._instance._init_cache()
            return cls._instance

    def _init_cache(self):
        self._cache: Dict[str, pd.DataFrame] = {}
        self._cache_lock = threading.Lock()

    def _generate_key(self, symbol: str, timeframe: str) -> str:
        return f"{symbol.upper()}:{timeframe.lower()}"

    def get_features(self, symbol: str, timeframe: str) -> Optional[pd.DataFrame]:
        """Retrieve pre-calculated features for a symbol/timeframe."""
        key = self._generate_key(symbol, timeframe)
        with self._cache_lock:
            if key in self._cache:
                logger.info(f"[FeatureStore] Cache hit for {key}")
                return self._cache[key].copy()
        
        logger.info(f"[FeatureStore] Cache miss for {key}")
        return None

    def store_features(self, symbol: str, timeframe: str, df: pd.DataFrame):
        """Store calculated features."""
        if df is None or df.empty:
            return
            
        key = self._generate_key(symbol, timeframe)
        with self._cache_lock:
            self._cache[key] = df.copy()
            logger.info(f"[FeatureStore] Stored features for {key} ({len(df)} rows)")

    def invalidate(self, symbol: str, timeframe: str):
        """Remove a cached dataframe."""
        key = self._generate_key(symbol, timeframe)
        with self._cache_lock:
            if key in self._cache:
                del self._cache[key]
                logger.info(f"[FeatureStore] Invalidated {key}")
                
    def clear_all(self):
        """Clear the entire feature store."""
        with self._cache_lock:
            self._cache.clear()
            logger.info("[FeatureStore] Cleared entirely.")

# Create a global instance for easy importing
feature_store = FeatureStore()
