"""Enemy types — Drone, Runner, Brute, Spitter.

All inherit from Enemy base class. Each defines its own state set
and transition logic via _setup_states() and _check_transitions().
"""
import math
import random
import pygame

from config import (ACID, BIO_MASS, DANGER, HULL_BLACK, ON_PRIMARY,
                    WORLD_W, WORLD_H, MAX_SLOPE)
from entities.enemy_base import (Enemy, EnemyState, AcidPool, AcidProjectile,
                                  ChaseState, StaggerState, DeathState,
                                  RetreatState)


# ============ SHARED PATROL STATE ============

class PatrolState(EnemyState):
    def __init__(self):
        super().__init__('patrol')

    def enter(self, enemy, player, terrain):
        super().enter(enemy, player, terrain)
        if not hasattr(enemy, 'patrol_target') or enemy.patrol_target is None:
            enemy._pick_patrol_target()

    def update(self, dt, enemy, player, terrain, enemies):
        self.timer += dt
        tx, ty = enemy.patrol_target
        dx = tx - enemy.x
        dy = ty - enemy.y
        d = math.sqrt(dx * dx + dy * dy)
        if d < 20:
            enemy._pick_patrol_target()
            return
        enemy.facing = math.atan2(dy, dx)
        spd = enemy.speed * 0.4 * dt
        nx = enemy.x + math.cos(enemy.facing) * spd
        ny = enemy.y + math.sin(enemy.facing) * spd
        if terrain.get_slope(nx, ny) < MAX_SLOPE:
            enemy.x = nx
            enemy.y = ny
        else:
            enemy._pick_patrol_target()


# ============ DRONE (original Xenomorph behavior) ============

class LungeState(EnemyState):
    def __init__(self):
        super().__init__('lunge')

    def enter(self, enemy, player, terrain):
        super().enter(enemy, player, terrain)
        self.duration = 0.3

    def update(self, dt, enemy, player, terrain, enemies):
        self.timer += dt
        lunge_speed = enemy.speed * 2.5 * dt
        dx = player.x - enemy.x
        dy = player.y - enemy.y
        enemy.facing = math.atan2(dy, dx)
        nx = enemy.x + math.cos(enemy.facing) * lunge_speed
        ny = enemy.y + math.sin(enemy.facing) * lunge_speed
        if terrain.get_slope(nx, ny) < MAX_SLOPE:
            enemy.x = nx
            enemy.y = ny


class AttackState(EnemyState):
    def __init__(self):
        super().__init__('attack')

    def enter(self, enemy, player, terrain):
        super().enter(enemy, player, terrain)
        self.has_hit = False

    def update(self, dt, enemy, player, terrain, enemies):
        self.timer += dt
        if not self.has_hit and self.timer > 0.1:
            player.health -= enemy.attack_damage
            self.has_hit = True
            dx = enemy.x - player.x
            dy = enemy.y - player.y
            d = math.sqrt(dx * dx + dy * dy) + 0.001
            enemy.vx = dx / d * 80
            enemy.vy = dy / d * 80


class Drone(Enemy):
    """Baseline xenomorph — patrol, chase, lunge, attack, stagger, death."""
    enemy_type = 'drone'

    def __init__(self, x, y, **kw):
        super().__init__(x, y, hp=40, speed=90, **kw)

    def _setup_states(self):
        self._states = {
            'patrol': PatrolState(),
            'chase': ChaseState(),
            'lunge': LungeState(),
            'attack': AttackState(),
            'stagger': StaggerState(),
            'death': DeathState(),
        }

    def _check_transitions(self, dt, player, terrain, enemies):
        if self.state in ('death', 'stagger'):
            if self.state == 'stagger' and self._current_state.timer >= 0.2:
                self._transition('chase')
                self.attack_cooldown = 1.2
            return
        dx = player.x - self.x
        dy = player.y - self.y
        dist = math.sqrt(dx * dx + dy * dy)

        if self.state == 'patrol':
            if dist < self.detect_range:
                self._transition('chase')
        elif self.state == 'chase':
            if dist < self.lunge_range and self.attack_cooldown <= 0:
                self._transition('lunge')
            elif dist < self.attack_range:
                self._transition('attack')
        elif self.state == 'lunge':
            if dist < self.attack_range:
                self._transition('attack')
            elif self._current_state.timer >= 0.3:
                self._transition('chase')
                self.attack_cooldown = 1.0
        elif self.state == 'attack':
            if self._current_state.timer > 0.15:
                self._transition('stagger')


# ============ RUNNER (fast, no patrol, leap attack) ============

class LeapState(EnemyState):
    """Fast leap — shorter than lunge, lower damage, faster cooldown."""
    def __init__(self):
        super().__init__('leap')

    def enter(self, enemy, player, terrain):
        super().enter(enemy, player, terrain)
        self.duration = 0.2

    def update(self, dt, enemy, player, terrain, enemies):
        self.timer += dt
        leap_speed = enemy.speed * 3.0 * dt
        dx = player.x - enemy.x
        dy = player.y - enemy.y
        enemy.facing = math.atan2(dy, dx)
        nx = enemy.x + math.cos(enemy.facing) * leap_speed
        ny = enemy.y + math.sin(enemy.facing) * leap_speed
        if terrain.get_slope(nx, ny) < MAX_SLOPE:
            enemy.x = nx
            enemy.y = ny


class RunnerAttackState(EnemyState):
    """Quick strike — lower damage, fast recovery."""
    def __init__(self):
        super().__init__('attack')

    def enter(self, enemy, player, terrain):
        super().enter(enemy, player, terrain)
        self.has_hit = False

    def update(self, dt, enemy, player, terrain, enemies):
        self.timer += dt
        if not self.has_hit and self.timer > 0.08:
            player.health -= enemy.attack_damage
            self.has_hit = True
            dx = enemy.x - player.x
            dy = enemy.y - player.y
            d = math.sqrt(dx * dx + dy * dy) + 0.001
            enemy.vx = dx / d * 50
            enemy.vy = dy / d * 50


class Runner(Enemy):
    """Fast, fragile, always aggro. No patrol — spawns chasing."""
    enemy_type = 'runner'

    def __init__(self, x, y, **kw):
        super().__init__(x, y, hp=25, speed=180, **kw)
        self.radius = 11
        self.attack_range = 28
        self.lunge_range = 100
        self.detect_range = 600  # always detects
        self.attack_damage = 8
        # Override initial state to chase (was 'patrol' from base init)
        self.state = 'chase'
        self._current_state = self._states.get('chase')
        if self._current_state:
            self._current_state.enter(self, None, None)

    def _setup_states(self):
        self._states = {
            'chase': ChaseState(),
            'leap': LeapState(),
            'attack': RunnerAttackState(),
            'stagger': StaggerState(),
            'death': DeathState(),
        }

    def _check_transitions(self, dt, player, terrain, enemies):
        if self.state in ('death', 'stagger'):
            if self.state == 'stagger' and self._current_state.timer >= 0.15:
                self._transition('chase')
                self.attack_cooldown = 0.6
            return
        dx = player.x - self.x
        dy = player.y - self.y
        dist = math.sqrt(dx * dx + dy * dy)

        if self.state == 'chase':
            if dist < self.lunge_range and self.attack_cooldown <= 0:
                self._transition('leap')
            elif dist < self.attack_range:
                self._transition('attack')
        elif self.state == 'leap':
            if dist < self.attack_range:
                self._transition('attack')
            elif self._current_state.timer >= 0.2:
                self._transition('chase')
                self.attack_cooldown = 0.5
        elif self.state == 'attack':
            if self._current_state.timer > 0.12:
                self._transition('stagger')


# ============ BRUTE (slow tank, charge + ground pound) ============

class WindupState(EnemyState):
    """Telegraph charge — 1s windup, visible to player."""
    def __init__(self):
        super().__init__('windup')

    def enter(self, enemy, player, terrain):
        super().enter(enemy, player, terrain)
        self.duration = 1.0

    def update(self, dt, enemy, player, terrain, enemies):
        self.timer += dt
        # Face player but don't move
        dx = player.x - enemy.x
        dy = player.y - enemy.y
        enemy.facing = math.atan2(dy, dx)


class ChargeState(EnemyState):
    """Fast charge in a straight line — high damage + knockback."""
    def __init__(self):
        super().__init__('charge')

    def enter(self, enemy, player, terrain):
        super().enter(enemy, player, terrain)
        self.duration = 0.6
        self.charge_dir = enemy.facing
        self.has_hit = False

    def update(self, dt, enemy, player, terrain, enemies):
        self.timer += dt
        charge_speed = enemy.speed * 3.5 * dt
        nx = enemy.x + math.cos(self.charge_dir) * charge_speed
        ny = enemy.y + math.sin(self.charge_dir) * charge_speed
        if terrain.get_slope(nx, ny) < MAX_SLOPE:
            enemy.x = nx
            enemy.y = ny
        else:
            # Hit a wall — end charge
            self.timer = self.duration

        # Check collision with player
        if not self.has_hit:
            dx = player.x - enemy.x
            dy = player.y - enemy.y
            if dx * dx + dy * dy < (enemy.radius + 20) ** 2:
                player.health -= enemy.attack_damage
                dx = player.x - enemy.x
                dy = player.y - enemy.y
                d = math.sqrt(dx * dx + dy * dy) + 0.001
                player.x += dx / d * 40  # knockback player
                player.y += dy / d * 40
                self.has_hit = True


class GroundPoundState(EnemyState):
    """AoE attack — damages player if close."""
    def __init__(self):
        super().__init__('groundpound')

    def enter(self, enemy, player, terrain):
        super().enter(enemy, player, terrain)
        self.duration = 0.5
        self.has_hit = False

    def update(self, dt, enemy, player, terrain, enemies):
        self.timer += dt
        if not self.has_hit and self.timer > 0.3:
            # AoE damage within radius
            dx = player.x - enemy.x
            dy = player.y - enemy.y
            if dx * dx + dy * dy < 80 * 80:
                player.health -= enemy.attack_damage * 0.7
                d = math.sqrt(dx * dx + dy * dy) + 0.001
                player.x += dx / d * 30
                player.y += dy / d * 30
            self.has_hit = True


class RecoverState(EnemyState):
    """Recovery after charge/ground pound."""
    def __init__(self):
        super().__init__('recover')

    def enter(self, enemy, player, terrain):
        super().enter(enemy, player, terrain)
        self.duration = 0.8

    def update(self, dt, enemy, player, terrain, enemies):
        self.timer += dt


class Brute(Enemy):
    """Slow tank. Charges when in LoS, ground pounds when close."""
    enemy_type = 'brute'

    def __init__(self, x, y, **kw):
        super().__init__(x, y, hp=150, speed=45, **kw)
        self.radius = 24  # matches 48px sprite
        self.attack_range = 60
        self.lunge_range = 350  # charge range
        self.detect_range = 450
        self.attack_damage = 25
        self.state = 'patrol'
        self._enraged = False

    def _setup_states(self):
        self._states = {
            'patrol': PatrolState(),
            'chase': ChaseState(),
            'windup': WindupState(),
            'charge': ChargeState(),
            'groundpound': GroundPoundState(),
            'recover': RecoverState(),
            'stagger': StaggerState(),
            'death': DeathState(),
        }

    def take_damage(self, dmg):
        super().take_damage(dmg)
        # Enrage at 50% HP
        if self.hp < self.max_hp * 0.5 and not self._enraged:
            self._enraged = True
            self.speed *= 1.5
            self.attack_damage = int(self.attack_damage * 1.3)

    def _check_transitions(self, dt, player, terrain, enemies):
        if self.state in ('death', 'stagger', 'recover'):
            if self.state == 'stagger' and self._current_state.timer >= 0.3:
                self._transition('chase')
            elif self.state == 'recover' and self._current_state.timer >= 0.8:
                self._transition('chase')
            return

        dx = player.x - self.x
        dy = player.y - self.y
        dist = math.sqrt(dx * dx + dy * dy)

        if self.state == 'patrol':
            if dist < self.detect_range:
                self._transition('chase')
        elif self.state == 'chase':
            if dist < self.attack_range and self.attack_cooldown <= 0:
                self._transition('groundpound')
            elif dist < self.lunge_range and self.attack_cooldown <= 0:
                self._transition('windup')
        elif self.state == 'windup':
            if self._current_state.timer >= 1.0:
                self._transition('charge')
        elif self.state == 'charge':
            if self._current_state.timer >= 0.6:
                self._transition('recover')
                self.attack_cooldown = 2.5
        elif self.state == 'groundpound':
            if self._current_state.timer >= 0.5:
                self._transition('recover')
                self.attack_cooldown = 2.0


# ============ SPITTER (ranged acid, keeps distance) ============

class SpitState(EnemyState):
    """Fire acid projectile at player."""
    def __init__(self):
        super().__init__('spit')

    def enter(self, enemy, player, terrain):
        super().enter(enemy, player, terrain)
        self.duration = 0.5
        self.has_fired = False

    def update(self, dt, enemy, player, terrain, enemies):
        self.timer += dt
        dx = player.x - enemy.x
        dy = player.y - enemy.y
        enemy.facing = math.atan2(dy, dx)

        if not self.has_fired and self.timer > 0.25:
            # Fire acid projectile
            if hasattr(enemy, 'on_spit'):
                enemy.on_spit(enemy.x, enemy.y, player.x, player.y)
            self.has_fired = True


class Spitter(Enemy):
    """Ranged attacker. Maintains distance, fires acid projectiles."""
    enemy_type = 'spitter'

    def __init__(self, x, y, **kw):
        super().__init__(x, y, hp=50, speed=70, **kw)
        self.radius = 13
        self.attack_range = 300   # spit range
        self.lunge_range = 200    # start retreating within this
        self.detect_range = 500
        self.attack_damage = 10
        self.state = 'patrol'
        self.on_spit = None  # callback set by spawner/main

    def _setup_states(self):
        self._states = {
            'patrol': PatrolState(),
            'chase': ChaseState(),
            'retreat': RetreatState(),
            'spit': SpitState(),
            'stagger': StaggerState(),
            'death': DeathState(),
        }

    def _check_transitions(self, dt, player, terrain, enemies):
        if self.state in ('death', 'stagger'):
            if self.state == 'stagger' and self._current_state.timer >= 0.2:
                self._transition('chase')
            return

        dx = player.x - self.x
        dy = player.y - self.y
        dist = math.sqrt(dx * dx + dy * dy)

        if self.state == 'patrol':
            if dist < self.detect_range:
                self._transition('chase')
        elif self.state == 'chase':
            if dist < self.lunge_range:
                self._transition('retreat')
            elif dist < self.attack_range and self.attack_cooldown <= 0:
                self._transition('spit')
        elif self.state == 'retreat':
            if dist > self.lunge_range + 50:
                self._transition('chase')
            elif dist < self.attack_range and self.attack_cooldown <= 0:
                self._transition('spit')
        elif self.state == 'spit':
            if self._current_state.timer >= 0.5:
                self._transition('chase')
                self.attack_cooldown = 2.0


# ============ FACTORY ============

ENEMY_TYPES = {
    'drone': Drone,
    'runner': Runner,
    'brute': Brute,
    'spitter': Spitter,
}


def create_enemy(enemy_type, x, y, **kw):
    """Factory function to create an enemy by type name."""
    cls = ENEMY_TYPES.get(enemy_type, Drone)
    return cls(x, y, **kw)
