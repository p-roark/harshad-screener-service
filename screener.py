"""Screener logic — ported from trading bot screener.py and optimizer.py."""
from __future__ import annotations
import logging
import math
from typing import Callable

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────
RSI_MIN, RSI_MAX = 35, 65
VOLUME_RATIO_MIN = 1.2
MIN_PRICE = 10.0
MIN_BARS = 55
CRYPTO_MIN_PRICE = 0.01
DIP_RSI_MAX = 32
DIP_VOL_MIN = 1.5
DIP_MAX_DRAWDOWN = 0.35
BREAKOUT_RSI_MIN, BREAKOUT_RSI_MAX = 50, 80
BREAKOUT_VOLUME_RATIO_MIN = 2.0
BREAKOUT_LOOKBACK = 20

REGIME_STRATEGY_MAP = {
    'TRENDING_UP':   ['MOMENTUM', 'BREAKOUT', 'CROSS_MOMENTUM', '52WK_HIGH', 'MACD_ZERO', 'LOW_VOL', 'DUAL_MOM',
                      'MA_CROSS', 'TRI_MA', 'PIVOT_SR', 'TREND_RIDER', 'MACD_HIST', 'STOCH_RANGE', 'BB_BOUNCE',
                      'DONCHIAN', 'SUPERTREND', 'PARABOLIC_SAR', 'AROON_CROSS', 'OBV_TREND', 'ICHIMOKU'],
    'TRENDING_DOWN': ['MEAN_REVERT', 'RSI_2', 'PIVOT_SR'],
    'RANGING':       ['MEAN_REVERT', 'RSI_2', 'TTM_SQUEEZE', 'LOW_VOL', 'PIVOT_SR', 'BB_BOUNCE',
                      'WILLIAMS_R', 'CCI_REVERT'],
    'HIGH_VOL':      ['MEAN_REVERT', 'RSI_2'],
}


# ── Regime detection ──────────────────────────────────────────────────────────

def detect_regime(df: pd.DataFrame) -> str:
    """Detect price regime from Title-case OHLCV DataFrame."""
    try:
        import pandas_ta as ta
        col = lambda name: df[name] if name in df.columns else df[name.title()]
        close = col('close'); high = col('high'); low = col('low')
        if len(close) < 30:
            return 'RANGING'
        adx_df = ta.adx(high, low, close, length=14)
        adx_col = [c for c in adx_df.columns if c.startswith('ADX_')] if adx_df is not None else []
        adx = float(adx_df[adx_col[0]].iloc[-1]) if adx_col else 20.0
        sma200 = ta.sma(close, length=200)
        above_sma200 = (float(close.iloc[-1]) > float(sma200.iloc[-1])
                        if sma200 is not None and len(sma200) > 0 and not np.isnan(float(sma200.iloc[-1]))
                        else True)
        returns = close.pct_change().dropna()
        vol_20d = float(returns.iloc[-20:].std()) * (252 ** 0.5) if len(returns) >= 20 else 0.0
        if vol_20d > 0.50:
            return 'HIGH_VOL'
        if adx > 25:
            return 'TRENDING_UP' if above_sma200 else 'TRENDING_DOWN'
        return 'RANGING'
    except Exception:
        return 'RANGING'


# ── Composite score ───────────────────────────────────────────────────────────

def _compute_score(df: pd.DataFrame, min_price: float = MIN_PRICE) -> dict | None:
    """Composite score: RSI, SMA50, volume ratio, momentum, relative strength."""
    if df is None or len(df) < MIN_BARS:
        return None
    try:
        import pandas_ta as ta
    except ImportError:
        return None
    close = df['close']; volume = df['volume'].values
    if close.iloc[-1] < min_price:
        return None
    rsi_s = ta.rsi(close, length=14)
    rsi = float(rsi_s.iloc[-1]) if rsi_s is not None and len(rsi_s) else None
    if rsi is None or np.isnan(rsi) or rsi < RSI_MIN or rsi > RSI_MAX:
        return None
    sma50_s = ta.sma(close, length=50)
    sma50 = float(sma50_s.iloc[-1]) if sma50_s is not None and len(sma50_s) else None
    if not sma50 or close.iloc[-1] <= sma50:
        return None
    avg_vol = np.mean(volume[-21:-1]) if len(volume) >= 21 else np.mean(volume)
    vol_ratio = volume[-1] / avg_vol if avg_vol > 0 else 1.0
    if vol_ratio < VOLUME_RATIO_MIN:
        return None
    c = close.values
    mom = (c[-1] - c[-6]) / c[-6] if len(c) >= 6 and c[-6] > 0 else 0
    ret_1m = (c[-1] - c[-22]) / c[-22] if len(c) >= 22 and c[-22] > 0 else 0.0
    ret_3m = (c[-1] - c[-64]) / c[-64] if len(c) >= 64 and c[-64] > 0 else 0.0
    rs_score = max(0, min((ret_1m * 0.4 + ret_3m * 0.6) / 0.15, 1.0))
    score = (
        (rsi - 35) / 30 * 0.30
        + 1.0 * 0.30
        + min(vol_ratio / 3.0, 1.0) * 0.15
        + max(0, min(mom / 0.05, 1.0)) * 0.10
        + rs_score * 0.15
    )
    return {
        'rsi': round(rsi, 1),
        'above_sma50': True,
        'vol_ratio': round(vol_ratio, 2),
        'momentum_5d': round(mom * 100, 2),
        'ret_1m': round(ret_1m * 100, 2),
        'ret_3m': round(ret_3m * 100, 2),
        'score': round(score, 4),
    }


def _compute_breakout_score(df: pd.DataFrame) -> dict | None:
    """Breakout: new 20-day high + 2× volume + RSI 50-80."""
    if df is None or len(df) < MIN_BARS or len(df) < BREAKOUT_LOOKBACK + 1:
        return None
    try:
        import pandas_ta as ta
    except ImportError:
        return None
    close = df['close']; volume = df['volume'].values
    if close.iloc[-1] < MIN_PRICE:
        return None
    rsi_s = ta.rsi(close, length=14)
    rsi = float(rsi_s.iloc[-1]) if rsi_s is not None and len(rsi_s) else None
    if rsi is None or np.isnan(rsi) or rsi < BREAKOUT_RSI_MIN or rsi > BREAKOUT_RSI_MAX:
        return None
    prior_high = float(close.iloc[-(BREAKOUT_LOOKBACK + 1):-1].max())
    if close.iloc[-1] < prior_high:
        return None
    avg_vol = np.mean(volume[-21:-1]) if len(volume) >= 21 else np.mean(volume)
    vol_ratio = volume[-1] / avg_vol if avg_vol > 0 else 1.0
    if vol_ratio < BREAKOUT_VOLUME_RATIO_MIN:
        return None
    high_strength = (close.iloc[-1] - prior_high) / prior_high if prior_high > 0 else 0
    score = (
        min(high_strength / 0.02, 1.0) * 0.4
        + min(vol_ratio / 4.0, 1.0) * 0.4
        + (rsi - 50) / 30 * 0.2
    )
    sma50_s = ta.sma(close, length=50)
    sma50 = float(sma50_s.iloc[-1]) if sma50_s is not None and len(sma50_s) else None
    return {
        'rsi': round(rsi, 1),
        'above_sma50': bool(close.iloc[-1] > sma50) if sma50 else False,
        'vol_ratio': round(vol_ratio, 2),
        'high_breakout_pct': round(high_strength * 100, 2),
        'score': round(score, 4),
        'signal_type': 'BREAKOUT',
    }


# ── Signal functions (ported from optimizer.py build_signal_fn) ───────────────

def build_signal_fn(strategy: str, params: dict) -> Callable:
    """Return a (df, i) -> bool signal function. df must have Title-case columns."""
    try:
        import pandas_ta as ta
    except ImportError:
        return lambda df, i: False

    if strategy == 'MOMENTUM':
        _cache: dict = {}
        def fn(df, i):
            if i < 55: return False
            key = id(df)
            if key not in _cache:
                c = df['Close']; v = df['Volume']
                _cache[key] = {'close': c.values, 'vol': v.values,
                               'rsi': ta.rsi(c, length=14),
                               'sma': ta.sma(c, length=params['sma_period'])}
            d = _cache[key]
            if d['rsi'] is None or d['sma'] is None: return False
            cv = d['close'][i]
            if cv < 10: return False
            rsi = float(d['rsi'].iloc[i])
            if np.isnan(rsi) or rsi < params['rsi_min'] or rsi > params['rsi_max']: return False
            sma_v = float(d['sma'].iloc[i])
            if np.isnan(sma_v) or cv <= sma_v: return False
            vols = d['vol']
            avg = np.mean(vols[max(0, i-20):i]) if i > 0 else 0.0
            return bool(avg > 0 and vols[i] / avg >= params['vol_ratio_min'])
        return fn

    if strategy == 'BREAKOUT':
        _cache: dict = {}
        def fn(df, i):
            lb = params['lookback_days']
            if i < max(55, lb + 1): return False
            key = id(df)
            if key not in _cache:
                c = df['Close']; v = df['Volume']
                _cache[key] = {'close': c.values, 'vol': v.values, 'rsi': ta.rsi(c, length=14)}
            d = _cache[key]
            if d['rsi'] is None: return False
            rsi = float(d['rsi'].iloc[i])
            if np.isnan(rsi) or rsi < params['rsi_min'] or rsi > params['rsi_max']: return False
            prior_high = float(np.max(d['close'][max(0, i-lb):i]))
            if d['close'][i] < prior_high: return False
            vols = d['vol']
            avg = np.mean(vols[max(0, i-20):i]) if i > 0 else 0.0
            return bool(avg > 0 and vols[i] / avg >= params['vol_ratio_min'])
        return fn

    if strategy == 'RSI_2':
        _cache: dict = {}
        def fn(df, i):
            sma_len = params['sma_filter']
            if i < sma_len + 5: return False
            key = id(df)
            if key not in _cache:
                c = df['Close']
                _cache[key] = {'close': c.values, 'rsi2': ta.rsi(c, length=2),
                               'sma': ta.sma(c, length=sma_len)}
            d = _cache[key]
            if d['rsi2'] is None or d['sma'] is None: return False
            rsi2 = float(d['rsi2'].iloc[i])
            if np.isnan(rsi2) or rsi2 >= params['rsi2_threshold']: return False
            sma_v = float(d['sma'].iloc[i])
            return bool(not np.isnan(sma_v) and d['close'][i] > sma_v)
        return fn

    if strategy == 'TTM_SQUEEZE':
        _cache: dict = {}
        def fn(df, i):
            if i < 30: return False
            key = id(df)
            if key not in _cache:
                c = df['Close']; h = df['High']; lo = df['Low']
                bb = ta.bbands(c, length=20, std=params['bb_std'])
                atr = ta.atr(h, lo, c, length=14)
                ema20 = ta.ema(c, length=20)
                if bb is None or atr is None or ema20 is None:
                    _cache[key] = None
                else:
                    bbu_col = next((x for x in bb.columns if 'BBU' in x), None)
                    bbl_col = next((x for x in bb.columns if 'BBL' in x), None)
                    if not bbu_col or not bbl_col:
                        _cache[key] = None
                    else:
                        kc_u = ema20 + params['kc_multiplier'] * atr
                        kc_l = ema20 - params['kc_multiplier'] * atr
                        lr = ta.linreg(c - (bb[bbu_col] + bb[bbl_col]) / 2, length=params['linreg_length'])
                        _cache[key] = {'bbu': bb[bbu_col], 'bbl': bb[bbl_col],
                                       'kc_u': kc_u, 'kc_l': kc_l, 'lr': lr}
            d = _cache[key]
            if d is None or d['lr'] is None: return False
            for j in range(1, 6):
                ji = i - j
                if ji < 0: return False
                if float(d['bbu'].iloc[ji]) > float(d['kc_u'].iloc[ji]) or \
                   float(d['bbl'].iloc[ji]) < float(d['kc_l'].iloc[ji]):
                    return False
            fired = (float(d['bbu'].iloc[i]) > float(d['kc_u'].iloc[i]) or
                     float(d['bbl'].iloc[i]) < float(d['kc_l'].iloc[i]))
            if not fired: return False
            lr_v = float(d['lr'].iloc[i])
            return bool(not np.isnan(lr_v) and lr_v > 0)
        return fn

    if strategy == '52WK_HIGH':
        _cache: dict = {}
        def fn(df, i):
            if i < 252: return False
            key = id(df)
            if key not in _cache:
                c = df['Close']; v = df['Volume']
                _cache[key] = {'close': c.values, 'vol': v.values, 'rsi': ta.rsi(c, length=14)}
            d = _cache[key]
            if d['rsi'] is None: return False
            cv = d['close'][i]
            if cv < 10: return False
            high_52wk = float(np.max(d['close'][max(0, i-251):i+1]))
            if high_52wk == 0 or cv / high_52wk < params['proximity_pct']: return False
            rsi = float(d['rsi'].iloc[i])
            if np.isnan(rsi) or rsi < params['rsi_min'] or rsi > params['rsi_max']: return False
            vols = d['vol']
            avg = np.mean(vols[max(0, i-20):i]) if i > 0 else 0.0
            return bool(avg > 0 and vols[i] / avg >= params['vol_ratio_min'])
        return fn

    if strategy == 'MACD_ZERO':
        _cache: dict = {}
        def fn(df, i):
            sma_len = params.get('sma_filter', 200)
            if i < max(params['slow'] + 50, sma_len): return False
            key = id(df)
            if key not in _cache:
                c = df['Close']; h = df['High']; lo = df['Low']
                macd_df = ta.macd(c, fast=params['fast'], slow=params['slow'], signal=9)
                adx_df = ta.adx(h, lo, c, length=14)
                mcol = next((x for x in (macd_df.columns if macd_df is not None else [])
                             if x.startswith('MACD_') and 'h' not in x.lower() and 's' not in x.lower()), None)
                acol = next((x for x in (adx_df.columns if adx_df is not None else []) if x.startswith('ADX_')), None)
                _cache[key] = {'close': c.values,
                               'macd': macd_df[mcol] if (macd_df is not None and mcol) else None,
                               'adx': adx_df[acol] if (adx_df is not None and acol) else None,
                               'sma': ta.sma(c, length=sma_len)}
            d = _cache[key]
            if d['macd'] is None or d['adx'] is None or d['sma'] is None: return False
            if i < 1: return False
            mp, mc = float(d['macd'].iloc[i-1]), float(d['macd'].iloc[i])
            if np.isnan(mp) or np.isnan(mc) or not (mp < 0 < mc): return False
            sma_v = float(d['sma'].iloc[i])
            if np.isnan(sma_v) or d['close'][i] <= sma_v: return False
            adx_v = float(d['adx'].iloc[i])
            return bool(not np.isnan(adx_v) and adx_v > params['adx_threshold'])
        return fn

    if strategy == 'CROSS_MOMENTUM':
        _cache: dict = {}
        def fn(df, i):
            if i < 63: return False
            key = id(df)
            if key not in _cache:
                c = df['Close']; v = df['Volume']
                _cache[key] = {'close': c.values, 'vol': v.values,
                               'sma': ta.sma(c, length=params['sma_filter'])}
            d = _cache[key]
            if d['sma'] is None: return False
            cv = d['close'][i]
            if cv < 10: return False
            r1m = (cv - d['close'][i-22]) / d['close'][i-22] if i >= 22 and d['close'][i-22] > 0 else -1
            r3m = (cv - d['close'][i-64]) / d['close'][i-64] if i >= 64 and d['close'][i-64] > 0 else -1
            if r1m < params['ret_1m_min'] or r3m < params['ret_3m_min']: return False
            sma_v = float(d['sma'].iloc[i])
            if np.isnan(sma_v) or cv <= sma_v: return False
            vols = d['vol']
            avg = np.mean(vols[max(0, i-20):i]) if i > 0 else 0.0
            return bool(avg > 0 and vols[i] / avg >= params['vol_ratio_min'])
        return fn

    if strategy == 'MEAN_REVERT':
        _cache: dict = {}
        def fn(df, i):
            sma_len = params['sma_filter']
            if i < sma_len + 5: return False
            key = id(df)
            if key not in _cache:
                c = df['Close']
                bb = ta.bbands(c, length=20, std=params['bb_std'])
                bbl_col = next((x for x in (bb.columns if bb is not None else []) if 'BBL' in x), None)
                _cache[key] = {'close': c.values, 'rsi2': ta.rsi(c, length=2),
                               'bbl': bb[bbl_col] if (bb is not None and bbl_col) else None,
                               'sma': ta.sma(c, length=sma_len)}
            d = _cache[key]
            if d['rsi2'] is None or d['bbl'] is None or d['sma'] is None: return False
            cv = d['close'][i]
            if cv < 10: return False
            rsi2 = float(d['rsi2'].iloc[i])
            if np.isnan(rsi2) or rsi2 >= params['rsi2_threshold']: return False
            bbl_v = float(d['bbl'].iloc[i])
            if np.isnan(bbl_v) or cv >= bbl_v: return False
            sma_v = float(d['sma'].iloc[i])
            return bool(not np.isnan(sma_v) and cv > sma_v)
        return fn

    if strategy == 'LOW_VOL':
        _cache: dict = {}
        def fn(df, i):
            sma_len = params['sma_filter']
            if i < sma_len + 25: return False
            key = id(df)
            if key not in _cache:
                c = df['Close']
                _cache[key] = {'close': c.values, 'rets': c.pct_change().values,
                               'rsi': ta.rsi(c, length=14), 'sma': ta.sma(c, length=sma_len)}
            d = _cache[key]
            if d['rsi'] is None or d['sma'] is None: return False
            cv = d['close'][i]
            if cv < 10: return False
            window = d['rets'][max(0, i-19):i+1]
            clean = window[~np.isnan(window)]
            if len(clean) < 2: return False
            vol = float(np.std(clean)) * (252 ** 0.5)
            if np.isnan(vol) or vol >= params['vol_threshold']: return False
            sma_v = float(d['sma'].iloc[i])
            if np.isnan(sma_v) or cv <= sma_v: return False
            rsi = float(d['rsi'].iloc[i])
            return bool(not np.isnan(rsi) and params['rsi_min'] <= rsi <= params['rsi_max'])
        return fn

    if strategy == 'DUAL_MOM':
        _cache: dict = {}
        def fn(df, i):
            lookback = params.get('ret_lookback', 252)
            skip = params.get('ret_skip', 22)
            sma_len = params['sma_filter']
            if i < lookback + skip + sma_len: return False
            key = id(df)
            if key not in _cache:
                c = df['Close']; v = df['Volume']
                _cache[key] = {'close': c.values, 'vol': v.values, 'sma': ta.sma(c, length=sma_len)}
            d = _cache[key]
            if d['sma'] is None: return False
            cv = d['close'][i]
            if cv < 10: return False
            ps = d['close'][i - lookback - skip]; pe = d['close'][i - skip]
            if ps <= 0 or (pe - ps) / ps < params['ret_min']: return False
            sma_v = float(d['sma'].iloc[i])
            if np.isnan(sma_v) or cv <= sma_v: return False
            vols = d['vol']
            avg = np.mean(vols[max(0, i-20):i]) if i > 0 else 0.0
            return bool(avg > 0 and vols[i] / avg >= params['vol_ratio_min'])
        return fn

    if strategy == 'MA_CROSS':
        _cache: dict = {}
        def fn(df, i):
            fast, slow = params['fast'], params['slow']
            if fast >= slow or i < slow + 1: return False
            key = id(df)
            if key not in _cache:
                c = df['Close']
                _cache[key] = {'close': c.values, 'sma_fast': ta.sma(c, length=fast),
                               'sma_slow': ta.sma(c, length=slow), 'rsi': ta.rsi(c, length=14)}
            d = _cache[key]
            if d['sma_fast'] is None or d['sma_slow'] is None or d['rsi'] is None: return False
            cv = d['close'][i]
            if cv < 10: return False
            sf = float(d['sma_fast'].iloc[i]); ss = float(d['sma_slow'].iloc[i])
            if np.isnan(sf) or np.isnan(ss) or sf <= ss: return False
            rsi = float(d['rsi'].iloc[i])
            return bool(not np.isnan(rsi) and rsi >= params['rsi_min'])
        return fn

    if strategy == 'TRI_MA':
        _cache: dict = {}
        def fn(df, i):
            fast, mid, slow = params['fast'], params['mid'], params['slow']
            if not (fast < mid < slow) or i < slow + 1: return False
            key = id(df)
            if key not in _cache:
                c = df['Close']
                _cache[key] = {'close': c.values, 'sma_f': ta.sma(c, length=fast),
                               'sma_m': ta.sma(c, length=mid), 'sma_s': ta.sma(c, length=slow)}
            d = _cache[key]
            if d['sma_f'] is None or d['sma_m'] is None or d['sma_s'] is None: return False
            if d['close'][i] < 10: return False
            vf = float(d['sma_f'].iloc[i]); vm = float(d['sma_m'].iloc[i]); vs = float(d['sma_s'].iloc[i])
            if any(np.isnan(v) for v in (vf, vm, vs)): return False
            return bool(vf > vm > vs)
        return fn

    if strategy == 'PIVOT_SR':
        _cache: dict = {}
        def fn(df, i):
            lb = params['lookback']
            if i < lb + 1: return False
            key = id(df)
            if key not in _cache:
                c = df['Close']
                _cache[key] = {'close': c.values, 'high': df['High'].values,
                               'low': df['Low'].values, 'vol': df['Volume'].values,
                               'rsi': ta.rsi(c, length=14)}
            d = _cache[key]
            if d['rsi'] is None: return False
            cv = d['close'][i]
            if cv < 10: return False
            ph = float(np.mean(d['high'][i-lb:i])); pl = float(np.mean(d['low'][i-lb:i]))
            pc = float(np.mean(d['close'][i-lb:i]))
            pivot = (ph + pl + pc) / 3.0; resistance = 2.0 * pivot - pl
            if cv <= pivot or cv >= resistance: return False
            rsi = float(d['rsi'].iloc[i])
            if np.isnan(rsi) or rsi < params['rsi_filter']: return False
            vols = d['vol']
            avg = np.mean(vols[max(0, i-20):i]) if i > 0 else 0.0
            return bool(avg > 0 and vols[i] / avg >= params['vol_ratio_min'])
        return fn

    if strategy == 'DONCHIAN':
        _cache: dict = {}
        def fn(df, i):
            lb = params['lookback']
            if i < max(55, lb + 1): return False
            key = id(df)
            if key not in _cache:
                c = df['Close']; v = df['Volume']
                _cache[key] = {'close': c.values, 'vol': v.values, 'rsi': ta.rsi(c, length=14)}
            d = _cache[key]
            if d['rsi'] is None: return False
            cv = d['close'][i]
            if cv < 10: return False
            prior_high = float(np.max(d['close'][max(0, i-lb):i]))
            if cv <= prior_high: return False
            vols = d['vol']
            avg = np.mean(vols[max(0, i-20):i]) if i > 0 else 0.0
            if not (avg > 0 and vols[i] / avg >= params['vol_ratio_min']): return False
            rsi = float(d['rsi'].iloc[i])
            return bool(not np.isnan(rsi) and rsi < params['rsi_max'])
        return fn

    if strategy == 'SUPERTREND':
        _cache: dict = {}
        def fn(df, i):
            period = params['period']
            if i < period + 10: return False
            key = id(df)
            if key not in _cache:
                c = df['Close']; h = df['High']; lo = df['Low']
                st_df = ta.supertrend(h, lo, c, length=period, multiplier=params['multiplier'])
                d_col = next((x for x in (st_df.columns if st_df is not None else []) if x.startswith('SUPERTd')), None)
                _cache[key] = {'close': c.values,
                               'direction': st_df[d_col] if (st_df is not None and d_col) else None,
                               'rsi': ta.rsi(c, length=14)}
            d = _cache[key]
            if d['direction'] is None or d['rsi'] is None: return False
            if d['close'][i] < 10 or i < 1: return False
            pd_, cd_ = float(d['direction'].iloc[i-1]), float(d['direction'].iloc[i])
            if np.isnan(pd_) or np.isnan(cd_) or not (pd_ == -1 and cd_ == 1): return False
            rsi = float(d['rsi'].iloc[i])
            return bool(not np.isnan(rsi) and rsi >= params['rsi_min'])
        return fn

    if strategy == 'PARABOLIC_SAR':
        _cache: dict = {}
        def fn(df, i):
            if i < 30: return False
            key = id(df)
            if key not in _cache:
                c = df['Close']; h = df['High']; lo = df['Low']
                psar_df = ta.psar(h, lo, c, af0=0.02, af=0.02, max_af=params['max_af'])
                l_col = next((x for x in (psar_df.columns if psar_df is not None else []) if x.startswith('PSARl')), None)
                adx_df = ta.adx(h, lo, c, length=14)
                a_col = next((x for x in (adx_df.columns if adx_df is not None else []) if x.startswith('ADX_')), None)
                _cache[key] = {'close': c.values,
                               'psarl': psar_df[l_col] if (psar_df is not None and l_col) else None,
                               'adx': adx_df[a_col] if (adx_df is not None and a_col) else None}
            d = _cache[key]
            if d['psarl'] is None or d['adx'] is None: return False
            if d['close'][i] < 10 or i < 1: return False
            prev_nan = np.isnan(float(d['psarl'].iloc[i-1]))
            curr_nan = np.isnan(float(d['psarl'].iloc[i]))
            if not prev_nan or curr_nan: return False
            adx_v = float(d['adx'].iloc[i])
            return bool(not np.isnan(adx_v) and adx_v > params['adx_threshold'])
        return fn

    if strategy == 'AROON_CROSS':
        _cache: dict = {}
        def fn(df, i):
            period = params['period']
            if i < period + 5: return False
            key = id(df)
            if key not in _cache:
                c = df['Close']; h = df['High']; lo = df['Low']
                aroon_df = ta.aroon(h, lo, length=period)
                u_col = next((x for x in (aroon_df.columns if aroon_df is not None else []) if 'AROONU' in x), None)
                dc = next((x for x in (aroon_df.columns if aroon_df is not None else []) if 'AROOND' in x), None)
                _cache[key] = {'close': c.values,
                               'aroon_u': aroon_df[u_col] if (aroon_df is not None and u_col) else None,
                               'aroon_d': aroon_df[dc] if (aroon_df is not None and dc) else None,
                               'rsi': ta.rsi(c, length=14)}
            d = _cache[key]
            if d['aroon_u'] is None or d['aroon_d'] is None or d['rsi'] is None: return False
            if d['close'][i] < 10: return False
            au = float(d['aroon_u'].iloc[i]); ad = float(d['aroon_d'].iloc[i])
            if np.isnan(au) or np.isnan(ad) or au - ad < params['margin']: return False
            rsi = float(d['rsi'].iloc[i])
            return bool(not np.isnan(rsi) and rsi >= params['rsi_min'])
        return fn

    if strategy == 'WILLIAMS_R':
        _cache: dict = {}
        def fn(df, i):
            sma_len = params['sma_filter']; period = params['period']
            if i < max(sma_len, period + 2): return False
            key = id(df)
            if key not in _cache:
                c = df['Close']; h = df['High']; lo = df['Low']
                _cache[key] = {'close': c.values, 'willr': ta.willr(h, lo, c, length=period),
                               'sma': ta.sma(c, length=sma_len)}
            d = _cache[key]
            if d['willr'] is None or d['sma'] is None: return False
            cv = d['close'][i]
            if cv < 10: return False
            sma_v = float(d['sma'].iloc[i])
            if np.isnan(sma_v) or cv <= sma_v: return False
            if i < 1: return False
            wp, wc = float(d['willr'].iloc[i-1]), float(d['willr'].iloc[i])
            if np.isnan(wp) or np.isnan(wc): return False
            return bool(wp < params['oversold'] and wc >= params['oversold'])
        return fn

    if strategy == 'CCI_REVERT':
        _cache: dict = {}
        def fn(df, i):
            sma_len = params['sma_filter']; period = params['period']
            if i < max(sma_len, period + 2): return False
            key = id(df)
            if key not in _cache:
                c = df['Close']; h = df['High']; lo = df['Low']
                _cache[key] = {'close': c.values, 'cci': ta.cci(h, lo, c, length=period),
                               'sma': ta.sma(c, length=sma_len)}
            d = _cache[key]
            if d['cci'] is None or d['sma'] is None: return False
            cv = d['close'][i]
            if cv < 10: return False
            sma_v = float(d['sma'].iloc[i])
            if np.isnan(sma_v) or cv <= sma_v: return False
            if i < 1: return False
            cp, cc = float(d['cci'].iloc[i-1]), float(d['cci'].iloc[i])
            if np.isnan(cp) or np.isnan(cc): return False
            return bool(cp < params['oversold'] and cc >= params['oversold'])
        return fn

    if strategy == 'OBV_TREND':
        _cache: dict = {}
        def fn(df, i):
            obv_ma_len = params['obv_ma']; sma_len = params['sma_filter']
            if i < max(sma_len, obv_ma_len + 5): return False
            key = id(df)
            if key not in _cache:
                c = df['Close']; v = df['Volume']
                obv = ta.obv(c, v)
                _cache[key] = {'close': c.values, 'obv': obv,
                               'obv_ma': ta.sma(obv, length=obv_ma_len) if obv is not None else None,
                               'sma': ta.sma(c, length=sma_len), 'rsi': ta.rsi(c, length=14)}
            d = _cache[key]
            if d['obv'] is None or d['obv_ma'] is None or d['sma'] is None or d['rsi'] is None: return False
            cv = d['close'][i]
            if cv < 10: return False
            if float(d['obv'].iloc[i]) <= float(d['obv_ma'].iloc[i]): return False
            sma_v = float(d['sma'].iloc[i])
            if np.isnan(sma_v) or cv <= sma_v: return False
            rsi = float(d['rsi'].iloc[i])
            return bool(not np.isnan(rsi) and rsi >= params['rsi_min'])
        return fn

    if strategy == 'ICHIMOKU':
        _cache: dict = {}
        def fn(df, i):
            tenkan_len = params['tenkan']; kijun_len = params['kijun']
            senkou_len = kijun_len * 2
            if i < senkou_len + 5: return False
            key = id(df)
            if key not in _cache:
                _cache[key] = {'close': df['Close'].values, 'high': df['High'].values, 'low': df['Low'].values}
            d = _cache[key]
            cv = d['close'][i]
            if cv < 10: return False
            hi = d['high']; lo = d['low']
            s = i - tenkan_len + 1
            if s < 0: return False
            tenkan = (float(np.max(hi[s:i+1])) + float(np.min(lo[s:i+1]))) / 2.0
            ks = i - kijun_len + 1
            if ks < 0: return False
            kijun = (float(np.max(hi[ks:i+1])) + float(np.min(lo[ks:i+1]))) / 2.0
            if tenkan <= kijun: return False
            cloud_i = i - kijun_len
            if cloud_i < senkou_len: return False
            ss2 = i - kijun_len
            k2s = ss2 - kijun_len + 1
            if k2s < 0: return False
            senkou_b = (float(np.max(hi[k2s:ss2+1])) + float(np.min(lo[k2s:ss2+1]))) / 2.0
            return bool(cv > max(tenkan, kijun, senkou_b))
        return fn

    if strategy == 'TREND_RIDER':
        _cache: dict = {}
        def fn(df, i):
            fast = params['ema_fast']; slow = params['ema_slow']
            if i < slow + 10: return False
            key = id(df)
            if key not in _cache:
                c = df['Close']; h = df['High']; lo = df['Low']
                adx_df = ta.adx(h, lo, c, length=14)
                a_col = next((x for x in (adx_df.columns if adx_df is not None else []) if x.startswith('ADX_')), None)
                _cache[key] = {'close': c.values,
                               'ema_fast': ta.ema(c, length=fast),
                               'ema_slow': ta.ema(c, length=slow),
                               'adx': adx_df[a_col] if (adx_df is not None and a_col) else None}
            d = _cache[key]
            if d['ema_fast'] is None or d['ema_slow'] is None or d['adx'] is None: return False
            cv = d['close'][i]
            if cv < 10: return False
            ef = float(d['ema_fast'].iloc[i]); es = float(d['ema_slow'].iloc[i])
            if np.isnan(ef) or np.isnan(es) or ef <= es: return False
            if cv > ef * (1 + params['pullback_pct']) or cv < ef * (1 - params['pullback_pct']): return False
            adx_v = float(d['adx'].iloc[i])
            return bool(not np.isnan(adx_v) and adx_v < params['adx_max'])
        return fn

    if strategy == 'BB_BOUNCE':
        _cache: dict = {}
        def fn(df, i):
            ma_len = params['ma_period']; lb = params['lookback_bars']
            if i < ma_len + lb + 5: return False
            key = id(df)
            if key not in _cache:
                c = df['Close']
                bb = ta.bbands(c, length=ma_len, std=params['bb_std'])
                bbu_col = next((x for x in (bb.columns if bb is not None else []) if 'BBU' in x), None)
                bbm_col = next((x for x in (bb.columns if bb is not None else []) if 'BBM' in x), None)
                _cache[key] = {'close': c.values,
                               'bbu': bb[bbu_col] if (bb is not None and bbu_col) else None,
                               'bbm': bb[bbm_col] if (bb is not None and bbm_col) else None}
            d = _cache[key]
            if d['bbu'] is None or d['bbm'] is None: return False
            cv = d['close'][i]
            if cv < 10: return False
            touched = any(d['close'][i-j] >= float(d['bbu'].iloc[i-j])
                          for j in range(1, lb+1) if i-j >= 0)
            if not touched: return False
            ma_v = float(d['bbm'].iloc[i])
            if np.isnan(ma_v) or ma_v <= 0: return False
            return bool(abs(cv - ma_v) / ma_v <= 0.01)
        return fn

    if strategy == 'MACD_HIST':
        _cache: dict = {}
        def fn(df, i):
            slow = params['slow']
            if i < slow + 40: return False
            key = id(df)
            if key not in _cache:
                c = df['Close']
                macd_df = ta.macd(c, fast=params['fast'], slow=slow, signal=params['signal'])
                h_col = next((x for x in (macd_df.columns if macd_df is not None else []) if x.startswith('MACDh')), None)
                _cache[key] = {'close': c.values,
                               'hist': macd_df[h_col] if (macd_df is not None and h_col) else None}
            d = _cache[key]
            if d['hist'] is None: return False
            if d['close'][i] < 10: return False
            n = params['min_bars']
            if i < n - 1: return False
            recent = [float(d['hist'].iloc[i-j]) for j in range(n)]
            return bool(all(not np.isnan(v) and v > 0 for v in recent))
        return fn

    if strategy == 'STOCH_RANGE':
        _cache: dict = {}
        def fn(df, i):
            sma_len = params['sma_filter']; k_len = params['k_period']
            if i < max(sma_len, k_len + 10): return False
            key = id(df)
            if key not in _cache:
                c = df['Close']; h = df['High']; lo = df['Low']
                stoch_df = ta.stoch(h, lo, c, k=k_len, d=3, smooth_k=3)
                k_col = next((x for x in (stoch_df.columns if stoch_df is not None else []) if x.startswith('STOCHk')), None)
                _cache[key] = {'close': c.values,
                               'k': stoch_df[k_col] if (stoch_df is not None and k_col) else None,
                               'sma': ta.sma(c, length=sma_len)}
            d = _cache[key]
            if d['k'] is None or d['sma'] is None: return False
            cv = d['close'][i]
            if cv < 10: return False
            sma_v = float(d['sma'].iloc[i])
            if np.isnan(sma_v) or cv <= sma_v: return False
            if i < 1: return False
            kp, kc = float(d['k'].iloc[i-1]), float(d['k'].iloc[i])
            if np.isnan(kp) or np.isnan(kc): return False
            return bool(kp < params['oversold'] and kc >= params['oversold'])
        return fn

    if strategy == 'ORB':
        atr_buf = params['atr_buffer']; vol_min = params['vol_ratio_min']
        _cache: dict = {}
        def fn(df, i):
            if i < 2: return False
            key = id(df)
            if key not in _cache:
                c = df['Close']; h = df['High']; v = df['Volume']
                _cache[key] = {'close': c.values, 'high': h.values, 'vol': v.values,
                               'atr': ta.atr(h, df['Low'], c, length=14)}
            d = _cache[key]
            if d['atr'] is None: return False
            atr_v = float(d['atr'].iloc[i])
            if np.isnan(atr_v) or atr_v <= 0: return False
            threshold = d['high'][0] + atr_buf * atr_v
            if d['close'][i] <= threshold: return False
            avg_vol = np.mean(d['vol'][max(0, i-20):i]) if i > 0 else 0.0
            return bool(avg_vol > 0 and d['vol'][i] / avg_vol >= vol_min)
        return fn

    if strategy == 'VWAP_REVERT':
        dev = params['dev_pct']; rsi_max_v = params['rsi_max']
        _cache: dict = {}
        def fn(df, i):
            if i < 15: return False
            key = id(df)
            if key not in _cache:
                c = df['Close']; v = df['Volume']
                cum_vol = v.cumsum()
                vwap = (c * v).cumsum() / cum_vol.replace(0, np.nan)
                _cache[key] = {'close': c.values, 'vwap': vwap, 'rsi': ta.rsi(c, length=14)}
            d = _cache[key]
            if d['rsi'] is None: return False
            cv = d['close'][i]
            vwap_v = float(d['vwap'].iloc[i])
            if np.isnan(vwap_v) or vwap_v <= 0: return False
            vwap_prev = float(d['vwap'].iloc[i-1])
            if np.isnan(vwap_prev): return False
            was_below = d['close'][i-1] < vwap_prev * (1 - dev)
            back_above = cv >= vwap_v
            if not (was_below and back_above): return False
            rsi_v = float(d['rsi'].iloc[i])
            return bool(not np.isnan(rsi_v) and rsi_v <= rsi_max_v)
        return fn

    if strategy == 'GAP_FILL':
        gap_min = params['gap_min_pct']; rvol_min = params['rvol_min']
        _cache: dict = {}
        def fn(df, i):
            if i < 2: return False
            key = id(df)
            if key not in _cache:
                c = df['Close']; o = df['Open'] if 'Open' in df.columns else df['Close']; v = df['Volume']
                _cache[key] = {'close': c.values, 'open': o.values, 'vol': v.values}
            d = _cache[key]
            gap = (d['open'][i] - d['close'][i-1]) / d['close'][i-1] if d['close'][i-1] > 0 else 0
            if gap < gap_min: return False
            avg_vol = np.mean(d['vol'][max(0, i-20):i]) if i > 0 else 0.0
            if not (avg_vol > 0 and d['vol'][i] / avg_vol >= rvol_min): return False
            return bool(d['close'][i] < d['open'][i])
        return fn

    if strategy == 'RVOL_BREAKOUT':
        rvol_min = params['rvol_min']; lb = params['lookback']; atr_buf = params['atr_buffer']
        _cache: dict = {}
        def fn(df, i):
            if i < lb + 14: return False
            key = id(df)
            if key not in _cache:
                c = df['Close']; h = df['High']; v = df['Volume']
                _cache[key] = {'close': c.values, 'high': h.values, 'vol': v.values,
                               'atr': ta.atr(h, df['Low'], c, length=14)}
            d = _cache[key]
            if d['atr'] is None: return False
            atr_v = float(d['atr'].iloc[i])
            if np.isnan(atr_v) or atr_v <= 0: return False
            prior_high = np.max(d['high'][max(0, i-lb):i])
            if d['close'][i] <= prior_high + atr_buf * atr_v: return False
            avg_vol = np.mean(d['vol'][max(0, i-20):i]) if i > 0 else 0.0
            return bool(avg_vol > 0 and d['vol'][i] / avg_vol >= rvol_min)
        return fn

    raise ValueError(f'Unknown strategy: {strategy}')


# ── Screen functions ──────────────────────────────────────────────────────────

from data import load_ticker_data
from tickers import SP500_TICKERS, NDX100_TICKERS, MIDCAP_TICKERS, SMALLCAP_TICKERS, CRYPTO_TICKERS


def _equity_tickers() -> list[str]:
    return list(set(SP500_TICKERS + NDX100_TICKERS + MIDCAP_TICKERS + SMALLCAP_TICKERS))


def _compute_optimized_score(df: pd.DataFrame, strategy: str, params: dict, config: dict) -> dict | None:
    """Run strategy signal on last bar. df must have lowercase columns."""
    if df is None or len(df) < 260:
        return None
    try:
        import pandas_ta as ta
    except ImportError:
        return None
    try:
        fn = build_signal_fn(strategy, params)
    except Exception:
        return None
    df_titled = df.rename(columns=str.title)
    if not fn(df_titled, len(df_titled) - 1):
        return None
    close = df['close']
    volume = df['volume'].values
    rsi_s = ta.rsi(close, length=14)
    rsi = float(rsi_s.iloc[-1]) if rsi_s is not None and len(rsi_s) else None
    avg_vol = np.mean(volume[-21:-1]) if len(volume) >= 21 else np.mean(volume)
    vol_ratio = float(volume[-1]) / avg_vol if avg_vol > 0 else 1.0
    score = config.get('test_return', 0) / 100.0
    return {
        'rsi': round(rsi, 1) if rsi is not None and not np.isnan(rsi) else None,
        'vol_ratio': round(vol_ratio, 2),
        'score': round(score, 4),
        'strategy_name': strategy,
        'strategy_confidence': config.get('confidence', 'LOW'),
    }


def screen(top_n: int = 10, interval: str = '1d') -> list[dict]:
    """Basic composite screener across equity universe."""
    candidates = []
    for ticker in _equity_tickers():
        try:
            df = load_ticker_data(ticker, years=2, interval=interval)
            metrics = _compute_score(df)
            if metrics is not None:
                candidates.append({'ticker': ticker, **metrics})
        except Exception as e:
            logger.debug(f'Screener skip {ticker}: {e}')
    candidates.sort(key=lambda x: x['score'], reverse=True)
    return candidates[:top_n]


def screen_dip(top_n: int = 10, interval: str = '1d') -> list[dict]:
    """Dip-buy screener: oversold quality stocks during sell-offs."""
    try:
        import pandas_ta as ta
    except ImportError:
        return []
    candidates = []
    min_bars = 50 if interval != '1d' else 200
    for ticker in _equity_tickers():
        try:
            df = load_ticker_data(ticker, years=2, interval=interval)
            if df is None or len(df) < min_bars:
                continue
            close = df['close']; volume = df['volume'].values
            price = float(close.iloc[-1])
            if price < MIN_PRICE:
                continue
            rsi_s = ta.rsi(close, length=14)
            if rsi_s is None or len(rsi_s) == 0:
                continue
            rsi = float(rsi_s.iloc[-1])
            if np.isnan(rsi) or rsi >= DIP_RSI_MAX:
                continue
            avg_vol = np.mean(volume[-21:-1]) if len(volume) >= 21 else np.mean(volume)
            vol_ratio = float(volume[-1]) / avg_vol if avg_vol > 0 else 1.0
            if vol_ratio < DIP_VOL_MIN:
                continue
            sma200_s = ta.sma(close, length=200)
            if sma200_s is None or len(sma200_s) == 0:
                continue
            sma200 = float(sma200_s.iloc[-1])
            if np.isnan(sma200) or sma200 <= 0:
                continue
            drawdown = (sma200 - price) / sma200
            if drawdown > DIP_MAX_DRAWDOWN:
                continue
            rsi_score = (DIP_RSI_MAX - rsi) / DIP_RSI_MAX
            vol_score = min(vol_ratio / 5.0, 1.0)
            sma200_proximity = max(0, 1 - drawdown / DIP_MAX_DRAWDOWN)
            score = rsi_score * 0.5 + vol_score * 0.3 + sma200_proximity * 0.2
            candidates.append({
                'ticker': ticker, 'rsi': round(rsi, 1),
                'vol_ratio': round(vol_ratio, 2), 'score': round(score, 4),
                'above_sma50': False, 'drawdown_from_sma200_pct': round(drawdown * 100, 1),
            })
        except Exception as e:
            logger.debug(f'Dip screener skip {ticker}: {e}')
    candidates.sort(key=lambda x: x['score'], reverse=True)
    return candidates[:top_n]


def screen_breakout(top_n: int = 5, interval: str = '1d') -> list[dict]:
    """Breakout: new 20-bar high + 2× volume + RSI 50-80."""
    candidates = []
    for ticker in _equity_tickers():
        try:
            df = load_ticker_data(ticker, years=2, interval=interval)
            metrics = _compute_breakout_score(df)
            if metrics is not None:
                candidates.append({'ticker': ticker, **metrics})
        except Exception as e:
            logger.debug(f'Breakout screener skip {ticker}: {e}')
    candidates.sort(key=lambda x: x['score'], reverse=True)
    return candidates[:top_n]


def screen_crypto(top_n: int = 10, interval: str = '1d') -> list[dict]:
    """Crypto screener using composite score with optional strategy signal."""
    import config_cache
    configs = config_cache.get_configs()
    candidates = []
    for ticker in CRYPTO_TICKERS:
        try:
            df = load_ticker_data(ticker, years=2, interval=interval)
            if df is None or len(df) < MIN_BARS:
                continue
            cfg = configs.get(ticker)
            if cfg and not cfg.get('fallback'):
                df_titled = df.rename(columns=str.title)
                regime = detect_regime(df_titled)
                allowed = REGIME_STRATEGY_MAP.get(regime, [])
                strategy = cfg.get('strategy', '')
                if strategy in allowed or not allowed:
                    try:
                        metrics = _compute_optimized_score(df, strategy, cfg.get('params', {}), cfg)
                        if metrics:
                            candidates.append({'ticker': ticker, 'regime': regime, **metrics})
                            continue
                    except Exception:
                        pass
            metrics = _compute_score(df, min_price=CRYPTO_MIN_PRICE)
            if metrics is not None:
                candidates.append({'ticker': ticker, **metrics})
        except Exception as e:
            logger.debug(f'Crypto screener skip {ticker}: {e}')
    candidates.sort(key=lambda x: x['score'], reverse=True)
    return candidates[:top_n]


def screen_optimized(top_n: int = 10, min_confidence: str = 'MEDIUM', interval: str = '1d') -> list[dict]:
    """Strategy-signal screener using cached configs from strategy-service."""
    import config_cache
    configs = config_cache.get_configs()
    if not configs:
        return []
    _conf_rank = {'HIGH': 2, 'MEDIUM': 1, 'LOW': 0}
    min_rank = _conf_rank.get(min_confidence, 1)
    candidates = []
    for ticker, cfg in configs.items():
        try:
            if cfg.get('fallback') or not cfg.get('strategy'):
                continue
            if _conf_rank.get(cfg.get('confidence', 'LOW'), 0) < min_rank:
                continue
            df = load_ticker_data(ticker, years=2, interval=interval)
            if df is None:
                continue
            regime = detect_regime(df.rename(columns=str.title))
            preferred = REGIME_STRATEGY_MAP.get(regime, [])
            chosen_cfg = cfg
            for s in cfg.get('top3', []):
                if s.get('strategy') in preferred:
                    chosen_cfg = s
                    break
            metrics = _compute_optimized_score(df, chosen_cfg['strategy'],
                                               chosen_cfg.get('params', {}), chosen_cfg)
            if metrics is not None:
                candidates.append({'ticker': ticker, 'regime': regime, **metrics})
        except Exception as e:
            logger.debug(f'Optimized screener skip {ticker}: {e}')
    candidates.sort(key=lambda x: (_conf_rank.get(x.get('strategy_confidence', 'LOW'), 0),
                                    x['score']), reverse=True)
    return candidates[:top_n]


def screen_combined(top_n: int = 10, min_confidence: str = 'MEDIUM', interval: str = '1d') -> list[dict]:
    """Run all 4 modes, merge, boost multi-screener hits."""
    _conf_rank = {'HIGH': 2, 'MEDIUM': 1, 'LOW': 0}
    all_results: dict[str, dict] = {}

    def _merge(candidates: list[dict], screener_name: str) -> None:
        for c in candidates:
            t = c['ticker']
            if t in all_results:
                all_results[t]['screeners_matched'].append(screener_name)
                all_results[t]['signal_count'] += 1
                if c.get('score', 0) > all_results[t].get('score', 0):
                    all_results[t]['score'] = c['score']
            else:
                all_results[t] = {**c, 'screeners_matched': [screener_name], 'signal_count': 1}

    try:
        _merge(screen(top_n=50, interval=interval), 'MOMENTUM')
    except Exception as e:
        logger.debug(f'screen_combined: MOMENTUM error: {e}')
    try:
        _merge(screen_breakout(top_n=20, interval=interval), 'BREAKOUT')
    except Exception as e:
        logger.debug(f'screen_combined: BREAKOUT error: {e}')
    try:
        _merge(screen_optimized(top_n=20, min_confidence=min_confidence, interval=interval), 'OPTIMIZED')
    except Exception as e:
        logger.debug(f'screen_combined: OPTIMIZED error: {e}')
    try:
        _merge(screen_dip(top_n=20, interval=interval), 'DIP')
    except Exception as e:
        logger.debug(f'screen_combined: DIP error: {e}')

    combined = list(all_results.values())
    combined.sort(key=lambda x: (x['signal_count'],
                                  _conf_rank.get(x.get('strategy_confidence', 'LOW'), 0),
                                  x.get('score', 0)), reverse=True)
    return combined[:top_n]
