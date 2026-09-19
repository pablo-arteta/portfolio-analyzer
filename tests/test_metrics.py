import pandas as pd
import pytest

from analytics.metrics import analyze_portfolio, historical_var, max_drawdown
from analytics.portfolio import buy_and_hold, validate_weights
from analytics.returns import annualized_return, cumulative_returns, daily_returns


def sample_prices() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "AAPL": [100.0, 110.0, 121.0],
            "CASH": [100.0, 100.0, 100.0],
        },
        index=pd.to_datetime(["2020-01-02", "2020-01-03", "2020-01-06"]),
    )


def test_daily_and_cumulative_returns() -> None:
    prices = pd.Series([100.0, 110.0, 121.0])
    daily = daily_returns(prices)
    assert daily.iloc[1] == pytest.approx(0.1)
    assert daily.iloc[2] == pytest.approx(0.1)
    assert cumulative_returns(prices).iloc[-1] == pytest.approx(0.21)


def test_annualized_return_is_cagr() -> None:
    prices = pd.Series(
        [100.0, 90.0, 108.0],
        index=pd.to_datetime(["2020-01-02", "2020-01-03", "2020-01-06"]),
    )
    years = 2 / 252
    assert annualized_return(prices) == pytest.approx((108 / 100) ** (1 / years) - 1)


def test_cagr_and_drawdown() -> None:
    prices = pd.Series(
        [100.0, 90.0, 108.0],
        index=pd.to_datetime(["2020-01-02", "2020-01-03", "2020-01-06"]),
    )
    assert max_drawdown(prices) == pytest.approx(-0.1)


def test_weights_must_sum_to_one() -> None:
    with pytest.raises(ValueError, match="must sum to 1"):
        validate_weights(["AAPL", "MSFT"], {"AAPL": 0.3, "MSFT": 0.3})
    weights = validate_weights(["AAPL", "MSFT"], {"AAPL": 0.5, "MSFT": 0.5})
    assert float(weights.sum()) == pytest.approx(1.0)


def test_buy_and_hold_does_not_rebalance() -> None:
    prices = pd.DataFrame(
        {"AAPL": [100.0, 200.0], "MSFT": [100.0, 100.0]},
        index=pd.to_datetime(["2020-01-02", "2020-01-03"]),
    )
    weights = validate_weights(["AAPL", "MSFT"], {"AAPL": 0.5, "MSFT": 0.5})
    book = buy_and_hold(prices, weights, 1_000.0)
    assert book["equity"].iloc[0] == pytest.approx(1000.0)
    assert book["equity"].iloc[-1] == pytest.approx(1500.0)
    assert book["current_weights"].iloc[-1]["AAPL"] == pytest.approx(2 / 3)


def test_historical_var_is_positive_loss() -> None:
    returns = pd.Series([-0.04, -0.01, 0.02, 0.01, -0.03])
    assert historical_var(returns, 0.8) > 0


def test_analyze_portfolio_weights_and_payload() -> None:
    prices = sample_prices()
    payload = analyze_portfolio(
        prices,
        weights={"AAPL": 1.0, "CASH": 0.0},
        initial_investment=1_000.0,
    )
    assert payload["weights"]["AAPL"] == 1.0
    assert payload["metrics"]["assets"]["AAPL"]["total_return"] == 0.21
    assert payload["portfolio"]["equity"][0] == 1000.0
    assert abs(payload["portfolio"]["equity"][-1] - 1210.0) < 1e-6
    assert payload["holdings"]["AAPL"]["shares"] == pytest.approx(10.0)
    assert payload["correlation"]["columns"] == ["AAPL", "CASH"]
