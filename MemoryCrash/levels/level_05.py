"""Level 5 configuration."""

from enemy.boss import ExchangeAI
from enemy.enemy_types import MarketVirus
from levels.level_manager import BaseLevel
from maps.exchange_core import ExchangeCoreMap


class Level05(BaseLevel):
    def __init__(self) -> None:
        super().__init__(
            name="LEVEL 5 - Exchange Core",
            chapter_text="Final market-combat coupling against Exchange AI.",
            map_obj=ExchangeCoreMap(),
            enemy_factory=[MarketVirus, MarketVirus, MarketVirus],
            boss_factory=ExchangeAI,
            timer_to_complete=14,
        )
