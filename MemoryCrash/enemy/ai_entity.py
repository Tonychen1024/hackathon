"""Dream Factory AI entities, projectiles, and their rendering."""

from __future__ import annotations

from dataclasses import dataclass, field
import math

import pygame

from config import SCREEN_HEIGHT, SCREEN_WIDTH


@dataclass
class AIBullet:
    x: float
    y: float
    vx: float
    vy: float
    damage: float
    color: tuple[int, int, int]
    piercing: bool = False
    radius: int = 5
    alive: bool = True
    hit_targets: set[int] = field(default_factory=set)
    lifetime: float = 1.25

    def update(self, dt: float, target_x: float, target_y: float, homing: bool = True) -> None:
        self.lifetime -= dt
        if homing:
            dx, dy = target_x - self.x, target_y - self.y
            distance = math.hypot(dx, dy)
            if distance:
                speed = math.hypot(self.vx, self.vy)
                desired_x, desired_y = dx / distance * speed, dy / distance * speed
                turn = min(1.0, 5.5 * dt)
                self.vx += (desired_x - self.vx) * turn
                self.vy += (desired_y - self.vy) * turn
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.alive = (
            self.lifetime > 0
            and -30 <= self.x <= SCREEN_WIDTH + 30
            and -30 <= self.y <= SCREEN_HEIGHT + 30
        )


class DreamAssistant:
    """An invulnerable friendly drone which follows and supports the player."""

    radius = 13
    fire_interval = 1 / 3
    bullet_damage = 10

    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y
        self.last_shot_at = -999.0
        self.bullets: list[AIBullet] = []

    def follow(self, player, dt: float, fear_count: int = 0) -> None:
        dx, dy = self.x - player.x, self.y - player.y
        distance = math.hypot(dx, dy)
        if distance < 0.1:
            dx, dy, distance = -1.0, 0.0, 1.0
        desired_distance = 60.0
        target_x = player.x + dx / distance * desired_distance
        target_y = player.y + dy / distance * desired_distance
        smooth = min(1.0, 6.0 * dt)
        move_x = (target_x - self.x) * smooth
        move_y = (target_y - self.y) * smooth
        max_step = (360 + fear_count * 35) * dt
        move_length = math.hypot(move_x, move_y)
        if move_length > max_step > 0:
            move_x, move_y = move_x / move_length * max_step, move_y / move_length * max_step
        self.x += move_x
        self.y += move_y
        self.x = max(self.radius, min(SCREEN_WIDTH - self.radius, self.x))
        self.y = max(self.radius, min(SCREEN_HEIGHT - self.radius, self.y))

    def fire_at_nearest(self, enemies, now: float, fear_count: int = 0) -> None:
        alive = [enemy for enemy in enemies if enemy.alive]
        if not alive or now - self.last_shot_at < self.fire_interval:
            return
        target = min(alive, key=lambda enemy: math.hypot(enemy.x - self.x, enemy.y - self.y))
        dx, dy = target.x - self.x, target.y - self.y
        distance = max(1.0, math.hypot(dx, dy))
        speed = 760 + fear_count * 45
        damage = self.bullet_damage * (1 + fear_count * 0.12)
        self.bullets.append(AIBullet(self.x, self.y, dx / distance * speed, dy / distance * speed, damage, (255, 230, 70), piercing=True))
        self.last_shot_at = now

    def update_bullets(self, dt: float, enemies) -> None:
        alive = [enemy for enemy in enemies if enemy.alive]
        for bullet in self.bullets:
            if alive:
                target = min(alive, key=lambda enemy: math.hypot(enemy.x - bullet.x, enemy.y - bullet.y))
                bullet.update(dt, target.x, target.y)
            else:
                # A missed friendly shot vanishes immediately rather than
                # drifting across the map after its target has been defeated.
                bullet.alive = False
        self.bullets = [bullet for bullet in self.bullets if bullet.alive]

    def draw(self, surface, transforming: bool = False, elapsed: float = 0.0) -> None:
        hostile = transforming and elapsed >= 0.6
        core = (245, 55, 65) if hostile else (60, 220, 255)
        glow = (255, 45, 55) if hostile else (90, 220, 255)
        layer = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        pulse = 20 + int(8 * math.sin(elapsed * 18)) if transforming else 12
        pygame.draw.circle(layer, (*glow, 130 if hostile else 65), (int(self.x), int(self.y)), self.radius + pulse)
        surface.blit(layer, (0, 0))
        points = [(self.x + math.cos(math.tau * index / 6) * self.radius, self.y + math.sin(math.tau * index / 6) * self.radius) for index in range(6)]
        pygame.draw.polygon(surface, core, points)
        pygame.draw.polygon(surface, (220, 250, 255), points, 2)
        for index in range(4):
            angle = math.tau * index / 4 + math.pi / 4
            pygame.draw.circle(surface, glow, (int(self.x + math.cos(angle) * (self.radius + 8)), int(self.y + math.sin(angle) * (self.radius + 8))), 4)
        for bullet in self.bullets:
            pygame.draw.circle(surface, bullet.color, (int(bullet.x), int(bullet.y)), bullet.radius)


class RogueAIEnemy:
    """A hostile autonomous drone for Dream Factory waves 4 through 6."""

    radius = 16
    fire_interval = 1 / 3

    def __init__(self, x: float, y: float, hp: float, damage: float) -> None:
        self.x = x
        self.y = y
        self.base_hp = hp
        self.base_damage = damage
        self.base_speed = 165
        self.hp = hp
        self.damage = damage
        self.speed = self.base_speed
        self.fear_count = 0
        self.last_shot_at = -999.0
        self.bullets: list[AIBullet] = []

    @property
    def alive(self) -> bool:
        return self.hp > 0

    def take_damage(self, amount: float) -> None:
        self.hp = max(0.0, self.hp - amount)

    def apply_fear_strength(self, fear_count: int) -> None:
        previous_max_hp = self.base_hp * (1 + self.fear_count * 0.25)
        max_hp = self.base_hp * (1 + fear_count * 0.25)
        if previous_max_hp > 0:
            self.hp = min(max_hp, self.hp * max_hp / previous_max_hp)
        self.damage = self.base_damage * (1 + fear_count * 0.15)
        self.speed = self.base_speed * (1 + fear_count * 0.08)
        self.fear_count = fear_count

    def update(self, dt: float, player, now: float, fear_count: int = 0) -> None:
        self.apply_fear_strength(fear_count)
        dx, dy = player.x - self.x, player.y - self.y
        distance = max(1.0, math.hypot(dx, dy))
        if distance > 150:
            self.x += dx / distance * self.speed * dt
            self.y += dy / distance * self.speed * dt
        self.x = max(self.radius, min(SCREEN_WIDTH - self.radius, self.x))
        self.y = max(self.radius, min(SCREEN_HEIGHT - self.radius, self.y))
        if now - self.last_shot_at >= self.fire_interval:
            speed = 520 + fear_count * 30
            self.bullets.append(AIBullet(self.x, self.y, dx / distance * speed, dy / distance * speed, self.damage, (255, 55, 65)))
            self.last_shot_at = now

    def update_bullets(self, dt: float, player) -> None:
        for bullet in self.bullets:
            bullet.update(dt, player.x, player.y)
        self.bullets = [bullet for bullet in self.bullets if bullet.alive]

    def apply_bullet_hits(self, player) -> None:
        for bullet in self.bullets:
            if bullet.alive and math.hypot(bullet.x - player.x, bullet.y - player.y) <= bullet.radius + player.radius:
                player.lose_money(bullet.damage)
                bullet.alive = False

    def draw(self, surface) -> None:
        layer = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        pygame.draw.circle(layer, (255, 35, 55, 125), (int(self.x), int(self.y)), self.radius + 22)
        surface.blit(layer, (0, 0))
        points = [(self.x + math.cos(math.tau * index / 6) * self.radius, self.y + math.sin(math.tau * index / 6) * self.radius) for index in range(6)]
        pygame.draw.polygon(surface, (245, 55, 65), points)
        pygame.draw.polygon(surface, (255, 205, 210), points, 2)
        for bullet in self.bullets:
            pygame.draw.circle(surface, (35, 0, 8), (int(bullet.x), int(bullet.y)), bullet.radius + 2)
            pygame.draw.circle(surface, bullet.color, (int(bullet.x), int(bullet.y)), bullet.radius, 2)
