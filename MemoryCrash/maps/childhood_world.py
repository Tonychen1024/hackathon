"""Level 2 map setup."""


class ChildhoodWorldMap:
    name = "Childhood World"

    def mood_color(self, childhood_price: float) -> tuple[int, int, int]:
        if childhood_price >= 100:
            return (95, 160, 120)
        return (78, 62, 98)

    def draw(self, screen, pygame, childhood_price: float) -> None:
        screen.fill(self.mood_color(childhood_price))
        pygame.draw.circle(screen, (180, 220, 120), (220, 220), 60, 2)
        pygame.draw.rect(screen, (220, 170, 120), (470, 300, 240, 150), 2)
        pygame.draw.rect(screen, (170, 200, 255), (900, 180, 200, 220), 2)
