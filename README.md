# portfolio-analyzer
A Python-based portfolio analytics and optimization platform.


# Portfolio Analyzer

A Python-based portfolio analytics platform for analyzing
investment performance, risk and diversification.

## Features

- Historical market data
- Portfolio performance analysis
- Volatility and risk metrics
- Correlation analysis
- Sharpe and Sortino ratios
- Maximum drawdown
- Value at Risk
- Benchmark comparison
- Portfolio optimization
- Backtesting

## Tech Stack

- Python
- NumPy
- pandas
- SciPy
- matplotlib
- FastAPI
- PostgreSQL
- React
- Docker
- GitHub Actions

## Project Status

🚧 In development

## Run the web app (WSL)

```bash
cd ~/portfolio-analyzer
source .venv/bin/activate
pip install -r requirements.txt
uvicorn api.main:app --app-dir src --reload --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000 — fetch prices from the form (or run `python scripts/fetch_prices.py` first). Phases 1–3: cleaned prices, daily/cumulative/annualized returns, and a buy-and-hold book from €10,000 (weights must sum to 1).
