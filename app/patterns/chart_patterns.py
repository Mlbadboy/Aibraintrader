import pandas as pd
import numpy as np
from scipy.signal import argrelextrema
import logging

logger = logging.getLogger(__name__)

class ChartPatternEngine:
    """
    Engine for detecting structural chart patterns based on local extrema.
    """
    
    def __init__(self, order=5):
        # Order dictates how many points on each side to check for local min/max
        self.order = order

    def find_extrema(self, df: pd.DataFrame, column='close'):
        """
        Finds local peaks and troughs in the price data.
        """
        if df.empty or len(df) < self.order * 2 + 1:
            return [], []
            
        data = df[column].values
        # Find local maxima (peaks)
        peaks = argrelextrema(data, np.greater, order=self.order)[0]
        # Find local minima (troughs)
        troughs = argrelextrema(data, np.less, order=self.order)[0]
        
        return peaks, troughs

    def detect_double_top(self, df: pd.DataFrame, tolerance=0.03) -> bool:
        """
        Basic detection for Double Top pattern near the end of the dataframe.
        tolerance: % difference allowed between the two peaks.
        """
        peaks, _ = self.find_extrema(df, 'high')
        if len(peaks) < 2:
            return False
            
        # Check the last two peaks
        p1_idx, p2_idx = peaks[-2], peaks[-1]
        p1_val, p2_val = df['high'].iloc[p1_idx], df['high'].iloc[p2_idx]
        
        # Check if they are similar in price
        if abs(p1_val - p2_val) / max(p1_val, p2_val) <= tolerance:
            # Additionally, check if current price has broken below the trough between them
            _, troughs = self.find_extrema(df.iloc[p1_idx:p2_idx+1], 'low')
            if len(troughs) > 0:
                neckline = df['low'].iloc[p1_idx + troughs[0]]
                current_price = df['close'].iloc[-1]
                if current_price < neckline:
                    return True # Breakdown confirmed
        return False
        
    def add_patterns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Adds chart pattern signals to dataframe.
        Note: True pattern logic is complex; this provides basic boolean flags.
        """
        df = df.copy()
        df['double_top'] = False
        
        if len(df) > 50:
            # For backtesting/historical feature generation, we'd roll this
            # For simplicity in real-time, just check the current state
            is_dt = self.detect_double_top(df)
            df.loc[df.index[-1], 'double_top'] = is_dt
            
        return df

if __name__ == "__main__":
    # Test with dummy wave data
    x = np.linspace(0, 4*np.pi, 100)
    y = np.sin(x) + 10 # Creates structural peaks/troughs
    # artificially drop the end to trigger double top neckline break
    y[-10:] = 8 
    
    df_test = pd.DataFrame({'high': y+0.5, 'low': y-0.5, 'close': y})
    engine = ChartPatternEngine(order=10)
    print("Double Top Detected:", engine.detect_double_top(df_test, tolerance=0.05))
