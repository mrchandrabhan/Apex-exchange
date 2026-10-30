from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root_describes_service() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["service"] == "apex-exchange-api"


def test_health_is_independent_of_database() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_markets_are_explicitly_synthetic() -> None:
    response = client.get("/api/v1/markets")
    assert response.status_code == 200
    body = response.json()
    assert body["data_mode"] == "SYNTHETIC_DEMO"
    assert {market["symbol"] for market in body["markets"]} == {"BTC/USDT", "ETH/USDT"}
