"""POST /screen route."""
from datetime import datetime
from fastapi import APIRouter
from models import ScreenRequest, ScreenResponse
import screener

router = APIRouter()

_SCREEN_FN = {
    'basic':     lambda req: screener.screen(top_n=req.top_n, interval=req.interval),
    'dip':       lambda req: screener.screen_dip(top_n=req.top_n, interval=req.interval),
    'breakout':  lambda req: screener.screen_breakout(top_n=req.top_n, interval=req.interval),
    'crypto':    lambda req: screener.screen_crypto(top_n=req.top_n, interval=req.interval),
    'optimized': lambda req: screener.screen_optimized(top_n=req.top_n,
                                                        min_confidence=req.min_confidence,
                                                        interval=req.interval),
    'combined':  lambda req: screener.screen_combined(top_n=req.top_n,
                                                       min_confidence=req.min_confidence,
                                                       interval=req.interval),
}


@router.post('/screen', response_model=ScreenResponse)
def run_screen(body: ScreenRequest):
    import config_cache
    warning = None
    if body.mode in ('optimized', 'combined') and not config_cache.get_configs():
        warning = 'strategy configs not loaded'

    fn = _SCREEN_FN[body.mode]
    candidates = fn(body)

    return ScreenResponse(
        mode=body.mode,
        interval=body.interval,
        count=len(candidates),
        screened_at=datetime.now().isoformat(timespec='seconds'),
        candidates=candidates,
        warning=warning,
    )
