"""Player skill models."""

from dataclasses import dataclass


@dataclass
class Skill:
    name: str
    cooldown: float
    duration: float
    active: bool = False
    remaining: float = 0.0

    def activate(self) -> bool:
        if self.remaining <= 0:
            self.active = True
            self.remaining = self.duration
            return True
        return False

    def update(self, dt: float) -> None:
        if self.remaining > 0:
            self.remaining -= dt
            if self.remaining <= 0:
                self.active = False
                self.remaining = -self.cooldown
        elif self.remaining < 0:
            self.remaining = min(0, self.remaining + dt)
