"""HTTP client for harshad-strategy-service (8003)."""
from __future__ import annotations
import logging
import os
import httpx

logger = logging.getLogger(__name__)
_DEFAULT_URL = os.environ.get('STRATEGY_SERVICE_URL', 'http://localhost:8003')


class StrategyServiceClient:
    def __init__(self, base_url: str = _DEFAULT_URL):
        self.base_url = base_url.rstrip('/')

    def list_strategies(self) -> list[str]:
        """Return list of strategy names."""
        r = httpx.get(f'{self.base_url}/strategies', timeout=10)
        r.raise_for_status()
        return [s['name'] for s in r.json()]

    def get_ticker_results(self, ticker: str, interval: str = '1d') -> list[dict]:
        """Return all strategy results for a ticker."""
        r = httpx.get(f'{self.base_url}/results/{ticker}',
                      params={'interval': interval}, timeout=10)
        r.raise_for_status()
        return r.json()
