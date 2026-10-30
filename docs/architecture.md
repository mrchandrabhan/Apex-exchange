# Apex Exchange — Architecture Notes

> The current matching engine is an in-memory simulation for correctness and learning. It is not a production financial system.

## Current topology

The FastAPI service owns a process-local `SimulatedExchange` with one independent `OrderBook` per demo market. The engine processes each submitted order synchronously within the API process. PostgreSQL remains available in the scaffold but is not yet the source of truth for matching state.

## Matching rules implemented

1. Each order receives a monotonically increasing acceptance sequence.
2. The best bid is the highest buy price; the best ask is the lowest sell price.
3. A buy crosses when its limit price is at least the best ask. A sell crosses when its limit price is no greater than the best bid.
4. Better prices execute before worse prices.
5. At one price level, orders execute FIFO by acceptance sequence.
6. Trades execute at the resting maker order's price.
7. The matched quantity is the smaller of the incoming and resting remaining quantities.
8. A partially filled resting order stays at the head of its price-level queue; a residual incoming order rests at the tail of its own price-level queue.
9. Canceled and filled orders cannot be canceled or matched again.

## Current API

- `POST /api/v1/orders` — submit a simulated limit order.
- `GET /api/v1/orders/{order_id}` — inspect order state and remaining quantity.
- `DELETE /api/v1/orders/{order_id}` — cancel an open or partially filled order.
- `GET /api/v1/orderbook/{symbol}` — retrieve aggregated bid/ask levels.
- `GET /api/v1/trades/{symbol}` — retrieve recent simulated trades.

All order, book, and trade responses include `data_mode: SYNTHETIC_DEMO`.

## Numeric representation

Prices and quantities use Python `Decimal`. The domain engine rejects binary float inputs, non-finite values, non-positive values, and precision beyond eight decimal places. API clients should send decimal values as JSON strings to preserve exact decimal intent.

## Invariants covered by tests

- The book cannot remain crossed after a matching command.
- A better price wins over a worse price.
- Equal-price orders preserve FIFO acceptance order.
- Filled quantity never exceeds original order quantity.
- Remaining quantity is reduced exactly by generated fills.
- A canceled order is removed from the active book.
- Each generated trade links one buy and one sell order.
- Replaying the same command sequence produces the same trades and book snapshot.

## Important limitations

- The book is in memory and local to one process. Restarting the API clears orders and trades.
- There is no authentication, user account, balance reservation, or ledger settlement yet.
- Multiple API workers would have independent books; do not scale the API horizontally in this state.
- Order acceptance and trade generation are not durable transactions.
- No real funds, deposits, withdrawals, custody, wallet keys, blockchain transactions, or live trading are supported.

## Next architecture steps

Add simulated accounts and a transactional double-entry ledger. Then persist commands and execution events so deterministic replay can rebuild the book after a restart. Only after defining those consistency boundaries should concurrent multi-worker processing or a WebSocket market-data stream be added.
