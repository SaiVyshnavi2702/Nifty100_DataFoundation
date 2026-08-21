-- Exploratory Queries


-- Query 01: Total number of companies
SELECT
    COUNT(*) AS total_companies
FROM companies;


-- Query 02: Companies by broad sector
SELECT
    s.broad_sector,
    COUNT(*) AS company_count
FROM sectors s
GROUP BY s.broad_sector
ORDER BY company_count DESC, s.broad_sector;


-- Query 03: Companies with the most financial history
SELECT
    c.id AS company_id,
    c.company_name,
    COUNT(DISTINCT p.period) AS pnl_periods
FROM companies c
LEFT JOIN profitandloss p
    ON p.company_id = c.id
GROUP BY c.id, c.company_name
ORDER BY pnl_periods DESC, c.company_name
LIMIT 20;


-- Query 04: Latest available P&L for each company
SELECT
    c.company_name,
    p.period,
    p.sales,
    p.operating_profit,
    p.opm_percentage,
    p.net_profit,
    p.eps
FROM companies c
JOIN profitandloss p
    ON p.company_id = c.id
WHERE p.period = (
    SELECT MAX(p2.period)
    FROM profitandloss p2
    WHERE p2.company_id = p.company_id
)
ORDER BY p.sales DESC
LIMIT 20;


-- Query 05: Companies with the highest sales
SELECT
    c.company_name,
    p.period,
    p.sales,
    p.net_profit
FROM profitandloss p
JOIN companies c
    ON c.id = p.company_id
WHERE p.sales IS NOT NULL
ORDER BY p.sales DESC
LIMIT 20;


-- Query 06: Highest operating profit margins
SELECT
    c.company_name,
    p.period,
    p.sales,
    p.operating_profit,
    p.opm_percentage
FROM profitandloss p
JOIN companies c
    ON c.id = p.company_id
WHERE p.opm_percentage IS NOT NULL
ORDER BY p.opm_percentage DESC
LIMIT 20;


-- Query 07: Highest return on equity
SELECT
    c.company_name,
    f.period,
    f.return_on_equity_pct,
    f.net_profit_margin_pct,
    f.debt_to_equity
FROM financial_ratios f
JOIN companies c
    ON c.id = f.company_id
WHERE f.return_on_equity_pct IS NOT NULL
ORDER BY f.return_on_equity_pct DESC
LIMIT 20;


-- Query 08: Companies with positive operating cash flow
SELECT
    c.company_name,
    cf.period,
    cf.operating_activity,
    cf.investing_activity,
    cf.financing_activity,
    cf.net_cash_flow
FROM cashflow cf
JOIN companies c
    ON c.id = cf.company_id
WHERE cf.operating_activity > 0
ORDER BY cf.operating_activity DESC
LIMIT 20;


-- Query 09: Stock-price summary by company
SELECT
    c.company_name,
    COUNT(sp.date) AS trading_days,
    MIN(sp.close_price) AS lowest_close,
    MAX(sp.close_price) AS highest_close,
    AVG(sp.close_price) AS average_close
FROM stock_prices sp
JOIN companies c
    ON c.id = sp.company_id
GROUP BY c.id, c.company_name
ORDER BY average_close DESC
LIMIT 20;


-- Query 10: Financial health overview
SELECT
    c.company_name,
    f.period,
    f.net_profit_margin_pct,
    f.operating_profit_margin_pct,
    f.return_on_equity_pct,
    f.debt_to_equity,
    f.interest_coverage,
    f.earnings_per_share
FROM financial_ratios f
JOIN companies c
    ON c.id = f.company_id
WHERE f.period = (
    SELECT MAX(f2.period)
    FROM financial_ratios f2
    WHERE f2.company_id = f.company_id
)
ORDER BY f.return_on_equity_pct DESC
LIMIT 20;