# Implementation Plan — Phase 5+: Expansion & Depth

> **Status:** Draft v2.0 · 2026-07-01
> **Prerequisite:** Phases 1–4 complete (4,243 lines across 25 files)
> **Parent plan:** `IMPLEMENTATION_PLAN.md` (Phases 1–4)

---

## Current State — What's Built

| System | Status | Files |
|--------|--------|-------|
| Terrain (heightfield + craters + normals + shading) | ✅ Shipped | `terrain/heightfield.py`, `terrain/terrain_renderer.py` |
| Player (movement, slope collision, sprint) | ✅ Shipped | `entities/player.py` |
| Player sprites (16×16 pixel art, 4-dir, 7 states) | ✅ Shipped | `entities/sprite_factory.py`, `entities/player_sprite.py` |
| Sci-Fi Military Marine outfit | ✅ Shipped | `entities/sprite_factory.py` (gunmetal armor, cyan visor, orange accent) |
| Xenomorph AI (6-state machine + sprites) | ✅ Shipped | `entities/xenomorph.py`, `entities/xenomorph_sprite.py` |
| Weapons (pulse rifle, shotgun, flamethrower) | ✅ Shipped | `combat/weapons.py` |
| Particles (muzzle flash, blood, acid, sparks) | ✅ Shipped | `combat/particles.py` |
| Projectiles (tracers, fire zones) | ✅ Shipped | `entities/projectiles.py` |
| Wave director (escalating waves) | ✅ Shipped | `entities/spawner.py` |
| Objectives (survive/reach/defend/scavenge + extraction) | ✅ Shipped | `game/objectives.py` |
| Game state machine (menu→briefing→play→extract→end) | ✅ Shipped | `game/state_machine.py` |
| Biomes (barren/polar/cratered/highland) | ✅ Shipped | `game/biomes.py` |
| Audio (11 procedural SFX) | ✅ Shipped | `game/audio.py` |
| HUD (health, ammo, wave, objective, threat, vignette) | ✅ Shipped | `ui/hud.py` |
| Motion tracker (ping sweep + blips) | ✅ Shipped | `ui/motion_tracker.py` |
| Menus (title, briefing, pause, gameover) | ✅ Shipped | `ui/menus.py` |
| Design tokens (DESIGN.md validated) | ✅ Shipped | `DESIGN.md` |

### Known Issues Addressed
- ✅ Aim bug (camera lag + mouse leaving window) — fixed with predicted cam + mouse clamping
- ✅ Title screen ghosting (multi-blit glow) — fixed with single clean render
- ✅ Radar/ammo counter overlap — tracker moved to top-right
- ✅ Sprite grid width bugs (197 bad rows) — fixed with `_row16()` auto-padding + import-time validation

---

## Phase 5: Enemy Variety & Meta-Progression

**Goal:** Add depth through enemy variety, a meta-progression loop, and run modifiers that make each playthrough feel different.

### 5.1 — New Enemy Types (3 new xenomorph variants)

Currently we have one enemy type (Drone). Add three more with distinct AI profiles:

```
                          ┌─────────────────────────────────────┐
                          │         ENEMY ROSTER (Phase 5)     │
                          ├──────────────┬──────────────────────┤
                          │  Drone       │  Baseline (shipped)  │
                          │  Runner      │  Fast, low HP, swarm │
                          │  Brute       │  Tank, slow, charges │
                          │  Spitter     │  Ranged acid attacks  │
                          └──────────────┴──────────────────────┘
```

**Runner** — `entities/enemy_runner.py`
- HP: 40 (Drone is 80), Speed: 2.0× Drone
- AI: No patrol state — always chasing. Spawns in groups of 3-4
- Attack: Leap attack (faster lunge, lower damage)
- Sprite: Smaller, leaner, elongated legs, red eyes (not green)
- Audio: High-pitched screech

**Brute** — `entities/enemy_brute.py`
- HP: 300, Speed: 0.6× Drone
- AI: Slow approach, charges when in line-of-sight (telegraphed 1s windup)
- Attack: Charge (high damage + knockback), ground pound (AoE)
- Sprite: Larger (48×48), bulky, heavy armor plates, no tail
- Audio: Deep roar, heavy footsteps
- On death: Spawns 2 acid pools (larger)

**Spitter** — `entities/enemy_spitter.py`
- HP: 60, Speed: 0.8× Drone
- AI: Maintains distance (200-400 units). Retreats if player closes
- Attack: Ranged acid spit (projectile, arcs, leaves acid pool on impact)
- Sprite: Hunched posture, distended head, glowing acid sacs on back
- Audio: Wet gurgling before spit, hiss on spit launch

**State machine additions:**

```
  RUNNER:    SPAWN → CHASE → LEAP → ATTACK → CHASE → (dead)
              (no patrol — always aggro)

  BRUTE:     SPAWN → APPROACH → WINDUP → CHARGE → RECOVER → APPROACH
                                    │              │
                                    └─ hp<50% ─────┴─→ ENRAGE (2× speed)

  SPITTER:   SPAWN → REPOSITION → SPIT → REPOSITION → (flee if close)
                                          │
                                          └─ spawns acid projectile
```

### 5.2 — Meta-Progression (Salvage System)

Between runs, the player spends salvaged materials on permanent upgrades:

```
  ┌──────────────────────────────────────────────────┐
  │              META-PROGRESSION FLOW               │
  │                                                  │
  │  Run ends → Salvage collected → Armory screen    │
  │       ↑                          │               │
  │       │                          ▼               │
  │  New run ← Deploy with upgrades ← Spend salvage  │
  └──────────────────────────────────────────────────┘
```

**Salvage currency:**
- Xenomorph chitin (drops on kill, +1 per kill, +3 per Brute)
- Supply caches (found during scavenge objectives, +5 each)
- Extraction bonus (+10 if extracted alive)

**Upgrade tree** (8 upgrades, 3 tiers each):

| Upgrade | T1 | T2 | T3 | Effect |
|---------|----|----|-----|--------|
| Reinforced Plating | +20 HP | +40 HP | +60 HP | Max health |
| Auto-Injector | +50% regen | +100% regen | Regen on kill | Health regen rate |
| Extended Mags | +30% ammo | +60% ammo | +100% ammo | Magazine size |
| Rapid Fire | +15% FR | +30% FR | +50% FR | Fire rate |
| Acid Resistance | -30% acid | -60% acid | Acid immunity | Acid damage reduction |
| Motion Scanner | +25% range | +50% range | See through walls | Tracker range |
| Combat Stims | +10% speed | +20% speed | +30% speed + no slow on slopes | Movement speed |
| Scavenger | +1 salvage/kill | +2/kill | +3/kill + rare drops | Salvage multiplier |

**Files:**
- `game/meta_progression.py` — `MetaState` class (save/load JSON), `Upgrade` dataclass
- `game/armory.py` — Armory screen rendering + upgrade purchase logic
- `data/upgrades.json` — Upgrade definitions (loaded at startup)
- Save file: `~/.xeno_breach/save.json` (auto-created)

### 5.3 — Run Modifiers (Mutators)

Each run rolls 1-2 mutators that change the rules:

| Mutator | Effect |
|---------|--------|
| `FOG_OF_WAR` | Vision limited to 200px radius around player |
| `ACID_RAIN` | Acid pools spawn randomly across terrain every 10s |
| `BLOODLUST` | Enemies move 30% faster but have 50% HP |
| `NIGHT_OPS` | Terrain darkened, visor provides light cone |
| `SWARM` | 2× enemy count, but they deal 40% less damage |
| `BRUTE_FORCE` | Every 3rd wave is all Brutes |

**Files:**
- `game/mutators.py` — `Mutator` base class + 6 subclasses, `roll_mutators(seed)` function

### 5.4 — Elite Enemies

5% chance per spawn to roll an elite variant:
- **Gamma** — Glowing green, +50% HP, drops 3× salvage
- **Alpha** — Glowing red, +100% HP, enraged (always fast)
- **Corrupted** — Glowing purple, leaves acid trail while moving

**Files:**
- `entities/enemy_mods.py` — `EliteMod` dataclass, `apply_elite(enemy, mod)` function

---

## Phase 6: Environmental Depth

### 6.1 — Destructible Terrain

- Crater walls can be destroyed by explosives (shotgun at close range, future grenade)
- Creates new pathways and changes cover dynamically
- Terrain heightfield modified at runtime (`terrain.modify_height(x, y, radius, depth)`)

### 6.2 — Interactive Props

| Prop | Effect |
|------|--------|
| Supply cache | +5 salvage, +health pack |
| Explosive barrel | Chain explosions, AoE damage |
| Sentry turret (broken) | Repairable: defends position for 30s |
| Data terminal | Reveals map + objective markers |
| Med-bay station | Full heal (one-time use per run) |

### 6.3 — Dynamic Weather

- Acid storms (reduced visibility + periodic acid rain damage)
- Dust storms (reduced visibility, muffles audio)
- Solar flare (increased visibility, enemies more aggressive)
- Weather changes every 60-120s, telegraphed by HUD

---

## Phase 7: Arsenal Expansion

### 7.1 — New Weapons

| Weapon | Type | Unlock |
|--------|------|--------|
| Smart Rifle | Hitscan with auto-aim assist (slight) | Default |
| SMG | Fast fire, low damage, high spread | T1 salvage |
| Revolver | High damage, slow fire, piercing | T2 salvage |
| Grenade Launcher | AoE explosive, arc projectile | T3 salvage |
| Railgun | Charged shot, pierces all enemies, long cooldown | T3 salvage |
| Plasma Caster | Charged beam, sustained damage, overheats | T3 salvage |

### 7.2 — Equipment/Throwables

| Item | Effect | Key |
|------|--------|-----|
| Frag grenade | AoE explosion | Q |
| Acid grenade | Leaves acid pool on impact | Q (hold) |
| Motion sensor | Deployable tracker ping for 15s | E |
| Stim pack | Instant +30 HP, 30s cooldown | F |
| Flare | Lights area for 20s (Night Ops) | G |

### 7.3 — Weapon Mods

Findable during runs (not meta-progression):
- **Extended barrel** — +20% range
- **Compensator** — -30% recoil spread
- **Acid rounds** — Bullets leave acid on hit
- **Incendiary rounds** — Bullets leave fire on hit
- **Scope** — +15% accuracy at range

---

## Phase 8: Boss Encounters

### Boss 1 — Brood Mother (Wave 5)
- Large (96×96 sprite), 2000 HP
- Spawns Runner swarms every 15s
- Attacks: Acid spray cone, tail sweep, charge
- Phases: 100-66% normal, 66-33% enrage (spawns faster), 33-0% berserk (charges constantly)
- Defeat triggers extraction beacon automatically

### Boss 2 — Praetorian Guard (Wave 10)
- Elite Brute variant, 3000 HP
- Shielded front (must flank)
- Attacks: Shield bash, ground pound shockwave, summon 2 Brutes
- Drops unique weapon mod on death

### Boss 3 — Queen (Final Wave)
- Massive (128×128), 5000 HP
- Multi-phase: grounded → wall climb → egg sac spawn → final stand
- Requires destroying egg sacs to expose weak point
- Victory = ending screen + unlock Nightmare difficulty

---

## Phase 9: Polish & Content

### 9.1 — Procedural Audio Music
- Dynamic music system: ambient drone → tension build → combat intensity → boss theme
- All synthesized via numpy (consistent with existing audio system)
- Music intensity tracks nearby enemy count + wave number

### 9.2 — Achievements
- 20 achievements (first kill, 100 kills, extract with 10% HP, solo a Brute, etc.)
- Displayed on game-over screen + persistent tracking

### 9.3 — Daily Challenge
- Fixed seed per day (hash of date)
- Leaderboard tracking locally (top 10 runs)
- Special mutator guaranteed (never same as yesterday)

### 9.4 — Accessibility
- Colorblind palettes (Protanopia, Deuteranopia, Tritanopia)
- Adjustable text size
- Toggle: screen shake, hit flash, particle density
- Key rebinding

---

## Revised Milestone Summary

| Milestone | Phase | Scope | New Files |
|-----------|-------|-------|-----------|
| **M5: Enemy Variety** | 5.1 | 3 new enemy types + elite variants | `enemy_runner.py`, `enemy_brute.py`, `enemy_spitter.py`, `enemy_mods.py` |
| **M5: Meta-Progression** | 5.2 | Salvage + armory + 8 upgrades | `meta_progression.py`, `armory.py`, `upgrades.json` |
| **M5: Run Modifiers** | 5.3 | 6 mutators | `mutators.py` |
| **M6: Environment** | 6 | Destructible terrain + props + weather | `props.py`, `weather.py`, terrain modifications |
| **M7: Arsenal** | 7 | 6 new weapons + 5 throwables + 5 mods | `weapons_expanded.py`, `equipment.py`, `weapon_mods.py` |
| **M8: Bosses** | 8 | 3 multi-phase boss fights | `bosses.py`, boss sprites |
| **M9: Polish** | 9 | Music + achievements + daily + a11y | `music.py`, `achievements.py`, `daily.py`, `accessibility.py` |

---

## Technical Considerations

### Architecture — Enemy Base Class Refactor
Current `Xenomorph` class is monolithic. Phase 5 requires extracting a base `Enemy` class:

```
  Enemy (base)
    ├── update(dt, player, terrain, enemies)
    ├── take_damage(amount)
    ├── draw(screen, cam_x, cam_y)
    ├── state: str
    ├── health, speed, radius, damage
    └── ai_state: State

  Drone(Enemy)      — current behavior
  Runner(Enemy)     — override: no patrol, leap attack
  Brute(Enemy)      — override: charge + ground pound
  Spitter(Enemy)    — override: ranged attack, keep distance
```

**Risk:** Breaking existing AI behavior during refactor.
**Mitigation:** Extract base class first, verify Drone behavior is byte-identical, then add new subclasses.

### Save System
- JSON file at `~/.xeno_breach/save.json`
- Schema: `{ "salvage": int, "upgrades": { "health": 2, "fire_rate": 1, ... }, "achievements": [...], "best_run": {...} }`
- Load on startup, save on run end + armory purchase
- Corruption recovery: if JSON parse fails, reset to defaults

### Performance Budget
- Current: 60 FPS with 30 enemies + particles
- Target: 60 FPS with 50 enemies + 5 fire zones + weather + props
- Optimization: enemy AI updates can be throttled (update far enemies at 30Hz instead of 60Hz)

### Difficulty Curve

```
  Wave  1-3:   Drones only (learning)
  Wave  4-6:   Drones + Runners (pressure)
  Wave  5:     BOSS: Brood Mother
  Wave  7-9:   Drones + Runners + Spitters (tactical)
  Wave 10:     BOSS: Praetorian Guard
  Wave 11-14:  All types + elites (chaos)
  Wave 15:     BOSS: Queen (final)
  Wave 16+:    Endless mode (scaling HP + speed)
```

---

## Recommended Implementation Order

1. **Enemy base class refactor** — extract `Enemy` from `Xenomorph`, verify no regressions
2. **Runner** — simplest new enemy (fast drone variant), validates the subclass pattern
3. **Brute** — introduces charge attack + larger sprite + knockback mechanic
4. **Spitter** — introduces ranged enemy AI + projectile acid
5. **Elite mods** — overlay system (modify existing enemies)
6. **Meta-progression** — salvage currency + armory screen + save system
7. **Mutators** — run-level rule changes
8. **Then Phase 6+** as time permits
