import logging

logger = logging.getLogger(__name__)

class ClassificationAgent:
    """
    Classifies an asset into 'Investment', 'Swing', or 'F&O' based on its current behavior.
    """
    def __init__(self):
        pass
        
    def classify(self, analysis_result: dict, raw_df) -> str:
        """
        Determines the trading grade of the asset.
        
        Investment criteria: Trending structure, reasonable volatility, bullish debate decision.
        Swing criteria: Clear short-term momentum (buy/sell).
        F&O criteria: Extreme liquidity (high volume) and high daily variance (ATR relative to price).
        """
        try:
            # We need raw_df to check volume and variance deeper if we wanted to be super robust.
            # For now, we use the pre-calculated analysis_result and latest indicator frame.
            
            regime = analysis_result.get('regime', '')
            decision = analysis_result.get('trading_decision', {}).get('decision', 'HOLD')
            latest = analysis_result.get('latest_indicators', {})
            
            price = latest.get('close', 1.0)
            atr = latest.get('atr', 0.0)
            volume = latest.get('volume', 0.0)
            
            # 1. Check F&O Suitability (High Liquidity + High Volatility)
            # Rough proxy: ATR is > 3% of price, and Volume is very high (> 5M shares usually)
            volatility_pct = (atr / price) * 100 if price > 0 else 0
            
            if volatility_pct > 2.5 and volume > 1000000:
                if "volatility" in regime or "trending" in regime:
                    return "F&O" # High octane play
            
            # 2. Check Investment Suitability
            # If the market is in a solid trend (not ranging) and volatility isn't wild.
            if regime == 'trending' and decision == 'BUY' and volatility_pct < 2.0:
                 return "Investment"
                 
            # 3. Check Swing Trading
            # If there's a strong BUY/SELL signal in a normal or ranging market.
            if decision in ['BUY', 'SELL']:
                 return "Swing"
                 
            return "Avoid" # If it's HOLD and uninteresting
            
        except Exception as e:
            logger.error(f"Error classifying asset: {e}")
            return "Unknown"
