"""Level 1 map setup."""


class MemoryCityMap:
    name = "Memory City"
    background = (30, 34, 52)

    def draw(self, screen, pygame) -> None:
        screen.fill(self.background)
        pygame.draw.rect(screen, (70, 80, 120), (80, 140, 250, 380), 2)
        pygame.draw.rect(screen, (90, 100, 150), (420, 90, 220, 420), 2)
        pygame.draw.rect(screen, (110, 120, 170), (750, 170, 280, 340), 2)
