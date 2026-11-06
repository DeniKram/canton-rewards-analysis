"""Concentration metrics for a vector of weights.

All functions take a 1-D array-like of non-negative weights, shape (n,).

Worked example, weights = [40, 30, 20, 10]  -> shares s = [0.4, 0.3, 0.2, 0.1]
    HHI          = 0.16 + 0.09 + 0.04 + 0.01 = 0.30
    top_k(k=1)   = 0.40
    nakamoto(1/3)= 1   (the largest alone holds 40% > 33.3%)
    nakamoto(2/3)= 2   (40+30 = 70% > 66.7%)
    gini         = 0.25
"""
import numpy as np


def shares(weights) -> np.ndarray:
    w = np.asarray(weights, dtype=float)
    total = w.sum()
    if total <= 0:
        raise ValueError("total weight must be positive")
    return w / total


def hhi(weights) -> float:
    """Herfindahl-Hirschman index on shares, in [1/n, 1]."""
    s = shares(weights)
    return float(np.sum(s ** 2))


def effective_n(weights) -> float:
    """1 / HHI: how many equal-sized SVs would give the same concentration."""
    return 1.0 / hhi(weights)


def top_k_share(weights, k: int) -> float:
    s = np.sort(shares(weights))[::-1]
    return float(s[:k].sum())


def nakamoto(weights, threshold: float) -> int:
    """Smallest number of largest holders whose combined share is STRICTLY above threshold.

    threshold=1/3: enough weight to block BFT consensus
    threshold=2/3: enough weight to control it
    """
    s = np.sort(shares(weights))[::-1]
    cum = np.cumsum(s)
    return int(np.argmax(cum > threshold) + 1)


def gini(weights) -> float:
    """Gini coefficient, 0 = perfectly equal, ->1 = one holder has everything."""
    w = np.sort(np.asarray(weights, dtype=float))  # ascending, shape (n,)
    n = w.size
    idx = np.arange(1, n + 1)
    return float((2 * np.sum(idx * w)) / (n * w.sum()) - (n + 1) / n)


def lorenz(weights) -> tuple[np.ndarray, np.ndarray]:
    """Lorenz curve points, both arrays shape (n+1,), starting at (0, 0)."""
    w = np.sort(np.asarray(weights, dtype=float))
    x = np.linspace(0, 1, w.size + 1)
    y = np.concatenate([[0.0], np.cumsum(w) / w.sum()])
    return x, y


def summary(weights) -> dict:
    w = np.asarray(weights, dtype=float)
    return {
        "n": int(w.size),
        "total_weight": float(w.sum()),
        "hhi": hhi(w),
        "effective_n": effective_n(w),
        "top1_share": top_k_share(w, 1),
        "top5_share": top_k_share(w, 5),
        "top10_share": top_k_share(w, 10),
        "nakamoto_1_3": nakamoto(w, 1 / 3),
        "nakamoto_2_3": nakamoto(w, 2 / 3),
        "gini": gini(w),
    }
