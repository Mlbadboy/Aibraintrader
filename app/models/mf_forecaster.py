import pandas as pd
from prophet import Prophet
import logging

logger = logging.getLogger(__name__)

class MFForecaster:
    """
    Uses Prophet to forecast future NAV trajectories based on historical time series.
    Provides Upper (Bull), Lower (Bear), and Expected (Base) scenarios.
    """
    
    def __init__(self):
        pass

    def forecast_nav(self, df: pd.DataFrame, periods_days: int = 365) -> dict:
        """
        Takes a DataFrame containing 'date' and 'nav'.
        Returns a dictionary mapping future dates to projected prices.
        """
        if df.empty or len(df) < 252:
            return {"error": "Need at least 1 year of data for forecasting."}
            
        try:
            # Prophet requires columns 'ds' and 'y'
            prophet_df = pd.DataFrame({
                'ds': df['date'],
                'y': df['nav']
            })
            
            # Configure Prophet for financial time series (less weekly seasonality, heavy trend)
            m = Prophet(daily_seasonality=False, weekly_seasonality=False, yearly_seasonality=True, 
                        changepoint_prior_scale=0.05)
            
            # Fit model (suppress verbose output)
            import logging as prophet_log
            prophet_log.getLogger('cmdstanpy').setLevel(prophet_log.ERROR)
            
            m.fit(prophet_df)
            
            # Create future dataframe
            future = m.make_future_dataframe(periods=periods_days, freq='D')
            
            # Predict
            forecast = m.predict(future)
            
            # Extract just the future portion
            future_forecast = forecast.tail(periods_days)
            
            current_nav = df['nav'].iloc[-1]
            future_base = future_forecast['yhat'].iloc[-1]
            future_bull = future_forecast['yhat_upper'].iloc[-1]
            future_bear = future_forecast['yhat_lower'].iloc[-1]
            
            return {
                "forecast_days": periods_days,
                "current_nav": float(current_nav),
                "expected_nav_1yr": float(future_base),
                "bull_case_nav_1yr": float(future_bull),
                "bear_case_nav_1yr": float(future_bear),
                "expected_cagr_1yr_pct": float(((future_base / current_nav) - 1) * 100),
                "bull_cagr_1yr_pct": float(((future_bull / current_nav) - 1) * 100),
                "bear_cagr_1yr_pct": float(((future_bear / current_nav) - 1) * 100),
                "time_series": future_forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].to_dict(orient='records')
            }
            
        except Exception as e:
            logger.error(f"Error forecasting NAV: {e}")
            return {"error": "Forecasting failed"}

if __name__ == "__main__":
    # Test
    from app.agents.mf_data_agent import MFDataAgent
    d_agent = MFDataAgent()
    df = d_agent.fetch_nav_history("SPY", "5y")
    forecaster = MFForecaster()
    res = forecaster.forecast_nav(df, periods_days=365)
    print(f"Current: {res['current_nav']:.2f} -> Expected 1Y: {res['expected_nav_1yr']:.2f}")
