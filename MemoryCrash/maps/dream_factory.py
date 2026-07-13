"""Level 3 map setup."""


class DreamFactoryMap:
    name = "Dream Factory"
    background = (32, 40, 68)

    def draw(self, screen, pygame) -> None:
        screen.fill(self.background)
        pygame.draw.rect(screen, (85, 115, 210), (90, 260, 300, 170), 2)
        pygame.draw.rect(screen, (95, 130, 220), (430, 180, 350, 260), 2)
        pygame.draw.rect(screen, (120, 140, 230), (840, 210, 330, 220), 2)
