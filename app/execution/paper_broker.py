import sqlite3
import logging
import os
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)

class PaperBroker:
    """
    A simulated broker execution engine that logs signals to a local SQLite/Postgres DB.
    """
    def __init__(self, db_path="trading.db"):
        self.db_path = db_path
        self._init_db()
        
    def _init_db(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS trades_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        symbol TEXT,
                        timestamp TEXT,
                        direction TEXT,
                        entry_price REAL,
                        stop_loss REAL,
                        take_profit REAL,
                        confidence REAL,
                        reason_tags TEXT,
                        status TEXT
                    )
                ''')
                conn.commit()
        except Exception as e:
            logger.error(f"[PaperBroker] DB Init failed: {e}")

    def execute_signal(self, signal: Dict[str, Any]) -> dict:
        """
        Takes a DebateAgent Signal dictionary and logs an OPEN paper trade.
        """
        direction = signal.get('direction', 'HOLD')
        if direction == 'HOLD':
            return {"status": "skipped", "reason": "No entry signal"}
            
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO trades_log 
                    (symbol, timestamp, direction, entry_price, stop_loss, take_profit, confidence, reason_tags, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    signal.get('symbol', 'UNKNOWN'),
                    datetime.now().isoformat(),
                    direction,
                    signal.get('entry', 0.0),
                    signal.get('sl', 0.0),
                    str(signal.get('targets', [])),
                    signal.get('confidence', 0.0),
                    ", ".join(signal.get('reason_tags', [])),
                    "OPEN_PAPER"
                ))
                conn.commit()
                trade_id = cursor.lastrowid
            
            logger.info(f"[PaperBroker] Executed paper trade #{trade_id} for {signal.get('symbol', '')}")
            return {"status": "executed", "trade_id": trade_id, "mode": "paper"}
            
        except Exception as e:
            logger.error(f"[PaperBroker] Error executing trade: {e}")
            return {"status": "error", "reason": str(e)}

    def get_open_trades(self):
        """Fetch all OPEN_PAPER status trades from the DB."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM trades_log WHERE status='OPEN_PAPER' ORDER BY timestamp DESC")
                columns = [col[0] for col in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"[PaperBroker] Fetch error: {e}")
            return []

if __name__ == "__main__":
    broker = PaperBroker()
    print("Testing Paper Broker Execution:")
    mock_signal = {
        "symbol": "BTC/USDT",
        "direction": "BUY",
        "entry": 65000.0,
        "sl": 63000.0,
        "targets": [67000.0, 70000.0],
        "confidence": 0.85,
        "reason_tags": ["ML: Bullish", "Sentiment: Bullish"]
    }
    res = broker.execute_signal(mock_signal)
    print("Execution Result:", res)
    print("Open Trades:", broker.get_open_trades())
