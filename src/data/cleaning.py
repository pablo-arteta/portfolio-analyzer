"""Clean and align historical price series."""

from __future__ import annotations

import pandas as pd


def strip_timezone(prices: pd.DataFrame) -> pd.DataFrame:
    cleaned = prices.copy()
    index = pd.to_datetime(cleaned.index)
    if getattr(index, "tz", None) is not None:
        index = index.tz_convert("UTC").tz_localize(None)
    cleaned.index = index
    cleaned.index.name = "date"
    return cleaned


def fill_missing_prices(prices: pd.DataFrame) -> pd.DataFrame:
    """Forward-fill gaps so a missing session reuses the last known price."""
    return prices.sort_index().ffill()


def drop_incomplete_rows(prices: pd.DataFrame) -> pd.DataFrame:
    """Keep days where every ticker has a price (after filling)."""
    return prices.dropna(how="any")


def clean_price_frame(prices: pd.DataFrame) -> pd.DataFrame:
    """Sort, remove timezones, fill gaps, and drop remaining missing values."""
    if prices.empty:
        raise ValueError("Price frame is empty.")

    cleaned = strip_timezone(prices)
    cleaned = cleaned.sort_index()
    cleaned = cleaned[~cleaned.index.duplicated(keep="last")]
    cleaned = fill_missing_prices(cleaned)
    cleaned = drop_incomplete_rows(cleaned)

    if cleaned.empty:
        raise ValueError("No overlapping dates remain after cleaning.")

    return cleaned
