# Market News Intelligence

A SaaS-ready prototype that ingests financial news, scores sentiment, combines it with basic technical indicators, and delivers probabilistic market direction (UP / DOWN / NEUTRAL) to a React dashboard in real time. Now with auth, plan tiers, and a public developer API.

## What's inside

- Real-time ingestion of news (NewsAPI or seeded mock) and market data (yfinance).
- Multi-asset coverage out of the box: EUR/USD, BTC/USD, Gold.
- VADER + finance lexicon sentiment, RSI / MA / trend, blended probabilistic signal.
- Aggregated **Market Mood** (Risk-On / Risk-Off / Mixed) across tracked assets.
- **Economic calendar** with anticipation pressure score per upcoming event.
- FastAPI backend with WebSocket push and polling fallback.
- React + Vite + Tailwind frontend: landing, pricing, login, register, dashboard, account.
- JWT user auth with bcrypt password hashing.
- Plan tiers (Free / Pro / Premium / Team / API) with feature gating.
- Hashed API keys with per-plan rate limits, surfaced via versioned `/v1` endpoints.
- Optional Redis container via `docker compose --profile cache up` for the cache/pubsub upgrade path.
- **Advanced intelligence layer** (rule-based, swappable with ML later):
  - Pre-news stress via ATR compression + range tightening.
  - Liquidity zones via swing-point clustering.
  - Smart-money flow via volume z-score + wick / close-location analysis.
  - Contradiction detector (news sentiment vs price return divergence).
  - Pre-news volatility countdown with fake-move risk.
  - News-reaction replay with similarity scoring against past events.

## Stack

| Layer | Tech |
|---|---|
| Backend | FastAPI, SQLAlchemy 2, APScheduler, SQLite (Postgres-ready) |
| Auth | JWT (PyJWT) + bcrypt + hashed API keys |
| NLP | VADER + finance lexicon |
| Market | yfinance |
| Frontend | React 18 + Vite + TypeScript + Tailwind + react-router |
| Charts | lightweight-charts |
| Transport | REST + WebSocket |

## Quick start (Docker)

```bash
cp .env.example .env
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

## Try the SaaS flow

1. Register at `/register`.
2. Open `/pricing` and switch to Pro or Premium (MVP mode applies instantly without payment).
3. Open `/account`, create an API key.
4. Call the public API:
   ```bash
   curl -H "X-API-Key: mni_..." "http://localhost:8000/v1/signal?asset=EURUSD"
   ```
   Response includes `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset` headers.

## Endpoints

**Dashboard (open):**
- `GET /healthz`
- `GET /assets`
- `GET /news?asset=EURUSD&limit=20`
- `GET /market?asset=EURUSD&timeframe=15m&limit=96`
- `GET /signal?asset=EURUSD`
- `GET /mood`
- `GET /events?hours=48&importance=1`
- `GET /intel?asset=EURUSD`
- `GET /intel/replay?asset=EURUSD`
- `WS  /realtime`

**SaaS (Bearer JWT):**
- `POST /auth/register`, `POST /auth/login`, `GET /auth/me`
- `GET /billing/plans`, `POST /billing/select`
- `GET /keys`, `POST /keys`, `DELETE /keys/{id}`
- `GET /watchlist`, `POST /watchlist`, `DELETE /watchlist/{symbol}`

**Public v1 API (X-API-Key):**
- `GET /v1/assets`
- `GET /v1/news?asset=&limit=`
- `GET /v1/signal?asset=`

## Project layout

```
backend/
  app/
    api/          # REST + WS routes (auth, billing, keys, watchlist, v1, ...)
    services/     # sentiment, indicators, signal engine, plans, rate limiter
    workers/      # APScheduler polling
    models.py     # User, ApiKey, WatchlistItem, Asset, News, Candle, Signal
    auth.py       # JWT, bcrypt, API-key auth deps
frontend/
  src/
    auth/         # React auth context (JWT in localStorage)
    api/          # fetch + WebSocket hooks
    components/   # NavBar, AssetCard, NewsList, ProbabilityBar, ...
    pages/        # Landing, Pricing, Login, Register, Account, Dashboard
ml/               # pure algorithms, swappable for FinBERT / XGBoost later
```

## CI

A GitHub Actions workflow is staged at `.github/workflows.example/ci.yml`. Run `gh auth refresh -h github.com -s workflow` once, then `git mv .github/workflows.example .github/workflows && git commit -am "enable CI" && git push`.

## Disclaimer

Informational and educational use only. MNI does not provide investment advice. Probabilistic output may be wrong. Do not make financial decisions based solely on MNI output.
