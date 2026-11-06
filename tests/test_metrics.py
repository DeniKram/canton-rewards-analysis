"""Hand-checked values for weights [40, 30, 20, 10]. Run: python -m pytest tests"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from metrics import effective_n, gini, hhi, nakamoto, top_k_share  # noqa: E402

W = [40, 30, 20, 10]


def test_hhi():
    assert hhi(W) == pytest.approx(0.30)
    assert effective_n(W) == pytest.approx(1 / 0.30)


def test_equal_weights_hhi_is_one_over_n():
    assert hhi([5, 5, 5, 5]) == pytest.approx(0.25)
    assert gini([5, 5, 5, 5]) == pytest.approx(0.0)


def test_top_k():
    assert top_k_share(W, 1) == pytest.approx(0.40)
    assert top_k_share(W, 2) == pytest.approx(0.70)


def test_nakamoto():
    assert nakamoto(W, 1 / 3) == 1
    assert nakamoto(W, 2 / 3) == 2
    assert nakamoto([1] * 9, 1 / 3) == 4  # 3/9 is not strictly above 1/3


def test_gini():
    assert gini(W) == pytest.approx(0.25)
