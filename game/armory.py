"""Armory screen — between-run upgrade shop.

Displays the upgrade tree, salvage balance, and lets the player
purchase upgrades with earned salvage. Accessed from the main menu
or after a run ends.

Navigation:
  UP/DOWN — select upgrade
  LEFT/RIGHT — select upgrade (alt)
  ENTER — purchase selected upgrade
  SPACE — deploy (start new run)
  ESC — back to menu
"""
import math
import pygame

from config import (SCREEN_WIDTH, SCREEN_HEIGHT,
                    ON_PRIMARY, ON_SECONDARY, HULL_BLACK, ADRENALINE,
                    DANGER, WARNING, ACID, CONSOLE, BULKHEAD)
from game.meta_progression import MetaState, UPGRADES, UPGRADE_ORDER


class ArmoryScreen:
    """Renders the armory upgrade screen and handles input."""

    def __init__(self):
        self.selected = 0
        self.anim_time = 0.0
        self.purchase_flash = 0.0
        self.purchase_msg = ""
        self.purchase_msg_color = ACID

    def update(self, dt):
        self.anim_time += dt
        self.purchase_flash = max(0, self.purchase_flash - dt * 3)

    def handle_input(self, key, meta: MetaState):
        """Handle key press. Returns 'deploy', 'back', or None."""
        if key == pygame.K_UP or key == pygame.K_w:
            self.selected = (self.selected - 1) % len(UPGRADE_ORDER)
        elif key == pygame.K_DOWN or key == pygame.K_s:
            self.selected = (self.selected + 1) % len(UPGRADE_ORDER)
        elif key in (pygame.K_RETURN, pygame.K_SPACE):
            if key == pygame.K_SPACE:
                return 'deploy'
            key_name = UPGRADE_ORDER[self.selected]
            if meta.can_purchase(key_name):
                upgrade = UPGRADES[key_name]
                tier = meta.get_tier(key_name)
                meta.purchase(key_name)
                self.purchase_flash = 1.0
                self.purchase_msg = f"PURCHASED: {upgrade.name} T{tier+1}"
                self.purchase_msg_color = ACID
            elif meta.is_maxed(key_name):
                self.purchase_flash = 1.0
                self.purchase_msg = "MAXED OUT"
                self.purchase_msg_color = WARNING
            else:
                cost = meta.get_next_tier_cost(key_name)
                self.purchase_flash = 1.0
                self.purchase_msg = f"NEED {cost} SALVAGE"
                self.purchase_msg_color = DANGER
        elif key == pygame.K_ESCAPE:
            return 'back'
        return None

    def draw(self, screen, meta: MetaState, font, big_font, small_font):
        """Draw the full armory screen."""
        screen.fill(HULL_BLACK)

        # Title
        title = big_font.render("ARMORY", True, ADRENALINE)
        screen.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, 40)))

        # Salvage balance
        salvage_text = font.render(f"SALVAGE: {meta.salvage}", True, WARNING)
        screen.blit(salvage_text, salvage_text.get_rect(center=(SCREEN_WIDTH // 2, 70)))

        # Stats line
        stats = f"RUNS: {meta.total_runs}  KILLS: {meta.total_kills}  EXTRACTS: {meta.total_extractions}  BEST WAVE: {meta.best_wave}"
        stats_text = small_font.render(stats, True, ON_SECONDARY)
        screen.blit(stats_text, stats_text.get_rect(center=(SCREEN_WIDTH // 2, 92)))

        # Upgrade list
        y_start = 120
        row_h = 56
        for i, key in enumerate(UPGRADE_ORDER):
            upgrade = UPGRADES[key]
            tier = meta.get_tier(key)
            is_selected = (i == self.selected)
            is_maxed = meta.is_maxed(key)
            can_buy = meta.can_purchase(key)

            y = y_start + i * row_h

            # Row background
            if is_selected:
                bg_col = CONSOLE
            else:
                bg_col = BULKHEAD
            pygame.draw.rect(screen, bg_col, (40, y, SCREEN_WIDTH - 80, row_h - 4))
            if is_selected:
                pygame.draw.rect(screen, ADRENALINE, (40, y, SCREEN_WIDTH - 80, row_h - 4), 2)

            # Name
            name_col = ON_PRIMARY if is_selected else ON_SECONDARY
            name_text = font.render(upgrade.name, True, name_col)
            screen.blit(name_text, (60, y + 4))

            # Description
            desc_text = small_font.render(upgrade.description, True, ON_SECONDARY)
            screen.blit(desc_text, (60, y + 24))

            # Tier indicators (3 pips)
            for t in range(upgrade.max_tier):
                px = 60 + t * 14
                py = y + 42
                if t < tier:
                    col = ACID
                elif t == tier and can_buy:
                    col = WARNING
                else:
                    col = (40, 44, 48)
                pygame.draw.rect(screen, col, (px, py, 10, 6))
                pygame.draw.rect(screen, ON_SECONDARY, (px, py, 10, 6), 1)

            # Current effect
            if tier > 0:
                effect = upgrade.tiers[tier - 1]['desc']
                eff_text = small_font.render(f"Current: {effect}", True, ACID)
                screen.blit(eff_text, (200, y + 42))

            # Cost / status (right side)
            if is_maxed:
                cost_text = font.render("MAX", True, ACID)
            else:
                cost = upgrade.tiers[tier]['cost']
                col = ACID if can_buy else DANGER
                cost_text = font.render(f"{cost}", True, col)
            screen.blit(cost_text, cost_text.get_rect(right=SCREEN_WIDTH - 60, centery=y + 20))

            # Next tier effect
            if not is_maxed:
                next_effect = upgrade.tiers[tier]['desc']
                ne_text = small_font.render(f"Next: {next_effect}", True, ON_SECONDARY)
                screen.blit(ne_text, ne_text.get_rect(right=SCREEN_WIDTH - 60, centery=y + 40))

        # Purchase message
        if self.purchase_flash > 0:
            alpha = min(255, int(255 * self.purchase_flash))
            msg_surf = font.render(self.purchase_msg, True, self.purchase_msg_color)
            msg_surf.set_alpha(alpha)
            screen.blit(msg_surf, msg_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 60)))

        # Controls hint
        pulse = (math.sin(self.anim_time * 3) + 1) * 0.5
        col = ADRENALINE if pulse > 0.5 else ON_PRIMARY
        hint = small_font.render("[ UP/DN ] SELECT   [ ENTER ] PURCHASE   [ SPACE ] DEPLOY   [ ESC ] MENU", True, col)
        screen.blit(hint, hint.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 24)))
