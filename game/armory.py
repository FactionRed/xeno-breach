"""Armory screen — between-run upgrade shop + weapon loadout.

Two tabs:
  1. UPGRADES — spend salvage on 8 permanent upgrades (3 tiers each)
  2. WEAPONS — unlock new weapons + select 3-weapon loadout

Navigation:
  TAB — switch between UPGRADES and WEAPONS tabs
  UP/DOWN — select item
  ENTER — purchase/unlock/equip selected item
  SPACE — deploy (start new run)
  ESC — back to menu
"""
import math
import pygame

from config import (SCREEN_WIDTH, SCREEN_HEIGHT,
                    ON_PRIMARY, ON_SECONDARY, HULL_BLACK, ADRENALINE,
                    DANGER, WARNING, ACID, CONSOLE, BULKHEAD)
from game.meta_progression import MetaState, UPGRADES, UPGRADE_ORDER
from combat.weapons import (WEAPON_STATS, WEAPON_ORDER, WEAPON_UNLOCK_COST,
                            WEAPON_SHORT_NAMES, DEFAULT_WEAPONS)


class ArmoryScreen:
    """Renders the armory upgrade screen and handles input."""

    def __init__(self):
        self.tab = 0  # 0=upgrades, 1=weapons
        self.selected = 0
        self.anim_time = 0.0
        self.purchase_flash = 0.0
        self.purchase_msg = ""
        self.purchase_msg_color = ACID
        # Loadout selection: index into unlocked_weapons for each slot
        self.loadout_edit = [0, 1, 2]  # indices into unlocked list
        self.loadout_slot = 0  # which slot we're editing

    def update(self, dt):
        self.anim_time += dt
        self.purchase_flash = max(0, self.purchase_flash - dt * 3)

    def handle_input(self, key, meta: MetaState):
        """Handle key press. Returns 'deploy', 'back', or None."""
        if key == pygame.K_TAB:
            self.tab = 1 - self.tab
            self.selected = 0
            self.loadout_slot = 0
            return None
        if key == pygame.K_UP or key == pygame.K_w:
            if self.tab == 0:
                self.selected = (self.selected - 1) % len(UPGRADE_ORDER)
            else:
                max_sel = max(0, len(meta.unlocked_weapons) - 1)
                self.loadout_slot = (self.loadout_slot - 1) % 3
            return None
        elif key == pygame.K_DOWN or key == pygame.K_s:
            if self.tab == 0:
                self.selected = (self.selected + 1) % len(UPGRADE_ORDER)
            else:
                self.loadout_slot = (self.loadout_slot + 1) % 3
            return None
        elif key == pygame.K_LEFT or key == pygame.K_a:
            if self.tab == 1:
                # Cycle weapon in this loadout slot
                unlocked = meta.unlocked_weapons
                idx = self.loadout_edit[self.loadout_slot]
                idx = (idx - 1) % len(unlocked)
                self.loadout_edit[self.loadout_slot] = idx
            return None
        elif key == pygame.K_RIGHT or key == pygame.K_d:
            if self.tab == 1:
                unlocked = meta.unlocked_weapons
                idx = self.loadout_edit[self.loadout_slot]
                idx = (idx + 1) % len(unlocked)
                self.loadout_edit[self.loadout_slot] = idx
            return None
        elif key == pygame.K_RETURN:
            if self.tab == 0:
                self._try_purchase_upgrade(meta)
            else:
                self._try_unlock_or_confirm_loadout(meta)
            return None
        elif key == pygame.K_SPACE:
            # Apply loadout before deploying
            if self.tab == 1:
                self._apply_loadout(meta)
            return 'deploy'
        elif key == pygame.K_ESCAPE:
            return 'back'
        return None

    def _try_purchase_upgrade(self, meta):
        key_name = UPGRADE_ORDER[self.selected]
        if meta.can_purchase(key_name):
            upgrade = UPGRADES[key_name]
            tier = meta.get_tier(key_name)
            meta.purchase(key_name)
            self._flash(f"PURCHASED: {upgrade.name} T{tier+1}", ACID)
        elif meta.is_maxed(key_name):
            self._flash("MAXED OUT", WARNING)
        else:
            cost = meta.get_next_tier_cost(key_name)
            self._flash(f"NEED {cost} SALVAGE", DANGER)

    def _try_unlock_or_confirm_loadout(self, meta):
        # If selected weapon is locked, try to unlock it
        unlocked = meta.unlocked_weapons
        # Find the next locked weapon
        for wname in WEAPON_ORDER:
            if not meta.is_weapon_unlocked(wname):
                cost = meta.get_weapon_unlock_cost(wname)
                if cost is not None and meta.salvage >= cost:
                    meta.unlock_weapon(wname)
                    self._flash(f"UNLOCKED: {WEAPON_SHORT_NAMES.get(wname, wname)}", ACID)
                elif cost is not None:
                    self._flash(f"NEED {cost} SALVAGE", DANGER)
                return
        # All weapons unlocked — apply loadout
        self._apply_loadout(meta)
        self._flash("LOADOUT SAVED", ACID)

    def _apply_loadout(self, meta):
        unlocked = meta.unlocked_weapons
        loadout = [unlocked[self.loadout_edit[i] % len(unlocked)] for i in range(3)]
        meta.set_loadout(loadout)

    def _flash(self, msg, color):
        self.purchase_flash = 1.0
        self.purchase_msg = msg
        self.purchase_msg_color = color

    def draw(self, screen, meta: MetaState, font, big_font, small_font):
        """Draw the full armory screen."""
        screen.fill(HULL_BLACK)

        # Title
        title = big_font.render("ARMORY", True, ADRENALINE)
        screen.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, 36)))

        # Tabs
        tab_y = 62
        tab_labels = ["[TAB] UPGRADES", "[TAB] WEAPONS"]
        for i, label in enumerate(tab_labels):
            col = ADRENALINE if i == self.tab else ON_SECONDARY
            txt = font.render(label, True, col)
            x = SCREEN_WIDTH // 2 + (i - 0.5) * 180 - txt.get_width() // 2
            screen.blit(txt, (x, tab_y))

        # Salvage balance
        salvage_text = font.render(f"SALVAGE: {meta.salvage}", True, WARNING)
        screen.blit(salvage_text, salvage_text.get_rect(center=(SCREEN_WIDTH // 2, 88)))

        # Stats line
        stats = f"RUNS: {meta.total_runs}  KILLS: {meta.total_kills}  BEST WAVE: {meta.best_wave}"
        stats_text = small_font.render(stats, True, ON_SECONDARY)
        screen.blit(stats_text, stats_text.get_rect(center=(SCREEN_WIDTH // 2, 106)))

        if self.tab == 0:
            self._draw_upgrades_tab(screen, meta, font, small_font)
        else:
            self._draw_weapons_tab(screen, meta, font, small_font)

        # Purchase message
        if self.purchase_flash > 0:
            alpha = min(255, int(255 * self.purchase_flash))
            msg_surf = font.render(self.purchase_msg, True, self.purchase_msg_color)
            msg_surf.set_alpha(alpha)
            screen.blit(msg_surf, msg_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 60)))

        # Controls hint
        pulse = (math.sin(self.anim_time * 3) + 1) * 0.5
        col = ADRENALINE if pulse > 0.5 else ON_PRIMARY
        hint = small_font.render("[ TAB ] SWITCH   [ UP/DN ] SELECT   [ ENTER ] BUY/UNLOCK   [ L/R ] CHANGE SLOT   [ SPACE ] DEPLOY   [ ESC ] MENU", True, col)
        screen.blit(hint, hint.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 24)))

    def _draw_upgrades_tab(self, screen, meta, font, small_font):
        y_start = 128
        row_h = 56
        for i, key in enumerate(UPGRADE_ORDER):
            upgrade = UPGRADES[key]
            tier = meta.get_tier(key)
            is_selected = (i == self.selected)
            is_maxed = meta.is_maxed(key)
            can_buy = meta.can_purchase(key)

            y = y_start + i * row_h
            bg_col = CONSOLE if is_selected else BULKHEAD
            pygame.draw.rect(screen, bg_col, (40, y, SCREEN_WIDTH - 80, row_h - 4))
            if is_selected:
                pygame.draw.rect(screen, ADRENALINE, (40, y, SCREEN_WIDTH - 80, row_h - 4), 2)

            name_col = ON_PRIMARY if is_selected else ON_SECONDARY
            screen.blit(font.render(upgrade.name, True, name_col), (60, y + 4))
            screen.blit(small_font.render(upgrade.description, True, ON_SECONDARY), (60, y + 24))

            # Tier pips
            for t in range(upgrade.max_tier):
                px = 60 + t * 14
                py = y + 42
                col = ACID if t < tier else (WARNING if t == tier and can_buy else (40, 44, 48))
                pygame.draw.rect(screen, col, (px, py, 10, 6))
                pygame.draw.rect(screen, ON_SECONDARY, (px, py, 10, 6), 1)

            if tier > 0:
                eff = upgrade.tiers[tier - 1]['desc']
                screen.blit(small_font.render(f"Current: {eff}", True, ACID), (200, y + 42))

            if is_maxed:
                cost_text = font.render("MAX", True, ACID)
            else:
                cost = upgrade.tiers[tier]['cost']
                col = ACID if can_buy else DANGER
                cost_text = font.render(f"{cost}", True, col)
            screen.blit(cost_text, cost_text.get_rect(right=SCREEN_WIDTH - 60, centery=y + 20))

    def _draw_weapons_tab(self, screen, meta, font, small_font):
        unlocked = meta.unlocked_weapons
        current_loadout = meta.get_loadout()

        # Sync loadout_edit indices with actual loadout
        for i in range(3):
            if i < len(current_loadout):
                try:
                    self.loadout_edit[i] = unlocked.index(current_loadout[i])
                except ValueError:
                    self.loadout_edit[i] = 0

        y_start = 128

        # Section 1: Weapon unlocks
        screen.blit(font.render("UNLOCK WEAPONS", True, ON_SECONDARY), (60, y_start))
        unlock_y = y_start + 24
        for i, wname in enumerate(WEAPON_ORDER):
            y = unlock_y + i * 28
            is_unlocked = meta.is_weapon_unlocked(wname)
            stats = WEAPON_STATS[wname]
            short = WEAPON_SHORT_NAMES.get(wname, wname[:4].upper())

            # Row bg
            col_bg = BULKHEAD
            pygame.draw.rect(screen, col_bg, (40, y, SCREEN_WIDTH - 80, 24))
            pygame.draw.rect(screen, ON_SECONDARY, (40, y, SCREEN_WIDTH - 80, 24), 1)

            # Name
            name_col = ON_PRIMARY if is_unlocked else ON_SECONDARY
            screen.blit(font.render(short, True, name_col), (52, y + 4))

            # Stats
            stat_text = f"DMG:{stats['damage']}  FR:{stats['fire_rate']}ms  MAG:{stats['mag_size']}  RNG:{stats['range']}"
            screen.blit(small_font.render(stat_text, True, ON_SECONDARY), (140, y + 6))

            # Status
            if is_unlocked:
                screen.blit(font.render("UNLOCKED", True, ACID),
                            font.render("UNLOCKED", True, ACID).get_rect(right=SCREEN_WIDTH - 60, centery=y + 12))
            else:
                cost = meta.get_weapon_unlock_cost(wname)
                can_buy = meta.salvage >= cost
                col = ACID if can_buy else DANGER
                screen.blit(font.render(f"{cost} SALVAGE", True, col),
                            font.render(f"{cost} SALVAGE", True, col).get_rect(right=SCREEN_WIDTH - 60, centery=y + 12))

        # Section 2: Loadout selection
        loadout_y = unlock_y + len(WEAPON_ORDER) * 28 + 16
        screen.blit(font.render("LOADOUT (pick 3)", True, ON_SECONDARY), (60, loadout_y))

        slot_w = (SCREEN_WIDTH - 120) // 3
        for i in range(3):
            sx = 60 + i * (slot_w + 8)
            sy = loadout_y + 24
            is_editing = (i == self.loadout_slot)
            idx = self.loadout_edit[i] % len(unlocked)
            wname = unlocked[idx]
            short = WEAPON_SHORT_NAMES.get(wname, wname[:4].upper())

            # Slot bg
            col_bg = CONSOLE if is_editing else BULKHEAD
            border_col = ADRENALINE if is_editing else ON_SECONDARY
            pygame.draw.rect(screen, col_bg, (sx, sy, slot_w, 50))
            pygame.draw.rect(screen, border_col, (sx, sy, slot_w, 50), 2)

            # Slot number
            screen.blit(font.render(f"SLOT {i+1}", True, ON_SECONDARY), (sx + 8, sy + 4))
            # Weapon name
            screen.blit(font.render(short, True, ON_PRIMARY), (sx + 8, sy + 24))

            # Weapon icon color
            icon_colors = {'pulse_rifle': (255, 180, 84), 'shotgun': DANGER,
                           'flamethrower': (255, 107, 0), 'smg': (120, 255, 120),
                           'railgun': (0, 217, 255)}
            icon_col = icon_colors.get(wname, ON_SECONDARY)
            pygame.draw.rect(screen, icon_col, (sx + slot_w - 24, sy + 8, 16, 16))
            pygame.draw.rect(screen, ON_PRIMARY, (sx + slot_w - 24, sy + 8, 16, 16), 1)
