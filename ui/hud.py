"""Full HUD system — all DESIGN.md components rendered with token colors.

Components:
  - Health bar (hud-panel + health-bar → health-bar-critical below 25%)
  - Ammo readout (mono digits, right-aligned)
  - Weapon slots (1-2-3, active highlighted)
  - Wave counter (top-center)
  - Kill counter (top-right)
  - Objective card (top-left, with progress bar)
  - Threat banner (full-bleed, bio-mass → danger during breach)
  - Extraction HUD (progress %, directional arrow)
  - Low-health vignette (pulsing red border)
  - Sprint indicator
"""
import math
import pygame

from config import (SCREEN_WIDTH, SCREEN_HEIGHT,
                    ON_PRIMARY, ON_SECONDARY, HULL_BLACK, ADRENALINE,
                    DANGER, WARNING, ACID, BIO_MASS, CONSOLE, BULKHEAD)
from combat.weapons import WEAPON_ORDER
from ui.motion_tracker import MotionTracker


class HUD:
    """Renders all HUD elements."""

    def __init__(self):
        self.motion_tracker = MotionTracker()
        self.threat_banner_timer = 0.0
        self.threat_active = False

    def update(self, dt, player, enemies, terrain):
        """Update motion tracker and threat state."""
        self.motion_tracker.update(dt, player, enemies, terrain)

        # Threat banner: active when enemies are very close
        near = sum(1 for e in enemies if not e.dead and
                   abs(e.x - player.x) < 100 and abs(e.y - player.y) < 100)
        if near >= 3:
            self.threat_active = True
            self.threat_banner_timer = 1.0
        else:
            self.threat_banner_timer = max(0, self.threat_banner_timer - dt)
            if self.threat_banner_timer <= 0:
                self.threat_active = False

    def draw(self, screen, font, med_font, small_font, player, weapons,
             wave_info, kills, objective, extraction_beacon, game_time,
             enemies=None, combo=0):
        """Draw all HUD elements."""
        self._draw_health(screen, font, player)
        self._draw_weapon_hud(screen, font, med_font, weapons)
        self._draw_wave_info(screen, font, wave_info)
        self._draw_kills(screen, font, kills)
        self._draw_objective(screen, font, objective)
        self._draw_threat_banner(screen, small_font)
        self._draw_extraction(screen, med_font, font, extraction_beacon, player)
        self._draw_low_health_vignette(screen, player)
        if combo >= 3:
            self._draw_combo(screen, med_font, combo)
        if enemies:
            self._draw_offscreen_indicators(screen, player, enemies)
        self.motion_tracker.draw(screen)

    def _draw_combo(self, screen, med_font, combo):
        text = f"x{combo} COMBO"
        color = WARNING if combo < 5 else ADRENALINE
        txt = med_font.render(text, True, color)
        screen.blit(txt, txt.get_rect(midtop=(SCREEN_WIDTH // 2, 40)))

    def _draw_offscreen_indicators(self, screen, player, enemies):
        """Draw arrows at screen edges pointing to off-screen enemies."""
        margin = 20
        for e in enemies:
            if e.dead or e.state == 'death':
                continue
            sx = e.x - player.x + SCREEN_WIDTH // 2
            sy = e.y - player.y + SCREEN_HEIGHT // 2
            if -margin < sx < SCREEN_WIDTH + margin and -margin < sy < SCREEN_HEIGHT + margin:
                continue  # on screen
            # Clamp to screen edge
            cx = max(margin, min(SCREEN_WIDTH - margin, sx))
            cy = max(margin, min(SCREEN_HEIGHT - margin, sy))
            # Arrow direction
            dx = e.x - player.x
            dy = e.y - player.y
            ang = math.atan2(dy, dx)
            # Color: red if close, amber if far
            dist = math.sqrt(dx * dx + dy * dy)
            color = DANGER if dist < 200 else WARNING
            # Draw triangle pointing toward enemy
            tip = (cx + math.cos(ang) * 8, cy + math.sin(ang) * 8)
            left = (cx + math.cos(ang + 2.5) * 5, cy + math.sin(ang + 2.5) * 5)
            right = (cx + math.cos(ang - 2.5) * 5, cy + math.sin(ang - 2.5) * 5)
            pygame.draw.polygon(screen, color, [tip, left, right])

    def _draw_health(self, screen, font, player):
        bar_w = 200; bar_h = 10; hx = 24; hy = SCREEN_HEIGHT - 44
        # Label
        screen.blit(font.render("INTEGRITY", True, ON_SECONDARY), (hx, hy - 20))
        # Beveled panel background (outer dark, inner panel)
        pygame.draw.rect(screen, (12, 16, 20), (hx - 5, hy - 5, bar_w + 10, bar_h + 10))
        pygame.draw.rect(screen, CONSOLE, (hx - 3, hy - 3, bar_w + 6, bar_h + 6))
        # Inner dark
        pygame.draw.rect(screen, (18, 22, 28), (hx, hy, bar_w, bar_h))
        # Fill with gradient effect (top brighter)
        hp_pct = player.health / player.max_health
        fill_w = int(bar_w * hp_pct)
        fill_color = ADRENALINE if hp_pct > 0.25 else DANGER
        if fill_w > 0:
            pygame.draw.rect(screen, fill_color, (hx, hy, fill_w, bar_h))
            # Top highlight (bevel)
            highlight = tuple(min(255, c + 40) for c in fill_color)
            pygame.draw.rect(screen, highlight, (hx, hy, fill_w, 2))
            # Bottom shadow
            shadow = tuple(max(0, c - 40) for c in fill_color)
            pygame.draw.rect(screen, shadow, (hx, hy + bar_h - 2, fill_w, 2))
        # Critical flash
        if hp_pct <= 0.25:
            flash = (math.sin(pygame.time.get_ticks() * 0.02) + 1) * 0.5
            if flash > 0.5:
                pygame.draw.rect(screen, (255, 255, 255), (hx, hy, fill_w, bar_h), 1)
        # Border
        pygame.draw.rect(screen, ON_SECONDARY, (hx - 3, hy - 3, bar_w + 6, bar_h + 6), 1)
        # HP text
        hp_text = font.render(f"{int(player.health)}/{int(player.max_health)}", True, ON_PRIMARY)
        screen.blit(hp_text, (hx + bar_w + 12, hy - 2))
        # Sprint
        if player.sprinting:
            screen.blit(font.render("[ SPRINT ]", True, WARNING), (hx + bar_w + 80, hy - 2))

    def _draw_weapon_hud(self, screen, font, med_font, weapons):
        wx = SCREEN_WIDTH - 24; wy = SCREEN_HEIGHT - 44
        weapon = weapons.current
        # Name
        name_text = med_font.render(weapon.name.upper().replace('_', ' '), True, ON_PRIMARY)
        screen.blit(name_text, name_text.get_rect(bottomright=(wx, wy - 8)))
        # Ammo
        if weapon.reloading:
            ammo_text = font.render("[ RELOADING ]", True, WARNING)
        else:
            col = DANGER if weapon.ammo == 0 else ON_PRIMARY
            ammo_text = med_font.render(f"{weapon.ammo} / {weapon.mag_size}", True, col)
        screen.blit(ammo_text, ammo_text.get_rect(bottomright=(wx, wy + 18)))
        # Reload progress bar
        if weapon.reloading:
            import time
            elapsed = time.monotonic() - weapon.reload_start
            pct = min(1.0, elapsed / weapon.reload_time)
            bar_w = 80; bar_h = 3
            bx = wx - bar_w
            by = wy + 22
            pygame.draw.rect(screen, CONSOLE, (bx, by, bar_w, bar_h))
            pygame.draw.rect(screen, WARNING, (bx, by, int(bar_w * pct), bar_h))
        # Slots
        slot_y = SCREEN_HEIGHT - 74
        for i, wname in enumerate(WEAPON_ORDER):
            slot_x = SCREEN_WIDTH - 120 + i * 35
            is_current = (i == weapons.current_idx)
            col = ADRENALINE if is_current else ON_SECONDARY
            screen.blit(font.render(f"{i+1}", True, col), (slot_x, slot_y))
            short = wname.split('_')[0][:4].upper()
            screen.blit(font.render(short, True, col), (slot_x + 12, slot_y))

    def _draw_wave_info(self, screen, font, wave_info):
        if wave_info['breather']:
            text = f"WAVE {wave_info['wave'] + 1} INCOMING — {wave_info['breather_time']:.1f}s"
            col = WARNING
        else:
            text = f"WAVE {wave_info['wave']} — {wave_info['remaining']} HOSTILES"
            col = DANGER
        wave_text = font.render(text, True, col)
        screen.blit(wave_text, wave_text.get_rect(midtop=(SCREEN_WIDTH // 2, 16)))

    def _draw_kills(self, screen, font, kills):
        screen.blit(font.render(f"KILLS: {kills}", True, ON_SECONDARY),
                    (24, 56))  # top-left, below objective

    def _draw_objective(self, screen, font, objective):
        if not objective:
            return
        obj_color = ACID if objective.complete else WARNING
        screen.blit(font.render(f"OBJ: {objective.name}", True, obj_color), (24, 16))
        if objective.target > 0:
            pw = 150
            ppct = objective.progress_pct
            pygame.draw.rect(screen, CONSOLE, (24, 38, pw, 4))
            pygame.draw.rect(screen, obj_color, (24, 38, int(pw * ppct), 4))

    def _draw_threat_banner(self, screen, small_font):
        if not self.threat_active:
            return
        # Full-bleed banner above HUD
        banner_y = SCREEN_HEIGHT - 90
        banner_h = 20
        col = DANGER if self.threat_banner_timer > 0.5 else BIO_MASS
        pygame.draw.rect(screen, col, (0, banner_y, SCREEN_WIDTH, banner_h))
        text = small_font.render("⚠ BREACH DETECTED — MULTIPLE HOSTILES ⚠", True,
                                  ON_PRIMARY if self.threat_banner_timer > 0.5 else WARNING)
        screen.blit(text, text.get_rect(center=(SCREEN_WIDTH // 2, banner_y + banner_h // 2)))

    def _draw_extraction(self, screen, med_font, font, beacon, player):
        if not beacon or not beacon.active:
            return
        # Progress
        ext_text = med_font.render(
            f"EXTRACTION  {beacon.hold_pct * 100:.0f}%", True, ADRENALINE)
        screen.blit(ext_text, ext_text.get_rect(midtop=(SCREEN_WIDTH // 2, 44)))
        # Direction arrow
        dx = beacon.x - player.x
        dy = beacon.y - player.y
        d = math.sqrt(dx * dx + dy * dy)
        if d > beacon.hold_radius:
            angle = math.atan2(dy, dx)
            ax = SCREEN_WIDTH // 2 + math.cos(angle) * 50
            ay = 80 + math.sin(angle) * 50
            pygame.draw.polygon(screen, ADRENALINE, [
                (ax + math.cos(angle) * 12, ay + math.sin(angle) * 12),
                (ax + math.cos(angle + 2.5) * 7, ay + math.sin(angle + 2.5) * 7),
                (ax + math.cos(angle - 2.5) * 7, ay + math.sin(angle - 2.5) * 7),
            ])

    def _draw_low_health_vignette(self, screen, player):
        hp_pct = player.health / player.max_health
        if hp_pct >= 0.25:
            return
        pulse = (math.sin(pygame.time.get_ticks() * 0.008) + 1) * 0.5
        vignette = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        for i in range(8):
            alpha = int(25 * pulse * (1 - i / 8))
            pygame.draw.rect(vignette, (255, 0, 0, alpha),
                            (i * 4, i * 4, SCREEN_WIDTH - i * 8, SCREEN_HEIGHT - i * 8), 4)
        screen.blit(vignette, (0, 0))
