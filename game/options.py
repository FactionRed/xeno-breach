"""Options screen — resolution, fullscreen, sound volume, screen shake.

Settings persist in ~/.xeno_breach/settings.json alongside the save file.
"""
import json
import os
import math
import pygame

from config import (SCREEN_WIDTH, SCREEN_HEIGHT,
                    ON_PRIMARY, ON_SECONDARY, HULL_BLACK, ADRENALINE,
                    DANGER, WARNING, ACID, CONSOLE, BULKHEAD)

# Available resolutions (16:9 only)
RESOLUTIONS = [
    (1280, 720),   # 720p
    (1600, 900),   # 900p
    (1920, 1080),  # 1080p
    (2560, 1440),  # 1440p
]


class GameSettings:
    """Persistent game settings."""

    def __init__(self):
        self.resolution_idx = 0  # index into RESOLUTIONS
        self.fullscreen = False
        self.master_volume = 0.7  # 0.0 to 1.0
        self.sfx_volume = 0.8
        self.screen_shake = True
        self.show_fps = False
        self._load()

    def _path(self):
        home = os.path.expanduser('~')
        d = os.path.join(home, '.xeno_breach')
        os.makedirs(d, exist_ok=True)
        return os.path.join(d, 'settings.json')

    def _load(self):
        path = self._path()
        if not os.path.exists(path):
            return
        try:
            with open(path) as f:
                data = json.load(f)
            self.resolution_idx = data.get('resolution_idx', 0)
            self.fullscreen = data.get('fullscreen', False)
            self.master_volume = data.get('master_volume', 0.7)
            self.sfx_volume = data.get('sfx_volume', 0.8)
            self.screen_shake = data.get('screen_shake', True)
            self.show_fps = data.get('show_fps', False)
        except (json.JSONDecodeError, IOError):
            pass

    def save(self):
        data = {
            'resolution_idx': self.resolution_idx,
            'fullscreen': self.fullscreen,
            'master_volume': self.master_volume,
            'sfx_volume': self.sfx_volume,
            'screen_shake': self.screen_shake,
            'show_fps': self.show_fps,
        }
        with open(self._path(), 'w') as f:
            json.dump(data, f, indent=2)

    @property
    def resolution(self):
        return RESOLUTIONS[self.resolution_idx]

    @property
    def width(self):
        return self.resolution[0]

    @property
    def height(self):
        return self.resolution[1]


class OptionsScreen:
    """Renders the options screen and handles input."""

    def __init__(self, settings: GameSettings):
        self.settings = settings
        self.selected = 0
        self.anim_time = 0.0
        self.needs_apply = False  # set when resolution/fullscreen changes

    @property
    def items(self):
        return ['resolution', 'fullscreen', 'master_volume',
                'sfx_volume', 'screen_shake', 'show_fps']

    @property
    def labels(self):
        return ['Resolution', 'Fullscreen', 'Master Volume',
                'SFX Volume', 'Screen Shake', 'Show FPS']

    def update(self, dt):
        self.anim_time += dt

    def handle_input(self, key):
        """Returns 'apply', 'back', or None."""
        if key in (pygame.K_UP, pygame.K_w):
            self.selected = (self.selected - 1) % len(self.items)
            return None
        elif key in (pygame.K_DOWN, pygame.K_s):
            self.selected = (self.selected + 1) % len(self.items)
            return None
        elif key in (pygame.K_LEFT, pygame.K_a):
            self._change(-1)
            return None
        elif key in (pygame.K_RIGHT, pygame.K_d):
            self._change(1)
            return None
        elif key in (pygame.K_RETURN, pygame.K_SPACE):
            self._toggle()
            return None
        elif key == pygame.K_ESCAPE:
            self.settings.save()
            if self.needs_apply:
                return 'apply'
            return 'back'
        return None

    def _change(self, direction):
        item = self.items[self.selected]
        if item == 'resolution':
            self.resolution_idx = (self.settings.resolution_idx + direction) % len(RESOLUTIONS)
            self.settings.resolution_idx = self.resolution_idx
            self.needs_apply = True
        elif item == 'master_volume':
            self.settings.master_volume = max(0.0, min(1.0, self.settings.master_volume + direction * 0.1))
        elif item == 'sfx_volume':
            self.settings.sfx_volume = max(0.0, min(1.0, self.settings.sfx_volume + direction * 0.1))
        elif item in ('fullscreen', 'screen_shake', 'show_fps'):
            # Toggle for ENTER, ignore L/R
            pass

    def _toggle(self):
        item = self.items[self.selected]
        if item == 'resolution':
            self.settings.resolution_idx = (self.settings.resolution_idx + 1) % len(RESOLUTIONS)
            self.needs_apply = True
        elif item == 'fullscreen':
            self.settings.fullscreen = not self.settings.fullscreen
            self.needs_apply = True
        elif item == 'master_volume':
            self.settings.master_volume = max(0.0, min(1.0, self.settings.master_volume + 0.1))
            if self.settings.master_volume > 0.99:
                self.settings.master_volume = 0.0
        elif item == 'sfx_volume':
            self.settings.sfx_volume = max(0.0, min(1.0, self.settings.sfx_volume + 0.1))
            if self.settings.sfx_volume > 0.99:
                self.settings.sfx_volume = 0.0
        elif item == 'screen_shake':
            self.settings.screen_shake = not self.settings.screen_shake
        elif item == 'show_fps':
            self.settings.show_fps = not self.settings.show_fps

    def draw(self, screen, font, big_font, small_font):
        screen.fill(HULL_BLACK)

        # Title
        title = big_font.render("OPTIONS", True, ADRENALINE)
        screen.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, 50)))

        # Settings list
        y_start = 120
        row_h = 56
        for i, (item, label) in enumerate(zip(self.items, self.labels)):
            y = y_start + i * row_h
            is_selected = (i == self.selected)
            panel_w = 500
            panel_x = (SCREEN_WIDTH - panel_w) // 2

            # Row bg
            bg_col = CONSOLE if is_selected else BULKHEAD
            pygame.draw.rect(screen, bg_col, (panel_x, y, panel_w, row_h - 6))
            if is_selected:
                pygame.draw.rect(screen, ADRENALINE, (panel_x, y, panel_w, row_h - 6), 2)

            # Label
            name_col = ON_PRIMARY if is_selected else ON_SECONDARY
            screen.blit(font.render(label, True, name_col), (panel_x + 16, y + 6))

            # Value
            val_col = ACID if is_selected else ON_SECONDARY
            if item == 'resolution':
                w, h = self.settings.resolution
                val_text = f"{w} x {h}"
            elif item == 'fullscreen':
                val_text = "ON" if self.settings.fullscreen else "OFF"
                val_col = ACID if self.settings.fullscreen else ON_SECONDARY
            elif item == 'master_volume':
                val_text = f"{int(self.settings.master_volume * 100)}%"
                self._draw_volume_bar(screen, panel_x + 250, y + 20, 150, 8,
                                      self.settings.master_volume, is_selected)
            elif item == 'sfx_volume':
                val_text = f"{int(self.settings.sfx_volume * 100)}%"
                self._draw_volume_bar(screen, panel_x + 250, y + 20, 150, 8,
                                      self.settings.sfx_volume, is_selected)
            elif item == 'screen_shake':
                val_text = "ON" if self.settings.screen_shake else "OFF"
                val_col = ACID if self.settings.screen_shake else ON_SECONDARY
            elif item == 'show_fps':
                val_text = "ON" if self.settings.show_fps else "OFF"
                val_col = ACID if self.settings.show_fps else ON_SECONDARY
            else:
                val_text = ""

            val_surf = font.render(val_text, True, val_col)
            screen.blit(val_surf, val_surf.get_rect(right=panel_x + panel_w - 16, centery=y + 16))

            # L/R hint for selected
            if is_selected:
                hint = small_font.render("< L/R >", True, WARNING)
                screen.blit(hint, hint.get_rect(right=panel_x + panel_w - 16, centery=y + 38))

        # Apply notice
        if self.needs_apply:
            pulse = (math.sin(self.anim_time * 4) + 1) * 0.5
            col = WARNING if pulse > 0.5 else DANGER
            notice = font.render("Press ESC to apply changes", True, col)
            screen.blit(notice, notice.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 56)))

        # Controls
        hint = small_font.render("[UP/DOWN] Select  [L/R] Change  [ENTER] Toggle  [ESC] Save & Back", True, ON_SECONDARY)
        screen.blit(hint, hint.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 22)))

    def _draw_volume_bar(self, screen, x, y, w, h, pct, active):
        pygame.draw.rect(screen, (30, 34, 38), (x, y, w, h))
        fill_w = int(w * pct)
        if fill_w > 0:
            col = ACID if active else ON_SECONDARY
            pygame.draw.rect(screen, col, (x, y, fill_w, h))
        pygame.draw.rect(screen, (50, 54, 58), (x, y, w, h), 1)
