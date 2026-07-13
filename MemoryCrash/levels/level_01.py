"""Level 1 configuration."""

from enemy.boss import ForgottenCitizen
from enemy.enemy_types import MemoryBug, FearVirus
from levels.level_manager import BaseLevel
from maps.memory_city import MemoryCityMap


class Level01(BaseLevel):
    def __init__(self) -> None:
        super().__init__(
            name="LEVEL 1 - Memory City",
            chapter_text="Childhood stocks begin to emerge.",
            map_obj=MemoryCityMap(),
            enemy_factory=[MemoryBug, FearVirus, MemoryBug],
            boss_factory=ForgottenCitizen,
        )
