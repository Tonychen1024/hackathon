"""Boss framework implementations."""

from enemy.enemy import Enemy


class Boss(Enemy):
    def move(self, dt: float) -> None:
        _ = dt

    def attack(self, target) -> None:
        target.take_damage(self.damage)

    def special_ability(self, target) -> str:
        raise NotImplementedError


class ForgottenCitizen(Boss):
    def __init__(self) -> None:
        super().__init__("The Forgotten Citizen", 220, 14, 60, "City Core Fragment")

    def special_ability(self, target) -> str:
        target.speed = max(120, target.speed - 30)
        return "Disable: Player partial abilities reduced."


class BrokenChildhood(Boss):
    def __init__(self) -> None:
        super().__init__("Broken Childhood", 260, 16, 65, "Memory Puppet")

    def special_ability(self, target) -> str:
        target.take_damage(12)
        return "Summon: Lost childhood memories attack player."


class DreamEater(Boss):
    def __init__(self) -> None:
        super().__init__("Dream Eater", 300, 18, 70, "Dream Kernel")

    def special_ability(self, target) -> str:
        target.damage = max(4, target.damage - 2)
        return "Debuff: Reduce all active player buffs."


class PastSelf(Boss):
    def __init__(self) -> None:
        super().__init__("The Past Self", 320, 20, 75, "Regret Token")

    def special_ability(self, target) -> str:
        target.take_damage(15)
        return "Reflection: Player confronts painful memories."


class ExchangeAI(Boss):
    def __init__(self) -> None:
        super().__init__("Exchange AI", 380, 23, 80, "Master Exchange Key")

    def special_ability(self, target) -> str:
        target.money = max(0, target.money - 100)
        return "Market Manipulation: Stocks, news, and player stats controlled."
