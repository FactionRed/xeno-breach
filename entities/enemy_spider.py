"""Stalker enemy — fast scuttling spider with lunge attack.

Uses SpiderComponent for procedural leg animation with second-order dynamics.

States:
  scuttle — walk toward player with springy body dynamics
  rear    — stop, lift front legs, wind up for 0.4s (telegraph)
  lunge   — burst toward player at 2.5x speed, deal damage on contact
  death   — collapse legs, fade out
"""
import math
import random
import pygame

from entities.enemy_base import Enemy, EnemyState
from entities.spider_component import SpiderComponent
from config import WORLD_W, WORLD_H


class ScuttleState(EnemyState):
    """Walk toward player."""
    def update(self, dt, enemy, player, terrain, enemies):
        dx = player.x - enemy.x
        dy = player.y - enemy.y
        dist = math.sqrt(dx * dx + dy * dy)
        if dist > 1:
            enemy.facing = math.atan2(dy, dx)
            enemy.x += math.cos(enemy.facing) * enemy.speed * dt
            enemy.y += math.sin(enemy.facing) * enemy.speed * dt
        # Update spider animation
        enemy.spider.update(dt, (enemy.x, enemy.y), enemy.facing, tilt=0.0)


class RearState(EnemyState):
    """Stop and rear up — telegraph the lunge."""
    def enter(self, enemy, player, terrain):
        enemy.rear_timer = 0.0
        enemy.lunge_dir = math.atan2(player.y - enemy.y, player.x - enemy.x)
        enemy.facing = enemy.lunge_dir

    def update(self, dt, enemy, player, terrain, enemies):
        enemy.rear_timer += dt
        # Tilt increases over the wind-up
        tilt = min(1.0, enemy.rear_timer / 0.4)
        enemy.spider.update(dt, (enemy.x, enemy.y), enemy.facing, tilt=tilt)


class LungeState(EnemyState):
    """Burst toward player at high speed."""
    def enter(self, enemy, player, terrain):
        enemy.lunge_timer = 0.0
        enemy.lunge_dir = math.atan2(player.y - enemy.y, player.x - enemy.x)
        enemy.facing = enemy.lunge_dir
        enemy.has_lunged_hit = False

    def update(self, dt, enemy, player, terrain, enemies):
        enemy.lunge_timer += dt
        lunge_speed = enemy.speed * 2.5
        enemy.x += math.cos(enemy.lunge_dir) * lunge_speed * dt
        enemy.y += math.sin(enemy.lunge_dir) * lunge_speed * dt

        # Check collision with player
        if not enemy.has_lunged_hit:
            dx = player.x - enemy.x
            dy = player.y - enemy.y
            if dx * dx + dy * dy <= (enemy.radius + 14) ** 2:
                player.health -= enemy.attack_damage
                enemy.has_lunged_hit = True

        # Body tilts forward during lunge
        enemy.spider.update(dt, (enemy.x, enemy.y), enemy.facing, tilt=-0.5)


class SpiderDeathState(EnemyState):
    """Collapse and fade out."""
    def enter(self, enemy, player, terrain):
        enemy.death_timer = 0.0

    def update(self, dt, enemy, player, terrain, enemies):
        enemy.death_timer += dt
        # Legs collapse — tilt goes negative (body flattens)
        tilt = -enemy.death_timer * 2.0
        enemy.spider.update(dt, (enemy.x, enemy.y), enemy.facing, tilt=tilt)
        if enemy.death_timer > 0.8:
            enemy.dead = True
            enemy.spawn_acid = True


class StalkerEnemy(Enemy):
    """Fast scuttling spider enemy with lunge attack."""
    enemy_type = 'stalker'
    custom_renderer = True

    def __init__(self, x, y, hp_mult=1.0, speed_mult=1.0):
        super().__init__(x, y, hp=35, speed=160, hp_mult=hp_mult, speed_mult=speed_mult)
        self.radius = 16
        self.attack_range = 35
        self.lunge_range = 140
        self.detect_range = 450
        self.attack_damage = 15
        self.rear_timer = 0.0
        self.lunge_timer = 0.0
        self.lunge_dir = 0.0
        self.death_timer = 0.0
        self.has_lunged_hit = False

        # Spider animation component
        self.spider = SpiderComponent((x, y))

    def _setup_states(self):
        self._states = {
            'scuttle': ScuttleState('scuttle'),
            'rear': RearState('rear'),
            'lunge': LungeState('lunge'),
            'death': SpiderDeathState('death'),
        }
        self.state = 'scuttle'
        self._current_state = self._states['scuttle']

    def _check_transitions(self, dt, player, terrain, enemies):
        if self.state == 'scuttle':
            dx = player.x - self.x
            dy = player.y - self.y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist <= self.lunge_range:
                self._transition('rear')
        elif self.state == 'rear':
            if self.rear_timer >= 0.4:
                self._transition('lunge')
        elif self.state == 'lunge':
            if self.lunge_timer >= 0.3:
                # After lunge, go back to scuttling (cooldown)
                self._transition('scuttle')

    def take_damage(self, dmg):
        self.hp -= dmg
        self.flash_timer = 0.1
        if self.hp <= 0 and self.state != 'death':
            self._transition('death')
        # Stalker doesn't get staggered — it's relentless
        # but it does cancel lunge if hit hard
        elif self.state == 'lunge' and dmg >= 20:
            self._transition('scuttle')

    def draw(self, screen, cam_x, cam_y):
        if self.dead:
            return
        # Flash white when hit
        if self.flash_timer > 0:
            # Draw with white overlay
            self.spider.draw(screen, cam_x, cam_y)
            # Overlay flash
            sx = int(self.x - cam_x)
            sy = int(self.y - cam_y)
            flash = pygame.Surface((50, 50), pygame.SRCALPHA)
            pygame.draw.circle(flash, (255, 255, 255, 80), (25, 25), 25)
            screen.blit(flash, (sx - 25, sy - 25), special_flags=pygame.BLEND_ADD)
        else:
            self.spider.draw(screen, cam_x, cam_y)
