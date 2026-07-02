"""Animation state machine — framework for sprite-based animation with states.

Each AnimationStateMachine holds a set of named states. Each state has:
  - frames: list of pygame Surfaces (the animation cels)
  - fps: playback speed
  - loop: whether to loop or hold on last frame
  - transitions: dict of {trigger_name: target_state}

The machine processes transitions based on external triggers (e.g. "start_walking",
"take_damage", "die"). This decouples game logic from visual representation.
"""
import math
import time


class AnimationState:
    """A single animation state (e.g. 'idle', 'walk', 'attack')."""
    def __init__(self, name, frames, fps=10, loop=True, transitions=None):
        self.name = name
        self.frames = frames
        self.fps = fps
        self.loop = loop
        self.transitions = transitions or {}
        self.frame_time = 1.0 / fps if fps > 0 else 0
        self.current_frame = 0
        self.timer = 0.0
        self.finished = False

    def reset(self):
        self.current_frame = 0
        self.timer = 0.0
        self.finished = False

    def update(self, dt):
        if self.finished or len(self.frames) <= 1:
            return
        self.timer += dt
        if self.timer >= self.frame_time:
            self.timer -= self.frame_time
            self.current_frame += 1
            if self.current_frame >= len(self.frames):
                if self.loop:
                    self.current_frame = 0
                else:
                    self.current_frame = len(self.frames) - 1
                    self.finished = True

    @property
    def current_surface(self):
        if not self.frames:
            return None
        return self.frames[min(self.current_frame, len(self.frames) - 1)]

    def add_transition(self, trigger, target_state):
        self.transitions[trigger] = target_state


class AnimationStateMachine:
    """Manages animation states and transitions for a sprite entity.

    Usage:
        anim = AnimationStateMachine()
        anim.add_state('idle', frames_list, fps=8, loop=True)
        anim.add_state('walk', frames_list, fps=12, loop=True,
                       transitions={'stop': 'idle'})
        anim.set_state('idle')
        # In update loop:
        anim.update(dt)
        # When player stops moving:
        anim.trigger('stop')
        # Get current frame to draw:
        surface = anim.current_surface
    """
    def __init__(self):
        self.states = {}
        self.current_state_name = None
        self.facing = 0.0  # radians, for rotation
        self.scale = 1.0

    def add_state(self, name, frames, fps=10, loop=True, transitions=None):
        self.states[name] = AnimationState(name, frames, fps, loop, transitions)

    def set_state(self, name, reset=True):
        if name not in self.states:
            return False
        if self.current_state_name == name and not reset:
            return True
        self.current_state_name = name
        if reset:
            self.states[name].reset()
        return True

    def trigger(self, trigger_name):
        """Fire a transition trigger. Returns True if a transition occurred."""
        if self.current_state_name is None:
            return False
        state = self.states[self.current_state_name]
        target = state.transitions.get(trigger_name)
        if target and target in self.states:
            self.set_state(target, reset=True)
            return True
        return False

    @property
    def current_state(self):
        if self.current_state_name is None:
            return None
        return self.states[self.current_state_name]

    @property
    def current_surface(self):
        state = self.current_state
        return state.current_surface if state else None

    @property
    def is_finished(self):
        state = self.current_state
        return state.finished if state else True

    def update(self, dt):
        state = self.current_state
        if state:
            state.update(dt)

    def draw(self, screen, x, y, cam_x, cam_y, rotation=0.0, scale=1.0):
        """Draw the current animation frame at screen position."""
        surf = self.current_surface
        if surf is None:
            return

        sx = int(x - cam_x)
        sy = int(y - cam_y)

        # Apply rotation if needed
        rot_deg = -math.degrees(rotation) if rotation != 0 else 0
        if rot_deg != 0 or scale != 1.0:
            w, h = surf.get_size()
            new_w = max(1, int(w * scale))
            new_h = max(1, int(h * scale))
            if scale != 1.0:
                surf = pygame.transform.smoothscale(surf, (new_w, new_h))
            if rot_deg != 0:
                surf = pygame.transform.rotate(surf, rot_deg)
            rect = surf.get_rect(center=(sx, sy))
            screen.blit(surf, rect)
        else:
            rect = surf.get_rect(center=(sx, sy))
            screen.blit(surf, rect)


import pygame
