"""Particle system — muzzle flash, blood spray, acid splash, impact sparks, dust."""
import math
import random
import numpy as np


class ParticleSystem:
    def __init__(self):
        self.particles = []

    def emit_muzzle_flash(self, x, y, angle, color):
        """Bright flash at barrel tip — uses additive blending."""
        for _ in range(6):
            spread = random.uniform(-0.4, 0.4)
            speed = random.uniform(100, 250)
            self.particles.append({
                'x': x, 'y': y,
                'vx': math.cos(angle + spread) * speed,
                'vy': math.sin(angle + spread) * speed,
                'life': random.uniform(0.05, 0.15),
                'max_life': 0.15,
                'size': random.uniform(3, 7),
                'color': color,
                'fade': True,
                'additive': True,
            })
        # Core bright flash
        self.particles.append({
            'x': x, 'y': y, 'vx': 0, 'vy': 0,
            'life': 0.05, 'max_life': 0.05,
            'size': 8, 'color': (255, 255, 220),
            'fade': True, 'additive': True,
        })

    def emit_blood_spray(self, x, y, angle, color=(91, 31, 46)):
        """Bio-mass colored spray on hit."""
        for _ in range(10):
            spread = random.uniform(-1.2, 1.2)
            speed = random.uniform(40, 150)
            self.particles.append({
                'x': x, 'y': y,
                'vx': math.cos(angle + spread) * speed,
                'vy': math.sin(angle + spread) * speed,
                'life': random.uniform(0.2, 0.5),
                'max_life': 0.5,
                'size': random.uniform(2, 5),
                'color': color,
                'fade': True,
                'gravity': 50,
            })

    def emit_acid_splash(self, x, y, color=(157, 255, 61)):
        """Acid green splash on xenomorph death."""
        for _ in range(16):
            angle = random.uniform(0, math.tau)
            speed = random.uniform(60, 200)
            self.particles.append({
                'x': x, 'y': y,
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed,
                'life': random.uniform(0.3, 0.7),
                'max_life': 0.7,
                'size': random.uniform(3, 7),
                'color': color,
                'fade': True,
                'gravity': 30,
            })

    def emit_impact_sparks(self, x, y, angle, color=(255, 180, 84)):
        """Sparks when bullet hits terrain."""
        for _ in range(5):
            spread = random.uniform(-0.8, 0.8)
            speed = random.uniform(50, 120)
            self.particles.append({
                'x': x, 'y': y,
                'vx': math.cos(angle + spread + math.pi) * speed,
                'vy': math.sin(angle + spread + math.pi) * speed,
                'life': random.uniform(0.1, 0.25),
                'max_life': 0.25,
                'size': random.uniform(1, 3),
                'color': color,
                'fade': True,
            })

    def emit_explosion(self, x, y):
        """Large explosion for grenades/environmental."""
        for _ in range(30):
            angle = random.uniform(0, math.tau)
            speed = random.uniform(80, 300)
            c = random.choice([(255, 65, 54), (255, 180, 84), (255, 255, 200)])
            self.particles.append({
                'x': x, 'y': y,
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed,
                'life': random.uniform(0.3, 0.8),
                'max_life': 0.8,
                'size': random.uniform(3, 8),
                'color': c,
                'fade': True,
                'gravity': 40,
            })

    def update(self, dt):
        for p in self.particles:
            p['x'] += p['vx'] * dt
            p['y'] += p['vy'] * dt
            p['vx'] *= 0.92
            p['vy'] *= 0.92
            if 'gravity' in p:
                p['vy'] += p['gravity'] * dt
            p['life'] -= dt
        self.particles = [p for p in self.particles if p['life'] > 0]

    def draw(self, screen, cam_x, cam_y):
        for p in self.particles:
            sx = int(p['x'] - cam_x)
            sy = int(p['y'] - cam_y)
            if sx < -10 or sx > screen.get_width() + 10 or sy < -10 or sy > screen.get_height() + 10:
                continue
            alpha = p['life'] / p['max_life']
            r = max(1, int(p['size'] * alpha))
            c = p['color']
            col = (int(c[0] * alpha), int(c[1] * alpha), int(c[2] * alpha))
            if p.get('additive'):
                # Additive blending: draw onto a temp surface, then BLEND_ADD
                ps = pygame.Surface((r * 2 + 2, r * 2 + 2), pygame.SRCALPHA)
                pygame.draw.circle(ps, (*col, int(200 * alpha)), (r + 1, r + 1), r)
                screen.blit(ps, (sx - r - 1, sy - r - 1), special_flags=pygame.BLEND_ADD)
            else:
                pygame.draw.circle(screen, col, (sx, sy), r)

    def clear(self):
        self.particles.clear()


import pygame  # needed for draw
