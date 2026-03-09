import logging

logger = logging.getLogger(__name__)

class SIPForecaster:
    """
    Calculates future SIP values based on AI-predicted CAGR and Inflation constraints.
    """
    def __init__(self, inflation_rate: float = 0.06):
        self.inflation_rate = inflation_rate

    def calculate_sip_future_value(self, monthly_sip: float, years: int, predicted_cagr_pct: float) -> dict:
        """
        Standard Future Value of an Annuity formula.
        """
        if monthly_sip <= 0 or years <= 0:
            return {"error": "Invalid inputs"}

        # Convert annual percentage to decimal
        r_annual = predicted_cagr_pct / 100.0
        
        # Monthly rate
        i = r_annual / 12.0
        n_months = years * 12
        
        # Future Value formula for SIP (payments at beginning of period usually, but standard annuity is end)
        # Using beginning of period (Annuity Due): P * [((1+i)^n - 1) / i] * (1+i)
        
        if i == 0:
            fv = monthly_sip * n_months
        else:
            fv = monthly_sip * ( ((1 + i)**n_months - 1) / i ) * (1 + i)
            
        total_invested = monthly_sip * n_months
        wealth_gained = fv - total_invested
        
        # Inflation Adjusted (Discount FV back to present value using inflation rate)
        inflation_adjusted_fv = fv / ((1 + self.inflation_rate)**years)
        
        return {
            "monthly_sip": round(monthly_sip, 2),
            "duration_years": years,
            "predicted_cagr_pct": round(predicted_cagr_pct, 2),
            "total_invested": round(total_invested, 2),
            "future_value_nominal": round(fv, 2),
            "wealth_gained": round(wealth_gained, 2),
            "inflation_adjusted_fv": round(inflation_adjusted_fv, 2),
            "wealth_multiplier": round(fv / total_invested, 2) if total_invested > 0 else 0
        }
