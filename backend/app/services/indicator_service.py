from __future__ import annotations


def _closes(klines: list[dict]) -> list[float]:
    return [float(item["close"]) for item in klines]


def sma(values: list[float], period: int) -> float | None:
    if len(values) < period:
        return None
    window = values[-period:]
    return sum(window) / period


def rsi(values: list[float], period: int = 14) -> float | None:
    if len(values) <= period:
        return None
    gains = []
    losses = []
    for previous, current in zip(values[:-1], values[1:]):
        change = current - previous
        gains.append(max(change, 0))
        losses.append(abs(min(change, 0)))
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def compute_indicators(klines: list[dict]) -> dict:
    closes = _closes(klines)
    if not closes:
        return {}
    latest = closes[-1]
    sma_10 = sma(closes, 10)
    sma_20 = sma(closes, 20)
    momentum_5 = None if len(closes) < 6 else (latest - closes[-6]) / closes[-6]
    return {
        "last_close": latest,
        "sma_10": sma_10,
        "sma_20": sma_20,
        "rsi_14": rsi(closes, 14),
        "momentum_5": momentum_5,
    }
