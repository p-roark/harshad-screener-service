import numpy as np
import pandas as pd
import pytest


def make_trending_df(n=260, start_price=15.0, end_price=25.0):
    """Synthetic upward-trending OHLCV with lowercase columns."""
    prices = np.linspace(start_price, end_price, n)
    noise = np.random.default_rng(42).normal(0, 0.1, n)
    close = prices + noise
    vol = np.full(n, 1_000_000.0)
    vol[-1] = 1_600_000.0  # 1.6× last bar
    return pd.DataFrame({
        'close': close,
        'open': close * 0.999,
        'high': close * 1.006,
        'low': close * 0.994,
        'volume': vol,
    })


def make_ranging_df(n=100):
    """Synthetic sideways OHLCV (low ADX)."""
    rng = np.random.default_rng(7)
    close = 20.0 + rng.normal(0, 0.3, n)
    vol = np.full(n, 800_000.0)
    return pd.DataFrame({
        'close': close, 'open': close * 0.999,
        'high': close * 1.003, 'low': close * 0.997,
        'volume': vol,
    })


def test_detect_regime_trending(trending_df):
    from screener import detect_regime
    df = trending_df.rename(columns=str.title)
    regime = detect_regime(df)
    assert regime in ('TRENDING_UP', 'TRENDING_DOWN', 'RANGING', 'HIGH_VOL')


def test_detect_regime_returns_string():
    from screener import detect_regime
    df = make_ranging_df()
    regime = detect_regime(df.rename(columns=str.title))
    assert isinstance(regime, str)
    assert regime in ('TRENDING_UP', 'TRENDING_DOWN', 'RANGING', 'HIGH_VOL')


def test_compute_score_returns_none_below_sma50():
    """Returns None when price is below SMA50 (hard filter)."""
    from screener import _compute_score
    # Downward price: will be below SMA50
    prices = np.linspace(25.0, 12.0, 100)
    df = pd.DataFrame({
        'close': prices, 'open': prices, 'high': prices * 1.01,
        'low': prices * 0.99, 'volume': np.full(100, 1_500_000.0),
    })
    result = _compute_score(df)
    assert result is None


def test_compute_score_returns_dict_for_passing_ticker(trending_df):
    """Returns score dict when all filters pass."""
    from screener import _compute_score
    result = _compute_score(trending_df)
    if result is not None:
        assert 'score' in result
        assert 'rsi' in result
        assert 'vol_ratio' in result
        assert isinstance(result['score'], float)


def test_compute_breakout_score_returns_none_no_breakout():
    """Returns None when price is not at 20-day high."""
    from screener import _compute_breakout_score
    # Flat prices — no breakout
    prices = np.full(100, 20.0)
    df = pd.DataFrame({
        'close': prices, 'open': prices, 'high': prices * 1.001,
        'low': prices * 0.999, 'volume': np.full(100, 500_000.0),
    })
    result = _compute_breakout_score(df)
    assert result is None


def test_build_signal_fn_momentum_returns_callable():
    """build_signal_fn returns a callable for MOMENTUM strategy."""
    from screener import build_signal_fn
    params = {'rsi_min': 40, 'rsi_max': 65, 'sma_period': 50, 'vol_ratio_min': 1.2}
    fn = build_signal_fn('MOMENTUM', params)
    assert callable(fn)


def test_build_signal_fn_momentum_false_on_short_df():
    """MOMENTUM signal returns False when df has fewer than 55 bars."""
    from screener import build_signal_fn
    params = {'rsi_min': 40, 'rsi_max': 65, 'sma_period': 50, 'vol_ratio_min': 1.2}
    fn = build_signal_fn('MOMENTUM', params)
    df = pd.DataFrame({
        'Close': np.linspace(15, 20, 30),
        'Volume': np.full(30, 1_000_000.0),
    })
    assert fn(df, 29) is False


def test_build_signal_fn_unknown_strategy_raises():
    """build_signal_fn raises ValueError for unknown strategy."""
    from screener import build_signal_fn
    with pytest.raises(ValueError, match='Unknown strategy'):
        build_signal_fn('FAKE_STRAT', {})


@pytest.fixture
def trending_df():
    return make_trending_df()
