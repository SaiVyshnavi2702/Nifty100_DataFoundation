PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS stock_prices;
DROP TABLE IF EXISTS market_cap;
DROP TABLE IF EXISTS financial_ratios;
DROP TABLE IF EXISTS cashflow;
DROP TABLE IF EXISTS profitandloss;
DROP TABLE IF EXISTS balancesheet;
DROP TABLE IF EXISTS documents;
DROP TABLE IF EXISTS prosandcons;
DROP TABLE IF EXISTS analysis;
DROP TABLE IF EXISTS peer_groups;
DROP TABLE IF EXISTS sectors;
DROP TABLE IF EXISTS companies;


CREATE TABLE companies (
    id TEXT PRIMARY KEY,
    company_logo TEXT,
    company_name TEXT NOT NULL,
    chart_link TEXT,
    about_company TEXT,
    website TEXT,
    nse_profile TEXT,
    bse_profile TEXT,
    face_value REAL,
    book_value REAL,
    roce_percentage REAL,
    roe_percentage REAL
);


CREATE TABLE sectors (
    id INTEGER PRIMARY KEY,
    company_id TEXT NOT NULL,
    broad_sector TEXT,
    sub_sector TEXT,
    index_weight_pct REAL,
    market_cap_category TEXT,

    FOREIGN KEY (company_id)
        REFERENCES companies(id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,

    UNIQUE(company_id)
);


CREATE TABLE peer_groups (
    id INTEGER PRIMARY KEY,
    peer_group_name TEXT NOT NULL,
    company_id TEXT NOT NULL,
    is_benchmark INTEGER NOT NULL DEFAULT 0
        CHECK (is_benchmark IN (0, 1)),

    FOREIGN KEY (company_id)
        REFERENCES companies(id)
        ON UPDATE CASCADE
        ON DELETE CASCADE
);


CREATE TABLE analysis (
    id INTEGER PRIMARY KEY,
    company_id TEXT NOT NULL,
    compounded_sales_growth REAL,
    compounded_profit_growth REAL,
    stock_price_cagr REAL,
    roe REAL,

    FOREIGN KEY (company_id)
        REFERENCES companies(id)
        ON UPDATE CASCADE
        ON DELETE CASCADE
);


CREATE TABLE balancesheet (
    id INTEGER PRIMARY KEY,
    company_id TEXT NOT NULL,
    year INTEGER,
    period TEXT NOT NULL,

    equity_capital REAL,
    reserves REAL,
    borrowings REAL,
    other_liabilities REAL,
    total_liabilities REAL,
    fixed_assets REAL,
    cwip REAL,
    investments REAL,
    other_asset REAL,
    total_assets REAL,

    FOREIGN KEY (company_id)
        REFERENCES companies(id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,

    UNIQUE(company_id, period)
);


CREATE TABLE profitandloss (
    id INTEGER PRIMARY KEY,
    company_id TEXT NOT NULL,
    year INTEGER,
    period TEXT NOT NULL,

    sales REAL,
    expenses REAL,
    operating_profit REAL,
    opm_percentage REAL,
    other_income REAL,
    interest REAL,
    depreciation REAL,
    profit_before_tax REAL,
    tax_percentage REAL,
    net_profit REAL,
    eps REAL,
    dividend_payout REAL,

    FOREIGN KEY (company_id)
        REFERENCES companies(id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,

    UNIQUE(company_id, period)
);


CREATE TABLE cashflow (
    id INTEGER PRIMARY KEY,
    company_id TEXT NOT NULL,
    year INTEGER,
    period TEXT NOT NULL,

    operating_activity REAL,
    investing_activity REAL,
    financing_activity REAL,
    net_cash_flow REAL,

    FOREIGN KEY (company_id)
        REFERENCES companies(id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,

    UNIQUE(company_id, period)
);


CREATE TABLE financial_ratios (
    id INTEGER PRIMARY KEY,
    company_id TEXT NOT NULL,
    year INTEGER,
    period TEXT NOT NULL,

    net_profit_margin_pct REAL,
    operating_profit_margin_pct REAL,
    return_on_equity_pct REAL,
    debt_to_equity REAL,
    interest_coverage REAL,
    asset_turnover REAL,
    free_cash_flow_cr REAL,
    capex_cr REAL,
    earnings_per_share REAL,
    book_value_per_share REAL,
    dividend_payout_ratio_pct REAL,
    total_debt_cr REAL,
    cash_from_operations_cr REAL,

    FOREIGN KEY (company_id)
        REFERENCES companies(id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,

    UNIQUE(company_id, period)
);


CREATE TABLE market_cap (
    id INTEGER PRIMARY KEY,
    company_id TEXT NOT NULL,
    year INTEGER,
    period TEXT NOT NULL,

    market_cap_crore REAL,
    enterprise_value_crore REAL,
    pe_ratio REAL,
    pb_ratio REAL,
    ev_ebitda REAL,
    dividend_yield_pct REAL,

    FOREIGN KEY (company_id)
        REFERENCES companies(id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,

    UNIQUE(company_id, period)
);


CREATE TABLE stock_prices (
    id INTEGER PRIMARY KEY,
    company_id TEXT NOT NULL,
    date TEXT NOT NULL,

    open_price REAL,
    high_price REAL,
    low_price REAL,
    close_price REAL,
    volume INTEGER,
    adjusted_close REAL,

    FOREIGN KEY (company_id)
        REFERENCES companies(id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,

    UNIQUE(company_id, date)
);


CREATE TABLE documents (
    id INTEGER PRIMARY KEY,
    company_id TEXT NOT NULL,
    year INTEGER,
    period TEXT,
    annual_report TEXT,

    FOREIGN KEY (company_id)
        REFERENCES companies(id)
        ON UPDATE CASCADE
        ON DELETE CASCADE
);



CREATE TABLE prosandcons (
    id INTEGER PRIMARY KEY,
    company_id TEXT NOT NULL,
    pros TEXT,
    cons TEXT,

    FOREIGN KEY (company_id)
        REFERENCES companies(id)
        ON UPDATE CASCADE
        ON DELETE CASCADE
);


CREATE INDEX idx_sectors_company
    ON sectors(company_id);

CREATE INDEX idx_peer_groups_company
    ON peer_groups(company_id);

CREATE INDEX idx_analysis_company
    ON analysis(company_id);

CREATE INDEX idx_balancesheet_company_period
    ON balancesheet(company_id, period);

CREATE INDEX idx_profitandloss_company_period
    ON profitandloss(company_id, period);

CREATE INDEX idx_cashflow_company_period
    ON cashflow(company_id, period);

CREATE INDEX idx_financial_ratios_company_period
    ON financial_ratios(company_id, period);

CREATE INDEX idx_market_cap_company_period
    ON market_cap(company_id, period);

CREATE INDEX idx_stock_prices_company_date
    ON stock_prices(company_id, date);

CREATE INDEX idx_documents_company
    ON documents(company_id);

CREATE INDEX idx_prosandcons_company
    ON prosandcons(company_id);
