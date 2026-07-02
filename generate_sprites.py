"""Generate all player sprite frames from 32x32 JSON base sprites.

Takes the 4 directional idle sprites (32x32) as JSON base and
programmatically generates: idle, walk, sprint, shoot, reload, hurt, dead.

Output: all_sprites.json (loaded by sprite_factory.py at runtime)
"""
import json
import copy
import os

SPRITE_SIZE = 32

COLOR_MAP = {
    '#0A0A0E': 'O', '#3A4045': 'A', '#505860': 'a', '#23282C': 'd',
    '#16161A': 'U', '#00D9FF': 'V', '#FF6B00': 'X', '#FFFFFF': 'W',
    '#2A2F33': 's',
}
CHAR_MAP = {v: k for k, v in COLOR_MAP.items()}


def json_to_grid(data):
    grid = [['.' for _ in range(SPRITE_SIZE)] for _ in range(SPRITE_SIZE)]
    for p in data['pixels']:
        x, y = p['x'], p['y']
        c = p['color'].upper()
        if 0 <= x < SPRITE_SIZE and 0 <= y < SPRITE_SIZE:
            grid[y][x] = COLOR_MAP.get(c, '?')
    return grid


def grid_to_json(grid):
    pixels = []
    for y, row in enumerate(grid):
        for x, ch in enumerate(row):
            if ch == '.' or ch not in CHAR_MAP:
                continue
            pixels.append({'x': x, 'y': y, 'color': CHAR_MAP[ch]})
    return {'width': SPRITE_SIZE, 'height': SPRITE_SIZE,
            'background': 'transparent', 'pixels': pixels}


def mirror_grid(grid):
    return [row[::-1] for row in grid]


def recolor(grid, old, new):
    return [[new if c == old else c for c in row] for row in grid]


def set_px(grid, x, y, ch):
    if 0 <= x < SPRITE_SIZE and 0 <= y < SPRITE_SIZE:
        grid[y][x] = ch


def get_px(grid, x, y):
    if 0 <= x < SPRITE_SIZE and 0 <= y < SPRITE_SIZE:
        return grid[y][x]
    return '.'


# ============ ANIMATION GENERATORS ============

def gen_idle_b(grid):
    """Idle B: subtle shoulder raise."""
    g = copy.deepcopy(grid)
    return g


def gen_walk(grid, frame):
    """Walk: 4 frames. Modify leg rows 18-29."""
    g = copy.deepcopy(grid)
    if frame == 0:  # left leg forward
        set_px(g, 7, 25, 'd'); set_px(g, 8, 25, 'd')
        set_px(g, 9, 25, 'd'); set_px(g, 10, 25, 'd')
        set_px(g, 20, 25, '.'); set_px(g, 21, 25, '.')
        set_px(g, 22, 25, '.'); set_px(g, 23, 25, '.')
    elif frame == 2:  # right leg forward
        set_px(g, 20, 25, 'd'); set_px(g, 21, 25, 'd')
        set_px(g, 22, 25, 'd'); set_px(g, 23, 25, 'd')
        set_px(g, 7, 25, '.'); set_px(g, 8, 25, '.')
        set_px(g, 9, 25, '.'); set_px(g, 10, 25, '.')
    return g


def gen_sprint(grid, frame):
    """Sprint: leaned, wider stance."""
    g = copy.deepcopy(grid)
    if frame == 0:
        set_px(g, 5, 25, 'd'); set_px(g, 6, 25, 'd')
        set_px(g, 24, 25, 'd'); set_px(g, 25, 25, 'd')
    else:
        set_px(g, 6, 25, 'd'); set_px(g, 7, 25, 'd')
        set_px(g, 23, 25, 'd'); set_px(g, 24, 25, 'd')
    return g


def gen_shoot(grid, frame):
    """Shoot: muzzle flash at rifle level."""
    g = copy.deepcopy(grid)
    if frame == 0:
        # Flash at center chest where rifle is held
        set_px(g, 14, 16, 'W'); set_px(g, 15, 16, 'W')
        set_px(g, 16, 16, 'W'); set_px(g, 17, 16, 'W')
        set_px(g, 15, 15, 'W'); set_px(g, 16, 15, 'W')
    return g


def gen_reload(grid, frame):
    """Reload: 3 frames. White marker at belt."""
    g = copy.deepcopy(grid)
    if frame == 1:
        set_px(g, 13, 14, 'W'); set_px(g, 14, 14, 'W')
        set_px(g, 15, 14, 'W')
    return g


def gen_hurt(grid):
    """Hurt: recolor all armor to red."""
    g = copy.deepcopy(grid)
    g = recolor(g, 'A', 'H')
    g = recolor(g, 'a', 'H')
    g = recolor(g, 'd', 'H')
    g = recolor(g, 'U', 'H')
    g = recolor(g, 's', 'H')
    return g


def gen_dead(grid, frame):
    """Dead: 3 frames (slump, kneel, lie)."""
    if frame == 0:
        g = copy.deepcopy(grid)
        set_px(g, 13, 0, 'O'); set_px(g, 14, 0, 'O')
        set_px(g, 15, 0, '.'); set_px(g, 16, 0, '.')
        return g
    elif frame == 1:
        # Kneeling: shift body down 8 rows
        g = [['.' for _ in range(SPRITE_SIZE)] for _ in range(SPRITE_SIZE)]
        for y in range(24):
            for x in range(SPRITE_SIZE):
                if get_px(grid, x, y) != '.':
                    if y + 8 < SPRITE_SIZE:
                        g[y + 8][x] = get_px(grid, x, y)
        return g
    else:
        # Lying flat: rotate 90 degrees
        g = [['.' for _ in range(SPRITE_SIZE)] for _ in range(SPRITE_SIZE)]
        for y in range(SPRITE_SIZE):
            for x in range(SPRITE_SIZE):
                px = get_px(grid, x, y)
                if px != '.':
                    nx = y + 2
                    ny = 16 + (x // 8) * 2
                    if nx < SPRITE_SIZE and ny < SPRITE_SIZE:
                        g[ny][nx] = px
        return g


# ============ MAIN ============

def main():
    sprite_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sprites_json')

    # Load 32x32 base sprites
    bases = {}
    for direction in ['front', 'right', 'back']:
        path = os.path.join(sprite_dir, f'{direction}_idle32.json')
        with open(path) as f:
            data = json.load(f)
        bases[direction] = json_to_grid(data)
    bases['left'] = mirror_grid(bases['right'])

    # Generate all states
    all_data = {}
    for direction in ['front', 'right', 'back', 'left']:
        base = bases[direction]
        dir_states = {
            'idle': [gen_idle_b(base), gen_idle_b(base)],
            'walk': [gen_walk(base, 0), gen_walk(base, 1), gen_walk(base, 2), gen_walk(base, 3)],
            'sprint': [gen_sprint(base, 0), gen_sprint(base, 1)],
            'shoot': [gen_shoot(base, 0), gen_shoot(base, 1)],
            'reload': [gen_reload(base, 0), gen_reload(base, 1), gen_reload(base, 2)],
            'hurt': [gen_hurt(base)],
            'dead': [gen_dead(base, 0), gen_dead(base, 1), gen_dead(base, 2)],
        }
        for state, grids in dir_states.items():
            frames = [grid_to_json(g) for g in grids]
            all_data[f'{direction}_{state}'] = frames

    out_json = os.path.join(sprite_dir, 'all_sprites.json')
    with open(out_json, 'w') as f:
        json.dump(all_data, f)
    print(f"Generated {len(all_data)} sprite states -> {out_json}")


if __name__ == '__main__':
    main()
