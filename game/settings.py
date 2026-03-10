from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

BASE_SCREEN_WIDTH = 960
BASE_SCREEN_HEIGHT = 540
SCREEN_WIDTH = BASE_SCREEN_WIDTH
SCREEN_HEIGHT = BASE_SCREEN_HEIGHT
FPS = 60
TITLE = "Sky Courier"

SKY_TOP = (113, 201, 255)
SKY_BOTTOM = (232, 244, 255)
SKY_GLOW = (255, 241, 195)
MENU_GLOW = (255, 255, 255, 85)
CITY_FAR = (187, 198, 214)
CITY_MID = (149, 165, 186)
CITY_NEAR = (107, 125, 150)
CITY_WINDOW = (255, 233, 154)
GROUND = (47, 84, 61)
GROUND_LINE = (92, 158, 104)
TEXT = (23, 32, 42)
WHITE = (255, 255, 255)
SHADOW = (0, 0, 0, 60)
PANEL = (255, 255, 255, 220)
PANEL_STROKE = (225, 236, 245)
ACCENT = (255, 169, 56)
ACCENT_DARK = (214, 121, 29)
SUCCESS = (66, 136, 94)
LOCKED = (126, 140, 156)
BUTTON_SOFT = (244, 249, 255)
BUTTON_HOVER = (255, 214, 127)
BUTTON_GLOW = (255, 255, 255, 110)
CARD_HOVER = (255, 250, 238, 230)
HUD_PANEL = (23, 36, 53, 190)
HUD_STROKE = (130, 170, 207)
HUD_ACCENT = (255, 215, 112)
HUD_PAUSE = (29, 46, 67)
HUD_PAUSE_HOVER = (39, 60, 86)

PLAYER_START_X = 170
PLAYER_START_Y = 310
PLAYER_SIZE = (92, 40)
PLAYER_SPEED = 360
PLAYER_GRAVITY = 1200
PLAYER_FLAP_FORCE = 420

OBSTACLE_SPEED = 320
OBSTACLE_WIDTH = 42
OBSTACLE_GAP = 170
OBSTACLE_SPAWN_MS = 1350

CLOUD_SPEED = 55
COIN_SPEED = 320
COIN_RADIUS = 14
COIN_SPAWN_MS = 1800

GROUND_HEIGHT = 86
SAVE_FILE = PROJECT_ROOT / "save_data.json"

SKINS = [
    {
        "id": "classic",
        "name": "Classic",
        "cost": 0,
        "body": (255, 193, 61),
        "wing": (255, 230, 164),
        "beak": (255, 129, 61),
    },
    {
        "id": "mint",
        "name": "Mint",
        "cost": 25,
        "body": (105, 214, 182),
        "wing": (199, 255, 235),
        "beak": (255, 180, 77),
    },
    {
        "id": "coral",
        "name": "Coral",
        "cost": 50,
        "body": (255, 128, 114),
        "wing": (255, 205, 190),
        "beak": (255, 221, 87),
    },
    {
        "id": "night",
        "name": "Night",
        "cost": 90,
        "body": (87, 102, 173),
        "wing": (182, 193, 245),
        "beak": (255, 205, 84),
    },
    {
        "id": "royal",
        "name": "Royal",
        "cost": 140,
        "body": (147, 97, 255),
        "wing": (225, 211, 255),
        "beak": (255, 161, 76),
    },
]
