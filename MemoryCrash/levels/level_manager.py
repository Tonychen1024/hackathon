"""Combat levels and the three-level Memory Crash progression."""

from __future__ import annotations

from dataclasses import dataclass, field
import math
import random

import pygame

from config import SCREEN_HEIGHT, SCREEN_WIDTH
from enemy.ai_entity import DreamAssistant, RogueAIEnemy
from enemy.enemy import Enemy


FRAGMENT_TYPES = ("Hope", "Dream", "Fear")
ENTITY_COLLISION_PADDING = 0.5


@dataclass
class MemoryFragment:
    x: float
    y: float
    kind: str
    size: int = 10
    is_covid: bool = False


@dataclass
class EnemyBullet:
    x: float
    y: float
    vx: float
    vy: float
    alive: bool = True

    def update(self, dt: float) -> None:
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.alive = 0 <= self.x <= SCREEN_WIDTH and 0 <= self.y <= SCREEN_HEIGHT


@dataclass
class CombatEffect:
    x: float
    y: float
    kind: str
    lifetime: float = 0.28
    max_lifetime: float = 0.28


@dataclass
class Level:
    index: int
    name: str
    enemy_target: int
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
    fear_drop_timer: float = 0.0
    assistant: DreamAssistant | None = None
    rogue_ais: list[RogueAIEnemy] = field(default_factory=list)
    level3_phase: str = ""
    rebellion_elapsed: float = 0.0
    apology_elapsed: float = 0.0
    news_request: str | None = None
    announcement: str = ""
    announcement_timer: float = 0.0
    combat_effects: list[CombatEffect] = field(default_factory=list)
    rogue_wave_delay: float = 0.0

    @property
    def is_dream_factory(self) -> bool:
        return self.index == 3

    @property
    def ai_combat_active(self) -> bool:
        return self.is_dream_factory and self.level3_phase == "rogue"

    @property
    def needs_news(self) -> bool:
        return self.news_request is not None

    def enter(self) -> None:
        self.enemies.clear()
        self.fragments.clear()
        self.enemy_bullets.clear()
        self.rogue_ais.clear()
        self.kills = 0
        self.cleared = False
        self.news_triggered = False
        self.collected_fragments = 0
        self.elapsed = 0.0
        self.fragment_drop_timer = 0.0
        self.fear_drop_timer = 0.0
        self.pending_reward = False
        self.pending_event = None
        self.reward_message = ""
        self.assistant = None
        self.rebellion_elapsed = 0.0
        self.apology_elapsed = 0.0
        self.news_request = None
        self.announcement = ""
        self.announcement_timer = 0.0
        self.combat_effects.clear()
        self.rogue_wave_delay = 0.0

        if self.is_dream_factory:
            self.wave_index = 0
            self.level3_phase = "intro"
            self.news_request = "ai_adoption"
        elif self.world_cup:
            self.start_wave(0)
        else:
            self.spawn_enemy()

    def dismiss_news(self, news_kind: str) -> None:
        if news_kind == "ai_adoption" and self.level3_phase == "intro":
            self.news_request = None
            self.level3_phase = "friendly"
            self.assistant = DreamAssistant(SCREEN_WIDTH / 2 - 65, SCREEN_HEIGHT / 2)
            self.announcement = "You no longer need to attack the enemy; the AI robot will eliminate them for you."
            self.announcement_timer = 4.0
            self.start_level3_wave(1)
        elif news_kind == "ai_revolt" and self.level3_phase == "revolt_news":
            self.news_request = None
            self.level3_phase = "rebellion_animation"
            self.rebellion_elapsed = 0.0

    def start_wave(self, index: int) -> None:
        """Start one of Level 2's football waves."""
        self.wave_index = index
        specs = ((5, 1.0, 1.0), (6, 0.8, 1.3), (8, 0.6, 1.7), (1, 0.5, 2.2))
        count, size, speed = specs[index]
        self.enemies = [
            Enemy(
                "World Cup Boss" if index == 3 else "Cup Runner",
                1,
                10,
                130 * speed,
                "",
                random.randint(80, 1200),
                random.randint(90, 650),
                max(7, int(18 * size)),
            )
            for _ in range(count)
        ]

    def start_level3_wave(self, wave: int) -> None:
        """Start a friendly-AI Dream Factory wave (1 through 3)."""
        self.wave_index = wave
        self.cleared = False
        self.enemies.clear()
        counts = {1: 15, 2: 10, 3: 10}
        self.enemies = [self.make_rolling_enemy(wave) for _ in range(counts[wave])]

    def start_rogue_wave(self, wave: int) -> None:
        """Start Wave 4, 5, or 6: only hostile AI units are spawned."""
        self.wave_index = wave
        self.rogue_wave_delay = 0.0
        self.cleared = False
        self.enemies.clear()
        self.rogue_ais.clear()
        counts = {4: 1, 5: 3, 6: 5}
        hp = {4: 48, 5: 48, 6: 30}[wave]
        damage = {4: 9, 5: 13, 6: 17}[wave]
        if wave == 4 and self.assistant is not None:
            positions = [(self.assistant.x, self.assistant.y)]
            self.assistant = None
        else:
            positions = [
                (random.randint(100, 1180), random.randint(110, 610))
                for _ in range(counts[wave])
            ]
        self.rogue_ais = [
            RogueAIEnemy(
                x,
                y,
                hp=hp,
                damage=damage,
                formation_offset=(index - (counts[wave] - 1) / 2) * 82 if wave >= 5 else 0,
                use_formation=wave >= 5,
            )
            for index, (x, y) in enumerate(positions)
        ]
        self.level3_phase = "rogue"

    def skip_to_level3_transformation(self) -> bool:
        """End the friendly waves and play the AI transformation before Wave 4."""
        if self.level3_phase != "friendly" or self.wave_index not in (1, 2, 3):
            return False
        self.enemies.clear()
        self.level3_phase = "rebellion_animation"
        self.rebellion_elapsed = 0.0
        self.announcement = "The AI is transforming..."
        self.announcement_timer = 3.0
        return True

    def make_rolling_enemy(self, wave: int) -> Enemy:
        # Each friendly-AI wave is visibly larger and hits harder than the last.
        hp, damage, speed, radius = {
            1: (100, 12, 355, 15),
            2: (135, 18, 405, 20),
            3: (180, 26, 455, 25),
        }[wave]
        enemy = Enemy(
            "Rolling Memory Error",
            hp=hp,
            damage=damage,
            speed=speed,
            reward_item=random.choice(FRAGMENT_TYPES),
            x=random.randint(70, 1210),
            y=random.randint(90, 650),
            radius=radius,
            attack_cooldown=0.7,
        )
        angle = random.random() * math.tau
        enemy.roll_vx = math.cos(angle) * enemy.speed
        enemy.roll_vy = math.sin(angle) * enemy.speed
        return enemy

    def spawn_enemy(self) -> None:
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

    def update(
        self,
        dt: float,
        player,
        now: float,
        enemy_speed_multiplier: float,
        enemy_money_damage: float,
        enemy_health_multiplier: float,
        enemy_size_multiplier: float,
        audio=None,
    ) -> None:
        self.elapsed += dt
        self.update_combat_effects(dt)
        if self.is_dream_factory:
            self.update_dream_factory(
                dt,
                player,
                now,
                enemy_speed_multiplier,
                enemy_money_damage,
                enemy_health_multiplier,
                enemy_size_multiplier,
                audio,
            )
        elif self.world_cup:
            self.fragment_drop_timer += dt
            while self.fragment_drop_timer >= 5.0:
                self.fragment_drop_timer -= 5.0
                self.drop_world_cup_fragment()
            self.update_world_cup(dt, player, now, enemy_speed_multiplier, enemy_money_damage, audio)
        else:
            self.update_normal(
                dt,
                player,
                now,
                enemy_speed_multiplier,
                enemy_money_damage,
                enemy_health_multiplier,
                enemy_size_multiplier,
                audio,
            )

    def update_normal(self, dt, player, now, speed_scale, money_damage, health_scale, size_scale, audio=None) -> None:
        for enemy in self.enemies:
            enemy.set_fear_strength(size_scale, health_scale)
            enemy.move(dt, player.x, player.y, speed_scale)
            self.keep_enemy_in_bounds(enemy)

        self.resolve_entity_collisions(self.enemies)
        for enemy in self.enemies:
            if math.hypot(enemy.x - player.x, enemy.y - player.y) <= enemy.radius + player.radius:
                if enemy.attack(player, now, money_damage) and audio:
                    audio.play("hit_heavy")

        self.resolve_player_bullets(player, audio)
        self.enemies = [enemy for enemy in self.enemies if enemy.alive]
        self.cleared = self.kills >= self.enemy_target and not self.enemies

    def update_dream_factory(self, dt, player, now, speed_scale, money_damage, health_scale, size_scale, audio=None) -> None:
        self.announcement_timer = max(0.0, self.announcement_timer - dt)
        if self.level3_phase in {"intro", "revolt_news"}:
            return
        if self.level3_phase == "rebellion_animation":
            if self.rebellion_elapsed == 0.0 and audio:
                audio.play("ai_transform")
            self.rebellion_elapsed += dt
            if self.rebellion_elapsed >= 3.0:
                if audio:
                    audio.set_combat_ambience(3, rebel=True)
                self.start_rogue_wave(4)
            return
        if self.level3_phase == "apology":
            self.apology_elapsed += dt
            return
        if self.level3_phase == "friendly":
            assert self.assistant is not None
            self.fear_drop_timer += dt
            while self.fear_drop_timer >= 2.0:
                self.fear_drop_timer -= 2.0
                self.drop_dispersed_fear_fragment()
            fear_count = player.fragments["Fear"]
            self.assistant.follow(player, dt, fear_count)
            self.assistant.fire_at_nearest(self.enemies, now, fear_count)
            self.update_rolling_enemies(dt, player, now, speed_scale, money_damage, health_scale, size_scale, audio)
            self.resolve_player_bullets(player, audio)
            self.assistant.update_bullets(dt, self.enemies)
            self.resolve_assistant_bullets(audio)
            self.enemies = [enemy for enemy in self.enemies if enemy.alive]
            if not self.enemies:
                if self.wave_index < 3:
                    self.start_level3_wave(self.wave_index + 1)
                else:
                    self.level3_phase = "revolt_news"
                    self.news_request = "ai_revolt"
            return
        if self.level3_phase == "rogue":
            if self.rogue_wave_delay > 0:
                self.rogue_wave_delay = max(0.0, self.rogue_wave_delay - dt)
                if self.rogue_wave_delay == 0:
                    self.start_rogue_wave(self.wave_index + 1)
                return
            self.resolve_player_rogue_hits(player, audio)
            for rogue in self.rogue_ais:
                rogue.update(dt, player, now, player.fragments["Fear"])
                rogue.update_bullets(dt, player)
                for hit_x, hit_y in rogue.apply_bullet_hits(player):
                    self.add_combat_effect(hit_x, hit_y, "player_hit")
                    if audio:
                        audio.play("hit_heavy")
            self.resolve_entities_and_player_collisions(self.rogue_ais, player)
            defeated = [rogue for rogue in self.rogue_ais if not rogue.alive]
            for rogue in defeated:
                self.fragments.append(MemoryFragment(rogue.x, rogue.y, random.choice(FRAGMENT_TYPES)))
            self.rogue_ais = [rogue for rogue in self.rogue_ais if rogue.alive]
            if not self.rogue_ais:
                if self.wave_index < 6:
                    self.rogue_wave_delay = 3.0
                else:
                    self.begin_apology()

    def update_rolling_enemies(self, dt, player, now, speed_scale, money_damage, health_scale, size_scale, audio=None) -> None:
        for enemy in self.enemies:
            enemy.set_fear_strength(size_scale, health_scale)
            speed = enemy.speed * speed_scale
            vx = getattr(enemy, "roll_vx", speed)
            vy = getattr(enemy, "roll_vy", 0.0)
            length = max(1.0, math.hypot(vx, vy))
            enemy.roll_vx = vx / length * speed
            enemy.roll_vy = vy / length * speed
            enemy.x += enemy.roll_vx * dt
            enemy.y += enemy.roll_vy * dt
            if enemy.x <= enemy.radius or enemy.x >= SCREEN_WIDTH - enemy.radius:
                enemy.roll_vx *= -1
                enemy.x = max(enemy.radius, min(SCREEN_WIDTH - enemy.radius, enemy.x))
            if enemy.y <= enemy.radius or enemy.y >= SCREEN_HEIGHT - enemy.radius:
                enemy.roll_vy *= -1
                enemy.y = max(enemy.radius, min(SCREEN_HEIGHT - enemy.radius, enemy.y))
            self.keep_enemy_in_bounds(enemy)
            if self.assistant is not None:
                if self.bounce_assistant_from_enemy(self.assistant, enemy):
                    ai_collision_damage = money_damage * (enemy.damage / 8) / 3
                    if enemy.attack(player, now, ai_collision_damage):
                        self.add_combat_effect(self.assistant.x, self.assistant.y, "ai_hit")
                        if audio:
                            audio.play("hit_heavy")

        for enemy in self.enemies:
            dx, dy = player.x - enemy.x, player.y - enemy.y
            distance = max(1.0, math.hypot(dx, dy))
            if distance <= enemy.radius + player.radius:
                impact_damage = money_damage * (enemy.damage / 8)
                if enemy.attack(player, now, impact_damage):
                    self.add_combat_effect(player.x, player.y, "blood")
                    if audio:
                        audio.play("hit_heavy")
                    knockback = 34
                    player.x += dx / distance * knockback
                    player.y += dy / distance * knockback
                    player.x = max(player.radius, min(SCREEN_WIDTH - player.radius, player.x))
                    player.y = max(player.radius, min(SCREEN_HEIGHT - player.radius, player.y))

        combat_entities = [*self.enemies]
        if self.assistant is not None:
            combat_entities.append(self.assistant)
        self.resolve_entities_and_player_collisions(combat_entities, player)

    def resolve_entity_collisions(self, entities) -> None:
        """Separate every pair of arena entities so their collision circles never overlap."""
        for _ in range(max(8, len(entities) * 4)):
            collision_found = False
            for index, first in enumerate(entities):
                for second in entities[index + 1:]:
                    if self.separate_entities(first, second):
                        collision_found = True
            if not collision_found:
                break

    def resolve_entities_and_player_collisions(self, entities, player) -> None:
        """Resolve entity pairs and player contact until all hitboxes are separated."""
        for _ in range(max(12, len(entities) * 3)):
            self.resolve_entity_collisions(entities)
            self.separate_entities_from_player(entities, player)
            if self.entities_and_player_are_separated(entities, player):
                return

    @staticmethod
    def entities_and_player_are_separated(entities, player) -> bool:
        for index, first in enumerate(entities):
            if math.hypot(first.x - player.x, first.y - player.y) < first.radius + player.radius:
                return False
            for second in entities[index + 1:]:
                if math.hypot(first.x - second.x, first.y - second.y) < first.radius + second.radius:
                    return False
        return True

    def separate_entities(self, first, second) -> bool:
        dx, dy = second.x - first.x, second.y - first.y
        distance = math.hypot(dx, dy)
        minimum_distance = first.radius + second.radius
        if distance >= minimum_distance:
            return False
        if distance < 0.001:
            angle = math.tau * ((id(first) ^ id(second)) & 0xFF) / 256
            dx, dy, distance = math.cos(angle), math.sin(angle), 1.0
        overlap = minimum_distance - distance + ENTITY_COLLISION_PADDING
        first.x -= dx / distance * overlap / 2
        first.y -= dy / distance * overlap / 2
        second.x += dx / distance * overlap / 2
        second.y += dy / distance * overlap / 2
        self.keep_enemy_in_bounds(first)
        self.keep_enemy_in_bounds(second)
        return True

    def separate_entities_from_player(self, entities, player) -> None:
        for entity in entities:
            self.separate_entity_from_player(entity, player)

    def separate_entity_from_player(self, entity, player) -> None:
        """Keep combat entities outside the player hitbox in Levels 2 and 3."""
        dx, dy = entity.x - player.x, entity.y - player.y
        distance = math.hypot(dx, dy)
        minimum_distance = entity.radius + player.radius
        if distance >= minimum_distance:
            return
        if distance < 0.001:
            dx, dy, distance = 1.0, 0.0, 1.0
        overlap = minimum_distance - distance + ENTITY_COLLISION_PADDING
        entity.x += dx / distance * overlap
        entity.y += dy / distance * overlap
        self.keep_enemy_in_bounds(entity)

        # If an enemy is already against a wall, move the player just enough
        # to finish separating the two collision boxes.
        dx, dy = entity.x - player.x, entity.y - player.y
        distance = math.hypot(dx, dy)
        if distance >= minimum_distance:
            return
        if distance < 0.001:
            dx, dy, distance = 1.0, 0.0, 1.0
        overlap = minimum_distance - distance + ENTITY_COLLISION_PADDING
        player.x -= dx / distance * overlap
        player.y -= dy / distance * overlap
        player.x = max(player.radius, min(SCREEN_WIDTH - player.radius, player.x))
        player.y = max(player.radius, min(SCREEN_HEIGHT - player.radius, player.y))

    def drop_dispersed_fear_fragment(self) -> None:
        """Place each timed Fear fragment across the whole arena, not its centre."""
        for _ in range(12):
            x = random.randint(70, SCREEN_WIDTH - 70)
            y = random.randint(110, SCREEN_HEIGHT - 60)
            if all(
                fragment.kind != "Fear" or math.hypot(fragment.x - x, fragment.y - y) >= 150
                for fragment in self.fragments
            ):
                self.fragments.append(MemoryFragment(x, y, "Fear"))
                return
        self.fragments.append(
            MemoryFragment(random.randint(70, SCREEN_WIDTH - 70), random.randint(110, SCREEN_HEIGHT - 60), "Fear")
        )

    @staticmethod
    def bounce_assistant_from_enemy(assistant: DreamAssistant, enemy: Enemy) -> bool:
        """The assistant is invulnerable but is physically pushed by rolling enemies."""
        dx, dy = assistant.x - enemy.x, assistant.y - enemy.y
        distance = math.hypot(dx, dy)
        minimum = assistant.radius + enemy.radius
        if distance >= minimum:
            return False
        if distance < 0.1:
            dx, dy, distance = 1.0, 0.0, 1.0
        push = minimum - distance + 16
        assistant.x = max(assistant.radius, min(SCREEN_WIDTH - assistant.radius, assistant.x + dx / distance * push))
        assistant.y = max(assistant.radius, min(SCREEN_HEIGHT - assistant.radius, assistant.y + dy / distance * push))
        enemy.roll_vx *= -1
        enemy.roll_vy *= -1
        return True

    def update_combat_effects(self, dt: float) -> None:
        for effect in self.combat_effects:
            effect.lifetime -= dt
        self.combat_effects = [effect for effect in self.combat_effects if effect.lifetime > 0]
        for target in [*self.enemies, *self.rogue_ais]:
            target.hit_flash = max(0.0, getattr(target, "hit_flash", 0.0) - dt)

    def add_combat_effect(self, x: float, y: float, kind: str) -> None:
        self.combat_effects.append(CombatEffect(x, y, kind))

    def resolve_player_bullets(self, player, audio=None) -> None:
        for bullet in player.bullets:
            if not bullet.alive:
                continue
            for enemy in self.enemies:
                if enemy.alive and math.hypot(bullet.x - enemy.x, bullet.y - enemy.y) <= bullet.radius + enemy.radius:
                    enemy.take_damage(bullet.damage)
                    bullet.alive = False
                    enemy.hit_flash = 0.14
                    self.add_combat_effect(enemy.x, enemy.y, "enemy_hit")
                    if audio:
                        audio.play("hit_light")
                    if not enemy.alive:
                        self.kills += 1
                        self.fragments.append(MemoryFragment(enemy.x, enemy.y, enemy.drop_memory()))
                    break

    def resolve_assistant_bullets(self, audio=None) -> None:
        assert self.assistant is not None
        for bullet in self.assistant.bullets:
            if not bullet.alive:
                continue
            for enemy in self.enemies:
                if id(enemy) in bullet.hit_targets or not enemy.alive:
                    continue
                if math.hypot(bullet.x - enemy.x, bullet.y - enemy.y) <= bullet.radius + enemy.radius:
                    enemy.take_damage(bullet.damage)
                    enemy.hit_flash = 0.14
                    self.add_combat_effect(enemy.x, enemy.y, "enemy_hit")
                    if audio:
                        audio.play("hit_light")
                    bullet.hit_targets.add(id(enemy))
                    if not enemy.alive:
                        self.kills += 1
                        self.fragments.append(MemoryFragment(enemy.x, enemy.y, enemy.drop_memory()))
                    if not bullet.piercing:
                        bullet.alive = False
                    break

    def resolve_player_rogue_hits(self, player, audio=None) -> None:
        for bullet in player.bullets:
            if not bullet.alive:
                continue
            for rogue in self.rogue_ais:
                if rogue.alive and math.hypot(bullet.x - rogue.x, bullet.y - rogue.y) <= bullet.radius + rogue.radius:
                    rogue.take_damage(bullet.damage)
                    bullet.alive = False
                    rogue.hit_flash = 0.14
                    self.add_combat_effect(rogue.x, rogue.y, "enemy_hit")
                    if audio:
                        audio.play("hit_light")
                    break

    def begin_apology(self) -> None:
        self.level3_phase = "apology"
        self.apology_elapsed = 0.0
        self.cleared = True
        self.assistant = DreamAssistant(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)

    def drop_world_cup_fragment(self) -> None:
        size = 10
        self.fragments.append(
            MemoryFragment(
                random.randint(size, SCREEN_WIDTH - size),
                random.randint(size, SCREEN_HEIGHT - size),
                random.choice(("Hope", "Dream")),
                size,
            )
        )

    @staticmethod
    def keep_enemy_in_bounds(enemy: Enemy) -> None:
        radius = min(enemy.radius, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        enemy.radius = radius
        enemy.x = max(radius, min(SCREEN_WIDTH - radius, enemy.x))
        enemy.y = max(radius, min(SCREEN_HEIGHT - radius, enemy.y))

    def update_world_cup(self, dt, player, now, fear_scale, money_damage, audio=None) -> None:
        for enemy in self.enemies:
            dx, dy = player.x - enemy.x, player.y - enemy.y
            distance = max(1.0, math.hypot(dx, dy))
            side = math.sin(now * 3 + enemy.x * 0.01)
            direction = -1 if distance < 260 else (1 if distance > 420 else 0)
            enemy.x += (dx / distance * direction + (-dy / distance) * side) * enemy.speed * fear_scale * dt
            enemy.y += (dy / distance * direction + (dx / distance) * side) * enemy.speed * fear_scale * dt
            self.keep_enemy_in_bounds(enemy)
            if now - enemy._last_attack_at > 1.35 / fear_scale:
                self.enemy_bullets.append(EnemyBullet(enemy.x, enemy.y, dx / distance * 300 * fear_scale, dy / distance * 300 * fear_scale))
                enemy._last_attack_at = now
        self.resolve_entities_and_player_collisions(self.enemies, player)
        for bullet in player.bullets:
            for enemy in self.enemies:
                if bullet.alive and math.hypot(bullet.x - enemy.x, bullet.y - enemy.y) <= bullet.radius + enemy.radius:
                    enemy.hp = 0
                    bullet.alive = False
                    if audio:
                        audio.play("hit_light")
                    self.kills += 1
                    self.pending_reward = True
                    if random.random() < 0.5:
                        self.pending_event = random.choice(((30, 15, 5), (50, 10, 10), (70, 5, 5)))
                    break
        self.enemies = [enemy for enemy in self.enemies if enemy.alive]
        for bullet in self.enemy_bullets:
            bullet.update(dt)
            if bullet.alive and math.hypot(bullet.x - player.x, bullet.y - player.y) < player.radius + 6:
                player.lose_money(money_damage)
                bullet.alive = False
                if audio:
                    audio.play("hit_heavy")
        self.enemy_bullets = [bullet for bullet in self.enemy_bullets if bullet.alive]

    def resolve_reward(self, player, choice: int | None = None, accept: bool = True) -> None:
        if self.pending_event and accept:
            chance, hope, fear = self.pending_event
            if random.randint(1, 100) <= chance:
                added = player.add_fragment("Hope", hope)
                self.reward_message = f"Hope +{added}" if added else "Hope capacity reached"
            else:
                added = player.add_fragment("Fear", fear)
                self.reward_message = f"Fear +{added}" if added else "Fear capacity reached"
        elif self.pending_event:
            self.reward_message = "Event declined"
        elif choice == 0:
            added = player.add_fragment("Hope", 3)
            self.reward_message = f"Hope +{added}" if added else "Hope capacity reached"
        elif choice == 1:
            added = player.add_fragment("Dream", 3)
            self.reward_message = f"Dream +{added}" if added else "Dream capacity reached"
        elif choice == 2:
            player.fragments["Fear"] = max(0, player.fragments["Fear"] - 3)
            self.reward_message = "Fear -3"
        self.pending_reward = False
        self.pending_event = None
        if not self.enemies:
            if self.wave_index == 3:
                self.cleared = True
            else:
                self.start_wave(self.wave_index + 1)

    def collect_fragments(self, player) -> None:
        remaining: list[MemoryFragment] = []
        for fragment in self.fragments:
            if math.hypot(fragment.x - player.x, fragment.y - player.y) <= fragment.size + player.radius:
                if player.add_item(fragment.kind):
                    self.collected_fragments += 1
                else:
                    remaining.append(fragment)
            else:
                remaining.append(fragment)
        self.fragments = remaining

    def scatter_fear_fragments(self, player, amount: int = 14) -> None:
        virus_size = 24
        for _ in range(amount):
            angle = random.uniform(0, math.tau)
            distance = random.uniform(30, 250)
            self.fragments.append(
                MemoryFragment(
                    max(virus_size + 8, min(SCREEN_WIDTH - virus_size - 8, player.x + math.cos(angle) * distance)),
                    max(virus_size + 8, min(SCREEN_HEIGHT - virus_size - 8, player.y + math.sin(angle) * distance)),
                    "Fear",
                    virus_size,
                    True,
                )
            )

    @staticmethod
    def draw_football_field(surface) -> None:
        width, height = surface.get_size()
        surface.fill((37, 118, 62))
        stripe_width = max(1, width // 12)
        for index, x in enumerate(range(0, width, stripe_width)):
            if index % 2 == 0:
                pygame.draw.rect(surface, (42, 132, 69), (x, 0, stripe_width, height))
        field = pygame.Rect(42, 72, width - 84, height - 112)
        line_color = (240, 245, 230)
        pygame.draw.rect(surface, line_color, field, 3)
        center_x, center_y = field.center
        pygame.draw.line(surface, line_color, (center_x, field.top), (center_x, field.bottom), 3)
        pygame.draw.circle(surface, line_color, (center_x, center_y), 82, 3)
        pygame.draw.circle(surface, line_color, (center_x, center_y), 4)
        box_height, small_box_height = 300, 150
        box_top, small_box_top = center_y - box_height // 2, center_y - small_box_height // 2
        pygame.draw.rect(surface, line_color, (field.left, box_top, 145, box_height), 3)
        pygame.draw.rect(surface, line_color, (field.right - 145, box_top, 145, box_height), 3)
        pygame.draw.rect(surface, line_color, (field.left, small_box_top, 58, small_box_height), 3)
        pygame.draw.rect(surface, line_color, (field.right - 58, small_box_top, 58, small_box_height), 3)
        pygame.draw.rect(surface, line_color, (field.left - 18, center_y - 46, 18, 92), 2)
        pygame.draw.rect(surface, line_color, (field.right, center_y - 46, 18, 92), 2)

    def draw(self, surface, fonts, fear_price: float = 1000.0) -> None:
        colors = {1: (20, 28, 48), 2: (28, 45, 35), 3: (42, 34, 60)}
        if self.world_cup:
            self.draw_football_field(surface)
        else:
            surface.fill(colors.get(self.index, (20, 20, 24)))
            for line_y in range(80, SCREEN_HEIGHT, 80):
                pygame.draw.line(surface, (50, 60, 90), (0, line_y), (SCREEN_WIDTH, line_y), 1)
        for enemy in self.enemies:
            color = (255, 245, 190) if getattr(enemy, "hit_flash", 0.0) > 0 else (230, 60, 60)
            pygame.draw.circle(surface, color, (int(enemy.x), int(enemy.y)), enemy.radius)
            if self.is_dream_factory:
                pygame.draw.circle(surface, (255, 180, 90), (int(enemy.x), int(enemy.y)), max(3, enemy.radius // 2), 2)
        for bullet in self.enemy_bullets:
            pygame.draw.circle(surface, (255, 110, 70), (int(bullet.x), int(bullet.y)), 6)
        if self.assistant is not None:
            self.assistant.draw(surface, transforming=self.level3_phase == "rebellion_animation", elapsed=self.rebellion_elapsed)
        for rogue in self.rogue_ais:
            rogue.draw(surface)
        fragment_colors = {"Hope": (120, 255, 170), "Dream": (130, 160, 255), "Fear": (220, 120, 255)}
        for fragment in self.fragments:
            color = fragment_colors[fragment.kind]
            if fragment.is_covid:
                center = (int(fragment.x), int(fragment.y))
                radius = fragment.size
                pygame.draw.circle(surface, (175, 42, 82), center, radius)
                pygame.draw.circle(surface, (255, 130, 160), center, radius, 2)
                for spike in range(12):
                    angle = math.tau * spike / 12
                    inner = (
                        int(fragment.x + math.cos(angle) * radius),
                        int(fragment.y + math.sin(angle) * radius),
                    )
                    outer = (
                        int(fragment.x + math.cos(angle) * (radius + 8)),
                        int(fragment.y + math.sin(angle) * (radius + 8)),
                    )
                    pygame.draw.line(surface, (255, 105, 145), inner, outer, 3)
                    pygame.draw.circle(surface, (255, 155, 180), outer, 4)
                pygame.draw.circle(surface, (105, 20, 55), center, max(4, radius // 3))
                continue
            pygame.draw.rect(surface, color, pygame.Rect(int(fragment.x - fragment.size / 2), int(fragment.y - fragment.size / 2), fragment.size, fragment.size))
        if fear_price > 1000:
            alpha = min(170, int((fear_price - 1000) / 9000 * 170))
            overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            pygame.draw.rect(overlay, (210, 0, 20, alpha), overlay.get_rect(), 4)
            surface.blit(overlay, (0, 0))
        # The combat HUD already identifies Dream Factory.  Keeping a second
        # title beneath that panel caused the text to peek out from its edge.
        # Other level titles start after the HUD instead of underneath it.
        if not self.is_dream_factory:
            label = fonts["body"].render(self.name, True, (240, 240, 255))
            surface.blit(label, (500, 18))
        if self.is_dream_factory:
            wave = fonts["small"].render(f"Wave {self.wave_index} / 6", True, (190, 230, 255))
            surface.blit(wave, (20, 52))
            message = self.level3_message()
            if message:
                text = fonts["title"].render(message, True, (255, 80, 90) if self.level3_phase == "rebellion_animation" else (120, 230, 255))
                surface.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, 100))
            if self.level3_phase == "apology":
                apology = fonts["body"].render("I'm sorry, I shouldn't have betrayed you", True, (150, 235, 255))
                surface.blit(apology, (SCREEN_WIDTH // 2 - apology.get_width() // 2, 185))
            if self.announcement_timer > 0:
                announcement = fonts["small"].render(self.announcement, True, (255, 235, 130))
                surface.blit(announcement, (SCREEN_WIDTH // 2 - announcement.get_width() // 2, SCREEN_HEIGHT - 58))

    def level3_message(self) -> str:
        if self.level3_phase != "rebellion_animation":
            return ""
        if self.rebellion_elapsed < 0.3:
            return "SYSTEM ERROR..."
        if self.rebellion_elapsed < 0.6:
            return "Recalculating..."
        if self.rebellion_elapsed < 1.0:
            return "Human identified as threat."
        return "Target acquired."

    def draw_combat_effects(self, surface) -> None:
        """Draw brief blood, spark, and hit-flash particles over combatants."""
        layer = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        for effect in self.combat_effects:
            ratio = max(0.0, effect.lifetime / effect.max_lifetime)
            if effect.kind == "blood":
                for index in range(7):
                    angle = math.tau * index / 7
                    distance = (1 - ratio) * 30 + 5
                    x = int(effect.x + math.cos(angle) * distance)
                    y = int(effect.y + math.sin(angle) * distance)
                    pygame.draw.circle(layer, (235, 35, 45, int(220 * ratio)), (x, y), max(2, int(5 * ratio)))
            elif effect.kind == "player_hit":
                pygame.draw.circle(layer, (255, 65, 75, int(220 * ratio)), (int(effect.x), int(effect.y)), int(10 + (1 - ratio) * 25), 3)
            elif effect.kind == "ai_hit":
                pygame.draw.circle(layer, (70, 225, 255, int(230 * ratio)), (int(effect.x), int(effect.y)), int(10 + (1 - ratio) * 25), 3)
                pygame.draw.circle(layer, (210, 250, 255, int(190 * ratio)), (int(effect.x), int(effect.y)), 5)
            else:
                pygame.draw.circle(layer, (255, 235, 100, int(230 * ratio)), (int(effect.x), int(effect.y)), int(8 + (1 - ratio) * 22), 3)
                pygame.draw.circle(layer, (255, 255, 235, int(180 * ratio)), (int(effect.x), int(effect.y)), 4)
        surface.blit(layer, (0, 0))


class LevelManager:
    def __init__(self) -> None:
        self.levels = [
            Level(1, "LEVEL 1 - Memory City", 36, enemy_hp_multiplier=1.6, enemy_damage_bonus=6, enemy_speed_bonus=36),
            Level(2, "LEVEL 2 - World Cup Fever", 0, world_cup=True),
            Level(3, "LEVEL 3 - Dream Factory", 0),
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
