# Market News Intelligence MVP

A minimal, runnable prototype that ingests financial news, scores sentiment, combines it with basic technical indicators, and pushes a probabilistic direction (UP / DOWN / NEUTRAL) to a React dashboard over WebSocket.

## What it does

- Pulls news for EUR/USD from NewsAPI (or a built-in mock dataset when no key is set).
- Pulls 15-minute OHLCV for EUR/USD from Yahoo Finance via `yfinance`.
- Scores each headline with VADER plus a small finance lexicon boost.
- Computes RSI(14), MA20, MA50 and a trend label.
- Blends news sentiment and technical score into calibrated-ish UP / DOWN / NEUTRAL probabilities.
- Streams updates to the browser over WebSocket with a polling fallback.

## Stack

| Layer | Tech |
|---|---|
| Backend | FastAPI, SQLAlchemy, APScheduler, SQLite |
| NLP | VADER + small finance lexicon |
| Market | yfinance |
| Frontend | React + Vite + TypeScript + Tailwind |
| Charts | lightweight-charts |
| Transport | REST + WebSocket |

## Quick start (Docker)

```bash
cp .env.example .env   # optional: set NEWSAPI_KEY
docker compose up --build
```

Open http://localhost:5173

## Quick start (manual)

Backend:
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e .
cp ../.env.example .env
uvicorn app.main:app --reload --port 8000
```

Frontend:
```bash
cd frontend
npm install
echo "VITE_API_URL=http://localhost:8000" > .env.local
npm run dev
```

## Endpoints

- `GET /healthz`
- `GET /news?asset=EURUSD&limit=20`
- `GET /market?asset=EURUSD&timeframe=15m&limit=96`
- `GET /signal?asset=EURUSD`
- `WS  /realtime`

## Project layout

See [docs](#project-layout) below and the folder comments in each service file.

```
backend/   FastAPI app, services, workers
frontend/  React dashboard
ml/        Pure algorithms, free of DB imports
```

## CI

A GitHub Actions workflow is staged at `.github/workflows.example/ci.yml`. To activate it, run `gh auth refresh -h github.com -s workflow` once, then `git mv .github/workflows.example .github/workflows && git commit -m "enable CI" && git push`.

## Notes

This is an MVP. It is not a trading system. Probabilities are heuristic, not calibrated on real outcome data. See the original design docs for the production architecture.
