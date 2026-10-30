import os

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.database import engine
from app.matching.exchange import SimulatedExchange
from app.matching.models import MatchingError, Order, OrderNotFound, OrderNotOpen, Trade
from app.matching.schemas import OrderCreate

app = FastAPI(
    title="Apex Exchange API",
    description=(
        "Simulation-only exchange API with a deterministic in-memory limit order "
        "matching engine. No real funds or live trading."
    ),
    version="0.2.0",
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

# Synthetic fixtures only. These are not live prices or executable external markets.
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

EXCHANGE = SimulatedExchange([market["symbol"] for market in DEMO_MARKETS])


def order_payload(order: Order) -> dict:
    return {
        "order_id": order.order_id,
        "symbol": order.symbol,
        "side": order.side.value,
        "price": str(order.price),
        "quantity": str(order.quantity),
        "filled_quantity": str(order.filled_quantity),
        "remaining_quantity": str(order.remaining_quantity),
        "sequence": order.sequence,
        "status": order.status.value,
    }


def trade_payload(trade: Trade) -> dict:
    return {
        "trade_id": trade.trade_id,
        "symbol": trade.symbol,
        "price": str(trade.price),
        "quantity": str(trade.quantity),
        "buy_order_id": trade.buy_order_id,
        "sell_order_id": trade.sell_order_id,
        "maker_order_id": trade.maker_order_id,
        "taker_order_id": trade.taker_order_id,
        "sequence": trade.sequence,
        "data_mode": "SYNTHETIC_DEMO",
    }


@app.get("/", tags=["system"])
def root() -> dict[str, str]:
    return {"service": "apex-exchange-api", "version": "0.2.0", "docs": "/docs"}


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
    """Return synthetic market fixtures. These are not live reference prices."""
    return {"data_mode": "SYNTHETIC_DEMO", "markets": DEMO_MARKETS}


@app.post("/api/v1/orders", status_code=status.HTTP_201_CREATED, tags=["orders"])
def submit_order(request: OrderCreate) -> dict:
    try:
        order, trades = EXCHANGE.submit(
            request.order_id,
            request.symbol,
            request.side.value,
            request.price,
            request.quantity,
        )
    except MatchingError as exc:
        if str(exc).startswith("Unknown market"):
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return {
        "data_mode": "SYNTHETIC_DEMO",
        "order": order_payload(order),
        "trades": [trade_payload(trade) for trade in trades],
    }


@app.get("/api/v1/orders/{order_id}", tags=["orders"])
def get_order(order_id: str) -> dict:
    try:
        order = EXCHANGE.get_order(order_id)
    except MatchingError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"data_mode": "SYNTHETIC_DEMO", "order": order_payload(order)}


@app.delete("/api/v1/orders/{order_id}", tags=["orders"])
def cancel_order(order_id: str) -> dict:
    try:
        order = EXCHANGE.cancel(order_id)
    except OrderNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except OrderNotOpen as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except MatchingError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"data_mode": "SYNTHETIC_DEMO", "order": order_payload(order)}


@app.get("/api/v1/orderbook/{symbol:path}", tags=["markets"])
def get_order_book(symbol: str, depth: int = 20) -> dict:
    try:
        snapshot = EXCHANGE.get_book(symbol).snapshot(depth=depth)
    except MatchingError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"data_mode": "SYNTHETIC_DEMO", **snapshot}


@app.get("/api/v1/trades/{symbol:path}", tags=["markets"])
def list_trades(symbol: str, limit: int = 50) -> dict:
    if limit < 1 or limit > 500:
        raise HTTPException(status_code=422, detail="limit must be between 1 and 500.")
    try:
        book = EXCHANGE.get_book(symbol)
    except MatchingError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    trades = [trade_payload(trade) for trade in book.trades[-limit:]]
    return {"data_mode": "SYNTHETIC_DEMO", "symbol": book.symbol, "trades": trades}
