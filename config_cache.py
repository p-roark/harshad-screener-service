"""In-memory strategy config cache. Refreshed monthly from strategy-service."""
from __future__ import annotations
import logging
import os

logger = logging.getLogger(__name__)

_configs: dict = {}
_scheduler = None

OPTIMIZER_TICKERS = os.environ.get(
    'OPTIMIZER_TICKERS',
    'AAPL,MSFT,TSLA,GOOGL,AMZN,NVDA,META,SPY,QQQ,BABA,ORCL,CRM,ADBE,AMD,INTC,'
    'JPM,BAC,GS,V,MA,WFC,JNJ,PFE,ABBV,MRK,XOM,CVX,COP,CAT,DE,HON,UPS,NFLX,'
    'DIS,CMCSA,SBUX,MCD,COST,WMT,HD,LOW,TGT,AMGN,GILD,REGN,VRTX,ISRG,'
    'BTC-USD,ETH-USD,SOL-USD,BNB-USD,XRP-USD'
).split(',')


def get_configs() -> dict:
    """Return current in-memory config cache."""
    return _configs


def load_configs() -> None:
    """Fetch strategy configs from strategy-service and populate cache."""
    from clients.strategy import StrategyServiceClient
    global _configs
    _conf_rank = {'HIGH': 2, 'MEDIUM': 1, 'LOW': 0}
    new_configs: dict = {}
    client = StrategyServiceClient()
    loaded = 0
    errors = 0
    for ticker in OPTIMIZER_TICKERS:
        try:
            results = client.get_ticker_results(ticker)
            if not results:
                continue
            best = max(results, key=lambda r: (
                _conf_rank.get(r.get('confidence', 'LOW'), 0),
                r.get('test_return') or 0,
            ))
            new_configs[ticker] = {
                'strategy': best['strategy_name'],
                'params': best.get('params') or {},
                'confidence': best.get('confidence', 'MEDIUM'),
                'test_return': best.get('test_return') or 0,
                'win_rate': best.get('win_rate') or 0,
                'trade_count': best.get('trade_count') or 0,
                'fallback': False,
                'top3': [
                    {'strategy': r['strategy_name'], 'params': r.get('params') or {},
                     'confidence': r.get('confidence', 'LOW')}
                    for r in sorted(results,
                                    key=lambda r: (_conf_rank.get(r.get('confidence', 'LOW'), 0),
                                                   r.get('test_return') or 0),
                                    reverse=True)[:3]
                ],
            }
            loaded += 1
        except Exception as e:
            logger.debug(f'Config cache skip {ticker}: {e}')
            errors += 1
    if new_configs:
        _configs = new_configs
        logger.info(f'Config cache loaded: {loaded} tickers ({errors} errors)')
    else:
        logger.warning(f'Config cache empty after load ({errors} errors) — strategy-service may be down')


def start_monthly_refresh() -> None:
    """Start APScheduler to refresh configs on the 1st of each month at 03:00 UTC."""
    global _scheduler
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        _scheduler = BackgroundScheduler()
        _scheduler.add_job(load_configs, trigger='cron', day=1, hour=3, minute=0,
                           name='monthly_config_refresh')
        _scheduler.start()
        logger.info('Config cache monthly refresh scheduled (1st of month, 03:00 UTC)')
    except Exception as e:
        logger.warning(f'Failed to start config refresh scheduler: {e}')


def stop_refresh() -> None:
    global _scheduler
    if _scheduler:
        _scheduler.shutdown()
        _scheduler = None
