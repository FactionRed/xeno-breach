"""Enemy sprite controller — wires any enemy AI state to animation frames.

Works with all enemy types (drone, runner, brute, spitter) by looking up
frames from the ENEMY_SPRITE_MAP via make_enemy_frames().
"""
import math
import pygame

from entities.animation import AnimationStateMachine
from entities.sprite_factory import make_enemy_frames, ENEMY_SPRITE_MAP


# FPS and loop config per animation state name
_STATE_CFG = {
    'patrol':     {'fps': 8,  'loop': True},
    'chase':      {'fps': 12, 'loop': True},
    'lunge':      {'fps': 14, 'loop': False},
    'leap':       {'fps': 16, 'loop': False},
    'attack':     {'fps': 16, 'loop': False},
    'windup':     {'fps': 6,  'loop': False},
    'charge':     {'fps': 12, 'loop': False},
    'groundpound': {'fps': 10, 'loop': False},
    'recover':    {'fps': 4,  'loop': False},
    'retreat':    {'fps': 12, 'loop': True},
    'spit':       {'fps': 8,  'loop': False},
    'stagger':    {'fps': 10, 'loop': False},
    'death':      {'fps': 8,  'loop': False},
}

# Sprite size per enemy type
_SPRITE_SIZE = {
    'drone': 40,
    'runner': 32,
    'brute': 48,
    'spitter': 36,
}


class EnemySprite:
    """Generic sprite controller for any enemy type."""

    def __init__(self, enemy_type='drone'):
        self.enemy_type = enemy_type
        self.size = _SPRITE_SIZE.get(enemy_type, 40)
        self.anim = AnimationStateMachine()
        self._build_states(enemy_type)
        self._last_ai_state = 'patrol'

    def _build_states(self, enemy_type):
        """Build all animation states for this enemy type."""
        sprite_map = ENEMY_SPRITE_MAP.get(enemy_type, ENEMY_SPRITE_MAP['drone'])
        initial_state = 'patrol'

        for state_name, factory in sprite_map.items():
            frames = factory(self.size)
            cfg = _STATE_CFG.get(state_name, {'fps': 10, 'loop': True})
            transitions = {}
            # Allow transitions to any other state in this enemy's map
            for other_state in sprite_map:
                if other_state != state_name:
                    transitions[other_state] = other_state
            self.anim.add_state(state_name, frames,
                                fps=cfg['fps'], loop=cfg['loop'],
                                transitions=transitions)

        # Set initial state
        if initial_state in sprite_map:
            self.anim.set_state(initial_state)

    def update(self, dt, enemy):
        """Update animation based on enemy AI state."""
        ai_state = enemy.state

        if ai_state != self._last_ai_state:
            if ai_state in self.anim.states:
                self.anim.set_state(ai_state, reset=True)
            self._last_ai_state = ai_state

        # Handle non-looping state completion
        if self.anim.is_finished:
            if self.anim.current_state_name in ('lunge', 'leap', 'attack',
                                                  'stagger', 'windup', 'charge',
                                                  'groundpound', 'recover', 'spit'):
                if 'chase' in self.anim.states:
                    self.anim.set_state('chase', reset=True)
                elif 'patrol' in self.anim.states:
                    self.anim.set_state('patrol', reset=True)

        self.anim.update(dt)

    def draw(self, screen, enemy, cam_x, cam_y):
        """Draw the enemy sprite with facing rotation."""
        self.anim.draw(screen, enemy.x, enemy.y, cam_x, cam_y,
                      rotation=enemy.facing, scale=1.0)


# Backward-compatible alias
XenoSprite = EnemySprite
