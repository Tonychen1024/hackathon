"""Save/load services for persistent progress."""

import json
from dataclasses import asdict
from pathlib import Path

from config import SAVE_FILE
from core.game_state import SaveData


class SaveSystem:
    def __init__(self, file_name: str = SAVE_FILE) -> None:
        self.path = Path(file_name)

    def save(self, data: SaveData) -> None:
        self.path.write_text(json.dumps(asdict(data), indent=2), encoding="utf-8")

    def load(self) -> SaveData:
        if not self.path.exists():
            return SaveData()
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        return SaveData(
            player_assets=raw.get("player_assets", {}),
            stock_data=raw.get("stock_data", {}),
            unlocked_levels=raw.get("unlocked_levels", 1),
            high_score=raw.get("high_score", 0),
        )
