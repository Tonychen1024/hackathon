"""Scene manager and playable prototype scenes."""

from __future__ import annotations

from dataclasses import dataclass
import pygame

from config import SCREEN_HEIGHT, SCREEN_WIDTH, TITLE
from levels.level_manager import LevelManager
from market.market import Market
from player.player import Player


class Scene:
    name = "SCENE"

    def __init__(self, manager: "SceneManager") -> None:
        self.manager = manager

    def enter(self, **kwargs) -> None:
        _ = kwargs

    def exit(self) -> None:
        pass

    def handle_event(self, event) -> None:
        _ = event

    def update(self, dt: float) -> None:
        _ = dt

    def draw(self, surface) -> None:
        _ = surface


@dataclass
class GameContext:
    player: Player
    level_manager: LevelManager
    market: Market
    fonts: dict
    running: bool = True


class SceneManager:
    def __init__(self, context: GameContext) -> None:
        self.context = context
        self.scenes: dict[str, Scene] = {}
        self.current_scene: Scene | None = None
        self.last_combat_scene: str = "LEVEL"

    def register(self, scene: Scene) -> None:
        self.scenes[scene.name] = scene

    def change_scene(self, scene_name: str, **kwargs) -> None:
        if self.current_scene:
            self.current_scene.exit()
        self.current_scene = self.scenes[scene_name]
        self.current_scene.enter(**kwargs)

    def handle_event(self, event) -> None:
        if self.current_scene:
            self.current_scene.handle_event(event)

    def update(self, dt: float) -> None:
        if self.current_scene:
            self.current_scene.update(dt)

    def draw(self, surface) -> None:
        if self.current_scene:
            self.current_scene.draw(surface)


class MenuScene(Scene):
    name = "MENU"

    def enter(self, **kwargs) -> None:
        _ = kwargs
        self.selected = self.manager.context.level_manager.current_index

    def handle_event(self, event) -> None:
        if event.type != pygame.KEYDOWN:
            return

        levels = self.manager.context.level_manager.levels
        if event.key == pygame.K_UP:
            self.selected = max(0, self.selected - 1)
        elif event.key == pygame.K_DOWN:
            self.selected = min(len(levels) - 1, self.selected + 1)
        elif event.key == pygame.K_RETURN:
            self.manager.context.level_manager.set_level(self.selected)
            next_scene = "BOSS" if self.manager.context.level_manager.current_level.is_boss else "LEVEL"
            self.manager.change_scene(next_scene)

    def draw(self, surface) -> None:
        surface.fill((12, 15, 25))
        fonts = self.manager.context.fonts
        title = fonts["title"].render(TITLE + " Prototype", True, (130, 180, 255))
        tip = fonts["body"].render("ENTER 開始 | 上下選擇關卡", True, (236, 240, 255))
        surface.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 120))
        surface.blit(tip, (SCREEN_WIDTH // 2 - tip.get_width() // 2, 190))

        y = 260
        for idx, level in enumerate(self.manager.context.level_manager.levels):
            marker = ">" if idx == self.selected else " "
            color = (255, 240, 120) if idx == self.selected else (210, 220, 250)
            row = fonts["body"].render(f"{marker} {level.name}", True, color)
            surface.blit(row, (380, y))
            y += 52


class CombatScene(Scene):
    combat_scene_name = "LEVEL"

    def __init__(self, manager: "SceneManager") -> None:
        super().__init__(manager)
        self.show_clear = False

    def enter(self, **kwargs) -> None:
        if kwargs.get("resume", False):
            return
        self.show_clear = False
        context = self.manager.context
        context.level_manager.current_level.enter()
        context.player.reset_position(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)

    def handle_event(self, event) -> None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_TAB:
            self.manager.last_combat_scene = self.combat_scene_name
            self.manager.change_scene("MARKET")

        if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
            level_manager = self.manager.context.level_manager
            if level_manager.current_level.cleared:
                if level_manager.move_next():
                    scene_name = "BOSS" if level_manager.current_level.is_boss else "LEVEL"
                    self.manager.change_scene(scene_name)
                else:
                    self.manager.change_scene("GAME_OVER")

    def update(self, dt: float) -> None:
        context = self.manager.context
        level = context.level_manager.current_level
        context.market.update(dt)
        effects = context.market.effects(context.player)

        keys = pygame.key.get_pressed()
        context.player.handle_movement(keys, dt, SCREEN_WIDTH, SCREEN_HEIGHT)
        if pygame.mouse.get_pressed()[0]:
            mx, my = pygame.mouse.get_pos()
            context.player.try_shoot(mx, my, pygame.time.get_ticks() / 1000.0, effects["dream_fire_scale"])

        context.player.update_bullets(dt, SCREEN_WIDTH, SCREEN_HEIGHT)
        context.player.heal(effects["hope_regen"] * dt)

        level.update(
            dt,
            context.player,
            pygame.time.get_ticks() / 1000.0,
            effects["fear_enemy_speed"],
        )
        level.collect_fragments(context.player)
        self.show_clear = level.cleared

        if (
            level.index == 1
            and not level.news_triggered
            and level.collected_fragments >= 8
        ):
            level.news_triggered = True
            context.market.trigger_ai_jobs_news()
            self.manager.last_combat_scene = self.combat_scene_name
            self.manager.change_scene("NEWS")
            return

        if context.player.hp <= 0:
            self.manager.change_scene("GAME_OVER")

    def draw(self, surface) -> None:
        context = self.manager.context
        level = context.level_manager.current_level
        level.draw(surface, context.fonts, context.market.stocks["Fear"]["price"])

        pygame.draw.circle(surface, (70, 140, 255), (int(context.player.x), int(context.player.y)), context.player.radius)
        for bullet in context.player.bullets:
            pygame.draw.circle(surface, (250, 230, 90), (int(bullet.x), int(bullet.y)), bullet.radius)

        draw_hud(surface, context)

        if self.show_clear:
            clear = context.fonts["title"].render("LEVEL CLEAR", True, (255, 255, 150))
            tip = context.fonts["body"].render("Press ENTER for next level", True, (255, 255, 255))
            surface.blit(clear, (SCREEN_WIDTH // 2 - clear.get_width() // 2, 280))
            surface.blit(tip, (SCREEN_WIDTH // 2 - tip.get_width() // 2, 345))


class LevelScene(CombatScene):
    name = "LEVEL"
    combat_scene_name = "LEVEL"


class BossScene(CombatScene):
    name = "BOSS"
    combat_scene_name = "BOSS"


class MarketScene(Scene):
    name = "MARKET"

    def enter(self, **kwargs) -> None:
        _ = kwargs
        self.stock_names = list(self.manager.context.market.stocks.keys())
        self.selected = 0

    @property
    def selected_stock(self) -> str:
        return self.stock_names[self.selected]

    def handle_event(self, event) -> None:
        if event.type != pygame.KEYDOWN:
            return

        context = self.manager.context
        if event.key == pygame.K_UP:
            self.selected = max(0, self.selected - 1)
        elif event.key == pygame.K_DOWN:
            self.selected = min(len(self.stock_names) - 1, self.selected + 1)
        elif event.key == pygame.K_b:
            context.market.buy_fragment(context.player, self.selected_stock, 1)
        elif event.key == pygame.K_s:
            context.market.sell_fragment(context.player, self.selected_stock, 1)
        elif event.key == pygame.K_ESCAPE:
            self.manager.change_scene(self.manager.last_combat_scene, resume=True)

    def update(self, dt: float) -> None:
        self.manager.context.market.update(dt)

    def draw(self, surface) -> None:
        context = self.manager.context
        fonts = context.fonts
        surface.fill((0, 0, 0))

        title = fonts["title"].render("MARKET", True, (255, 255, 255))
        surface.blit(title, (40, 20))

        money = fonts["body"].render(f"Money: {int(context.player.money)}", True, (255, 255, 255))
        surface.blit(money, (40, 100))

        y = 170
        for idx, stock_name in enumerate(self.stock_names):
            data = context.market.stocks[stock_name]
            owned = context.player.fragments.get(stock_name, 0)
            marker = ">" if idx == self.selected else " "
            line = f"{marker} {stock_name}: Price {data['price']:,.2f} | Owned {owned}"
            color = (255, 230, 120) if idx == self.selected else (220, 220, 220)
            text = fonts["body"].render(line, True, color)
            surface.blit(text, (40, y))
            y += 50

        guide = fonts["small"].render("UP/DOWN 選擇 | B 買入 | S 賣出 1 個碎片 | ESC 返回戰鬥", True, (200, 200, 200))
        surface.blit(guide, (40, 660))


class NewsScene(Scene):
    """A modal news screen; combat is paused because its scene is inactive."""

    name = "NEWS"

    def handle_event(self, event) -> None:
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_ESCAPE):
            self.manager.change_scene(self.manager.last_combat_scene, resume=True)

    def draw(self, surface) -> None:
        context = self.manager.context
        fonts = context.fonts
        surface.fill((15, 12, 24))
        title = fonts["title"].render("BREAKING NEWS", True, (255, 100, 100))
        headline = fonts["body"].render("AI is about to explode and replace 80% of human jobs", True, (255, 235, 170))
        result = fonts["body"].render("FEAR x10 and becomes highly volatile", True, (220, 220, 255))
        tip = fonts["small"].render("Press ENTER, SPACE, or ESC to resume combat", True, (200, 200, 200))
        surface.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 220))
        surface.blit(headline, (SCREEN_WIDTH // 2 - headline.get_width() // 2, 310))
        surface.blit(result, (SCREEN_WIDTH // 2 - result.get_width() // 2, 365))
        surface.blit(tip, (SCREEN_WIDTH // 2 - tip.get_width() // 2, 450))


class GameOverScene(Scene):
    name = "GAME_OVER"

    def handle_event(self, event) -> None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
            player = self.manager.context.player
            player.hp = 100
            self.manager.change_scene("MENU")

    def draw(self, surface) -> None:
        fonts = self.manager.context.fonts
        surface.fill((8, 8, 12))
        title = fonts["title"].render("GAME OVER", True, (255, 120, 120))
        tip = fonts["body"].render("Press ENTER to return MENU", True, (235, 235, 235))
        surface.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 280))
        surface.blit(tip, (SCREEN_WIDTH // 2 - tip.get_width() // 2, 350))


def draw_hud(surface, context: GameContext) -> None:
    fonts = context.fonts
    player = context.player
    level = context.level_manager.current_level

    left_lines = [
        f"HP: {int(player.hp)}",
        f"Money: {int(player.money)}",
        f"Level: {level.index}",
        f"hope_owned: {player.fragments['Hope']}",
        f"dream_owned: {player.fragments['Dream']}",
        f"fear_owned: {player.fragments['Fear']}",
    ]
    for idx, line in enumerate(left_lines):
        txt = fonts["body"].render(line, True, (240, 240, 255))
        surface.blit(txt, (16, 16 + idx * 30))

    x = SCREEN_WIDTH - 260
    y = 16
    for stock_name, data in context.market.stocks.items():
        txt = fonts["small"].render(f"{stock_name}: {data['price']:,.2f}", True, (255, 255, 255))
        surface.blit(txt, (x, y))
        y += 24
