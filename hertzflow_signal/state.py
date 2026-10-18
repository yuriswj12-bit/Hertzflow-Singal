from __future__ import annotations

import json
from pathlib import Path
from typing import Set


class State:
    def __init__(self, path: Path):
        self.path = path
        self.processed: Set[int] = set()
        self.open_symbols: Set[str] = set()
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        data = json.loads(self.path.read_text())
        self.processed = set(data.get("processed", []))
        self.open_symbols = set(data.get("open_symbols", []))

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(
                {
                    "processed": sorted(self.processed),
                    "open_symbols": sorted(self.open_symbols),
                },
                indent=2,
            )
        )

    def seen(self, message_id: int) -> bool:
        return message_id in self.processed

    def mark(self, message_id: int) -> None:
        self.processed.add(message_id)
        self.save()
