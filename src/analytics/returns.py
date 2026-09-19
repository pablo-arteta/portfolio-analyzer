"""Daily, cumulative, and annualized returns (Phase 2)."""

from __future__ import annotations

import pandas as pd

TRADING_DAYS = 252


def daily_returns(prices: pd.DataFrame | pd.Series) -> pd.DataFrame | pd.Series:
    return prices.pct_change()


def cumulative_returns(prices: pd.DataFrame | pd.Series) -> pd.DataFrame | pd.Series:
    return prices / prices.iloc[0] - 1.0


def sample_years(n_rows: int) -> float:
    return max(n_rows - 1, 1) / TRADING_DAYS


def annualized_return(prices: pd.Series) -> float:
    """Geometric (CAGR) annualized return from a price or equity series."""
    start = float(prices.iloc[0])
    end = float(prices.iloc[-1])
    years = sample_years(len(prices))
    if start <= 0 or years <= 0:
        return float("nan")
    return (end / start) ** (1.0 / years) - 1.0


def annualized_arithmetic(returns: pd.Series) -> float:
    clean = returns.dropna()
    if clean.empty:
        return float("nan")
    return float(clean.mean() * TRADING_DAYS)
