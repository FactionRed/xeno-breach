"""Weapon system — data-driven from stats, handles fire/reload/switch logic."""
import math
import time


class Weapon:
    def __init__(self, name, stats):
        self.name = name
        self.damage = stats['damage']
        self.fire_rate = stats['fire_rate']       # ms between shots
        self.mag_size = stats['mag_size']
        self.range = stats['range']               # pixels
        self.spread = math.radians(stats['spread'])  # degrees -> radians
        self.pellets = stats.get('pellets', 1)
        self.tracer_color = tuple(stats['tracer_color'])
        self.muzzle_flash = stats.get('muzzle_flash', True)
        self.area_denial = stats.get('area_denial', False)
        self.reload_time = stats.get('reload_time', 1.5)  # seconds
        self.ammo = self.mag_size
        self.last_fired = 0.0
        self.reloading = False
        self.reload_start = 0.0

    def can_fire(self):
        if self.reloading:
            return False
        if self.ammo <= 0:
            return False
        now = time.monotonic() * 1000
        return (now - self.last_fired) >= self.fire_rate

    def fire(self):
        """Fire one shot. Returns list of (angle_offset) for each pellet."""
        if not self.can_fire():
            return None
        self.last_fired = time.monotonic() * 1000
        self.ammo -= 1
        import random
        angles = []
        for _ in range(self.pellets):
            offset = random.uniform(-self.spread, self.spread)
            angles.append(offset)
        return angles

    def start_reload(self):
        if self.reloading or self.ammo >= self.mag_size:
            return False
        self.reloading = True
        self.reload_start = time.monotonic()
        return True

    def update(self):
        if self.reloading:
            if time.monotonic() - self.reload_start >= self.reload_time:
                self.ammo = self.mag_size
                self.reloading = False

    def ammo_pct(self):
        return self.ammo / self.mag_size


# Weapon definitions (from IMPLEMENTATION_PLAN.md)
WEAPON_STATS = {
    'pulse_rifle': {
        'damage': 22, 'fire_rate': 100, 'mag_size': 30,
        'range': 800, 'spread': 2.0, 'pellets': 1,
        'tracer_color': [255, 180, 84],
        'muzzle_flash': True,
        'reload_time': 1.5,
    },
    'shotgun': {
        'damage': 14, 'fire_rate': 550, 'mag_size': 8,
        'range': 450, 'spread': 11, 'pellets': 6,
        'tracer_color': [255, 65, 54],
        'muzzle_flash': True,
        'reload_time': 2.0,
    },
    'flamethrower': {
        'damage': 10, 'fire_rate': 70, 'mag_size': 100,
        'range': 320, 'spread': 22, 'pellets': 1,
        'tracer_color': [255, 120, 40],
        'muzzle_flash': False,
        'area_denial': True,
        'reload_time': 2.5,
    },
}

WEAPON_ORDER = ['pulse_rifle', 'shotgun', 'flamethrower']


class WeaponSystem:
    """Manages weapon inventory, switching, and current weapon state."""
    def __init__(self):
        self.weapons = {}
        for name in WEAPON_ORDER:
            self.weapons[name] = Weapon(name, WEAPON_STATS[name])
        self.current_idx = 0
        self.current_name = WEAPON_ORDER[0]

    @property
    def current(self):
        return self.weapons[self.current_name]

    def switch_to(self, idx):
        if 0 <= idx < len(WEAPON_ORDER):
            self.current_idx = idx
            self.current_name = WEAPON_ORDER[idx]
            return True
        return False

    def switch_by_key(self, key):
        """Switch weapon by number key 1-3."""
        idx_map = {pygame.K_1: 0, pygame.K_2: 1, pygame.K_3: 2}
        import pygame
        if key in idx_map:
            return self.switch_to(idx_map[key])
        return False

    def update(self):
        for w in self.weapons.values():
            w.update()
