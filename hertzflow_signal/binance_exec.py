from __future__ import annotations

import logging
from dataclasses import asdict, dataclass
from typing import Any, Optional

from hertzflow_signal.config import Settings
from hertzflow_signal.parse import Signal

log = logging.getLogger("hertzflow")


@dataclass
class PlannedOrder:
    symbol: str
    side: str  # BUY / SELL
    position_side: str  # LONG / SHORT
    quote_usdt: float
    leverage: int
    stop_price: float
    take_profit: Optional[float]
    trailing: bool
    dry_run: bool


def _client(settings: Settings):
    from binance.client import Client

    client = Client(settings.binance_api_key, settings.binance_api_secret, testnet=settings.binance_testnet)
    if settings.binance_testnet:
        client.FUTURES_URL = "https://testnet.binancefuture.com/fapi"
    return client


def plan(signal: Signal, settings: Settings) -> PlannedOrder:
    return PlannedOrder(
        symbol=signal.symbol,
        side="SELL" if signal.side == "SHORT" else "BUY",
        position_side=signal.side,
        quote_usdt=settings.position_usdt,
        leverage=settings.leverage,
        stop_price=signal.stop_loss,
        take_profit=signal.take_profit,
        trailing=signal.trailing,
        dry_run=not settings.can_place_live,
    )


def _qty(client: Any, symbol: str, quote_usdt: float, price: float) -> str:
    info = client.futures_exchange_info()
    filt = next(s for s in info["symbols"] if s["symbol"] == symbol)
    step = 0.001
    min_qty = 0.0
    for f in filt["filters"]:
        if f["filterType"] == "LOT_SIZE":
            step = float(f["stepSize"])
            min_qty = float(f["minQty"])
    raw = quote_usdt / price
    precision = max(0, str(step)[::-1].find("."))
    qty = max(min_qty, (raw // step) * step)
    return f"{qty:.{precision}f}"


def execute(signal: Signal, settings: Settings) -> PlannedOrder:
    planned = plan(signal, settings)
    log.info("计划下单 %s", asdict(planned))
    if planned.dry_run:
        log.info("DRY_RUN=true，不下真单")
        return planned
    if not settings.binance_api_key or not settings.binance_api_secret:
        raise RuntimeError("LIVE 模式需要 BINANCE_API_KEY / BINANCE_API_SECRET")

    client = _client(settings)
    mark = float(client.futures_mark_price(symbol=signal.symbol)["markPrice"])
    band = settings.max_slippage_pct / 100.0
    if signal.side == "SHORT" and mark > signal.stop_loss:
        log.warning("标记价 %.6f 已在止损 %.6f 上方，跳过", mark, signal.stop_loss)
        return planned
    if signal.side == "LONG" and mark < signal.stop_loss:
        log.warning("标记价 %.6f 已在止损 %.6f 下方，跳过", mark, signal.stop_loss)
        return planned
    if signal.entry:
        drift = abs(mark - signal.entry) / signal.entry
        if drift > band:
            log.warning("相对帖内价格偏离 %.2f%% > 滑点上限，仍按市价但请人工确认", drift * 100)

    client.futures_change_leverage(symbol=signal.symbol, leverage=settings.leverage)
    qty = _qty(client, signal.symbol, settings.position_usdt, mark)
    client.futures_create_order(
        symbol=signal.symbol,
        side=planned.side,
        type="MARKET",
        quantity=qty,
        positionSide="BOTH",
    )
    sl_side = "BUY" if signal.side == "SHORT" else "SELL"
    client.futures_create_order(
        symbol=signal.symbol,
        side=sl_side,
        type="STOP_MARKET",
        stopPrice=signal.stop_loss,
        closePosition=True,
        workingType="MARK_PRICE",
    )
    if signal.trailing:
        client.futures_create_order(
            symbol=signal.symbol,
            side=sl_side,
            type="TRAILING_STOP_MARKET",
            callbackRate=1.0,
            quantity=qty,
            workingType="MARK_PRICE",
        )
    elif signal.take_profit is not None:
        client.futures_create_order(
            symbol=signal.symbol,
            side=sl_side,
            type="TAKE_PROFIT_MARKET",
            stopPrice=signal.take_profit,
            closePosition=True,
            workingType="MARK_PRICE",
        )
    log.info("已下单 %s %s qty=%s", planned.side, signal.symbol, qty)
    return planned
