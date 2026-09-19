"""CLI: download, clean, and store historical prices."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from data.config import DEFAULT_BENCHMARK, DEFAULT_END, DEFAULT_START, DEFAULT_TICKERS
from data.pipeline import BENCHMARK_PATH, PRICES_PATH, RETURNS_PATH, refresh_market_data


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
    result = refresh_market_data(args.tickers, args.start, args.end, args.benchmark)
    print(f"Saved {len(result['prices'])} rows to {PRICES_PATH}")
    print(f"Saved {len(result['returns'])} return rows to {RETURNS_PATH}")
    if "benchmark" in result:
        print(f"Saved {len(result['benchmark'])} rows to {BENCHMARK_PATH}")


if __name__ == "__main__":
    main()
