"""Level 5 map setup."""


class ExchangeCoreMap:
    name = "Exchange Core"
    background = (24, 48, 62)

    def draw(self, screen, pygame) -> None:
        screen.fill(self.background)
        pygame.draw.circle(screen, (100, 180, 220), (640, 360), 170, 3)
        pygame.draw.circle(screen, (100, 180, 220), (640, 360), 85, 3)
        pygame.draw.rect(screen, (120, 220, 230), (560, 40, 160, 80), 2)
