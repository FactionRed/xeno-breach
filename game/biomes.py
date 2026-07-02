"""Biome system — 4 planet biomes with palette + hazard modifiers.

Biomes adjust the terrain coloring, movement speed, visibility, and hazard
density based on the planet's latitude at the drop zone.

  BARREN:   Default — standard craters, low cover, fast movement
  POLAR:    Snow caps, fog (reduced vis), slower on ice, fewer craters
  CRATERED: Dense crater field, lots of cover, ambush-prone
  HIGHLAND: Elevated plateaus with cliffs, long sight lines
"""
import numpy as np
import random

from config import (TERRAIN_SCALE, NOISE_SCALE, OCTAVES, PERSISTENCE,
                    LACUNARITY, SEED_OFFSET, HEIGHT_AMP,
                    CRATER_COUNT, CRATER_MAX_DEPTH,
                    CRATER_MIN_RADIUS, CRATER_MAX_RADIUS,
                    PLAYER_SPEED, LIGHT_DIR, AMBIENT,
                    HULL_BLACK, ADRENALINE, DANGER, WARNING, ACID,
                    BIO_MASS, ON_PRIMARY, ON_SECONDARY, CONSOLE, BULKHEAD)
from terrain.heightfield import generate_heightmap, add_craters, compute_normals


class Biome:
    """Base biome definition."""
    name = "Barren"
    description = "Flat, cratered wasteland. Standard conditions."

    # Terrain params
    height_amp = HEIGHT_AMP
    crater_count = CRATER_COUNT
    crater_min_r = CRATER_MIN_RADIUS
    crater_max_r = CRATER_MAX_RADIUS
    noise_scale = NOISE_SCALE

    # Gameplay mods
    speed_mult = 1.0
    visibility = 1.0          # 1.0 = full, lower = fog
    fog_color = (80, 80, 90)
    fog_density = 0.0

    # Visual
    ambient = AMBIENT
    light_dir = LIGHT_DIR
    snow_amount = 0.0         # 0 = no snow, 1 = full snow
    tint = (1.0, 1.0, 1.0)    # color tint multiplier

    def apply_to_terrain(self, h, seed):
        """Apply biome-specific terrain modifications."""
        return h

    def apply_to_colors(self, rgb, h):
        """Apply biome-specific color modifications."""
        if self.snow_amount > 0:
            # Blend toward white at high elevations
            snow = np.array([0.97, 0.98, 1.00])
            he = (h - h.min()) / (h.max() - h.min() + 1e-9)
            snow_mask = np.clip((he - 0.4) * self.snow_amount, 0, 1)
            rgb = rgb * (1 - snow_mask[:, :, None]) + snow[None, None, :] * snow_mask[:, :, None]
        # Apply tint
        rgb = rgb * np.array(self.tint)
        return np.clip(rgb, 0, 1).astype(np.float32)


class BarrenBiome(Biome):
    name = "Barren Wasteland"
    description = "Flat, cratered wasteland. Standard combat conditions."
    speed_mult = 1.0
    visibility = 1.0


class PolarBiome(Biome):
    name = "Polar Ice Field"
    description = "Frozen surface with reduced visibility. Movement slowed on ice."
    height_amp = 0.10
    crater_count = 15
    speed_mult = 0.85
    visibility = 0.6
    fog_color = (180, 190, 200)
    fog_density = 0.35
    snow_amount = 0.6
    ambient = 0.45
    tint = (0.9, 0.95, 1.0)


class CrateredBiome(Biome):
    name = "Crater Field"
    description = "Dense impact craters provide cover but enable ambushes."
    height_amp = 0.18
    crater_count = 50
    crater_min_r = 8
    crater_max_r = 45
    speed_mult = 1.0
    visibility = 0.9
    tint = (1.0, 0.95, 0.85)


class HighlandBiome(Biome):
    name = "Highland Plateau"
    description = "Elevated terrain with cliffs. Long sight lines for rifles."
    height_amp = 0.25
    crater_count = 12
    noise_scale = NOISE_SCALE * 0.6
    speed_mult = 0.95
    visibility = 1.0
    ambient = 0.30
    tint = (1.0, 0.92, 0.80)


BIOMES = [BarrenBiome, PolarBiome, CrateredBiome, HighlandBiome]


def pick_biome(seed):
    """Pick a biome based on seed (deterministic per planet)."""
    rng = random.Random(seed)
    return rng.choice(BIOMES)()


def biome_from_latitude(lat_deg):
    """Pick biome from planet latitude (polar near poles, etc)."""
    abs_lat = abs(lat_deg)
    if abs_lat > 60:
        return PolarBiome()
    elif abs_lat > 30:
        return HighlandBiome()
    elif abs_lat > 10:
        return CrateredBiome()
    else:
        return BarrenBiome()
