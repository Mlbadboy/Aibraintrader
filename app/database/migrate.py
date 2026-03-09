import sqlite3
import logging
from sqlalchemy.orm import Session
from app.database.session import SessionLocal, engine
from app.database.models import Prediction, Asset, Base
import uuid
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Paths to legacy SQLite DBs
FEEDBACK_DB = "app/feedback/feedback.db"
RADAR_DB = "app/radar/radar.db"

def migrate_predictions():
    """Migrates predictions from feedback.db to PostgreSQL."""
    try:
        sqlite_conn = sqlite3.connect(FEEDBACK_DB)
        cursor = sqlite_conn.cursor()
        cursor.execute("SELECT symbol, asset_type, signal, confidence, timestamp, metadata FROM predictions")
        rows = cursor.fetchall()
        
        pg_db = SessionLocal()
        
        for symbol, asset_type, signal, confidence, timestamp, metadata_json in rows:
            # 1. Ensure Asset exists in PG
            asset = pg_db.query(Asset).filter(Asset.symbol == symbol).first()
            if not asset:
                asset = Asset(
                    id=uuid.uuid4(),
                    symbol=symbol,
                    asset_name=symbol,
                    market_type=asset_type
                )
                pg_db.add(asset)
                pg_db.commit()
                pg_db.refresh(asset)
            
            # 2. Add Prediction
            new_pred = Prediction(
                asset_id=asset.id,
                probability_up=confidence if signal == 'BUY' else 1-confidence if signal == 'SELL' else 0.5,
                confidence_score=confidence,
                regime=signal,
                raw_payload=json.loads(metadata_json) if metadata_json else {}
            )
            pg_db.add(new_pred)
            
        pg_db.commit()
        logger.info(f"Successfully migrated {len(rows)} predictions to PostgreSQL.")
        pg_db.close()
        sqlite_conn.close()
        
    except Exception as e:
        logger.error(f"Migration Error: {e}")

if __name__ == "__main__":
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)
    migrate_predictions()
