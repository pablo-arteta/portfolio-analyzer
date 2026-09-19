"""FastAPI app: JSON API plus the JavaScript frontend."""

from __future__ import annotations

import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from analytics.metrics import analyze_portfolio  # noqa: E402
from data.config import (  # noqa: E402
    CURRENCY,
    DEFAULT_BENCHMARK,
    DEFAULT_END,
    DEFAULT_START,
    DEFAULT_TICKERS,
    DEFAULT_WEIGHTS,
    INITIAL_INVESTMENT,
)
from data.pipeline import (  # noqa: E402
    frame_to_payload,
    load_stored_benchmark,
    load_stored_prices,
    refresh_market_data,
)

FRONTEND_DIR = ROOT / "frontend"

app = FastAPI(title="Portfolio Analyzer")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class FetchRequest(BaseModel):
    tickers: list[str] = Field(default_factory=lambda: list(DEFAULT_TICKERS))
    start: str = DEFAULT_START
    end: str = DEFAULT_END
    benchmark: str | None = DEFAULT_BENCHMARK


class AnalysisRequest(BaseModel):
    weights: dict[str, float] | None = None
    rf: float = 0.0
    initial_investment: float = INITIAL_INVESTMENT


def _analysis_payload(
    prices,
    weights: dict[str, float] | None,
    rf: float,
    initial_investment: float,
    *,
    allow_equal_fallback: bool = False,
) -> dict:
    if prices is None:
        raise HTTPException(
            status_code=404,
            detail="No stored prices yet. Fetch market data from the UI.",
        )
    try:
        return analyze_portfolio(
            prices,
            benchmark=load_stored_benchmark(),
            weights=weights,
            rf=rf,
            initial_investment=initial_investment,
            allow_equal_fallback=allow_equal_fallback,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/config")
def get_config() -> dict:
    return {
        "tickers": DEFAULT_TICKERS,
        "start": DEFAULT_START,
        "end": DEFAULT_END,
        "benchmark": DEFAULT_BENCHMARK,
        "weights": DEFAULT_WEIGHTS,
        "initial_investment": INITIAL_INVESTMENT,
        "currency": CURRENCY,
        "rf": 0.0,
    }


@app.get("/api/prices")
def get_prices() -> dict:
    prices = load_stored_prices()
    if prices is None:
        raise HTTPException(
            status_code=404,
            detail="No stored prices yet. Fetch market data from the UI.",
        )
    payload = frame_to_payload(prices)
    benchmark = load_stored_benchmark()
    if benchmark is not None:
        payload["benchmark"] = frame_to_payload(benchmark)
    return payload


@app.post("/api/prices/refresh")
def post_refresh(body: FetchRequest) -> dict:
    tickers = [ticker.strip().upper() for ticker in body.tickers if ticker.strip()]
    if not tickers:
        raise HTTPException(status_code=400, detail="At least one ticker is required.")
    try:
        result = refresh_market_data(
            tickers=tickers,
            start=body.start,
            end=body.end,
            benchmark=body.benchmark,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    payload = frame_to_payload(result["prices"])
    if "benchmark" in result:
        payload["benchmark"] = frame_to_payload(result["benchmark"])
    return payload


@app.get("/api/analysis")
def get_analysis() -> dict:
    return _analysis_payload(
        load_stored_prices(),
        DEFAULT_WEIGHTS,
        0.0,
        INITIAL_INVESTMENT,
        allow_equal_fallback=True,
    )


@app.post("/api/analysis")
def post_analysis(body: AnalysisRequest) -> dict:
    return _analysis_payload(
        load_stored_prices(),
        body.weights,
        body.rf,
        body.initial_investment,
    )


app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
