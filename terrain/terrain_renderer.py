"""Terrain renderer — converts a heightfield into a shaded pygame surface.

Generates the full terrain once at startup, creates a scaled pygame surface,
and provides fast per-frame blitting with camera offset. Includes procedural
texture overlays (noise detail, cracks, rock speckling) for visual richness.
"""
import numpy as np
import pygame
import random
import math

from config import (TERRAIN_SIZE, TERRAIN_SCALE, WORLD_W, WORLD_H,
                    NOISE_SCALE, OCTAVES, PERSISTENCE, LACUNARITY,
                    SEED_OFFSET, HEIGHT_AMP, CRATER_COUNT, CRATER_MAX_DEPTH,
                    CRATER_MIN_RADIUS, CRATER_MAX_RADIUS,
                    LIGHT_DIR, AMBIENT, HULL_BLACK)
from terrain.heightfield import (generate_heightmap, add_craters,
                                 compute_normals, colorize_terrain,
                                 shade_terrain, height_at, slope_at)


class TerrainRenderer:
    """Owns the terrain heightmap and the pre-rendered world surface."""

    def __init__(self, seed=0):
        print(f"[terrain] Generating {TERRAIN_SIZE}x{TERRAIN_SIZE} heightmap...")
        h = generate_heightmap(TERRAIN_SIZE, NOISE_SCALE, OCTAVES,
                               PERSISTENCE, LACUNARITY, SEED_OFFSET + seed)
        h *= HEIGHT_AMP
        print(f"[terrain] Adding {CRATER_COUNT} craters...")
        h = add_craters(h, CRATER_COUNT, CRATER_MAX_DEPTH,
                        CRATER_MIN_RADIUS, CRATER_MAX_RADIUS,
                        int(SEED_OFFSET) + seed)
        print(f"[terrain] Height range: [{h.min():.4f}, {h.max():.4f}]")

        self.heightmap = h

        print("[terrain] Computing normals...")
        normals = compute_normals(h, cell_size=1.0)

        print("[terrain] Colorizing...")
        rgb = colorize_terrain(h)

        print("[terrain] Shading...")
        shaded = shade_terrain(rgb, normals, LIGHT_DIR, AMBIENT)

        # Procedural texture overlay: fine noise speckling
        print("[terrain] Adding texture detail...")
        rng = np.random.RandomState(int(SEED_OFFSET) + seed)
        noise_detail = rng.randn(TERRAIN_SIZE, TERRAIN_SIZE) * 0.04
        # Higher-frequency noise for rock speckle
        speckle = rng.rand(TERRAIN_SIZE, TERRAIN_SIZE)
        speckle = (speckle > 0.97).astype(np.float32) * 0.15  # bright spots
        # Dark cracks in low areas
        crack_mask = (h < -0.05).astype(np.float32) * (rng.rand(TERRAIN_SIZE, TERRAIN_SIZE) > 0.98) * 0.2

        shaded += noise_detail[:, :, None] + speckle[:, :, None] - crack_mask[:, :, None]
        shaded = np.clip(shaded, 0, 1)

        # Convert to pygame surface at grid resolution
        arr_uint8 = (shaded * 255).clip(0, 255).astype(np.uint8)
        arr_t = np.transpose(arr_uint8, (1, 0, 2))
        grid_surface = pygame.surfarray.make_surface(arr_t)

        # Scale up to world resolution
        print(f"[terrain] Scaling to {WORLD_W}x{WORLD_H}...")
        self.world_surface = pygame.transform.smoothscale(
            grid_surface, (WORLD_W, WORLD_H)
        )

        # Add procedural rock props
        self._add_rock_props(seed)

        # Build vignette overlay (atmospheric depth)
        self._build_vignette()

        print("[terrain] Ready.")

    def _add_rock_props(self, seed):
        """Draw procedural rocks and debris on the terrain surface."""
        rng = random.Random(int(SEED_OFFSET) + seed)
        rock_count = 80
        for _ in range(rock_count):
            x = rng.randint(20, WORLD_W - 20)
            y = rng.randint(20, WORLD_H - 20)
            # Only place on flat-ish ground (skip steep slopes)
            slope = self.get_slope(x, y)
            if slope > 0.2:
                continue
            size = rng.randint(4, 10)
            # Draw rock: dark base + lighter top (fake 3D)
            base_col = (40 + rng.randint(-10, 10), 35 + rng.randint(-8, 8), 30 + rng.randint(-5, 5))
            top_col = (min(255, base_col[0] + 30), min(255, base_col[1] + 25), min(255, base_col[2] + 20))
            # Shadow
            shadow_surf = pygame.Surface((size * 3, size * 2), pygame.SRCALPHA)
            pygame.draw.ellipse(shadow_surf, (0, 0, 0, 80), (0, 0, size * 3, size * 2))
            self.world_surface.blit(shadow_surf, (x - size + 1, y - size + 1))
            # Rock body
            pygame.draw.ellipse(self.world_surface, base_col, (x - size, y - size // 2, size * 2, size))
            pygame.draw.ellipse(self.world_surface, top_col, (x - size + 1, y - size // 2, size * 2 - 3, size - 3))
            pygame.draw.ellipse(self.world_surface, (20, 18, 15), (x - size, y - size // 2, size * 2, size), 1)

    def _build_vignette(self):
        """Build a radial vignette overlay for atmospheric depth."""
        vig = pygame.Surface((WORLD_W, WORLD_H), pygame.SRCALPHA)
        cx, cy = WORLD_W // 2, WORLD_H // 2
        max_dist = math.sqrt(cx * cx + cy * cy)
        # Draw concentric rings from center outward, increasing darkness
        steps = 20
        for i in range(steps):
            r = int(max_dist * (1 - i / steps))
            alpha = int(60 * (i / steps) ** 2)
            pygame.draw.circle(vig, (0, 0, 0, alpha), (cx, cy), r)
        self.vignette = vig

    def world_to_grid(self, world_x, world_y):
        return world_x / TERRAIN_SCALE, world_y / TERRAIN_SCALE

    def get_height(self, world_x, world_y):
        gx, gy = self.world_to_grid(world_x, world_y)
        return height_at(self.heightmap, gx, gy)

    def get_slope(self, world_x, world_y):
        gx, gy = self.world_to_grid(world_x, world_y)
        return slope_at(self.heightmap, gx, gy)

    def render(self, screen, cam_x, cam_y):
        """Blit the terrain surface with camera offset."""
        screen.blit(self.world_surface, (-cam_x, -cam_y))
