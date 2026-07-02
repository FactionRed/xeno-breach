"""Player controller — movement with slope-based speed and crater wall collision."""
import math
import numpy as np
import pygame

from config import (PLAYER_SPEED, PLAYER_SPRINT_MULT, PLAYER_RADIUS,
                    MAX_SLOPE, SLOPE_SPEED_FALLOFF,
                    ADRENALINE, ON_PRIMARY, HULL_BLACK)


class Player:
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.vx = 0.0
        self.vy = 0.0
        self.facing = 0.0          # radians, 0 = right
        self.speed = PLAYER_SPEED
        self.radius = PLAYER_RADIUS
        self.health = 100.0
        self.max_health = 100.0
        self.sprinting = False
        self.footstep_timer = 0.0
        self.dust_particles = []

    def update(self, dt, keys, terrain, mouse_pos, screen_center):
        """Update player position based on input and terrain."""
        # Movement input
        dx, dy = 0.0, 0.0
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy -= 1.0
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy += 1.0
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx -= 1.0
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx += 1.0

        # Normalize diagonal
        mag = math.sqrt(dx * dx + dy * dy)
        if mag > 0:
            dx /= mag
            dy /= mag

        self.sprinting = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
        speed_mult = PLAYER_SPRINT_MULT if self.sprinting else 1.0

        # Facing: point toward mouse
        mx, my = mouse_pos
        cx, cy = screen_center
        self.facing = math.atan2(my - cy, mx - cx)

        # Try to move
        base_speed = self.speed * speed_mult
        move_x = dx * base_speed * dt
        move_y = dy * base_speed * dt

        # Check slope at target position — reduce speed on uphill
        if dx != 0 or dy != 0:
            target_x = self.x + move_x
            target_y = self.y + move_y
            slope = terrain.get_slope(target_x, target_y)

            if slope > MAX_SLOPE:
                # Too steep — block movement
                move_x = 0.0
                move_y = 0.0
            else:
                # Speed falloff with slope
                slope_factor = max(0.25, 1.0 - slope * SLOPE_SPEED_FALLOFF / MAX_SLOPE)
                move_x *= slope_factor
                move_y *= slope_factor

        self.x += move_x
        self.y += move_y

        # Footstep dust
        if mag > 0:
            self.footstep_timer += dt
            step_interval = 0.25 if self.sprinting else 0.4
            if self.footstep_timer >= step_interval:
                self.footstep_timer = 0.0
                self._spawn_dust()

        # Update dust particles
        self._update_dust(dt)

    def _spawn_dust(self):
        for _ in range(3):
            angle = self.facing + np.random.uniform(-0.5, 0.5) + math.pi
            speed = np.random.uniform(15, 35)
            self.dust_particles.append({
                'x': self.x + np.random.uniform(-4, 4),
                'y': self.y + np.random.uniform(-4, 4),
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed,
                'life': np.random.uniform(0.3, 0.5),
                'max_life': 0.5,
                'size': np.random.uniform(2, 4),
            })

    def _update_dust(self, dt):
        for p in self.dust_particles:
            p['x'] += p['vx'] * dt
            p['y'] += p['vy'] * dt
            p['vx'] *= 0.92
            p['vy'] *= 0.92
            p['life'] -= dt
        self.dust_particles = [p for p in self.dust_particles if p['life'] > 0]

    def draw(self, screen, cam_x, cam_y):
        """Draw the player and dust particles."""
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y)

        # Dust particles (drawn first, behind player)
        for p in self.dust_particles:
            ps = int(p['x'] - cam_x)
            py = int(p['y'] - cam_y)
            alpha = p['life'] / p['max_life']
            r = max(1, int(p['size'] * alpha))
            col = (int(80 * alpha + 40), int(70 * alpha + 35), int(55 * alpha + 30))
            pygame.draw.circle(screen, col, (ps, py), r)

        # Shadow (offset for pseudo-depth)
        shadow_offset = 4
        shadow_surf = pygame.Surface((self.radius * 3, self.radius * 2), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_surf, (0, 0, 0, 80),
                           (0, 0, self.radius * 3, self.radius * 2))
        screen.blit(shadow_surf,
                    (sx - self.radius * 1 + shadow_offset,
                     sy - self.radius + shadow_offset))

        # Body — circle with outline
        pygame.draw.circle(screen, HULL_BLACK, (sx, sy), self.radius + 2)
        pygame.draw.circle(screen, ADRENALINE, (sx, sy), self.radius)

        # Facing indicator — small triangle pointing toward mouse
        fx = sx + math.cos(self.facing) * (self.radius + 8)
        fy = sy + math.sin(self.facing) * (self.radius + 8)
        perp = self.facing + math.pi / 2
        p1 = (fx, fy)
        p2 = (sx + math.cos(perp) * 4, sy + math.sin(perp) * 4)
        p3 = (sx - math.cos(perp) * 4, sy - math.sin(perp) * 4)
        pygame.draw.polygon(screen, ON_PRIMARY, [p1, p2, p3])
