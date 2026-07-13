"""Prototype market system with buy/sell and timed price updates."""

from __future__ import annotations

import random


class Market:
    def __init__(self) -> None:
        self.stocks: dict[str, dict[str, int]] = {
            "Hope": {"price": 20},
            "Dream": {"price": 50},
            "Fear": {"price": 10},
        }
        self._price_timer = 0.0

    def update(self, dt: float) -> None:
        self._price_timer += dt
        if self._price_timer < 60.0:
            return

        self._price_timer = 0.0
        for data in self.stocks.values():
            data["price"] = max(1, min(500, data["price"] + random.randint(-5, 5)))

    def randomize_prices(self) -> None:
        """Give Level 1 a fresh, visible opening market fluctuation."""
        for data in self.stocks.values():
            data["price"] = max(1, min(500, data["price"] + random.randint(-12, 12)))

    def trigger_ai_jobs_news(self) -> None:
        """Apply the Level 1 news shock: fear rises, hope and dream crash."""
        self.stocks["Fear"]["price"] = min(500, int(self.stocks["Fear"]["price"] * 2.2))
        self.stocks["Dream"]["price"] = max(1, int(self.stocks["Dream"]["price"] * 0.45))
        self.stocks["Hope"]["price"] = max(1, int(self.stocks["Hope"]["price"] * 0.45))

    def sell_fragment(self, player, stock_name: str, amount: int = 1) -> bool:
        if stock_name not in self.stocks or amount <= 0:
            return False

        sold = player.sell_fragment(stock_name, amount)
        if sold <= 0:
            return False

        player.money += self.stocks[stock_name]["price"] * sold
        return True

    def effects(self, player) -> dict[str, float]:
        hope = player.fragments.get("Hope", 0)
        dream = player.fragments.get("Dream", 0)
        fear = player.fragments.get("Fear", 0)
        return {
            "hope_regen": min(6.0, 0.35 * hope),
            "dream_fire_scale": max(0.35, 1.0 - (0.06 * dream)),
            "fear_enemy_speed": min(2.0, 1.0 + (0.03 * fear)),
        }
