"use client";

import { useEffect, useState } from "react";

type ApiState = "checking" | "online" | "offline";
type Market = {
  symbol: string;
  base_asset: string;
  quote_asset: string;
  reference_price: string;
  data_mode: string;
};

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8100";

export default function Home() {
  const [apiState, setApiState] = useState<ApiState>("checking");
  const [markets, setMarkets] = useState<Market[]>([]);
  const [message, setMessage] = useState("Connecting to API…");

  async function loadStatus() {
    setApiState("checking");
    setMessage("Connecting to API…");
    try {
      const [healthResponse, marketsResponse] = await Promise.all([
        fetch(`${API_BASE}/ready`, { cache: "no-store" }),
        fetch(`${API_BASE}/api/v1/markets`, { cache: "no-store" })
      ]);
      if (!healthResponse.ok || !marketsResponse.ok) throw new Error("API unavailable");
      const health = await healthResponse.json();
      const marketData = await marketsResponse.json();
      setMarkets(marketData.markets ?? []);
      setApiState("online");
      setMessage(`API connected · Database ${health.database ?? "ready"}`);
    } catch {
      setApiState("offline");
      setMessage("API unavailable — start the Docker Compose stack.");
    }
  }

  useEffect(() => {
    void loadStatus();
  }, []);

  return (
    <main className="app-shell">
      <header className="topbar">
        <a className="brand" href="/"><span className="brand-mark">A</span> APEX <small>EXCHANGE</small></a>
        <nav><a className="selected" href="#markets">Markets</a><a href="#engine">Engine</a><a href="#system">System status</a></nav>
        <span className="mode-pill">PAPER TRADING SIMULATION</span>
      </header>

      <section className="notice"><span>SIMULATION ONLY</span> Test balances and synthetic reference prices. No real assets, deposits, withdrawals, or live trading.</section>

      <div className="page-content">
        <div className="page-heading">
          <div><span className="eyebrow">ENGINEERING SANDBOX / BUILD 0.1.0</span><h1>Market overview</h1><p>A centralized exchange simulation focused on deterministic order matching and ledger correctness.</p></div>
          <button className="refresh" onClick={() => void loadStatus()}>↻ Refresh status</button>
        </div>

        <div className="system-strip" id="system">
          <span className="pulse" data-state={apiState} />
          <strong>{apiState === "online" ? "SYSTEM ONLINE" : apiState === "offline" ? "SYSTEM OFFLINE" : "CHECKING SYSTEM"}</strong>
          <span>{message}</span>
        </div>

        <section id="markets">
          <div className="section-title"><div><span className="eyebrow">SYNTHETIC REFERENCE DATA</span><h2>Markets</h2></div><span className="small-label">NOT LIVE PRICES</span></div>
          <div className="market-grid">
            {markets.length ? markets.map((market) => (
              <article className="market-card" key={market.symbol}>
                <div className="pair"><span className="coin">{market.base_asset.slice(0, 1)}</span><span><strong>{market.symbol}</strong><small>{market.base_asset} / {market.quote_asset}</small></span></div>
                <div className="price">{market.reference_price}<small>{market.quote_asset}</small></div>
                <span className="demo-label">{market.data_mode}</span>
              </article>
            )) : (
              <article className="market-card empty"><strong>{apiState === "offline" ? "Waiting for API" : "Loading markets…"}</strong><span>Market fixtures are served by the backend.</span></article>
            )}
          </div>
        </section>

        <div className="trading-grid" id="engine">
          <section className="panel">
            <div className="panel-heading"><div><span className="eyebrow">CORE COMPONENT</span><h2>Order book</h2></div><span className="build-badge">NEXT MILESTONE</span></div>
            <div className="book-head"><span>PRICE (USDT)</span><span>AMOUNT (BTC)</span><span>TOTAL</span></div>
            <div className="empty-state"><div className="book-icon">⇅</div><strong>Matching engine scaffolded next</strong><p>The order book, price-time priority, partial fills and cancellation flow will be implemented in the next milestone.</p></div>
          </section>
          <section className="panel">
            <div className="panel-heading"><div><span className="eyebrow">PLATFORM ROADMAP</span><h2>Exchange services</h2></div></div>
            <div className="service-row"><span className="service-icon">⌁</span><span><strong>Order management</strong><small>Order validation and lifecycle</small></span><em>PLANNED</em></div>
            <div className="service-row"><span className="service-icon">◈</span><span><strong>Matching engine</strong><small>Deterministic price-time priority</small></span><em>PLANNED</em></div>
            <div className="service-row"><span className="service-icon">▤</span><span><strong>Ledger service</strong><small>Simulated balances and postings</small></span><em>PLANNED</em></div>
            <div className="service-row"><span className="service-icon">⌘</span><span><strong>Market data</strong><small>WebSocket event distribution</small></span><em>PLANNED</em></div>
          </section>
        </div>

        <footer><span>APEX EXCHANGE · DEVELOPMENT BUILD 0.1.0</span><span>Test environment · No real funds</span></footer>
      </div>
    </main>
  );
}
