"""Main game orchestration and scene flow."""

from __future__ import annotations

import pygame

from config import COLORS, FPS, SCREEN_HEIGHT, SCREEN_WIDTH, TITLE
from core.event_system import EventSystem
from core.game_state import RuntimeState, SaveData, SceneType
from core.save_system import SaveSystem
from core.scene_manager import SceneManager
from levels.level_01 import Level01
from levels.level_02 import Level02
from levels.level_03 import Level03
from levels.level_04 import Level04
from levels.level_05 import Level05
from levels.level_manager import LevelManager
from market.market import Market
from player.player import Player
from ui.boss_ui import BossUI
from ui.hud import HUD
from ui.market_ui import MarketUI


class BaseScene:
    def __init__(self, game: "Game", name: str) -> None:
        self.game = game
        self.name = name

    def enter(self) -> None:
        pass

    def exit(self) -> None:
        pass

    def handle_event(self, event) -> None:
        _ = event

    def update(self, dt: float) -> None:
        _ = dt

    def draw(self, surface) -> None:
        _ = surface


class MenuScene(BaseScene):
    def __init__(self, game: "Game") -> None:
        super().__init__(game, "Menu")

    def handle_event(self, event) -> None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
            self.game.start_adventure()

    def draw(self, surface) -> None:
        surface.fill(COLORS["bg"])
        title = self.game.fonts["title"].render(TITLE, True, COLORS["accent"])
        subtitle = self.game.fonts["body"].render("Press ENTER to start memory hunting", True, COLORS["text"])
        surface.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 270))
        surface.blit(subtitle, (SCREEN_WIDTH // 2 - subtitle.get_width() // 2, 340))


class LevelScene(BaseScene):
    def __init__(self, game: "Game") -> None:
        super().__init__(game, "Level")

    def enter(self) -> None:
        level = self.game.level_manager.current_level
        level.load()
        self.game.runtime_state.scene = SceneType.LEVEL

    def update(self, dt: float) -> None:
        level = self.game.level_manager.current_level
        level.update(dt)
        self.game.runtime_state.score += int(dt * 10)
        if level.complete():
            self.game.open_market()

    def draw(self, surface) -> None:
        level = self.game.level_manager.current_level
        level.draw(surface, pygame, self.game.fonts)

        if level.name.startswith("LEVEL 2"):
            childhood_stock = self.game.market.stocks["Childhood"].price
            level.map_obj.draw(surface, pygame, childhood_stock)

        self.game.hud.draw(surface, self.game.fonts, self.game.player, self.game.runtime_state)


class MarketScene(BaseScene):
    def __init__(self, game: "Game") -> None:
        super().__init__(game, "Market")
        self.stock_names: list[str] = []
        self.selected_idx = 0

    def enter(self) -> None:
        self.stock_names = list(self.game.market.stocks.keys())
        self.selected_idx = 0
        self.game.market.update_price()
        self.game.market.random_event()
        self.game.market.apply_gameplay_effects(self.game.player)
        self.game.runtime_state.scene = SceneType.MARKET

    def handle_event(self, event) -> None:
        if event.type != pygame.KEYDOWN:
            return

        if event.key == pygame.K_UP:
            self.selected_idx = max(0, self.selected_idx - 1)
        elif event.key == pygame.K_DOWN:
            self.selected_idx = min(len(self.stock_names) - 1, self.selected_idx + 1)
        elif event.key == pygame.K_b:
            self.game.market.buy(self.game.player, self.selected_stock, 1)
        elif event.key == pygame.K_s:
            self.game.market.sell(self.game.player, self.selected_stock, 1)
        elif event.key == pygame.K_RETURN:
            self.game.open_boss()

    @property
    def selected_stock(self) -> str:
        return self.stock_names[self.selected_idx]

    def draw(self, surface) -> None:
        surface.fill((20, 25, 38))
        self.game.market_ui.draw(surface, self.game.fonts, self.game.market, self.selected_stock)
        if self.game.market.last_news:
            line = f"NEWS: {self.game.market.last_news.title}"
            text = self.game.fonts["small"].render(line, True, (255, 224, 160))
            surface.blit(text, (36, 575))


class BossScene(BaseScene):
    def __init__(self, game: "Game") -> None:
        super().__init__(game, "Boss")
        self.boss = None

    def enter(self) -> None:
        self.boss = self.game.level_manager.current_level.create_boss()
        self.game.runtime_state.scene = SceneType.BOSS

    def handle_event(self, event) -> None:
        if event.type != pygame.KEYDOWN:
            return

        if event.key == pygame.K_f:
            self.boss.take_damage(self.game.player.damage)
            if not self.boss.alive:
                self.game.finish_current_level()
        elif event.key == pygame.K_SPACE:
            self.boss.special_ability(self.game.player)

    def draw(self, surface) -> None:
        surface.fill((34, 20, 24))
        self.game.boss_ui.draw(surface, self.game.fonts, self.boss)
        pygame.draw.rect(surface, (200, 80, 100), (510, 280, 260, 260), 3)


class GameOverScene(BaseScene):
    def __init__(self, game: "Game") -> None:
        super().__init__(game, "GameOver")

    def draw(self, surface) -> None:
        surface.fill((8, 10, 16))
        title = self.game.fonts["title"].render("MISSION COMPLETE", True, (140, 220, 180))
        score = self.game.fonts["body"].render(f"Final Score: {self.game.runtime_state.score}", True, (240, 245, 255))
        tip = self.game.fonts["small"].render("Press ESC to quit.", True, (170, 180, 210))
        surface.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 260))
        surface.blit(score, (SCREEN_WIDTH // 2 - score.get_width() // 2, 330))
        surface.blit(tip, (SCREEN_WIDTH // 2 - tip.get_width() // 2, 370))


class Game:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption(TITLE)
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()

        self.fonts = {
            "title": pygame.font.SysFont("consolas", 48, bold=True),
            "body": pygame.font.SysFont("consolas", 26),
            "small": pygame.font.SysFont("consolas", 18),
        }

        self.events = EventSystem()
        self.runtime_state = RuntimeState()
        self.save_system = SaveSystem()
        self.player = Player()
        self.market = Market()
        self.level_manager = LevelManager([Level01(), Level02(), Level03(), Level04(), Level05()])

        self.hud = HUD()
        self.market_ui = MarketUI()
        self.boss_ui = BossUI()

        self.scene_manager = SceneManager()
        self.menu_scene = MenuScene(self)
        self.level_scene = LevelScene(self)
        self.market_scene = MarketScene(self)
        self.boss_scene = BossScene(self)
        self.game_over_scene = GameOverScene(self)

        self.restore_progress()
        self.scene_manager.switch(self.menu_scene)

    def restore_progress(self) -> None:
        data = self.save_system.load()
        self.player.money = data.player_assets.get("money", self.player.money)
        self.player.inventory = data.player_assets.get("inventory", self.player.inventory)
        self.player.stocks = data.player_assets.get("stocks", self.player.stocks)

        for name, stock in self.market.stocks.items():
            if name in data.stock_data:
                stock.price = data.stock_data[name].get("price", stock.price)
                stock.history = data.stock_data[name].get("history", stock.history)

        self.runtime_state.current_level_index = max(0, data.unlocked_levels - 1)
        self.level_manager.current_index = min(self.runtime_state.current_level_index, len(self.level_manager.levels) - 1)

    def export_save_data(self) -> SaveData:
        return SaveData(
            player_assets={
                "money": self.player.money,
                "inventory": self.player.inventory,
                "stocks": self.player.stocks,
            },
            stock_data={
                name: {"price": stock.price, "history": stock.history}
                for name, stock in self.market.stocks.items()
            },
            unlocked_levels=self.level_manager.current_index + 1,
            high_score=max(self.runtime_state.score, 0),
        )

    def start_adventure(self) -> None:
        self.scene_manager.switch(self.level_scene)

    def open_market(self) -> None:
        self.scene_manager.switch(self.market_scene)

    def open_boss(self) -> None:
        self.scene_manager.switch(self.boss_scene)

    def finish_current_level(self) -> None:
        if self.level_manager.move_next():
            self.runtime_state.current_level_index = self.level_manager.current_index
            self.scene_manager.switch(self.level_scene)
        else:
            self.runtime_state.game_completed = True
            self.scene_manager.switch(self.game_over_scene)

    def run(self) -> None:
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False
                else:
                    self.scene_manager.handle_event(event)

            self.scene_manager.update(dt)
            self.scene_manager.draw(self.screen)
            pygame.display.flip()

        self.save_system.save(self.export_save_data())
        pygame.quit()
