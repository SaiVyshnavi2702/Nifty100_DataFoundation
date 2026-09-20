import sqlite3
from pathlib import Path
from urllib.parse import urlparse

from fastapi import APIRouter, HTTPException

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parents[3]
DB_PATH = BASE_DIR / "data" / "nifty100.db"


def is_valid_url(url):
    if not url:
        return False

    try:
        parsed = urlparse(url)
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)
    except Exception:
        return False


@router.get("/companies/{ticker}/documents")
def get_company_documents(ticker: str):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    query = """
        SELECT
            company_id,
            year,
            period,
            annual_report
        FROM documents
        WHERE UPPER(company_id) = UPPER(?)
        ORDER BY year DESC
    """

    rows = conn.execute(query, (ticker,)).fetchall()

    conn.close()

    if not rows:
        raise HTTPException(
            status_code=404,
            detail="Company documents not found",
        )

    documents = []

    for row in rows:
        documents.append(
            {
                "company_id": row["company_id"],
                "year": row["year"],
                "period": row["period"],
                "annual_report": row["annual_report"],
                "is_url_valid": is_valid_url(row["annual_report"]),
            }
        )

    return documents    