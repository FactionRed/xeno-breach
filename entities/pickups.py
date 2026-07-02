"""Pickup system — health and ammo drops from killed enemies."""
import math
import random
import pygame

from config import ACID, DANGER, WARNING, ADRENALINE, ON_PRIMARY, ON_SECONDARY


class Pickup:
    def __init__(self, x, y, kind='health'):
        self.x = float(x)
        self.y = float(y)
        self.kind = kind  # 'health' or 'ammo'
        self.radius = 8
        self.life = 15.0  # despawns after 15s
        self.dead = False
        self.bob = random.random() * math.tau

    def update(self, dt, player):
        self.life -= dt
        self.bob += dt * 3
        if self.life <= 0:
            self.dead = True
            return
        # Check pickup
        dx = player.x - self.x
        dy = player.y - self.y
        if dx * dx + dy * dy < (self.radius + 15) ** 2:
            if self.kind == 'health':
                player.health = min(player.max_health, player.health + 25)
            elif self.kind == 'ammo':
                # Refill current weapon
                pass  # handled by caller
            self.dead = True

    def draw(self, screen, cam_x, cam_y):
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y + math.sin(self.bob) * 2)
        if sx < -20 or sx > screen.get_width() + 20:
            return
        # Blink when about to despawn
        if self.life < 3 and int(self.life * 6) % 2 == 0:
            return
        if self.kind == 'health':
            color = DANGER
            # Draw cross
            pygame.draw.rect(screen, color, (sx - 3, sy - 1, 6, 2))
            pygame.draw.rect(screen, color, (sx - 1, sy - 3, 2, 6))
            pygame.draw.circle(screen, ON_PRIMARY, (sx, sy), 7, 1)
        else:
            color = WARNING
            # Draw ammo box
            pygame.draw.rect(screen, color, (sx - 4, sy - 3, 8, 6))
            pygame.draw.rect(screen, ON_PRIMARY, (sx - 4, sy - 3, 8, 6), 1)
            pygame.draw.line(screen, ON_PRIMARY, (sx, sy - 3), (sx, sy + 3), 1)


class PickupSystem:
    def __init__(self):
        self.pickups = []

    def maybe_drop(self, x, y, enemy_type='drone', elite=None):
        """Chance to drop a pickup when an enemy dies."""
        roll = random.random()
        base_chance = 0.08 if enemy_type != 'brute' else 0.25
        if elite:
            base_chance += 0.15
        if roll < base_chance:
            kind = 'health' if random.random() < 0.6 else 'ammo'
            self.pickups.append(Pickup(x, y, kind))

    def update(self, dt, player, weapons):
        for p in self.pickups:
            if p.kind == 'ammo':
                # Check pickup with ammo refill
                dx = player.x - p.x
                dy = player.y - p.y
                if dx * dx + dy * dy < (p.radius + 15) ** 2:
                    weapon = weapons.current
                    weapon.ammo = min(weapon.mag_size, weapon.ammo + weapon.mag_size // 2)
                    p.dead = True
                else:
                    p.update(dt, player)
            else:
                p.update(dt, player)
        self.pickups = [p for p in self.pickups if not p.dead]

    def draw(self, screen, cam_x, cam_y):
        for p in self.pickups:
            p.draw(screen, cam_x, cam_y)
