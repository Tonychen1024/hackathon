"""Market interface renderer."""


class MarketUI:
    def draw(self, screen, fonts, market, selected_stock: str) -> None:
        title = fonts["title"].render("Memory Exchange Market", True, (236, 240, 255))
        screen.blit(title, (30, 20))
        y = 100
        for stock_name, stock in market.stocks.items():
            marker = ">" if stock_name == selected_stock else " "
            line = f"{marker} {stock_name:10} | Price: {stock.price:7.2f} | Effect: {stock.effect}"
            surface = fonts["body"].render(line, True, (220, 230, 255))
            screen.blit(surface, (36, y))
            y += 38

        help_text = fonts["small"].render("W/S select | B buy | F sell | ENTER continue", True, (170, 180, 210))
        screen.blit(help_text, (36, 620))
