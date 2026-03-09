import sqlite3
import logging
from datetime import datetime
import os

logger = logging.getLogger(__name__)

DB_PATH = "app/feedback/feedback.db"

def _init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            symbol TEXT,
            regime TEXT,
            strategy TEXT,
            decision TEXT,
            confidence REAL,
            entry_price REAL,
            stop_loss REAL,
            take_profit REAL,
            outcome TEXT DEFAULT 'PENDING',
            actual_pnl REAL DEFAULT 0.0
        )
    ''')
    conn.commit()
    conn.close()

# Initialize database on module load
_init_db()

class FeedbackLoop:
    """
    Logs predictions to a local SQLite database for future evaluation and model retraining.
    """
    
    @staticmethod
    def log_prediction(symbol: str, analysis_result: dict):
        """
        Logs a generated trading decision and its risk parameters.
        """
        try:
            decision = analysis_result.get('trading_decision', {})
            risk = analysis_result.get('risk_assessment', {})
            
            # Don't log holds or invalid trades as strongly, but could be useful
            if decision.get('decision') == 'HOLD':
                return

            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO predictions 
                (timestamp, symbol, regime, strategy, decision, confidence, entry_price, stop_loss, take_profit)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                datetime.utcnow().isoformat(),
                symbol,
                analysis_result.get('regime'),
                analysis_result.get('selected_strategy'),
                decision.get('decision'),
                decision.get('confidence'),
                risk.get('entry_price'),
                risk.get('stop_loss'),
                risk.get('take_profit')
            ))
            
            conn.commit()
            conn.close()
            logger.info(f"Logged prediction for {symbol} to feedback database.")
            
        except Exception as e:
            logger.error(f"Failed to log prediction: {e}")

    @staticmethod
    def evaluate_pending_trades():
        """
        Evaluates all PENDING trades by checking if the current price has hit
        Stop Loss or Take Profit. Updates outcome to WIN or LOSS accordingly.
        Called periodically by the radar scheduler.
        """
        try:
            import yfinance as yf
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, symbol, decision, entry_price, stop_loss, take_profit, timestamp
                FROM predictions
                WHERE outcome = 'PENDING' AND stop_loss IS NOT NULL AND take_profit IS NOT NULL
                LIMIT 50
            """)
            pending = cursor.fetchall()
            resolved = 0
            
            for row in pending:
                pid, symbol, decision, entry_price, stop_loss, take_profit, ts = row
                try:
                    ticker = yf.Ticker(symbol)
                    hist = ticker.history(period="1d", interval="5m")
                    if hist.empty:
                        continue
                    
                    high = hist['High'].max()
                    low = hist['Low'].min()
                    current_price = hist['Close'].iloc[-1]
                    
                    outcome = None
                    actual_pnl = 0.0
                    
                    if decision == 'BUY':
                        if low <= stop_loss:
                            outcome = 'LOSS'
                            actual_pnl = stop_loss - entry_price
                        elif high >= take_profit:
                            outcome = 'WIN'
                            actual_pnl = take_profit - entry_price
                    elif decision == 'SELL':
                        if high >= stop_loss:
                            outcome = 'LOSS'
                            actual_pnl = entry_price - stop_loss
                        elif low <= take_profit:
                            outcome = 'WIN'
                            actual_pnl = entry_price - take_profit
                    
                    if outcome:
                        cursor.execute("""
                            UPDATE predictions SET outcome = ?, actual_pnl = ? WHERE id = ?
                        """, (outcome, round(actual_pnl, 4), pid))
                        resolved += 1
                        logger.info(f"Trade Resolved: {symbol} {decision} → {outcome} (PnL: {actual_pnl:.2f})")
                
                except Exception as e:
                    logger.warning(f"Could not evaluate trade {pid} for {symbol}: {e}")
            
            conn.commit()
            conn.close()
            if resolved > 0:
                logger.info(f"Feedback Loop: Resolved {resolved} pending trades.")
                # ── Phase 29: resolve profit targets after feedback updates ──
                try:
                    from app.journal.db import JournalDB
                    newly_resolved = JournalDB.resolve_targets_from_feedback()
                    if newly_resolved:
                        for r in newly_resolved:
                            logger.info(
                                f"🎯 Target AUTO-RESOLVED: {r['symbol']} → {r['status']} "
                                f"(outcome={r['outcome']}, pnl={r['actual_pnl']})"
                            )
                except Exception as te:
                    logger.warning(f"Target resolution post-feedback failed: {te}")
                
        except Exception as e:
            logger.error(f"Feedback evaluation failed: {e}")

if __name__ == "__main__":
    # Test DB creation
    FeedbackLoop.log_prediction("TEST", {
        "regime": "test",
        "selected_strategy": "test",
        "trading_decision": {"decision": "BUY", "confidence": 0.9},
        "risk_assessment": {"entry_price": 100, "stop_loss": 90, "take_profit": 120}
    })
    print("Test prediction logged. Check app/feedback/feedback.db")
