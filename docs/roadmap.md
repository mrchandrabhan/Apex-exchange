# Apex Exchange — Delivery Roadmap

Features are intentionally staged. A checkbox is only complete after implementation and automated verification.

## Phase 0 — Project baseline
- [x] Public repository created
- [x] Project scope and simulation-only safety boundary documented
- [x] Initial architecture and core invariants documented
- [x] Backend and frontend scaffold
- [x] Docker Compose for local development
- [x] API liveness/readiness endpoints and backend smoke tests
- [x] GitHub Actions workflow for backend, Compose, and frontend

## Phase 1 — Deterministic matching engine
- [x] Define Decimal precision and reject binary float inputs in the engine
- [x] Implement order models and validation
- [x] Implement bid and ask books with FIFO queues per price
- [x] Implement price-time priority
- [x] Implement crossing and maker-price trade generation
- [x] Implement partial fills and remaining quantity
- [x] Implement cancellation behavior and order state checks
- [x] Add deterministic unit tests for price/time priority, fills, cancel, replay, and invariants
- [x] Expose simulated order, order-book, and trade REST endpoints
- [x] Add property-based tests over generated order streams
- [x] Connect the Next.js UI to order entry and order-book snapshots

## Phase 2 — Accounts and ledger
- [ ] Seed simulated users and test balances
- [ ] Design accounts, orders, fills, trades, and ledger schema
- [ ] Implement balance reservation/release
- [ ] Implement double-entry posting groups
- [ ] Implement idempotency keys
- [ ] Integrate order acceptance with matching and settlement
- [ ] Add reconciliation tests

## Phase 3 — User-facing trading workflow
- [ ] REST endpoints for accounts and balance views
- [x] Next.js trading interface for synthetic markets, book snapshots, recent trades and test-order entry
- [ ] Open order and trade history views
- [ ] WebSocket trade and order-book updates
- [x] Explicit simulation/test-funds labeling throughout the UI
- [ ] Error and reconnect handling

## Phase 4 — Reliability engineering
- [ ] Concurrent order-submission tests
- [ ] Duplicate request and retry tests
- [ ] Crash/restart and event replay tests
- [ ] Ledger and book reconciliation
- [ ] Load test with reproducible workload
- [ ] p50/p95/p99 latency and throughput report
- [ ] Structured logs and Prometheus metrics
- [ ] Deployment and recovery runbook

## Future enhancements
- [ ] Go matching-engine implementation and benchmark against Python
- [ ] Redis caching where measured to help
- [ ] Transactional outbox and Kafka event distribution
- [ ] Kubernetes and Terraform deployment
- [ ] Multi-market isolation and scaling experiments
- [ ] Chaos testing and SLO/error-budget reporting

## Current implementation boundary

The matching engine and REST order endpoints are in-memory and reset when the API process restarts. The Next.js interface supports synthetic market selection, order-book snapshots, recent simulated trades and limit test-order entry. There is no user account model, balance reservation, durable order persistence, or ledger settlement yet. All orders and trades are simulated test data only.

## Definition of MVP complete

A local simulation can accept limit orders, match them deterministically, partially fill and cancel orders, maintain non-negative available balances, write balanced ledger entries, and stream market updates. Automated tests cover the stated invariants and duplicate-request handling.
