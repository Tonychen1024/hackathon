"""Level base and level progression manager."""

from __future__ import annotations

from dataclasses import dataclass, field


class Level:
    name: str = "Level"

    def load(self) -> None:
        raise NotImplementedError

    def update(self, dt: float) -> None:
        raise NotImplementedError

    def draw(self, screen, pygame, fonts) -> None:
        raise NotImplementedError

    def complete(self) -> bool:
        raise NotImplementedError


@dataclass
class BaseLevel(Level):
    name: str
    chapter_text: str
    map_obj: object
    enemy_factory: list
    boss_factory: object
    timer_to_complete: float = 12.0
    elapsed: float = 0.0
    loaded: bool = False
    enemies: list = field(default_factory=list)

    def load(self) -> None:
        self.enemies = [factory() for factory in self.enemy_factory]
        self.elapsed = 0.0
        self.loaded = True

    def update(self, dt: float) -> None:
        if not self.loaded:
            self.load()
        self.elapsed += dt

    def draw(self, screen, pygame, fonts) -> None:
        if hasattr(self.map_obj, "draw"):
            self.map_obj.draw(screen, pygame)
        overlay = fonts["body"].render(f"{self.name} | {self.chapter_text}", True, (240, 245, 255))
        screen.blit(overlay, (28, 18))

    def complete(self) -> bool:
        return self.elapsed >= self.timer_to_complete

    def create_boss(self):
        return self.boss_factory()


class LevelManager:
    def __init__(self, levels: list[BaseLevel]) -> None:
        self.levels = levels
        self.current_index = 0

    @property
    def current_level(self) -> BaseLevel:
        return self.levels[self.current_index]

    def move_next(self) -> bool:
        if self.current_index + 1 < len(self.levels):
            self.current_index += 1
            self.current_level.load()
            return True
        return False

    def all_completed(self) -> bool:
        return self.current_index >= len(self.levels) - 1 and self.current_level.complete()
