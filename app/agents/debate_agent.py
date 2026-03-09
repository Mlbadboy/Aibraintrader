import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class DebateAgent:
    """
    Meta-agent that resolves conflicts between different predictive models
    and sentiment logic, outputting a structured Signal.
    """
    
    def __init__(self, confidence_threshold=0.60):
        self.threshold = confidence_threshold
        
    def generate_signal(self, 
                        symbol: str, 
                        current_price: float, 
                        atr: float, 
                        ml_bull_prob: float, 
                        sentiment_score: float) -> Dict[str, Any]:
        """
        Evaluates probabilities heavily weighting sentiment.
        sentiment_score: 0 (extremely bearish) to 1 (extremely bullish), neutral is 0.5
        Returns a structured Signal dict matching the Production Spec.
        """
        reason_tags = []
        ml_bear_prob = 1.0 - ml_bull_prob
        
        # 1. Base ML Decision
        if ml_bull_prob >= self.threshold:
            base_decision = "BUY"
            reason_tags.append(f"ML: Bullish ({ml_bull_prob:.2f})")
        elif ml_bear_prob >= self.threshold:
            base_decision = "SELL"
            reason_tags.append(f"ML: Bearish ({ml_bear_prob:.2f})")
        else:
            base_decision = "HOLD"
            reason_tags.append(f"ML: Neutral")

        # 2. Sentiment Context
        if sentiment_score >= 0.65:
            reason_tags.append("Sentiment: Bullish")
        elif sentiment_score <= 0.35:
            reason_tags.append("Sentiment: Bearish")
        else:
            reason_tags.append("Sentiment: Neutral")

        final_decision = base_decision
        final_confidence = max(ml_bull_prob, ml_bear_prob)
        
        # 3. Override Rules (Vetoes)
        if base_decision == "BUY" and sentiment_score <= 0.35:
            final_decision = "HOLD"
            final_confidence -= 0.15
            reason_tags.append("VETO: Negative News Override")
        elif base_decision == "SELL" and sentiment_score >= 0.65:
            final_decision = "HOLD"
            final_confidence -= 0.15
            reason_tags.append("VETO: Positive News Override")
            
        # 4. Risk / Stop Loss / Targets Math
        entry = current_price
        sl = current_price
        targets = []
        
        # Simple ATR-based positioning
        atr_multiplier = 1.5
        if atr <= 0: atr = current_price * 0.01 # fallback to 1% generic distance if atr fails
        
        if final_decision == "BUY":
            sl = entry - (atr_multiplier * atr)
            targets = [entry + (1 * atr), entry + (2 * atr)]
        elif final_decision == "SELL":
            sl = entry + (atr_multiplier * atr)
            targets = [entry - (1 * atr), entry - (2 * atr)]

        logger.info(f"Signal Generated: {symbol} -> {final_decision} (Conf: {final_confidence:.2f})")
        
        return {
            "symbol": symbol,
            "decision": final_decision,
            "entry": round(entry, 2),
            "sl": round(sl, 2),
            "targets": [round(t, 2) for t in targets],
            "confidence": round(final_confidence, 2),
            "reason_tags": reason_tags
        }

if __name__ == "__main__":
    agent = DebateAgent()
    print("Testing Debate Agent Veto Rule (Buy Signal + Bad News):")
    sig = agent.generate_signal("AAPL", 150.0, 3.5, 0.75, 0.20)
    print(sig)
