"""Level 2 configuration."""

from enemy.boss import BrokenChildhood
from enemy.enemy_types import LostToy, ChildhoodVirus
from levels.level_manager import BaseLevel
from maps.childhood_world import ChildhoodWorldMap


class Level02(BaseLevel):
    def __init__(self) -> None:
        super().__init__(
            name="LEVEL 2 - Childhood World",
            chapter_text="Map mood shifts by Childhood stock.",
            map_obj=ChildhoodWorldMap(),
            enemy_factory=[LostToy, ChildhoodVirus, LostToy],
            boss_factory=BrokenChildhood,
        )
