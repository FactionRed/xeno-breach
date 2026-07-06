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

# Human-readable weapon descriptions
WEAPON_INFO = {
    'pulse_rifle': {
        'name': 'Pulse Rifle',
        'desc': 'Reliable standard-issue weapon. Balanced damage and fire rate.',
        'role': 'All-rounder',
    },
    'shotgun': {
        'name': 'Shotgun',
        'desc': 'Devastating up close. Fires 6 pellets per shot.',
        'role': 'Close range',
    },
    'flamethrower': {
        'name': 'Flamethrower',
        'desc': 'Sprays a cone of fire. High DPS but short range.',
        'role': 'Crowd control',
    },
    'smg': {
        'name': 'SMG',
        'desc': 'Extremely fast fire rate. Low damage per shot but shreds groups.',
        'role': 'Suppressive fire',
    },
    'railgun': {
        'name': 'Railgun',
        'desc': 'Charged shot that pierces through enemies. Massive damage.',
        'role': 'Heavy hitter',
    },
}

WEAPON_ICON_COLORS = {
    'pulse_rifle': (255, 180, 84), 'shotgun': DANGER,
    'flamethrower': (255, 107, 0), 'smg': (120, 255, 120),
    'railgun': (0, 217, 255),
}


class ArmoryScreen:
    """Renders the armory upgrade screen and handles input."""

    def __init__(self):
        self.tab = 0  # 0=upgrades, 1=weapons
        self.selected = 0
        self.anim_time = 0.0
        self.purchase_flash = 0.0
        self.purchase_msg = ""
        self.purchase_msg_color = ACID
        self.loadout_edit = [0, 1, 2]
        self.loadout_slot = 0
        self._loadout_synced = False
        # Mouse click rects
        self._click_rects = []  # (rect, action) pairs

    def reset(self):
        """Call when entering the armory to re-sync from saved loadout."""
        self._loadout_synced = False
        self.tab = 0
        self.selected = 0
        self.loadout_slot = 0

    def update(self, dt):
        self.anim_time += dt
        self.purchase_flash = max(0, self.purchase_flash - dt * 3)

    def handle_input(self, key, meta: MetaState):
        if key == pygame.K_TAB:
            self.tab = 1 - self.tab
            self.selected = 0
            self.loadout_slot = 0
            return None
        if key == pygame.K_UP or key == pygame.K_w:
            if self.tab == 0:
                self.selected = (self.selected - 1) % len(UPGRADE_ORDER)
            else:
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
            # Always apply loadout before deploying (in case user edited it)
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
            self._flash(f"Purchased {upgrade.name} Tier {tier+1}", ACID)
        elif meta.is_maxed(key_name):
            self._flash("Already maxed out", WARNING)
        else:
            cost = meta.get_next_tier_cost(key_name)
            self._flash(f"Need {cost} more salvage", DANGER)

    def _try_unlock_or_confirm_loadout(self, meta):
        for wname in WEAPON_ORDER:
            if not meta.is_weapon_unlocked(wname):
                cost = meta.get_weapon_unlock_cost(wname)
                if cost is not None and meta.salvage >= cost:
                    meta.unlock_weapon(wname)
                    info = WEAPON_INFO.get(wname, {})
                    self._flash(f"Unlocked: {info.get('name', wname)}", ACID)
                elif cost is not None:
                    self._flash(f"Need {cost} more salvage", DANGER)
                return
        self._apply_loadout(meta)
        self._flash("Loadout saved", ACID)

    def _apply_loadout(self, meta):
        unlocked = meta.unlocked_weapons
        loadout = [unlocked[self.loadout_edit[i] % len(unlocked)] for i in range(3)]
        meta.set_loadout(loadout)

    def _flash(self, msg, color):
        self.purchase_flash = 1.0
        self.purchase_msg = msg
        self.purchase_msg_color = color

    def handle_mouse(self, pos, clicked, meta):
        """Handle mouse input. Returns 'deploy', 'back', or None."""
        for rect, action in self._click_rects:
            if rect.collidepoint(pos):
                if not clicked:
                    return None  # just hovering
                if action == 'deploy':
                    self._apply_loadout(meta)
                    return 'deploy'
                elif action == 'back':
                    return 'back'
                elif action.startswith('tab_'):
                    self.tab = int(action.split('_')[1])
                    self.selected = 0
                    self.loadout_slot = 0
                return None
        return None

    # ============ DRAW ============

    def draw(self, screen, meta: MetaState, font, big_font, small_font):
        screen.fill(HULL_BLACK)
        self._click_rects = []  # reset click targets

        # Title
        title = big_font.render("ARMORY", True, ADRENALINE)
        screen.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, 36)))

        # Tabs — clickable
        tab_y = 64
        mouse_pos = pygame.mouse.get_pos()
        for i, label in enumerate(["UPGRADES", "WEAPONS"]):
            col = ADRENALINE if i == self.tab else ON_SECONDARY
            txt = font.render(label, True, col)
            x = SCREEN_WIDTH // 2 + (i - 0.5) * 160 - txt.get_width() // 2
            tab_rect = txt.get_rect(topleft=(x, tab_y)).inflate(20, 10)
            if tab_rect.collidepoint(mouse_pos):
                col = ADRENALINE
                bg = pygame.Surface((tab_rect.w, tab_rect.h), pygame.SRCALPHA)
                bg.fill((*ADRENALINE, 20))
                screen.blit(bg, tab_rect.topleft)
            screen.blit(txt, (x, tab_y))
            if i == self.tab:
                pygame.draw.line(screen, ADRENALINE, (x, tab_y + 20), (x + txt.get_width(), tab_y + 20), 2)
            self._click_rects.append((tab_rect, f'tab_{i}'))

        # Deploy button (bottom center)
        deploy_rect = pygame.Rect(SCREEN_WIDTH // 2 - 80, SCREEN_HEIGHT - 50, 160, 30)
        deploy_hover = deploy_rect.collidepoint(mouse_pos)
        deploy_col = ADRENALINE if deploy_hover else WARNING
        pygame.draw.rect(screen, (20, 24, 28), deploy_rect)
        pygame.draw.rect(screen, deploy_col, deploy_rect, 2)
        deploy_txt = font.render("DEPLOY", True, deploy_col)
        screen.blit(deploy_txt, deploy_txt.get_rect(center=deploy_rect.center))
        self._click_rects.append((deploy_rect, 'deploy'))

        # ESC button (bottom left)
        esc_rect = pygame.Rect(40, SCREEN_HEIGHT - 50, 100, 30)
        if esc_rect.collidepoint(mouse_pos):
            pygame.draw.rect(screen, (30, 34, 38), esc_rect)
            pygame.draw.rect(screen, DANGER, esc_rect, 2)
        else:
            pygame.draw.rect(screen, (20, 24, 28), esc_rect)
            pygame.draw.rect(screen, ON_SECONDARY, esc_rect, 2)
        esc_txt = font.render("MENU", True, ON_SECONDARY)
        screen.blit(esc_txt, esc_txt.get_rect(center=esc_rect.center))
        self._click_rects.append((esc_rect, 'back'))

        # Salvage
        salvage_text = font.render(f"Salvage: {meta.salvage}", True, WARNING)
        screen.blit(salvage_text, salvage_text.get_rect(center=(SCREEN_WIDTH // 2, 94)))

        # Stats
        stats = f"Runs: {meta.total_runs}  |  Kills: {meta.total_kills}  |  Best Wave: {meta.best_wave}"
        stats_text = small_font.render(stats, True, ON_SECONDARY)
        screen.blit(stats_text, stats_text.get_rect(center=(SCREEN_WIDTH // 2, 112)))

        if self.tab == 0:
            self._draw_upgrades_tab(screen, meta, font, small_font)
        else:
            self._draw_weapons_tab(screen, meta, font, small_font)

        # Toast message
        if self.purchase_flash > 0:
            alpha = min(255, int(255 * self.purchase_flash))
            msg_surf = font.render(self.purchase_msg, True, self.purchase_msg_color)
            msg_surf.set_alpha(alpha)
            screen.blit(msg_surf, msg_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 56)))

        # Controls
        pulse = (math.sin(self.anim_time * 3) + 1) * 0.5
        col = ADRENALINE if pulse > 0.5 else ON_PRIMARY
        if self.tab == 0:
            hint_text = "[UP/DOWN] Select  [ENTER] Purchase  [TAB] Weapons  [SPACE] Deploy  [ESC] Menu"
        else:
            hint_text = "[UP/DOWN] Slot  [LEFT/RIGHT] Cycle  [ENTER] Unlock/Save  [TAB] Upgrades  [SPACE] Deploy  [ESC] Menu"
        hint = small_font.render(hint_text, True, col)
        screen.blit(hint, hint.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 22)))

    # ============ UPGRADES TAB ============

    def _draw_upgrades_tab(self, screen, meta, font, small_font):
        list_w = 720
        list_x = 40
        detail_x = list_x + list_w + 16
        detail_w = SCREEN_WIDTH - detail_x - 40
        y_start = 132
        row_h = 52

        # Upgrade list (left)
        for i, key in enumerate(UPGRADE_ORDER):
            upgrade = UPGRADES[key]
            tier = meta.get_tier(key)
            is_selected = (i == self.selected)
            is_maxed = meta.is_maxed(key)
            can_buy = meta.can_purchase(key)

            y = y_start + i * row_h
            bg_col = CONSOLE if is_selected else BULKHEAD
            pygame.draw.rect(screen, bg_col, (list_x, y, list_w, row_h - 4))
            if is_selected:
                pygame.draw.rect(screen, ADRENALINE, (list_x, y, list_w, row_h - 4), 2)

            # Name + tier level
            name_col = ON_PRIMARY if is_selected else ON_SECONDARY
            screen.blit(font.render(upgrade.name, True, name_col), (list_x + 12, y + 4))
            tier_label = f"Tier {tier}/{upgrade.max_tier}" if tier > 0 else "Not owned"
            tier_col = ACID if tier > 0 else ON_SECONDARY
            screen.blit(small_font.render(tier_label, True, tier_col), (list_x + 12, y + 24))

            # Tier pips (visual progress bar)
            pip_x = list_x + 200
            pip_y = y + 10
            pip_total = upgrade.max_tier
            pip_w = 30
            for t in range(pip_total):
                px = pip_x + t * (pip_w + 4)
                if t < tier:
                    col = ACID
                    pygame.draw.rect(screen, col, (px, pip_y, pip_w, 12))
                elif t == tier and can_buy:
                    col = WARNING
                    pygame.draw.rect(screen, col, (px, pip_y, pip_w, 12), 2)
                    fill = pygame.Surface((pip_w, 12), pygame.SRCALPHA)
                    fill.fill((*WARNING, 40))
                    screen.blit(fill, (px, pip_y))
                else:
                    pygame.draw.rect(screen, (40, 44, 48), (px, pip_y, pip_w, 12))
                    pygame.draw.rect(screen, (60, 64, 68), (px, pip_y, pip_w, 12), 1)

            # Cost / status
            if is_maxed:
                cost_text = font.render("MAX", True, ACID)
            else:
                cost = upgrade.tiers[tier]['cost']
                col = ACID if can_buy else DANGER
                cost_text = font.render(f"{cost}", True, col)
            screen.blit(cost_text, cost_text.get_rect(right=list_x + list_w - 12, centery=y + 14))

            # Current effect (compact)
            if tier > 0:
                eff = upgrade.tiers[tier - 1]['desc']
                screen.blit(small_font.render(eff, True, ACID), (list_x + 200, y + 28))
            elif not is_maxed:
                eff = upgrade.tiers[0]['desc']
                screen.blit(small_font.render(f"Next: {eff}", True, ON_SECONDARY), (list_x + 200, y + 28))

        # Detail panel (right) — shows full info for selected upgrade
        sel_key = UPGRADE_ORDER[self.selected]
        sel_upgrade = UPGRADES[sel_key]
        sel_tier = meta.get_tier(sel_key)
        dy = y_start
        # Panel bg
        pygame.draw.rect(screen, CONSOLE, (detail_x, dy, detail_w, 360))
        pygame.draw.rect(screen, ON_SECONDARY, (detail_x, dy, detail_w, 360), 1)

        # Name
        screen.blit(font.render(sel_upgrade.name, True, ON_PRIMARY), (detail_x + 12, dy + 8))
        # Description
        screen.blit(small_font.render(sel_upgrade.description, True, ON_SECONDARY), (detail_x + 12, dy + 32))

        # All tiers
        screen.blit(small_font.render("UPGRADE TIERS", True, ADRENALINE), (detail_x + 12, dy + 56))
        for t in range(sel_upgrade.max_tier):
            ty = dy + 76 + t * 56
            tier_data = sel_upgrade.tiers[t]
            owned = t < sel_tier
            current = t == sel_tier
            # Tier row bg
            row_bg = (30, 40, 30) if owned else (BULKHEAD if not current else (40, 36, 24))
            pygame.draw.rect(screen, row_bg, (detail_x + 8, ty, detail_w - 16, 48))
            border = ACID if owned else (WARNING if current else (50, 54, 58))
            pygame.draw.rect(screen, border, (detail_x + 8, ty, detail_w - 16, 48), 1)

            # Tier label
            tcol = ACID if owned else (WARNING if current else ON_SECONDARY)
            screen.blit(font.render(f"Tier {t+1}", True, tcol), (detail_x + 14, ty + 4))
            # Effect
            screen.blit(small_font.render(tier_data['desc'], True, ON_PRIMARY if owned or current else ON_SECONDARY), (detail_x + 14, ty + 24))
            # Cost
            if owned:
                screen.blit(small_font.render("Owned", True, ACID),
                            small_font.render("Owned", True, ACID).get_rect(right=detail_x + detail_w - 14, centery=ty + 16))
            else:
                screen.blit(small_font.render(f"Cost: {tier_data['cost']}", True, WARNING),
                            small_font.render(f"Cost: {tier_data['cost']}", True, WARNING).get_rect(right=detail_x + detail_w - 14, centery=ty + 16))

    # ============ WEAPONS TAB ============

    def _draw_weapons_tab(self, screen, meta, font, small_font):
        unlocked = meta.unlocked_weapons
        current_loadout = meta.get_loadout()

        if not self._loadout_synced:
            for i in range(3):
                if i < len(current_loadout):
                    try:
                        self.loadout_edit[i] = unlocked.index(current_loadout[i])
                    except ValueError:
                        self.loadout_edit[i] = 0
            self._loadout_synced = True

        list_w = 720
        list_x = 40
        detail_x = list_x + list_w + 16
        detail_w = SCREEN_WIDTH - detail_x - 40
        y_start = 132
        row_h = 36

        # Weapon list (left)
        screen.blit(font.render("WEAPON ARSENAL", True, ON_SECONDARY), (list_x, y_start - 8))
        for i, wname in enumerate(WEAPON_ORDER):
            y = y_start + i * row_h
            is_unlocked = meta.is_weapon_unlocked(wname)
            stats = WEAPON_STATS[wname]
            info = WEAPON_INFO.get(wname, {})
            display_name = info.get('name', wname.replace('_', ' ').title())

            # Row bg
            pygame.draw.rect(screen, BULKHEAD, (list_x, y, list_w, row_h - 4))
            pygame.draw.rect(screen, (50, 54, 58), (list_x, y, list_w, row_h - 4), 1)

            # Weapon icon
            icon_col = WEAPON_ICON_COLORS.get(wname, ON_SECONDARY)
            pygame.draw.rect(screen, icon_col, (list_x + 8, y + 6, 20, 20))
            pygame.draw.rect(screen, ON_PRIMARY, (list_x + 8, y + 6, 20, 20), 1)

            # Name + role
            name_col = ON_PRIMARY if is_unlocked else ON_SECONDARY
            screen.blit(font.render(display_name, True, name_col), (list_x + 36, y + 4))
            role = info.get('role', '')
            screen.blit(small_font.render(role, True, ON_SECONDARY), (list_x + 36, y + 22))

            # Stats bar (visual)
            bar_x = list_x + 300
            bar_w = 80
            # Damage bar
            self._draw_stat_bar(screen, small_font, "DMG", bar_x, y + 4, bar_w, stats['damage'] / 80, is_unlocked)
            # Fire rate bar (inverted — lower ms = faster = better)
            fr_pct = 1.0 - min(1.0, stats['fire_rate'] / 800)
            self._draw_stat_bar(screen, small_font, "SPD", bar_x, y + 18, bar_w, fr_pct, is_unlocked)
            # Mag size bar
            self._draw_stat_bar(screen, small_font, "MAG", bar_x + 130, y + 4, bar_w, stats['mag_size'] / 100, is_unlocked)
            # Range bar
            self._draw_stat_bar(screen, small_font, "RNG", bar_x + 130, y + 18, bar_w, stats['range'] / 1200, is_unlocked)

            # Status
            if is_unlocked:
                screen.blit(small_font.render("Available", True, ACID),
                            small_font.render("Available", True, ACID).get_rect(right=list_x + list_w - 12, centery=y + 14))
            else:
                cost = meta.get_weapon_unlock_cost(wname)
                can_buy = meta.salvage >= cost
                col = ACID if can_buy else DANGER
                txt = font.render(f"{cost}", True, col)
                screen.blit(txt, txt.get_rect(right=list_x + list_w - 12, centery=y + 14))
                screen.blit(small_font.render("salvage", True, ON_SECONDARY),
                            small_font.render("salvage", True, ON_SECONDARY).get_rect(right=list_x + list_w - 12, centery=y + 28))

        # Detail panel (right) — selected weapon info
        # Find selected weapon (first locked, or last viewed)
        sel_wname = None
        for wname in WEAPON_ORDER:
            if not meta.is_weapon_unlocked(wname):
                sel_wname = wname
                break
        if not sel_wname:
            # All unlocked — show current loadout slot's weapon
            idx = self.loadout_edit[self.loadout_slot] % len(unlocked)
            sel_wname = unlocked[idx]

        info = WEAPON_INFO.get(sel_wname, {})
        stats = WEAPON_STATS[sel_wname]
        dy = y_start
        pygame.draw.rect(screen, CONSOLE, (detail_x, dy, detail_w, 360))
        pygame.draw.rect(screen, ON_SECONDARY, (detail_x, dy, detail_w, 360), 1)

        # Icon + name
        icon_col = WEAPON_ICON_COLORS.get(sel_wname, ON_SECONDARY)
        pygame.draw.rect(screen, icon_col, (detail_x + 12, dy + 12, 24, 24))
        pygame.draw.rect(screen, ON_PRIMARY, (detail_x + 12, dy + 12, 24, 24), 1)
        screen.blit(font.render(info.get('name', sel_wname), True, ON_PRIMARY), (detail_x + 44, dy + 14))
        screen.blit(small_font.render(info.get('role', ''), True, WARNING), (detail_x + 44, dy + 34))

        # Description
        screen.blit(small_font.render(info.get('desc', ''), True, ON_SECONDARY), (detail_x + 12, dy + 56))

        # Stats (readable format)
        sy = dy + 84
        screen.blit(small_font.render("STATS", True, ADRENALINE), (detail_x + 12, sy))
        sy += 20
        stat_lines = [
            f"Damage:    {stats['damage']} per hit",
            f"Fire Rate: {stats['fire_rate']}ms between shots",
            f"Magazine:  {stats['mag_size']} rounds",
            f"Range:     {stats['range']} pixels",
            f"Reload:    {stats.get('reload_time', 1.5)}s",
        ]
        for line in stat_lines:
            screen.blit(small_font.render(line, True, ON_PRIMARY), (detail_x + 16, sy))
            sy += 18

        # Loadout section (bottom)
        loadout_y = y_start + len(WEAPON_ORDER) * row_h + 20
        screen.blit(font.render("YOUR LOADOUT", True, ON_SECONDARY), (list_x, loadout_y))

        slot_w = (list_w - 16) // 3
        for i in range(3):
            sx = list_x + i * (slot_w + 8)
            sy2 = loadout_y + 24
            is_editing = (i == self.loadout_slot)
            idx = self.loadout_edit[i] % len(unlocked)
            wname = unlocked[idx]
            info2 = WEAPON_INFO.get(wname, {})
            short = WEAPON_SHORT_NAMES.get(wname, wname[:4].upper())

            col_bg = CONSOLE if is_editing else BULKHEAD
            border_col = ADRENALINE if is_editing else ON_SECONDARY
            pygame.draw.rect(screen, col_bg, (sx, sy2, slot_w, 56))
            pygame.draw.rect(screen, border_col, (sx, sy2, slot_w, 56), 2)

            # Slot number
            screen.blit(small_font.render(f"SLOT {i+1}", True, ON_SECONDARY), (sx + 8, sy2 + 4))
            # Weapon name
            screen.blit(font.render(info2.get('name', short), True, ON_PRIMARY), (sx + 8, sy2 + 22))
            # Icon
            ic = WEAPON_ICON_COLORS.get(wname, ON_SECONDARY)
            pygame.draw.rect(screen, ic, (sx + slot_w - 28, sy2 + 8, 18, 18))
            pygame.draw.rect(screen, ON_PRIMARY, (sx + slot_w - 28, sy2 + 8, 18, 18), 1)

            if is_editing:
                screen.blit(small_font.render("< L/R >", True, WARNING), (sx + 8, sy2 + 42))

    def _draw_stat_bar(self, screen, font, label, x, y, w, pct, active):
        """Draw a labeled stat bar (0.0 to 1.0)."""
        screen.blit(font.render(label, True, ON_SECONDARY), (x, y))
        bar_x = x + 28
        bar_w = w - 28
        bar_h = 8
        pygame.draw.rect(screen, (30, 34, 38), (bar_x, y + 2, bar_w, bar_h))
        fill_w = int(bar_w * max(0, min(1, pct)))
        if fill_w > 0:
            col = ACID if active else (60, 64, 68)
            pygame.draw.rect(screen, col, (bar_x, y + 2, fill_w, bar_h))
        pygame.draw.rect(screen, (50, 54, 58), (bar_x, y + 2, bar_w, bar_h), 1)
