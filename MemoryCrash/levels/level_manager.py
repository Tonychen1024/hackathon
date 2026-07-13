"""Level system for combat progression."""

from __future__ import annotations

from dataclasses import dataclass, field
import random
import math
import pygame

from enemy.enemy import Enemy


FRAGMENT_TYPES = ["Hope", "Dream", "Fear"]


@dataclass
class MemoryFragment:
    x: float
    y: float
    kind: str
    size: int = 10


@dataclass
class Level:
    index: int
    name: str
    enemy_target: int
    is_boss: bool = False
    enemies: list[Enemy] = field(default_factory=list)
    fragments: list[MemoryFragment] = field(default_factory=list)
    kills: int = 0
    cleared: bool = False
    news_triggered: bool = False
    collected_fragments: int = 0
    elapsed: float = 0.0
    enemy_hp_multiplier: float = 1.0
    enemy_damage_bonus: float = 0.0
    enemy_speed_bonus: float = 0.0

    def enter(self) -> None:
        self.enemies = []
        self.fragments = []
        self.kills = 0
        self.cleared = False
        self.news_triggered = False
        self.collected_fragments = 0
        self.elapsed = 0.0
        self.spawn_enemy()

    def exit(self) -> None:
        self.enemies = []
        self.fragments = []

    def spawn_enemy(self) -> None:
        if self.is_boss:
            self.enemies.append(
                Enemy(
                    name="Exchange Core Boss",
                    hp=420,
                    damage=12,
                    speed=120,
                    reward_item="Core",
                    x=640,
                    y=180,
                    radius=30,
                    attack_cooldown=0.6,
                )
            )
            return

        for _ in range(self.enemy_target):
            self.enemies.append(
                Enemy(
                    name="Memory Error",
                    hp=(20 + self.index * 4) * self.enemy_hp_multiplier,
                    damage=6 + self.index + self.enemy_damage_bonus,
                    speed=95 + self.index * 12 + self.enemy_speed_bonus,
                    reward_item=random.choice(FRAGMENT_TYPES),
                    x=random.randint(40, 1240),
                    y=random.randint(40, 680),
                    radius=14,
                )
            )

    def update(self, dt: float, player, now: float, enemy_speed_multiplier: float, enemy_damage_multiplier: float, enemy_health_multiplier: float, enemy_size_multiplier: float) -> None:
        self.elapsed += dt
        for enemy in self.enemies:
            enemy.set_fear_strength(enemy_size_multiplier, enemy_health_multiplier)
            enemy.move(dt, player.x, player.y, enemy_speed_multiplier)
            if math.hypot(enemy.x - player.x, enemy.y - player.y) <= enemy.radius + player.radius:
                enemy.attack(player, now, enemy_damage_multiplier)

        for bullet in player.bullets:
            if not bullet.alive:
                continue
            for enemy in self.enemies:
                if not enemy.alive:
                    continue
                if math.hypot(bullet.x - enemy.x, bullet.y - enemy.y) <= bullet.radius + enemy.radius:
                    enemy.take_damage(bullet.damage)
                    bullet.alive = False
                    if not enemy.alive:
                        self.kills += 1
                        if not self.is_boss:
                            self.fragments.append(
                                MemoryFragment(x=enemy.x, y=enemy.y, kind=enemy.drop_memory())
                            )
                    break

        self.enemies = [enemy for enemy in self.enemies if enemy.alive]
        self.check_complete()

    def collect_fragments(self, player) -> None:
        remain: list[MemoryFragment] = []
        for fragment in self.fragments:
            if math.hypot(fragment.x - player.x, fragment.y - player.y) <= fragment.size + player.radius:
                player.add_item(fragment.kind)
                self.collected_fragments += 1
            else:
                remain.append(fragment)
        self.fragments = remain

    def scatter_fear_fragments(self, player, amount: int = 36) -> None:
        """Flood the nearby map with Fear after the breaking-news event."""
        for _ in range(amount):
            angle = random.uniform(0, math.tau)
            distance = random.uniform(30, 250)
            x = max(16, min(1264, player.x + math.cos(angle) * distance))
            y = max(16, min(704, player.y + math.sin(angle) * distance))
            self.fragments.append(MemoryFragment(x=x, y=y, kind="Fear", size=12))

    def check_complete(self) -> bool:
        if self.is_boss:
            self.cleared = len(self.enemies) == 0
        else:
            self.cleared = self.kills >= self.enemy_target and len(self.enemies) == 0
        return self.cleared

    def draw(self, surface, fonts, fear_price: float = 1000.0) -> None:
        color_bank = {
            1: (20, 28, 48),
            2: (28, 45, 35),
            3: (42, 34, 60),
            4: (50, 28, 30),
            5: (18, 18, 18),
        }
        surface.fill(color_bank.get(self.index, (20, 20, 24)))

        for line_y in range(80, 720, 80):
            pygame_color = (50, 60, 90) if self.index < 4 else (80, 40, 40)
            pygame.draw.line(surface, pygame_color, (0, line_y), (1280, line_y), 1)

        glow_layer = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        for enemy in self.enemies:
            if enemy.radius > enemy.base_radius:
                glow_radius = int(enemy.radius * 1.65)
                pygame.draw.circle(glow_layer, (255, 20, 55, 85), (int(enemy.x), int(enemy.y)), glow_radius)
                pygame.draw.circle(glow_layer, (255, 90, 35, 120), (int(enemy.x), int(enemy.y)), int(enemy.radius * 1.28))
        surface.blit(glow_layer, (0, 0))

        for enemy in self.enemies:
            pygame.draw.circle(surface, (230, 60, 60), (int(enemy.x), int(enemy.y)), enemy.radius)

        fragment_colors = {
            "Hope": (120, 255, 170),
            "Dream": (130, 160, 255),
            "Fear": (220, 120, 255),
        }
        for fragment in self.fragments:
            color = fragment_colors.get(fragment.kind, (255, 255, 255))
            rect = pygame.Rect(
                int(fragment.x - fragment.size // 2),
                int(fragment.y - fragment.size // 2),
                fragment.size,
                fragment.size,
            )
            pygame.draw.rect(surface, color, rect)

        # A Fear price above the opening value stains the edge of the map red.
        # The effect strengthens gradually, up to the 10x news-shock value.
        fear_intensity = max(0.0, min(1.0, (fear_price - 1000.0) / 9000.0))
        if fear_intensity > 0:
            overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            alpha = int(55 + 145 * fear_intensity)
            width = int(18 + 52 * fear_intensity)
            pygame.draw.rect(overlay, (210, 0, 20, alpha), overlay.get_rect(), width)
            pygame.draw.rect(overlay, (100, 0, 10, alpha // 2), overlay.get_rect().inflate(-width, -width), 8)
            surface.blit(overlay, (0, 0))

        label = fonts["body"].render(self.name, True, (240, 240, 255))
        surface.blit(label, (20, 18))


class LevelManager:
    def __init__(self) -> None:
        self.levels = [
            Level(
                1,
                "LEVEL 1 - Memory City",
                36,
                enemy_hp_multiplier=1.6,
                enemy_damage_bonus=6,
                enemy_speed_bonus=36,
            ),
            Level(2, "LEVEL 2 - Childhood World", 30),
            Level(3, "LEVEL 3 - Dream Factory", 40),
            Level(4, "LEVEL 4 - Regret Land", 50),
            Level(5, "LEVEL 5 - Exchange Core", 1, is_boss=True),
        ]
        self.current_index = 0

    @property
    def current_level(self) -> Level:
        return self.levels[self.current_index]

    def set_level(self, index: int) -> None:
        self.current_index = max(0, min(index, len(self.levels) - 1))

    def move_next(self) -> bool:
        if self.current_index + 1 < len(self.levels):
            self.current_index += 1
            return True
        return False
