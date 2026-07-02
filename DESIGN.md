---
version: alpha
name: Xeno Breach
description: Hostile-colony survival shooter — industrial salvage aesthetic under corrosive alien threat.
colors:
  primary: "#0A0E12"
  secondary: "#3A4651"
  tertiary: "#C8362F"
  neutral: "#121820"
  surface: "#1C2530"
  on-primary: "#E8EDF2"
  on-secondary: "#9AA6B0"
  on-tertiary: "#FFFFFF"
  danger: "#FF4136"
  acid: "#9DFF3D"
  warning: "#FFB454"
  bio-mass: "#5B1F2E"
typography:
  h1:
    fontFamily: "IBM Plex Mono"
    fontSize: 3.5rem
    fontWeight: 700
    lineHeight: 1.05
    letterSpacing: "-0.02em"
  h2:
    fontFamily: "IBM Plex Mono"
    fontSize: 2rem
    fontWeight: 600
    lineHeight: 1.15
    letterSpacing: "-0.01em"
  h3:
    fontFamily: "IBM Plex Mono"
    fontSize: 1.25rem
    fontWeight: 500
    lineHeight: 1.3
  body-md:
    fontFamily: "IBM Plex Sans"
    fontSize: 1rem
    fontWeight: 400
    lineHeight: 1.55
  body-sm:
    fontFamily: "IBM Plex Sans"
    fontSize: 0.875rem
    fontWeight: 400
    lineHeight: 1.5
  label-caps:
    fontFamily: "IBM Plex Mono"
    fontSize: 0.6875rem
    fontWeight: 600
    letterSpacing: "0.14em"
  hud-value:
    fontFamily: "IBM Plex Mono"
    fontSize: 1.125rem
    fontWeight: 600
    lineHeight: 1.0
    letterSpacing: "0.02em"
  readout:
    fontFamily: "IBM Plex Mono"
    fontSize: 0.75rem
    fontWeight: 400
    letterSpacing: "0.06em"
rounded:
  none: 0px
  sm: 2px
  md: 4px
  lg: 8px
  full: 9999px
spacing:
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 48px
  hud: 12px
components:
  hud-panel:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-primary}"
    rounded: "{rounded.sm}"
    padding: 12px
  health-bar:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.danger}"
    rounded: "{rounded.none}"
    height: 8px
  health-bar-critical:
    backgroundColor: "{colors.danger}"
    textColor: "{colors.on-primary}"
    rounded: "{rounded.none}"
    height: 8px
  ammo-readout:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-tertiary}"
    typography: "{typography.hud-value}"
    rounded: "{rounded.sm}"
    padding: 12px
  motion-blip:
    backgroundColor: "{colors.acid}"
    textColor: "{colors.primary}"
    rounded: "{rounded.full}"
    size: 6px
  motion-blip-threat:
    backgroundColor: "{colors.danger}"
    textColor: "{colors.on-primary}"
    rounded: "{rounded.full}"
    size: 8px
  button-primary:
    backgroundColor: "{colors.tertiary}"
    textColor: "{colors.on-tertiary}"
    typography: "{typography.label-caps}"
    rounded: "{rounded.sm}"
    padding: 12px
  button-primary-hover:
    backgroundColor: "{colors.danger}"
    textColor: "{colors.on-tertiary}"
  button-ghost:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-secondary}"
    typography: "{typography.label-caps}"
    rounded: "{rounded.sm}"
    padding: 12px
  button-ghost-hover:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-primary}"
  objective-card:
    backgroundColor: "{colors.neutral}"
    textColor: "{colors.on-secondary}"
    typography: "{typography.body-sm}"
    rounded: "{rounded.md}"
    padding: 16px
  threat-banner:
    backgroundColor: "{colors.bio-mass}"
    textColor: "{colors.warning}"
    typography: "{typography.label-caps}"
    rounded: "{rounded.none}"
    padding: 8px
  threat-banner-active:
    backgroundColor: "{colors.danger}"
    textColor: "{colors.on-tertiary}"
    typography: "{typography.label-caps}"
    rounded: "{rounded.none}"
    padding: 8px
---

## Overview

Xeno Breach is the visual identity for a top-down survival shooter set in a
corroding industrial colony on a hostile rocky planet. The look is *salvage
chic*: the cold, pressurized UI of a marine deployment terminal laid over the
organic, chitinous menace of the xenomorph swarm. Every screen should feel
like a clipboard checklist a sergeant read once before the lights went out.

The dominant mood is **controlled dread**. Dark, near-black surfaces (the hull
interior) are punctuated by a single hot-red interaction driver and an
unmistakable acid-green that only ever means one thing: something alive is
close. Warning amber shows up when systems — not creatures — are failing.
Typography leans on IBM Plex Mono for HUD and headers to read as operator
hardware; Plex Sans carries body copy so prose stays legible during long
briefings.

## Colors

- **Primary ({colors.primary}):** "Hull Black" — the deep, near-blacks of
  pressurized interior plating. Base canvas for every screen.
- **Secondary ({colors.secondary}):** "Deck Plate" — cool gunmetal for
  borders, dividers, inactive control surfaces.
- **Tertiary ({colors.tertiary}):** "Adrenaline Red" — the sole driver for
  player interaction. Buttons, active fire-mode selectors, extraction beacons.
  Use sparingly; its power comes from scarcity.
- **Neutral ({colors.neutral}):** "Bulkhead" — the page surface, a touch
  lighter than primary so panels lift off the background.
- **Surface ({colors.surface}):** "Console Panel" — raised HUD tiles and
  readout housings.
- **Danger ({colors.danger}):** "Hull Breach" — critical health, lethal
  proximity, override alarms. Hotter and brighter than tertiary so it never
  reads as just another red.
- **Acid ({colors.acid}):** "Xenorph Blood" — reserved exclusively for living
  threats and corrosive feedback. The single signal that means *biological*.
  Never use it for UI chrome.
- **Warning ({colors.warning}):** "Caution Amber" — systems-level warnings:
  low oxygen, failing motion tracker, weapon overheat. Mechanical, not alive.
- **Bio-mass ({colors.bio-mass}):** "Nest Interior" — the bruised
  purple-black of alien hive architecture. Threat banners and infestation
  vignettes only.

## Typography

IBM Plex Mono carries every display and HUD element: headlines, ammo
readouts, motion-tracker labels, objective tags. Its fixed advance reads as
operator hardware and keeps numeric HUD columns aligned without extra
tabular-feature plumbing. IBM Plex Sans handles body copy and briefings where
sustained reading comfort matters.

Weight and size carry hierarchy, not family. Display sizes run tight
letter-spacing; the `label-caps` and `readout` styles open up tracking to
evoke stencil-cut control labels. No italics anywhere.

## Layout

Spacing follows a 4px baseline. `hud` (12px) is the intra-panel gap inside HUD
tiles; `md` (16px) separates controls; `lg` (24px) is the breathing room
between HUD clusters and the playfield edge. HUD tiles pin to screen margins
with `lg` insets so the playfield never touches the bezel.

## Shapes

Corners stay industrial and clipped. `none` for bars and full-bleed banners;
`sm` (2px) for HUD panels and buttons — barely softened, never soft. `md`
for grouped content cards. `full` is reserved for motion-tracker blips and
status dots where a circle is the signal, not decoration.

## Components

- `hud-panel` is the housing for every fixed-screen overlay: health, ammo,
  minimap, objectives. Surface color lifts it off the bulkhead background.
- `health-bar` drains to `health-bar-critical` below 25% — the fill swaps to
  `danger`, the panel flashes. Critical state is a sibling component, not a
  style toggle.
- `ammo-readout` is right-aligned mono digits on hull black so reload counts
  read at a glance against the playfield.
- `motion-blip` is a small acid-green dot for ambient contacts. It promotes
  to `motion-blip-threat` (larger, danger red) when a contact is classified
  hostile — size and color shift together.
- `button-primary` is the only high-emphasis action per screen
  (deploy, extract, override). `button-ghost` handles secondary actions
  without competing for the eye.
- `threat-banner` sits full-bleed above the HUD when a nest is near; it
  escalates to `threat-banner-active` (bright danger fill) during a breach
  event. Both use `rounded: none` to read as welded-on warning plates.
- `objective-card` carries mission text on a bulkhead surface so briefing
  copy stays calm against the hot interaction palette.

## Do's and Don'ts

- **Do** reserve `{colors.acid}` for biological threats only. If a player
  learns green means *alive*, the motion tracker teaches itself.
- **Do** keep `{colors.tertiary}` to one primary action per screen — its
  signal dies the moment two red buttons compete.
- **Do** use token references (`{colors.danger}`) in component definitions,
  never literal hex, so palette changes propagate everywhere.
- **Don't** introduce off-palette reds or greens. Extend the color tokens
  first; the threat vocabulary depends on strict hue boundaries.
- **Don't** nest component variants. `health-bar-critical` is a sibling of
  `health-bar`, not a child key.
- **Don't** round corners beyond `md`. This is salvage hardware, not a
  consumer app — soft radii break the industrial read.
- **Don't** use italics. Operators don't italicize.
