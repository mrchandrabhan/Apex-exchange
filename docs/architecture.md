# Apex Exchange — Architecture Notes

> Design baseline for a simulated exchange. This document does not describe a production financial system.

## Initial topology

Start with a modular monolith to preserve simple transaction boundaries while the domain rules are being validated. Separate modules for identity, accounts, orders, matching, ledger, and market data. A single-writer matching loop processes each market's commands in a deterministic sequence.

## Order lifecycle

1. Authenticate the user and validate the trading pair and order parameters.
2. Check idempotency key and reject duplicate request submissions.
3. Validate available balance and reserve the required quote/base asset.
4. Enqueue the order command for the relevant market's matching loop.
5. Apply price-time priority against the opposite side of the book.
6. Produce zero or more fills; update remaining quantity and order status.
7. Persist order/fill state and balanced ledger postings using a defined transaction strategy.
8. Publish committed market events to WebSocket subscribers.

The exact transaction boundary between in-memory matching state and durable database state must be specified and tested before the exchange is considered correct. The MVP should use an append-only command/event journal or a transactionally persisted state transition so restart recovery can rebuild the book without inventing fills.

## Core invariants

- Available balance cannot become negative.
- Every trade has a buyer, seller, price, quantity, and unique trade identifier.
- Total base and quote quantities on both sides of a fill agree.
- Ledger debits and credits balance for each posting group.
- A canceled order cannot match after its cancellation is acknowledged.
- A duplicate client request cannot create another order or settlement.
- An order's cumulative filled quantity cannot exceed its original quantity.
- Replaying committed events must reconstruct the same order-book state.

## Ordering and concurrency

For the MVP, serialize commands per market through a single-writer loop. Parallelize across independent markets only after market state is isolated. Do not allow multiple API workers to mutate one order book concurrently.

## Persistence and recovery

Persist accepted commands and resulting events with stable identifiers and sequence numbers. Recovery should replay the durable sequence into an empty book, then reconcile open-order reservations and ledger balances. Add crash-injection tests around acceptance, matching, settlement, and event publication.

Use an outbox or equivalent durable publication mechanism before introducing asynchronous brokers. A broker is not a substitute for transaction correctness.

## Numeric representation

Use Decimal in Python or integer-scaled fixed-point values. Define supported precision per asset and market. Validate rounding at API boundaries and never use float for balances, price, or quantity.

## Observability

Track request rate, rejection reasons, order acceptance latency, matching latency, fills per second, open orders, queue depth, ledger reconciliation failures, WebSocket connections, and recovery duration. Report benchmark workload and environment alongside results.
