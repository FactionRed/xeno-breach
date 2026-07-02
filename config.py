"""Xeno Breach — global configuration constants."""
import numpy as np

# ---- Display ----
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60
TITLE = "XENO BREACH — Survival Shooter"

# ---- Terrain ----
TERRAIN_SIZE = 512          # grid resolution (cells per side)
TERRAIN_SCALE = 3           # screen pixels per grid cell
WORLD_W = TERRAIN_SIZE * TERRAIN_SCALE   # 1536 px
WORLD_H = TERRAIN_SIZE * TERRAIN_SCALE   # 1536 px

# Noise parameters (adapted from planet_generator.py)
NOISE_SCALE = 0.018         # spatial frequency — lower = broader features
OCTAVES = 5
PERSISTENCE = 0.50
LACUNARITY = 2.1
SEED_OFFSET = 1337.0        # z-coordinate for snoise3 — different per planet
HEIGHT_AMP = 0.14           # terrain height amplitude

# Craters
CRATER_COUNT = 30
CRATER_MAX_DEPTH = 0.18
CRATER_MIN_RADIUS = 12      # in grid cells
CRATER_MAX_RADIUS = 38

# ---- Player ----
PLAYER_SPEED = 200.0        # pixels per second
PLAYER_SPRINT_MULT = 1.7
PLAYER_RADIUS = 12          # pixels (on-screen)
MAX_SLOPE = 0.28            # gradient above this = impassable wall
SLOPE_SPEED_FALLOFF = 0.6   # higher = more speed loss on slopes

# ---- Lighting (top-down, light from upper-left) ----
LIGHT_DIR = np.array([0.45, -0.35, 0.82])
LIGHT_DIR = LIGHT_DIR / np.linalg.norm(LIGHT_DIR)
AMBIENT = 0.40               # minimum illumination (brighter for visibility)

# ---- Colors (from DESIGN.md tokens) ----
HULL_BLACK   = (10, 14, 18)     # colors.primary
DECK_PLATE   = (58, 70, 81)     # colors.secondary
ADRENALINE   = (200, 54, 47)    # colors.tertiary
BULKHEAD     = (18, 24, 32)     # colors.neutral
CONSOLE      = (28, 37, 48)     # colors.surface
ON_PRIMARY   = (232, 237, 242)  # colors.on-primary
ON_SECONDARY = (154, 166, 176)  # colors.on-secondary
DANGER       = (255, 65, 54)    # colors.danger
ACID         = (157, 255, 61)   # colors.acid
WARNING      = (255, 180, 84)  # colors.warning
BIO_MASS     = (91, 31, 46)    # colors.bio-mass
