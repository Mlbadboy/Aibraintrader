import logging

logger = logging.getLogger(__name__)

class RiskGuardian:
    """
    Agent responsible for capital protection, stop-loss calculations, and position sizing.
    """
    
    def __init__(self, max_risk_per_trade_pct: float = 0.02, atr_multiplier: float = 2.0):
        # Default: Risk max 2% of total capital per trade
        self.max_risk_pct = max_risk_per_trade_pct
        # Determine strictness of stop loss (2x ATR is common)
        self.atr_multiplier = atr_multiplier
        
    def assess_trade(self, decision: dict, current_price: float, atr: float, capital: float) -> dict:
        """
        Evaluates a trading decision and attaches risk parameters.
        Returns a dictionary with position size and stop loss.
        """
        trade_dir = decision.get("decision", "HOLD")
        confidence = decision.get("confidence", 0.0)
        
        # Determine if we should VETO
        # Veto if ATR is abnormally high (undefined or zero)
        if not atr or atr <= 0:
             logger.warning("Invalid ATR. Vetoing trade.")
             trade_dir = "HOLD"
             
        # Veto if decision confidence is too low (handled by Debate, but double checked here)
        if confidence < 0.60:
             trade_dir = "HOLD"

        risk_assessment = {
            "approved_action": trade_dir,
            "entry_price": current_price,
            "stop_loss": None,
            "take_profit": None, # Fixed 1:2 R:R for now
            "position_size_usd": 0.0,
            "position_size_units": 0.0,
            "risk_amount_usd": 0.0
        }

        if trade_dir == "HOLD":
            return risk_assessment
            
        # Calculate Risk Amount (Total USD we are willing to lose)
        risk_usd = capital * self.max_risk_pct
        
        # Calculate Stop Loss Distance
        sl_distance = atr * self.atr_multiplier
        
        if trade_dir == "BUY":
            stop_loss = current_price - sl_distance
            take_profit = current_price + (sl_distance * 2) # Target 1:2 Risk-Reward
        elif trade_dir == "SELL":
            stop_loss = current_price + sl_distance
            take_profit = current_price - (sl_distance * 2)
            
        # Position Sizing (Simplified Kelly/Risk Model)
        # Position Size = Risk Amount / (Entry Price - Stop Loss Price)
        # i.e., How many shares can I buy where if it hits SL, I lose exactly `risk_usd`?
        try:
             position_units = risk_usd / sl_distance
             position_usd = position_units * current_price
             
             # Capital constraint
             if position_usd > capital:
                 position_usd = capital
                 position_units = position_usd / current_price
                 # Re-calculate real risk if we cap the trade size
                 risk_usd = position_units * sl_distance
                 
        except ZeroDivisionError:
             position_units = 0.0
             position_usd = 0.0
             risk_usd = 0.0

        risk_assessment.update({
            "stop_loss": round(stop_loss, 2),
            "take_profit": round(take_profit, 2),
            "position_size_usd": round(position_usd, 2),
            "position_size_units": round(position_units, 4),
            "risk_amount_usd": round(risk_usd, 2)
        })
        
        logger.info(f"Risk Assessed: {trade_dir} | SL: {stop_loss:.2f} | Size: ${position_usd:.2f} | Risk: ${risk_usd:.2f}")

        return risk_assessment

if __name__ == "__main__":
    guardian = RiskGuardian(max_risk_per_trade_pct=0.02)
    fake_decision = {"decision": "BUY", "confidence": 0.85}
    res = guardian.assess_trade(fake_decision, current_price=150.0, atr=3.5, capital=10000.0)
    print("Test Risk Assessment:", res)
