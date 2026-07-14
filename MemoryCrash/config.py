"""Global configuration for Memory Crash."""

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60
TITLE = "Memory Crash"

PLAYER_BASE_HP = 100
PLAYER_BASE_DAMAGE = 10
PLAYER_BASE_SPEED = 220
PLAYER_START_MONEY = 20000
PLAYER_MONEY_HEALTH_MAX = 20000

SAVE_FILE = "savegame.json"

COLORS = {
    "bg": (14, 16, 24),
    "panel": (28, 32, 48),
    "accent": (93, 147, 255),
    "danger": (255, 94, 94),
    "text": (236, 240, 255),
    "muted": (160, 170, 210),
}

DEFAULT_STOCKS = {
    "Childhood": {"price": 100.0, "volatility": 0.06, "effect": "map_mood"},
    "Dream": {"price": 120.0, "volatility": 0.08, "effect": "atk_speed"},
    "Regret": {"price": 90.0, "volatility": 0.12, "effect": "enemy_power"},
    "Fear": {"price": 95.0, "volatility": 0.1, "effect": "boss_power"},
}
