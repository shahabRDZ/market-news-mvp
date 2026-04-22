# Market News Intelligence

A SaaS-ready prototype that ingests financial news, scores sentiment, combines it with basic technical indicators, and delivers probabilistic market direction (UP / DOWN / NEUTRAL) to a React dashboard in real time. Now with auth, plan tiers, and a public developer API.

## What's inside

- **Real news** via RSS (Reuters, CNBC, ForexLive, Investing, MarketWatch, CoinDesk, Yahoo, FXStreet) with zero API key. NewsAPI kicks in when `NEWSAPI_KEY` is set.
- **Live crypto prices** every 5s via Coinbase/Binance WebSocket, with Yahoo Finance chart-endpoint fast-poll fallback when exchange WS is blocked.
- Multi-asset coverage out of the box: EUR/USD, BTC/USD, ETH/USD, Gold.
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
- **Unique features suite** (all live at `/features/*` and on the `/features` page):
  - Time Machine, Narrative Tracker, Silence Detector
  - Consensus Breaker, Correlation Break, Did-I-Miss digest
  - Pattern Library, Confidence Calibration, Retail vs Institutional split
  - Asset Personality, Paper Bet (tracked accuracy), News Markers
  - Soft Push (tab badge), Contagion Map, Boring Day detector

## Stack

| Layer | Tech |
|---|---|
| Backend | FastAPI, SQLAlchemy 2, Alembic, APScheduler, Postgres (SQLite fallback) |
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

Backend (Postgres):
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e .
cp ../.env.example .env           # edit DATABASE_URL if not using docker's db
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

Backend (SQLite fallback for quick local hacking):
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e .
DATABASE_URL=sqlite:///./mni.db uvicorn app.main:app --reload --port 8000
```
SQLite path skips Alembic and creates tables via `Base.metadata.create_all`.

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

## Accessibility

- **Plain English mode**: a header toggle replaces every number on screen with a human label ("Overbought (cool-down likely)" instead of "RSI 72").
- **Persian localization**: full UI in فارسی with automatic RTL layout; toggle in the header.
- **Tooltips on jargon**: every technical term has a one-line explainer on hover (RSI, MA, sentiment, impact, stress, etc.).
- **Today's Brief**: a 3-sentence plain-English card at the top of the dashboard, auto-generated from mood + latest driver + next event. Refreshes every minute.

## Disclaimer

Informational and educational use only. MNI does not provide investment advice. Probabilistic output may be wrong. Do not make financial decisions based solely on MNI output.
