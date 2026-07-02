"""Enemy base class — shared infrastructure for all enemy types.

Extracted from the original Xenomorph class. Provides:
  - Position, health, movement, facing
  - AI state machine framework (states with enter/update/exit)
  - Damage handling, death, acid pool spawning
  - Fallback draw method
  - Sensor-based transition system

Subclasses (Drone, Runner, Brute, Spitter) define their own state sets
and sensor logic by overriding _setup_states() and _check_transitions().
"""
import math
import random
import pygame

from config import (ACID, BIO_MASS, DANGER, HULL_BLACK, ON_PRIMARY,
                    PLAYER_RADIUS, WORLD_W, WORLD_H, MAX_SLOPE)


class AcidPool:
    """Lingering acid pool left by dead enemies."""
    def __init__(self, x, y, radius=30, dps=8, life=5.0):
        self.x = x
        self.y = y
        self.radius = radius
        self.dps = dps
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
        r = int(self.radius)
        surf = pygame.Surface((r * 2 + 4, r * 2 + 4), pygame.SRCALPHA)
        pygame.draw.circle(surf, (int(ACID[0] * 0.3), int(ACID[1] * 0.3),
                                  int(ACID[2] * 0.3), int(100 * alpha)),
                          (r + 2, r + 2), r)
        pygame.draw.circle(surf, (ACID[0], ACID[1], ACID[2], int(80 * alpha)),
                          (r + 2, r + 2), int(r * 0.7))
        for _ in range(3):
            bx = random.randint(-r, r)
            by = random.randint(-r, r)
            if bx * bx + by * by < r * r:
                pygame.draw.circle(surf, (ACID[0], ACID[1], ACID[2], int(150 * alpha)),
                                  (r + 2 + bx, r + 2 + by), random.randint(2, 4))
        screen.blit(surf, (sx - r - 2, sy - r - 2))


class AcidProjectile:
    """Projectile fired by Spitter enemies."""
    def __init__(self, x, y, tx, ty, speed=200, damage=8, radius=20, life=2.0):
        self.x = float(x)
        self.y = float(y)
        dx = tx - x
        dy = ty - y
        d = math.sqrt(dx * dx + dy * dy) + 0.001
        self.vx = dx / d * speed
        self.vy = dy / d * speed
        self.damage = damage
        self.radius = radius
        self.life = life
        self.dead = False

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.life -= dt
        if self.life <= 0:
            self.dead = True
        if self.x < 0 or self.x > WORLD_W or self.y < 0 or self.y > WORLD_H:
            self.dead = True

    def contains(self, x, y):
        dx = x - self.x
        dy = y - self.y
        return dx * dx + dy * dy <= self.radius * self.radius

    def draw(self, screen, cam_x, cam_y):
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y)
        if sx < -20 or sx > screen.get_width() + 20 or sy < -20 or sy > screen.get_height() + 20:
            return
        surf = pygame.Surface((self.radius * 2 + 4, self.radius * 2 + 4), pygame.SRCALPHA)
        pygame.draw.circle(surf, (*ACID, 180), (self.radius + 2, self.radius + 2), self.radius)
        pygame.draw.circle(surf, (255, 255, 255, 100), (self.radius + 2, self.radius + 2), self.radius - 3)
        screen.blit(surf, (sx - self.radius - 2, sy - self.radius - 2))


# ============ AI STATE BASE ============

class EnemyState:
    """Base AI state."""
    def __init__(self, name):
        self.name = name
        self.timer = 0.0

    def enter(self, enemy, player, terrain):
        self.timer = 0.0

    def update(self, dt, enemy, player, terrain, enemies):
        self.timer += dt

    def exit(self, enemy):
        pass


# ============ SHARED STATES ============

class ChaseState(EnemyState):
    def __init__(self):
        super().__init__('chase')

    def update(self, dt, enemy, player, terrain, enemies):
        self.timer += dt
        dx = player.x - enemy.x
        dy = player.y - enemy.y
        dist = math.sqrt(dx * dx + dy * dy)
        enemy.facing = math.atan2(dy, dx)
        spd = enemy.speed * dt
        nx = enemy.x + math.cos(enemy.facing) * spd
        ny = enemy.y + math.sin(enemy.facing) * spd
        if terrain.get_slope(nx, ny) < MAX_SLOPE:
            enemy.x = nx
            enemy.y = ny
        else:
            perp = enemy.facing + math.pi / 2
            for sign in (1, -1):
                sx = enemy.x + math.cos(perp) * sign * spd
                sy = enemy.y + math.sin(perp) * sign * spd
                if terrain.get_slope(sx, sy) < MAX_SLOPE:
                    enemy.x = sx
                    enemy.y = sy
                    break


class StaggerState(EnemyState):
    def __init__(self):
        super().__init__('stagger')

    def enter(self, enemy, player, terrain):
        super().enter(enemy, player, terrain)
        self.duration = 0.2

    def update(self, dt, enemy, player, terrain, enemies):
        self.timer += dt
        enemy.x += enemy.vx * dt
        enemy.y += enemy.vy * dt
        enemy.vx *= 0.85
        enemy.vy *= 0.85


class DeathState(EnemyState):
    def __init__(self):
        super().__init__('death')

    def enter(self, enemy, player, terrain):
        super().enter(enemy, player, terrain)
        self.duration = 0.4

    def update(self, dt, enemy, player, terrain, enemies):
        self.timer += dt
        if self.timer >= self.duration:
            enemy.dead = True
            enemy.spawn_acid = True


class RetreatState(EnemyState):
    """Move away from player — used by Spitter."""
    def __init__(self):
        super().__init__('retreat')

    def update(self, dt, enemy, player, terrain, enemies):
        self.timer += dt
        dx = enemy.x - player.x
        dy = enemy.y - player.y
        dist = math.sqrt(dx * dx + dy * dy) + 0.001
        enemy.facing = math.atan2(dy, dx)
        spd = enemy.speed * dt
        nx = enemy.x + math.cos(enemy.facing) * spd
        ny = enemy.y + math.sin(enemy.facing) * spd
        if terrain.get_slope(nx, ny) < MAX_SLOPE:
            enemy.x = nx
            enemy.y = ny


# ============ ENEMY BASE CLASS ============

class Enemy:
    """Base enemy class. Subclasses define _setup_states() and _check_transitions()."""

    # Type identifier for spawner/sprites
    enemy_type = 'drone'

    def __init__(self, x, y, hp=40, speed=90, hp_mult=1.0, speed_mult=1.0):
        self.x = float(x)
        self.y = float(y)
        self.hp = int(hp * hp_mult)
        self.max_hp = self.hp
        self.speed = speed * speed_mult
        self.radius = 14
        self.facing = 0.0
        self.vx = 0.0
        self.vy = 0.0
        self.dead = False
        self.spawn_acid = False
        self.flash_timer = 0.0

        # AI parameters (overridden by subclasses)
        self.attack_range = 35
        self.lunge_range = 120
        self.detect_range = 400
        self.attack_cooldown = 0.0
        self.attack_damage = 12

        # Patrol
        self.patrol_target = None
        self._pick_patrol_target()

        # State machine
        self.state = 'patrol'
        self._states = {}
        self._setup_states()
        self._current_state = self._states.get(self.state)
        if self._current_state:
            self._current_state.enter(self, None, None)

    def _setup_states(self):
        """Override in subclass to register AI states."""
        pass

    def _pick_patrol_target(self):
        self.patrol_target = (
            random.uniform(50, WORLD_W - 50),
            random.uniform(50, WORLD_H - 50),
        )

    def take_damage(self, dmg):
        self.hp -= dmg
        self.flash_timer = 0.1
        if self.hp <= 0 and self.state != 'death':
            self._transition('death')
        elif self.state == 'patrol':
            self._transition('chase')

    def _transition(self, new_state_name):
        if new_state_name == self.state:
            return
        if new_state_name not in self._states:
            return
        self._current_state.exit(self)
        self.state = new_state_name
        self._current_state = self._states[new_state_name]
        self._current_state.enter(self, None, None)

    def update(self, dt, player, terrain, enemies):
        if self.dead:
            return

        self.flash_timer = max(0, self.flash_timer - dt)
        self.attack_cooldown = max(0, self.attack_cooldown - dt)

        if self._current_state is not None:
            self._current_state.update(dt, self, player, terrain, enemies)
            self._check_transitions(dt, player, terrain, enemies)
        else:
            # State was never set (e.g. Runner starts with 'chase' but base
            # init set 'patrol' which doesn't exist) — fall back to first state
            if self._states:
                first_state = next(iter(self._states))
                self._transition(first_state)

        self.x = max(self.radius, min(WORLD_W - self.radius, self.x))
        self.y = max(self.radius, min(WORLD_H - self.radius, self.y))

    def _check_transitions(self, dt, player, terrain, enemies):
        """Override in subclass for sensor-based transitions."""
        pass

    def draw(self, screen, cam_x, cam_y):
        """Fallback draw when no sprite controller is available."""
        if self.dead:
            return
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y)
        if sx < -30 or sx > screen.get_width() + 30 or sy < -30 or sy > screen.get_height() + 30:
            return

        if self.state == 'death':
            t = max(0, 1 - self._current_state.timer / 0.4)
            r = max(1, int(self.radius * t))
            alpha = int(255 * t)
            surf = pygame.Surface((r * 2 + 4, r * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*BIO_MASS, alpha), (r + 2, r + 2), r)
            screen.blit(surf, (sx - r - 2, sy - r - 2))
            return

        shadow = pygame.Surface((self.radius * 3, self.radius * 2), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 60), (0, 0, self.radius * 3, self.radius * 2))
        screen.blit(shadow, (sx - self.radius + 2, sy - self.radius + 2))

        body_color = BIO_MASS
        if self.flash_timer > 0:
            body_color = ON_PRIMARY

        ell_w = self.radius * 2 + 4
        ell_h = self.radius * 2 - 2
        body_surf = pygame.Surface((ell_w + 4, ell_h + 4), pygame.SRCALPHA)
        pygame.draw.ellipse(body_surf, body_color, (2, 2, ell_w, ell_h))
        pygame.draw.ellipse(body_surf, HULL_BLACK, (2, 2, ell_w, ell_h), 2)

        rot_deg = -math.degrees(self.facing)
        rotated = pygame.transform.rotate(body_surf, rot_deg)
        rect = rotated.get_rect(center=(sx, sy))
        screen.blit(rotated, rect)

        hx = sx + math.cos(self.facing) * (self.radius - 2)
        hy = sy + math.sin(self.facing) * (self.radius - 2)
        pygame.draw.circle(screen, HULL_BLACK, (int(hx), int(hy)), 5)
        pygame.draw.circle(screen, body_color, (int(hx), int(hy)), 4)

        if self.hp < self.max_hp:
            bar_w = 24
            bar_h = 3
            bx = sx - bar_w // 2
            by = sy - self.radius - 8
            pygame.draw.rect(screen, (40, 40, 40), (bx, by, bar_w, bar_h))
            pct = self.hp / self.max_hp
            pygame.draw.rect(screen, DANGER, (bx, by, int(bar_w * pct), bar_h))
