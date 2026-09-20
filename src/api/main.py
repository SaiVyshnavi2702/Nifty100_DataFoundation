
import sqlite3
import time
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from src.api.routers import (
    companies,
    screener,
    sectors,    
    peers,
    valuation,
    portfolio,
    documents,
    health,
)

BASE_DIR = Path(__file__).resolve().parents[2]
DB_PATH = BASE_DIR / "data" / "nifty100.db"

START_TIME = time.time()
VERSION = "1.0.0"


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


app = FastAPI(
    title="Nifty 100 Data Foundation API",
    version=VERSION,
)

app.state.start_time = START_TIME


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()

    response = await call_next(request)

    elapsed = time.time() - start

    print(
        f"{request.method} {request.url.path} "
        f"{response.status_code} {elapsed:.4f}s"
    )

    return response


app.include_router(companies.router, prefix="/api/v1")
app.include_router(screener.router, prefix="/api/v1")
app.include_router(sectors.router, prefix="/api/v1")
app.include_router(peers.router, prefix="/api/v1")
app.include_router(valuation.router, prefix="/api/v1")
app.include_router(portfolio.router, prefix="/api/v1")
app.include_router(documents.router, prefix="/api/v1")
app.include_router(health.router, prefix="/api/v1")


@app.get("/")
def root():
    return {
        "message": "Nifty 100 Data Foundation API",
        "version": VERSION,
    }

