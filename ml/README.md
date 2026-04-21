# ml/

Pure algorithms, free of DB and HTTP imports. The backend wraps these via `app/services/*`.
Today it is VADER + a formula. Swap `sentiment_baseline.py` for FinBERT and
`signal_formula.py` for an XGBoost model without touching the rest of the app.
