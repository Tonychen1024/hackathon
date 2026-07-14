"""Entry point for playable Memory Crash prototype."""

from __future__ import annotations

import pygame

from config import FPS, SCREEN_HEIGHT, SCREEN_WIDTH, TITLE
from core.scene_manager import (
    EndingScene,
    GameContext,
    GameOverScene,
    LevelScene,
    Level2IntroScene,
    MarketScene,
    MenuScene,
    NewsScene,
    PenaltyScene,
    FeeNoticeScene,
    TransactionLimitScene,
    SceneManager,
)
from core.ending_manager import EndingManager
from levels.level_manager import LevelManager
from market.market import Market
from player.player import Player


def main() -> None:
    pygame.init()
    pygame.display.set_caption(TITLE)
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()

    fonts = {
        "title": pygame.font.SysFont("consolas", 48, bold=True),
        "body": pygame.font.SysFont("consolas", 28),
        "small": pygame.font.SysFont("consolas", 18),
    }

    context = GameContext(
        player=Player(),
        level_manager=LevelManager(),
        market=Market(),
        fonts=fonts,
        ending_manager=EndingManager(),
    )
    scene_manager = SceneManager(context)
    scene_manager.register(MenuScene(scene_manager))
    scene_manager.register(LevelScene(scene_manager))
    scene_manager.register(Level2IntroScene(scene_manager))
    scene_manager.register(MarketScene(scene_manager))
    scene_manager.register(NewsScene(scene_manager))
    scene_manager.register(PenaltyScene(scene_manager))
    scene_manager.register(FeeNoticeScene(scene_manager))
    scene_manager.register(TransactionLimitScene(scene_manager))
    scene_manager.register(GameOverScene(scene_manager))
    scene_manager.register(EndingScene(scene_manager))
    scene_manager.change_scene("MENU")

    while context.running:
        dt = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                context.running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE and scene_manager.current_scene and scene_manager.current_scene.name == "MENU":
                context.running = False
            else:
                scene_manager.handle_event(event)

        scene_manager.update(dt)
        scene_manager.draw(screen)
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
