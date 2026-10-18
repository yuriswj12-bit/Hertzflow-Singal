from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal, Optional

Side = Literal["LONG", "SHORT"]

_SYMBOL = re.compile(
    r"(?:标的|资产|asset|symbol)\s*[:：]?\s*([A-Z0-9]{2,20}(?:USDT|USD|USDC)?)",
    re.I,
)
_SYMBOL_BARE = re.compile(r"\b([A-Z]{2,10}USDT)\b")
_SL = re.compile(
    r"(?:止损|sl)\s*[:：]?\s*([0-9]+(?:\.[0-9]+)?)",
    re.I,
)
_TP_TRAIL = re.compile(r"(?:止盈|tp)\s*[:：]?\s*(trailing|追踪)", re.I)
_TP_PRICE = re.compile(
    r"(?:止盈|tp)\s*[:：]?\s*([0-9]+(?:\.[0-9]+)?)",
    re.I,
)
_ENTRY = re.compile(
    r"(?:当前价|入场|entry)\s*[:：]?\s*([0-9]+(?:\.[0-9]+)?)",
    re.I,
)

_SHORT_HINTS = ("short", "做空", "空单", "空头", "sell")
_LONG_HINTS = ("long", "做多", "多单", "多头", "buy")


@dataclass(frozen=True)
class Signal:
    side: Side
    symbol: str
    stop_loss: float
    take_profit: float | None
    trailing: bool
    entry: float | None
    raw: str


def _side(text: str) -> Optional[Side]:
    low = text.lower()
    # Check explicit bilingual title tokens first.
    short_hit = any(h in low for h in _SHORT_HINTS) or "做空" in text or "空单" in text
    long_hit = any(h in low for h in _LONG_HINTS) or "做多" in text or "多单" in text
    if short_hit and not long_hit:
        return "SHORT"
    if long_hit and not short_hit:
        return "LONG"
    if short_hit and long_hit:
        # Title like "Short / 做空" counts as short; mixed junk is rejected.
        if low.find("short") >= 0 or "做空" in text:
            if low.find("long") < 0 and "做多" not in text:
                return "SHORT"
        return None
    return None


def _symbol(text: str) -> Optional[str]:
    m = _SYMBOL.search(text)
    if m:
        sym = m.group(1).upper()
        if not sym.endswith(("USDT", "USD", "USDC")):
            sym += "USDT"
        return sym
    m = _SYMBOL_BARE.search(text)
    return m.group(1).upper() if m else None


def parse_signal(text: str) -> Optional[Signal]:
    """Return a Signal only when direction + symbol + SL + TP are all present."""
    if not text or not text.strip():
        return None
    side = _side(text)
    symbol = _symbol(text)
    sl_m = _SL.search(text)
    trail = bool(_TP_TRAIL.search(text))
    tp_m = None if trail else _TP_PRICE.search(text)
    if not side or not symbol or not sl_m:
        return None
    if not trail and not tp_m:
        return None
    entry_m = _ENTRY.search(text)
    return Signal(
        side=side,
        symbol=symbol,
        stop_loss=float(sl_m.group(1)),
        take_profit=None if trail else float(tp_m.group(1)),
        trailing=trail,
        entry=float(entry_m.group(1)) if entry_m else None,
        raw=text,
    )
