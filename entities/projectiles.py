"""Projectile system — hitscan tracers, flamethrower cones, lingering fire zones."""
import math
import random
import pygame


class Tracer:
    """A visible tracer line from a fired shot."""
    def __init__(self, x1, y1, x2, y2, color, life=0.08):
        self.x1, self.y1 = x1, y1
        self.x2, self.y2 = x2, y2
        self.color = color
        self.life = life
        self.max_life = life

    def update(self, dt):
        self.life -= dt

    def draw(self, screen, cam_x, cam_y):
        alpha = max(0, self.life / self.max_life)
        c = self.color
        col = (int(c[0] * alpha), int(c[1] * alpha), int(c[2] * alpha))
        w = max(1, int(3 * alpha))
        pygame.draw.line(screen, col,
                         (int(self.x1 - cam_x), int(self.y1 - cam_y)),
                         (int(self.x2 - cam_x), int(self.y2 - cam_y)), w)


class FireZone:
    """Lingering flamethrower area — damages enemies that stand in it."""
    def __init__(self, x, y, radius, damage_per_sec, life=0.5):
        self.x = x
        self.y = y
        self.radius = radius
        self.dps = damage_per_sec
        self.life = life
        self.max_life = life

    def update(self, dt):
        self.life -= dt

    def contains(self, x, y):
        dx = x - self.x
        dy = y - self.y
        return dx * dx + dy * dy <= self.radius * self.radius

    def draw(self, screen, cam_x, cam_y):
        alpha = max(0, self.life / self.max_life)
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y)
        r = int(self.radius * (0.7 + 0.3 * random.random()))
        # Outer glow
        glow = pygame.Surface((r * 2 + 4, r * 2 + 4), pygame.SRCALPHA)
        pygame.draw.circle(glow, (255, 65, 54, int(80 * alpha)), (r + 2, r + 2), r)
        pygame.draw.circle(glow, (255, 180, 84, int(120 * alpha)), (r + 2, r + 2), int(r * 0.6))
        screen.blit(glow, (sx - r - 2, sy - r - 2))


class ProjectileSystem:
    def __init__(self):
        self.tracers = []
        self.fire_zones = []

    def add_tracer(self, x1, y1, x2, y2, color, life=0.08):
        self.tracers.append(Tracer(x1, y1, x2, y2, color, life))

    def add_fire_zone(self, x, y, radius, dps, life=0.5):
        self.fire_zones.append(FireZone(x, y, radius, dps, life))

    def update(self, dt):
        for t in self.tracers:
            t.update(dt)
        for f in self.fire_zones:
            f.update(dt)
        self.tracers = [t for t in self.tracers if t.life > 0]
        self.fire_zones = [f for f in self.fire_zones if f.life > 0]

    def draw(self, screen, cam_x, cam_y):
        for f in self.fire_zones:
            f.draw(screen, cam_x, cam_y)
        for t in self.tracers:
            t.draw(screen, cam_x, cam_y)

    def clear(self):
        self.tracers.clear()
        self.fire_zones.clear()
