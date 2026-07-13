"""Enemy model with basic chase and contact attack behavior."""

from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass
class Enemy:
    name: str
    hp: float
    damage: float
    speed: float
    reward_item: str
    x: float = 0.0
    y: float = 0.0
    radius: int = 14
    attack_cooldown: float = 0.8
    _last_attack_at: float = -999.0

    def move(self, dt: float, target_x: float, target_y: float, speed_scale: float = 1.0) -> None:
        dx = target_x - self.x
        dy = target_y - self.y
        length = math.hypot(dx, dy)
        if length <= 0:
            return
        step = self.speed * speed_scale * dt
        self.x += (dx / length) * step
        self.y += (dy / length) * step

    def attack(self, target, now: float = 0.0) -> None:
        if now - self._last_attack_at < self.attack_cooldown:
            return
        target.take_damage(self.damage)
        self._last_attack_at = now

    def take_damage(self, amount: float) -> None:
        self.hp = max(0.0, self.hp - amount)

    def drop_memory(self) -> str:
        return self.reward_item

    @property
    def alive(self) -> bool:
        return self.hp > 0
