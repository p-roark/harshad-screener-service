import pytest
from pydantic import ValidationError
from models import ScreenRequest, ScreenCandidate, ScreenResponse
from datetime import datetime


def test_screen_request_defaults():
    req = ScreenRequest()
    assert req.mode == 'combined'
    assert req.top_n == 10
    assert req.interval == '1d'
    assert req.min_confidence == 'MEDIUM'


def test_screen_request_valid_mode():
    for mode in ('basic', 'dip', 'breakout', 'crypto', 'optimized', 'combined'):
        req = ScreenRequest(mode=mode)
        assert req.mode == mode


def test_screen_request_invalid_mode():
    with pytest.raises(ValidationError):
        ScreenRequest(mode='unknown')


def test_screen_request_invalid_interval():
    with pytest.raises(ValidationError):
        ScreenRequest(interval='5m')


def test_screen_request_top_n_bounds():
    with pytest.raises(ValidationError):
        ScreenRequest(top_n=0)
    with pytest.raises(ValidationError):
        ScreenRequest(top_n=51)


def test_screen_response_shape():
    resp = ScreenResponse(
        mode='basic', interval='1d', count=0,
        screened_at='2026-04-27T10:00:00', candidates=[], warning=None,
    )
    assert resp.count == 0
    assert resp.warning is None
