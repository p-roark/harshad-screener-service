import os
import tempfile
import pandas as pd
import pytest
from unittest.mock import patch, MagicMock


def make_mock_df():
    import numpy as np
    n = 60
    prices = 20.0 + np.arange(n) * 0.1
    df = pd.DataFrame({
        'Open': prices * 0.999,
        'High': prices * 1.005,
        'Low': prices * 0.995,
        'Close': prices,
        'Volume': [1_000_000] * n,
    })
    return df


def test_load_ticker_data_uses_cache(tmp_path):
    """Returns cached data when cache file is fresh."""
    import data as data_module
    old_cache = data_module.CACHE_DIR
    data_module.CACHE_DIR = str(tmp_path)
    try:
        df = make_mock_df()
        df.to_csv(tmp_path / 'AAPL_2y.csv')
        result = data_module.load_ticker_data('AAPL', years=2, interval='1d')
        assert result is not None
        assert len(result) == 60
        assert 'close' in result.columns
    finally:
        data_module.CACHE_DIR = old_cache


def test_load_ticker_data_returns_lowercase_columns(tmp_path):
    """Loaded data always has lowercase column names."""
    import data as data_module
    old_cache = data_module.CACHE_DIR
    data_module.CACHE_DIR = str(tmp_path)
    try:
        df = make_mock_df()
        df.to_csv(tmp_path / 'MSFT_2y.csv')
        result = data_module.load_ticker_data('MSFT', years=2, interval='1d')
        assert result is not None
        for col in result.columns:
            assert col == col.lower(), f"Column {col!r} is not lowercase"
    finally:
        data_module.CACHE_DIR = old_cache


def test_tickers_lists_not_empty():
    """All ticker lists have entries."""
    from tickers import SP500_TICKERS, NDX100_TICKERS, CRYPTO_TICKERS, ALL_TICKERS
    assert len(SP500_TICKERS) > 50
    assert len(NDX100_TICKERS) > 50
    assert len(CRYPTO_TICKERS) >= 10
    assert len(ALL_TICKERS) > 100
