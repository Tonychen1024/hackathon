"""Core game state models."""

from dataclasses import dataclass, field
from enum import Enum, auto


class SceneType(Enum):
    MENU = auto()
    LEVEL = auto()
    MARKET = auto()
    BOSS = auto()
    GAME_OVER = auto()


@dataclass
class SaveData:
    player_assets: dict = field(default_factory=dict)
    stock_data: dict = field(default_factory=dict)
    unlocked_levels: int = 1
    high_score: int = 0


@dataclass
class RuntimeState:
    current_level_index: int = 0
    score: int = 0
    scene: SceneType = SceneType.MENU
    game_completed: bool = False
