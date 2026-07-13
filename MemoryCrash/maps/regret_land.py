"""Level 4 map setup."""


class RegretLandMap:
    name = "Regret Land"
    background = (54, 34, 40)

    def draw(self, screen, pygame) -> None:
        screen.fill(self.background)
        pygame.draw.line(screen, (180, 90, 90), (100, 100), (1180, 620), 3)
        pygame.draw.line(screen, (150, 70, 70), (120, 620), (1160, 120), 3)
        pygame.draw.rect(screen, (120, 80, 80), (520, 250, 200, 160), 2)
