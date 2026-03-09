import sqlite3
import os
import json
import logging

logger = logging.getLogger(__name__)

DB_PATH = "app/radar/radar.db"

def _init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Stores the list of assets to scan
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS watchlist (
            symbol TEXT PRIMARY KEY,
            asset_type TEXT, -- 'stock', 'crypto', 'etf', 'option', 'commodity'
            target_horizon TEXT DEFAULT 'SHORT', -- 'INTRADAY', 'SHORT', 'LONG'
            added_at TEXT
        )
    ''')
    
    # Stores the latest computed results for the UI
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS radar_results (
            symbol TEXT,
            horizon TEXT, -- 'INTRADAY', 'SHORT', 'LONG'
            last_scanned TEXT,
            classification TEXT, 
            current_price REAL,
            regime TEXT,
            decision TEXT,
            confidence REAL,
            expected_return REAL, -- Added for performance ranking
            raw_payload TEXT,
            PRIMARY KEY (symbol, horizon)
        )
    ''')
    
    # Insert some default stocks to monitor if empty
    cursor.execute("SELECT COUNT(*) FROM watchlist")
    if cursor.fetchone()[0] <= 3: # If only the initial 3 US/Crypto defaults exist, expand
        defaults = [
            ("AAPL", "stock", "SHORT"),
            ("TSLA", "stock", "SHORT"),
            ("BTC", "crypto", "SHORT"),
            ("NIFTY", "stock", "INTRADAY"),
            ("SENSEX", "stock", "SHORT"),
            ("BANKNIFTY", "stock", "INTRADAY"),
            ("GOLD", "commodity", "SHORT"),
            ("SILVER", "commodity", "SHORT"),
            ("GOLDBEES", "etf", "LONG"),
            ("RELIANCE.NS", "stock", "SHORT")
        ]
        import datetime
        now = datetime.datetime.utcnow().isoformat()
        for symbol, asset_type, horizon in defaults:
            cursor.execute("INSERT OR IGNORE INTO watchlist (symbol, asset_type, target_horizon, added_at) VALUES (?, ?, ?, ?)", 
                           (symbol, asset_type, horizon, now))
                           
    conn.commit()
    conn.close()

_init_db()

class RadarDB:
    @staticmethod
    def get_watchlist():
        """Returns list of dicts: [{'symbol': 'AAPL', 'asset_type': 'stock'}, ...]"""
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM watchlist")
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return rows

    @staticmethod
    def add_to_watchlist(symbol: str, asset_type: str = "stock", target_horizon: str = "SHORT"):
        import datetime
        import json
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT OR REPLACE INTO watchlist (symbol, asset_type, target_horizon, added_at) VALUES (?, ?, ?, ?)",
                           (symbol.upper(), asset_type, target_horizon.upper(), datetime.datetime.utcnow().isoformat()))
            
            # Insert placeholder into radar_results so UI sees it instantly and fast_price_job can update its price
            cursor.execute('''
                INSERT OR IGNORE INTO radar_results 
                (symbol, horizon, last_scanned, classification, current_price, regime, decision, confidence, expected_return, raw_payload)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                symbol.upper(),
                target_horizon.upper(),
                datetime.datetime.utcnow().isoformat(),
                'Pending',
                0.0,
                'Unknown',
                'HOLD',
                0.0,
                0.0,
                json.dumps({"message": "Awaiting scan cycle"})
            ))

            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False # Already exists
        finally:
            conn.close()

    @staticmethod
    def update_result(symbol: str, horizon: str, data: dict):
        """Update or insert a scan result for a specific symbol and horizon."""
        import datetime
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Safe extraction — the pipeline returns nested dicts
        trading_decision = data.get('trading_decision', {}) or {}
        decision = trading_decision.get('decision') or data.get('decision', 'HOLD')
        conf = trading_decision.get('confidence') or data.get('confidence', 0.0)
        
        price = (data.get('latest_indicators') or {}).get('close', 0.0)
        if not price:
            price = trading_decision.get('entry') or 0.0
        
        regime = data.get('regime', 'Neutral')
        classification = data.get('classification', 'Avoid')
        expected_return = data.get('expected_return', 0.0)
        
        # If expected_return is 0, derive from ML confidence direction
        if not expected_return and decision in ('BUY', 'SELL'):
            ml = data.get('ml_predictions', {}) or {}
            bull_prob = ml.get('bull_prob', 0.5)
            bear_prob = ml.get('bear_prob', 0.5)
            expected_return = ((bull_prob - 0.5) * 20) if decision == 'BUY' else ((bear_prob - 0.5) * 20)
        
        cursor.execute('''
            INSERT INTO radar_results 
            (symbol, horizon, last_scanned, classification, current_price, regime, decision, confidence, expected_return, raw_payload)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(symbol, horizon) DO UPDATE SET
            last_scanned=excluded.last_scanned,
            classification=excluded.classification,
            current_price=excluded.current_price,
            regime=excluded.regime,
            decision=excluded.decision,
            confidence=excluded.confidence,
            expected_return=excluded.expected_return,
            raw_payload=excluded.raw_payload
        ''', (
            symbol.upper(),
            horizon.upper(),
            datetime.datetime.utcnow().isoformat(),
            classification,
            price,
            regime,
            decision,
            conf,
            expected_return,
            json.dumps(data)
        ))
        conn.commit()

    @staticmethod
    def update_live_price(symbol: str, price: float):
        """Fast-path update for current price only, across all horizons for a symbol"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE radar_results 
            SET current_price = ? 
            WHERE symbol = ?
        ''', (price, symbol.upper()))
        conn.commit()
        conn.close()

    @staticmethod
    def get_all_results(horizon: str = None):
        """Returns the latest radar data for the frontend dashboard, optionally filtered by horizon."""
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # LEFT JOIN from watchlist to radar_results ensures unscanned injected assets show up
        # and imports the 'asset_type' field so UI category filters work.
        if horizon:
            query = '''
                SELECT w.symbol, w.target_horizon as horizon, w.asset_type,
                       r.last_scanned, r.classification, r.current_price, r.regime, r.decision, r.confidence, r.expected_return, r.raw_payload
                FROM watchlist w
                LEFT JOIN radar_results r ON w.symbol = r.symbol AND w.target_horizon = r.horizon
                WHERE w.target_horizon = ?
                ORDER BY r.expected_return DESC NULLS LAST
            '''
            cursor.execute(query, (horizon.upper(),))
        else:
            query = '''
                SELECT w.symbol, w.target_horizon as horizon, w.asset_type,
                       r.last_scanned, r.classification, r.current_price, r.regime, r.decision, r.confidence, r.expected_return, r.raw_payload
                FROM watchlist w
                LEFT JOIN radar_results r ON w.symbol = r.symbol AND w.target_horizon = r.horizon
                ORDER BY r.expected_return DESC NULLS LAST
            '''
            cursor.execute(query)
            
        rows = []
        for row in cursor.fetchall():
            d = dict(row)
            if d['raw_payload']:
                d['raw_payload'] = json.loads(d['raw_payload'])
            else:
                d['raw_payload'] = {}
                d['classification'] = "Awaiting ML"
                d['decision'] = "SCANNING"
                d['current_price'] = 0.0
                d['expected_return'] = 0.0
                d['confidence'] = 0.0
                d['regime'] = "Pending"
            rows.append(d)
        conn.close()
        return rows
