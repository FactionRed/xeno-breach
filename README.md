# Xeno Breach

A top-down survival shooter on procedurally generated rocky planets. Built with Python, pygame-ce, numpy, and the `noise` library.

## Features

- **Procedural terrain** — fBm simplex noise heightfields with impact craters, slope-based shading, and 5-tier elevation coloring
- **4 enemy types** — Drone (baseline), Runner (fast swarmer), Brute (tank with charge attack), Spitter (ranged acid projectiles)
- **Elite variants** — Gamma (green, +50% HP), Alpha (red, enraged), Corrupted (purple, acid trail)
- **3 weapons** — Pulse rifle, shotgun, flamethrower with distinct feel and stats
- **4 biomes** — Barren wasteland, polar ice field, crater field, highland plateau
- **Wave director** — Escalating difficulty with enemy type progression by wave number
- **Objectives** — Survive, reach beacon, defend position, scavenge supply caches + extraction
- **32×32 pixel art sprites** — Designed via JSON coordinate data, rendered with Pillow
- **Procedural audio** — 11 sound effects synthesized from numpy waveforms, no external files
- **Game-feel juice** — Screen shake, hit markers, floating damage numbers, kill combos, low-health vignette, off-screen enemy indicators, reload progress bar
- **AI-generated splash art** — Title screen and game-over backgrounds

## Installation

```bash
pip install pygame-ce numpy noise pillow
```

## Running

```bash
python main.py
```

## Controls

| Key | Action |
|-----|--------|
| WASD / Arrows | Move |
| Mouse | Aim |
| LMB | Fire |
| 1/2/3 | Switch weapons |
| R | Reload |
| Shift | Sprint |
| M | Mute audio |
| F1 | Debug overlay |
| ESC | Pause / Quit |
| Space | Deploy / Confirm |

## Project Structure

```
xeno_shooter/
├── main.py                    # Game loop, state machine, combat integration
├── config.py                  # All game constants + DESIGN.md color tokens
├── DESIGN.md                  # Google DESIGN.md visual token spec
├── IMPLEMENTATION_PLAN.md     # Phases 1-4 plan
├── IMPLEMENTATION_PLAN_PHASE5_PLUS.md  # Phase 5+ expansion plan
├── generate_sprites.py        # Generates animation frames from base JSON sprites
├── design_32x32.py            # 32×32 base sprite designer
├── assets/
│   ├── splash_background.png  # AI-generated title screen art
│   └── gameover_background.png # AI-generated game-over art
├── sprites_json/
│   ├── front_idle32.json      # 32×32 base sprites (JSON pixel data)
│   ├── right_idle32.json
│   ├── back_idle32.json
│   └── all_sprites.json       # All 28 states × frames (generated)
├── terrain/
│   ├── heightfield.py         # fBm noise, craters, normals, colorize, shade
│   └── terrain_renderer.py    # Pre-renders terrain surface + rock props + vignette
├── entities/
│   ├── player.py              # Movement, slope collision, sprint
│   ├── player_sprite.py       # 4-directional animation state machine
│   ├── enemy_base.py          # Enemy base class + AcidPool + AcidProjectile
│   ├── enemy_types.py         # Drone, Runner, Brute, Spitter + create_enemy factory
│   ├── enemy_mods.py          # Elite variants: Gamma, Alpha, Corrupted
│   ├── xenomorph.py           # Legacy compatibility shim
│   ├── xenomorph_sprite.py    # EnemySprite controller (all enemy types)
│   ├── sprite_factory.py      # Sprite loading (JSON → pygame Surface) + enemy sprites
│   ├── spawner.py             # Wave director with enemy type scaling
│   ├── projectiles.py         # Hitscan tracers + flamethrower fire zones
│   ├── pickups.py             # Health/ammo drops with bob animation
│   └── animation.py           # AnimationStateMachine framework
├── combat/
│   ├── weapons.py             # 3 weapons with data-driven stats
│   ├── particles.py           # Muzzle flash, blood, acid, sparks (additive blending)
│   └── floating_text.py       # Damage numbers, combo popups, pickup notifications
├── game/
│   ├── state_machine.py       # Menu → Briefing → Playing → Extraction → Victory/Gameover
│   ├── objectives.py          # 4 objective types + extraction beacon
│   ├── biomes.py              # 4 biomes with palette + hazard modifiers
│   └── audio.py               # 11 procedural SFX via numpy synthesis
└── ui/
    ├── hud.py                 # Full HUD: health, ammo, wave, objective, combo, indicators
    ├── menus.py               # Title, briefing, pause, gameover screens
    └── motion_tracker.py      # Aliens-style radar with ping sweep
```

## License

MIT
