from sqlalchemy import create_all
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import create_engine
import os
import logging
from .models import Base

logger = logging.getLogger(__name__)

# Use environment variables for production readiness
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/trading_db")

engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Drops and Recreates all tables for Phase 8 development (Use migrations in prod)"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Enterprise Database Tables Initialized Successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")

def get_db():
    """FastAPI Dependency for DB session injection."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
