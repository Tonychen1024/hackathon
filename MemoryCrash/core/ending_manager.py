"""State for Dream Factory's two distinct ending outcomes."""

from __future__ import annotations


class EndingManager:
    def __init__(self) -> None:
        self.outcome: str | None = None

    def start_ai_apology(self) -> None:
        self.outcome = "ai_apology"

    def start_ai_victory(self) -> None:
        self.outcome = "ai_victory"

    def clear(self) -> None:
        self.outcome = None
