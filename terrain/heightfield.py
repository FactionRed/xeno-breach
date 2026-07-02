"""Terrain heightfield generation — adapted from planet_generator.py.

Samples 3D simplex noise on a 2D plane (z=SEED_OFFSET) instead of the unit
sphere, giving fast, seamless terrain for a game level.  Reuses the same fBm,
crater, and 5-tier elevation coloring pipeline.
"""
import numpy as np
from noise import snoise3

_snoise3_vec = np.vectorize(snoise3, otypes=[np.float64])


def generate_heightmap(size, noise_scale, octaves, persistence, lacunarity,
                       seed_offset):
    """Generate a (size, size) heightmap in roughly [-1, 1].

    Uses 3D simplex noise with z = seed_offset so each planet (different
    seed_offset) gets unique terrain.  The noise library's built-in multi-octave
    fBm is used directly — much faster than a Python loop.
    """
    coords = np.linspace(0, size * noise_scale, size)
    xx, yy = np.meshgrid(coords, coords)
    zz = np.full_like(xx, seed_offset)
    h = _snoise3_vec(xx, yy, zz,
                     octaves=octaves,
                     persistence=persistence,
                     lacunarity=lacunarity)
    return h.astype(np.float32)


def add_craters(h, count, max_depth, min_r, max_r, seed):
    """Stamp impact craters: bowl depression + raised rim."""
    rng = np.random.default_rng(seed + 999)
    size = h.shape[0]
    placed = 0
    for _ in range(count * 5):
        if placed >= count:
            break
        cx = rng.integers(0, size)
        cy = rng.integers(0, size)
        radius = rng.uniform(min_r, max_r)
        depth = rng.uniform(max_depth * 0.6, max_depth)

        # bounding box for this crater
        r_int = int(radius * 1.3) + 1
        y0, y1 = max(0, cy - r_int), min(size, cy + r_int + 1)
        x0, x1 = max(0, cx - r_int), min(size, cx + r_int + 1)
        if y1 - y0 < 4 or x1 - x0 < 4:
            continue

        ys, xs = np.mgrid[y0:y1, x0:x1]
        dist = np.sqrt((xs - cx) ** 2 + (ys - cy) ** 2)

        # bowl interior
        mask = dist < radius
        if mask.sum() < 4:
            continue
        t = dist[mask] / radius
        h_sub = h[y0:y1, x0:x1]
        h_sub[mask] -= depth * (1.0 - t * t)

        # raised rim
        rim = (dist >= radius) & (dist < radius * 1.25)
        if rim.any():
            rt = (dist[rim] - radius) / (radius * 0.25)
            h_sub[rim] += 0.45 * depth * (1.0 - rt) * np.sin(
                np.clip(rt, 0, 1) * np.pi
            )
        placed += 1
    return h


def compute_normals(h, cell_size=1.0):
    """Compute per-cell surface normals from the heightfield gradient.

    Returns (size, size, 3) float32 array of unit normals.
    """
    gy, gx = np.gradient(h, cell_size)
    # Normal = (-dg/dx, -dg/dy, 1) normalized
    nz = np.ones_like(h)
    nx = -gx
    ny = -gy
    norm = np.sqrt(nx ** 2 + ny ** 2 + nz ** 2)
    nx /= norm
    ny /= norm
    nz /= norm
    return np.stack([nx, ny, nz], axis=-1).astype(np.float32)


def colorize_terrain(h):
    """5-tier elevation-based coloring (from planet_generator.py palette).

    Returns (size, size, 3) float32 RGB in [0, 1].
    """
    hmin, hmax = h.min(), h.max()
    he = (h - hmin) / (hmax - hmin + 1e-9)   # 0..1

    deep    = np.array([0.10, 0.08, 0.07])
    lowland = np.array([0.34, 0.26, 0.19])
    rock    = np.array([0.55, 0.45, 0.35])
    high    = np.array([0.66, 0.58, 0.50])
    snow    = np.array([0.97, 0.98, 1.00])

    def band(lo, hi, c_a, c_b):
        mask = (he >= lo) & (he < hi)
        t = np.clip((he - lo) / (hi - lo), 0, 1)
        return (c_a[None, None, :] * (1 - t[:, :, None]) +
                c_b[None, None, :] * t[:, :, None]) * mask[:, :, None]

    rgb = (band(-0.01, 0.25, deep, lowland) +
           band(0.25, 0.55, lowland, rock) +
           band(0.55, 0.80, rock, high) +
           band(0.80, 1.01, high, snow))
    return rgb.astype(np.float32)


def shade_terrain(rgb, normals, light_dir, ambient):
    """Apply Lambert shading to the terrain.

    Returns (size, size, 3) float32 shaded RGB in [0, 1].
    """
    ndotl = (normals[..., 0] * light_dir[0] +
             normals[..., 1] * light_dir[1] +
             normals[..., 2] * light_dir[2])
    diff = np.clip(ndotl, 0.0, 1.0)
    shade = ambient + (1.0 - ambient) * diff
    shaded = rgb * shade[:, :, None]
    return np.clip(shaded, 0, 1).astype(np.float32)


def height_at(h, gx, gy):
    """Bilinearly sample the heightmap at fractional grid coords."""
    size = h.shape[0]
    gx = np.clip(gx, 0, size - 1.001)
    gy = np.clip(gy, 0, size - 1.001)
    x0, y0 = int(gx), int(gy)
    fx, fy = gx - x0, gy - y0
    h00 = h[y0, x0]
    h10 = h[y0, x0 + 1]
    h01 = h[y0 + 1, x0]
    h11 = h[y0 + 1, x0 + 1]
    return (h00 * (1 - fx) * (1 - fy) + h10 * fx * (1 - fy) +
            h01 * (1 - fx) * fy + h11 * fx * fy)


def slope_at(h, gx, gy):
    """Approximate slope magnitude at fractional grid coords."""
    eps = 1.0
    h_c = height_at(h, gx, gy)
    h_x = height_at(h, gx + eps, gy)
    h_y = height_at(h, gx, gy + eps)
    dh_dx = (h_x - h_c) / eps
    dh_dy = (h_y - h_c) / eps
    return np.sqrt(dh_dx ** 2 + dh_dy ** 2)
