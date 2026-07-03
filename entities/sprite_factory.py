"""Procedural sprite factory — generates sprite sheets at runtime.

PLAYER SPRITES: 16×16 pixel art matching the template sprite sheet style:
  - Peach fill (#FFC090), dark brown outline (#4A2E18)
  - Chibi proportions: large head, blocky body, short limbs
  - 4-directional: front / right / back / left
  - Flat colors, no shading, no anti-aliasing
  - Scaled 2× to 32×32 for in-game visibility

XENOMORPH SPRITES: procedural dark segmented alien with glowing acid eyes.
"""
import math
import random
import sys
import pygame
import numpy as np

from config import (HULL_BLACK, ADRENALINE, DANGER, WARNING, ACID, BIO_MASS,
                    ON_PRIMARY, ON_SECONDARY, CONSOLE, BULKHEAD)

# ============ PLAYER PIXEL ART COLORS — Sci-Fi Military Marine ============
# Armor palette (dark tactical gunmetal + accents)
ARMOR     = (58, 64, 69)       # #3A4045 — primary armor plates (chest, helmet, shoulders)
ARMOR_LT  = (80, 88, 95)       # lighter armor (highlights, shoulder pads)
ARMOR_DK  = (35, 40, 44)       # darker armor (lower legs, boots)
UNDERSUIT = (22, 22, 26)       # #16161A — undersuit/joints (near-black)
VISOR     = (0, 217, 255)      # #00D9FF — cyan visor/tech glow
ACCENT    = (255, 107, 0)      # #FF6B00 — orange chest stripe/backpack light
SKIN      = (200, 168, 140)    # exposed skin (face under visor)
HURT_FILL = (255, 60, 60)      # red flash when hurt
WHITE     = (255, 255, 255)    # muzzle flash

# Color index:  '.' transparent, 'A' armor, 'a' armor_lt, 'd' armor_dk,
#                'U' undersuit, 'V' visor, 'X' accent, 'S' skin,
#                'O' outline, 'H' hurt, 'W' white
_C = {'.': None,
      'A': ARMOR, 'a': ARMOR_LT, 'd': ARMOR_DK,
      'U': UNDERSUIT, 'V': VISOR, 'X': ACCENT, 'S': SKIN,
      'O': (10, 10, 12),  # near-black outline
      'H': HURT_FILL, 'W': WHITE}

SPRITE_W = 16
SPRITE_H = 16
SCALE = 2  # for 16x16 sprites (legacy fallback)


def _pad16(s):
    """Pad/truncate a string to exactly 16 chars."""
    if len(s) < 16:
        s = s + '.' * (16 - len(s))
    return s[:16]


def _row16(s):
    """Convert a string to a 16-char list, padding if needed."""
    return list(_pad16(s))


def _validate(grid, name=""):
    """Assert every row is exactly 16 chars and there are exactly 16 rows."""
    assert len(grid) == 16, f"{name}: expected 16 rows, got {len(grid)}"
    for i, row in enumerate(grid):
        assert len(row) == 16, f"{name} row {i}: expected 16 chars, got {len(row)}: {row!r}"


def _grid_to_surface(grid):
    """Convert a 16-row string grid to a scaled pygame Surface."""
    w = len(grid[0])
    h = len(grid)
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    for y, row in enumerate(grid):
        for x, ch in enumerate(row):
            color = _C.get(ch)
            if color is not None:
                surf.set_at((x, y), color)
    return pygame.transform.scale(surf, (w * SCALE, h * SCALE))


def _mirror(grid):
    """Mirror a grid horizontally."""
    return [row[::-1] for row in grid]


def _recolor(grid, old, new):
    """Replace all instances of old char with new char."""
    return [row.replace(old, new) for row in grid]


def _set_char(grid_list, row, col, ch):
    """Set a single character in a list-of-lists grid."""
    grid_list[row][col] = ch


def _grid_to_str(grid_list):
    """Convert list-of-lists back to list of strings."""
    return [''.join(row) for row in grid_list]


# ================================================================
#  PLAYER SPRITES — Sci-Fi Military Marine, 16×16 pixel art
# ================================================================
# Legend: '.' transparent, 'A' armor, 'a' armor_lt, 'd' armor_dk,
#         'U' undersuit, 'V' visor, 'X' accent, 'S' skin,
#         'O' outline, 'H' hurt, 'W' white
#
# Body plan (16 rows):
#   0-1   : helmet top
#   2-6   : helmet with visor + face
#   7     : shoulder pads + backpack top
#   8-10  : chest plate with accent stripe
#   11    : belt/waist
#   12-13 : upper legs (undersuit)
#   14-15 : boots (armor_dk)

# ---- FRONT BASE: angular helmet, pauldrons, chest plate, rifle, boots ----
def _make_front_base():
    """Front-facing marine: angular helmet w/ visor slit, wide shoulder
    pauldrons, chest plate w/ orange accent, rifle held across body,
    backpack with light, armored knee pads, combat boots."""
    g = [
        _row16(".....OOOOOO....."),  # 0: helmet top (narrow, angular)
        _row16("....OaAAAAAO...."),  # 1: helmet upper ridge
        _row16("...OAAAAAAAAO..."),  # 2: helmet widest (angular sides)
        _row16("...OAAVVVVAAO..."),  # 3: visor slit (cyan, narrow)
        _row16("...OAAAAAAAAO..."),  # 4: helmet chin/lower face
        _row16("....OAAAAAAO...."),  # 5: jaw (narrower)
        _row16("....OOAAAAOO...."),  # 6: neck seal
        _row16(".OOaaAAAAAAaOO.."),  # 7: WIDE shoulder pauldrons
        _row16("OOaaAAXXXXAAaaO."),  # 8: chest plate w/ orange stripe, wide
        _row16("OOaAAAAAAAAAaaO."),  # 9: chest (pauldron edges visible)
        _row16(".OaAAUUUUUAAaO.."),  # 10: belt + undersuit midsection
        _row16(".OOOUUUUUUOOO..."),  # 11: waist
        _row16("..OOUU..UUOO..."),  # 12: legs split (symmetric)
        _row16("..OOddUUddOO..."),  # 13: thighs + knee pads (symmetric)
        _row16("..OOdd..ddOO..."),  # 14: boots (dark armor)
        _row16(".OOOdd..ddOOO.."),  # 15: feet
    ]
    return g


def _add_front_eyes(g):
    """Add two tiny skin-tone dots under the visor for face."""
    _set_char(g, 4, 6, 'S')
    _set_char(g, 4, 9, 'S')


# ---- FRONT IDLE A ----
def _build_front_idle_a():
    g = _make_front_base()
    _add_front_eyes(g)
    return _grid_to_str(g)


# ---- FRONT IDLE B (breathing: shoulders raise) ----
def _build_front_idle_b():
    g = _make_front_base()
    _add_front_eyes(g)
    # Widen shoulders slightly
    _set_char(g, 7, 1, 'a')
    _set_char(g, 7, 14, 'a')
    return _grid_to_str(g)


# ---- FRONT WALK (4 frames) ----
def _build_front_walk(frame):
    g = _make_front_base()
    _add_front_eyes(g)
    if frame == 0:  # left leg forward
        g[12] = _row16("...OOUU..UUOO...")
        g[13] = _row16("..OOUU..UUOOO..")
        g[14] = _row16("..OOdd..ddOOO..")
        g[15] = _row16(".OOOdd..ddOOOO..")
    elif frame == 2:  # right leg forward
        g[12] = _row16("...OOUU..UUOO...")
        g[13] = _row16("..OOOUU..UUOO..")
        g[14] = _row16("..OOOodd..ddO..")
        g[15] = _row16(".OOOOdd..ddOO...")
    return _grid_to_str(g)


# ---- FRONT SPRINT (2 frames, leaned) ----
def _build_front_sprint(frame):
    g = _make_front_base()
    _add_front_eyes(g)
    if frame == 0:
        g[12] = _row16("..OOUU..UUOO...")
        g[13] = _row16(".OOUU...UUOO..")
        g[14] = _row16("OOOdd...ddOO..")
        g[15] = _row16("..Od....dOOO..")
    else:
        g[12] = _row16("..OOUU..UUOO...")
        g[13] = _row16(".OOUU...UUOO..")
        g[14] = _row16("OOOodd..ddOO..")
        g[15] = _row16("..Odd..ddOOO..")
    return _grid_to_str(g)


# ---- FRONT SHOOT (2 frames: recoil + flash) ----
def _build_front_shoot(frame):
    g = _make_front_base()
    _add_front_eyes(g)
    if frame == 0:  # muzzle flash centered below chest
        _set_char(g, 11, 7, 'W')
        _set_char(g, 11, 8, 'W')
        _set_char(g, 12, 6, 'W')
        _set_char(g, 12, 9, 'W')
    return _grid_to_str(g)


# ---- FRONT RELOAD (3 frames: lower, swap, raise) ----
def _build_front_reload(frame):
    g = _make_front_base()
    _add_front_eyes(g)
    if frame == 1:  # mag swap — white marker at belt
        _set_char(g, 11, 7, 'W')
        _set_char(g, 11, 8, 'W')
    # Arms lower on all reload frames
    if frame == 0 or frame == 2:
        _set_char(g, 8, 2, 'a')
        _set_char(g, 8, 13, 'a')
    return _grid_to_str(g)


# ---- FRONT HURT (red flash — recolor armor to hurt) ----
def _build_front_hurt():
    g = _make_front_base()
    _add_front_eyes(g)
    s = _grid_to_str(g)
    s = _recolor(s, 'A', 'H')
    s = _recolor(s, 'a', 'H')
    s = _recolor(s, 'd', 'H')
    s = _recolor(s, 'U', 'H')
    return s


# ---- FRONT DEAD (3 frames: collapse) ----
def _build_front_dead(frame):
    if frame == 0:  # slumped standing
        g = _make_front_base()
        _add_front_eyes(g)
        g[0] = _row16(".....OOOOOOO...")
        g[1] = _row16("..OOaAAAAAAA0..")
        return _grid_to_str(g)
    elif frame == 1:  # kneeling
        return [
            "................",
            "................",
            "................",
            "................",
            "....OOOOOOOO....",
            "..OOaAAAAAAAAaO.",
            "..OAAVVVVVVAAAO.",
            "..OAAAAAAAAAAO..",
            "..OaAAAAAAAAaO..",
            "...OAXXXXXXAO...",
            "...OAUUUUUUAO...",
            "...OOUU..UUOO...",
            "..OOOdd..ddOOO..",
            "..OOOOOOOOOOOOO.",
            "................",
            "................",
        ]
    else:  # lying flat
        return [
            "................",
            "................",
            "................",
            "................",
            "................",
            "................",
            "................",
            "................",
            "................",
            "................",
            "...OOOOOOOOOO...",
            "..OaAAAAAAAAAaO.",
            "..OAVVAAAAAAVVO.",
            "..OOddOOOOOddO..",
            "..OOOOOOOOOOOO..",
            "................",
        ]


# ---- RIGHT PROFILE BASE ----
def _make_right_base():
    """Right-facing profile: angular helmet w/ visor slit on right,
    bulky backpack with orange light, pauldron visible, rifle forward."""
    g = [
        _row16(".....OOOOOO....."),  # 0: helmet top (angular)
        _row16("....OaAAAAAO...."),  # 1: helmet ridge
        _row16("...OAAAAAAAAO.."),  # 2: helmet widest
        _row16("...OAAAAAAAVO.."),  # 3: visor on right side (cyan slit)
        _row16("...OAAAAAAAAO.."),  # 4: chin
        _row16("....OAAAAAAO..."),  # 5: jaw
        _row16("....OOAAAAO...."),  # 6: neck
        _row16("..OaaAAAAAAaO.."),  # 7: shoulder pauldron + backpack
        _row16(".OaaAXXXXXXaO.."),  # 8: chest stripe + pauldron edge
        _row16(".OaAAAAAAAAO..."),  # 9: chest
        _row16(".OAAUUUUUAO...."),  # 10: belt
        _row16(".OOUUUUUUO...."),  # 11: waist
        _row16("..OOUU..UUOO.."),  # 12: legs (symmetric)
        _row16("..OddUUUUddO.."),  # 13: knee pad + thigh
        _row16("..OOdd..ddO..."),  # 14: boots
        _row16(".OOOdd..dOOO.."),  # 15: feet
    ]
    return g


def _add_right_eye(g):
    """One skin dot under visor on right side."""
    _set_char(g, 4, 11, 'S')


def _build_right_idle_a():
    g = _make_right_base()
    _add_right_eye(g)
    return _grid_to_str(g)


def _build_right_idle_b():
    g = _make_right_base()
    _add_right_eye(g)
    _set_char(g, 7, 1, 'a')
    return _grid_to_str(g)


def _build_right_walk(frame):
    g = _make_right_base()
    _add_right_eye(g)
    if frame == 0:
        g[12] = _row16("...OOUU..UUOO..")
        g[13] = _row16("..OOUU..UUOOO..")
        g[14] = _row16(".OOOdd..ddOOO..")
        g[15] = _row16("OOOdd..ddOOOO..")
    elif frame == 2:
        g[12] = _row16("...OOUU..UUOO..")
        g[13] = _row16("..OOOUU..UUOO..")
        g[14] = _row16("..OOOodd..ddO..")
        g[15] = _row16(".OOOOdd..ddOO..")
    return _grid_to_str(g)


def _build_right_sprint(frame):
    g = _make_right_base()
    _add_right_eye(g)
    if frame == 0:
        g[12] = _row16("..OOUU..UUOO..")
        g[13] = _row16(".OOUU...UUOO..")
        g[14] = _row16("OOOdd...ddOO..")
        g[15] = _row16("..Od....dOOO..")
    else:
        g[12] = _row16("..OOUU..UUOO..")
        g[13] = _row16(".OOUU...UUOO..")
        g[14] = _row16("OOOodd..ddOO..")
        g[15] = _row16("..Odd..ddOOO..")
    return _grid_to_str(g)


def _build_right_shoot(frame):
    g = _make_right_base()
    _add_right_eye(g)
    if frame == 0:  # muzzle flash at front (right side, near visor level)
        _set_char(g, 8, 13, 'W')
        _set_char(g, 8, 14, 'W')
    return _grid_to_str(g)


def _build_right_reload(frame):
    g = _make_right_base()
    _add_right_eye(g)
    if frame == 1:
        _set_char(g, 11, 7, 'W')
        _set_char(g, 11, 8, 'W')
    return _grid_to_str(g)


def _build_right_hurt():
    g = _make_right_base()
    _add_right_eye(g)
    s = _grid_to_str(g)
    s = _recolor(s, 'A', 'H')
    s = _recolor(s, 'a', 'H')
    s = _recolor(s, 'd', 'H')
    s = _recolor(s, 'U', 'H')
    return s


def _build_right_dead(frame):
    return _build_front_dead(frame)


# ---- BACK BASE (no visor, no face — backpack prominent, wide pauldrons) ----
def _make_back_base():
    """Back view: angular helmet from behind, wide shoulder pauldrons,
    prominent backpack with orange light, knee pads, no visor/face."""
    g = [
        _row16(".....OOOOOO....."),  # 0: helmet top (angular, matches front)
        _row16("....OaAAAAAO...."),  # 1: helmet ridge
        _row16("...OAAAAAAAAO.."),  # 2: helmet widest
        _row16("...OAAAAAAAAO.."),  # 3: no visor (back of helmet)
        _row16("...OAAAAAAAAO.."),  # 4: helmet lower
        _row16("....OAAAAAAO..."),  # 5: neck
        _row16("....OOAAAAO...."),  # 6: neck seal
        _row16(".OOaaAAXXAAAaO.."),  # 7: WIDE pauldrons + backpack with orange light
        _row16("OOaaAAAAAAAaaO."),  # 8: back plate, pauldron edges
        _row16("OOaAAAAAAAAAaO."),  # 9: back (pauldron visible)
        _row16(".OaAAUUUUUAAaO."),  # 10: belt + undersuit
        _row16(".OOOUUUUUUOOO.."),  # 11: waist
        _row16("..OOUU..UUOO..."),  # 12: legs split
        _row16("..OddUUUUddO..."),  # 13: thighs + knee pads
        _row16("..OOdd..ddOO..."),  # 14: boots
        _row16(".OOOdd..ddOOO.."),  # 15: feet
    ]
    return g


def _build_back_idle_a():
    return _grid_to_str(_make_back_base())


def _build_back_idle_b():
    g = _make_back_base()
    _set_char(g, 7, 1, 'a')
    return _grid_to_str(g)


def _build_back_walk(frame):
    g = _make_back_base()
    if frame == 0:
        g[12] = _row16("...OOUU..UUOO..")
        g[13] = _row16("..OOUU..UUOOO..")
        g[14] = _row16(".OOOdd..ddOOO..")
        g[15] = _row16("OOOdd..ddOOOO..")
    elif frame == 2:
        g[12] = _row16("...OOUU..UUOO..")
        g[13] = _row16("..OOOUU..UUOO..")
        g[14] = _row16("..OOOodd..ddO..")
        g[15] = _row16(".OOOOdd..ddOO..")
    return _grid_to_str(g)


def _build_back_sprint(frame):
    g = _make_back_base()
    if frame == 0:
        g[12] = _row16("..OOUU..UUOO..")
        g[13] = _row16(".OOUU...UUOO..")
        g[14] = _row16("OOOdd...ddOO..")
        g[15] = _row16("..Od....dOOO..")
    else:
        g[12] = _row16("..OOUU..UUOO..")
        g[13] = _row16(".OOUU...UUOO..")
        g[14] = _row16("OOOodd..ddOO..")
        g[15] = _row16("..Odd..ddOOO..")
    return _grid_to_str(g)


def _build_back_shoot(frame):
    g = _make_back_base()
    if frame == 0:  # muzzle flash from rifle (right side)
        _set_char(g, 12, 13, 'W')
        _set_char(g, 12, 14, 'W')
        _set_char(g, 11, 14, 'W')
    return _grid_to_str(g)


def _build_back_reload(frame):
    g = _make_back_base()
    if frame == 1:
        _set_char(g, 11, 7, 'W')
        _set_char(g, 11, 8, 'W')
    return _grid_to_str(g)


def _build_back_hurt():
    s = _grid_to_str(_make_back_base())
    s = _recolor(s, 'A', 'H')
    s = _recolor(s, 'a', 'H')
    s = _recolor(s, 'd', 'H')
    s = _recolor(s, 'U', 'H')
    return s


def _build_back_dead(frame):
    return _build_front_dead(frame)


# ---- LEFT = mirror of RIGHT ----
def _build_left_idle_a():
    return _mirror(_build_right_idle_a())

def _build_left_idle_b():
    return _mirror(_build_right_idle_b())

def _build_left_walk(frame):
    return _mirror(_build_right_walk(frame))

def _build_left_sprint(frame):
    return _mirror(_build_right_sprint(frame))

def _build_left_shoot(frame):
    return _mirror(_build_right_shoot(frame))

def _build_left_reload(frame):
    return _mirror(_build_right_reload(frame))

def _build_left_hurt():
    return _mirror(_build_right_hurt())

def _build_left_dead(frame):
    return _build_front_dead(frame)



# ============ DIRECTIONAL BUILDERS ============

DIRECTIONS = ['front', 'right', 'back', 'left']

_DIR_MAP = {
    'front': {
        'idle':   (_build_front_idle_a(), _build_front_idle_b()),
        'walk':   (_build_front_walk(0), _build_front_walk(1),
                   _build_front_walk(2), _build_front_walk(3)),
        'sprint': (_build_front_sprint(0), _build_front_sprint(1)),
        'shoot':  (_build_front_shoot(0), _build_front_shoot(1)),
        'reload': (_build_front_reload(0), _build_front_reload(1),
                   _build_front_reload(2)),
        'hurt':   (_build_front_hurt(),),
        'dead':   (_build_front_dead(0), _build_front_dead(1), _build_front_dead(2)),
    },
    'right': {
        'idle':   (_build_right_idle_a(), _build_right_idle_b()),
        'walk':   (_build_right_walk(0), _build_right_walk(1),
                   _build_right_walk(2), _build_right_walk(3)),
        'sprint': (_build_right_sprint(0), _build_right_sprint(1)),
        'shoot':  (_build_right_shoot(0), _build_right_shoot(1)),
        'reload': (_build_right_reload(0), _build_right_reload(1),
                   _build_right_reload(2)),
        'hurt':   (_build_right_hurt(),),
        'dead':   (_build_right_dead(0), _build_right_dead(1), _build_right_dead(2)),
    },
    'back': {
        'idle':   (_build_back_idle_a(), _build_back_idle_b()),
        'walk':   (_build_back_walk(0), _build_back_walk(1),
                   _build_back_walk(2), _build_back_walk(3)),
        'sprint': (_build_back_sprint(0), _build_back_sprint(1)),
        'shoot':  (_build_back_shoot(0), _build_back_shoot(1)),
        'reload': (_build_back_reload(0), _build_back_reload(1),
                   _build_back_reload(2)),
        'hurt':   (_build_back_hurt(),),
        'dead':   (_build_back_dead(0), _build_back_dead(1), _build_back_dead(2)),
    },
    'left': {
        'idle':   (_build_left_idle_a(), _build_left_idle_b()),
        'walk':   (_build_left_walk(0), _build_left_walk(1),
                   _build_left_walk(2), _build_left_walk(3)),
        'sprint': (_build_left_sprint(0), _build_left_sprint(1)),
        'shoot':  (_build_left_shoot(0), _build_left_shoot(1)),
        'reload': (_build_left_reload(0), _build_left_reload(1),
                   _build_left_reload(2)),
        'hurt':   (_build_left_hurt(),),
        'dead':   (_build_left_dead(0), _build_left_dead(1), _build_left_dead(2)),
    },
}

# Validate ALL grids at import time
for _dir, _states in _DIR_MAP.items():
    for _state, _grids in _states.items():
        for _i, _grid in enumerate(_grids):
            _validate(_grid, f"{_dir}/{_state}[{_i}]")


def make_player_frames(state, direction='front'):
    """Build player sprite frames for a given animation state + direction.

    Loads from JSON sprite data (generated by generate_sprites.py using the
    pixel-art-json-renderer skill methodology). Falls back to old text-grid
    method if JSON is not available.
    """
    # Try loading from JSON sprite sheet first
    import json as _json
    import os as _os
    _json_path = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))),
                               'sprites_json', 'all_sprites.json')
    if getattr(sys, 'frozen', False):
        _json_path = _os.path.join(sys._MEIPASS, 'sprites_json', 'all_sprites.json')
    if _os.path.exists(_json_path):
        with open(_json_path) as f:
            _all_sprites = _json.load(f)
        key = f'{direction}_{state}'
        if key in _all_sprites:
            frames = []
            for frame_data in _all_sprites[key]:
                surf = _json_to_surface(frame_data)
                frames.append(surf)
            return frames

    # Fallback: old text-grid method
    grids = _DIR_MAP.get(direction, _DIR_MAP['front']).get(state)
    if grids is None:
        grids = _DIR_MAP['front'][state]
    return [_grid_to_surface(g) for g in grids]


def _json_to_surface(frame_data):
    """Convert JSON pixel data to a scaled pygame Surface."""
    w = frame_data['width']
    h = frame_data['height']
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    for pixel in frame_data.get('pixels', []):
        x, y = pixel['x'], pixel['y']
        color_str = pixel['color']
        if color_str == 'transparent':
            continue
        hex_str = color_str.lstrip('#')
        if len(hex_str) == 6:
            r, g, b = int(hex_str[0:2], 16), int(hex_str[2:4], 16), int(hex_str[4:6], 16)
            surf.set_at((x, y), (r, g, b, 255))
        elif len(hex_str) == 8:
            r, g, b, a = (int(hex_str[i:i+2], 16) for i in range(0, 8, 2))
            surf.set_at((x, y), (r, g, b, a))
    # Scale: 32x32 sprites get 1.5x, 16x16 get 2x (legacy)
    if w >= 32:
        scaled_w, scaled_h = int(w * 1.5), int(h * 1.5)
    else:
        scaled_w, scaled_h = w * SCALE, h * SCALE
    return pygame.transform.scale(surf, (scaled_w, scaled_h))


# ============ XENOMORPH SPRITES (refined) ============

def _xsurf(w, h):
    return pygame.Surface((w, h), pygame.SRCALPHA)

# Xeno color palette
_X_BODY = (55, 20, 30)      # dark chitin
_X_BODY_LT = (75, 28, 38)   # lighter segment
_X_HEAD = (40, 14, 24)      # darker head
_X_EYE = (157, 255, 61)     # acid green eyes
_X_EYE_RED = (255, 65, 54)  # red eyes when attacking
_X_TAIL = (50, 18, 28)      # tail
_X_CLAW = (100, 40, 50)     # claws
_X_FLASH = (232, 237, 242)  # hit flash (white)


def make_xeno_patrol_frames(size=40):
    """Patrol: slow undulating crawl, 4 frames."""
    frames = []
    for i in range(4):
        s = _xsurf(size, size)
        cx, cy = size // 2, size // 2
        phase = i / 4.0 * math.tau
        # Shadow
        pygame.draw.ellipse(s, (0, 0, 0, 70), (3, size - 7, size - 6, 5))
        # Body: 5 segments undulating
        for seg in range(5):
            sx = cx - 12 + seg * 6
            sy = cy + int(math.sin(phase + seg * 0.7) * 2)
            r = max(3, 5 - abs(seg - 2))
            col = _X_BODY_LT if seg % 2 == 0 else _X_BODY
            pygame.draw.circle(s, col, (sx, sy), r)
            pygame.draw.circle(s, HULL_BLACK, (sx, sy), r, 1)
        # Head
        hx = cx + 14
        hy = cy + int(math.sin(phase) * 3)
        pygame.draw.circle(s, _X_HEAD, (hx, hy), 6)
        pygame.draw.circle(s, HULL_BLACK, (hx, hy), 6, 1)
        # Eye
        pygame.draw.circle(s, _X_EYE, (hx + 2, hy - 1), 1)
        # Tail
        tx = cx - 16
        ty = cy + int(math.sin(phase + 2) * 5)
        pygame.draw.line(s, _X_TAIL, (cx - 12, cy), (tx, ty), 2)
        pygame.draw.circle(s, _X_CLAW, (tx, ty), 2)
        frames.append(s)
    return frames


def make_xeno_chase_frames(size=40):
    """Chase: fast crawl with tail lashing, 4 frames."""
    frames = []
    for i in range(4):
        s = _xsurf(size, size)
        cx, cy = size // 2, size // 2
        phase = i / 4.0 * math.tau
        pygame.draw.ellipse(s, (0, 0, 0, 80), (3, size - 7, size - 6, 5))
        # 6 segments, more stretched
        for seg in range(6):
            sx = cx - 14 + seg * 5
            sy = cy + int(math.sin(phase + seg * 0.5) * 3)
            r = max(3, 5 - abs(seg - 2) + 1)
            col = _X_BODY_LT if seg % 2 == 0 else _X_BODY
            pygame.draw.circle(s, col, (sx, sy), r)
            pygame.draw.circle(s, HULL_BLACK, (sx, sy), r, 1)
        # Head, larger
        hx = cx + 16
        hy = cy + int(math.sin(phase) * 4)
        pygame.draw.circle(s, _X_HEAD, (hx, hy), 7)
        pygame.draw.circle(s, HULL_BLACK, (hx, hy), 7, 1)
        # Two glowing eyes
        pygame.draw.circle(s, _X_EYE, (hx + 3, hy - 2), 2)
        pygame.draw.circle(s, _X_EYE, (hx + 3, hy + 2), 1)
        # Tail lashing
        tx = cx - 18
        ty = cy + int(math.sin(phase + 2) * 8)
        pygame.draw.line(s, _X_TAIL, (cx - 12, cy), (tx, ty), 2)
        pygame.draw.circle(s, _X_CLAW, (tx, ty), 2)
        # Legs
        for leg in range(2):
            ls = 1 if leg == 0 else -1
            lx = cx + ls * 4
            ly = cy + 6
            pygame.draw.line(s, _X_BODY, (lx, ly), (lx + ls * 3, ly + 4), 2)
        frames.append(s)
    return frames


def make_xeno_lunge_frames(size=40):
    """Lunge: coil → spring → extend, 3 frames."""
    frames = []
    for i in range(3):
        s = _xsurf(size, size)
        cx, cy = size // 2, size // 2
        if i == 0:  # coiled
            pygame.draw.ellipse(s, (0, 0, 0, 80), (3, size - 7, size - 6, 5))
            for seg in range(4):
                r = 6 - seg
                pygame.draw.circle(s, _X_BODY, (cx - 6 + seg * 4, cy), r)
                pygame.draw.circle(s, HULL_BLACK, (cx - 6 + seg * 4, cy), r, 1)
            pygame.draw.circle(s, _X_HEAD, (cx + 8, cy), 6)
            pygame.draw.circle(s, HULL_BLACK, (cx + 8, cy), 6, 1)
            pygame.draw.circle(s, _X_EYE, (cx + 10, cy - 2), 2)
        elif i == 1:  # springing
            pygame.draw.ellipse(s, (0, 0, 0, 60), (3, size - 7, size - 6, 5))
            for seg in range(6):
                sx = cx - 14 + seg * 5
                pygame.draw.circle(s, _X_BODY_LT, (sx, cy), 4)
                pygame.draw.circle(s, HULL_BLACK, (sx, cy), 4, 1)
            pygame.draw.circle(s, _X_HEAD, (cx + 18, cy), 7)
            pygame.draw.circle(s, HULL_BLACK, (cx + 18, cy), 7, 1)
            pygame.draw.circle(s, _X_EYE, (cx + 20, cy - 2), 2)
            # Claws extended
            pygame.draw.line(s, _X_CLAW, (cx + 15, cy + 5), (cx + 23, cy + 9), 2)
            pygame.draw.line(s, _X_CLAW, (cx + 15, cy - 5), (cx + 23, cy - 9), 2)
        else:  # extended
            pygame.draw.ellipse(s, (0, 0, 0, 50), (3, size - 7, size - 6, 5))
            for seg in range(7):
                sx = cx - 16 + seg * 5
                pygame.draw.circle(s, _X_BODY, (sx, cy), 3)
            pygame.draw.circle(s, _X_HEAD, (cx + 20, cy), 6)
            pygame.draw.circle(s, HULL_BLACK, (cx + 20, cy), 6, 1)
            pygame.draw.circle(s, _X_EYE, (cx + 22, cy - 2), 2)
        frames.append(s)
    return frames


def make_xeno_attack_frames(size=40):
    """Attack: strike → recover, 2 frames."""
    frames = []
    for i in range(2):
        s = _xsurf(size, size)
        cx, cy = size // 2, size // 2
        if i == 0:  # strike
            pygame.draw.ellipse(s, (0, 0, 0, 80), (3, size - 7, size - 6, 5))
            pygame.draw.circle(s, _X_BODY, (cx - 4, cy), 6)
            pygame.draw.circle(s, HULL_BLACK, (cx - 4, cy), 6, 1)
            pygame.draw.circle(s, _X_HEAD, (cx + 12, cy), 8)
            pygame.draw.circle(s, HULL_BLACK, (cx + 12, cy), 8, 1)
            # Red eyes when attacking
            pygame.draw.circle(s, _X_EYE_RED, (cx + 14, cy - 2), 2)
            pygame.draw.circle(s, _X_EYE_RED, (cx + 14, cy + 2), 2)
            # Claws
            pygame.draw.line(s, _X_CLAW, (cx + 8, cy + 5), (cx + 21, cy + 10), 2)
            pygame.draw.line(s, _X_CLAW, (cx + 8, cy - 5), (cx + 21, cy - 10), 2)
            # Mouth
            pygame.draw.line(s, _X_EYE_RED, (cx + 14, cy), (cx + 18, cy), 1)
        else:  # recover
            pygame.draw.ellipse(s, (0, 0, 0, 80), (3, size - 7, size - 6, 5))
            pygame.draw.circle(s, _X_BODY, (cx, cy), 5)
            pygame.draw.circle(s, HULL_BLACK, (cx, cy), 5, 1)
            pygame.draw.circle(s, _X_HEAD, (cx + 10, cy), 6)
            pygame.draw.circle(s, HULL_BLACK, (cx + 10, cy), 6, 1)
            pygame.draw.circle(s, _X_EYE, (cx + 12, cy - 2), 1)
        frames.append(s)
    return frames


def make_xeno_stagger_frames(size=40):
    """Stagger: knockback + white flash, 2 frames."""
    frames = []
    for i in range(2):
        s = _xsurf(size, size)
        cx, cy = size // 2, size // 2
        offset = -4 + i * 4
        pygame.draw.ellipse(s, (0, 0, 0, 60), (3, size - 7, size - 6, 5))
        for seg in range(4):
            sx = cx - 8 + seg * 5 + offset
            sy = cy - i * 2
            pygame.draw.circle(s, _X_BODY, (sx, sy), 4)
            pygame.draw.circle(s, HULL_BLACK, (sx, sy), 4, 1)
        pygame.draw.circle(s, _X_HEAD, (cx + 10 + offset, cy - i * 2), 5)
        pygame.draw.circle(s, HULL_BLACK, (cx + 10 + offset, cy - i * 2), 5, 1)
        pygame.draw.circle(s, _X_EYE, (cx + 12 + offset, cy - i * 2 - 2), 1)
        # White flash outline on first frame
        if i == 0:
            pygame.draw.circle(s, _X_FLASH, (cx, cy), 10, 2)
        frames.append(s)
    return frames


def make_xeno_death_frames(size=40):
    """Death: collapse → dissolve → acid splash, 4 frames."""
    frames = []
    for i in range(4):
        s = _xsurf(size, size)
        cx, cy = size // 2, size // 2
        sink = i * 4
        alpha = max(0, 255 - i * 60)
        # Body collapsing
        for seg in range(5):
            sx = cx - 10 + seg * 5
            sy = cy + sink
            r = max(1, 5 - i)
            col = (max(0, _X_BODY[0] - i * 10),
                   max(0, _X_BODY[1] - i * 3),
                   max(0, _X_BODY[2] - i * 5))
            tmp = _xsurf(size, size)
            pygame.draw.circle(tmp, (*col, alpha), (sx, sy), r)
            s.blit(tmp, (0, 0))
        # Acid splash on frame 0
        if i == 0:
            for _ in range(8):
                ax = cx + random.randint(-14, 14)
                ay = cy + random.randint(-10, 10)
                pygame.draw.circle(s, _X_EYE, (ax, ay), random.randint(2, 4))
        # Dissolving particles on later frames
        if i >= 2:
            for _ in range(5):
                ax = cx + random.randint(-10, 10)
                ay = cy - i * 3 + random.randint(-4, 4)
                pygame.draw.circle(s, (*_X_EYE, 100), (ax, ay), 2)
        # Fading eye
        if i < 2:
            ex = cx + 14
            ey = cy + sink - 2
            ea = max(0, alpha - 50)
            tmp = _xsurf(size, size)
            pygame.draw.circle(tmp, (*_X_EYE, ea), (ex, ey), 2)
            s.blit(tmp, (0, 0))
        frames.append(s)
    return frames


# ============ RUNNER SPRITES ============
# Leaner, faster, red eyes (not green)

_R_BODY = (65, 20, 25)
_R_BODY_LT = (85, 28, 35)
_R_HEAD = (45, 15, 20)
_R_EYE = (255, 50, 50)       # red eyes
_R_TAIL = (55, 18, 23)

def make_runner_chase_frames(size=32):
    frames = []
    for i in range(4):
        s = _xsurf(size, size)
        cx, cy = size // 2, size // 2
        phase = i / 4.0 * math.tau
        pygame.draw.ellipse(s, (0, 0, 0, 80), (3, size - 7, size - 6, 5))
        for seg in range(7):
            sx = cx - 14 + seg * 4
            sy = cy + int(math.sin(phase + seg * 0.4) * 2)
            r = max(2, 4 - abs(seg - 3) + 1)
            col = _R_BODY_LT if seg % 2 == 0 else _R_BODY
            pygame.draw.circle(s, col, (sx, sy), r)
            pygame.draw.circle(s, HULL_BLACK, (sx, sy), r, 1)
        hx = cx + 14; hy = cy + int(math.sin(phase) * 3)
        pygame.draw.circle(s, _R_HEAD, (hx, hy), 5)
        pygame.draw.circle(s, HULL_BLACK, (hx, hy), 5, 1)
        pygame.draw.circle(s, _R_EYE, (hx + 2, hy - 1), 2)
        tx = cx - 18; ty = cy + int(math.sin(phase + 2) * 6)
        pygame.draw.line(s, _R_TAIL, (cx - 14, cy), (tx, ty), 2)
        frames.append(s)
    return frames

def make_runner_leap_frames(size=32):
    return make_xeno_lunge_frames(size)

def make_runner_attack_frames(size=32):
    return make_xeno_attack_frames(size)

def make_runner_stagger_frames(size=32):
    return make_xeno_stagger_frames(size)

def make_runner_death_frames(size=32):
    return make_xeno_death_frames(size)


# ============ BRUTE SPRITES ============

_B_BODY = (50, 18, 28)
_B_BODY_LT = (70, 25, 35)
_B_PLATE = (90, 35, 45)
_B_HEAD = (40, 14, 22)
_B_EYE = (255, 40, 40)

def make_brute_patrol_frames(size=48):
    frames = []
    for i in range(3):
        s = _xsurf(size, size)
        cx, cy = size // 2, size // 2 + 4
        phase = i / 3.0 * math.tau
        pygame.draw.ellipse(s, (0, 0, 0, 100), (4, size - 10, size - 8, 8))
        for seg in range(3):
            sx = cx - 8 + seg * 8
            sy = cy + int(math.sin(phase + seg * 0.5) * 1)
            r = 10 - seg * 2
            pygame.draw.circle(s, _B_BODY, (sx, sy), r)
            pygame.draw.circle(s, HULL_BLACK, (sx, sy), r, 1)
            pygame.draw.circle(s, _B_PLATE, (sx, sy - 2), r - 3)
        hx = cx + 12; hy = cy - 2
        pygame.draw.circle(s, _B_HEAD, (hx, hy), 9)
        pygame.draw.circle(s, HULL_BLACK, (hx, hy), 9, 1)
        pygame.draw.circle(s, _B_EYE, (hx + 3, hy - 2), 2)
        pygame.draw.circle(s, _B_EYE, (hx + 3, hy + 2), 2)
        pygame.draw.rect(s, _B_BODY, (cx - 4, cy + 8, 4, 6))
        pygame.draw.rect(s, _B_BODY, (cx + 4, cy + 8, 4, 6))
        frames.append(s)
    return frames

def make_brute_chase_frames(size=48):
    return make_brute_patrol_frames(size)

def make_brute_windup_frames(size=48):
    frames = []
    for i in range(2):
        s = _xsurf(size, size)
        cx, cy = size // 2, size // 2 + 4
        pygame.draw.ellipse(s, (0, 0, 0, 100), (4, size - 10, size - 8, 8))
        for seg in range(3):
            sx = cx - 8 + seg * 8
            r = 10 - seg * 2
            pygame.draw.circle(s, _B_BODY, (sx, cy), r)
            pygame.draw.circle(s, HULL_BLACK, (sx, cy), r, 1)
            pygame.draw.circle(s, _B_PLATE, (sx, cy - 2), r - 3)
        hx = cx + 12; hy = cy - 2
        pygame.draw.circle(s, _B_HEAD, (hx, hy), 9)
        pygame.draw.circle(s, HULL_BLACK, (hx, hy), 9, 1)
        pygame.draw.circle(s, _B_EYE, (hx + 3, hy - 2), 3)
        pygame.draw.circle(s, _B_EYE, (hx + 3, hy + 2), 3)
        if i == 0:
            pygame.draw.circle(s, (255, 50, 50, 60), (hx, hy), 14, 2)
        frames.append(s)
    return frames

def make_brute_charge_frames(size=48):
    frames = []
    for i in range(3):
        s = _xsurf(size, size)
        cx, cy = size // 2, size // 2 + 4
        pygame.draw.ellipse(s, (0, 0, 0, 80), (4, size - 10, size - 8, 8))
        for seg in range(3):
            sx = cx - 6 + seg * 8 + i * 2
            r = 10 - seg * 2
            pygame.draw.circle(s, _B_BODY, (sx, cy), r)
            pygame.draw.circle(s, HULL_BLACK, (sx, cy), r, 1)
            pygame.draw.circle(s, _B_PLATE, (sx, cy - 2), r - 3)
        hx = cx + 16 + i * 2; hy = cy - 2
        pygame.draw.circle(s, _B_HEAD, (hx, hy), 9)
        pygame.draw.circle(s, HULL_BLACK, (hx, hy), 9, 1)
        pygame.draw.circle(s, _B_EYE, (hx + 3, hy - 2), 2)
        pygame.draw.circle(s, _B_EYE, (hx + 3, hy + 2), 2)
        frames.append(s)
    return frames

def make_brute_groundpound_frames(size=48):
    frames = []
    for i in range(2):
        s = _xsurf(size, size)
        cx, cy = size // 2, size // 2 + 4
        pygame.draw.ellipse(s, (0, 0, 0, 100), (4, size - 10, size - 8, 8))
        for seg in range(3):
            sx = cx - 8 + seg * 8
            r = 10 - seg * 2
            pygame.draw.circle(s, _B_BODY, (sx, cy), r)
            pygame.draw.circle(s, HULL_BLACK, (sx, cy), r, 1)
            pygame.draw.circle(s, _B_PLATE, (sx, cy - 2), r - 3)
        hx = cx + 12; hy = cy - 2
        pygame.draw.circle(s, _B_HEAD, (hx, hy), 9)
        pygame.draw.circle(s, HULL_BLACK, (hx, hy), 9, 1)
        pygame.draw.circle(s, _B_EYE, (hx + 3, hy - 2), 3)
        pygame.draw.circle(s, _B_EYE, (hx + 3, hy + 2), 3)
        if i == 1:
            pygame.draw.circle(s, (200, 100, 100, 100), (cx, cy + 8), 20, 2)
        frames.append(s)
    return frames

def make_brute_stagger_frames(size=48):
    return make_xeno_stagger_frames(size)

def make_brute_death_frames(size=48):
    frames = []
    for i in range(4):
        s = _xsurf(size, size)
        cx, cy = size // 2, size // 2 + 4
        sink = i * 6
        alpha = max(0, 255 - i * 60)
        for seg in range(3):
            sx = cx - 8 + seg * 8
            sy = cy + sink
            r = max(2, 10 - seg * 2 - i * 2)
            col = (max(0, _B_BODY[0] - i * 10), max(0, _B_BODY[1] - i * 3), max(0, _B_BODY[2] - i * 5))
            tmp = _xsurf(size, size)
            pygame.draw.circle(tmp, (*col, alpha), (sx, sy), r)
            s.blit(tmp, (0, 0))
        if i == 0:
            for _ in range(12):
                ax = cx + random.randint(-16, 16)
                ay = cy + random.randint(-12, 12)
                pygame.draw.circle(s, ACID, (ax, ay), random.randint(3, 5))
        if i >= 2:
            for _ in range(6):
                ax = cx + random.randint(-14, 14)
                ay = cy - i * 3 + random.randint(-5, 5)
                pygame.draw.circle(s, (*ACID[:3], 100), (ax, ay), 2)
        frames.append(s)
    return frames


# ============ SPITTER SPRITES ============

_S_BODY = (55, 22, 30)
_S_BODY_LT = (75, 30, 38)
_S_HEAD = (45, 18, 25)
_S_EYE = (157, 255, 61)
_S_SAC = (100, 200, 50)

def make_spitter_patrol_frames(size=36):
    frames = []
    for i in range(4):
        s = _xsurf(size, size)
        cx, cy = size // 2, size // 2
        phase = i / 4.0 * math.tau
        pygame.draw.ellipse(s, (0, 0, 0, 70), (3, size - 7, size - 6, 5))
        for seg in range(4):
            sx = cx - 8 + seg * 5
            sy = cy + int(math.sin(phase + seg * 0.7) * 2)
            r = max(2, 4 - abs(seg - 2))
            col = _S_BODY_LT if seg % 2 == 0 else _S_BODY
            pygame.draw.circle(s, col, (sx, sy), r)
            pygame.draw.circle(s, HULL_BLACK, (sx, sy), r, 1)
        hx = cx + 12; hy = cy - 1
        pygame.draw.circle(s, _S_HEAD, (hx, hy), 6)
        pygame.draw.circle(s, HULL_BLACK, (hx, hy), 6, 1)
        pygame.draw.circle(s, _S_EYE, (hx + 2, hy - 1), 1)
        for sac in range(2):
            sac_x = cx - 6 + sac * 4
            sac_y = cy - 4
            pygame.draw.circle(s, _S_SAC, (sac_x, sac_y), 3)
            pygame.draw.circle(s, HULL_BLACK, (sac_x, sac_y), 3, 1)
        frames.append(s)
    return frames

def make_spitter_chase_frames(size=36):
    return make_spitter_patrol_frames(size)

def make_spitter_retreat_frames(size=36):
    return make_spitter_patrol_frames(size)

def make_spitter_spit_frames(size=36):
    frames = []
    for i in range(2):
        s = _xsurf(size, size)
        cx, cy = size // 2, size // 2
        pygame.draw.ellipse(s, (0, 0, 0, 70), (3, size - 7, size - 6, 5))
        for seg in range(4):
            sx = cx - 8 + seg * 5
            r = max(2, 4 - abs(seg - 2))
            col = _S_BODY_LT if seg % 2 == 0 else _S_BODY
            pygame.draw.circle(s, col, (sx, cy), r)
            pygame.draw.circle(s, HULL_BLACK, (sx, cy), r, 1)
        hx = cx + 12; hy = cy - 2 - i
        pygame.draw.circle(s, _S_HEAD, (hx, hy), 6)
        pygame.draw.circle(s, HULL_BLACK, (hx, hy), 6, 1)
        pygame.draw.circle(s, _S_EYE, (hx + 2, hy - 1), 2)
        for sac in range(2):
            sac_x = cx - 6 + sac * 4
            sac_y = cy - 4
            pygame.draw.circle(s, (150, 255, 80), (sac_x, sac_y), 4)
            pygame.draw.circle(s, HULL_BLACK, (sac_x, sac_y), 4, 1)
        if i == 1:
            pygame.draw.circle(s, ACID, (hx + 8, hy), 3)
        frames.append(s)
    return frames

def make_spitter_stagger_frames(size=36):
    return make_xeno_stagger_frames(size)

def make_spitter_death_frames(size=36):
    return make_xeno_death_frames(size)


# ============ ENEMY SPRITE FACTORY ============

ENEMY_SPRITE_MAP = {
    'drone': {
        'patrol': make_xeno_patrol_frames, 'chase': make_xeno_chase_frames,
        'lunge': make_xeno_lunge_frames, 'attack': make_xeno_attack_frames,
        'stagger': make_xeno_stagger_frames, 'death': make_xeno_death_frames,
        'leap': make_xeno_lunge_frames,
    },
    'runner': {
        'patrol': make_runner_chase_frames, 'chase': make_runner_chase_frames,
        'leap': make_runner_leap_frames, 'attack': make_runner_attack_frames,
        'stagger': make_runner_stagger_frames, 'death': make_runner_death_frames,
    },
    'brute': {
        'patrol': make_brute_patrol_frames, 'chase': make_brute_chase_frames,
        'windup': make_brute_windup_frames, 'charge': make_brute_charge_frames,
        'groundpound': make_brute_groundpound_frames, 'recover': make_brute_patrol_frames,
        'stagger': make_brute_stagger_frames, 'death': make_brute_death_frames,
    },
    'spitter': {
        'patrol': make_spitter_patrol_frames, 'chase': make_spitter_chase_frames,
        'retreat': make_spitter_retreat_frames, 'spit': make_spitter_spit_frames,
        'stagger': make_spitter_stagger_frames, 'death': make_spitter_death_frames,
    },
}


def make_enemy_frames(enemy_type, state, size=None):
    """Get sprite frames for an enemy type + animation state."""
    sprite_map = ENEMY_SPRITE_MAP.get(enemy_type, ENEMY_SPRITE_MAP['drone'])
    factory = sprite_map.get(state, sprite_map.get('patrol', make_xeno_patrol_frames))
    if factory is None:
        factory = make_xeno_patrol_frames
    if size is not None:
        return factory(size)
    return factory()
