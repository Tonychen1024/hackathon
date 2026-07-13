"""Enemy base class interfaces."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Enemy:
    name: str
    hp: float
    damage: float
    speed: float
    reward_item: str

    def move(self, dt: float) -> None:
        raise NotImplementedError

    def attack(self, target) -> None:
        raise NotImplementedError

    def take_damage(self, amount: float) -> None:
        self.hp = max(0, self.hp - amount)

    def drop_memory(self) -> str:
        return self.reward_item

    @property
    def alive(self) -> bool:
        return self.hp > 0
