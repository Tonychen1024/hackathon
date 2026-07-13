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
        self._chart_timer = 0.0
        self._fear_volatility_timer = 0.0
        self.elapsed = 0.0
        self.fear_shocked = False
        self.history: dict[str, list[tuple[float, float]]] = {
            name: [(0.0, data["price"])] for name, data in self.stocks.items()
        }

    def update(self, dt: float) -> None:
        self.elapsed += dt
        self._chart_timer += dt
        while self._chart_timer >= 0.1 - 1e-9:
            self._chart_timer -= 0.1
            if abs(self._chart_timer) < 1e-9:
                self._chart_timer = 0.0
            tick_time = self.elapsed - self._chart_timer

            for name in ("Hope", "Dream"):
                data = self.stocks[name]
                # Ten small steps create the former +/-3% per-second feel,
                # while making the graph update smoothly every 0.1 seconds.
                data["price"] = round(max(1.0, data["price"] * random.choice((0.997, 1.003))), 2)

            fear = self.stocks["Fear"]
            if not self.fear_shocked:
                fear["price"] = round(max(1.0, fear["price"] * random.choice((0.997, 1.003))), 2)
            elif fear["price"] < 30000:
                # Sustained, visible rise until Fear reaches the cap threshold.
                fear["price"] = round(fear["price"] * random.uniform(1.007, 1.012), 2)
            else:
                # Once Fear reaches $30,000, it becomes a once-per-second
                # high-volatility asset instead of rising forever.
                self._fear_volatility_timer += 0.1
                if self._fear_volatility_timer >= 1.0 - 1e-9:
                    self._fear_volatility_timer -= 1.0
                    if abs(self._fear_volatility_timer) < 1e-9:
                        self._fear_volatility_timer = 0.0
                    fear["price"] = round(fear["price"] * random.choice((0.90, 1.10)), 2)

            for name, data in self.stocks.items():
                self.history[name].append((tick_time, data["price"]))

        cutoff = self.elapsed - 5.0
        for name in self.history:
            self.history[name] = [point for point in self.history[name] if point[0] >= cutoff]

    def trigger_ai_jobs_news(self) -> None:
        """Start Fear's sustained upward trend after the Level 1 news."""
        self.fear_shocked = True

    def recent_history(self, stock_name: str, seconds: float = 5.0) -> list[tuple[float, float]]:
        return [point for point in self.history[stock_name] if point[0] >= self.elapsed - seconds]

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
            "fear_enemy_speed": min(2.0, 1.0 + (0.05 * fear)),
            "fear_enemy_damage": min(7.0, 1.0 + (0.50 * fear)),
            "fear_enemy_health": min(6.0, 1.0 + (0.40 * fear)),
            "fear_enemy_size": min(3.4, 1.0 + (0.18 * fear)),
        }
