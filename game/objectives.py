"""Objective system — mission types + extraction beacon.

Objective types:
  SURVIVE:  Live for N seconds against waves
  REACH:    Get to a beacon marker across the terrain
  DEFEND:   Protect a downed shuttle section for a timer
  SCAVENGE: Collect N supply crates scattered across terrain

Each objective tracks progress and triggers extraction when complete.
"""
import math
import random
import pygame
import numpy as np

from config import (WORLD_W, WORLD_H, TERRAIN_SCALE,
                    ADRENALINE, WARNING, ON_PRIMARY, ON_SECONDARY,
                    DANGER, ACID, CONSOLE, HULL_BLACK)


class Objective:
    """Base objective."""
    OBJ_TYPE = 'base'

    def __init__(self, name, description):
        self.name = name
        self.description = description
        self.progress = 0.0
        self.target = 1.0
        self.complete = False
        self.failed = False

    @property
    def progress_pct(self):
        return min(1.0, self.progress / self.target) if self.target > 0 else 0

    def update(self, dt, player, wave_director, terrain):
        """Override in subclass."""
        pass

    def get_markers(self):
        """Return list of (world_x, world_y, color, label) markers to draw on minimap."""
        return []


class SurviveObjective(Objective):
    """Survive for N seconds."""
    OBJ_TYPE = 'survive'

    def __init__(self, duration=120.0):
        super().__init__(
            f"SURVIVE {int(duration)}s",
            f"Hold position and survive for {int(duration)} seconds."
        )
        self.target = duration
        self.progress = 0.0

    def update(self, dt, player, wave_director, terrain):
        if self.complete:
            return
        self.progress += dt
        if self.progress >= self.target:
            self.progress = self.target
            self.complete = True


class ReachObjective(Objective):
    """Reach a beacon marker."""
    OBJ_TYPE = 'reach'

    def __init__(self, beacon_x, beacon_y):
        super().__init__(
            "REACH BEACON",
            "Navigate to the extraction beacon."
        )
        self.beacon_x = beacon_x
        self.beacon_y = beacon_y
        self.target = 1.0
        self.arrival_radius = 40

    def update(self, dt, player, wave_director, terrain):
        if self.complete:
            return
        dx = player.x - self.beacon_x
        dy = player.y - self.beacon_y
        dist = math.sqrt(dx * dx + dy * dy)
        if dist < self.arrival_radius:
            self.complete = True
            self.progress = 1.0
        else:
            # Progress = inverse of distance (for display)
            max_dist = math.sqrt(WORLD_W ** 2 + WORLD_H ** 2)
            self.progress = 1.0 - min(1.0, dist / max_dist)

    def get_markers(self):
        return [(self.beacon_x, self.beacon_y, ADRENALINE, "BEACON")]


class DefendObjective(Objective):
    """Defend a downed shuttle for N seconds."""
    OBJ_TYPE = 'defend'

    def __init__(self, shuttle_x, shuttle_y, duration=90.0):
        super().__init__(
            f"DEFEND SHUTTLE {int(duration)}s",
            f"Protect the downed shuttle at the crash site."
        )
        self.shuttle_x = shuttle_x
        self.shuttle_y = shuttle_y
        self.target = duration
        self.progress = 0.0
        self.shuttle_hp = 100.0
        self.shuttle_max_hp = 100.0
        self.arrival_radius = 150

    def update(self, dt, player, wave_director, terrain):
        if self.complete:
            return
        self.progress += dt
        if self.progress >= self.target:
            self.progress = self.target
            self.complete = True

    def get_markers(self):
        return [(self.shuttle_x, self.shuttle_y, WARNING, "SHUTTLE")]


class ScavengeObjective(Objective):
    """Collect N supply crates."""
    OBJ_TYPE = 'scavenge'

    def __init__(self, crate_positions):
        super().__init__(
            f"SCAVENGE {len(crate_positions)} CRATES",
            "Collect supply crates scattered across the terrain."
        )
        self.crates = [{'x': x, 'y': y, 'collected': False} for x, y in crate_positions]
        self.target = len(self.crates)
        self.progress = 0

    def update(self, dt, player, wave_director, terrain):
        if self.complete:
            return
        for crate in self.crates:
            if crate['collected']:
                continue
            dx = player.x - crate['x']
            dy = player.y - crate['y']
            if dx * dx + dy * dy < 25 * 25:
                crate['collected'] = True
                self.progress += 1
        if self.progress >= self.target:
            self.complete = True

    def get_markers(self):
        return [(c['x'], c['y'], ADRENALINE, "CRATE") for c in self.crates if not c['collected']]


class ExtractionBeacon:
    """Extraction beacon — player must reach and hold for extraction."""

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.active = False
        self.hold_time = 0.0
        self.hold_required = 10.0
        self.hold_radius = 50
        self.complete = False
        self.pulse_timer = 0.0

    def activate(self):
        self.active = True

    def update(self, dt, player):
        self.pulse_timer += dt
        if not self.active or self.complete:
            return
        dx = player.x - self.x
        dy = player.y - self.y
        dist = math.sqrt(dx * dx + dy * dy)
        if dist < self.hold_radius:
            self.hold_time += dt
        else:
            self.hold_time = max(0, self.hold_time - dt * 0.5)  # slow decay
        if self.hold_time >= self.hold_required:
            self.complete = True

    @property
    def hold_pct(self):
        return self.hold_time / self.hold_required

    def draw(self, screen, cam_x, cam_y):
        if not self.active:
            return
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y)
        # Pulsing beacon
        pulse = (math.sin(self.pulse_timer * 4) + 1) * 0.5
        r = int(15 + pulse * 8)
        # Glow
        glow = pygame.Surface((r * 4, r * 4), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*ADRENALINE, int(60 * pulse)), (r * 2, r * 2), r * 2)
        pygame.draw.circle(glow, (*ADRENALINE, int(120 * pulse)), (r * 2, r * 2), r)
        pygame.draw.circle(glow, ON_PRIMARY, (r * 2, r * 2), int(r * 0.4))
        screen.blit(glow, (sx - r * 2, sy - r * 2))
        # Hold radius
        pygame.draw.circle(screen, ADRENALINE, (sx, sy), self.hold_radius, 1)
        # Hold progress
        if self.hold_time > 0:
            arc_r = self.hold_radius + 5
            pygame.draw.arc(screen, ADRENALINE,
                          (sx - arc_r, sy - arc_r, arc_r * 2, arc_r * 2),
                          -math.pi / 2, -math.pi / 2 + self.hold_pct * math.tau, 3)


def generate_objective(wave_number, terrain, player):
    """Generate an objective based on wave number."""
    rng = random.Random(wave_number * 42 + 7)
    h = terrain.heightmap
    size = h.shape[0]

    def random_far_point(min_dist=300):
        for _ in range(50):
            gx = rng.randint(0, size - 1)
            gy = rng.randint(0, size - 1)
            wx = gx * TERRAIN_SCALE
            wy = gy * TERRAIN_SCALE
            dx = wx - player.x
            dy = wy - player.y
            if dx * dx + dy * dy > min_dist * min_dist:
                return (wx, wy)
        return (WORLD_W / 2 + rng.uniform(-200, 200),
                WORLD_H / 2 + rng.uniform(-200, 200))

    obj_types = ['survive', 'reach', 'defend', 'scavenge']
    obj_type = obj_types[wave_number % len(obj_types)]

    if obj_type == 'survive':
        return SurviveObjective(duration=60.0 + wave_number * 15)
    elif obj_type == 'reach':
        x, y = random_far_point(400)
        return ReachObjective(x, y)
    elif obj_type == 'defend':
        x, y = random_far_point(200)
        return DefendObjective(x, y, duration=45.0 + wave_number * 10)
    else:  # scavenge
        positions = [random_far_point(200) for _ in range(3 + wave_number)]
        return ScavengeObjective(positions)
