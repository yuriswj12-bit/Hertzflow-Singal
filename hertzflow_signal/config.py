from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field


class Settings(BaseModel):
    telegram_api_id: int
    telegram_api_hash: str
    telegram_session: str = "data/hertzflow"
    telegram_channel: str = "hertzflowcrypto"
    binance_api_key: str = ""
    binance_api_secret: str = ""
    binance_testnet: bool = True
    dry_run: bool = True
    live: bool = False
    position_usdt: float = 50.0
    leverage: int = 1
    max_slippage_pct: float = 1.5
    state_path: Path = Field(default_factory=lambda: Path("data/state.json"))

    @property
    def can_place_live(self) -> bool:
        return self.live and not self.dry_run


def _b(name: str, default: bool) -> bool:
    import os
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def load_settings() -> Settings:
    load_dotenv()
    import os

    api_id = os.getenv("TELEGRAM_API_ID", "").strip()
    api_hash = os.getenv("TELEGRAM_API_HASH", "").strip()
    if not api_id or not api_hash:
        raise SystemExit("缺少 TELEGRAM_API_ID / TELEGRAM_API_HASH，先复制 .env.example 为 .env 再填。")
    return Settings(
        telegram_api_id=int(api_id),
        telegram_api_hash=api_hash,
        telegram_session=os.getenv("TELEGRAM_SESSION", "data/hertzflow"),
        telegram_channel=os.getenv("TELEGRAM_CHANNEL", "hertzflowcrypto").lstrip("@"),
        binance_api_key=os.getenv("BINANCE_API_KEY", ""),
        binance_api_secret=os.getenv("BINANCE_API_SECRET", ""),
        binance_testnet=_b("BINANCE_TESTNET", True),
        dry_run=_b("DRY_RUN", True),
        live=_b("LIVE", False),
        position_usdt=float(os.getenv("POSITION_USDT", "50")),
        leverage=int(os.getenv("LEVERAGE", "1")),
        max_slippage_pct=float(os.getenv("MAX_SLIPPAGE_PCT", "1.5")),
        state_path=Path(os.getenv("STATE_PATH", "data/state.json")),
    )
