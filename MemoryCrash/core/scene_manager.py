"""Scene management primitives."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class Scene(Protocol):
    name: str

    def enter(self) -> None:
        ...

    def exit(self) -> None:
        ...

    def handle_event(self, event) -> None:
        ...

    def update(self, dt: float) -> None:
        ...

    def draw(self, surface) -> None:
        ...


@dataclass
class SceneManager:
    current_scene: Scene | None = None

    def switch(self, scene: Scene) -> None:
        if self.current_scene:
            self.current_scene.exit()
        self.current_scene = scene
        self.current_scene.enter()

    def handle_event(self, event) -> None:
        if self.current_scene:
            self.current_scene.handle_event(event)

    def update(self, dt: float) -> None:
        if self.current_scene:
            self.current_scene.update(dt)

    def draw(self, surface) -> None:
        if self.current_scene:
            self.current_scene.draw(surface)
