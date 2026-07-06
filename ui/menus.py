"""Menu screens — title, briefing, pause, victory, gameover.

All screens use DESIGN.md token colors and IBM Plex Mono-style fonts.
"""
import math
import os
import sys
import pygame

from config import (SCREEN_WIDTH, SCREEN_HEIGHT,
                    ON_PRIMARY, ON_SECONDARY, HULL_BLACK, ADRENALINE,
                    DANGER, WARNING, ACID, CONSOLE, BULKHEAD)

def _resource_path(*parts):
    """Resolve a bundled resource path (works in PyInstaller exe and dev)."""
    if getattr(sys, 'frozen', False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, *parts)


class MenuRenderer:
    """Renders all menu and overlay screens."""

    def __init__(self):
        self.title_anim = 0.0
        # Load splash background
        self._splash = None
        self._gameover_bg = None
        splash_path = _resource_path("assets", "splash_background.png")
        gameover_path = _resource_path("assets", "gameover_background.png")
        if os.path.exists(splash_path):
            self._splash = pygame.image.load(splash_path)
            self._splash = pygame.transform.smoothscale(self._splash,
                                                        (SCREEN_WIDTH, SCREEN_HEIGHT))
        if os.path.exists(gameover_path):
            self._gameover_bg = pygame.image.load(gameover_path)
            self._gameover_bg = pygame.transform.smoothscale(self._gameover_bg,
                                                             (SCREEN_WIDTH, SCREEN_HEIGHT))
        # Clickable button rects: filled during draw, used by handle_mouse
        self._menu_rects = []
        self._pause_rects = []
        self._hover_idx = -1

    def update(self, dt):
        self.title_anim += dt

    def draw_title(self, screen, big_font, med_font, font, selected, options):
        """Draw the main title screen."""
        self._menu_rects = []
        # Splash background (or black fallback)
        if self._splash:
            screen.blit(self._splash, (0, 0))
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 120))
            screen.blit(overlay, (0, 0))
        else:
            screen.fill(HULL_BLACK)

        # Animated title glow
        glow = (math.sin(self.title_anim * 2) + 1) * 0.5
        glow_val = int(20 + glow * 30)

        title = big_font.render("XENO BREACH", True, ADRENALINE)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 100))
        glow_pulse = (math.sin(self.title_anim * 2) + 1) * 0.5
        if glow_pulse > 0.3:
            glow_surf = big_font.render("XENO BREACH", True, ADRENALINE)
            glow_surf = pygame.transform.smoothscale(glow_surf,
                           (glow_surf.get_width() + 8, glow_surf.get_height() + 4))
            glow_surf.set_alpha(int(40 * glow_pulse))
            glow_rect = glow_surf.get_rect(center=title_rect.center)
            screen.blit(glow_surf, glow_rect)
        screen.blit(title, title_rect)

        subtitle = font.render("PROCEDURAL SURVIVAL SHOOTER", True, ON_SECONDARY)
        screen.blit(subtitle, subtitle.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 60)))

        # Menu options — store rects for mouse clicks
        mouse_pos = pygame.mouse.get_pos()
        for i, opt in enumerate(options):
            is_hover = False
            col = ADRENALINE if i == selected else ON_SECONDARY
            txt = med_font.render(opt, True, col)
            r = txt.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + i * 50))
            # Expand rect for easier clicking
            click_r = r.inflate(40, 16)
            if click_r.collidepoint(mouse_pos):
                is_hover = True
                col = ADRENALINE
                # Draw hover background
                bg = pygame.Surface((click_r.w, click_r.h), pygame.SRCALPHA)
                bg.fill((*ADRENALINE, 30))
                screen.blit(bg, click_r.topleft)
            screen.blit(txt, r)
            if i == selected or is_hover:
                offset = int(math.sin(self.title_anim * 4) * 3)
                arrow = med_font.render(">", True, ADRENALINE)
                screen.blit(arrow, (r.x - 30 + offset, r.y))
            self._menu_rects.append((click_r, i))

        # Controls
        controls = [
            "WASD = MOVE    MOUSE = AIM    LMB = FIRE",
            "1/2/3 = WEAPONS    R = RELOAD    SHIFT = SPRINT",
            "M = MUTE    F1 = DEBUG    ESC = PAUSE",
        ]
        for i, c in enumerate(controls):
            txt = font.render(c, True, ON_SECONDARY)
            screen.blit(txt, txt.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 80 + i * 20)))

    def handle_title_mouse(self, pos, clicked):
        """Handle mouse on title screen. Returns selected index if clicked, -1 otherwise."""
        for rect, idx in self._menu_rects:
            if rect.collidepoint(pos):
                if clicked:
                    return idx
                return -2  # hover
        return -1

    def draw_briefing(self, screen, big_font, med_font, font, run_seed, biome, objective):
        """Draw mission briefing screen."""
        screen.fill(HULL_BLACK)

        # Header
        screen.blit(big_font.render("MISSION BRIEFING", True, ADRENALINE),
                    big_font.render("MISSION BRIEFING", True, ADRENALINE).get_rect(
                        center=(SCREEN_WIDTH // 2, 80)))

        # Sector
        screen.blit(font.render(f"SECTOR LV-{run_seed:05d}", True, ON_SECONDARY),
                    font.render(f"SECTOR LV-{run_seed:05d}", True, ON_SECONDARY).get_rect(
                        center=(SCREEN_WIDTH // 2, 120)))

        # Biome
        screen.blit(med_font.render(biome.name, True, WARNING),
                    med_font.render(biome.name, True, WARNING).get_rect(
                        center=(SCREEN_WIDTH // 2, 180)))
        screen.blit(font.render(biome.description, True, ON_SECONDARY),
                    font.render(biome.description, True, ON_SECONDARY).get_rect(
                        center=(SCREEN_WIDTH // 2, 210)))

        # Divider
        pygame.draw.line(screen, ON_SECONDARY,
                        (SCREEN_WIDTH // 4, 250), (3 * SCREEN_WIDTH // 4, 250), 1)

        # Objective
        screen.blit(med_font.render("OBJECTIVE", True, ON_PRIMARY),
                    med_font.render("OBJECTIVE", True, ON_PRIMARY).get_rect(
                        center=(SCREEN_WIDTH // 2, 290)))
        screen.blit(med_font.render(objective.name, True, WARNING),
                    med_font.render(objective.name, True, WARNING).get_rect(
                        center=(SCREEN_WIDTH // 2, 330)))
        screen.blit(font.render(objective.description, True, ON_PRIMARY),
                    font.render(objective.description, True, ON_PRIMARY).get_rect(
                        center=(SCREEN_WIDTH // 2, 360)))

        # Deploy prompt
        pulse = (math.sin(self.title_anim * 3) + 1) * 0.5
        col = ADRENALINE if pulse > 0.5 else ON_PRIMARY
        screen.blit(med_font.render("[ SPACE ] DEPLOY", True, col),
                    med_font.render("[ SPACE ] DEPLOY", True, col).get_rect(
                        center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100)))

    def draw_paused(self, screen, big_font, font, selected=0, options=None):
        """Draw pause overlay with menu options."""
        if options is None:
            options = ["RESUME", "RESTART", "QUIT TO MENU"]
        self._pause_rects = []
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))
        screen.blit(big_font.render("PAUSED", True, ON_PRIMARY),
                    big_font.render("PAUSED", True, ON_PRIMARY).get_rect(
                        center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 60)))
        mouse_pos = pygame.mouse.get_pos()
        for i, opt in enumerate(options):
            is_hover = False
            col = ADRENALINE if i == selected else ON_SECONDARY
            txt = font.render(opt, True, col)
            r = txt.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + i * 30))
            click_r = r.inflate(40, 12)
            if click_r.collidepoint(mouse_pos):
                is_hover = True
                col = ADRENALINE
                bg = pygame.Surface((click_r.w, click_r.h), pygame.SRCALPHA)
                bg.fill((*ADRENALINE, 30))
                screen.blit(bg, click_r.topleft)
            screen.blit(txt, r)
            self._pause_rects.append((click_r, i))
        screen.blit(font.render("[ UP/DN ] SELECT   [ ENTER ] CONFIRM   [ ESC ] RESUME", True, ON_SECONDARY),
                    font.render("[ UP/DN ] SELECT   [ ENTER ] CONFIRM   [ ESC ] RESUME", True, ON_SECONDARY).get_rect(
                        center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 40)))

    def handle_pause_mouse(self, pos, clicked):
        """Handle mouse on pause screen. Returns selected index if clicked, -1 otherwise."""
        for rect, idx in self._pause_rects:
            if rect.collidepoint(pos):
                if clicked:
                    return idx
                return -2
        return -1

    def draw_gameover(self, screen, big_font, med_font, font, is_victory, stats):
        """Draw game over / victory screen."""
        # Background image (or dark overlay)
        if self._gameover_bg and not is_victory:
            screen.blit(self._gameover_bg, (0, 0))
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 140))
            screen.blit(overlay, (0, 0))
        else:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))

        if is_victory:
            title = big_font.render("EXTRACTED", True, ACID)
        else:
            title = big_font.render("SIGNAL LOST", True, DANGER)
        screen.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 80)))

        for i, s in enumerate(stats):
            txt = med_font.render(s, True, ON_PRIMARY)
            screen.blit(txt, txt.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + i * 32)))

        screen.blit(font.render("[ ENTER ] RETURN TO MENU    [ ESC ] QUIT", True, ON_SECONDARY),
                    font.render("[ ENTER ] RETURN TO MENU    [ ESC ] QUIT", True, ON_SECONDARY).get_rect(
                        center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 80)))
