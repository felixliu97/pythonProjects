/*
ASX Research Pipeline - Decoupled Schema
Treats every table as a standalone entity with NO physical foreign keys.
Ensures data integrity remains in child tables even if parent stocks are deleted.
*/

-- 1. Setup Namespace
DROP SCHEMA IF EXISTS asx CASCADE;
CREATE SCHEMA asx;

-- 2. Core Metadata (Stocks/ETFs)
CREATE TABLE asx.stocks (
    symbol VARCHAR(20) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    industry VARCHAR(255),
    stock_type VARCHAR(50) NOT NULL -- 'growth', 'foundation', 'etf'
);

-- 3. Technical & Momentum Metrics (SCD Type 2)
CREATE TABLE asx.market_trends (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20), -- Logical Link
    current_price DECIMAL(15, 4),
    market_cap BIGINT,
    pe DECIMAL(15, 2),
    yield_val DECIMAL(10, 2),
    score DECIMAL(10, 2) DEFAULT 0,
    price_change_1d DECIMAL(10, 4) DEFAULT 0,
    price_diff_1d DECIMAL(10, 4) DEFAULT 0,
    price_change_5d DECIMAL(10, 4) DEFAULT 0,
    price_history TEXT, -- Store mini sparkline data
    price_diff_5d DECIMAL(10, 4) DEFAULT 0,
    momentum DECIMAL(10, 4) DEFAULT 0,
    volatility DECIMAL(10, 4) DEFAULT 0,
    volume_change DECIMAL(10, 4) DEFAULT 0,
    rsi DECIMAL(10, 2) DEFAULT 50,
    
    market_date DATE NOT NULL,
    valid_from TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    valid_to TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- 4. Fundamental Research (Catalysts)
CREATE TABLE asx.catalyst_masters (
    symbol VARCHAR(20) PRIMARY KEY,
    company VARCHAR(255) NOT NULL,
    sector VARCHAR(255),
    cr_risk VARCHAR(500),
    cr_risk_reason TEXT,
    breakout_probability VARCHAR(500),
    breakout_probability_reason TEXT,
    core_notes TEXT
);

-- 5. Catalyst Line Items (Many-to-One with Master)
CREATE TABLE asx.catalyst_items (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20), -- Logical Link
    item_type VARCHAR(50) NOT NULL, -- 'catalyst', 'risk', 'earnings', 'milestone'
    content TEXT NOT NULL,
    label VARCHAR(200), -- Used for milestone dates/times
    
    valid_from TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    valid_to TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- 6. Announcements (News Feed)
CREATE TABLE asx.announcements (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20), -- Logical Link
    company VARCHAR(255),
    headline VARCHAR(1000) NOT NULL,
    event_date DATE,
    summary TEXT,
    pdf_link VARCHAR(1000),
    rating INTEGER DEFAULT 2,
    unique_key VARCHAR(500) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 7. Placements (Capital Raising)
CREATE TABLE asx.placements (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20), -- Logical Link
    company VARCHAR(255),
    headline VARCHAR(1000) NOT NULL,
    event_date DATE,
    cr_price DECIMAL(15, 4),
    current_price DECIMAL(15, 4),
    price_diff_percent DECIMAL(10, 4),
    pdf_link VARCHAR(1000),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 8. Statistics & Global Indexes
CREATE INDEX idx_trends_symbol ON asx.market_trends(symbol);
CREATE INDEX idx_trends_market_date ON asx.market_trends(market_date);
CREATE INDEX idx_trends_active ON asx.market_trends(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_catalyst_items_symbol ON asx.catalyst_items(symbol);
CREATE INDEX idx_catalyst_items_active ON asx.catalyst_items(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_announcements_symbol ON asx.announcements(symbol);
CREATE INDEX idx_announcements_date ON asx.announcements(event_date);
CREATE INDEX idx_placements_symbol ON asx.placements(symbol);

