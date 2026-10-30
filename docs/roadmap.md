# Apex Exchange — Delivery Roadmap

Features are intentionally staged. A checkbox is only complete after implementation and automated verification.

## Phase 0 — Project baseline
- [x] Public repository created
- [x] Project scope and simulation-only safety boundary documented
- [x] Initial architecture and core invariants documented
- [x] Add backend and frontend scaffold
- [x] Add Docker Compose for local development
- [x] Add API liveness/readiness endpoints and backend smoke tests
- [ ] Add linting, formatting, and CI

## Phase 1 — Deterministic matching engine
- [ ] Define asset/market precision and Decimal types
- [ ] Implement order models and validation
- [ ] Implement bid and ask books
- [ ] Implement price-time priority
- [ ] Implement crossing and trade generation
- [ ] Implement partial fills and remaining quantity
- [ ] Implement cancellation behavior
- [ ] Add deterministic unit tests and property-based invariants

## Phase 2 — Accounts and ledger
- [ ] Seed simulated users and test balances
- [ ] Design accounts, orders, fills, trades, and ledger schema
- [ ] Implement balance reservation/release
- [ ] Implement double-entry posting groups
- [ ] Implement idempotency keys
- [ ] Integrate order acceptance with matching and settlement
- [ ] Add reconciliation tests

## Phase 3 — User-facing trading workflow
- [ ] REST endpoints for accounts, orders, trades, and book snapshots
- [ ] Next.js trading interface
- [ ] Open order and trade history views
- [ ] WebSocket trade and order-book updates
- [ ] Explicit test-funds labeling throughout the UI
- [ ] Error and reconnect handling

## Phase 4 — Reliability engineering
- [ ] Concurrent order-submission tests
- [ ] Duplicate request and retry tests
- [ ] Crash/restart and event replay tests
- [ ] Ledger and book reconciliation
- [ ] Load test with reproducible workload
- [ ] p50/p95/p99 latency and throughput report
- [ ] Structured logs and Prometheus metrics
- [ ] Docker Compose and CI workflow
- [ ] Deployment and recovery runbook

## Future enhancements
- [ ] Go matching-engine implementation and benchmark against Python
- [ ] Redis caching where measured to help
- [ ] Transactional outbox and Kafka event distribution
- [ ] Kubernetes and Terraform deployment
- [ ] Multi-market isolation and scaling experiments
- [ ] Chaos testing and SLO/error-budget reporting

## Definition of MVP complete

A local or deployed simulation can accept limit orders, match them deterministically, partially fill and cancel orders, maintain non-negative available balances, write balanced ledger entries, and stream market updates. Automated tests cover the stated invariants and duplicate-request handling.
