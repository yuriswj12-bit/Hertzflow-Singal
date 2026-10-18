from __future__ import annotations

import logging
from pathlib import Path

from telethon import TelegramClient, events

from hertzflow_signal.binance_exec import execute
from hertzflow_signal.config import Settings
from hertzflow_signal.parse import parse_signal
from hertzflow_signal.state import State

log = logging.getLogger("hertzflow")


def _text(message) -> str:
    return (message.message or "") + "\n" + (message.text or "")


async def run_listener(settings: Settings) -> None:
    Path(settings.telegram_session).parent.mkdir(parents=True, exist_ok=True)
    settings.state_path.parent.mkdir(parents=True, exist_ok=True)
    state = State(settings.state_path)
    client = TelegramClient(
        settings.telegram_session,
        settings.telegram_api_id,
        settings.telegram_api_hash,
    )
    await client.start()
    entity = await client.get_entity(settings.telegram_channel)
    log.info("开始监听 @%s  dry_run=%s live=%s", settings.telegram_channel, settings.dry_run, settings.live)

    @client.on(events.NewMessage(chats=entity))
    async def on_new(event):  # type: ignore[no-untyped-def]
        msg = event.message
        if state.seen(msg.id):
            return
        text = msg.message or ""
        signal = parse_signal(text)
        state.mark(msg.id)
        if signal is None:
            log.info("忽略非交易帖 message_id=%s", msg.id)
            return
        if signal.symbol in state.open_symbols and not settings.dry_run:
            log.info("已有仓位 %s，跳过", signal.symbol)
            return
        log.info("识别到信号 %s %s SL=%s TP=%s trailing=%s", signal.side, signal.symbol, signal.stop_loss, signal.take_profit, signal.trailing)
        try:
            execute(signal, settings)
            if not settings.dry_run:
                state.open_symbols.add(signal.symbol)
                state.save()
        except Exception:
            log.exception("下单失败 %s", signal.symbol)

    await client.run_until_disconnected()
