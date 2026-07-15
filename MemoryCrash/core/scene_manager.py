"""Scene manager and playable prototype scenes."""

from __future__ import annotations

from dataclasses import dataclass
import math
import pygame

from config import SCREEN_HEIGHT, SCREEN_WIDTH, TITLE
from core.ending_manager import EndingManager
from levels.level_manager import LevelManager
from market.market import Market
from player.player import Player


# This control contains a long label, so keep enough horizontal breathing room
# between it and the exchange HUD on the right.
LEVEL3_FAST_FORWARD_BUTTON = pygame.Rect(SCREEN_WIDTH - 630, 14, 360, 42)
COMBAT_PAUSE_BUTTON = pygame.Rect(322, 14, 160, 42)
LEVEL_START_INVULNERABILITY_SECONDS = 3.0

UI_BG = (9, 13, 25)
UI_PANEL = (19, 28, 48)
UI_PANEL_ALT = (27, 39, 66)
UI_BORDER = (76, 107, 164)
UI_TEXT = (238, 244, 255)
UI_MUTED = (158, 177, 212)
UI_ACCENT = (93, 207, 255)
UI_HOPE = (112, 255, 174)
UI_DREAM = (125, 169, 255)
UI_FEAR = (255, 104, 127)
UI_GOLD = (255, 213, 110)


def draw_screen_background(surface, accent: tuple[int, int, int] = UI_ACCENT) -> None:
    """Draw the shared dark-tech backdrop used by menus and modal screens."""
    surface.fill(UI_BG)
    glow = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    pygame.draw.circle(glow, (*accent, 24), (SCREEN_WIDTH - 90, 70), 310)
    pygame.draw.circle(glow, (100, 92, 210, 16), (150, SCREEN_HEIGHT - 30), 260)
    surface.blit(glow, (0, 0))
    for x in range(0, SCREEN_WIDTH + 1, 64):
        pygame.draw.line(surface, (24, 35, 59), (x, 0), (x, SCREEN_HEIGHT), 1)
    for y in range(0, SCREEN_HEIGHT + 1, 64):
        pygame.draw.line(surface, (24, 35, 59), (0, y), (SCREEN_WIDTH, y), 1)


def draw_panel(surface, rect: pygame.Rect, *, border: tuple[int, int, int] = UI_BORDER, fill: tuple[int, int, int] = UI_PANEL, radius: int = 14) -> None:
    """Draw a raised, subtly highlighted information panel."""
    shadow = rect.move(0, 6)
    pygame.draw.rect(surface, (4, 7, 14), shadow, border_radius=radius)
    pygame.draw.rect(surface, fill, rect, border_radius=radius)
    pygame.draw.rect(surface, border, rect, 2, border_radius=radius)
    pygame.draw.line(surface, tuple(min(255, channel + 42) for channel in border), (rect.x + radius, rect.y + 2), (rect.right - radius, rect.y + 2), 1)


def draw_centered_text(surface, font, text: str, color: tuple[int, int, int], center: tuple[int, int]) -> None:
    label = font.render(text, True, color)
    surface.blit(label, label.get_rect(center=center))


def draw_centered_wrapped_text(
    surface, font, text: str, color: tuple[int, int, int], center_x: int, top: int, max_width: int, line_gap: int = 7
) -> int:
    """Draw a centered paragraph within a safe text width and return its height."""
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if current and font.size(candidate)[0] > max_width:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)

    y = top
    for line in lines:
        label = font.render(line, True, color)
        surface.blit(label, label.get_rect(midtop=(center_x, y)))
        y += label.get_height() + line_gap
    return y - top - line_gap


def draw_keycap(surface, font, text: str, position: tuple[int, int], accent: tuple[int, int, int] = UI_BORDER) -> int:
    label = font.render(text, True, UI_TEXT)
    rect = label.get_rect(topleft=(position[0] + 10, position[1] + 5)).inflate(20, 10)
    pygame.draw.rect(surface, UI_PANEL_ALT, rect, border_radius=6)
    pygame.draw.rect(surface, accent, rect, 1, border_radius=6)
    surface.blit(label, (position[0] + 10, position[1] + 5))
    return rect.width


def draw_section_label(surface, font, text: str, position: tuple[int, int], color: tuple[int, int, int] = UI_MUTED) -> None:
    label = font.render(text, True, color)
    surface.blit(label, position)
    pygame.draw.line(surface, color, (position[0], position[1] + label.get_height() + 6), (position[0] + 260, position[1] + label.get_height() + 6), 1)


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
    ending_manager: EndingManager
    running: bool = True
    mouse_position: tuple[int, int] = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)


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

    def start_selected_level(self) -> None:
        """Start the highlighted scenario from either keyboard or mouse input."""
        context = self.manager.context
        context.level_manager.set_level(self.selected)
        if context.level_manager.current_level.world_cup:
            context.player.reset_for_level_two()
        else:
            context.player.reset_for_new_run()
        context.market.reset()
        next_scene = "LEVEL2_INTRO" if context.level_manager.current_level.world_cup else "LEVEL"
        self.manager.change_scene(next_scene)

    def handle_event(self, event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for index in range(len(self.manager.context.level_manager.levels)):
                row = pygame.Rect(226, 262 + index * 96, 828, 82)
                if row.collidepoint(event.pos):
                    self.selected = index
                    self.start_selected_level()
                    return
            return

        if event.type != pygame.KEYDOWN:
            return

        levels = self.manager.context.level_manager.levels
        if event.key in (pygame.K_UP, pygame.K_w):
            self.selected = max(0, self.selected - 1)
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            self.selected = min(len(levels) - 1, self.selected + 1)
        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
            self.start_selected_level()

    def draw(self, surface) -> None:
        draw_screen_background(surface)
        fonts = self.manager.context.fonts
        draw_panel(surface, pygame.Rect(152 - 25, 70, 976 + 50, 570), border=UI_ACCENT, fill=(16, 27, 49), radius=22)
        draw_centered_text(surface, fonts["title"], TITLE.upper(), UI_TEXT, (SCREEN_WIDTH // 2, 135))
        draw_centered_text(surface, fonts["small"], "A MEMORY-DRIVEN MARKET SURVIVAL GAME", UI_ACCENT, (SCREEN_WIDTH // 2, 178))
        draw_section_label(surface, fonts["small"], "SELECT A SCENARIO", (226, 222))

        # Keep the timeline in the narrow left gutter so it lines up with each
        # scenario without competing with the card text.
        timeline_x = 208
        timeline_year_x = 170
        timeline_points = (303 - 3, 399 - 3, 495 - 3)
        timeline_years = ("2019", "2026", "2050")
        draw_centered_text(surface, fonts["small"], "PAST", UI_MUTED, (timeline_year_x, 269 - 3))
        pygame.draw.line(surface, UI_BORDER, (timeline_x, 284), (timeline_x, 514), 2)
        for point_y, year in zip(timeline_points, timeline_years):
            pygame.draw.circle(surface, UI_ACCENT, (timeline_x, point_y), 7)
            pygame.draw.circle(surface, UI_BG, (timeline_x, point_y), 3)
            pygame.draw.line(surface, UI_BORDER, (timeline_x + 7, point_y), (220, point_y), 1)
            draw_centered_text(surface, fonts["small"], year, UI_TEXT, (timeline_year_x, point_y))
        draw_centered_text(surface, fonts["small"], "FUTURE", UI_MUTED, (timeline_year_x + 4, 533))

        
        descriptions = (
            "Survive the first wave of unstable memories.",
            "Enter the World Cup market with limited trades.",
            "Trust the AI assistant — until it changes its mind.",
        )
        y = 262
        for idx, level in enumerate(self.manager.context.level_manager.levels):
            selected = idx == self.selected
            row = pygame.Rect(226, y, 828, 82)
            accent = (UI_GOLD if idx == 1 else UI_DREAM if idx == 2 else UI_ACCENT)
            draw_panel(surface, row, border=accent if selected else (55, 75, 112), fill=(32, 47, 77) if selected else UI_PANEL, radius=12)
            badge = pygame.Rect(row.x + 18, row.y + 17, 48, 48)
            pygame.draw.rect(surface, accent if selected else UI_PANEL_ALT, badge, border_radius=10)
            draw_centered_text(surface, fonts["body"], f"{idx + 1:02}", UI_BG if selected else UI_TEXT, badge.center)
            name = fonts["body"].render(level.name.replace("LEVEL ", ""), True, UI_TEXT if selected else (205, 217, 240))
            surface.blit(name, (row.x + 86, row.y + 14))
            detail = fonts["small"].render(descriptions[idx], True, UI_MUTED)
            surface.blit(detail, (row.x + 87, row.y + 49))
            if selected:
                marker = fonts["small"].render("READY", True, accent)
                surface.blit(marker, (row.right - marker.get_width() - 25, row.y + 31))
            y += 96

        draw_centered_text(surface, fonts["small"], "UP / DOWN  •  SELECT        ENTER  •  START", UI_MUTED, (SCREEN_WIDTH // 2, 602))


class CombatScene(Scene):
    combat_scene_name = "LEVEL"

    def __init__(self, manager: "SceneManager") -> None:
        super().__init__(manager)
        self.show_clear = False
        self.is_paused = False

    def enter(self, **kwargs) -> None:
        if kwargs.get("resume", False):
            self.manager.context.player.grant_invulnerability()
            return
        self.show_clear = False
        self.is_paused = False
        context = self.manager.context
        context.level_manager.current_level.enter()
        level = context.level_manager.current_level
        context.market.level_mode = "level2" if level.world_cup else ("level3" if level.is_dream_factory else "level1")
        context.player.reset_position(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
        context.player.grant_invulnerability(LEVEL_START_INVULNERABILITY_SECONDS)
        if level.is_dream_factory:
            context.market.trigger_ai_adoption()
            self.manager.last_combat_scene = self.combat_scene_name
            self.manager.change_scene("NEWS")

    def handle_event(self, event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if COMBAT_PAUSE_BUTTON.collidepoint(event.pos):
                self.is_paused = not self.is_paused
                return
            if self.is_paused:
                return
            context = self.manager.context
            level = context.level_manager.current_level
            if (
                level.is_dream_factory
                and level.level3_phase == "friendly"
                and level.wave_index in (1, 2, 3)
                and LEVEL3_FAST_FORWARD_BUTTON.collidepoint(event.pos)
                and level.skip_to_level3_transformation()
            ):
                context.market.trigger_ai_revolt()
            return

        if self.is_paused or event.type != pygame.KEYDOWN:
            return
        if event.key == pygame.K_SPACE:
            self.manager.context.player.try_dash(
                pygame.key.get_pressed(), SCREEN_WIDTH, SCREEN_HEIGHT
            )
        elif event.key == pygame.K_TAB:
            self.manager.last_combat_scene = self.combat_scene_name
            self.manager.change_scene("MARKET")
        elif event.key == pygame.K_ESCAPE:
            self.manager.change_scene("MENU")
        elif event.key == pygame.K_RETURN:
            level_manager = self.manager.context.level_manager
            if level_manager.current_level.cleared:
                if level_manager.current_level.is_dream_factory:
                    return
                if level_manager.move_next():
                    context = self.manager.context
                    if level_manager.current_level.world_cup:
                        context.player.reset_for_level_two()
                        context.market.reset()
                    scene_name = "LEVEL2_INTRO" if level_manager.current_level.world_cup else "LEVEL"
                    self.manager.change_scene(scene_name)
                else:
                    self.manager.context.ending_manager.start_ai_apology()
                    self.manager.change_scene("ENDING")

    def update(self, dt: float) -> None:
        if self.is_paused:
            return
        context = self.manager.context
        level = context.level_manager.current_level
        context.player.update_invulnerability(dt)
        context.market.update(dt)
        effects = context.market.effects(context.player)
        context.player.apply_fragment_effects(
            0 if level.world_cup else context.player.fragments["Dream"],
            0 if level.world_cup else context.player.fragments["Hope"], dt
        )

        keys = pygame.key.get_pressed()
        context.player.handle_movement(keys, dt, SCREEN_WIDTH, SCREEN_HEIGHT)
        if pygame.mouse.get_pressed()[0]:
            mx, my = context.mouse_position
            context.player.try_shoot(mx, my, pygame.time.get_ticks() / 1000.0, effects["dream_fire_scale"], level.world_cup)

        context.player.update_bullets(dt, SCREEN_WIDTH, SCREEN_HEIGHT)

        level.update(
            dt,
            context.player,
            pygame.time.get_ticks() / 1000.0,
            effects["fear_enemy_speed"],
            effects["fear_enemy_damage"],
            effects["fear_enemy_health"],
            effects["fear_enemy_size"],
        )
        level.collect_fragments(context.player)
        if level.world_cup and level.pending_reward:
            self.manager.last_combat_scene = self.combat_scene_name; self.manager.change_scene("PENALTY"); return
        if level.needs_news:
            if level.news_request == "ai_revolt":
                context.market.trigger_ai_revolt()
            self.manager.last_combat_scene = self.combat_scene_name
            self.manager.change_scene("NEWS")
            return
        if level.is_dream_factory and level.level3_phase == "apology" and level.apology_elapsed >= 3.0:
            context.ending_manager.start_ai_apology()
            self.manager.change_scene("ENDING")
            return
        self.show_clear = level.cleared

        if (
            level.index == 1
            and not level.news_triggered
            and level.elapsed >= 10.0
        ):
            level.news_triggered = True
            context.market.trigger_ai_jobs_news()
            level.scatter_fear_fragments(context.player)
            self.manager.last_combat_scene = self.combat_scene_name
            self.manager.change_scene("NEWS")
            return

        if context.player.money <= 0:
            if level.ai_combat_active:
                context.ending_manager.start_ai_victory()
                self.manager.change_scene("ENDING")
            else:
                self.manager.change_scene("GAME_OVER")

    def draw(self, surface) -> None:
        context = self.manager.context
        level = context.level_manager.current_level
        level.draw(surface, context.fonts, context.market.stocks["Fear"]["price"])

        draw_player_effects(surface, context.player)
        pygame.draw.circle(surface, (70, 140, 255), (int(context.player.x), int(context.player.y)), context.player.radius)
        draw_money_health_bar(surface, context.player)
        for bullet in context.player.bullets:
            if bullet.football:
                draw_rotating_football(surface, bullet)
            else:
                pygame.draw.circle(surface, (250, 230, 90), (int(bullet.x), int(bullet.y)), bullet.radius)
        level.draw_combat_effects(surface)

        draw_hud(surface, context)

        pause_label = "START" if self.is_paused else "PAUSE"
        pause_accent = UI_HOPE if self.is_paused else UI_GOLD
        draw_panel(surface, COMBAT_PAUSE_BUTTON, border=pause_accent, fill=(28, 57, 55) if self.is_paused else (58, 47, 28), radius=8)
        draw_centered_text(surface, context.fonts["small"], pause_label, UI_TEXT, COMBAT_PAUSE_BUTTON.center)

        if (
            level.is_dream_factory
            and level.level3_phase == "friendly"
            and level.wave_index in (1, 2, 3)
        ):
            draw_panel(surface, LEVEL3_FAST_FORWARD_BUTTON, border=UI_ACCENT, fill=(27, 77, 114), radius=8)
            label = context.fonts["small"].render("FAST FORWARD -> AI TRANSFORMATION", True, (240, 250, 255))
            surface.blit(
                label,
                (
                    LEVEL3_FAST_FORWARD_BUTTON.centerx - label.get_width() // 2,
                    LEVEL3_FAST_FORWARD_BUTTON.centery - label.get_height() // 2,
                ),
            )

        if self.show_clear and not level.is_dream_factory:
            modal = pygame.Rect(SCREEN_WIDTH // 2 - 260, 250, 520, 190)
            draw_panel(surface, modal, border=UI_GOLD, fill=(48, 43, 30), radius=18)
            draw_centered_text(surface, context.fonts["title"], "LEVEL CLEAR", UI_GOLD, (modal.centerx, modal.y + 63))
            draw_centered_text(surface, context.fonts["small"], "PRESS ENTER TO CONTINUE", UI_TEXT, (modal.centerx, modal.y + 127))


class LevelScene(CombatScene):
    name = "LEVEL"
    combat_scene_name = "LEVEL"

class Level2IntroScene(Scene):
    name = "LEVEL2_INTRO"

    def handle_event(self, event) -> None:
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE):
            self.manager.change_scene("LEVEL")

    def draw(self, surface):
        draw_screen_background(surface, UI_HOPE)
        f = self.manager.context.fonts
        draw_panel(surface, pygame.Rect(245, 200, 790, 300), border=UI_HOPE, fill=(18, 47, 45), radius=22)
        draw_centered_text(surface, f["title"], "WORLD CUP", UI_GOLD, (SCREEN_WIDTH // 2, 275))
        draw_centered_text(surface, f["body"], "The World Cup is in full swing.", UI_TEXT, (SCREEN_WIDTH // 2, 343))
        draw_centered_text(surface, f["body"], "Hold onto the hopes for the country you support.", UI_TEXT, (SCREEN_WIDTH // 2, 385))
        draw_centered_text(surface, f["small"], "PRESS ENTER OR SPACE TO KICK OFF", UI_HOPE, (SCREEN_WIDTH // 2, 448))


class MarketScene(Scene):
    name = "MARKET"

    def enter(self, **kwargs) -> None:
        _ = kwargs
        self.stock_names = ["Dream", "Hope", "Fear"]
        self.selected = 0

    @property
    def selected_stock(self) -> str:
        return self.stock_names[self.selected]

    def handle_event(self, event) -> None:
        if event.type != pygame.KEYDOWN:
            return

        context = self.manager.context
        if event.key in (pygame.K_UP, pygame.K_w):
            self.selected = max(0, self.selected - 1)
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            self.selected = min(len(self.stock_names) - 1, self.selected + 1)
        elif event.key == pygame.K_b:
            if context.market.level1_transaction_limit_reached:
                self.manager.change_scene("TRANSACTION_LIMIT")
                return
            if context.player.fragments.get(self.selected_stock, 0) >= context.player.FRAGMENT_CAP:
                self.manager.change_scene("FRAGMENT_LIMIT", fragment_name=self.selected_stock)
                return
            changed = context.market.buy_fragment(context.player, self.selected_stock, 1)
            if changed and context.level_manager.current_level.world_cup and not context.market.level2_fee_notice_shown:
                context.market.level2_fee_notice_shown = True; self.manager.change_scene("FEE_NOTICE")
        elif event.key == pygame.K_f:
            if context.market.level1_transaction_limit_reached:
                self.manager.change_scene("TRANSACTION_LIMIT")
                return
            changed = context.market.sell_fragment(context.player, self.selected_stock, 1)
            if changed and context.level_manager.current_level.world_cup and not context.market.level2_fee_notice_shown:
                context.market.level2_fee_notice_shown = True; self.manager.change_scene("FEE_NOTICE")
        elif event.key in (pygame.K_ESCAPE, pygame.K_TAB, pygame.K_q):
            self.manager.change_scene(self.manager.last_combat_scene, resume=True)

    def update(self, dt: float) -> None:
        self.manager.context.market.update(dt)

    def draw(self, surface) -> None:
        context = self.manager.context
        fonts = context.fonts
        draw_screen_background(surface, UI_DREAM)
        draw_panel(surface, pygame.Rect(30, 25, 1220, 82), border=UI_DREAM, fill=(17, 30, 57), radius=16)
        title = fonts["title"].render("MEMORY EXCHANGE", True, UI_TEXT)
        surface.blit(title, (58, 39))
        cash = pygame.Rect(946, 33, 274, 66)
        pygame.draw.rect(surface, (26, 55, 73), cash, border_radius=10)
        pygame.draw.rect(surface, UI_HOPE, cash, 1, border_radius=10)
        draw_centered_text(surface, fonts["small"], "AVAILABLE FUNDS", UI_MUTED, (cash.centerx, cash.y + 16))
        draw_centered_text(surface, fonts["body"], f"${int(context.player.money):,}", UI_HOPE, (cash.centerx, cash.y + 45))

        draw_section_label(surface, fonts["small"], "FRAGMENT PORTFOLIO", (54, 134))
        effect_text = {
            "Hope": "Movement speed bonus",
            "Dream": "Shield and faster fire rate",
            "Fear": "Earn now, but enemies grow stronger",
        }
        colors = {"Hope": UI_HOPE, "Dream": UI_DREAM, "Fear": UI_FEAR}
        for idx, stock_name in enumerate(self.stock_names):
            data = context.market.stocks[stock_name]
            selected = idx == self.selected
            accent = colors[stock_name]
            card = pygame.Rect(48, 174 + idx * 128, 585, 108)
            draw_panel(surface, card, border=accent if selected else (55, 75, 112), fill=(31, 48, 79) if selected else UI_PANEL, radius=14)
            icon = pygame.Rect(card.x + 18, card.y + 23, 62, 62)
            pygame.draw.rect(surface, accent, icon, border_radius=13)
            draw_centered_text(surface, fonts["body"], stock_name[0], UI_BG, icon.center)
            name = fonts["body"].render(stock_name.upper(), True, UI_TEXT)
            surface.blit(name, (card.x + 98, card.y + 18))
            #detail = fonts["small"].render(effect_text[stock_name], True, UI_MUTED)
            #surface.blit(detail, (card.x + 98, card.y + 52))
            price = fonts["body"].render(f"${data['price']:,.0f}", True, accent)
            surface.blit(price, (card.right - price.get_width() - 24, card.y + 18))
            owned = fonts["small"].render(
                f"OWNED  {context.player.fragments.get(stock_name, 0)} / {context.player.FRAGMENT_CAP}", True, UI_TEXT
            )
            surface.blit(owned, (card.right - owned.get_width() - 24, card.y + 57))

        draw_price_chart(surface, context, pygame.Rect(668, 134, 552, 458))
        draw_panel(surface, pygame.Rect(48, 584, 1172, 90), border=(55, 75, 112), fill=(14, 23, 40), radius=14)
        draw_section_label(surface, fonts["small"], "TRADE CONTROLS", (72, 600))
        draw_centered_text(surface, fonts["small"], "W / S  SELECT     B  BUY     F  SELL     ESC / TAB / Q  RETURN", UI_TEXT, (634, 645))


class NewsScene(Scene):
    """A modal news screen; combat is paused because its scene is inactive."""

    name = "NEWS"

    def enter(self, **kwargs) -> None:
        _ = kwargs
        self.news_kind = self.manager.context.level_manager.current_level.news_request or "covid"

    def handle_event(self, event) -> None:
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_ESCAPE):
            if self.news_kind in ("ai_adoption", "ai_revolt"):
                self.manager.context.level_manager.current_level.dismiss_news(self.news_kind)
            self.manager.change_scene(self.manager.last_combat_scene, resume=True)

    def draw(self, surface) -> None:
        context = self.manager.context
        fonts = context.fonts
        draw_screen_background(surface, UI_FEAR)
        stories = {
            "covid": (
                "The continued spread of COVID-19",
                "may lead to severe disaster in many region",
                "Fear fragments are spreading. Fear price begins a sustained rise.",
            ),
            "ai_adoption": (
                "With the widespread adoption of AI,",
                "we now have machine assistants for everyone. Please make good use of them.",
                "Dream price begins a long rise. Fear price begins a long decline.",
            ),
            "ai_revolt": (
                "AI systems have developed self-awareness",
                "and begun attacking humans.",
                "Dream is falling. Fear is rising.",
            ),
        }
        story = stories[self.news_kind]
        card = pygame.Rect(65, 135, 1150, 456)
        draw_panel(surface, card, border=UI_FEAR, fill=(47, 22, 42), radius=22)
        draw_centered_text(surface, fonts["small"], "BREAKING NEWS  //  MARKET ALERT", UI_FEAR, (card.centerx, card.y + 43))
        draw_centered_text(surface, fonts["title"], "HEADLINE", UI_TEXT, (card.centerx, card.y + 106))
        story_top = card.y + 158
        story_top += draw_centered_wrapped_text(surface, fonts["body"], story[0], UI_GOLD, card.centerx, story_top, card.width - 72) + 12
        story_top += draw_centered_wrapped_text(surface, fonts["body"], story[1], UI_GOLD, card.centerx, story_top, card.width - 72) + 18
        divider_y = story_top
        pygame.draw.line(surface, UI_BORDER, (card.x + 80, divider_y), (card.right - 80, divider_y), 1)
        draw_centered_wrapped_text(surface, fonts["body"], story[2], UI_TEXT, card.centerx, divider_y + 22, card.width - 72)
        draw_centered_text(surface, fonts["small"], "ENTER / SPACE / ESC  •  RETURN TO COMBAT", UI_MUTED, (card.centerx, card.bottom - 39))

class PenaltyScene(Scene):
    name = "PENALTY"
    def enter(self, **kwargs): self.selected=0
    def handle_event(self,event):
        if event.type!=pygame.KEYDOWN:return
        level=self.manager.context.level_manager.current_level
        if level.reward_message:
            if event.key in (pygame.K_RETURN,pygame.K_ESCAPE): level.reward_message=""; self.manager.change_scene("LEVEL",resume=True)
            return
        if level.pending_event:
            if event.key in (pygame.K_y,pygame.K_RETURN): level.resolve_reward(self.manager.context.player,accept=True)
            elif event.key in (pygame.K_n,pygame.K_ESCAPE): level.resolve_reward(self.manager.context.player,accept=False)
        else:
            if event.key in (pygame.K_UP, pygame.K_w):self.selected=max(0,self.selected-1)
            elif event.key in (pygame.K_DOWN, pygame.K_s):self.selected=min(2,self.selected+1)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE): level.resolve_reward(self.manager.context.player,self.selected)
    def draw(self,surface):
        f=self.manager.context.fonts; level=self.manager.context.level_manager.current_level
        draw_screen_background(surface, UI_HOPE)
        card = pygame.Rect(238, 150, 804, 430)
        draw_panel(surface, card, border=UI_GOLD, fill=(24, 51, 56), radius=22)
        draw_centered_text(surface, f['small'], 'WORLD CUP  //  BONUS EVENT', UI_HOPE, (card.centerx, card.y + 40))
        draw_centered_text(surface, f['title'], 'PENALTY SHOOTOUT', UI_GOLD, (card.centerx, card.y + 94))
        if level.reward_message:
            draw_centered_text(surface, f['title'], level.reward_message, UI_GOLD, (card.centerx, card.y + 192))
            draw_centered_text(surface, f['small'], 'PRESS ENTER TO CONTINUE', UI_MUTED, (card.centerx, card.y + 265))
            return
        if level.pending_event:
            c,h,fr=level.pending_event
            draw_centered_text(surface, f['body'], 'RANDOM EVENT', UI_TEXT, (card.centerx, card.y + 165))
            draw_centered_text(surface, f['body'], f'{c}%  HOPE +{h}       {100-c}%  FEAR +{fr}', UI_TEXT, (card.centerx, card.y + 213))
            draw_centered_text(surface, f['small'], 'Y / ENTER  ACCEPT       N / ESC  DECLINE', UI_GOLD, (card.centerx, card.y + 285))
        else:
            for i,t in enumerate(('Hope +3','Dream +3','Fear -3')):
                selected = i == self.selected
                choice = pygame.Rect(card.x + 172, card.y + 145 + i * 64, 460, 50)
                draw_panel(surface, choice, border=UI_GOLD if selected else (55, 75, 112), fill=(51, 57, 48) if selected else UI_PANEL, radius=10)
                draw_centered_text(surface, f['body'], t, UI_GOLD if selected else UI_TEXT, choice.center)
            draw_centered_text(surface, f['small'], 'UP / DOWN  SELECT       ENTER  CONFIRM', UI_MUTED, (card.centerx, card.y + 365))

class FeeNoticeScene(Scene):
    name = "FEE_NOTICE"
    def handle_event(self,event):
        if event.type==pygame.KEYDOWN and event.key in (pygame.K_RETURN,pygame.K_ESCAPE): self.manager.change_scene("MARKET")
    def draw(self,surface):
        draw_screen_background(surface, UI_GOLD); f=self.manager.context.fonts
        card = pygame.Rect(300, 230, 680, 260)
        draw_panel(surface, card, border=UI_GOLD, fill=(49, 40, 25), radius=20)
        draw_centered_text(surface, f['title'], 'TRADING NOTICE', UI_GOLD, (card.centerx, card.y + 62))
        draw_centered_text(surface, f['body'], "You're too fond of stock trading.", UI_TEXT, (card.centerx, card.y + 124))
        draw_centered_text(surface, f['body'], "A 5% transaction fee now applies.", UI_TEXT, (card.centerx, card.y + 161))
        draw_centered_text(surface, f['small'], 'PRESS ENTER TO CONTINUE', UI_MUTED, (card.centerx, card.y + 215))


class TransactionLimitScene(Scene):
    name = "TRANSACTION_LIMIT"

    def handle_event(self, event) -> None:
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_ESCAPE):
            self.manager.change_scene("MARKET")

    def draw(self, surface) -> None:
        draw_screen_background(surface, UI_FEAR)
        fonts = self.manager.context.fonts
        card = pygame.Rect(300, 245, 680, 230)
        draw_panel(surface, card, border=UI_FEAR, fill=(50, 25, 38), radius=20)
        draw_centered_text(surface, fonts["title"], "LIMIT REACHED", UI_FEAR, (card.centerx, card.y + 64))
        draw_centered_text(surface, fonts["body"], "You have reached your transaction limit.", UI_TEXT, (card.centerx, card.y + 122))
        draw_centered_text(surface, fonts["small"], "PRESS ENTER TO RETURN TO THE MARKET", UI_MUTED, (card.centerx, card.y + 175))


class FragmentLimitScene(Scene):
    name = "FRAGMENT_LIMIT"

    def enter(self, **kwargs) -> None:
        self.fragment_name = kwargs.get("fragment_name", "this")

    def handle_event(self, event) -> None:
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_ESCAPE, pygame.K_SPACE):
            self.manager.change_scene("MARKET")

    def draw(self, surface) -> None:
        draw_screen_background(surface, UI_GOLD)
        fonts = self.manager.context.fonts
        card = pygame.Rect(300, 245, 680, 230)
        draw_panel(surface, card, border=UI_GOLD, fill=(50, 40, 25), radius=20)
        draw_centered_text(surface, fonts["title"], "FRAGMENT CAP REACHED", UI_GOLD, (card.centerx, card.y + 64))
        draw_centered_text(surface, fonts["body"], f"You already own 30 {self.fragment_name} fragments.", UI_TEXT, (card.centerx, card.y + 122))
        draw_centered_text(surface, fonts["small"], "SELL SOME FIRST, THEN TRY AGAIN", UI_MUTED, (card.centerx, card.y + 175))


class GameOverScene(Scene):
    name = "GAME_OVER"

    def handle_event(self, event) -> None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
            player = self.manager.context.player
            player.reset_for_new_run()
            self.manager.context.market.reset()
            self.manager.change_scene("MENU")

    def draw(self, surface) -> None:
        fonts = self.manager.context.fonts
        draw_screen_background(surface, UI_FEAR)
        card = pygame.Rect(310, 240, 660, 240)
        draw_panel(surface, card, border=UI_FEAR, fill=(48, 20, 33), radius=22)
        draw_centered_text(surface, fonts["title"], "GAME OVER", UI_FEAR, (card.centerx, card.y + 78))
        draw_centered_text(surface, fonts["body"], "Your remaining capital has reached zero.", UI_TEXT, (card.centerx, card.y + 135))
        draw_centered_text(surface, fonts["small"], "PRESS ENTER TO RETURN TO MENU", UI_MUTED, (card.centerx, card.y + 190))


class EndingScene(Scene):
    name = "ENDING"

    def handle_event(self, event) -> None:
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_ESCAPE, pygame.K_SPACE):
            context = self.manager.context
            context.ending_manager.clear()
            context.player.reset_for_new_run()
            context.market.reset()
            self.manager.change_scene("MENU")

    def draw(self, surface) -> None:
        context = self.manager.context
        draw_screen_background(surface, UI_DREAM)
        card = pygame.Rect(190, 210, 900, 300)
        accent = UI_FEAR if context.ending_manager.outcome == "ai_victory" else UI_DREAM
        fill = (49, 21, 36) if context.ending_manager.outcome == "ai_victory" else (21, 37, 67)
        draw_panel(surface, card, border=accent, fill=fill, radius=22)
        if context.ending_manager.outcome == "ai_victory":
            title_text, subtitle_text = "AI VICTORY", "You have become a servant of AI."
        else:
            title_text, subtitle_text = "MEMORY CRASH COMPLETE", "The Dream Assistant returned to blue."
        draw_centered_text(surface, context.fonts["small"], "FINAL MARKET REPORT", accent, (card.centerx, card.y + 48))
        draw_centered_text(surface, context.fonts["title"], title_text, accent, (card.centerx, card.y + 120))
        draw_centered_text(surface, context.fonts["body"], subtitle_text, UI_TEXT, (card.centerx, card.y + 183))
        draw_centered_text(surface, context.fonts["small"], "ENTER / SPACE / ESC  •  RETURN TO MENU", UI_MUTED, (card.centerx, card.y + 244))


def draw_hud(surface, context: GameContext) -> None:
    fonts = context.fonts
    player = context.player
    level = context.level_manager.current_level
    # Keep combat information readable while letting the arena remain visible.
    hud_surface = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    left = pygame.Rect(16, 14, 286, 154)
    draw_panel(hud_surface, left, border=(64, 92, 144), fill=(13, 24, 43), radius=12)
    title = fonts["small"].render(f"LEVEL {level.index}  //  {level.name.split('-')[-1].strip().upper()}", True, UI_ACCENT)
    hud_surface.blit(title, (left.x + 14, left.y + 12))
    money = fonts["body"].render(f"${int(player.money):,}", True, UI_TEXT)
    hud_surface.blit(money, (left.x + 14, left.y + 38))
    assets = (("HOPE", player.fragments["Hope"], UI_HOPE), ("DREAM", player.fragments["Dream"], UI_DREAM), ("FEAR", player.fragments["Fear"], UI_FEAR))
    for index, (name, amount, color) in enumerate(assets):
        x = left.x + 16 + index * 88
        pygame.draw.circle(hud_surface, color, (x + 6, left.y + 94), 5)
        text = fonts["small"].render(f"{name[0]} {amount}", True, UI_TEXT)
        hud_surface.blit(text, (x + 16, left.y + 84))
    if level.world_cup:
        footballs = player.fragments["Hope"] + player.fragments["Dream"]
        text = fonts["small"].render(f"FOOTBALLS AVAILABLE  {footballs}", True, UI_GOLD)
        hud_surface.blit(text, (left.x + 16, left.y + 119))
    elif level.is_dream_factory:
        text = fonts["small"].render(f"WAVE {level.wave_index} / 6", True, UI_GOLD)
        hud_surface.blit(text, (left.x + 16, left.y + 112))
    dash_hint = fonts["small"].render("SPACE  DASH  •  DREAM -> HOPE", True, UI_MUTED)
    hud_surface.blit(dash_hint, (left.x + 16, left.y + 132))

    right = pygame.Rect(SCREEN_WIDTH - 250, 14, 234, 113)
    draw_panel(hud_surface, right, border=(64, 92, 144), fill=(13, 24, 43), radius=12)
    label = fonts["small"].render("LIVE EXCHANGE", True, UI_MUTED)
    hud_surface.blit(label, (right.x + 14, right.y + 11))
    colors = {"Hope": UI_HOPE, "Dream": UI_DREAM, "Fear": UI_FEAR}
    for index, (stock_name, data) in enumerate(context.market.stocks.items()):
        y = right.y + 38 + index * 22
        pygame.draw.circle(hud_surface, colors[stock_name], (right.x + 18, y + 6), 4)
        name = fonts["small"].render(stock_name.upper(), True, UI_TEXT)
        price = fonts["small"].render(f"${data['price']:,.0f}", True, colors[stock_name])
        hud_surface.blit(name, (right.x + 30, y))
        hud_surface.blit(price, (right.right - price.get_width() - 13, y))
    hud_surface.set_alpha(165)
    surface.blit(hud_surface, (0, 0))


def draw_player_effects(surface, player: Player) -> None:
    """Render Hope flames and the bounded, yellow Dream shield."""
    if player.trail_intensity > 0:
        trail_surface = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        total = max(1, len(player.trail))
        for index, (x, y) in enumerate(player.trail):
            age = (index + 1) / total
            radius = int(3 + 9 * player.trail_intensity * age)
            alpha = int(35 + 170 * player.trail_intensity * age)
            pygame.draw.circle(trail_surface, (255, 105, 20, alpha), (int(x), int(y)), radius)
            pygame.draw.circle(trail_surface, (255, 225, 80, alpha), (int(x), int(y)), max(1, radius // 2))
        surface.blit(trail_surface, (0, 0))

    if player.dash_effects:
        dash_surface = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        for x, y, lifetime in player.dash_effects:
            alpha = int(255 * lifetime / 0.28)
            radius = int(10 + 18 * lifetime / 0.28)
            pygame.draw.circle(dash_surface, (125, 169, 255, alpha), (int(x), int(y)), radius)
            pygame.draw.circle(dash_surface, (238, 244, 255, alpha), (int(x), int(y)), max(3, radius // 3))
        surface.blit(dash_surface, (0, 0))

    if player.shield_max > 0:
        ratio = player.shield / player.shield_max if player.shield_max else 0.0
        width = max(1, min(8, int(1 + player.shield_max / 20)))
        color = (255, 220, 40) if ratio > 0.2 else (140, 115, 30)
        pygame.draw.circle(surface, color, (int(player.x), int(player.y)), player.radius + 6, width)

    if player.is_invulnerable:
        shield_surface = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        center = (int(player.x), int(player.y))
        pygame.draw.circle(shield_surface, (255, 255, 255, 65), center, player.radius + 11)
        pygame.draw.circle(shield_surface, (255, 255, 255, 230), center, player.radius + 11, 2)
        surface.blit(shield_surface, (0, 0))


def draw_rotating_football(surface, bullet) -> None:
    """Draw a high-contrast, spinning black-and-white football projectile."""
    center = (int(bullet.x), int(bullet.y))
    radius = bullet.radius
    rotation = math.radians(bullet.rotation)

    def pentagon(x: float, y: float, size: float, angle: float) -> list[tuple[int, int]]:
        return [
            (
                int(x + math.cos(angle + math.tau * index / 5 - math.pi / 2) * size),
                int(y + math.sin(angle + math.tau * index / 5 - math.pi / 2) * size),
            )
            for index in range(5)
        ]

    pygame.draw.circle(surface, (255, 255, 255), center, radius)
    pygame.draw.circle(surface, (18, 25, 38), center, radius, 2)
    pygame.draw.polygon(surface, (18, 25, 38), pentagon(*center, radius * 0.36, rotation))
    for index in range(5):
        angle = rotation + math.tau * index / 5
        patch_x = center[0] + math.cos(angle) * radius * 0.58
        patch_y = center[1] + math.sin(angle) * radius * 0.58
        pygame.draw.line(surface, (68, 76, 91), center, (int(patch_x), int(patch_y)), 1)
        pygame.draw.polygon(surface, (18, 25, 38), pentagon(patch_x, patch_y, radius * 0.20, rotation + angle))


def draw_money_health_bar(surface, player: Player) -> None:
    """Draw the player's money-backed health bar above their head."""
    width, height = 58, 8
    x = int(player.x - width / 2)
    y = int(player.y - player.radius - 16)
    pygame.draw.rect(surface, (8, 12, 22), (x - 2, y - 2, width + 4, height + 4), border_radius=4)
    pygame.draw.rect(surface, (75, 20, 28), (x, y, width, height), border_radius=3)
    fill_width = int(width * player.money_health_ratio)
    if fill_width:
        pygame.draw.rect(surface, (238, 75, 88), (x, y, fill_width, height), border_radius=3)
    pygame.draw.rect(surface, (255, 225, 225), (x, y, width, height), 1, border_radius=3)


def draw_price_chart(surface, context: GameContext, rect: pygame.Rect) -> None:
    """Plot the last five seconds of live fragment prices as OHLC candles."""
    draw_panel(surface, rect, border=UI_DREAM, fill=(15, 26, 49), radius=14)
    title = context.fonts["body"].render("LIVE PRICE HISTORY", True, UI_TEXT)
    subtitle = context.fonts["small"].render("LAST 5 SECONDS", True, UI_MUTED)
    surface.blit(title, (rect.x + 18, rect.y + 14))
    surface.blit(subtitle, (rect.right - subtitle.get_width() - 18, rect.y + 20))

    plot = pygame.Rect(rect.x + 54, rect.y + 70, rect.width - 76, rect.height - 120)
    pygame.draw.rect(surface, (21, 36, 64), plot, border_radius=6)
    for offset in range(1, 5):
        x = plot.x + plot.width * offset // 5
        pygame.draw.line(surface, (55, 68, 95), (x, plot.y), (x, plot.bottom), 1)
    for offset in range(1, 4):
        y = plot.y + plot.height * offset // 4
        pygame.draw.line(surface, (55, 68, 95), (plot.x, y), (plot.right, y), 1)

    names = ("Hope", "Dream", "Fear")
    series = {name: context.market.recent_history(name) for name in names}
    candles = context.market.recent_candles("Fear")
    values = [price for points in series.values() for _, price in points]
    low, high = (min(values), max(values)) if values else (0.0, 1.0)
    if high - low < 1:
        high = low + 1
    padding = (high - low) * 0.12
    low -= padding
    high += padding
    start = context.market.elapsed - 5.0
    legend_colors = {"Hope": (110, 255, 165), "Dream": (120, 175, 255), "Fear": (255, 75, 95)}
    candle_layer = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    candle_width = max(4, min(12, plot.width // 42))

    def price_to_y(price: float) -> int:
        return int(plot.bottom - (price - low) / (high - low) * plot.height)

    for index, name in enumerate(names):
        color = legend_colors[name]
        legend = context.fonts["small"].render(name, True, color)
        surface.blit(legend, (plot.x + index * 110, rect.bottom - 30))

        # Preserve the original per-fragment trend line beneath the candles.
        # It makes the long-term direction immediately legible while the OHLC
        # marks show the short-term volatility within each interval.
        coords = [
            (
                int(plot.x + max(0.0, min(1.0, (timestamp - start) / 5.0)) * plot.width),
                price_to_y(price),
            )
            for timestamp, price in series[name]
        ]
        if len(coords) >= 2:
            pygame.draw.aalines(surface, color, False, coords)
            pygame.draw.lines(surface, color, False, coords, 2)
        elif coords:
            pygame.draw.circle(surface, color, coords[0], 3)

        if name != "Fear":
            continue

        for timestamp, open_price, high_price, low_price, close_price in candles:
            x = int(plot.x + max(0.0, min(1.0, (timestamp - start + 0.25) / 5.0)) * plot.width)
            open_y, high_y = price_to_y(open_price), price_to_y(high_price)
            low_y, close_y = price_to_y(low_price), price_to_y(close_price)
            rising = close_price >= open_price
            color = (72, 235, 145, 135) if rising else (255, 82, 102, 135)
            edge = (125, 255, 190, 220) if rising else (255, 145, 155, 220)
            pygame.draw.line(candle_layer, edge, (x, high_y), (x, low_y), 2)
            body_top = min(open_y, close_y)
            body_height = max(3, abs(close_y - open_y))
            body = pygame.Rect(x - candle_width // 2, body_top, candle_width, body_height)
            pygame.draw.rect(candle_layer, color, body, border_radius=2)
            pygame.draw.rect(candle_layer, edge, body, 1, border_radius=2)

    surface.blit(candle_layer, (0, 0))

    top_label = context.fonts["small"].render(f"{high:,.0f}", True, (175, 185, 210))
    bottom_label = context.fonts["small"].render(f"{low:,.0f}", True, (175, 185, 210))
    surface.blit(top_label, (rect.x + 4, plot.y))
    surface.blit(bottom_label, (rect.x + 4, plot.bottom - bottom_label.get_height()))
