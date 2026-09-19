"""Download, clean, and persist the default market-data set."""

from __future__ import annotations

import pandas as pd

from analytics.returns import daily_returns

from .cleaning import clean_price_frame
from .config import DEFAULT_BENCHMARK, DEFAULT_END, DEFAULT_START, DEFAULT_TICKERS
from .loader import (
    PROCESSED_DIR,
    download_prices,
    load_prices,
    save_prices,
    save_raw_and_processed,
)

PRICES_PATH = PROCESSED_DIR / "prices.csv"
RETURNS_PATH = PROCESSED_DIR / "returns.csv"
BENCHMARK_PATH = PROCESSED_DIR / "benchmark.csv"


def refresh_market_data(
    tickers: list[str] | None = None,
    start: str = DEFAULT_START,
    end: str = DEFAULT_END,
    benchmark: str | None = DEFAULT_BENCHMARK,
) -> dict[str, pd.DataFrame]:
    tickers = list(tickers or DEFAULT_TICKERS)
    prices = clean_price_frame(download_prices(tickers, start, end))
    save_raw_and_processed(prices)
    returns = daily_returns(prices).dropna(how="all")
    save_prices(returns, RETURNS_PATH)
    result: dict[str, pd.DataFrame] = {"prices": prices, "returns": returns}

    if benchmark:
        bench = clean_price_frame(download_prices([benchmark], start, end))
        save_prices(bench, BENCHMARK_PATH)
        result["benchmark"] = bench

    return result


def load_stored_prices() -> pd.DataFrame | None:
    if not PRICES_PATH.exists():
        return None
    return load_prices(PRICES_PATH)


def load_stored_returns() -> pd.DataFrame | None:
    if not RETURNS_PATH.exists():
        return None
    return load_prices(RETURNS_PATH)


def load_stored_benchmark() -> pd.DataFrame | None:
    if not BENCHMARK_PATH.exists():
        return None
    return load_prices(BENCHMARK_PATH)


def frame_to_payload(prices: pd.DataFrame) -> dict:
    dates = [d.strftime("%Y-%m-%d") for d in prices.index]
    return {
        "dates": dates,
        "series": {
            str(column): [None if pd.isna(value) else float(value) for value in prices[column]]
            for column in prices.columns
        },
        "start": dates[0] if dates else None,
        "end": dates[-1] if dates else None,
        "rows": len(dates),
    }
