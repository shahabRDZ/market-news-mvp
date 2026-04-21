from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

_analyzer = SentimentIntensityAnalyzer()

FINANCE_LEXICON: dict[str, float] = {
    "hike": -0.3,
    "hikes": -0.3,
    "cut": 0.3,
    "cuts": 0.3,
    "bullish": 0.4,
    "bearish": -0.4,
    "surge": 0.3,
    "plunge": -0.4,
    "rally": 0.3,
    "crash": -0.5,
    "beat": 0.25,
    "miss": -0.25,
    "hawkish": -0.3,
    "dovish": 0.3,
    "inflation": -0.1,
    "recession": -0.4,
    "growth": 0.2,
    "default": -0.4,
    "surprise": 0.15,
}


def _lexicon_boost(text: str) -> float:
    lowered = text.lower()
    boost = 0.0
    for word, weight in FINANCE_LEXICON.items():
        if word in lowered:
            boost += weight
    return boost


def score(text: str) -> float:
    if not text:
        return 0.0
    base = _analyzer.polarity_scores(text)["compound"]
    adjusted = base + 0.5 * _lexicon_boost(text)
    return max(-1.0, min(1.0, adjusted))


def impact_class(sentiment: float, keyword_hits: int) -> str:
    magnitude = abs(sentiment) + 0.1 * keyword_hits
    if magnitude >= 0.6:
        return "HIGH"
    if magnitude >= 0.3:
        return "MED"
    return "LOW"


def count_keywords(text: str) -> int:
    lowered = text.lower()
    return sum(1 for word in FINANCE_LEXICON if word in lowered)
