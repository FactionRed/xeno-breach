"""Motion tracker — Aliens-style circular radar.

Detects enemies within range and displays them as blips:
  - Green blip (acid): ambient contact, >30 units, has line-of-sight
  - Red blip (danger): hostile contact, <30 units, ignores terrain

Includes a rotating ping sweep line and static noise effect.
"""
import math
import random
import pygame
import numpy as np

from config import (SCREEN_WIDTH, SCREEN_HEIGHT,
                    ACID, DANGER, ON_PRIMARY, ON_SECONDARY,
                    CONSOLE, HULL_BLACK, BULKHEAD)

TRACKER_SIZE = 140
TRACKER_RANGE = 400  # world units detected
PING_PERIOD = 2.0    # seconds per sweep


class MotionTracker:
    def __init__(self):
        self.x = SCREEN_WIDTH - TRACKER_SIZE - 16
        self.y = 50  # top-right, below the kill counter
        self.size = TRACKER_SIZE
        self.center = (self.x + self.size // 2, self.y + self.size // 2)
        self.radius = self.size // 2 - 4
        self.ping_angle = 0.0
        self.blips = []  # list of {rel_x, rel_y, hostile, life}
        self.static_noise = 0.0

    def update(self, dt, player, enemies, terrain):
        """Update ping sweep and detect enemies."""
        self.ping_angle += dt * (math.tau / PING_PERIOD)
        if self.ping_angle > math.tau:
            self.ping_angle -= math.tau

        # Detect enemies
        self.blips.clear()
        for e in enemies:
            if e.dead or e.state == 'death':
                continue
            dx = e.x - player.x
            dy = e.y - player.y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist > TRACKER_RANGE:
                continue

            # Normalize to tracker circle
            scale = (dist / TRACKER_RANGE) * self.radius
            ang = math.atan2(dy, dx)
            rel_x = math.cos(ang) * scale
            rel_y = math.sin(ang) * scale

            hostile = dist < 150 or e.state in ('lunge', 'attack')
            self.blips.append({
                'rel_x': rel_x,
                'rel_y': rel_y,
                'hostile': hostile,
                'dist': dist,
                'angle': ang,
            })

        # Random static (increases when many enemies near)
        near = sum(1 for b in self.blips if b['dist'] < 100)
        self.static_noise = min(0.4, near * 0.08)

    def draw(self, screen):
        """Draw the motion tracker."""
        cx, cy = self.center

        # Background disc
        tracker_surf = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        tc = self.size // 2
        pygame.draw.circle(tracker_surf, (*HULL_BLACK, 200), (tc, tc), self.radius)
        pygame.draw.circle(tracker_surf, (*CONSOLE, 100), (tc, tc), self.radius, 1)

        # Range rings
        for r_frac in (0.33, 0.66, 1.0):
            r = int(self.radius * r_frac)
            pygame.draw.circle(tracker_surf, (*ON_SECONDARY, 40), (tc, tc), r, 1)

        # Crosshairs
        pygame.draw.line(tracker_surf, (*ON_SECONDARY, 30),
                        (tc - self.radius, tc), (tc + self.radius, tc), 1)
        pygame.draw.line(tracker_surf, (*ON_SECONDARY, 30),
                        (tc, tc - self.radius), (tc, tc + self.radius), 1)

        # Ping sweep line
        sweep_x = tc + math.cos(self.ping_angle) * self.radius
        sweep_y = tc + math.sin(self.ping_angle) * self.radius
        # Sweep trail (fading wedge)
        for i in range(12):
            trail_ang = self.ping_angle - i * 0.05
            tx = tc + math.cos(trail_ang) * self.radius
            ty = tc + math.sin(trail_ang) * self.radius
            alpha = int(60 * (1 - i / 12))
            pygame.draw.line(tracker_surf, (*ACID, alpha), (tc, tc), (tx, ty), 1)
        pygame.draw.line(tracker_surf, ACID, (tc, tc), (sweep_x, sweep_y), 2)

        # Blips
        for blip in self.blips:
            bx = tc + blip['rel_x']
            by = tc + blip['rel_y']
            if blip['hostile']:
                pygame.draw.circle(tracker_surf, DANGER, (int(bx), int(by)), 4)
                pygame.draw.circle(tracker_surf, (255, 255, 255), (int(bx), int(by)), 4, 1)
            else:
                pygame.draw.circle(tracker_surf, ACID, (int(bx), int(by)), 3)

        # Static noise (random dots)
        if self.static_noise > 0:
            for _ in range(int(self.static_noise * 30)):
                nx = random.randint(tc - self.radius, tc + self.radius)
                ny = random.randint(tc - self.radius, tc + self.radius)
                if (nx - tc) ** 2 + (ny - tc) ** 2 < self.radius ** 2:
                    tracker_surf.set_at((nx, ny), (*ON_PRIMARY, 80))

        # Border ring
        pygame.draw.circle(tracker_surf, ON_SECONDARY, (tc, tc), self.radius, 2)

        screen.blit(tracker_surf, (self.x, self.y))

        # Label
        font = pygame.font.SysFont("Consolas", 11)
        label = font.render("MOTION TRACKER", True, ON_SECONDARY)
        screen.blit(label, (self.x, self.y - 16))
