from pathlib import Path

import pandas as pd
from fastapi.testclient import TestClient

from api.main import app
from data.pipeline import frame_to_payload


client = TestClient(app)


def test_config_returns_example_portfolio() -> None:
    response = client.get("/api/config")
    assert response.status_code == 200
    body = response.json()
    assert body["tickers"] == ["AAPL", "MSFT", "GOOGL", "SPY"]
    assert body["initial_investment"] == 10000
    assert body["currency"] == "EUR"


def test_prices_404_when_missing(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("api.main.load_stored_prices", lambda: None)
    response = client.get("/api/prices")
    assert response.status_code == 404


def test_frontend_is_served() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "Portfolio Analyzer" in response.text
    assert 'id="fetch-form"' in response.text
    assert "/app.js" in response.text


def test_frame_to_payload_round_trip() -> None:
    prices = pd.DataFrame(
        {"AAPL": [100.0, 110.0]},
        index=pd.to_datetime(["2020-01-02", "2020-01-03"]),
    )
    payload = frame_to_payload(prices)
    assert payload["rows"] == 2
    assert payload["series"]["AAPL"] == [100.0, 110.0]
    assert payload["start"] == "2020-01-02"


def test_analysis_uses_stored_prices(monkeypatch) -> None:
    prices = pd.DataFrame(
        {"AAPL": [100.0, 110.0, 121.0], "MSFT": [50.0, 50.0, 50.0]},
        index=pd.to_datetime(["2020-01-02", "2020-01-03", "2020-01-06"]),
    )
    monkeypatch.setattr("api.main.load_stored_prices", lambda: prices)
    monkeypatch.setattr("api.main.load_stored_benchmark", lambda: None)
    response = client.post(
        "/api/analysis",
        json={"weights": {"AAPL": 1, "MSFT": 0}, "initial_investment": 1000},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["metrics"]["assets"]["AAPL"]["total_return"] == 0.21
    assert abs(body["portfolio"]["equity"][-1] - 1210) < 1e-4


def test_analysis_rejects_weights_that_do_not_sum_to_one(monkeypatch) -> None:
    prices = pd.DataFrame(
        {"AAPL": [100.0, 110.0], "MSFT": [50.0, 50.0]},
        index=pd.to_datetime(["2020-01-02", "2020-01-03"]),
    )
    monkeypatch.setattr("api.main.load_stored_prices", lambda: prices)
    monkeypatch.setattr("api.main.load_stored_benchmark", lambda: None)
    response = client.post(
        "/api/analysis",
        json={"weights": {"AAPL": 0.3, "MSFT": 0.3}},
    )
    assert response.status_code == 400
    assert "sum to 1" in response.json()["detail"]
