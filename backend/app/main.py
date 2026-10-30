import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.database import engine

app = FastAPI(
    title="Apex Exchange API",
    description="Backend foundation for a simulation-only digital asset exchange.",
    version="0.1.0",
)

origins = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:3001").split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Synthetic fixtures for the initial UI scaffold. These are not live market prices.
DEMO_MARKETS = [
    {
        "symbol": "BTC/USDT",
        "base_asset": "BTC",
        "quote_asset": "USDT",
        "reference_price": "67250.00",
        "data_mode": "SYNTHETIC_DEMO",
    },
    {
        "symbol": "ETH/USDT",
        "base_asset": "ETH",
        "quote_asset": "USDT",
        "reference_price": "3450.00",
        "data_mode": "SYNTHETIC_DEMO",
    },
]


@app.get("/", tags=["system"])
def root() -> dict[str, str]:
    return {"service": "apex-exchange-api", "version": "0.1.0", "docs": "/docs"}


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    """Liveness check: confirms the API process can answer requests."""
    return {"status": "ok", "service": "apex-exchange-api"}


@app.get("/ready", tags=["system"])
def ready() -> dict[str, str]:
    """Readiness check: confirms the API can reach PostgreSQL."""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=503, detail="Database unavailable") from exc
    return {"status": "ready", "database": "connected"}


@app.get("/api/v1/markets", tags=["markets"])
def list_markets() -> dict[str, object]:
    """Return synthetic market fixtures for the initial dashboard."""
    return {"data_mode": "SYNTHETIC_DEMO", "markets": DEMO_MARKETS}
