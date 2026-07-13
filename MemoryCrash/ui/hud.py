"""Gameplay HUD widget."""


class HUD:
    def draw(self, screen, fonts, player, runtime_state) -> None:
        lines = [
            f"HP: {int(player.hp)}",
            f"DMG: {player.damage:.1f}",
            f"SPD: {player.speed:.1f}",
            f"$ {player.money:.0f}",
            f"Score: {runtime_state.score}",
            f"Level: {runtime_state.current_level_index + 1}",
        ]
        for i, text in enumerate(lines):
            surface = fonts["body"].render(text, True, (236, 240, 255))
            screen.blit(surface, (18, 58 + i * 24))
