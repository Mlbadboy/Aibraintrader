import pandas as pd
import ta
import logging

logger = logging.getLogger(__name__)

class RegimeAgent:
    """
    Agent responsible for classifying the current market regime.
    Regimes: trending, ranging, high_volatility, low_volatility
    """
    
    def __init__(self, adx_threshold=25, volatility_threshold_pct=0.01):
        self.adx_threshold = adx_threshold
        self.vol_threshold = volatility_threshold_pct
        
    def analyze(self, df: pd.DataFrame) -> str:
        """
        Analyzes the dataframe to determine the market regime of the most recent data point.
        Assumes features like ATR and basic OHLCV are present or can be calculated.
        """
        if df.empty or len(df) < 14:
            return "unknown"
            
        try:
            # Need ADX for trend strength
            adx = ta.trend.ADXIndicator(df['high'], df['low'], df['close'], window=14).adx().iloc[-1]
            
            # Need ATR for volatility
            atr = ta.volatility.AverageTrueRange(df['high'], df['low'], df['close'], window=14).average_true_range().iloc[-1]
            current_price = df['close'].iloc[-1]
            
            # Calculate volatility as a percentage of price
            volatility_pct = atr / current_price if current_price > 0 else 0
            
            if pd.isna(adx) or pd.isna(atr):
                return "unknown"
                
            if adx > self.adx_threshold:
                # Trending market
                if volatility_pct > self.vol_threshold * 2:
                    return "trending_volatile"
                return "trending"
            else:
                # Ranging market
                if volatility_pct < self.vol_threshold:
                    return "low_volatility_ranging"
                elif volatility_pct > self.vol_threshold * 2:
                    return "high_volatility_ranging"
                return "ranging"
                
        except Exception as e:
            logger.error(f"Error determining market regime: {e}")
            return "unknown"

if __name__ == "__main__":
    # Simple test
    import numpy as np
    data = {"high": np.random.randn(50) + 100, "low": np.random.randn(50) + 98, "close": np.random.randn(50) + 99}
    df = pd.DataFrame(data)
    agent = RegimeAgent()
    print(f"Regime: {agent.analyze(df)}")
