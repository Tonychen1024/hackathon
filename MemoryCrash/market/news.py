"""Market news and event effects."""

from dataclasses import dataclass
from random import choice


@dataclass
class NewsEvent:
    title: str
    stock_name: str
    impact: float


DEFAULT_NEWS = [
    NewsEvent("Emotional data leak in downtown exchange.", "Childhood", -0.25),
    NewsEvent("AI creativity grants boost dream assets.", "Dream", 0.30),
    NewsEvent("Fear index suppressed by neural firewall.", "Fear", -0.18),
]


def pick_news() -> NewsEvent:
    return choice(DEFAULT_NEWS)
