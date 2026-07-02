# Xeno Breach

A top-down survival shooter where you fight waves of alien creatures on procedurally generated rocky planets. Built with Python and pygame-ce.

## Install

```bash
pip install pygame-ce numpy noise pillow
```

## Play

```bash
python main.py
```

## Controls

| Key | Action |
|-----|--------|
| WASD / Arrows | Move |
| Mouse | Aim |
| Left Click | Fire |
| 1 / 2 / 3 | Switch weapons |
| R | Reload |
| Shift | Sprint |
| ESC | Pause |
| M | Mute |
| F1 | Debug overlay |

## What's In The Game

**Combat** — Three weapons (pulse rifle, shotgun, flamethrower) with distinct feel. Hit markers, damage numbers, screen shake, kill combos.

**Enemies** — Four types that get harder as waves progress:
- **Drone** — Standard alien, patrols then lunges
- **Runner** — Fast and fragile, always chasing
- **Brute** — Slow tank, telegraphed charge attack, enrages at half HP
- **Spitter** — Keeps distance, fires acid projectiles

**Elites** — Random glowing variants with bonus HP and better salvage drops.

**Meta-Progression** — Earn salvage from kills and extractions. Spend it in the armory on 8 permanent upgrades (health, regen, ammo, fire rate, acid resistance, scanner range, speed, salvage multiplier). Saves automatically between sessions.

**Procedural Terrain** — Every run generates a different planet with fBm noise heightfields, impact craters, rock props, and one of four biomes (barren, polar, cratered, highland).

**Game Flow** — Menu → Armory (optional) → Briefing → Survive waves + complete objective → Extract → Spend salvage → Repeat.

**Atmosphere** — Procedural sound effects (no audio files), AI-generated splash art, motion tracker radar, low-health vignette, off-screen enemy indicators.

## Project Structure

```
main.py              # Game loop and state machine
config.py            # All tuning constants and colors
generate_sprites.py  # Builds animation frames from base sprite JSON
terrain/             # Heightfield generation, rendering, rock props
entities/            # Player, enemies, pickups, sprites, wave director
combat/              # Weapons, particles, floating text
game/                # State machine, objectives, biomes, audio, meta-progression
ui/                  # HUD, menus, motion tracker
sprites_json/        # 32x32 pixel art sprites as JSON coordinate data
assets/              # Splash and game-over background images
```

## License

MIT
