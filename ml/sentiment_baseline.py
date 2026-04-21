"""Reference implementation of the MVP sentiment pipeline.

Kept importable so notebooks and batch jobs can reuse it without pulling in the
FastAPI app. The production service wraps the same logic in
`backend/app/services/sentiment.py`.
"""
from __future__ import annotations

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

_analyzer = SentimentIntensityAnalyzer()

FINANCE_LEXICON: dict[str, float] = {
    "hike": -0.3, "cut": 0.3, "bullish": 0.4, "bearish": -0.4,
    "surge": 0.3, "plunge": -0.4, "rally": 0.3, "crash": -0.5,
    "beat": 0.25, "miss": -0.25, "hawkish": -0.3, "dovish": 0.3,
    "recession": -0.4, "growth": 0.2,
}


def score(text: str) -> float:
    if not text:
        return 0.0
    base = _analyzer.polarity_scores(text)["compound"]
    lowered = text.lower()
    boost = sum(w for k, w in FINANCE_LEXICON.items() if k in lowered)
    return max(-1.0, min(1.0, base + 0.5 * boost))


if __name__ == "__main__":
    samples = [
        "Fed hikes rates 25bps, hawkish forward guidance",
        "ECB cuts rates, EUR weakens against USD",
        "Eurozone PMI beats expectations, growth surprise",
    ]
    for s in samples:
        print(f"{score(s):+.2f}  {s}")
