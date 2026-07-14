"""Level system for combat progression."""

from __future__ import annotations

from dataclasses import dataclass, field
import random
import math
import pygame

from config import SCREEN_HEIGHT, SCREEN_WIDTH
from enemy.enemy import Enemy


FRAGMENT_TYPES = ["Hope", "Dream", "Fear"]


@dataclass
class MemoryFragment:
    x: float
    y: float
    kind: str
    size: int = 10
    is_covid: bool = False

@dataclass
class EnemyBullet:
    x: float; y: float; vx: float; vy: float; alive: bool = True
    def update(self, dt: float) -> None:
        self.x += self.vx * dt; self.y += self.vy * dt
        self.alive = 0 <= self.x <= 1280 and 0 <= self.y <= 720


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
    world_cup: bool = False
    wave_index: int = 0
    enemy_bullets: list[EnemyBullet] = field(default_factory=list)
    pending_reward: bool = False
    pending_event: tuple[int, int, int] | None = None
    reward_message: str = ""
    fragment_drop_timer: float = 0.0

    def enter(self) -> None:
        self.enemies = []
        self.fragments = []
        self.kills = 0
        self.cleared = False
        self.news_triggered = False
        self.collected_fragments = 0
        self.elapsed = 0.0
        self.fragment_drop_timer = 0.0
        self.enemy_bullets = []; self.pending_reward = False; self.pending_event = None; self.reward_message = ""
        if self.world_cup: self.start_wave(0)
        else: self.spawn_enemy()

    def start_wave(self, index: int) -> None:
        self.wave_index = index
        specs = [(5, 1.0, 1.0), (6, .8, 1.3), (8, .6, 1.7), (1, .5, 2.2)]
        count, size, speed = specs[index]
        self.enemies = [Enemy("World Cup Boss" if index == 3 else "Cup Runner", 1, 10, 130 * speed, "", random.randint(80,1200), random.randint(90,650), max(7,int(18*size))) for _ in range(count)]

    def resolve_reward(self, player, choice: int | None = None, accept: bool = True) -> None:
        if self.pending_event and accept:
            chance, hope, fear = self.pending_event
            if random.randint(1,100) <= chance: player.fragments["Hope"] += hope; self.reward_message=f"Hope +{hope}"
            else: player.fragments["Fear"] += fear; self.reward_message=f"Fear +{fear}"
        elif self.pending_event: self.reward_message="Event declined"
        elif choice == 0: player.fragments["Hope"] += 3; self.reward_message="Hope +3"
        elif choice == 1: player.fragments["Dream"] += 3; self.reward_message="Dream +3"
        elif choice == 2: player.fragments["Fear"] = max(0, player.fragments["Fear"] - 3); self.reward_message="Fear -3"
        self.pending_reward = False; self.pending_event = None
        if not self.enemies:
            if self.wave_index == 3: self.cleared = True
            else: self.start_wave(self.wave_index + 1)

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

    def update(self, dt: float, player, now: float, enemy_speed_multiplier: float, enemy_money_damage: float, enemy_health_multiplier: float, enemy_size_multiplier: float) -> None:
        self.elapsed += dt
        if self.world_cup:
            self.fragment_drop_timer += dt
            while self.fragment_drop_timer >= 5.0:
                self.fragment_drop_timer -= 5.0
                self.drop_world_cup_fragment()
            self.update_world_cup(
                dt, player, now, enemy_speed_multiplier, enemy_money_damage
            )
            return
        for enemy in self.enemies:
            enemy.set_fear_strength(enemy_size_multiplier, enemy_health_multiplier)
            enemy.move(dt, player.x, player.y, enemy_speed_multiplier)
            self.keep_enemy_in_bounds(enemy)
            if math.hypot(enemy.x - player.x, enemy.y - player.y) <= enemy.radius + player.radius:
                enemy.attack(player, now, enemy_money_damage)

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

    def drop_world_cup_fragment(self) -> None:
        """Drop a collectible Hope or Dream fragment somewhere in level 2."""
        size = 10
        self.fragments.append(
            MemoryFragment(
                x=random.randint(size, 1280 - size),
                y=random.randint(size, 720 - size),
                kind=random.choice(("Hope", "Dream")),
                size=size,
            )
        )

    @staticmethod
    def keep_enemy_in_bounds(enemy: Enemy) -> None:
        """Keep the enemy's complete sprite inside the playable arena."""
        radius = min(enemy.radius, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        enemy.radius = radius
        enemy.x = max(radius, min(SCREEN_WIDTH - radius, enemy.x))
        enemy.y = max(radius, min(SCREEN_HEIGHT - radius, enemy.y))

    def update_world_cup(self, dt, player, now, fear_scale, money_damage) -> None:
        for enemy in self.enemies:
            dx, dy = player.x-enemy.x, player.y-enemy.y; dist=max(1,math.hypot(dx,dy))
            side = math.sin(now*3 + enemy.x*.01)
            direction = -1 if dist < 260 else (1 if dist > 420 else 0)
            enemy.x += (dx/dist*direction + (-dy/dist)*side) * enemy.speed*fear_scale*dt
            enemy.y += (dy/dist*direction + (dx/dist)*side) * enemy.speed*fear_scale*dt
            self.keep_enemy_in_bounds(enemy)
            if now-enemy._last_attack_at > 1.35/fear_scale:
                self.enemy_bullets.append(EnemyBullet(enemy.x,enemy.y,dx/dist*300*fear_scale,dy/dist*300*fear_scale)); enemy._last_attack_at=now
        for bullet in player.bullets:
            for enemy in self.enemies:
                if bullet.alive and math.hypot(bullet.x-enemy.x,bullet.y-enemy.y) <= bullet.radius+enemy.radius:
                    enemy.hp=0; bullet.alive=False; self.kills+=1; self.pending_reward=True
                    if random.random()<.5: self.pending_event=random.choice([(30,15,5),(50,10,10),(70,5,5)])
                    break
        self.enemies=[e for e in self.enemies if e.alive]
        for b in self.enemy_bullets:
            b.update(dt)
            if b.alive and math.hypot(b.x-player.x,b.y-player.y)<player.radius+6:
                player.lose_money(money_damage)
                b.alive = False
        self.enemy_bullets=[b for b in self.enemy_bullets if b.alive]

    def collect_fragments(self, player) -> None:
        remain: list[MemoryFragment] = []
        for fragment in self.fragments:
            if math.hypot(fragment.x - player.x, fragment.y - player.y) <= fragment.size + player.radius:
                player.add_item(fragment.kind)
                self.collected_fragments += 1
            else:
                remain.append(fragment)
        self.fragments = remain

    def scatter_fear_fragments(self, player, amount: int = 14) -> None:
        """Scatter a smaller set of enlarged COVID-shaped Fear fragments."""
        for _ in range(amount):
            angle = random.uniform(0, math.tau)
            distance = random.uniform(30, 250)
            x = max(16, min(1264, player.x + math.cos(angle) * distance))
            y = max(16, min(704, player.y + math.sin(angle) * distance))
            self.fragments.append(MemoryFragment(x=x, y=y, kind="Fear", size=20, is_covid=True))

    def check_complete(self) -> bool:
        if self.is_boss:
            self.cleared = len(self.enemies) == 0
        else:
            self.cleared = self.kills >= self.enemy_target and len(self.enemies) == 0
        return self.cleared

    @staticmethod
    def draw_football_field(surface) -> None:
        """Render Level 2 as a full football pitch."""
        width, height = surface.get_size()
        surface.fill((37, 118, 62))
        stripe_width = max(1, width // 12)
        for index, x in enumerate(range(0, width, stripe_width)):
            if index % 2 == 0:
                pygame.draw.rect(surface, (42, 132, 69), (x, 0, stripe_width, height))

        field = pygame.Rect(42, 72, width - 84, height - 112)
        line_color = (240, 245, 230)
        line_width = 3
        pygame.draw.rect(surface, line_color, field, line_width)

        center_x, center_y = field.center
        pygame.draw.line(surface, line_color, (center_x, field.top), (center_x, field.bottom), line_width)
        pygame.draw.circle(surface, line_color, (center_x, center_y), 82, line_width)
        pygame.draw.circle(surface, line_color, (center_x, center_y), 4)

        box_height = 300
        box_top = center_y - box_height // 2
        left_box = pygame.Rect(field.left, box_top, 145, box_height)
        right_box = pygame.Rect(field.right - 145, box_top, 145, box_height)
        pygame.draw.rect(surface, line_color, left_box, line_width)
        pygame.draw.rect(surface, line_color, right_box, line_width)

        small_box_height = 150
        small_box_top = center_y - small_box_height // 2
        pygame.draw.rect(surface, line_color, (field.left, small_box_top, 58, small_box_height), line_width)
        pygame.draw.rect(surface, line_color, (field.right - 58, small_box_top, 58, small_box_height), line_width)
        pygame.draw.circle(surface, line_color, (field.left + 100, center_y), 4)
        pygame.draw.circle(surface, line_color, (field.right - 100, center_y), 4)

        goal_height = 92
        goal_top = center_y - goal_height // 2
        pygame.draw.rect(surface, line_color, (field.left - 18, goal_top, 18, goal_height), 2)
        pygame.draw.rect(surface, line_color, (field.right, goal_top, 18, goal_height), 2)

    def draw(self, surface, fonts, fear_price: float = 1000.0) -> None:
        color_bank = {
            1: (20, 28, 48),
            2: (28, 45, 35),
            3: (42, 34, 60),
            4: (50, 28, 30),
            5: (18, 18, 18),
        }
        if self.world_cup:
            self.draw_football_field(surface)
        else:
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
        for bullet in self.enemy_bullets:
            pygame.draw.circle(surface, (255, 110, 70), (int(bullet.x), int(bullet.y)), 6)

        fragment_colors = {
            "Hope": (120, 255, 170),
            "Dream": (130, 160, 255),
            "Fear": (220, 120, 255),
        }
        for fragment in self.fragments:
            color = fragment_colors.get(fragment.kind, (255, 255, 255))
            if fragment.is_covid:
                center = (int(fragment.x), int(fragment.y))
                radius = fragment.size
                pygame.draw.circle(surface, (185, 45, 70), center, radius)
                pygame.draw.circle(surface, (255, 125, 120), center, radius, 2)
                for spike in range(12):
                    angle = math.tau * spike / 12
                    inner = (
                        int(fragment.x + math.cos(angle) * radius),
                        int(fragment.y + math.sin(angle) * radius),
                    )
                    outer = (
                        int(fragment.x + math.cos(angle) * (radius + 7)),
                        int(fragment.y + math.sin(angle) * (radius + 7)),
                    )
                    pygame.draw.line(surface, (255, 105, 100), inner, outer, 3)
                    pygame.draw.circle(surface, (255, 145, 135), outer, 4)
                pygame.draw.circle(surface, (115, 20, 45), center, max(3, radius // 3))
                continue
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
            Level(2, "LEVEL 2 - World Cup Fever", 0, world_cup=True),
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
