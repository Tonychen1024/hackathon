"""Playable player entity for prototype combat."""

from __future__ import annotations

from dataclasses import dataclass, field
import math
import pygame

from config import PLAYER_BASE_DAMAGE, PLAYER_BASE_HP, PLAYER_BASE_SPEED


@dataclass
class Bullet:
    x: float
    y: float
    vx: float
    vy: float
    radius: int = 4
    damage: float = PLAYER_BASE_DAMAGE
    alive: bool = True

    def update(self, dt: float, width: int, height: int) -> None:
        self.x += self.vx * dt
        self.y += self.vy * dt
        if self.x < 0 or self.x > width or self.y < 0 or self.y > height:
            self.alive = False


@dataclass
class Player:
    hp: float = PLAYER_BASE_HP
    damage: float = PLAYER_BASE_DAMAGE
    speed: float = PLAYER_BASE_SPEED
    money: float = 100
    inventory: list[str] = field(default_factory=list)
    stocks: dict[str, int] = field(default_factory=dict)
    x: float = 640
    y: float = 360
    radius: int = 16
    fire_cooldown: float = 0.22
    last_shot_at: float = -999.0
    bullets: list[Bullet] = field(default_factory=list)

    def reset_position(self, x: float, y: float) -> None:
        self.x = x
        self.y = y
        self.bullets.clear()

    def handle_movement(self, keys, dt: float, width: int, height: int) -> None:
        dx = (1 if keys[pygame.K_d] else 0) - (1 if keys[pygame.K_a] else 0)
        dy = (1 if keys[pygame.K_s] else 0) - (1 if keys[pygame.K_w] else 0)

        if dx != 0 or dy != 0:
            length = math.hypot(dx, dy)
            self.x += (dx / length) * self.speed * dt
            self.y += (dy / length) * self.speed * dt

        self.x = max(self.radius, min(width - self.radius, self.x))
        self.y = max(self.radius, min(height - self.radius, self.y))

    def try_shoot(self, target_x: float, target_y: float, now: float, cooldown_scale: float = 1.0) -> None:
        cooldown = max(0.06, self.fire_cooldown * cooldown_scale)
        if now - self.last_shot_at < cooldown:
            return

        direction_x = target_x - self.x
        direction_y = target_y - self.y
        length = math.hypot(direction_x, direction_y)
        if length <= 0:
            return

        speed = 500
        self.bullets.append(
            Bullet(
                x=self.x,
                y=self.y,
                vx=(direction_x / length) * speed,
                vy=(direction_y / length) * speed,
                damage=self.damage,
            )
        )
        self.last_shot_at = now

    def update_bullets(self, dt: float, width: int, height: int) -> None:
        for bullet in self.bullets:
            bullet.update(dt, width, height)
        self.bullets = [bullet for bullet in self.bullets if bullet.alive]

    def take_damage(self, value: float) -> None:
        self.hp = max(0.0, self.hp - value)

    def heal(self, value: float) -> None:
        self.hp = min(PLAYER_BASE_HP, self.hp + value)

    def add_item(self, item_name: str) -> None:
        self.inventory.append(item_name)

    def buy_stock(self, stock_name: str, amount: int) -> None:
        self.stocks[stock_name] = self.stocks.get(stock_name, 0) + amount

    def sell_stock(self, stock_name: str, amount: int) -> int:
        owned = self.stocks.get(stock_name, 0)
        sold = min(amount, owned)
        self.stocks[stock_name] = owned - sold
        return sold

    @property
    def memory_count(self) -> int:
        return len(self.inventory)
