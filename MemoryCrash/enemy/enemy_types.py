"""Normal enemy implementations."""

from enemy.enemy import Enemy


class BasicEnemy(Enemy):
    def move(self, dt: float) -> None:
        _ = dt

    def attack(self, target) -> None:
        target.take_damage(self.damage)


class MemoryBug(BasicEnemy):
    def __init__(self) -> None:
        super().__init__("Memory Bug", 20, 5, 110, "Childhood Fragment")


class FearVirus(BasicEnemy):
    def __init__(self) -> None:
        super().__init__("Fear Virus", 28, 7, 100, "Hope Fragment")


class LostToy(BasicEnemy):
    def __init__(self) -> None:
        super().__init__("Lost Toy", 25, 6, 115, "Childhood Fragment")


class ChildhoodVirus(BasicEnemy):
    def __init__(self) -> None:
        super().__init__("Childhood Virus", 30, 8, 105, "Hope Fragment")


class DreamCollector(BasicEnemy):
    def __init__(self) -> None:
        super().__init__("Dream Collector", 32, 9, 120, "Dream Shard")


class AIWorker(BasicEnemy):
    def __init__(self) -> None:
        super().__init__("AI Worker", 36, 10, 95, "Dream Shard")


class MarketVirus(BasicEnemy):
    def __init__(self) -> None:
        super().__init__("Market Virus", 40, 11, 130, "Core Data")
