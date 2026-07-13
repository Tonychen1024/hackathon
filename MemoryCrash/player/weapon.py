"""Weapon models."""

from dataclasses import dataclass


@dataclass
class Weapon:
    name: str
    damage: float
    fire_rate: float
    range_value: float

    def upgrade(self, ratio: float) -> None:
        self.damage *= ratio
