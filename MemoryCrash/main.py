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
    FragmentLimitScene,
    TransactionLimitScene,
    SceneManager,
)
from core.ending_manager import EndingManager
from levels.level_manager import LevelManager
from market.market import Market
from player.player import Player


def draw_return_to_menu_confirmation(surface, fonts: dict) -> None:
    """Draw the modal confirmation shown before abandoning a combat level."""
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 185))
    surface.blit(overlay, (0, 0))

    dialog = pygame.Rect(SCREEN_WIDTH // 2 - 310, SCREEN_HEIGHT // 2 - 120, 620, 240)
    pygame.draw.rect(surface, (25, 32, 52), dialog, border_radius=14)
    pygame.draw.rect(surface, (130, 180, 255), dialog, 3, border_radius=14)
    title = fonts["body"].render("Return to the main menu?", True, (245, 245, 255))
    tip = fonts["small"].render("ENTER / SPACE / CLICK: return    ESC / N: keep playing", True, (205, 220, 245))
    surface.blit(title, (dialog.centerx - title.get_width() // 2, dialog.y + 68))
    surface.blit(tip, (dialog.centerx - tip.get_width() // 2, dialog.y + 138))


def main() -> None:
    pygame.init()
    pygame.display.set_caption(TITLE)
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
    game_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
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
    scene_manager.register(FragmentLimitScene(scene_manager))
    scene_manager.register(GameOverScene(scene_manager))
    scene_manager.register(EndingScene(scene_manager))
    scene_manager.change_scene("MENU")
    return_to_menu_confirmation = False

    def viewport() -> tuple[pygame.Rect, tuple[int, int]]:
        window_width, window_height = screen.get_size()
        scale = min(window_width / SCREEN_WIDTH, window_height / SCREEN_HEIGHT)
        size = (max(1, round(SCREEN_WIDTH * scale)), max(1, round(SCREEN_HEIGHT * scale)))
        return pygame.Rect((window_width - size[0]) // 2, (window_height - size[1]) // 2, *size), size

    def to_game_coordinates(position: tuple[int, int]) -> tuple[int, int]:
        view, _ = viewport()
        x = (position[0] - view.x) * SCREEN_WIDTH / view.width
        y = (position[1] - view.y) * SCREEN_HEIGHT / view.height
        return max(0, min(SCREEN_WIDTH, round(x))), max(0, min(SCREEN_HEIGHT, round(y)))

    while context.running:
        dt = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if return_to_menu_confirmation:
                if event.type == pygame.QUIT:
                    context.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_y):
                        return_to_menu_confirmation = False
                        scene_manager.change_scene("MENU")
                    elif event.key in (pygame.K_ESCAPE, pygame.K_n):
                        return_to_menu_confirmation = False
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    dialog = pygame.Rect(SCREEN_WIDTH // 2 - 310, SCREEN_HEIGHT // 2 - 120, 620, 240)
                    if dialog.collidepoint(to_game_coordinates(event.pos)):
                        return_to_menu_confirmation = False
                        scene_manager.change_scene("MENU")
                continue

            if event.type == pygame.QUIT:
                context.running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE and scene_manager.current_scene and scene_manager.current_scene.name == "LEVEL":
                return_to_menu_confirmation = True
            elif event.type == pygame.VIDEORESIZE:
                screen = pygame.display.set_mode(event.size, pygame.RESIZABLE)
            else:
                if hasattr(event, "pos"):
                    event = pygame.event.Event(event.type, {**event.dict, "pos": to_game_coordinates(event.pos)})
                scene_manager.handle_event(event)

        context.mouse_position = to_game_coordinates(pygame.mouse.get_pos())
        if not return_to_menu_confirmation:
            scene_manager.update(dt)
        scene_manager.draw(game_surface)
        if return_to_menu_confirmation:
            draw_return_to_menu_confirmation(game_surface, fonts)
        view, size = viewport()
        screen.fill((0, 0, 0))
        screen.blit(pygame.transform.smoothscale(game_surface, size), view)
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
