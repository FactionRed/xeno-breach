"""Player sprite controller — 4-directional pixel art animation states.

Uses the template sprite sheet style: 16×16 pixel art, peach fill (#FFC090),
dark brown outline (#4A2E18), chibi proportions, scaled 2× to 32×32.

States: idle → walk → sprint → shoot → reload → hurt → dead
Directions: front / right / back / left (selected by movement direction)
"""
import math
import pygame

from entities.animation import AnimationStateMachine
from entities.sprite_factory import make_player_frames, DIRECTIONS


class PlayerSprite:
    """Manages directional pixel-art animation for the player."""

    def __init__(self):
        self._anim_sets = {}  # (state, direction) -> AnimationStateMachine

        # Build animation state machines for each direction
        state_configs = {
            'idle':   {'fps': 4,  'loop': True},
            'walk':   {'fps': 12, 'loop': True},
            'sprint': {'fps': 14, 'loop': True},
            'shoot':  {'fps': 20, 'loop': False},
            'reload': {'fps': 6,  'loop': False},
            'hurt':   {'fps': 4,  'loop': False},
            'dead':   {'fps': 8,  'loop': False},
        }

        transitions = {
            'idle':   {'walk': 'walk', 'sprint': 'sprint', 'shoot': 'shoot',
                       'reload': 'reload', 'hurt': 'hurt', 'die': 'dead'},
            'walk':   {'stop': 'idle', 'sprint': 'sprint', 'shoot': 'shoot',
                       'reload': 'reload', 'hurt': 'hurt', 'die': 'dead',
                       'turn': 'walk'},
            'sprint': {'stop': 'idle', 'walk': 'walk', 'shoot': 'shoot',
                       'reload': 'reload', 'hurt': 'hurt', 'die': 'dead',
                       'turn': 'sprint'},
            'shoot':  {'done': 'idle', 'walk': 'walk', 'sprint': 'sprint',
                       'hurt': 'hurt', 'die': 'dead'},
            'reload': {'done': 'idle', 'walk': 'walk', 'hurt': 'hurt',
                       'die': 'dead'},
            'hurt':   {'done': 'idle', 'die': 'dead'},
            'dead':   {},
        }

        for direction in DIRECTIONS:
            for state_name, cfg in state_configs.items():
                frames = make_player_frames(state_name, direction)
                key = (state_name, direction)
                anim = AnimationStateMachine()
                anim.add_state(state_name, frames, fps=cfg['fps'],
                              loop=cfg['loop'], transitions=transitions.get(state_name, {}))
                # Also add all other states to this anim machine so transitions work
                for other_state, other_cfg in state_configs.items():
                    if other_state == state_name:
                        continue
                    other_frames = make_player_frames(other_state, direction)
                    anim.add_state(other_state, other_frames, fps=other_cfg['fps'],
                                  loop=other_cfg['loop'],
                                  transitions=transitions.get(other_state, {}))
                anim.set_state(state_name)
                self._anim_sets[key] = anim

        # Current state
        self._current_state = 'idle'
        self._current_direction = 'front'
        self._dead = False

        # Tracking
        self._shoot_timer = 0.0
        self._hurt_timer = 0.0

    def _get_anim(self):
        return self._anim_sets.get((self._current_state, self._current_direction),
                                   self._anim_sets.get(('idle', 'front')))

    def _set_direction(self, facing_angle):
        """Determine cardinal direction from facing angle."""
        # facing angle in radians: 0=right, pi/2=down(front), pi=left, -pi/2=up(back)
        # Convert to degrees for easier logic
        deg = math.degrees(facing_angle) % 360
        if 45 <= deg < 135:
            self._current_direction = 'front'    # facing down (toward viewer)
        elif 135 <= deg < 225:
            self._current_direction = 'left'
        elif 225 <= deg < 315:
            self._current_direction = 'back'     # facing up (away from viewer)
        else:
            self._current_direction = 'right'

    def update(self, dt, player, is_firing=False, is_reloading=False):
        """Update animation based on player state."""
        # Determine direction from facing
        self._set_direction(player.facing)

        if self._dead:
            anim = self._get_anim()
            anim.update(dt)
            return

        if player.health <= 0 and not self._dead:
            self._dead = True
            self._current_state = 'dead'
            anim = self._get_anim()
            anim.set_state('dead', reset=True)
            anim.update(dt)
            return

        # Determine movement state
        speed_sq = getattr(player, '_speed_sq', 0)
        is_moving = speed_sq > 100
        is_sprint = player.sprinting and is_moving

        # Hurt overrides
        if self._hurt_timer > 0:
            self._hurt_timer -= dt
            if self._current_state != 'hurt':
                self._current_state = 'hurt'
                self._get_anim().set_state('hurt', reset=True)
            self._get_anim().update(dt)
            if self._get_anim().is_finished:
                self._current_state = 'idle'
                self._get_anim().set_state('idle')
            return

        # Reload
        if is_reloading:
            if self._current_state != 'reload':
                self._current_state = 'reload'
                self._get_anim().set_state('reload', reset=True)
            self._get_anim().update(dt)
            if self._get_anim().is_finished:
                self._current_state = 'idle'
                self._get_anim().set_state('idle')
            return

        # Shoot
        if is_firing:
            self._shoot_timer = 0.1
            if self._current_state != 'shoot':
                self._current_state = 'shoot'
                self._get_anim().set_state('shoot', reset=True)

        if self._shoot_timer > 0:
            self._shoot_timer -= dt
            self._get_anim().update(dt)
            if self._get_anim().is_finished:
                self._current_state = 'idle'
                self._get_anim().set_state('idle')
            return

        # Movement
        new_state = self._current_state
        if is_sprint:
            new_state = 'sprint'
        elif is_moving:
            new_state = 'walk'
        else:
            new_state = 'idle'

        if new_state != self._current_state:
            self._current_state = new_state
            self._get_anim().set_state(new_state, reset=True)

        self._get_anim().update(dt)

    def trigger_hurt(self):
        self._hurt_timer = 0.3

    def draw(self, screen, player, cam_x, cam_y):
        """Draw the player sprite — no rotation, uses directional frames."""
        anim = self._get_anim()
        # Draw at player position, no rotation (directional sprites handle facing)
        surf = anim.current_surface
        if surf is None:
            return
        sx = int(player.x - cam_x)
        sy = int(player.y - cam_y)
        rect = surf.get_rect(center=(sx, sy))

        # Draw shadow first
        shadow = pygame.Surface((surf.get_width(), surf.get_height() // 2), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 60),
                           (0, 0, surf.get_width(), surf.get_height() // 2))
        screen.blit(shadow, (rect.x, rect.bottom - surf.get_height() // 4))

        screen.blit(surf, rect)
