import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)

class MFRiskEngine:
    """
    Calculates advanced proprietary risk metrics for Mutual Funds.
    """
    
    def __init__(self, risk_free_rate: float = 0.05): # Default 5% Risk Free Rate for India/Global avg
        self.rfr = risk_free_rate

    def calculate_cagr(self, initial_value, final_value, years):
        if initial_value <= 0 or years <= 0: return 0.0
        return ((final_value / initial_value) ** (1 / years)) - 1

    def calculate_max_drawdown(self, nav_series: pd.Series) -> float:
        rolling_max = nav_series.cummax()
        drawdown = nav_series / rolling_max - 1.0
        return abs(drawdown.min())

    def analyze_risk(self, df: pd.DataFrame) -> dict:
        """
        Expects a DataFrame with 'date' and 'nav' columns.
        Returns a dictionary of institutional metrics.
        """
        if df.empty or len(df) < 252: # Need at least a year
            return {"error": "Insufficient data for risk analysis. Need at least 1 year."}

        df = df.copy()
        
        # Calculate daily returns
        df['return'] = df['nav'].pct_change()
        
        # 1. Total & Annualized Return
        start_nav = df['nav'].iloc[0]
        end_nav = df['nav'].iloc[-1]
        days = (df['date'].iloc[-1] - df['date'].iloc[0]).days
        years = days / 365.25
        
        cagr = self.calculate_cagr(start_nav, end_nav, years)
        
        # 2. Volatility (Standard Deviation annualized)
        # 252 trading days roughly
        daily_volatility = df['return'].std()
        annual_volatility = daily_volatility * np.sqrt(252)
        
        # 3. Sharpe Ratio
        # (Return - RFR) / Volatility
        sharpe_ratio = (cagr - self.rfr) / annual_volatility if annual_volatility > 0 else 0
        
        # 4. Sortino Ratio
        # (Return - RFR) / Downside Deviation
        downside_returns = df.loc[df['return'] < 0, 'return']
        downside_deviation = downside_returns.std() * np.sqrt(252)
        sortino_ratio = (cagr - self.rfr) / downside_deviation if downside_deviation > 0 else 0
        
        # 5. Max Drawdown
        max_dd = self.calculate_max_drawdown(df['nav'])
        
        # 6. Proprietary Risk Score (0-100)
        # Lower is less risky.
        # Combines Volatility (40%), Max DD (40%), and lack of upside Sharpe (20%)
        norm_vol = min(annual_volatility / 0.40, 1.0) # Cap at 40% vol
        norm_dd = min(max_dd / 0.50, 1.0) # Cap at 50% drawdown
        norm_sharpe_penalty = max(1.0 - (sharpe_ratio / 2.0), 0.0) # Reward sharpe > 2.0
        
        risk_score = (norm_vol * 40) + (norm_dd * 40) + (norm_sharpe_penalty * 20)
        
        # Classification
        vol_class = "Low"
        if annual_volatility > 0.15: vol_class = "Moderate"
        if annual_volatility > 0.25: vol_class = "High"

        return {
            "cagr_pct": cagr * 100,
            "annual_volatility_pct": annual_volatility * 100,
            "sharpe_ratio": sharpe_ratio,
            "sortino_ratio": sortino_ratio,
            "max_drawdown_pct": max_dd * 100,
            "risk_score_100": min(round(risk_score), 100),
            "volatility_class": vol_class,
            "years_analyzed": years
        }

if __name__ == "__main__":
    # Mock test
    from app.agents.mf_data_agent import MFDataAgent
    d_agent = MFDataAgent()
    df = d_agent.fetch_nav_history("SPY", "3y")
    engine = MFRiskEngine()
    print(engine.analyze_risk(df))
