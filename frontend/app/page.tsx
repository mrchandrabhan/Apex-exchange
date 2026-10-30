"use client";

import { FormEvent, useEffect, useState } from "react";

type ApiState = "checking" | "online" | "offline";
type Market = {
  symbol: string;
  base_asset: string;
  quote_asset: string;
  reference_price: string;
  data_mode: string;
};
type Level = { price: string; quantity: string; order_count: number };
type BookSnapshot = { symbol: string; bids: Level[]; asks: Level[] };
type Trade = {
  trade_id: string;
  price: string;
  quantity: string;
  buy_order_id: string;
  sell_order_id: string;
};
const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8100";

export default function Home() {
  const [apiState, setApiState] = useState<ApiState>("checking");
  const [markets, setMarkets] = useState<Market[]>([]);
  const [message, setMessage] = useState("Connecting to API…");
  const [symbol, setSymbol] = useState("BTC/USDT");
  const [book, setBook] = useState<BookSnapshot | null>(null);
  const [side, setSide] = useState<"BUY" | "SELL">("BUY");
  const [price, setPrice] = useState("67200.00");
  const [quantity, setQuantity] = useState("0.01");
  const [orderMessage, setOrderMessage] = useState("");
  const [orderLoading, setOrderLoading] = useState(false);
  const [recentTrades, setRecentTrades] = useState<Trade[]>([]);

  async function loadBook(selectedSymbol: string) {
    try {
      const response = await fetch(
        `${API_BASE}/api/v1/orderbook/${encodeURIComponent(selectedSymbol)}`,
        { cache: "no-store" }
      );
      if (!response.ok) throw new Error("Could not load the order book.");
      setBook(await response.json());
      const tradesResponse = await fetch(
        `${API_BASE}/api/v1/trades/${encodeURIComponent(selectedSymbol)}`,
        { cache: "no-store" }
      );
      if (tradesResponse.ok) {
        const body = await tradesResponse.json();
        setRecentTrades(body.trades ?? []);
      }
    } catch {
      setBook(null);
      setRecentTrades([]);
    }
  }

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
      const availableMarkets: Market[] = marketData.markets ?? [];
      setMarkets(availableMarkets);
      setApiState("online");
      setMessage(`API connected · Database ${health.database ?? "ready"} · SIMULATION ONLY`);
      const initialSymbol = availableMarkets.some((m) => m.symbol === symbol)
        ? symbol
        : (availableMarkets[0]?.symbol ?? "BTC/USDT");
      setSymbol(initialSymbol);
      await loadBook(initialSymbol);
    } catch {
      setApiState("offline");
      setMessage("API unavailable — start the Docker Compose stack.");
    }
  }

  async function submitOrder(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setOrderLoading(true);
    setOrderMessage("");
    try {
      const response = await fetch(`${API_BASE}/api/v1/orders`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          order_id: `web-${Date.now()}`,
          symbol,
          side,
          price,
          quantity
        })
      });
      const body = await response.json();
      if (!response.ok) throw new Error(body.detail ?? "Order was rejected.");
      const order = body.order;
      const fills = body.trades ?? [];
      setOrderMessage(
        `Order ${order.order_id}: ${order.status} · filled ${order.filled_quantity} · remaining ${order.remaining_quantity}` +
        (fills.length ? ` · ${fills.length} trade(s) generated` : " · resting in the order book")
      );
      await loadBook(symbol);
    } catch (error) {
      setOrderMessage(error instanceof Error ? error.message : "Unexpected order error.");
    } finally {
      setOrderLoading(false);
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

      <section className="notice"><span>SIMULATION ONLY</span> Test orders, in-memory order books, and synthetic reference prices. No real assets, deposits, withdrawals, or live trading.</section>

      <div className="page-content">
        <div className="page-heading">
          <div><span className="eyebrow">DETERMINISTIC MATCHING ENGINE / BUILD 0.2.0</span><h1>Market overview</h1><p>Limit-order matching with Decimal precision, price-time priority, partial fills, and cancellation.</p></div>
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
              <button className={`market-card market-button ${symbol === market.symbol ? "market-selected" : ""}`} key={market.symbol} onClick={() => { setSymbol(market.symbol); void loadBook(market.symbol); }}>
                <div className="pair"><span className="coin">{market.base_asset.slice(0, 1)}</span><span><strong>{market.symbol}</strong><small>{market.base_asset} / {market.quote_asset}</small></span></div>
                <div className="price">{market.reference_price}<small>{market.quote_asset}</small></div>
                <span className="demo-label">{market.data_mode}</span>
              </button>
            )) : (
              <article className="market-card empty"><strong>{apiState === "offline" ? "Waiting for API" : "Loading markets…"}</strong><span>Market fixtures are served by the backend.</span></article>
            )}
          </div>
        </section>

        <div className="trading-grid" id="engine">
          <section className="panel">
            <div className="panel-heading"><div><span className="eyebrow">LIVE IN-MEMORY BOOK</span><h2>Order book · {symbol}</h2></div><span className="build-badge">SYNTHETIC</span></div>
            <div className="book-columns">
              <div>
                <div className="book-column-title buy-text">BIDS · BUY</div>
                <div className="book-head"><span>PRICE</span><span>QUANTITY</span><span>ORDERS</span></div>
                {book?.bids.length ? book.bids.map((level) => <div className="book-row bid-row" key={level.price}><strong>{level.price}</strong><span>{level.quantity}</span><span>{level.order_count}</span></div>) : <div className="book-empty">No resting bids</div>}
              </div>
              <div>
                <div className="book-column-title sell-text">ASKS · SELL</div>
                <div className="book-head"><span>PRICE</span><span>QUANTITY</span><span>ORDERS</span></div>
                {book?.asks.length ? book.asks.map((level) => <div className="book-row ask-row" key={level.price}><strong>{level.price}</strong><span>{level.quantity}</span><span>{level.order_count}</span></div>) : <div className="book-empty">No resting asks</div>}
              </div>
            </div>
            <button className="refresh book-refresh" onClick={() => void loadBook(symbol)}>↻ Refresh book</button>
          </section>

          <section className="panel order-entry">
            <div className="panel-heading"><div><span className="eyebrow">LIMIT ORDER</span><h2>Submit test order</h2></div><span className="build-badge">NO REAL FUNDS</span></div>
            <form onSubmit={submitOrder}>
              <label>Market<select value={symbol} onChange={(event) => { setSymbol(event.target.value); void loadBook(event.target.value); }}>{markets.map((market) => <option key={market.symbol} value={market.symbol}>{market.symbol}</option>)}</select></label>
              <div className="side-switch">
                <button type="button" className={side === "BUY" ? "buy-active" : ""} onClick={() => setSide("BUY")}>BUY</button>
                <button type="button" className={side === "SELL" ? "sell-active" : ""} onClick={() => setSide("SELL")}>SELL</button>
              </div>
              <label>Limit price<input value={price} onChange={(event) => setPrice(event.target.value)} inputMode="decimal" required /></label>
              <label>Quantity<input value={quantity} onChange={(event) => setQuantity(event.target.value)} inputMode="decimal" required /></label>
              <button className={`submit-order ${side.toLowerCase()}`} type="submit" disabled={orderLoading || apiState !== "online"}>{orderLoading ? "Submitting…" : `Submit ${side} order`}</button>
            </form>
            {orderMessage && <p className="order-message" role="status">{orderMessage}</p>}
            <p className="engine-disclaimer">Orders and trades exist only in this API process and are cleared when it restarts. Account balances and settlement are not implemented yet.</p>
          </section>
        </div>

        <section className="panel trades-panel">
          <div className="panel-heading"><div><span className="eyebrow">EXECUTION HISTORY</span><h2>Recent simulated trades</h2></div><span className="small-label">MAKER PRICE EXECUTION</span></div>
          {recentTrades.length ? (
            <div className="trade-list">
              {recentTrades.slice().reverse().map((trade) => (
                <div className="trade-row" key={trade.trade_id}>
                  <strong>{trade.trade_id}</strong><span>{trade.price} USDT</span><span>{trade.quantity} {symbol.split("/")[0]}</span><small>Buy {trade.buy_order_id} · Sell {trade.sell_order_id}</small>
                </div>
              ))}
            </div>
          ) : <div className="book-empty">No trades yet. Submit a crossing limit order to generate a simulated execution.</div>}
        </section>

        <footer><span>APEX EXCHANGE · DEVELOPMENT BUILD 0.2.0</span><span>Test environment · No real funds</span></footer>
      </div>
    </main>
  );
}
