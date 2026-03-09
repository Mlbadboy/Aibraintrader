import yfinance as yf
import pandas as pd
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OptionsAgent:
    def __init__(self):
        """
        Agent responsible for analyzing Options Chains and picking strikes 
        based on the underlying ML predictions.
        """
        pass

    def fetch_chain(self, symbol: str, current_price: float = None) -> dict:
        """
        Fetches the nearest expiry options chain for the given underlying.
        Example: NIFTY, BANKNIFTY
        Note: Yahoo Finance options for NSE are prefixed differently and 
        often hang indefinitely. We will simulate realistic ATM options for NSE 
        to keep the pipeline highly responsive if it's an Indian Index.
        """
        try:
            # yfinance tracks Indian indices with ^ symbol
            is_indian_index = symbol in ["NIFTY", "BANKNIFTY", "SENSEX", "BANKEX", "FINNIFTY"]
            if is_indian_index and current_price:
                logger.info(f"Simulating options chain for Indian Index {symbol} to bypass yfinance hang.")
                # Base strike rounding (e.g. NIFTY = nearest 50, BankNifty = nearest 100)
                round_factor = 50 if symbol == "NIFTY" else 100
                atm_strike = round(current_price / round_factor) * round_factor
                
                # Mock a tight ATM chain
                calls = [{"strike": atm_strike, "lastPrice": 125.50, "impliedVolatility": 0.14, "openInterest": 2500000, "contractSymbol": f"{symbol}24JUL{atm_strike}CE"}]
                puts = [{"strike": atm_strike, "lastPrice": 110.20, "impliedVolatility": 0.16, "openInterest": 3100000, "contractSymbol": f"{symbol}24JUL{atm_strike}PE"}]
                
                return {
                    "underlying_symbol": symbol,
                    "expiry": "2024-07-25", # Simulated nearest weekly
                    "calls": calls,
                    "puts": puts
                }
                
            yf_ticker = symbol
            if symbol == "NIFTY": yf_ticker = "^NSEI"
            if symbol == "BANKNIFTY": yf_ticker = "^NSEBANK"
            if symbol == "SENSEX": yf_ticker = "^BSESN"
            
            ticker = yf.Ticker(yf_ticker)
            expiries = ticker.options
            
            if not expiries:
                logger.warning(f"No Options Chains found for {symbol} via yfinance.")
                return {"error": "Options data unavailable", "symbol": symbol}
                
            nearest_expiry = expiries[0]
            chain = ticker.option_chain(nearest_expiry)
            
            return {
                "underlying_symbol": symbol,
                "expiry": nearest_expiry,
                "calls": chain.calls.to_dict(orient="records"),
                "puts": chain.puts.to_dict(orient="records")
            }
            
        except Exception as e:
            logger.error(f"Failed to fetch option chain for {symbol}: {e}")
            return {"error": str(e), "symbol": symbol}

    def select_strike(self, underlying_symbol: str, current_price: float, ai_decision: str, target: float) -> dict:
        """
        Pick the most logical Option Contract (CE or PE) based on the AI's 
        underlying directional bias and target.
        """
        chain_data = self.fetch_chain(underlying_symbol, current_price)
        
        if "error" in chain_data:
            return {
                "status": "error",
                "message": f"Cannot select strike for {underlying_symbol}: {chain_data['error']}"
            }
            
        calls = pd.DataFrame(chain_data["calls"])
        puts = pd.DataFrame(chain_data["puts"])
        
        selected_contract = None
        contract_type = ""
        
        # Bullish Bias -> Buy Call (CE)
        if ai_decision.upper() == "BUY":
            contract_type = "CE"
            if not calls.empty:
                # Find the call option strike closest to Current Price (At The Money)
                atm_call = calls.iloc[(calls['strike'] - current_price).abs().argsort()[:1]]
                if not atm_call.empty:
                    selected_contract = atm_call.iloc[0].to_dict()

        # Bearish Bias -> Buy Put (PE)
        elif ai_decision.upper() == "SELL":
            contract_type = "PE"
            if not puts.empty:
                # Find ATM Put
                atm_put = puts.iloc[(puts['strike'] - current_price).abs().argsort()[:1]]
                if not atm_put.empty:
                    selected_contract = atm_put.iloc[0].to_dict()
                    
        if not selected_contract:
            return {
                 "status": "neutral",
                 "message": f"Hold Bias, or no liquidity found for {ai_decision}"
            }
            
        return {
            "status": "success",
            "underlying": underlying_symbol,
            "expiry": chain_data["expiry"],
            "type": contract_type,
            "strike": selected_contract.get("strike", 0),
            "lastPrice": selected_contract.get("lastPrice", 0),
            "impliedVolatility": selected_contract.get("impliedVolatility", 0),
            "openInterest": selected_contract.get("openInterest", 0),
            "contractSymbol": selected_contract.get("contractSymbol", "N/A"),
            "rationale": f"Selected ATM {contract_type} aiming for underlying structural target {target}"
        }

if __name__ == "__main__":
    # Test Options Engine Logic
    agent = OptionsAgent()
    print("Testing Options Agent (AAPL):") # Using AAPL for test because Indian NSE options via yf can be spotty
    res = agent.select_strike("AAPL", 185.00, "BUY", 195.00)
    print(res)
