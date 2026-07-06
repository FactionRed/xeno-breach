"""Xeno Breach — Survival Shooter

Full roguelite survival shooter with:
  - Procedural terrain from planet_generator.py pipeline
  - 4-directional pixel art player sprites with animation state machine
  - Xenomorph AI with formalized state machine + sprite animations
  - 3 weapons (pulse rifle, shotgun, flamethrower)
  - Wave director with escalating difficulty
  - 4 objective types + extraction beacon
  - Game state machine (menu → briefing → playing → extraction → victory/gameover)
  - Motion tracker, full HUD, threat banners
  - 4 biomes (barren/polar/cratered/highland)
  - Procedural audio (numpy-synthesized SFX)
  - Game-feel juice: screen shake, hit markers, vignette, kill flash

Controls:
  WASD / Arrows — Move
  Mouse         — Aim
  LMB           — Fire
  1/2/3         — Switch weapons
  R             — Reload
  Shift         — Sprint
  M             — Mute audio
  F1            — Debug overlay
  ESC           — Pause / Quit
"""
import sys
import math
import random
import numpy as np
import pygame

from config import (SCREEN_WIDTH, SCREEN_HEIGHT, FPS, TITLE,
                    WORLD_W, WORLD_H, TERRAIN_SIZE, TERRAIN_SCALE,
                    PLAYER_RADIUS, MAX_SLOPE,
                    ON_PRIMARY, ON_SECONDARY, HULL_BLACK, ADRENALINE,
                    DANGER, WARNING, ACID, CONSOLE, BULKHEAD)
from terrain.terrain_renderer import TerrainRenderer
from entities.player import Player
from entities.player_sprite import PlayerSprite
from entities.enemy_base import AcidPool, AcidProjectile
from entities.enemy_types import Drone, Runner, Brute, Spitter, create_enemy
from entities.enemy_mods import maybe_roll_elite
from entities.xenomorph_sprite import EnemySprite
from entities.spawner import WaveDirector
from entities.projectiles import ProjectileSystem
from combat.weapons import WeaponSystem, WEAPON_ORDER
from combat.particles import ParticleSystem
from combat.floating_text import FloatingTextSystem
from entities.pickups import PickupSystem
from game.state_machine import GameState, StateMachine
from game.objectives import generate_objective, ExtractionBeacon
from game.biomes import pick_biome
from game.audio import AudioSystem
from game.meta_progression import MetaState
from game.armory import ArmoryScreen
from game.options import GameSettings, OptionsScreen
from ui.hud import HUD
from ui.menus import MenuRenderer


def main():
    pygame.init()
    pygame.display.set_caption(TITLE)
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT),
                                     pygame.SCALED, vsync=1)
    clock = pygame.time.Clock()

    font = pygame.font.SysFont("Consolas", 16)
    big_font = pygame.font.SysFont("Consolas", 36, bold=True)
    med_font = pygame.font.SysFont("Consolas", 22, bold=True)
    small_font = pygame.font.SysFont("Consolas", 13)

    game = Game(screen, clock, font, big_font, med_font, small_font)
    game.run()

    pygame.quit()
    print("[game] Exited.")


class Game:
    def __init__(self, screen, clock, font, big_font, med_font, small_font):
        self.screen = screen
        self.clock = clock
        self.font = font
        self.big_font = big_font
        self.med_font = med_font
        self.small_font = small_font
        self.show_debug = False

        # Audio
        self.audio = AudioSystem()

        # Meta progression
        self.meta = MetaState()
        self.armory = ArmoryScreen()

        # Settings
        self.settings = GameSettings()
        self.options = OptionsScreen(self.settings)

        # Game state machine
        self.sm = StateMachine()
        self.sm.register_handler(GameState.MENU, self._update_menu)
        self.sm.register_handler(GameState.ARMORY, self._update_armory)
        self.sm.register_handler(GameState.OPTIONS, self._update_options)
        self.sm.register_handler(GameState.BRIEFING, self._update_briefing)
        self.sm.register_handler(GameState.PLAYING, self._update_playing)
        self.sm.register_handler(GameState.EXTRACTION, self._update_extraction)
        self.sm.register_handler(GameState.VICTORY, self._update_gameover)
        self.sm.register_handler(GameState.GAMEOVER, self._update_gameover)
        self.sm.register_handler(GameState.PAUSED, self._update_paused)

        # Terrain (generated once)
        self.terrain = TerrainRenderer(seed=0)

        # UI
        self.hud = HUD()
        self.menus = MenuRenderer()

        # Game entities
        self.player = None
        self.player_sprite = None
        self.weapons = None
        self.particles = None
        self.projectiles = None
        self.floating_texts = FloatingTextSystem()
        self.pickups = PickupSystem()
        self.wave_director = None
        self.xeno_sprites = {}
        self.acid_pools = []
        self.acid_projectiles = []  # spitter acid projectiles
        self.objective = None
        self.extraction_beacon = None
        self.biome = None

        # Camera
        self.cam_x = 0
        self.cam_y = 0

        # Screen shake & juice
        self.shake_amount = 0.0
        self.kill_flash = 0.0
        self.time_scale = 1.0
        self.time_scale_timer = 0.0

        # Stats
        self.kills = 0
        self.combo = 0
        self.combo_timer = 0.0
        self.run_salvage = 0
        self.shots_fired = 0
        self.shots_hit = 0
        self.waves_completed = 0
        self.run_seed = 0

        # Hit markers
        self.hit_markers = []

        # Menu
        self.menu_selected = 0
        self.menu_options = ["DEPLOY", "ARMORY", "OPTIONS", "QUIT"]
        self.pause_selected = 0
        self.pause_options = ["RESUME", "RESTART", "OPTIONS", "QUIT TO MENU"]

        print("[game] Xeno Breach ready.")

        # Apply saved settings on startup
        self.audio.master_volume = self.settings.master_volume
        self.audio.sfx_volume = self.settings.sfx_volume

    def run(self):
        running = True
        while running:
            raw_dt = self.clock.tick(FPS) / 1000.0
            raw_dt = min(raw_dt, 1 / 30)
            dt = raw_dt * self.time_scale  # time scale for slow-mo

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if self.sm.is_menu:
                            running = False
                        elif self.sm.is_armory:
                            self.sm.transition(GameState.MENU)
                        elif self.sm.is_options:
                            self.settings.save()
                            if self.sm.previous_state == GameState.PAUSED:
                                self.sm.transition(GameState.PAUSED)
                            else:
                                self.sm.transition(GameState.MENU)
                        elif self.sm.current_state == GameState.PAUSED:
                            self.sm.transition(GameState.PLAYING)
                        elif self.sm.is_playing or self.sm.is_extraction:
                            self.sm.transition(GameState.PAUSED)
                        elif self.sm.is_gameover:
                            running = False
                    elif event.key == pygame.K_F1:
                        self.show_debug = not self.show_debug
                    elif event.key == pygame.K_m:
                        muted = self.audio.toggle_mute()
                        print(f"[audio] {'MUTED' if muted else 'UNMUTED'}")
                    elif self.sm.is_menu:
                        if event.key in (pygame.K_UP, pygame.K_w):
                            self.menu_selected = (self.menu_selected - 1) % len(self.menu_options)
                            self.audio.play('ui_click')
                        elif event.key in (pygame.K_DOWN, pygame.K_s):
                            self.menu_selected = (self.menu_selected + 1) % len(self.menu_options)
                            self.audio.play('ui_click')
                        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                            if self.menu_selected == 0:
                                self._start_new_run()
                            elif self.menu_selected == 1:
                                self.audio.play('ui_click')
                                self.armory.reset()
                                self.sm.transition(GameState.ARMORY)
                            elif self.menu_selected == 2:
                                self.audio.play('ui_click')
                                self.sm.transition(GameState.OPTIONS)
                            else:
                                running = False
                    elif self.sm.is_armory:
                        result = self.armory.handle_input(event.key, self.meta)
                        self.audio.play('ui_click')
                        if result == 'deploy':
                            self._start_new_run()
                        elif result == 'back':
                            self.sm.transition(GameState.MENU)
                    elif self.sm.is_options:
                        result = self.options.handle_input(event.key)
                        self.audio.play('ui_click')
                        if result == 'apply':
                            self._apply_settings()
                        elif result == 'back':
                            if self.sm.previous_state == GameState.PAUSED:
                                self.sm.transition(GameState.PAUSED)
                            else:
                                self.sm.transition(GameState.MENU)
                    elif self.sm.current_state == GameState.BRIEFING:
                        if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                            self.audio.play('ui_click')
                            self.sm.transition(GameState.PLAYING)
                    elif self.sm.current_state == GameState.PAUSED:
                        if event.key in (pygame.K_UP, pygame.K_w):
                            self.pause_selected = (self.pause_selected - 1) % len(self.pause_options)
                            self.audio.play('ui_click')
                        elif event.key in (pygame.K_DOWN, pygame.K_s):
                            self.pause_selected = (self.pause_selected + 1) % len(self.pause_options)
                            self.audio.play('ui_click')
                        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                            self.audio.play('ui_click')
                            if self.pause_selected == 0:  # RESUME
                                self.sm.transition(GameState.PLAYING)
                            elif self.pause_selected == 1:  # RESTART
                                self._start_new_run()
                            elif self.pause_selected == 2:  # OPTIONS
                                self.sm.transition(GameState.OPTIONS)
                            else:  # QUIT TO MENU
                                self.sm.transition(GameState.MENU)
                    elif self.sm.is_playing or self.sm.is_extraction:
                        if event.key == pygame.K_r:
                            if self.weapons.current.start_reload():
                                self.audio.play('reload')
                        elif event.key in (pygame.K_1, pygame.K_2, pygame.K_3):
                            idx = {pygame.K_1: 0, pygame.K_2: 1, pygame.K_3: 2}[event.key]
                            if self.weapons.switch_to(idx):
                                self.audio.play('ui_click')
                    elif self.sm.is_gameover:
                        if event.key == pygame.K_RETURN:
                            self.audio.play('ui_click')
                            self.armory.reset()
                            self.sm.transition(GameState.ARMORY)

            self.menus.update(raw_dt)
            self.sm.update(dt, self)

            # Time scale recovery
            if self.time_scale_timer > 0:
                self.time_scale_timer -= raw_dt
                if self.time_scale_timer <= 0:
                    self.time_scale = 1.0

            self._render()
            pygame.display.flip()

    # ============ STATE HANDLERS ============

    def _update_menu(self, dt, game):
        pass

    def _update_armory(self, dt, game):
        self.armory.update(dt)

    def _update_options(self, dt, game):
        self.options.update(dt)

    def _apply_settings(self):
        """Apply changed settings (resolution, fullscreen, volume)."""
        s = self.settings
        flags = pygame.FULLSCREEN if s.fullscreen else 0
        try:
            self.screen = pygame.display.set_mode((s.width, s.height), flags)
        except pygame.error:
            self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), 0)
            print(f"[settings] Failed to set {s.width}x{s.height}, fell back")
        # Apply audio volumes
        self.audio.master_volume = s.master_volume
        self.audio.sfx_volume = s.sfx_volume
        s.save()
        self.options.needs_apply = False
        if self.sm.previous_state == GameState.PAUSED:
            self.sm.transition(GameState.PAUSED)
        else:
            self.sm.transition(GameState.MENU)

    def _update_briefing(self, dt, game):
        pass

    def _update_playing(self, dt, game):
        self._update_gameplay(dt)

    def _update_extraction(self, dt, game):
        self._update_gameplay(dt)
        if self.extraction_beacon and self.extraction_beacon.complete:
            # Extraction bonus salvage
            bonus = 10 + self.wave_director.wave_number * 2
            self.meta.add_salvage(bonus)
            self.run_salvage += bonus
            self.meta.record_run_end(self.kills, self.wave_director.wave_number, True)
            self.sm.transition(GameState.VICTORY)

    def _update_gameover(self, dt, game):
        pass

    def _update_paused(self, dt, game):
        pass

    # ============ GAMEPLAY ============

    def _start_new_run(self):
        self.run_seed = random.randint(0, 99999)
        self.biome = pick_biome(self.run_seed)
        self.player = Player(WORLD_W / 2, WORLD_H / 2)
        self.player_sprite = PlayerSprite()
        self.weapons = WeaponSystem(loadout=self.meta.get_loadout())
        self.particles = ParticleSystem()
        self.projectiles = ProjectileSystem()
        self.acid_pools = []
        self.acid_projectiles = []
        self.xeno_sprites = {}
        self.wave_director = WaveDirector(self.terrain)
        self.extraction_beacon = None
        self.kills = 0
        self.combo = 0
        self.combo_timer = 0.0
        self.run_salvage = 0
        self.shots_fired = 0
        self.shots_hit = 0

        # Apply meta upgrades
        self.player.max_health = 100 + self.meta.bonus_health
        self.player.health = self.player.max_health
        self.player.speed *= self.meta.speed_mult
        # Apply weapon upgrades
        from combat.weapons import WEAPON_STATS
        for wname in self.weapons.loadout:
            w = self.weapons.weapons[wname]
            w.mag_size = int(WEAPON_STATS[wname]['mag_size'] * self.meta.ammo_mult)
            w.ammo = w.mag_size
            w.fire_rate = int(WEAPON_STATS[wname]['fire_rate'] / self.meta.fire_rate_mult)
        self.waves_completed = 0
        self.shake_amount = 0
        self.kill_flash = 0
        self.time_scale = 1.0
        self.hit_markers = []
        self.objective = generate_objective(0, self.terrain, self.player)
        self.sm.transition(GameState.BRIEFING)

    def _update_gameplay(self, dt):
        keys = pygame.key.get_pressed()
        mouse_pos = pygame.mouse.get_pos()
        mouse_buttons = pygame.mouse.get_pressed()
        screen_center = (SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)

        # Predict camera position for this frame so aim reference is accurate
        # (camera follows player, so compute where camera will be after this
        # frame's lerp from the previous camera toward the player)
        target_cx = self.player.x - SCREEN_WIDTH / 2
        target_cy = self.player.y - SCREEN_HEIGHT / 2
        lerp = 1.0 - math.exp(-dt * 8.0)
        predicted_cam_x = self.cam_x + (target_cx - self.cam_x) * lerp
        predicted_cam_y = self.cam_y + (target_cy - self.cam_y) * lerp
        predicted_cam_x = max(0, min(WORLD_W - SCREEN_WIDTH, predicted_cam_x))
        predicted_cam_y = max(0, min(WORLD_H - SCREEN_HEIGHT, predicted_cam_y))

        # Player movement — use ACTUAL player screen position for aiming,
        # not fixed screen center (camera lags + clamps at world edges)
        player_screen_x = self.player.x - predicted_cam_x
        player_screen_y = self.player.y - predicted_cam_y
        # Clamp mouse to screen bounds so aim doesn't break when cursor
        # leaves the window
        mx, my = mouse_pos
        mx = max(0, min(SCREEN_WIDTH - 1, mx))
        my = max(0, min(SCREEN_HEIGHT - 1, my))
        aim_center = (player_screen_x, player_screen_y)
        self.player.update(dt, keys, self.terrain, (mx, my), aim_center)
        self.player.x = max(self.player.radius, min(WORLD_W - self.player.radius, self.player.x))
        self.player.y = max(self.player.radius, min(WORLD_H - self.player.radius, self.player.y))

        # Track speed for animation
        dx_move = dy_move = 0
        if keys[pygame.K_w] or keys[pygame.K_UP]: dy_move -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]: dy_move += 1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]: dx_move -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]: dx_move += 1
        self.player._speed_sq = (dx_move * dx_move + dy_move * dy_move) * 340 ** 2

        # Camera
        target_cx = self.player.x - SCREEN_WIDTH / 2
        target_cy = self.player.y - SCREEN_HEIGHT / 2
        lerp = 1.0 - math.exp(-dt * 8.0)
        self.cam_x += (target_cx - self.cam_x) * lerp
        self.cam_y += (target_cy - self.cam_y) * lerp
        self.cam_x = max(0, min(WORLD_W - SCREEN_WIDTH, self.cam_x))
        self.cam_y = max(0, min(WORLD_H - SCREEN_HEIGHT, self.cam_y))

        # Weapons
        self.weapons.update()

        # Firing
        is_firing = False
        if mouse_buttons[0] and self.weapons.current.can_fire():
            self._fire_weapon()
            is_firing = True

        # Player sprite
        is_reloading = self.weapons.current.reloading
        self.player_sprite.update(dt, self.player, is_firing, is_reloading)

        # Wave director
        prev_wave = self.wave_director.wave_number
        enemies = self.wave_director.update(dt, self.player)
        if self.wave_director.wave_number > prev_wave:
            self.audio.play('wave_alarm', volume=0.4)

        # Xeno sprites
        for e in enemies:
            if id(e) not in self.xeno_sprites:
                self.xeno_sprites[id(e)] = EnemySprite(getattr(e, 'enemy_type', 'drone'))
                self.audio.play('xeno_screech', volume=0.3)
            self.xeno_sprites[id(e)].update(dt, e)

            # Wire spitter callback
            if hasattr(e, 'on_spit') and e.on_spit is None:
                e.on_spit = self._on_spitter_spit

        alive_ids = {id(e) for e in enemies}
        self.xeno_sprites = {k: v for k, v in self.xeno_sprites.items() if k in alive_ids}

        # Acid pools + kill effects
        # Kill rewards: combo, floating text, pickups
        for e in enemies:
            if e.spawn_acid:
                e.spawn_acid = False
                self.acid_pools.append(AcidPool(e.x, e.y, radius=30, dps=8, life=5.0))
                self.particles.emit_acid_splash(e.x, e.y)
                self.kills += 1
                self.kill_flash = 0.15
                self.combo += 1
                self.combo_timer = 3.0
                self.audio.play('xeno_death', volume=0.4)
                # Earn salvage
                salvage = self.meta.salvage_per_kill
                if getattr(e, 'enemy_type', 'drone') == 'brute':
                    salvage += 2
                if getattr(e, 'elite', None):
                    salvage += 2
                self.meta.add_salvage(salvage)
                self.run_salvage += salvage
                # Floating damage number on kill
                self.floating_texts.add_damage(e.x, e.y, 999, crit=True)
                # Combo popup
                self.floating_texts.add_combo(e.x, e.y, self.combo)
                # Pickup drop
                self.pickups.maybe_drop(e.x, e.y, getattr(e, 'enemy_type', 'drone'),
                                       getattr(e, 'elite', None))

        # Acid pool damage
        for pool in self.acid_pools:
            pool.update(dt)
            if pool.contains(self.player.x, self.player.y):
                acid_dmg = pool.dps * dt * (1.0 - self.meta.acid_resist)
                self.player.health -= acid_dmg
        self.acid_pools = [p for p in self.acid_pools if p.life > 0]

        # HP regen (from Auto-Injector upgrade)
        if self.meta.regen_rate > 0 and self.player.health > 0:
            self.player.health = min(self.player.max_health,
                                     self.player.health + self.meta.regen_rate * dt)

        # Acid projectiles (from spitters)
        for proj in self.acid_projectiles:
            proj.update(dt)
            if proj.contains(self.player.x, self.player.y):
                self.player.health -= proj.damage * (1.0 - self.meta.acid_resist)
                self.acid_pools.append(AcidPool(proj.x, proj.y, radius=20, dps=5, life=3.0))
                proj.dead = True
        self.acid_projectiles = [p for p in self.acid_projectiles if not p.dead]

        # Particles & projectiles
        self.particles.update(dt)
        self.projectiles.update(dt)
        self.floating_texts.update(dt)
        self.pickups.update(dt, self.player, self.weapons)

        # Combo decay
        if self.combo_timer > 0:
            self.combo_timer -= dt
            if self.combo_timer <= 0:
                self.combo = 0

        # Hit markers
        self.hit_markers = [(x, y, l - dt) for x, y, l in self.hit_markers if l - dt > 0]

        # Screen shake & juice decay
        self.shake_amount = max(0, self.shake_amount - dt * 30)
        self.kill_flash = max(0, self.kill_flash - dt * 5)

        # HUD update
        self.hud.update(dt, self.player, enemies, self.terrain)

        # Audio update (motion tracker ping + footsteps)
        near = sum(1 for e in enemies if not e.dead and
                   abs(e.x - self.player.x) < 200 and abs(e.y - self.player.y) < 200)
        self.audio.update(dt, near)
        moving = (dx_move != 0 or dy_move != 0)
        sprinting = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
        self.audio.update_footsteps(dt, moving, sprinting)

        # Objective
        if self.objective:
            self.objective.update(dt, self.player, self.wave_director, self.terrain)
            if self.objective.complete and self.sm.is_playing:
                self._start_extraction()

        # Extraction beacon
        if self.extraction_beacon:
            self.extraction_beacon.update(dt, self.player)

        # Player hurt audio
        old_hp = getattr(self, '_last_hp', self.player.health)
        if self.player.health < old_hp - 5:
            self.audio.play('player_hurt', volume=0.5)
            self.player_sprite.trigger_hurt()
        self._last_hp = self.player.health

        # Game over
        if self.player.health <= 0:
            self.player.health = 0
            self.meta.record_run_end(self.kills, self.wave_director.wave_number, False)
            self.sm.transition(GameState.GAMEOVER)

    def _start_extraction(self):
        best = (WORLD_W / 2, WORLD_H / 2)
        best_dist = 0
        for _ in range(30):
            x = random.uniform(100, WORLD_W - 100)
            y = random.uniform(100, WORLD_H - 100)
            dx = x - self.player.x
            dy = y - self.player.y
            d = dx * dx + dy * dy
            if d > best_dist:
                best_dist = d
                best = (x, y)
        self.extraction_beacon = ExtractionBeacon(best[0], best[1])
        self.extraction_beacon.activate()
        self.sm.transition(GameState.EXTRACTION)
        self.waves_completed = self.wave_director.wave_number
        self.audio.play('extraction', volume=0.5)
        print(f"[game] Extraction activated at ({best[0]:.0f}, {best[1]:.0f})")

    def _on_spitter_spit(self, sx, sy, tx, ty):
        """Callback for Spitter enemies to spawn acid projectiles."""
        self.acid_projectiles.append(AcidProjectile(sx, sy, tx, ty))
        self.audio.play('xeno_screech', volume=0.15)

    def _fire_weapon(self):
        weapon = self.weapons.current
        angles = weapon.fire()
        if angles is None:
            return

        self.shots_fired += 1
        px = self.player.x
        py = self.player.y
        facing = self.player.facing
        barrel_x = px + math.cos(facing) * (self.player.radius + 6)
        barrel_y = py + math.sin(facing) * (self.player.radius + 6)

        # Weapon sound
        snd_map = {'pulse_rifle': 'pulse_rifle', 'shotgun': 'shotgun',
                   'flamethrower': 'flamethrower'}
        vol_map = {'pulse_rifle': 0.35, 'shotgun': 0.25, 'flamethrower': 0.3}
        self.audio.play(snd_map.get(weapon.name, 'pulse_rifle'),
                        volume=vol_map.get(weapon.name, 0.3))

        for angle_offset in angles:
            shot_angle = facing + angle_offset
            dx = math.cos(shot_angle)
            dy = math.sin(shot_angle)
            end_x = barrel_x + dx * weapon.range
            end_y = barrel_y + dy * weapon.range

            hit_enemy = None
            hit_dist = weapon.range
            for e in self.wave_director.enemies:
                if e.dead or e.state == 'death':
                    continue
                ex = e.x - barrel_x
                ey = e.y - barrel_y
                proj = ex * dx + ey * dy
                if proj < 0 or proj > weapon.range:
                    continue
                perp_sq = ex * ex + ey * ey - proj * proj
                if perp_sq < (e.radius + 4) ** 2 and proj < hit_dist:
                    hit_dist = proj
                    hit_enemy = e

            if hit_enemy:
                dmg = weapon.damage
                if weapon.name == 'shotgun':
                    dmg *= max(0.3, 1.0 - hit_dist / weapon.range)
                hit_enemy.take_damage(dmg)
                self.shots_hit += 1
                self.particles.emit_blood_spray(hit_enemy.x, hit_enemy.y, shot_angle)
                self.particles.emit_blood_spray(hit_enemy.x, hit_enemy.y, shot_angle + math.pi)
                self.hit_markers.append((hit_enemy.x, hit_enemy.y, 0.3))
                self.floating_texts.add_damage(hit_enemy.x, hit_enemy.y, dmg)
                self.audio.play('hit_marker', volume=0.2)
                end_x = barrel_x + dx * hit_dist
                end_y = barrel_y + dy * hit_dist
                self.projectiles.add_tracer(barrel_x, barrel_y, end_x, end_y, weapon.tracer_color)
            else:
                self.projectiles.add_tracer(barrel_x, barrel_y, end_x, end_y, weapon.tracer_color)
                if random.random() < 0.3:
                    self.particles.emit_impact_sparks(end_x, end_y, shot_angle, weapon.tracer_color)

            if weapon.area_denial:
                fire_x = barrel_x + dx * min(hit_dist, weapon.range * 0.7)
                fire_y = barrel_y + dy * min(hit_dist, weapon.range * 0.7)
                self.projectiles.add_fire_zone(fire_x, fire_y, radius=30,
                                               dps=weapon.damage * 2, life=0.5)
                for e in self.wave_director.enemies:
                    if e.dead:
                        continue
                    for fz in self.projectiles.fire_zones:
                        if fz.contains(e.x, e.y):
                            e.take_damage(fz.dps * 0.016)

        if weapon.muzzle_flash:
            self.particles.emit_muzzle_flash(barrel_x, barrel_y, facing, weapon.tracer_color)
        if weapon.name == 'shotgun':
            self.shake_amount = 5.0
        elif weapon.name == 'pulse_rifle':
            self.shake_amount = 1.5
        else:
            self.shake_amount = 0.8

    # ============ RENDER ============

    def _render(self):
        if self.sm.is_menu:
            self.menus.draw_title(self.screen, self.big_font, self.med_font,
                                  self.font, self.menu_selected, self.menu_options)
        elif self.sm.is_armory:
            self.armory.draw(self.screen, self.meta, self.font, self.big_font, self.small_font)
        elif self.sm.is_options:
            self.options.draw(self.screen, self.font, self.big_font, self.small_font)
        elif self.sm.current_state == GameState.BRIEFING:
            self.menus.draw_briefing(self.screen, self.big_font, self.med_font,
                                     self.font, self.run_seed, self.biome, self.objective)
        elif self.sm.is_playing or self.sm.is_extraction or self.sm.is_gameover or self.sm.current_state == GameState.PAUSED:
            self._render_gameplay()
            if self.sm.current_state == GameState.PAUSED:
                self.menus.draw_paused(self.screen, self.big_font, self.font, self.pause_selected, self.pause_options)
            elif self.sm.is_gameover:
                stats = [
                    f"WAVES SURVIVED: {self.waves_completed}",
                    f"XENOMORPHS KILLED: {self.kills}",
                    f"ACCURACY: {self._accuracy():.0f}%",
                    f"SALVAGE EARNED: {self.run_salvage}",
                    f"TOTAL SALVAGE: {self.meta.salvage}",
                ]
                self.menus.draw_gameover(self.screen, self.big_font, self.med_font,
                                         self.font, self.sm.current_state == GameState.VICTORY, stats)
        pygame.display.flip()

    def _render_gameplay(self):
        shake_x = random.uniform(-1, 1) * self.shake_amount if self.shake_amount > 0 else 0
        shake_y = random.uniform(-1, 1) * self.shake_amount if self.shake_amount > 0 else 0
        cam_x = int(self.cam_x + shake_x)
        cam_y = int(self.cam_y + shake_y)

        self.screen.fill(HULL_BLACK)
        self.terrain.render(self.screen, cam_x, cam_y)

        # Acid pools
        for pool in self.acid_pools:
            pool.draw(self.screen, cam_x, cam_y)

        # Acid projectiles (from spitters)
        for proj in self.acid_projectiles:
            proj.draw(self.screen, cam_x, cam_y)

        # Pickups
        self.pickups.draw(self.screen, cam_x, cam_y)

        # Fire zones
        self.projectiles.draw(self.screen, cam_x, cam_y)

        # Xenomorph sprites
        for e in self.wave_director.enemies:
            sprite = self.xeno_sprites.get(id(e))
            if sprite:
                sprite.draw(self.screen, e, cam_x, cam_y)
            else:
                e.draw(self.screen, cam_x, cam_y)

        # Player sprite
        self.player_sprite.draw(self.screen, self.player, cam_x, cam_y)

        # Particles
        self.particles.draw(self.screen, cam_x, cam_y)

        # Floating text (damage numbers, combos, pickups)
        self.floating_texts.draw(self.screen, cam_x, cam_y)

        # Hit markers
        for hx, hy, life in self.hit_markers:
            alpha = life / 0.3
            sx = int(hx - cam_x)
            sy = int(hy - cam_y)
            col = (int(255 * alpha), int(180 * alpha), int(84 * alpha))
            size = 6
            pygame.draw.line(self.screen, col, (sx - size, sy - size), (sx + size, sy + size), 2)
            pygame.draw.line(self.screen, col, (sx + size, sy - size), (sx - size, sy + size), 2)

        # Extraction beacon
        if self.extraction_beacon:
            self.extraction_beacon.draw(self.screen, cam_x, cam_y)

        # Kill flash overlay
        if self.kill_flash > 0:
            flash = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            flash.fill((255, 255, 255, int(40 * self.kill_flash)))
            self.screen.blit(flash, (0, 0))

        # Biome fog
        if self.biome and self.biome.fog_density > 0:
            fog = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            fog.fill((*self.biome.fog_color, int(255 * self.biome.fog_density * 0.3)))
            self.screen.blit(fog, (0, 0))

        # HUD
        wave_info = self.wave_director.get_wave_info() if self.wave_director else None
        if wave_info:
            self.hud.draw(self.screen, self.font, self.med_font, self.small_font,
                         self.player, self.weapons, wave_info, self.kills,
                         self.objective, self.extraction_beacon,
                         pygame.time.get_ticks() / 1000.0,
                         enemies=self.wave_director.enemies if self.wave_director else None,
                         combo=self.combo)

        if self.show_debug:
            self._draw_debug(cam_x, cam_y)

    def _draw_debug(self, cam_x, cam_y):
        lines = [
            f"FPS: {self.clock.get_fps():.1f}",
            f"State: {self.sm.current_state.value}",
            f"Biome: {self.biome.name if self.biome else 'N/A'}",
            f"Pos: ({self.player.x:.0f}, {self.player.y:.0f})",
            f"Health: {self.player.health:.0f}/{self.player.max_health:.0f}",
            f"Enemies: {sum(1 for e in self.wave_director.enemies if not e.dead)}",
            f"Particles: {len(self.particles.particles)}",
            f"Tracers: {len(self.projectiles.tracers)}",
            f"Kills: {self.kills}  Acc: {self._accuracy():.0f}%",
            f"Time scale: {self.time_scale:.2f}",
        ]
        for i, line in enumerate(lines):
            txt = self.font.render(line, True, ON_PRIMARY)
            self.screen.blit(txt, (16, 60 + i * 20))

    def _accuracy(self):
        if self.shots_fired == 0:
            return 0
        return (self.shots_hit / self.shots_fired) * 100


if __name__ == "__main__":
    main()
