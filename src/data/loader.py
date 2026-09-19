"""Download and persist historical market prices."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import yfinance as yf

from .config import DEFAULT_END, DEFAULT_START, DEFAULT_TICKERS

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"


def download_prices(
    tickers: list[str] | None = None,
    start: str = DEFAULT_START,
    end: str = DEFAULT_END,
) -> pd.DataFrame:
    """Download adjusted close prices. Columns are tickers, index is dates."""
    tickers = list(tickers or DEFAULT_TICKERS)
    if not tickers:
        raise ValueError("At least one ticker is required.")

    raw = yf.download(
        tickers=tickers,
        start=start,
        end=end,
        auto_adjust=True,
        progress=False,
        threads=True,
    )
    if raw.empty:
        raise ValueError(
            f"No prices returned for {tickers} between {start} and {end}."
        )
    return _extract_close(raw, tickers)


def _extract_close(raw: pd.DataFrame, tickers: list[str]) -> pd.DataFrame:
    if isinstance(raw.columns, pd.MultiIndex):
        level0 = raw.columns.get_level_values(0)
        level1 = raw.columns.get_level_values(1)
        if "Close" in level0:
            prices = raw["Close"].copy()
        elif "Close" in level1:
            prices = raw.xs("Close", axis=1, level=1).copy()
        else:
            raise ValueError("Downloaded data has no Close column.")
    else:
        if "Close" not in raw.columns:
            raise ValueError("Downloaded data has no Close column.")
        prices = raw[["Close"]].rename(columns={"Close": tickers[0]})

    prices = prices.reindex(columns=tickers)
    prices.index = pd.to_datetime(prices.index)
    prices.index.name = "date"
    return prices


def save_prices(prices: pd.DataFrame, path: Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    prices.to_csv(path)
    return path


def load_prices(path: Path) -> pd.DataFrame:
    prices = pd.read_csv(path, index_col=0, parse_dates=True)
    prices.index.name = "date"
    return prices


def save_raw_and_processed(prices: pd.DataFrame) -> Path:
    """Write one CSV per ticker plus a combined processed file."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    for ticker in prices.columns:
        save_prices(prices[[ticker]], RAW_DIR / f"{ticker}.csv")

    processed_path = PROCESSED_DIR / "prices.csv"
    save_prices(prices, processed_path)
    return processed_path
