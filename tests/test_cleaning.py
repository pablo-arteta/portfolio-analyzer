import pandas as pd
import pytest

from data.cleaning import clean_price_frame, fill_missing_prices, strip_timezone


def test_fill_missing_prices_forward_fills_gaps() -> None:
    prices = pd.DataFrame(
        {"AAPL": [100.0, None, 102.0]},
        index=pd.to_datetime(["2020-01-02", "2020-01-03", "2020-01-06"]),
    )
    filled = fill_missing_prices(prices)
    assert filled.loc[pd.Timestamp("2020-01-03"), "AAPL"] == 100.0


def test_clean_price_frame_aligns_tickers() -> None:
    prices = pd.DataFrame(
        {
            "AAPL": [100.0, 101.0, 102.0],
            "MSFT": [200.0, None, 202.0],
        },
        index=pd.to_datetime(["2020-01-02", "2020-01-03", "2020-01-06"]),
    )
    cleaned = clean_price_frame(prices)
    assert list(cleaned.columns) == ["AAPL", "MSFT"]
    assert cleaned.isna().sum().sum() == 0
    assert len(cleaned) == 3
    assert cleaned.loc[pd.Timestamp("2020-01-03"), "MSFT"] == 200.0


def test_clean_price_frame_rejects_empty() -> None:
    with pytest.raises(ValueError, match="empty"):
        clean_price_frame(pd.DataFrame())


def test_strip_timezone_makes_naive_index() -> None:
    prices = pd.DataFrame(
        {"AAPL": [1.0, 2.0]},
        index=pd.to_datetime(["2020-01-02", "2020-01-03"], utc=True),
    )
    cleaned = strip_timezone(prices)
    assert cleaned.index.tz is None
