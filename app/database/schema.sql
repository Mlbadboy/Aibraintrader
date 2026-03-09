-- Institutional AI Trading Engine - PostgreSQL Core Schema
-- --------------------------------------------------------

-- 1. USER DOMAIN
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    role VARCHAR(20) DEFAULT 'retail', -- retail, HNI, admin
    kyc_status VARCHAR(20) DEFAULT 'pending',
    risk_level VARCHAR(20) DEFAULT 'Moderate',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    plan_name VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'active',
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. MARKET DATA DOMAIN
CREATE TABLE IF NOT EXISTS assets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    symbol VARCHAR(20) UNIQUE NOT NULL,
    asset_name TEXT NOT NULL,
    market_type VARCHAR(20) NOT NULL, -- Stock, Crypto, Forex, MutualFund
    sector VARCHAR(50),
    category VARCHAR(50),
    benchmark_symbol VARCHAR(20),
    expense_ratio NUMERIC(10, 4),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS price_history (
    id BIGSERIAL,
    asset_id UUID REFERENCES assets(id) ON DELETE CASCADE,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    open_price NUMERIC(20, 8),
    high_price NUMERIC(20, 8),
    low_price NUMERIC(20, 8),
    close_price NUMERIC(20, 8),
    volume NUMERIC(30, 8),
    PRIMARY KEY (asset_id, timestamp)
);

-- 3. TRADING DOMAIN
CREATE TABLE IF NOT EXISTS portfolios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    portfolio_name VARCHAR(100) NOT NULL,
    total_value NUMERIC(20, 2) DEFAULT 0.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS holdings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    portfolio_id UUID REFERENCES portfolios(id) ON DELETE CASCADE,
    asset_id UUID REFERENCES assets(id),
    quantity NUMERIC(20, 8) DEFAULT 0,
    average_buy_price NUMERIC(20, 8) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS trades (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    asset_id UUID REFERENCES assets(id),
    trade_type VARCHAR(10) NOT NULL, -- BUY, SELL
    entry_price NUMERIC(20, 8) NOT NULL,
    stop_loss NUMERIC(20, 8),
    take_profit NUMERIC(20, 8),
    quantity NUMERIC(20, 8) NOT NULL,
    pnl NUMERIC(20, 2),
    execution_regime TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 4. AI/ML DOMAIN
CREATE TABLE IF NOT EXISTS models (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS model_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_id UUID REFERENCES models(id),
    version_tag VARCHAR(20) NOT NULL,
    training_window_start TIMESTAMP WITH TIME ZONE,
    training_window_end TIMESTAMP WITH TIME ZONE,
    validation_score NUMERIC(10, 6),
    status VARCHAR(20) DEFAULT 'candidate', -- deployed, candidate, deprecated
    deployed_at TIMESTAMP WITH TIME ZONE,
    artifact_path TEXT, -- Link to bucket/registry
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS predictions (
    id BIGSERIAL PRIMARY KEY,
    asset_id UUID REFERENCES assets(id),
    model_version_id UUID REFERENCES model_versions(id),
    probability_up NUMERIC(10, 6),
    expected_return NUMERIC(10, 6),
    confidence_score NUMERIC(10, 6),
    regime TEXT,
    raw_payload JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS forecasts (
    id BIGSERIAL PRIMARY KEY,
    asset_id UUID REFERENCES assets(id),
    horizon_days INTEGER NOT NULL,
    projected_value NUMERIC(20, 8),
    lower_band NUMERIC(20, 8),
    upper_band NUMERIC(20, 8),
    scenario_type VARCHAR(20), -- bull, base, bear
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 5. GOVERNANCE & AUDIT DOMAIN
CREATE TABLE IF NOT EXISTS audit_logs (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID, -- NULL for system-level actions
    action_type VARCHAR(50) NOT NULL, -- LOGIN, TRADE, MODEL_DEPLOY, CONFIG_CHANGE
    module VARCHAR(50) NOT NULL,
    payload JSONB,
    severity VARCHAR(20) DEFAULT 'info',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS drift_logs (
    id BIGSERIAL PRIMARY KEY,
    model_version_id UUID REFERENCES model_versions(id),
    drift_score NUMERIC(10, 6),
    feature_impact JSONB,
    anomaly_detected BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS circuit_breaker_status (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    module VARCHAR(50) UNIQUE NOT NULL,
    is_tripped BOOLEAN DEFAULT FALSE,
    trip_reason TEXT,
    tripped_at TIMESTAMP WITH TIME ZONE,
    reset_at TIMESTAMP WITH TIME ZONE
);

-- INDEXES FOR PERFORMANCE
CREATE INDEX IF NOT EXISTS idx_price_history_timestamp ON price_history (timestamp);
CREATE INDEX IF NOT EXISTS idx_predictions_asset_id ON predictions (asset_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs (action_type);
CREATE INDEX IF NOT EXISTS idx_trades_user_asset ON trades (user_id, asset_id);
