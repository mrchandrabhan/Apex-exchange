from fastapi.testclient import TestClient

from app import main
from app.matching.exchange import SimulatedExchange


def test_api_order_submission_and_order_book_snapshot(monkeypatch):
    monkeypatch.setattr(main, "EXCHANGE", SimulatedExchange(["BTC/USDT"]))
    client = TestClient(main.app)

    ask = client.post(
        "/api/v1/orders",
        json={"order_id": "ask-1", "symbol": "BTC/USDT", "side": "SELL", "price": "100", "quantity": "2"},
    )
    bid = client.post(
        "/api/v1/orders",
        json={"order_id": "bid-1", "symbol": "BTC/USDT", "side": "BUY", "price": "105", "quantity": "1"},
    )

    assert ask.status_code == 201
    assert bid.status_code == 201
    assert bid.json()["data_mode"] == "SYNTHETIC_DEMO"
    assert bid.json()["order"]["status"] == "FILLED"
    assert bid.json()["trades"][0]["price"] == "100"
    assert client.get("/api/v1/orderbook/BTC%2FUSDT").json()["asks"][0]["quantity"] == "1"


def test_api_cancel_and_unknown_market(monkeypatch):
    monkeypatch.setattr(main, "EXCHANGE", SimulatedExchange(["BTC/USDT"]))
    client = TestClient(main.app)

    created = client.post(
        "/api/v1/orders",
        json={"order_id": "resting", "symbol": "BTC/USDT", "side": "SELL", "price": "100", "quantity": "1"},
    )
    canceled = client.delete("/api/v1/orders/resting")
    unknown = client.post(
        "/api/v1/orders",
        json={"symbol": "DOGE/USDT", "side": "BUY", "price": "1", "quantity": "1"},
    )

    assert created.status_code == 201
    assert canceled.status_code == 200
    assert canceled.json()["order"]["status"] == "CANCELED"
    assert unknown.status_code == 404
