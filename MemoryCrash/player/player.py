"""Playable player entity for prototype combat."""

from __future__ import annotations

from dataclasses import dataclass, field
import math
import pygame

from config import (
    PLAYER_BASE_DAMAGE,
    PLAYER_BASE_HP,
    PLAYER_BASE_SPEED,
    PLAYER_MONEY_HEALTH_MAX,
    PLAYER_START_MONEY,
)


@dataclass
class Bullet:
    x: float
    y: float
    vx: float
    vy: float
    radius: int = 4
    damage: float = PLAYER_BASE_DAMAGE
    alive: bool = True
    football: bool = False

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
    money: float = PLAYER_START_MONEY
    inventory: list[str] = field(default_factory=list)
    # Fragments are the player's tradable resources.  Keep the three keys
    # present so the HUD and market never need to special-case an empty type.
    fragments: dict[str, int] = field(
        default_factory=lambda: {"Hope": 0, "Dream": 0, "Fear": 0}
    )
    x: float = 640
    y: float = 360
    radius: int = 16
    fire_cooldown: float = 0.22
    last_shot_at: float = -999.0
    bullets: list[Bullet] = field(default_factory=list)
    shield: float = 0.0
    shield_max: float = 0.0
    trail: list[tuple[float, float]] = field(default_factory=list)
    trail_intensity: float = 0.0
    invulnerability_timer: float = 0.0

    def reset_position(self, x: float, y: float) -> None:
        self.x = x
        self.y = y
        self.bullets.clear()
        self.trail.clear()

    def reset_for_new_run(self) -> None:
        """Restore all player-owned gameplay state before a fresh level run."""
        self.hp = PLAYER_BASE_HP
        self.damage = PLAYER_BASE_DAMAGE
        self.speed = PLAYER_BASE_SPEED
        self.money = PLAYER_START_MONEY
        self.inventory.clear()
        self.fragments = {"Hope": 0, "Dream": 0, "Fear": 0}
        self.shield = 0.0
        self.shield_max = 0.0
        self.trail_intensity = 0.0
        self.invulnerability_timer = 0.0
        self.last_shot_at = -999.0
        self.bullets.clear()
        self.trail.clear()

    def reset_for_level_two(self) -> None:
        """Reset for Level 2 with its fixed Hope and Dream starting supply."""
        fragments = self.fragments.copy()
        self.reset_for_new_run()
        fragments["Hope"] = 3
        fragments["Dream"] = 3
        self.fragments = fragments

    @property
    def money_health_ratio(self) -> float:
        """Return the money-backed health bar ratio, capped at full health."""
        return max(0.0, min(1.0, self.money / PLAYER_MONEY_HEALTH_MAX))

    def apply_fragment_effects(self, dream: int, hope: int, dt: float) -> None:
        """Apply bounded Dream shield and Hope movement bonuses."""
        old_max = self.shield_max
        self.shield_max = min(120.0, max(0.0, dream * 15.0))
        if self.shield_max > old_max:
            self.shield = min(self.shield_max, self.shield + self.shield_max - old_max)
        self.shield = min(self.shield_max, self.shield + 10.0 * dt)
        self.speed = PLAYER_BASE_SPEED + min(180.0, max(0.0, hope * 18.0))
        self.trail_intensity = min(1.0, hope / 10.0)

    def handle_movement(self, keys, dt: float, width: int, height: int) -> None:
        dx = (1 if keys[pygame.K_d] else 0) - (1 if keys[pygame.K_a] else 0)
        dy = (1 if keys[pygame.K_s] else 0) - (1 if keys[pygame.K_w] else 0)

        if dx != 0 or dy != 0:
            length = math.hypot(dx, dy)
            self.x += (dx / length) * self.speed * dt
            self.y += (dy / length) * self.speed * dt
            if self.trail_intensity > 0:
                self.trail.append((self.x, self.y))
                self.trail = self.trail[-24:]
        elif self.trail:
            self.trail = self.trail[-8:]

        self.x = max(self.radius, min(width - self.radius, self.x))
        self.y = max(self.radius, min(height - self.radius, self.y))

    def try_shoot(self, target_x: float, target_y: float, now: float, cooldown_scale: float = 1.0, football: bool = False) -> bool:
        cooldown = max(0.06, self.fire_cooldown * cooldown_scale)
        if now - self.last_shot_at < cooldown:
            return False
        if football and not self.consume_football():
            return False

        direction_x = target_x - self.x
        direction_y = target_y - self.y
        length = math.hypot(direction_x, direction_y)
        if length <= 0:
            return False

        speed = 500
        self.bullets.append(
            Bullet(
                x=self.x,
                y=self.y,
                vx=(direction_x / length) * speed,
                vy=(direction_y / length) * speed,
                damage=self.damage, radius=10 if football else 4, football=football,
            )
        )
        self.last_shot_at = now
        return True

    def consume_football(self) -> bool:
        for name in ("Dream", "Hope"):
            if self.fragments[name] > 0:
                self.fragments[name] -= 1
                return True
        return False

    def take_damage(self, value: float) -> None:
        if self.is_invulnerable:
            return
        self.hp = max(0.0, self.hp - value)

    def grant_invulnerability(self, duration: float = 1.0) -> None:
        """Block all damage for a short period after returning to combat."""
        self.invulnerability_timer = max(self.invulnerability_timer, duration)

    def update_invulnerability(self, dt: float) -> None:
        self.invulnerability_timer = max(0.0, self.invulnerability_timer - dt)

    @property
    def is_invulnerable(self) -> bool:
        return self.invulnerability_timer > 0.0

    def update_bullets(self, dt: float, width: int, height: int) -> None:
        for bullet in self.bullets:
            bullet.update(dt, width, height)
        self.bullets = [bullet for bullet in self.bullets if bullet.alive]

    def lose_money(self, value: float) -> float:
        """Shield absorbs a variable money hit before the wallet is charged."""
        if self.is_invulnerable:
            return 0.0
        absorbed = min(self.shield, value)
        self.shield -= absorbed
        paid = min(self.money, value - absorbed)
        self.money -= paid
        return paid

    def heal(self, value: float) -> None:
        self.hp = min(PLAYER_BASE_HP, self.hp + value)

    def add_item(self, item_name: str) -> None:
        if item_name in self.fragments:
            self.fragments[item_name] += 1
            return
        self.inventory.append(item_name)

    def sell_fragment(self, fragment_name: str, amount: int = 1) -> int:
        owned = self.fragments.get(fragment_name, 0)
        sold = min(amount, owned)
        self.fragments[fragment_name] = owned - sold
        return sold

    @property
    def fragment_count(self) -> int:
        return sum(self.fragments.values())

    @property
    def memory_count(self) -> int:
        return len(self.inventory)
