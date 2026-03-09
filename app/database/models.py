from sqlalchemy import Column, String, Integer, Numeric, Boolean, DateTime, ForeignKey, Text, BigInteger
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()

# --- 1. USER DOMAIN ---
class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=True) # Nullable for OAuth users
    full_name = Column(String(100))
    profile_pic = Column(String(255))
    role = Column(String(20), default="retail")
    kyc_status = Column(String(20), default="pending")
    risk_level = Column(String(20), default="Moderate")
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    portfolios = relationship("Portfolio", back_populates="owner")
    trades = relationship("Trade", back_populates="user")

class UserSubscription(Base):
    __tablename__ = "user_subscriptions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    plan_name = Column(String(50), nullable=False)
    status = Column(String(20), default="active")
    expires_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

# --- 2. MARKET DATA DOMAIN ---
class Asset(Base):
    __tablename__ = "assets"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol = Column(String(20), unique=True, nullable=False)
    asset_name = Column(String, nullable=False)
    market_type = Column(String(20), nullable=False) # Stock, Crypto, Forex, MutualFund
    sector = Column(String(50))
    category = Column(String(50))
    benchmark_symbol = Column(String(20))
    expense_ratio = Column(Numeric(10, 4))
    is_active = Column(Boolean, default=TRUE)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    price_history = relationship("PriceHistory", back_populates="asset")
    predictions = relationship("Prediction", back_populates="asset")

class PriceHistory(Base):
    __tablename__ = "price_history"
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id"), primary_key=True)
    timestamp = Column(DateTime(timezone=True), primary_key=True)
    open_price = Column(Numeric(20, 8))
    high_price = Column(Numeric(20, 8))
    low_price = Column(Numeric(20, 8))
    close_price = Column(Numeric(20, 8))
    volume = Column(Numeric(30, 8))
    
    asset = relationship("Asset", back_populates="price_history")

# --- 3. TRADING DOMAIN ---
class Portfolio(Base):
    __tablename__ = "portfolios"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    portfolio_name = Column(String(100), nullable=False)
    total_value = Column(Numeric(20, 2), default=0.0)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    owner = relationship("User", back_populates="portfolios")

class Trade(Base):
    __tablename__ = "trades"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id"))
    trade_type = Column(String(10), nullable=False) # BUY, SELL
    entry_price = Column(Numeric(20, 8), nullable=False)
    stop_loss = Column(Numeric(20, 8))
    take_profit = Column(Numeric(20, 8))
    quantity = Column(Numeric(20, 8), nullable=False)
    pnl = Column(Numeric(20, 2))
    execution_regime = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    user = relationship("User", back_populates="trades")

# --- 4. AI/ML DOMAIN ---
class Model(Base):
    __tablename__ = "models"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_name = Column(String(50), unique=True, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

class ModelVersion(Base):
    __tablename__ = "model_versions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_id = Column(UUID(as_uuid=True), ForeignKey("models.id"))
    version_tag = Column(String(20), nullable=False)
    validation_score = Column(Numeric(10, 6))
    status = Column(String(20), default="candidate")
    deployed_at = Column(DateTime(timezone=True))
    artifact_path = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

class Prediction(Base):
    __tablename__ = "predictions"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id"))
    model_version_id = Column(UUID(as_uuid=True), ForeignKey("model_versions.id"))
    probability_up = Column(Numeric(10, 6))
    expected_return = Column(Numeric(10, 6))
    confidence_score = Column(Numeric(10, 6))
    regime = Column(Text)
    raw_payload = Column(JSONB)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    asset = relationship("Asset", back_populates="predictions")

# --- 5. GOVERNANCE DOMAIN ---
class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True))
    action_type = Column(String(50), nullable=False)
    module = Column(String(50), nullable=False)
    payload = Column(JSONB)
    severity = Column(String(20), default="info")
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
