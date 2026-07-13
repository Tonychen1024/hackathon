"""Level 4 configuration."""

from enemy.boss import PastSelf
from enemy.enemy_types import FearVirus, AIWorker
from levels.level_manager import BaseLevel
from maps.regret_land import RegretLandMap


class Level04(BaseLevel):
    def __init__(self) -> None:
        super().__init__(
            name="LEVEL 4 - Regret Land",
            chapter_text="Negative memory system and crash events appear.",
            map_obj=RegretLandMap(),
            enemy_factory=[FearVirus, AIWorker, FearVirus],
            boss_factory=PastSelf,
        )
