"""Level 3 configuration."""

from enemy.boss import DreamEater
from enemy.enemy_types import DreamCollector, AIWorker
from levels.level_manager import BaseLevel
from maps.dream_factory import DreamFactoryMap


class Level03(BaseLevel):
    def __init__(self) -> None:
        super().__init__(
            name="LEVEL 3 - Dream Factory",
            chapter_text="Dream stock drives attack speed and cooldown pressure.",
            map_obj=DreamFactoryMap(),
            enemy_factory=[DreamCollector, AIWorker, DreamCollector],
            boss_factory=DreamEater,
        )
