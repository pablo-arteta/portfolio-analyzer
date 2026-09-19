from pathlib import Path

import pandas as pd

from data.loader import _extract_close, load_prices, save_prices


def test_extract_close_from_multiindex() -> None:
    index = pd.to_datetime(["2020-01-02", "2020-01-03"])
    columns = pd.MultiIndex.from_product([["Close", "High"], ["AAPL", "MSFT"]])
    raw = pd.DataFrame(
        [
            [100.0, 200.0, 101.0, 201.0],
            [102.0, 202.0, 103.0, 203.0],
        ],
        index=index,
        columns=columns,
    )
    prices = _extract_close(raw, ["AAPL", "MSFT"])
    assert list(prices.columns) == ["AAPL", "MSFT"]
    assert prices.loc[pd.Timestamp("2020-01-02"), "AAPL"] == 100.0


def test_save_and_load_prices(tmp_path: Path) -> None:
    prices = pd.DataFrame(
        {"AAPL": [100.0, 101.0]},
        index=pd.to_datetime(["2020-01-02", "2020-01-03"]),
    )
    prices.index.name = "date"
    path = tmp_path / "prices.csv"
    save_prices(prices, path)
    loaded = load_prices(path)
    pd.testing.assert_frame_equal(loaded, prices, check_freq=False)
