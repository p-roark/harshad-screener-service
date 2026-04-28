"""Pydantic models for harshad-screener-service."""
from __future__ import annotations
from typing import Literal, Optional
from pydantic import BaseModel, field_validator


class ScreenRequest(BaseModel):
    mode: Literal['basic', 'dip', 'breakout', 'crypto', 'optimized', 'combined'] = 'combined'
    top_n: int = 10
    interval: Literal['1d', '1h'] = '1d'
    min_confidence: Literal['HIGH', 'MEDIUM', 'LOW'] = 'MEDIUM'

    @field_validator('top_n')
    @classmethod
    def top_n_in_range(cls, v: int) -> int:
        if v < 1 or v > 50:
            raise ValueError('top_n must be between 1 and 50')
        return v


class ScreenCandidate(BaseModel):
    ticker: str
    score: float
    rsi: Optional[float] = None
    above_sma50: Optional[bool] = None
    vol_ratio: Optional[float] = None
    momentum_5d: Optional[float] = None
    ret_1m: Optional[float] = None
    ret_3m: Optional[float] = None
    high_breakout_pct: Optional[float] = None
    drawdown_from_sma200_pct: Optional[float] = None
    signal_count: Optional[int] = None
    screeners_matched: Optional[list[str]] = None
    strategy_name: Optional[str] = None
    strategy_confidence: Optional[str] = None
    regime: Optional[str] = None


class ScreenResponse(BaseModel):
    mode: str
    interval: str
    count: int
    screened_at: str
    candidates: list[ScreenCandidate]
    warning: Optional[str] = None
