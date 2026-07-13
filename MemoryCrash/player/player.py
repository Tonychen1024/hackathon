"""Player entity and stats container."""

from __future__ import annotations

from dataclasses import dataclass, field

from config import (
    PLAYER_BASE_DAMAGE,
    PLAYER_BASE_HP,
    PLAYER_BASE_SPEED,
    PLAYER_START_MONEY,
)
from player.skill import Skill
from player.weapon import Weapon


@dataclass
class Player:
    hp: float = PLAYER_BASE_HP
    damage: float = PLAYER_BASE_DAMAGE
    speed: float = PLAYER_BASE_SPEED
    money: float = PLAYER_START_MONEY
    inventory: list[str] = field(default_factory=list)
    stocks: dict[str, int] = field(default_factory=dict)
    weapon: Weapon = field(default_factory=lambda: Weapon("Pulse Blaster", 10, 2.0, 320))
    skills: list[Skill] = field(default_factory=lambda: [Skill("Memory Dash", 8, 2.5)])

    def take_damage(self, value: float) -> None:
        self.hp = max(0, self.hp - value)

    def heal(self, value: float) -> None:
        self.hp = min(PLAYER_BASE_HP, self.hp + value)

    def add_item(self, item_name: str) -> None:
        self.inventory.append(item_name)

    def add_money(self, value: float) -> None:
        self.money += value

    def buy_stock(self, stock_name: str, amount: int) -> None:
        self.stocks[stock_name] = self.stocks.get(stock_name, 0) + amount

    def sell_stock(self, stock_name: str, amount: int) -> int:
        owned = self.stocks.get(stock_name, 0)
        sold = min(amount, owned)
        self.stocks[stock_name] = owned - sold
        return sold

    def apply_market_effect(self, effect_name: str, strength: float) -> None:
        if effect_name == "atk_speed":
            self.weapon.fire_rate = max(0.6, self.weapon.fire_rate - strength)
        if effect_name == "enemy_power":
            self.damage = max(2, self.damage - strength)
