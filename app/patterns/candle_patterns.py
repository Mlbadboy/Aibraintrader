import pandas as pd
import logging

logger = logging.getLogger(__name__)

class CandlePatternEngine:
    """
    Engine for detecting basic candlestick patterns.
    """
    
    @staticmethod
    def add_patterns(df: pd.DataFrame) -> pd.DataFrame:
        """
        Adds boolean columns for detected candlestick patterns.
        """
        if df.empty or len(df) < 3:
            return df
            
        try:
            # Body and Shadows
            df['body'] = abs(df['close'] - df['open'])
            df['upper_shadow'] = df['high'] - df[['open', 'close']].max(axis=1)
            df['lower_shadow'] = df[['open', 'close']].min(axis=1) - df['low']
            df['is_bullish'] = df['close'] > df['open']
            df['is_bearish'] = df['close'] < df['open']
            
            # 1. Bullish Engulfing
            df['bullish_engulfing'] = (
                df['is_bullish'] & 
                df['is_bearish'].shift(1) & 
                (df['close'] >= df['open'].shift(1)) & 
                (df['open'] <= df['close'].shift(1)) &
                (df['body'] > df['body'].shift(1))
            )

            # 2. Bearish Engulfing
            df['bearish_engulfing'] = (
                df['is_bearish'] & 
                df['is_bullish'].shift(1) & 
                (df['close'] <= df['open'].shift(1)) & 
                (df['open'] >= df['close'].shift(1)) &
                (df['body'] > df['body'].shift(1))
            )
            
            # 3. Doji (Body is very small compared to shadows)
            avg_body = df['body'].rolling(window=10).mean()
            df['doji'] = df['body'] < (0.1 * avg_body)
            
            # 4. Hammer (Small body, long lower shadow, little to no upper shadow)
            df['hammer'] = (
                (df['lower_shadow'] > 2 * df['body']) & 
                (df['upper_shadow'] < 0.2 * df['body'])
            )

            # Drop temporary calculation columns if desired, but they might be useful features
            # df.drop(columns=['body', 'upper_shadow', 'lower_shadow', 'is_bullish', 'is_bearish'], inplace=True)
            
            return df
            
        except Exception as e:
            logger.error(f"Error detecting candle patterns: {e}")
            return df

if __name__ == "__main__":
    # Simple test
    df_test = pd.DataFrame({
        'open': [100, 95, 90],
        'high': [105, 98, 102],
        'low': [90, 88, 85],
        'close': [92, 90, 100] # Bullish engulfing on last candle
    })
    engine = CandlePatternEngine()
    res = engine.add_patterns(df_test)
    print("Bullish Engulfing Signals:\n", res[['close', 'bullish_engulfing']])
