"""Weight checks and buy-and-hold portfolio value (Phase 3)."""

from __future__ import annotations

import pandas as pd

WEIGHT_TOLERANCE = 1e-4


def validate_weights(
    columns: list[str],
    weights: dict[str, float] | None,
) -> pd.Series:
    """Require a weight for the portfolio tickers that sums to 1."""
    if not columns:
        raise ValueError("At least one asset is required.")
    if not weights:
        raise ValueError("Weights are required and must sum to 1.")

    series = pd.Series(0.0, index=columns, dtype=float)
    unknown = []
    for ticker, value in weights.items():
        name = str(ticker)
        if name not in series.index:
            unknown.append(name)
            continue
        series[name] = float(value)

    if unknown:
        raise ValueError(f"Unknown tickers in weights: {', '.join(unknown)}.")

    total = float(series.sum())
    if abs(total - 1.0) > WEIGHT_TOLERANCE:
        raise ValueError(f"Weights must sum to 1 (got {total:.6f}).")
    if (series < -WEIGHT_TOLERANCE).any():
        raise ValueError("Weights cannot be negative.")
    return series


def equal_weights(columns: list[str]) -> pd.Series:
    if not columns:
        raise ValueError("At least one asset is required.")
    return pd.Series(1.0 / len(columns), index=columns)


def weights_for_prices(
    columns: list[str],
    weights: dict[str, float] | None,
    *,
    allow_equal_fallback: bool = False,
) -> pd.Series:
    if weights:
        aligned = {column: float(weights.get(column, 0.0)) for column in columns}
        try:
            return validate_weights(columns, aligned)
        except ValueError:
            if not allow_equal_fallback:
                raise
    if allow_equal_fallback:
        return equal_weights(columns)
    raise ValueError("Weights are required and must sum to 1.")


def buy_and_hold(
    prices: pd.DataFrame,
    weights: pd.Series,
    initial_investment: float,
) -> dict[str, pd.DataFrame | pd.Series]:
    """Allocate once at the first close; let position values drift."""
    start = prices.iloc[0]
    if (start <= 0).any():
        raise ValueError("Start prices must be positive.")
    shares = weights * initial_investment / start
    holdings = prices.mul(shares, axis=1)
    equity = holdings.sum(axis=1)
    current_weights = holdings.div(equity, axis=0)
    return {
        "shares": shares,
        "holdings": holdings,
        "equity": equity,
        "current_weights": current_weights,
    }
