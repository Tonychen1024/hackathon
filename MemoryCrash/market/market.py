"""Fragment market with live, event-driven prices."""

from __future__ import annotations

import random


LEVEL1_TRANSACTION_LIMIT = 100
AI_ADOPTION_DREAM_CAP = 5000.0
AI_ADOPTION_FEAR_FLOOR = 500.0
AI_REVOLT_DREAM_FLOOR = 500.0
AI_REVOLT_FEAR_CAP = 5000.0


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
        self.ai_market_state: str | None = None
        self.level_mode = "level1"
        self.level2_timer = 0.0
        self.level2_starts = None
        self.level2_targets = None
        self.level2_fee_notice_shown = False
        self.level1_transaction_count = 0
        self.reached_high_point1 = False
        self.reached_high_point2 = False
        self.reached_low_point = False
        self.time_counter = 0
        self.climb = False
        self.history: dict[str, list[tuple[float, float]]] = {
            name: [(0.0, data["price"])] for name, data in self.stocks.items()
        }

    def update(self, dt: float) -> None:
        if self.level_mode == "level2":
            self.elapsed += dt; self.level2_timer += dt; self._chart_timer += dt
            if self.level2_starts is None:
                self.level2_starts={n:self.stocks[n]['price'] for n in self.stocks}
                self.level2_targets={"Hope":self.level2_starts['Hope']*random.uniform(1.01,1.03),"Dream":self.level2_starts['Dream']*random.uniform(.95,1.08),"Fear":self.level2_starts['Fear']*random.uniform(.97,.99)}
            if self.level2_timer >= 10:
                self.level2_timer -= 10; self.level2_starts={n:self.stocks[n]['price'] for n in self.stocks}
                self.level2_targets={"Hope":self.level2_starts['Hope']*random.uniform(1.01,1.03),"Dream":self.level2_starts['Dream']*random.uniform(.95,1.08),"Fear":self.level2_starts['Fear']*random.uniform(.97,.99)}
            progress=min(1.0,self.level2_timer/10)
            for n in self.stocks: self.stocks[n]['price']=round(self.level2_starts[n]+(self.level2_targets[n]-self.level2_starts[n])*progress,2)
            while self._chart_timer >= .1-1e-9:
                self._chart_timer-=.1
                for n in self.stocks:self.history[n].append((self.elapsed-self._chart_timer,self.stocks[n]['price']))
            cutoff=self.elapsed-5
            for n in self.history:self.history[n]=[p for p in self.history[n] if p[0]>=cutoff]
            return
        self.elapsed += dt
        self._chart_timer += dt
        while self._chart_timer >= 0.1 - 1e-9:
            self._chart_timer -= 0.1
            if abs(self._chart_timer) < 1e-9:
                self._chart_timer = 0.0
            tick_time = self.elapsed - self._chart_timer

            for name in ("Hope", "Dream"):
                data = self.stocks[name]
                if (
                    name == "Dream"
                    and (
                        self.ai_market_state == "adoption" and data["price"] >= AI_ADOPTION_DREAM_CAP
                        or self.ai_market_state == "revolt" and data["price"] <= AI_REVOLT_DREAM_FLOOR
                    )
                ):
                    continue
                # Ten small steps create the former +/-3% per-second feel,
                # while making the graph update smoothly every 0.1 seconds.
                data["price"] = round(max(1.0, data["price"] * random.choice((0.997, 1.003))), 2)

            if self.ai_market_state == "adoption":
                # The first Dream Factory news is a lasting market trend.
                self.stocks["Dream"]["price"] = round(min(AI_ADOPTION_DREAM_CAP, self.stocks["Dream"]["price"] * random.uniform(0.991, 1.0252)), 2)
            elif self.ai_market_state == "revolt":
                # After the betrayal, the two AI-sensitive assets reverse.
                self.stocks["Dream"]["price"] = round(max(AI_REVOLT_DREAM_FLOOR, self.stocks["Dream"]["price"] * random.uniform(0.968, 1.01)), 2)

            fear = self.stocks["Fear"]
            if self.ai_market_state == "adoption":
                fear["price"] = round(max(AI_ADOPTION_FEAR_FLOOR, fear["price"] * random.uniform(0.968, 1.01)), 2)
            elif self.ai_market_state == "revolt":
                fear["price"] = round(min(AI_REVOLT_FEAR_CAP, fear["price"] * random.uniform(0.991, 1.0252)), 2)
            elif not self.fear_shocked:
                fear["price"] = round(max(500.0, fear["price"] * random.choice((0.997, 1.003))), 2)
            elif fear["price"] < 5000 and not self.reached_high_point1:
                # Sustained, visible rise until Fear reaches the cap threshold.
                fear["price"] = round(fear["price"] * random.uniform(0.99, 1.052), 2)
            else:
                # Once Fear reaches $5,000, it becomes a once-per-second
                # high-volatility asset instead of rising forever.
                self.reached_high_point1 = True
                self._fear_volatility_timer += 0.1
                if self._fear_volatility_timer >= 0.1 - 1e-9:
                    self._fear_volatility_timer -= 0.1
                    self.time_counter += 1
                    if abs(self._fear_volatility_timer) < 1e-9:
                        self._fear_volatility_timer = 0.0
                    if fear["price"] > 7000:
                        self.climb = False
                    elif fear["price"] < 3000:    
                        self.climb = True
                    if self.climb:
                        fear["price"] = round(fear["price"] * (1.1 if random.randint(0, 1) == 1 else 0.99), 2)
                    else:
                        fear["price"] = round(fear["price"] * (0.91 if random.randint(0, 1) == 1 else 1.01), 2)
            for name, data in self.stocks.items():
                self.history[name].append((tick_time, data["price"]))

        cutoff = self.elapsed - 5.0
        for name in self.history:
            self.history[name] = [point for point in self.history[name] if point[0] >= cutoff]

    def trigger_ai_jobs_news(self) -> None:
        """Start Fear's sustained upward trend after the Level 1 news."""
        self.fear_shocked = True

    def trigger_ai_adoption(self) -> None:
        """Begin Dream's long rise and Fear's long decline in Level 3."""
        self.ai_market_state = "adoption"

    def trigger_ai_revolt(self) -> None:
        """Reverse the Dream Factory market trend after the AI betrayal."""
        self.ai_market_state = "revolt"

    def reset(self) -> None:
        """Restore opening prices, chart data, and event state for a new run."""
        self.__init__()

    @property
    def level1_transaction_limit_reached(self) -> bool:
        return (
            self.level_mode == "level1"
            and self.level1_transaction_count >= LEVEL1_TRANSACTION_LIMIT
        )

    def record_transaction(self) -> None:
        if self.level_mode == "level1":
            self.level1_transaction_count += 1

    def recent_history(self, stock_name: str, seconds: float = 5.0) -> list[tuple[float, float]]:
        return [point for point in self.history[stock_name] if point[0] >= self.elapsed - seconds]

    def recent_candles(
        self, stock_name: str, seconds: float = 5.0, interval: float = 0.5
    ) -> list[tuple[float, float, float, float, float]]:
        """Aggregate recent ticks into standard open/high/low/close candles."""
        points = self.recent_history(stock_name, seconds)
        if not points:
            return []

        start = self.elapsed - seconds
        buckets: dict[int, list[float]] = {}
        for timestamp, price in points:
            bucket = max(0, min(int(seconds / interval) - 1, int((timestamp - start) / interval)))
            buckets.setdefault(bucket, []).append(price)

        candles: list[tuple[float, float, float, float, float]] = []
        previous_close = points[0][1]
        for bucket in range(int(seconds / interval)):
            prices = buckets.get(bucket)
            if prices:
                open_price = previous_close
                close_price = prices[-1]
                candles.append((start + bucket * interval, open_price, max(prices + [open_price]), min(prices + [open_price]), close_price))
                previous_close = close_price
        return candles

    def buy_fragment(self, player, stock_name: str, amount: int = 1) -> bool:
        if (
            stock_name not in self.stocks
            or amount <= 0
            or self.level1_transaction_limit_reached
            or player.fragments.get(stock_name, 0) + amount > player.FRAGMENT_CAP
        ):
            return False

        total = self.stocks[stock_name]["price"] * amount
        fee = 1.05 if self.level_mode == "level2" else 1.0
        if stock_name == "Fear":
            player.money += total / fee
            player.add_fragment(stock_name, amount)
            self.record_transaction()
            return True
        if player.money < total * fee:
            return False

        player.money -= total * fee
        player.add_fragment(stock_name, amount)
        self.record_transaction()
        return True

    def sell_fragment(self, player, stock_name: str, amount: int = 1) -> bool:
        if (
            stock_name not in self.stocks
            or amount <= 0
            or self.level1_transaction_limit_reached
        ):
            return False

        total = self.stocks[stock_name]["price"] * amount
        fee = 1.05 if self.level_mode == "level2" else 1.0
        if stock_name == "Fear":
            if player.fragments.get(stock_name, 0) < amount or player.money < total * fee:
                return False
            player.sell_fragment(stock_name, amount)
            player.money -= total * fee
            self.record_transaction()
            return True

        sold = player.sell_fragment(stock_name, amount)
        if sold <= 0:
            return False
        player.money += self.stocks[stock_name]["price"] * sold / fee
        self.record_transaction()
        return True

    def effects(self, player) -> dict[str, float]:
        hope = player.fragments.get("Hope", 0)
        dream = player.fragments.get("Dream", 0)
        fear = player.fragments.get("Fear", 0)
        # Enemy hits always take money.  The first two Fear fragments share
        # the $1,500 tier; from three onward each fragment adds another $500.
        fear_money_damage = (
            1000.0 if fear == 0 else 1500.0 if fear <= 2 else 2000.0 + (fear - 3) * 500.0
        )
        return {
            "dream_shield": min(120.0, dream * 15.0),
            "hope_speed_bonus": min(180.0, hope * 18.0),
            "dream_fire_scale": max(0.35, 1.0 - (0.06 * dream)),
            # A hit's monetary loss follows the Fear-fragment tiers above.
            "fear_enemy_speed": 1.0 + (0.12 * fear),
            "fear_enemy_damage": fear_money_damage,
            "fear_enemy_health": 1.0 + (0.40 * fear),
            "fear_enemy_size": 1.0 + (0.18 * fear),
        }
