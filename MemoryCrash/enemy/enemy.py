"""Enemy model with basic chase and contact attack behavior."""

from __future__ import annotations

from dataclasses import dataclass
import math
import random


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
    base_radius: int = 0
    base_hp: float = 0.0
    fear_health_scale: float = 1.0

    def __post_init__(self) -> None:
        self.base_radius = self.radius
        self.base_hp = self.hp

    def move(self, dt: float, target_x: float, target_y: float, speed_scale: float = 1.0) -> None:
        dx = target_x - self.x
        dy = target_y - self.y
        length = math.hypot(dx, dy)
        if length <= 0:
            return
        step = self.speed * speed_scale * dt
        self.x += (dx / length) * step
        self.y += (dy / length) * step

    def attack(self, target, now: float = 0.0, damage_scale: float = 1.0) -> None:
        if now - self._last_attack_at < self.attack_cooldown:
            return
        # Each hit removes a fluctuating amount of money instead of HP.
        loss = self.damage * random.uniform(3.0, 6.0) * damage_scale
        target.lose_money(loss)
        self._last_attack_at = now

    def set_fear_strength(self, size_scale: float, health_scale: float) -> None:
        self.radius = max(1, int(self.base_radius * size_scale))
        previous_max_hp = self.base_hp * self.fear_health_scale
        new_max_hp = self.base_hp * health_scale
        if previous_max_hp > 0:
            self.hp = min(new_max_hp, self.hp * new_max_hp / previous_max_hp)
        self.fear_health_scale = health_scale

    def take_damage(self, amount: float) -> None:
        self.hp = max(0.0, self.hp - amount)

    def drop_memory(self) -> str:
        return self.reward_item

    @property
    def alive(self) -> bool:
        return self.hp > 0
