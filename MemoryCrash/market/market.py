"""Fragment market with live, event-driven prices."""

from __future__ import annotations

import random


class Market:
    def __init__(self) -> None:
        self.stocks: dict[str, dict[str, float]] = {
            "Hope": {"price": 1000.0},
            "Dream": {"price": 1000.0},
            "Fear": {"price": 1000.0},
        }
        self._price_timer = 0.0
        self.fear_shocked = False

    def update(self, dt: float) -> None:
        self._price_timer += dt
        while self._price_timer >= 1.0:
            self._price_timer -= 1.0
            for name, data in self.stocks.items():
                change = 0.10 if name == "Fear" and self.fear_shocked else 0.03
                data["price"] = round(max(1.0, data["price"] * random.choice((1 - change, 1 + change))), 2)

    def trigger_ai_jobs_news(self) -> None:
        """Apply the Level 1 news shock and make Fear permanently volatile."""
        self.stocks["Fear"]["price"] = round(self.stocks["Fear"]["price"] * 10, 2)
        self.fear_shocked = True

    def buy_fragment(self, player, stock_name: str, amount: int = 1) -> bool:
        if stock_name not in self.stocks or amount <= 0:
            return False

        total = self.stocks[stock_name]["price"] * amount
        if stock_name == "Fear":
            player.money += total
            player.fragments[stock_name] += amount
            return True
        if player.money < total:
            return False

        player.money -= total
        player.fragments[stock_name] += amount
        return True

    def sell_fragment(self, player, stock_name: str, amount: int = 1) -> bool:
        if stock_name not in self.stocks or amount <= 0:
            return False

        total = self.stocks[stock_name]["price"] * amount
        if stock_name == "Fear":
            if player.fragments.get(stock_name, 0) < amount or player.money < total:
                return False
            player.sell_fragment(stock_name, amount)
            player.money -= total
            return True

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
            "dream_shield": min(120.0, dream * 15.0),
            "hope_speed_bonus": min(180.0, hope * 18.0),
            "dream_fire_scale": max(0.35, 1.0 - (0.06 * dream)),
            "fear_enemy_speed": min(2.5, 1.0 + (0.08 * fear)),
            "fear_enemy_damage": min(3.0, 1.0 + (0.12 * fear)),
            "fear_enemy_size": min(2.2, 1.0 + (0.07 * fear)),
        }
