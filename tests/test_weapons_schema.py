"""Golden snapshot + construction tests for the weapon schema.

The EXPECTED table below is copied VERBATIM from the original flat
WEAPON_STATS literal. It is the frozen source of truth: the base+override
refactor must resolve to exactly these values. Do NOT edit EXPECTED to make a
failing test pass — a diff here means an override is wrong.
"""
import math

from combat.weapons import Weapon, WeaponSystem, WEAPON_ORDER, WEAPON_STATS

EXPECTED = {
    'pulse_rifle': {
        'damage': 22, 'fire_rate': 100, 'mag_size': 30,
        'range': 800, 'spread': 2.0, 'pellets': 1,
        'tracer_color': [255, 180, 84],
        'muzzle_flash': True,
        'reload_time': 1.5,
    },
    'shotgun': {
        'damage': 14, 'fire_rate': 550, 'mag_size': 8,
        'range': 450, 'spread': 11, 'pellets': 6,
        'tracer_color': [255, 65, 54],
        'muzzle_flash': True,
        'reload_time': 2.0,
    },
    'flamethrower': {
        'damage': 10, 'fire_rate': 70, 'mag_size': 100,
        'range': 320, 'spread': 22, 'pellets': 1,
        'tracer_color': [255, 120, 40],
        'muzzle_flash': False,
        'area_denial': True,
        'reload_time': 2.5,
    },
    'smg': {
        'damage': 8, 'fire_rate': 50, 'mag_size': 50,
        'range': 500, 'spread': 4.0, 'pellets': 1,
        'tracer_color': [120, 255, 120],
        'muzzle_flash': True,
        'reload_time': 1.8,
    },
    'railgun': {
        'damage': 80, 'fire_rate': 800, 'mag_size': 5,
        'range': 1200, 'spread': 0.5, 'pellets': 1,
        'tracer_color': [0, 217, 255],
        'muzzle_flash': True,
        'pierce': True,
        'reload_time': 3.0,
    },
}


def test_weapon_stats_match_golden():
    assert WEAPON_STATS == EXPECTED


def test_every_weapon_constructs():
    for name in WEAPON_ORDER:
        w = Weapon(name, WEAPON_STATS[name])
        assert w.tracer_color == tuple(WEAPON_STATS[name]['tracer_color'])
        assert w.spread == math.radians(WEAPON_STATS[name]['spread'])


def test_weapon_system_default_loadout_builds():
    ws = WeaponSystem()
    assert len(ws.weapons) == 3
