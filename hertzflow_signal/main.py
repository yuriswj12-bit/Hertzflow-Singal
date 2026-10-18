from __future__ import annotations

import asyncio
import logging

from hertzflow_signal.config import load_settings
from hertzflow_signal.telegram_listener import run_listener


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    settings = load_settings()
    asyncio.run(run_listener(settings))


if __name__ == "__main__":
    main()
