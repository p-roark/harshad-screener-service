import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient


def make_bullish_df(n=100):
    """Synthetic upward-trending OHLCV for screener tests."""
    prices = np.linspace(15.0, 25.0, n)
    prices += np.random.default_rng(99).normal(0, 0.05, n)
    vol = np.full(n, 1_000_000.0)
    vol[-1] = 1_600_000.0
    return pd.DataFrame({
        'close': prices, 'open': prices * 0.999,
        'high': prices * 1.006, 'low': prices * 0.994,
        'volume': vol,
    })


@pytest.fixture
def client():
    from app import app
    return TestClient(app)
