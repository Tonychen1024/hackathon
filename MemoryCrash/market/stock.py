"""Stock model used by market simulation."""

from dataclasses import dataclass, field
from random import uniform


@dataclass
class Stock:
    name: str
    price: float
    history: list[float] = field(default_factory=list)
    volatility: float = 0.05
    effect: str = ""

    def update(self, multiplier: float = 1.0) -> float:
        delta_ratio = uniform(-self.volatility, self.volatility) * multiplier
        self.price = max(1.0, self.price * (1.0 + delta_ratio))
        self.history.append(round(self.price, 2))
        return self.price
