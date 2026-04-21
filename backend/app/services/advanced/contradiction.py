"""Market contradiction detector.

Rule: if aggregate news sentiment over last 6h is clearly directional but the
price return over the same window moves the other way, the market is pricing
opposite the news. This is a smart-money-vs-retail proxy.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ContradictionResult:
    flagged: bool
    direction: str  # "opposite" | "aligned" | "unclear"
    news_bias: float
    price_return: float
    note: str


def detect(sentiment_6h: float, price_return_6h: float) -> ContradictionResult:
    sentiment_strong = abs(sentiment_6h) >= 0.2
    price_strong = abs(price_return_6h) >= 0.001  # 10 bps for FX; looser for crypto
    if not sentiment_strong or not price_strong:
        return ContradictionResult(False, "unclear", sentiment_6h, price_return_6h, "insufficient directional signal")
    same_sign = (sentiment_6h > 0) == (price_return_6h > 0)
    if same_sign:
        return ContradictionResult(
            False, "aligned", sentiment_6h, price_return_6h, "news and price agree",
        )
    note = (
        "Sentiment positive but price down: possible distribution into good news"
        if sentiment_6h > 0
        else "Sentiment negative but price up: possible absorption / short squeeze"
    )
    return ContradictionResult(True, "opposite", sentiment_6h, price_return_6h, note)
