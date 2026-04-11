-- 1. CLEANUP
DROP SCHEMA IF EXISTS asx CASCADE;

-- 2. SCHEMA AND TABLES
CREATE SCHEMA IF NOT EXISTS asx;

-- CORE METADATA
CREATE TABLE IF NOT EXISTS asx.stocks (
    symbol VARCHAR(20) NOT NULL, 
    name VARCHAR(255), 
    industry VARCHAR(255), 
    stock_type VARCHAR(50), 
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now(), 
    PRIMARY KEY (symbol)
);
CREATE INDEX IF NOT EXISTS ix_stocks_symbol ON asx.stocks (symbol);

-- TECHNICAL HISTORY (Temporal)
CREATE TABLE IF NOT EXISTS asx.market_trends (
    id SERIAL NOT NULL, 
    symbol VARCHAR(20), 
    current_price FLOAT, 
    market_cap BIGINT, 
    pe FLOAT, 
    ps FLOAT, 
    yield_val FLOAT, 
    score FLOAT, 
    price_change_1d FLOAT, 
    price_diff_1d FLOAT, 
    price_change_5d FLOAT, 
    price_diff_5d FLOAT, 
    momentum FLOAT, 
    volatility FLOAT, 
    volume_change FLOAT, 
    rsi FLOAT, 
    market_date DATE,
    valid_from TIMESTAMP WITHOUT TIME ZONE DEFAULT now(), 
    valid_to TIMESTAMP WITHOUT TIME ZONE, 
    is_active BOOLEAN DEFAULT TRUE, 
    PRIMARY KEY (id), 
    FOREIGN KEY(symbol) REFERENCES asx.stocks (symbol) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS ix_market_trends_symbol ON asx.market_trends (symbol);
CREATE INDEX IF NOT EXISTS ix_market_trends_is_active ON asx.market_trends (is_active);
CREATE INDEX IF NOT EXISTS ix_market_trends_market_date ON asx.market_trends (market_date);

-- FUNDAMENTAL METADATA
CREATE TABLE IF NOT EXISTS asx.catalyst_masters (
    symbol VARCHAR(20) NOT NULL, 
    company VARCHAR(255), 
    sector VARCHAR(255), 
    cr_risk VARCHAR(500), 
    probability VARCHAR(500), 
    core_notes TEXT, 
    PRIMARY KEY (symbol), 
    FOREIGN KEY(symbol) REFERENCES asx.stocks (symbol) ON DELETE CASCADE
);

-- CONSOLIDATED ANALYSIS ITEMS (SCD Type 2)
CREATE TABLE IF NOT EXISTS asx.catalyst_items (
    id SERIAL NOT NULL, 
    symbol VARCHAR(20), 
    item_type VARCHAR(50), -- catalyst, risk, earnings, milestone
    content TEXT NOT NULL, 
    label VARCHAR(200), -- time labels for milestones
    valid_from TIMESTAMP WITHOUT TIME ZONE DEFAULT now(), 
    valid_to TIMESTAMP WITHOUT TIME ZONE, 
    is_active BOOLEAN DEFAULT TRUE, 
    PRIMARY KEY (id), 
    FOREIGN KEY(symbol) REFERENCES asx.catalyst_masters (symbol) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS ix_catalyst_items_symbol ON asx.catalyst_items (symbol);
CREATE INDEX IF NOT EXISTS ix_catalyst_items_item_type ON asx.catalyst_items (item_type);
CREATE INDEX IF NOT EXISTS ix_catalyst_items_is_active ON asx.catalyst_items (is_active);

-- SCRAPED CORPORATE EVENTS
CREATE TABLE IF NOT EXISTS asx.announcements (
    id SERIAL NOT NULL, 
    symbol VARCHAR(20), 
    company VARCHAR(255), 
    headline VARCHAR(1000), 
    event_date DATE, 
    summary TEXT, 
    pdf_link VARCHAR(1000), 
    rating INTEGER, 
    unique_key VARCHAR(500), 
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now(), 
    PRIMARY KEY (id), 
    FOREIGN KEY(symbol) REFERENCES asx.stocks (symbol) ON DELETE CASCADE,
    UNIQUE (unique_key)
);
CREATE INDEX IF NOT EXISTS ix_announcements_symbol ON asx.announcements (symbol);
CREATE INDEX IF NOT EXISTS ix_announcements_event_date ON asx.announcements (event_date);

CREATE TABLE IF NOT EXISTS asx.placements (
    id SERIAL NOT NULL, 
    symbol VARCHAR(20), 
    company VARCHAR(255), 
    headline VARCHAR(1000), 
    event_date DATE, 
    cr_price FLOAT, 
    current_price FLOAT, 
    price_diff_percent FLOAT, 
    pdf_link VARCHAR(1000), 
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now(), 
    PRIMARY KEY (id), 
    FOREIGN KEY(symbol) REFERENCES asx.stocks (symbol) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS ix_placements_symbol ON asx.placements (symbol);
CREATE INDEX IF NOT EXISTS ix_placements_event_date ON asx.placements (event_date);
