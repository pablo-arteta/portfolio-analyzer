"""CLI: download, clean, and store historical prices."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from data.cleaning import clean_price_frame
from data.config import DEFAULT_BENCHMARK, DEFAULT_END, DEFAULT_START, DEFAULT_TICKERS
from data.loader import download_prices, save_prices, save_raw_and_processed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch and clean market prices.")
    parser.add_argument(
        "--tickers",
        nargs="+",
        default=DEFAULT_TICKERS,
        help="Tickers to download (default: example portfolio).",
    )
    parser.add_argument("--start", default=DEFAULT_START)
    parser.add_argument("--end", default=DEFAULT_END)
    parser.add_argument(
        "--benchmark",
        default=DEFAULT_BENCHMARK,
        help="Benchmark ticker saved separately (default: ^GSPC).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    print(f"Downloading {args.tickers} from {args.start} to {args.end}...")
    raw_prices = download_prices(args.tickers, args.start, args.end)
    prices = clean_price_frame(raw_prices)
    processed_path = save_raw_and_processed(prices)
    print(f"Saved {len(prices)} rows to {processed_path}")

    if args.benchmark:
        print(f"Downloading benchmark {args.benchmark}...")
        benchmark = download_prices([args.benchmark], args.start, args.end)
        benchmark = clean_price_frame(benchmark)
        bench_path = ROOT / "data" / "processed" / "benchmark.csv"
        save_prices(benchmark, bench_path)
        print(f"Saved {len(benchmark)} rows to {bench_path}")


if __name__ == "__main__":
    main()
