import pandas as pd
import logging
import sys

logger = logging.getLogger(__name__)

class BacktestEngine:
    """
    Simulates trading over a historical dataframe using the agentic pipeline.
    """
    
    def __init__(self, initial_capital=10000.0, commission_pct=0.001):
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.commission_pct = commission_pct
        self.trades = []
        self.equity_curve = []
        
        # State variables
        self.position = 0 # 0 = Flat, 1 = Long, -1 = Short (Shorting simplified)
        self.entry_price = 0.0
        self.position_size_units = 0.0
        self.stop_loss = 0.0
        self.take_profit = 0.0

    def calculate_pnl(self, exit_price):
        if self.position == 1:
            pnl = (exit_price - self.entry_price) * self.position_size_units
        elif self.position == -1:
             pnl = (self.entry_price - exit_price) * self.position_size_units
        else:
            pnl = 0
            
        # Deduct commission on exit and abstractly on entry
        commission = (self.entry_price * self.position_size_units * self.commission_pct) + (exit_price * self.position_size_units * self.commission_pct)
        return pnl - commission

    def run(self, df: pd.DataFrame, decisions: list, risks: list):
        """
        Runs the backtest. 
        Note: For a realistic backtest, `decisions` and `risks` must be generated in a rolling window to prevent lookahead bias.
        For this prototype, we simulate iterating over the pre-calculated pipeline outputs.
        """
        if len(df) != len(decisions) or len(df) != len(risks):
            logger.error("Data mismatch: df, decisions, risks must be same length.")
            return {}

        logger.info(f"Starting Backtest on {len(df)} candles. Initial Capital: ${self.initial_capital}")

        for i in range(len(df)):
            row = df.iloc[i]
            decision = decisions[i]
            risk = risks[i]
            current_price = row['close']
            
            # --- Check active trade for exit ---
            if self.position != 0:
                exit_triggered = False
                exit_reason = ""
                exit_p = current_price
                
                # Check Stop Loss / Take profit (Simplified using only Close price)
                if self.position == 1:
                    if row['low'] <= self.stop_loss:
                        exit_triggered = True; exit_reason = "SL"; exit_p = self.stop_loss
                    elif row['high'] >= self.take_profit:
                        exit_triggered = True; exit_reason = "TP"; exit_p = self.take_profit
                elif self.position == -1:
                    if row['high'] >= self.stop_loss:
                        exit_triggered = True; exit_reason = "SL"; exit_p = self.stop_loss
                    elif row['low'] <= self.take_profit:
                        exit_triggered = True; exit_reason = "TP"; exit_p = self.take_profit
                        
                if exit_triggered:
                    pnl = self.calculate_pnl(exit_p)
                    self.capital += pnl
                    self.trades.append({
                        "id": len(self.trades)+1, "entry_idx": i, "exit_idx": i,
                        "type": "LONG" if self.position == 1 else "SHORT",
                        "entry_price": self.entry_price, "exit_price": exit_p, 
                        "pnl": pnl, "capital": self.capital, "reason": exit_reason
                    })
                    self.position = 0
            
            # --- Check for new trade entry if flat ---
            if self.position == 0:
                action = risk.get('approved_action', 'HOLD')
                if action in ['BUY', 'SELL']:
                    # Enter trade
                    self.position = 1 if action == 'BUY' else -1
                    self.entry_price = risk['entry_price']
                    self.position_size_units = risk['position_size_units']
                    self.stop_loss = risk['stop_loss']
                    self.take_profit = risk['take_profit']
            
            self.equity_curve.append(self.capital)

        # Force exit at the end if still in position
        if self.position != 0:
            final_price = df['close'].iloc[-1]
            pnl = self.calculate_pnl(final_price)
            self.capital += pnl
            self.trades.append({
                        "id": len(self.trades)+1, "entry_idx": i, "exit_idx": i,
                        "type": "LONG" if self.position == 1 else "SHORT",
                        "entry_price": self.entry_price, "exit_price": final_price, 
                        "pnl": pnl, "capital": self.capital, "reason": "End of Data"
                    })
            self.position = 0

        return self._generate_report()

    def _generate_report(self):
        total_trades = len(self.trades)
        winning_trades = sum(1 for t in self.trades if t['pnl'] > 0)
        win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
        total_pnl = self.capital - self.initial_capital
        
        # Max Drawdown
        equity_series = pd.Series(self.equity_curve)
        rolling_max = equity_series.cummax()
        drawdowns = (equity_series - rolling_max) / rolling_max
        max_dd = drawdowns.min() * 100 if not drawdowns.empty else 0
        
        report = {
            "initial_capital": self.initial_capital,
            "final_capital": round(self.capital, 2),
            "total_pnl": round(total_pnl, 2),
            "total_trades": total_trades,
            "win_rate_pct": round(win_rate, 2),
            "max_drawdown_pct": round(max_dd, 2)
        }
        logger.info(f"Backtest Complete. Report: {report}")
        return report

if __name__ == "__main__":
    print("Run verify_phase3.py to test the Backtest Engine.")
