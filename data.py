"""OHLCV data loader — cache-first, yfinance fallback."""
import logging
import os
from datetime import datetime, timedelta

import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)

CACHE_DIR = os.environ.get('DATA_CACHE_PATH', 'data_cache')


def load_ticker_data(ticker: str, years: int = 2, interval: str = '1d') -> pd.DataFrame | None:
    """Load OHLCV from cache (<12h old) or yfinance. Returns lowercase columns."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    cache_path = os.path.join(CACHE_DIR, f'{ticker}_{years}y.csv')

    if os.path.exists(cache_path):
        age_hours = (datetime.now().timestamp() - os.path.getmtime(cache_path)) / 3600
        if age_hours < 12:
            try:
                df = pd.read_csv(cache_path, index_col=0, parse_dates=True)
                df.columns = [c.lower() for c in df.columns]
                return df
            except Exception as e:
                logger.warning(f'Cache read failed for {ticker}: {e}')

    end = datetime.today()
    start = end - timedelta(days=years * 365 + 60)
    try:
        df = yf.download(
            ticker,
            start=start.strftime('%Y-%m-%d'),
            end=end.strftime('%Y-%m-%d'),
            interval=interval,
            progress=False,
            auto_adjust=True,
        )
        if df is None or df.empty:
            return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [col[0] for col in df.columns]
        df.to_csv(cache_path)
        df.columns = [c.lower() for c in df.columns]
        logger.info(f'Downloaded and cached {ticker} ({len(df)} bars)')
        return df
    except Exception as e:
        logger.error(f'yfinance download failed for {ticker}: {e}')
        return None
