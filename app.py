"""FastAPI application for harshad-screener-service."""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
import config_cache
from routes import router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app):
    logger.info("Loading strategy configs from strategy-service...")
    config_cache.load_configs()
    config_cache.start_monthly_refresh()
    yield
    config_cache.stop_refresh()


app = FastAPI(title='harshad-screener-service', version='0.1.0', lifespan=lifespan)
app.include_router(router)


@app.get('/health')
def health():
    return {'status': 'ok', 'strategy_configs_loaded': len(config_cache.get_configs())}
