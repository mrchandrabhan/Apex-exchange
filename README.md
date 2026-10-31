# Apex Exchange — Simulated Digital Asset Exchange

> **Status: Deterministic in-memory matching engine, REST API, Docker Compose stack and Next.js test-order dashboard implemented; simulated balances, ledger and durable exchange state remain in progress.**

[![CI](https://github.com/mrchandrabhan/Apex-exchange/actions/workflows/ci.yml/badge.svg)](https://github.com/mrchandrabhan/Apex-exchange/actions/workflows/ci.yml)

Apex Exchange is a portfolio project exploring the backend and reliability engineering behind an exchange-style matching system. It is a **simulation only**: every order and trade uses test data in a local, in-memory engine.

**Repository:** https://github.com/mrchandrabhan/Apex-exchange  
**Portfolio:** https://mrchandrabhan.github.io/

## Implemented functionality

| Capability | Status |
|---|---|
| Project scope and simulation-only boundary | Published |
| Decimal-based limit-order validation | Implemented |
| Bid and ask books with FIFO price levels | Implemented |
| Price-time priority | Implemented |
| Crossing orders and maker-price trades | Implemented |
| Partial fills and remaining quantities | Implemented |
| Order cancellation and state validation | Implemented |
| Deterministic replay and book invariants | Unit-tested |
| REST order, order-book, and trade endpoints | Implemented |
| Simulated accounts and balance reservations | Next milestone |
| Double-entry ledger and durable persistence | Planned |
| WebSocket market updates | Planned |

## Matching engine

The engine is a pure Python domain package under `backend/app/matching`. It keeps one book per market, applies better-price-first matching and FIFO within a price level, and executes at the resting maker's price. All price and quantity arithmetic uses `Decimal`; the engine rejects binary float inputs and values with more than eight decimal places.

### Example

A sell order rests at 100.00 for 2 units. A buy order arrives at 105.00 for 1 unit. The buy crosses the ask and executes 1 unit at the resting sell price of 100.00. The ask remains open with 1 unit.

## REST API

Open http://localhost:8100/docs.

- `POST /api/v1/orders` — submit a simulated limit order.
- `GET /api/v1/orders/{order_id}` — inspect an order.
- `DELETE /api/v1/orders/{order_id}` — cancel an open or partially filled order.
- `GET /api/v1/orderbook/{symbol}` — get aggregated bid/ask levels.
- `GET /api/v1/trades/{symbol}` — list recent simulated trades.
- `GET /api/v1/markets` — synthetic market fixtures.

Example request:

```json
{
  "order_id": "demo-ask-001",
  "symbol": "BTC/USDT",
  "side": "SELL",
  "price": "67200.00",
  "quantity": "0.025"
}
```

Send prices and quantities as JSON strings to preserve decimal precision. API responses contain `data_mode: SYNTHETIC_DEMO`.

## Run locally

From the repository root:

```powershell
docker compose up --build -d
docker compose ps
```

Open:
- Web application: http://localhost:3001
- API documentation: http://localhost:8100/docs
- API liveness: http://localhost:8100/health
- API/database readiness: http://localhost:8100/ready

Run backend tests:

```powershell
docker compose exec backend pytest -q
```

The matching engine is currently in-memory and resets when the backend restarts. It runs as a single process only; do not horizontally scale this version.

## Safety and scope

This is **not** a real exchange. It has no real-money deposits, withdrawals, custody, wallet keys, blockchain transactions, or live execution. No external market prices are consumed. All balances and trades are simulated test data.

See [docs/architecture.md](docs/architecture.md) and [docs/roadmap.md](docs/roadmap.md) for the current design and next stages.
