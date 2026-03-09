import logging

logger = logging.getLogger(__name__)

class StrategyAgent:
    """
    Selects the best trading strategy/model based on the current market regime.
    """
    
    def __init__(self):
        # Map regimes to specific strategy handlers or model names
        self.regime_map = {
            "trending": "trend_following_model",
            "trending_volatile": "breakout_model",
            "ranging": "mean_reversion_model",
            "low_volatility_ranging": "accumulation_model",
            "high_volatility_ranging": "volatility_expansion_model",
            "unknown": "default_model"
        }
        
    def select_strategy(self, regime: str) -> str:
        """
        Returns the name of the strategy to execute.
        """
        strategy = self.regime_map.get(regime, "default_model")
        logger.info(f"Regime evaluated as '{regime}'. Selected strategy: {strategy}")
        return strategy

if __name__ == "__main__":
    agent = StrategyAgent()
    print("Testing Strategy Selection:")
    print(f"Trending -> {agent.select_strategy('trending')}")
    print(f"Ranging -> {agent.select_strategy('ranging')}")
