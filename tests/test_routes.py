import pytest
from unittest.mock import patch
from tests.conftest import make_bullish_df


FAKE_CANDIDATE = {
    'ticker': 'AAPL', 'score': 0.65, 'rsi': 52.1, 'above_sma50': True,
    'vol_ratio': 1.5, 'momentum_5d': 1.2, 'ret_1m': 3.1, 'ret_3m': 8.4,
}


def test_health_endpoint(client):
    """GET /health returns 200 with strategy_configs_loaded field."""
    resp = client.get('/health')
    assert resp.status_code == 200
    data = resp.json()
    assert data['status'] == 'ok'
    assert 'strategy_configs_loaded' in data


def test_screen_basic_returns_200(client):
    """POST /screen mode=basic returns 200 with valid shape."""
    with patch('screener.screen', return_value=[FAKE_CANDIDATE]):
        resp = client.post('/screen', json={'mode': 'basic', 'top_n': 5})
    assert resp.status_code == 200
    data = resp.json()
    assert data['mode'] == 'basic'
    assert data['count'] == 1
    assert data['candidates'][0]['ticker'] == 'AAPL'
    assert 'screened_at' in data


def test_screen_dip_returns_200(client):
    """POST /screen mode=dip returns 200."""
    with patch('screener.screen_dip', return_value=[]):
        resp = client.post('/screen', json={'mode': 'dip'})
    assert resp.status_code == 200
    assert resp.json()['mode'] == 'dip'


def test_screen_breakout_returns_200(client):
    """POST /screen mode=breakout returns 200."""
    with patch('screener.screen_breakout', return_value=[FAKE_CANDIDATE]):
        resp = client.post('/screen', json={'mode': 'breakout'})
    assert resp.status_code == 200
    assert resp.json()['count'] == 1


def test_screen_crypto_returns_200(client):
    """POST /screen mode=crypto returns 200."""
    with patch('screener.screen_crypto', return_value=[]):
        resp = client.post('/screen', json={'mode': 'crypto'})
    assert resp.status_code == 200


def test_screen_optimized_empty_cache_returns_warning(client):
    """POST /screen mode=optimized with empty config cache returns warning."""
    with patch('screener.screen_optimized', return_value=[]):
        resp = client.post('/screen', json={'mode': 'optimized'})
    assert resp.status_code == 200
    data = resp.json()
    assert data['warning'] == 'strategy configs not loaded'
    assert data['candidates'] == []


def test_screen_combined_returns_200(client):
    """POST /screen mode=combined returns 200."""
    candidate_with_signals = {**FAKE_CANDIDATE, 'signal_count': 2,
                               'screeners_matched': ['MOMENTUM', 'BREAKOUT']}
    with patch('screener.screen_combined', return_value=[candidate_with_signals]):
        resp = client.post('/screen', json={'mode': 'combined', 'top_n': 10})
    assert resp.status_code == 200
    data = resp.json()
    assert data['candidates'][0]['signal_count'] == 2


def test_screen_invalid_mode_returns_422(client):
    """POST /screen with unknown mode returns 422."""
    resp = client.post('/screen', json={'mode': 'foobar'})
    assert resp.status_code == 422


def test_screen_top_n_zero_returns_422(client):
    """POST /screen with top_n=0 returns 422."""
    resp = client.post('/screen', json={'top_n': 0})
    assert resp.status_code == 422


def test_screen_invalid_interval_returns_422(client):
    """POST /screen with interval=5m returns 422."""
    resp = client.post('/screen', json={'interval': '5m'})
    assert resp.status_code == 422
