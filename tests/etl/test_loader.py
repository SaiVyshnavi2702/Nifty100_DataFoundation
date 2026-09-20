from src.etl.loader import load_all_files


def test_loader_reads_analysis():
    datasets = load_all_files()

    assert len(datasets["analysis"]) == 20
    assert list(datasets["analysis"].columns) == [
        "id",
        "company_id",
        "compounded_sales_growth",
        "compounded_profit_growth",
        "stock_price_cagr",
        "roe",
    ]


def test_loader_reads_balancesheet():
    datasets = load_all_files()

    assert len(datasets["balancesheet"]) == 1225
    assert list(datasets["balancesheet"].columns) == [
        "id",
        "company_id",
        "year",
        "equity_capital",
        "reserves",
        "borrowings",
        "other_liabilities",
        "total_liabilities",
        "fixed_assets",
        "cwip",
        "investments",
        "other_asset",
        "total_assets",
        "period",
    ]


def test_loader_reads_cashflow():
    datasets = load_all_files()

    assert len(datasets["cashflow"]) == 1152
    assert list(datasets["cashflow"].columns) == [
        "id",
        "company_id",
        "year",
        "operating_activity",
        "investing_activity",
        "financing_activity",
        "net_cash_flow",
        "period",
    ]


def test_loader_reads_companies_and_documents():
    datasets = load_all_files()

    assert len(datasets["companies"]) == 100
    assert list(datasets["companies"].columns) == [
        "id",
        "company_logo",
        "company_name",
        "chart_link",
        "about_company",
        "website",
        "nse_profile",
        "bse_profile",
        "face_value",
        "book_value",
        "roce_percentage",
        "roe_percentage",
    ]

    assert len(datasets["documents"]) == 1584
    assert list(datasets["documents"].columns) == [
        "id",
        "company_id",
        "year",
        "annual_report",
        "period",
    ]


def test_loader_reads_profitandloss():
    datasets = load_all_files()

    assert len(datasets["profitandloss"]) == 1263
    assert list(datasets["profitandloss"].columns) == [
        "id",
        "company_id",
        "year",
        "sales",
        "expenses",
        "operating_profit",
        "opm_percentage",
        "other_income",
        "interest",
        "depreciation",
        "profit_before_tax",
        "tax_percentage",
        "net_profit",
        "eps",
        "dividend_payout",
        "period",
    ]


def test_loader_reads_prosandcons_and_peer_groups():
    datasets = load_all_files()

    assert len(datasets["prosandcons"]) == 16
    assert list(datasets["prosandcons"].columns) == [
        "id",
        "company_id",
        "pros",
        "cons",
    ]

    assert len(datasets["peer_groups"]) == 56
    assert list(datasets["peer_groups"].columns) == [
        "id",
        "peer_group_name",
        "company_id",
        "is_benchmark",
    ]


def test_loader_reads_financial_ratios():
    datasets = load_all_files()

    assert len(datasets["financial_ratios"]) == 1065
    assert list(datasets["financial_ratios"].columns) == [
        "id",
        "company_id",
        "year",
        "net_profit_margin_pct",
        "operating_profit_margin_pct",
        "return_on_equity_pct",
        "debt_to_equity",
        "interest_coverage",
        "asset_turnover",
        "free_cash_flow_cr",
        "capex_cr",
        "earnings_per_share",
        "book_value_per_share",
        "dividend_payout_ratio_pct",
        "total_debt_cr",
        "cash_from_operations_cr",
        "period",
    ]


def test_loader_reads_market_cap():
    datasets = load_all_files()

    assert len(datasets["market_cap"]) == 552
    assert list(datasets["market_cap"].columns) == [
        "id",
        "company_id",
        "year",
        "market_cap_crore",
        "enterprise_value_crore",
        "pe_ratio",
        "pb_ratio",
        "ev_ebitda",
        "dividend_yield_pct",
        "period",
    ]


def test_loader_reads_sectors():
    datasets = load_all_files()

    assert len(datasets["sectors"]) == 92
    assert list(datasets["sectors"].columns) == [
        "id",
        "company_id",
        "broad_sector",
        "sub_sector",
        "index_weight_pct",
        "market_cap_category",
    ]


def test_loader_reads_stock_prices():
    datasets = load_all_files()

    assert len(datasets["stock_prices"]) == 5520
    assert list(datasets["stock_prices"].columns) == [
        "id",
        "company_id",
        "date",
        "open_price",
        "high_price",
        "low_price",
        "close_price",
        "volume",
        "adjusted_close",
    ]
