"""Market service with buy/sell and random events."""

from __future__ import annotations

from random import random

from config import DEFAULT_STOCKS
from market.news import pick_news, NewsEvent
from market.stock import Stock


class Market:
    def __init__(self) -> None:
        self.stocks = {
            name: Stock(name=name, **values, history=[values["price"]])
            for name, values in DEFAULT_STOCKS.items()
        }
        self.last_news: NewsEvent | None = None

    def buy(self, player, stock_name: str, amount: int) -> bool:
        stock = self.stocks[stock_name]
        total = stock.price * amount
        if amount <= 0 or player.money < total:
            return False
        player.money -= total
        player.buy_stock(stock_name, amount)
        return True

    def sell(self, player, stock_name: str, amount: int) -> bool:
        stock = self.stocks[stock_name]
        sold = player.sell_stock(stock_name, amount)
        if sold <= 0:
            return False
        player.money += stock.price * sold
        return True

    def update_price(self) -> None:
        for stock in self.stocks.values():
            stock.update()

    def random_event(self) -> NewsEvent | None:
        if random() < 0.35:
            event = pick_news()
            if event.stock_name in self.stocks:
                self.stocks[event.stock_name].update(1 + abs(event.impact))
            self.last_news = event
            return event
        self.last_news = None
        return None

    def apply_gameplay_effects(self, player) -> dict[str, float]:
        effect_values: dict[str, float] = {}
        for stock in self.stocks.values():
            normalized = (stock.price - 100) / 100
            effect_values[stock.effect] = normalized
            player.apply_market_effect(stock.effect, abs(normalized))
        return effect_values
