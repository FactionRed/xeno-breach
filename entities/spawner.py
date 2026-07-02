"""Wave director — spawns enemies in escalating waves from crater locations.

Wave composition scales with wave number:
  Wave 1-3:   Drones only
  Wave 4-6:   Drones + Runners
  Wave 7-9:   Drones + Runners + Spitters
  Wave 10+:   All types + Brutes
  Every 5th wave: Heavier mix
"""
import math
import random
import time
import numpy as np

from entities.enemy_types import create_enemy
from entities.enemy_mods import maybe_roll_elite
from config import WORLD_W, WORLD_H, TERRAIN_SCALE


class WaveDirector:
    def __init__(self, terrain):
        self.terrain = terrain
        self.wave_number = 0
        self.enemies = []
        self.spawn_timer = 0.0
        self.wave_active = False
        self.breather_timer = 3.0  # initial delay before first wave
        self.in_breather = True
        self.to_spawn = 0
        self.spawn_interval = 1.5

        # Find crater spawn points (low elevation areas)
        self._find_spawn_points()

    def _find_spawn_points(self):
        """Find low-elevation grid points far from center for spawn locations."""
        h = self.terrain.heightmap
        size = h.shape[0]
        # Find local minima (crater bottoms)
        # Sample a grid of candidate points
        candidates = []
        step = 32
        for y in range(0, size, step):
            for x in range(0, size, step):
                # Check if this is a local minimum in a small window
                y0, y1 = max(0, y - step), min(size, y + step + 1)
                x0, x1 = max(0, x - step), min(size, x + step + 1)
                sub = h[y0:y1, x0:x1]
                if h[y, x] <= sub.min() + 0.01 and h[y, x] < -0.05:
                    candidates.append((x * TERRAIN_SCALE, y * TERRAIN_SCALE))
        # Fallback: random edge points
        if len(candidates) < 5:
            for _ in range(20):
                candidates.append((
                    random.uniform(50, WORLD_W - 50),
                    random.uniform(50, WORLD_H - 50),
                ))
        self.spawn_points = candidates

    def update(self, dt, player):
        """Update wave logic, spawn enemies, return list of active enemies."""
        if self.in_breather:
            self.breather_timer -= dt
            if self.breather_timer <= 0:
                self._start_wave()
        elif self.wave_active:
            # Spawn enemies
            if self.to_spawn > 0:
                self.spawn_timer -= dt
                if self.spawn_timer <= 0:
                    self._spawn_enemy(player)
                    self.to_spawn -= 1
                    self.spawn_timer = self.spawn_interval

            # Check if wave is cleared
            alive = [e for e in self.enemies if not e.dead]
            if self.to_spawn == 0 and len(alive) == 0:
                self.wave_active = False
                self.in_breather = True
                self.breather_timer = max(3.0, 8.0 - self.wave_number * 0.5)

        # Update all enemies
        for e in self.enemies:
            e.update(dt, player, self.terrain, self.enemies)

        # Remove fully dead enemies (death anim done) — but keep for acid pool spawn
        new_enemies = []
        for e in self.enemies:
            if e.dead and not e.spawn_acid:
                continue  # fully removed
            new_enemies.append(e)
        self.enemies = new_enemies

        return self.enemies

    def _start_wave(self):
        self.wave_number += 1
        n = 5 + 3 * self.wave_number
        self.to_spawn = n
        self.spawn_interval = max(0.4, 1.5 - 0.08 * self.wave_number)
        self.wave_active = True
        self.in_breather = False
        self.spawn_timer = 0.0
        print(f"[wave] Wave {self.wave_number} starting — {n} enemies")

    def _spawn_enemy(self, player):
        # Pick spawn point far from player
        best = None
        best_dist = 0
        for _ in range(10):
            sp = random.choice(self.spawn_points)
            dx = sp[0] - player.x
            dy = sp[1] - player.y
            d = math.sqrt(dx * dx + dy * dy)
            if d > best_dist and d > 300:
                best_dist = d
                best = sp
        if best is None:
            for _ in range(20):
                x = random.uniform(50, WORLD_W - 50)
                y = random.uniform(50, WORLD_H - 50)
                dx = x - player.x
                dy = y - player.y
                if math.sqrt(dx * dx + dy * dy) > 250:
                    best = (x, y)
                    break
        if best is None:
            best = (0, 0)

        # Pick enemy type based on wave number
        enemy_type = self._pick_enemy_type()

        hp_mult = 1.0 + 0.08 * self.wave_number
        spd_mult = 1.0 + 0.04 * self.wave_number
        enemy = create_enemy(enemy_type, best[0], best[1],
                            hp_mult=hp_mult, speed_mult=spd_mult)

        # Roll for elite (5% chance)
        maybe_roll_elite(enemy, chance=0.05)

        self.enemies.append(enemy)

    def _pick_enemy_type(self):
        """Determine enemy type based on wave number."""
        w = self.wave_number
        # Build weighted pool based on wave progression
        pool = ['drone'] * 10  # base weight

        if w >= 4:
            pool += ['runner'] * min(4, w - 3)
        if w >= 7:
            pool += ['spitter'] * min(3, w - 6)
        if w >= 10:
            pool += ['brute'] * min(2, (w - 9) // 2)

        # Every 5th wave: add extra variety
        if w % 5 == 0:
            pool += ['runner'] * 3
            pool += ['brute'] * 2

        return random.choice(pool)

    def get_wave_info(self):
        alive = sum(1 for e in self.enemies if not e.dead)
        remaining = self.to_spawn + alive
        return {
            'wave': self.wave_number,
            'remaining': remaining,
            'breather': self.in_breather,
            'breather_time': max(0, self.breather_timer),
        }
