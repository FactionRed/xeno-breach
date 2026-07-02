# Implementation Plan — Xeno Breach: Survival Shooter on Procedural Rocky Planets

> **Status:** Draft v1.0 · 2026-06-30
> **Parent assets:** `planet_generator.py` (terrain + rendering), `DESIGN.md` (visual token spec), `xeno_shooter/`

---

## 1. Project Overview

**Xeno Breach** is a top-down survival shooter set on the procedurally generated
rocky planets produced by `planet_generator.py`. The player is a colonial
salvager stranded after a drop-ship crash, fighting escalating waves of
xenomorph-like creatures across an alien wasteland of craters, ridges, and
polar ice.

**Core loop:** Scavenge → Defend → Advance → Extract.

| Attribute | Decision |
|-----------|----------|
| Genre | Top-down twin-stick survival shooter |
| Engine | Python + pygame-ce (2.5D heightmap rendering) |
| Visual style | See `DESIGN.md` — "salvage chic," dark industrial UI over alien terrain |
| Procedural system | Reuse `planet_generator.py` noise + crater + colorize pipeline |
| Session length | 15–25 min runs, roguelite structure |
| Target platform | Windows / Linux desktop |

---

## 2. What We Already Have

| Asset | File | Role |
|-------|------|------|
| Terrain heightfield | `planet_generator.py` → `make_grid`, `fbm_grid`, `add_craters_grid` | Generates a `(lat,lon)` height grid with fBm noise + impact craters |
| Elevation coloring | `planet_generator.py` → `colorize_grid` | 5-tier palette (basins → lowland → rock → highland → snow) |
| Terrain normals | `planet_generator.py` → `terrain_normals_grid` | Per-gridpoint surface normals for slope shading |
| Software rasterizer | `planet_generator.py` → `render`, `bilinear_sample` | Z-buffered ray-sphere render + bilinear color/normal sampling |
| Design system | `DESIGN.md` | Full token spec: colors, typography, components, WCAG-validated |
| Output artifacts | `planet.png`, `planet_scene.png` | Reference renders showing the target visual quality |

---

## 3. Architecture

```
xeno_shooter/
├── DESIGN.md                 # ✅ Done — visual token spec
├── IMPLEMENTATION_PLAN.md    # ✅ This file
├── main.py                   # Entry point: game loop, state machine
├── config.py                 # Constants (screen, FPS, balance tuning)
│
├── terrain/
│   │   __init__.py
│   ├── heightfield.py        # Adapted from planet_generator.py
│   ├── terrain_renderer.py   # Real-time heightmap → screen renderer
│   └── biome.py              # Biome rules (color, hazards, cover density)
│
├── entities/
│   │   __init__.py
│   ├── player.py             # Player controller: movement, health, weapons
│   ├── xenomorph.py          # Enemy AI: states, pathfinding, attacks
│   ├── xenomorph_spawner.py  # Wave director + spawn logic
│   └── projectiles.py        # Bullets, acid spray, tracers
│
├── combat/
│   │   __init__.py
│   ├── weapons.py            # Weapon definitions: rifle, shotgun, flamer
│   ├── damage.py             # Damage resolution, acid blood mechanics
│   └── particles.py          # Muzzle flash, blood, explosions, acid pools
│
├── ui/
│   │   __init__.py
│   ├── hud.py                # HUD panels (health, ammo, minimap, objectives)
│   ├── motion_tracker.py     # Aliens-style ping display
│   └── menus.py              # Title, pause, game-over, extraction screen
│
├── game/
│   │   __init__.py
│   ├── state_machine.py      # MENU → BRIEFING → PLAYING → EXTRACTION → GAMEOVER
│   ├── wave_director.py     # Spawn scaling, objective triggers, difficulty curve
│   ├── objectives.py        # Mission types: survive, reach point, defend, scavenge
│   └── world.py              # Planet seed, biome selection, hazard placement
│
└── assets/
    ├── sprites/              # Player, xenomorph, weapons (PNG sprite sheets)
    ├── audio/                # Gunfire, alien screeches, motion tracker ping, ambient
    └── data/                 # Weapon stats, wave configs, biome tables (JSON/YAML)
```

---

## 4. Implementation Phases

### Phase 1 — Terrain Playground (Week 1)

**Goal:** Walk/run a player across a procedurally generated planet surface in real time.

**Tasks:**

1. **Extract terrain core from `planet_generator.py`**
   - Copy `make_grid`, `fbm_grid`, `add_craters_grid`, `colorize_grid`,
     `terrain_normals_grid` into `terrain/heightfield.py`
   - Add a `local_heightfield(seed, center_lat, center_lon, radius, res)` function
     that samples a square patch around the player's current position instead of
     generating the entire planet — this gives effectively infinite terrain
   - Keep the existing noise parameters (OCTAVES=5, HEIGHT_AMP=0.14, CRATER_COUNT=18)
     as defaults

2. **Real-time terrain renderer** (`terrain_renderer.py`)
   - Render a top-down angled view (30–45° pitch) of the local height patch
   - For each screen pixel, map to terrain coordinates, bilinearly sample
     color + normal, apply Lambert shading (reuse the `render` logic from
     `planet_generator.py` but adapt to a local patch instead of a full sphere)
   - Target 60 FPS at 1280×720 with a 200×200 terrain grid (40k pixels →
     trivially fast in numpy)
   - Player stays centered; terrain scrolls beneath them

3. **Player movement**
   - WASD for directional movement, mouse for aim
   - Speed varies by slope (uphill slower — use terrain normals to compute
     incline)
   - Collision with steep crater rims (slope > threshold = impassable rock wall)
   - Footstep dust particles (placeholder circles)

4. **Camera system**
   - Smooth follow with slight look-ahead in movement direction
   - Slight zoom-out when sprinting, zoom-in when aiming
   - Screen shake on explosions

**Deliverable:** A runnable demo where you run across an alien planet surface
with elevation, craters, and snow caps, with slope-based movement and a
following camera.

---

### Phase 2 — Combat Core (Week 2)

**Goal:** Shoot xenomorphs and watch them die.

**Tasks:**

1. **Weapon system** (`combat/weapons.py`)
   - Data-driven from `assets/data/weapons.json`:
     ```json
     {
       "pulse_rifle": {
         "damage": 18, "fire_rate": 600, "mag_size": 30,
         "range": 800, "spread": 2.5, " pellets": 1,
         "tracer_color": "#FFB454", "muzzle_flash": true
       },
       "shotgun": {
         "damage": 12, "fire_rate": 900, "mag_size": 8,
         "range": 400, "spread": 12, "pellets": 6,
         "tracer_color": "#FF4136", "muzzle_flash": true
       },
       "flamethrower": {
         "damage": 8, "fire_rate": 100, "mag_size": 100,
         "range": 250, "spread": 30, "pellets": 1,
         "tracer_color": "#FF4136", "muzzle_flash": false,
         "area_denial": true
       }
       }
     ```
   - Hitscan for rifle/shotgun; cone for flamethrower (lingering fire zones)
   - Reload mechanic (R key, timed per weapon, interruptible)
   - Weapon switch (1/2/3 keys)

2. **Projectile + tracer rendering** (`entities/projectiles.py`)
   - Tracer lines: bright `warning` amber for pulse rifle, `danger` red for
     shotgun, flame cone for flamer
   - Impact sparks on terrain hit
   - Bullet trail fade (alpha decay over 3 frames)

3. **Xenomorph entity** (`entities/xenomorph.py`)
   - Sprite: elongated head, dark chitinous body, bladed tail (drawn or
     placeholder dark elongated ellipse with gradient)
   - AI state machine:
     ```
     PATROL → (player detected) → CHASE → (in range) → LUNGE → ATTACK → (hit) → STAGGER → CHASE
                                                      ↓ (killed)
                                                    DEATH_ANIM → ACID_POOL
     ```
   - Movement: crawl toward player, speed varies by terrain slope
   - Pathfinding: simple steering (move toward player, avoid steep slopes via
     terrain normals). If path blocked, try to flank. No A* needed for
     top-down open terrain — boids-style steering is sufficient
   - Health: 40 HP (3 rifle hits, 1 shotgun blast at close range)
   - Death: ragdoll fade + acid blood pool (damages player on contact for 3s)

4. **Damage resolution** (`combat/damage.py`)
   - Hitscan ray vs entity bounding circles
   - Damage falloff by distance for shotgun
   - Headshot multiplier (2x) if hit in upper sprite region
   - Acid blood: on xenomorph death, spawn a circular acid pool at death
     location. Player takes 5 dmg/s while standing in it. Pools fade after 5s.
   - Player death at 0 HP → game over state

5. **Particle system** (`combat/particles.py`)
   - Muzzle flash (2-frame `warning`-colored flash at barrel tip)
   - Blood spray (`bio-mass` colored particles on hit)
   - Acid splash (`acid` green particles on xenomorph death)
   - Explosion (for grenades/environmental hazards — `danger` + `warning`)
   - Dust kicks when running on terrain

**Deliverable:** Shoot xenomorphs with 3 weapons; they chase, attack, die
with acid blood; player takes damage and can die.

---

### Phase 3 — Waves, Objectives, Extraction (Week 3)

**Goal:** Full roguelite run loop with escalating threat.

**Tasks:**

1. **Wave director** (`game/wave_director.py`)
   - Difficulty scales with time + objectives completed:
     ```
     wave_n_enemies = 5 + 3 * wave_number
     wave_spawn_rate = max(0.5s, 2.0s - 0.1s * wave_number)
     enemy_hp_mult = 1.0 + 0.08 * wave_number
     enemy_speed_mult = 1.0 + 0.04 * wave_number
     ```
   - Spawn from terrain depressions (craters, basins) — use the heightfield
     to find low-elevation points near but not visible to the player
   - Breather windows between waves (5s, shrinking with wave number)
   - Mini-boss every 5 waves (brute xenomorph: 200 HP, charge attack, acid
     spray on death covering larger area)

2. **Objective system** (`game/objectives.py`)
   - **SURVIVE:** Live for N seconds against waves
   - **REACH:** Get to a beacon marker across the terrain (craters provide
     cover, ridges block line of sight)
   - **DEFEND:** Protect a downed shuttle section (static structure) from
     waves for a timer
   - **SCAVENGE:** Collect N supply crates scattered across the terrain,
     each guarded by a small xenomorph pack
   - One objective per "level" (planet sector); completing it unlocks
     extraction

3. **Extraction sequence**
   - When objective complete, extraction beacon appears on terrain (pulsing
     `tertiary` red light visible from far away)
   - Player must reach the beacon under fire (final wave spawns at maximum
     intensity)
   - 10-second hold at beacon to extract → victory screen
   - If player dies during extraction → game over (no retries)

4. **State machine** (`game/state_machine.py`)
   ```
   MENU → BRIEFING (objective text, planet seed display)
        → PLAYING (terrain + combat + HUD)
        → EXTRACTION (beacon active, final wave)
        → VICTORY (stats: kills, time, accuracy, planet seed)
        → GAMEOVER (same stats + retry option)
   ```
   - `P` pauses → PAUSED state (dim screen, objective card overlay)
   - `ESC` returns to menu

**Deliverable:** Full run loop — drop in, fight waves, complete objective,
extract or die. Repeatable with different planet seeds.

---

### Phase 4 — HUD, Audio, Polish (Week 4)

**Goal:** Game feels like the `DESIGN.md` spec — cold operator hardware under
biological threat.

**Tasks:**

1. **HUD** (`ui/hud.py`) — implement all components from `DESIGN.md`:
   - **Health bar** (`hud-panel` housing, `health-bar` fill that promotes to
     `health-bar-critical` below 25% with a flash)
   - **Ammo readout** (`ammo-readout`: mono digits, right-aligned, `on-tertiary`
     on `primary` background)
   - **Weapon selector** (3 slots, active slot highlighted with `tertiary` border)
   - **Minimap** (top-down terrain height map thumbnail with player dot +
     objective markers; craters shown as dark circles)
   - **Objective card** (`objective-card`: current objective text, progress
     bar, pinned to right side of screen)
   - **Threat banner** (`threat-banner` → `threat-banner-active` during breach
     events: full-bleed `bio-mass` strip above HUD with `warning` text; flips
     to `danger` fill during active breach)

2. **Motion tracker** (`ui/motion_tracker.py`)
   - Aliens-style circular radar in bottom-right corner
   - `motion-blip` (acid green, 6px) for ambient contacts within detection
     range (60 units)
   - Promotes to `motion-blip-threat` (danger red, 8px) for hostile contacts
     within 30 units
   - Ping sweep animation (rotating line, 2s period)
   - Static/noise when xenomorph is underground or behind thick terrain

3. **Menu screens** (`ui/menus.py`)
   - **Title:** `h1` "XENO BREACH" in `IBM Plex Mono` on `primary` background,
     `button-primary` "DEPLOY" + `button-ghost` "BRIEFING"
   - **Briefing:** `objective-card` with mission text, planet seed display,
     `h2` sector designation (e.g., "SECTOR LV-426-B")
   - **Game over:** Stats panel (`readout` text), `button-primary` "REDEPLOY"
   - All transitions: 200ms fade, no slides (industrial, not flashy)

4. **Audio** (`assets/audio/`)
   - Pulse rifle: sharp metallic crack (short .ogg, pitch-shifted per shot)
   - Shotgun: heavy thump + metallic ring
   - Flamethrower: sustained whoosh (looped .ogg)
   - Xenomorph screech: descending chitter (played on detection + on death)
   - Motion tracker ping: subtle sonar tone (2s interval, speeds up as
     contacts approach)
   - Ambient: low wind drone + occasional distant creature calls
   - UI clicks: muted metallic thuds
   - Use pygame.mixer (channels: 8 for SFX, 1 for music, 1 for ambient loop)

5. **Planet procedural seeding** (`game/world.py`)
   - Each run picks a random seed → different terrain layout, crater
     distribution, objective placement
   - Planet "biomes" adjust palette + hazard density:
     - **Barren** (default): standard craters, low cover, fast movement
     - **Polar:** snow caps, reduced visibility (fog), slower movement on ice,
       fewer craters but more ridge cover
     - **Cratered:** dense crater field, lots of cover, ambush-prone
     - **Highland:** elevated plateaus with cliffs (fall damage), long sight
       lines for rifle
   - Biome determined by sampling the planet's latitude at the drop zone

6. **Juice and feel**
   - Hit markers on xenomorphs (small `warning`-colored X that fades)
   - Kill confirmation (brief `danger` flash on the dead enemy)
   - Screen shake: 2px on shotgun, 6px on explosion, 10px on brute charge hit
   - Low-health vignette: pulsing `danger`-tinted screen edge below 25% HP
   - Time slowdown (0.3x for 200ms) on player near-death

**Deliverable:** Full polished game with HUD, motion tracker, menus, audio,
and biome variety. Ready to playtest.

---

## 5. Data-Driven Configuration

All tuning values live in `assets/data/` as JSON so designers can iterate
without touching code:

```
assets/data/
├── weapons.json         # Weapon stats (damage, fire rate, spread, pellets)
├── waves.json           # Wave composition, spawn rates, scaling curves
├── biomes.json          # Biome palettes, hazard densities, movement mods
├── xenomorph_types.json # Enemy variants (drone, runner, brute, queen)
└── objectives.json      # Objective definitions and triggers
```

---

## 6. Key Technical Decisions

| Decision | Rationale |
|----------|-----------|
| **pygame-ce, not Godot/Unity** | Keeps the Python ecosystem from `planet_generator.py`; avoids engine onboarding overhead for a prototype |
| **Top-down 2.5D, not full 3D** | The terrain is a heightfield — rendering it as a tilted top-down view with slope shading reuses the existing rasterizer logic directly. Full 3D would require porting to a different pipeline. |
| **Hitscan weapons, not projectiles** | Top-down combat at 60 FPS — hitscan is simpler, cheaper, and reads better for rifle/shotgun. Flamethrower uses a cone + lingering zones. |
| **Steering AI, not A* pathfinding** | Open terrain with slope-based obstacles doesn't need grid pathfinding. Boids-style steering with terrain-normal avoidance is cheaper and looks organic (xenomorphs crawl around ridges rather than pathing through nodes). |
| **Local terrain patch sampling** | Instead of generating the entire planet (256×512 grid), sample a 200×200 patch around the player's lat/lon. The noise function is cheap per-point; only compute what's on screen. Player position maps to a lat/lon origin that shifts as they move. |
| **Craters as tactical cover** | The existing crater generation produces bowl-shaped depressions with raised rims. These become natural cover walls (line-of-sight blockers) and ambush spawn points — the terrain generator's output IS the level design. |
| **DESIGN.md tokens drive the HUD** | Every HUD color, font size, corner radius, and spacing value comes from the validated token spec. No magic numbers in rendering code. |
| **Procedural sprites, not loaded PNGs** | All character and enemy sprites are drawn at runtime via pygame primitives (no external asset files needed). This keeps the project zero-dependency and allows infinite variation via seeds. |
| **Formalized AI state machine** | Each AI state is its own class (PatrolState, ChaseState, etc.) with enter/update/exit semantics, not inline if-else chains. This makes adding new enemy types trivial — just add new state classes. |
| **Animation state machine decoupled from AI** | The sprite controller watches the AI state machine's string state and maps it to animation states. Adding a new animation is a matter of adding a new state + frames to the sprite factory, with no changes to AI logic. |

---

## 6.1 AI State Machine — Xenomorph

The xenomorph AI uses a formalized finite state machine. Each state is a class
with `enter()`, `update()`, and `exit()` methods. Transitions are driven by
sensors (distance to player, HP, timers) evaluated after each state update.

```
                         ┌──────────────────────────────────────────┐
                         │                                          │
                         ▼                                        │
                   ┌──────────┐    player detected     ┌──────────┐
         ────────→ │  PATROL  │───────────────────────→ │  CHASE   │
                   └──────────┘                         └──────────┘
                     │    ▲                               │    ▲
          damaged    │    │                    in lunge  │    │
                     ▼    │                    range     ▼    │ player
                   ┌──────────┐                   ┌──────────┐ escaped
                   │  CHASE   │←───────────────── │  LUNGE   │─────┘
                   └──────────┘  timer expired    └──────────┘
                        │                            │
              in attack │                            │ hit player
               range    ▼                            ▼
                   ┌──────────┐                  ┌──────────┐
                   │  ATTACK  │────────────────→ │ STAGGER  │
                   └──────────┘   hit player     └──────────┘
                        │                            │
                        │                    timer    │
                        │                    expired │
                        └───────────┬────────────────┘
                                    │
                          hp <= 0   │
                                    ▼
                              ┌──────────┐
                              │  DEATH   │──→ spawn acid pool
                              └──────────┘
```

### State Behaviors

| State | Behavior | Duration |
|-------|----------|----------|
| **PATROL** | Wander between random waypoints at 40% speed. Pick new target on arrival or if blocked by terrain. | Until player detected |
| **CHASE** | Move toward player at full speed. Terrain-aware steering: if slope blocks direct path, strafe perpendicular to flank. | Until in lunge/attack range |
| **LUNGE** | Fast dash toward player at 2.5× speed. | 0.3s |
| **ATTACK** | Deal `attack_damage` to player after 0.1s windup. Knockback self away from player. | 0.15s + knockback |
| **STAGGER** | Apply knockback velocity, decelerate. | 0.2s |
| **DEATH** | Brief collapse animation, then spawn acid pool at death location. | 0.4s |

### Sensors

| Sensor | Condition | Effect |
|--------|-----------|--------|
| `detect_player` | dist < 400px | PATROL → CHASE |
| `in_lunge_range` | dist < 120px & cooldown ready | CHASE → LUNGE |
| `in_attack_range` | dist < 35px | CHASE/LUNGE → ATTACK |
| `lunge_expired` | lunge timer > 0.3s | LUNGE → CHASE + cooldown |
| `attack_hit` | attack timer > 0.15s | ATTACK → STAGGER |
| `stagger_recovered` | stagger timer > 0.2s | STAGGER → CHASE + cooldown |
| `hp_depleted` | hp <= 0 | ANY → DEATH |

### Scaling

| Parameter | Formula |
|-----------|---------|
| Wave enemy count | `5 + 3 × wave_number` |
| Enemy HP | `40 × (1 + 0.08 × wave_number)` |
| Enemy speed | `90 × (1 + 0.04 × wave_number)` |
| Spawn interval | `max(0.4s, 1.5 - 0.08 × wave_number)` |
| Breather duration | `max(3.0s, 8.0 - 0.5 × wave_number)` |

---

## 6.2 Game State Machine

```
    ┌────────┐  select DEPLOY  ┌──────────┐  SPACE  ┌─────────┐
    │  MENU  │───────────────→│ BRIEFING │────────→│ PLAYING │←──┐
    └────────┘                └──────────┘         └─────────┘   │
         ▲                                              │        │
         │                                    objective │        │
         │                                    complete  │        │ ESC
         │                                         ▼     │        │
    ┌────────┐  ENTER                     ┌────────────┐ │   ┌──────┐
    │GAMEOVER│←───────────────────────────│ EXTRACTION │ │   │PAUSED│
    └────────┘                            └────────────┘ │   └──────┘
         ▲                                     │          │      │
         │ player dies                         │ beacon    │      │ ESC
         │                                     │ hold      │      │
         │                                     ▼          │      │
         │                               ┌─────────┐      │      │
         │                               │ VICTORY │      │      │
         │                               └─────────┘      │      │
         │                                     │            │      │
         └─────────────────────────────────────┴────────────┘      │
                                                                   │
              VICTORY/GAMEOVER ──ENTER──→ MENU ←───────────────────┘
```

### Game States

| State | Purpose |
|-------|---------|
| **MENU** | Title screen with DEPLOY/QUIT options |
| **BRIEFING** | Mission briefing: sector designation, objective, deploy prompt |
| **PLAYING** | Core gameplay: combat + waves + objective tracking |
| **EXTRACTION** | Objective complete → extraction beacon active → hold to extract |
| **VICTORY** | Extraction successful → stats screen |
| **GAMEOVER** | Player death → stats screen with redeploy option |
| **PAUSED** | ESC during PLAYING → frozen game with overlay |

---

## 6.3 Animation State Machine — Player

The player sprite has 7 animation states, driven by game logic inputs:

```
                    ┌──────┐
              ┌────→│ IDLE │←──────────────┐
              │     └──────┘                │
              │       │                     │
         start│moving │                     │stop
              │       ▼                     │
              │  ┌──────┐               ┌──────┐
              │  │ WALK │←───stop───→    │SPRINT│
              │  └──────┘               └──────┘
              │    │  │                    │
              │    │  └──sprint──→────────┘
              │    │
       fire   │    ▼
         ┌────┐  ┌──────┐  reload  ┌────────┐
         │SHOOT│→│      │────────→│ RELOAD │
         └────┘  │      │         └────────┘
              │  │      │              │
   take_dmg  │  │      │       done   │
         ┌────┐  │      │←────────────┘
         │HURT │→│      │
         └────┘  │      │
              │  └──────┘  (any state)
              │       │
              │  hp≤0 │
              ▼       ▼
         ┌──────┐  ┌──────┐
         │ DEAD │←─│ DEAD │
         └──────┘  └──────┘
```

### Player Animation States

| State | Frames | FPS | Loop | Trigger |
|-------|--------|-----|------|--------|
| idle | 2 (breathing) | 4 | yes | stop moving |
| walk | 6 (leg cycle) | 12 | yes | moving (normal) |
| sprint | 4 (lean + pump) | 14 | yes | moving + shift |
| shoot | 2 (recoil) | 20 | no | fire weapon |
| reload | 3 (lower/swap/raise) | 6 | no | R key |
| hurt | 1 (red flash) | 4 | no | take damage |
| dead | 3 (collapse) | 8 | no | hp ≤ 0 |

---

## 6.4 Animation State Machine — Xenomorph

The xenomorph sprite has 6 animation states, driven by the AI state machine:

```
    ┌────────┐  player detected  ┌────────┐  in lunge  ┌────────┐
    │ PATROL │──────────────────→│ CHASE  │───────────→│ LUNGE  │
    └────────┘                    └────────┘            └────────┘
         ▲                          │   ▲                   │
         │                          │   │         hit/timer │
         │                          │   │                   ▼
         │                     in   │   │  timer     ┌────────┐
         │                   attack  │   └──────────→│ATTACK  │
         │                   range   │                └────────┘
         │                          │                     │
         │                     ┌──────┐                  │
         │                ┌───→│STAGGER│←─────────────────┘
         │                │    └──────┘
         │   timer        │       │
         │  expired       │  timer│
         └────────────────┘expired│
                                    │
                          hp ≤ 0   │
                                    ▼
                              ┌────────┐
                              │ DEATH  │──→ acid pool
                              └────────┘
```

### Xenomorph Animation States

| State | Frames | FPS | Loop | AI State Mapping |
|-------|--------|-----|------|-----------------|
| patrol | 4 (undulating crawl) | 8 | yes | `patrol` |
| chase | 4 (fast crawl, tail lash) | 12 | yes | `chase` |
| lunge | 3 (coil/spring/extend) | 14 | no | `lunge` |
| attack | 2 (strike/recover) | 16 | no | `attack` |
| stagger | 2 (knockback + flash) | 10 | no | `stagger` |
| death | 4 (collapse + dissolve + acid) | 8 | no | `death` |

---

## 7. Risk Mitigation

| Risk | Mitigation |
|------|------------|
| pygame-ce terrain rendering too slow at 60 FPS | Profile early. If numpy terrain sampling is the bottleneck, pre-compute terrain color+normal for a larger patch (e.g. 400×400) and cache it, only re-sampling when the player crosses a chunk boundary. If still slow, downgrade to 48 FPS. |
| Steering AI looks dumb (xenomorphs stuck on cliffs) | Add a "wall climb" behavior: if a xenomorph is blocked by a steep slope for >0.5s, it transitions to a climb state that moves over the ridge (slower, no attack). Xenomorphs are supposed to crawl on walls anyway. |
| Acid blood pools are unfun (invisible damage) | Always render acid pools with `acid`-colored particle effects + a faint smoke. Add a 0.5s grace period after a xenomorph death where the pool is forming but not yet damaging. |
| Motion tracker is too noisy to be useful | Two-tier detection: green blips only appear within 60 units AND have line-of-sight (terrain raycast). Red blips appear within 30 units regardless of terrain. Player learns to trust the red blips for immediate threat. |
| Scope creep (too many biomes, weapons, enemy types) | Ship Phase 1–3 with one biome (Barren), three weapons, one enemy type (drone). Phase 4 adds biomes + brute. Post-launch adds runner, queen, polar biome. |

---

## 8. Milestone Summary

| Milestone | End of Phase | Weeks | Playable? |
|-----------|-------------|-------|-----------|
| **M1: Terrain playground** | Phase 1 | 1 | Run across planet surface |
| **M2: Combat core** | Phase 2 | 2 | Shoot and kill xenomorphs |
| **M3: Full run loop** | Phase 3 | 3 | Complete run: drop → fight → extract |
| **M4: Polished release** | Phase 4 | 4 | Full game with HUD, audio, biomes |

---

## 9. Getting Started

After approval, Phase 1 begins with:

```bash
cd C:/Users/sydne/xeno_shooter
pip install pygame-ce numpy noise
# Extract terrain core from planet_generator.py into terrain/heightfield.py
# Build terrain_renderer.py (adapt the render() function for a local patch)
# Build player.py (movement + camera)
# Run: python main.py
```

The first playable is a player running across a cratered alien landscape
with slope-based movement and a following camera — no enemies, no HUD, just
the planet beneath your feet.
