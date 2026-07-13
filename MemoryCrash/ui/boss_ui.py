"""Boss warning and status renderer."""


class BossUI:
    def draw(self, screen, fonts, boss) -> None:
        title = fonts["title"].render("BOSS ENGAGEMENT", True, (255, 120, 120))
        screen.blit(title, (32, 20))

        status = fonts["body"].render(f"{boss.name} HP: {boss.hp:.0f}", True, (255, 200, 200))
        screen.blit(status, (36, 72))

        tip = fonts["small"].render("Press F to fire. SPACE triggers boss special.", True, (220, 180, 180))
        screen.blit(tip, (36, 110))
