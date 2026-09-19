"""Assemble analysis payloads. Risk helpers stay here for later phases."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .portfolio import buy_and_hold, weights_for_prices
from .returns import (
    TRADING_DAYS,
    annualized_arithmetic,
    annualized_return,
    cumulative_returns,
    daily_returns,
)

cagr = annualized_return


def annualized_vol(returns: pd.Series) -> float:
    clean = returns.dropna()
    if clean.empty:
        return float("nan")
    return float(clean.std(ddof=1) * np.sqrt(TRADING_DAYS))


def sharpe_ratio(returns: pd.Series, rf: float = 0.0) -> float:
    vol = annualized_vol(returns)
    if not vol or np.isnan(vol):
        return float("nan")
    excess = float(returns.dropna().mean() * TRADING_DAYS) - rf
    return excess / vol


def sortino_ratio(returns: pd.Series, rf: float = 0.0) -> float:
    clean = returns.dropna()
    if clean.empty:
        return float("nan")
    daily_rf = rf / TRADING_DAYS
    downside = clean[clean < daily_rf] - daily_rf
    if downside.empty:
        return float("nan")
    downside_dev = float(np.sqrt((downside**2).mean()) * np.sqrt(TRADING_DAYS))
    if not downside_dev:
        return float("nan")
    excess = float(clean.mean() * TRADING_DAYS) - rf
    return excess / downside_dev


def max_drawdown(equity: pd.Series) -> float:
    peak = equity.cummax()
    return float((equity / peak - 1.0).min())


def drawdown_series(equity: pd.Series) -> pd.Series:
    peak = equity.cummax()
    return equity / peak - 1.0


def historical_var(returns: pd.Series, level: float = 0.95) -> float:
    """1-day historical VaR as a positive loss fraction."""
    clean = returns.dropna()
    if clean.empty:
        return float("nan")
    quantile = float(np.nanpercentile(clean, (1.0 - level) * 100.0))
    return -quantile


def to_list(series: pd.Series) -> list[float | None]:
    values: list[float | None] = []
    for value in series:
        if pd.isna(value):
            values.append(None)
        else:
            values.append(round(float(value), 8))
    return values


def finite(value: float) -> float | None:
    if value is None or pd.isna(value):
        return None
    number = float(value)
    if not np.isfinite(number):
        return None
    return round(number, 6)


def summarize_prices(prices: pd.Series, rf: float = 0.0) -> dict:
    returns = prices.pct_change()
    return {
        "total_return": finite(float(prices.iloc[-1] / prices.iloc[0] - 1.0)),
        "cagr": finite(annualized_return(prices)),
        "annualized_return": finite(annualized_return(prices)),
        "annualized_arithmetic": finite(annualized_arithmetic(returns)),
        "volatility": finite(annualized_vol(returns)),
        "sharpe": finite(sharpe_ratio(returns, rf)),
        "sortino": finite(sortino_ratio(returns, rf)),
        "max_drawdown": finite(max_drawdown(prices)),
        "var_95": finite(historical_var(returns)),
    }


def correlation_payload(returns: pd.DataFrame) -> dict:
    corr = returns.dropna(how="all").corr()
    columns = [str(column) for column in corr.columns]
    matrix = [
        [finite(corr.loc[row, column]) for column in corr.columns]
        for row in corr.index
    ]
    return {"columns": columns, "matrix": matrix}


def analyze_portfolio(
    prices: pd.DataFrame,
    benchmark: pd.DataFrame | None = None,
    weights: dict[str, float] | None = None,
    rf: float = 0.0,
    initial_investment: float = 10_000.0,
    *,
    allow_equal_fallback: bool = False,
) -> dict:
    if prices.empty:
        raise ValueError("Price frame is empty.")

    tickers = [str(column) for column in prices.columns]
    weight_series = weights_for_prices(
        tickers,
        weights,
        allow_equal_fallback=allow_equal_fallback,
    )
    book = buy_and_hold(prices, weight_series, initial_investment)
    shares: pd.Series = book["shares"]
    holdings: pd.DataFrame = book["holdings"]
    port_equity: pd.Series = book["equity"]
    current_weights: pd.DataFrame = book["current_weights"]
    asset_returns = daily_returns(prices)
    port_returns = daily_returns(port_equity)

    payload: dict = {
        "dates": [stamp.strftime("%Y-%m-%d") for stamp in prices.index],
        "start": prices.index[0].strftime("%Y-%m-%d"),
        "end": prices.index[-1].strftime("%Y-%m-%d"),
        "rows": int(len(prices)),
        "rf": rf,
        "currency": "EUR",
        "initial_investment": initial_investment,
        "weights": {ticker: finite(weight_series[ticker]) for ticker in tickers},
        "current_weights": {
            ticker: finite(current_weights.iloc[-1][ticker]) for ticker in tickers
        },
        "shares": {ticker: finite(shares[ticker]) for ticker in tickers},
        "prices": {ticker: to_list(prices[ticker]) for ticker in tickers},
        "normalized": {
            ticker: to_list(prices[ticker] / prices[ticker].iloc[0])
            for ticker in tickers
        },
        "daily_returns": {ticker: to_list(asset_returns[ticker]) for ticker in tickers},
        "cumulative_returns": {
            ticker: to_list(cumulative_returns(prices[ticker])) for ticker in tickers
        },
        "holdings": {
            ticker: {
                "shares": finite(shares[ticker]),
                "start_weight": finite(weight_series[ticker]),
                "current_weight": finite(current_weights.iloc[-1][ticker]),
                "start_value": finite(holdings.iloc[0][ticker]),
                "current_value": finite(holdings.iloc[-1][ticker]),
                "daily_return": finite(asset_returns.iloc[-1][ticker]),
                "cumulative_return": finite(float(prices[ticker].iloc[-1] / prices[ticker].iloc[0] - 1.0)),
                "annualized_return": finite(annualized_return(prices[ticker])),
            }
            for ticker in tickers
        },
        "portfolio": {
            "daily_returns": to_list(port_returns),
            "equity": to_list(port_equity),
            "cumulative_returns": to_list(cumulative_returns(port_equity)),
            "drawdown": to_list(drawdown_series(port_equity)),
            "start_value": finite(float(port_equity.iloc[0])),
            "current_value": finite(float(port_equity.iloc[-1])),
        },
        "metrics": {
            "assets": {
                ticker: summarize_prices(prices[ticker], rf) for ticker in tickers
            },
            "portfolio": summarize_prices(port_equity, rf),
        },
        "correlation": correlation_payload(asset_returns),
    }

    if benchmark is not None and not benchmark.empty:
        bench_name = str(benchmark.columns[0])
        bench_prices = benchmark.iloc[:, 0].reindex(prices.index).ffill()
        bench_equity = bench_prices / bench_prices.iloc[0] * initial_investment
        payload["benchmark_name"] = bench_name
        payload["benchmark"] = {
            "normalized": to_list(bench_prices / bench_prices.iloc[0]),
            "equity": to_list(bench_equity),
            "daily_returns": to_list(daily_returns(bench_equity)),
            "cumulative_returns": to_list(cumulative_returns(bench_equity)),
            "drawdown": to_list(drawdown_series(bench_equity)),
        }
        payload["metrics"]["benchmark"] = summarize_prices(bench_equity, rf)

    return payload
