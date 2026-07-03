"""Meta-progression system — salvage currency, upgrade tree, save/load.

Salvage is earned during runs (kills, objectives, extraction bonus) and
spent in the armory between runs on permanent upgrades.

Save file: ~/.xeno_breach/save.json
"""
import json
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional

# Save file version — increment when save format changes.
# Migration functions in _migrate() handle upgrading old saves.
SAVE_VERSION = 3


# ============ UPGRADE DEFINITIONS ============

@dataclass
class UpgradeDef:
    key: str
    name: str
    description: str
    tiers: List[dict]  # [{cost, effect_value, effect_desc}, ...]

    @property
    def max_tier(self):
        return len(self.tiers)


UPGRADES: Dict[str, UpgradeDef] = {
    'health': UpgradeDef(
        key='health', name='Reinforced Plating',
        description='Increase maximum integrity',
        tiers=[
            {'cost': 10, 'value': 20, 'desc': '+20 HP'},
            {'cost': 25, 'value': 40, 'desc': '+40 HP'},
            {'cost': 50, 'value': 60, 'desc': '+60 HP'},
        ]
    ),
    'regen': UpgradeDef(
        key='regen', name='Auto-Injector',
        description='Slowly regenerate integrity over time',
        tiers=[
            {'cost': 15, 'value': 1.0, 'desc': '+1 HP/s regen'},
            {'cost': 35, 'value': 2.0, 'desc': '+2 HP/s regen'},
            {'cost': 70, 'value': 3.0, 'desc': '+3 HP/s + regen on kill'},
        ]
    ),
    'ammo': UpgradeDef(
        key='ammo', name='Extended Magazines',
        description='Increase magazine capacity for all weapons',
        tiers=[
            {'cost': 10, 'value': 0.30, 'desc': '+30% ammo'},
            {'cost': 25, 'value': 0.60, 'desc': '+60% ammo'},
            {'cost': 50, 'value': 1.00, 'desc': '+100% ammo'},
        ]
    ),
    'fire_rate': UpgradeDef(
        key='fire_rate', name='Rapid Fire Mod',
        description='Reduce time between shots',
        tiers=[
            {'cost': 15, 'value': 0.15, 'desc': '+15% fire rate'},
            {'cost': 35, 'value': 0.30, 'desc': '+30% fire rate'},
            {'cost': 70, 'value': 0.50, 'desc': '+50% fire rate'},
        ]
    ),
    'acid_resist': UpgradeDef(
        key='acid_resist', name='Acid Resistance',
        description='Reduce damage from acid pools and spit',
        tiers=[
            {'cost': 15, 'value': 0.30, 'desc': '-30% acid dmg'},
            {'cost': 35, 'value': 0.60, 'desc': '-60% acid dmg'},
            {'cost': 70, 'value': 1.00, 'desc': 'Acid immunity'},
        ]
    ),
    'scanner': UpgradeDef(
        key='scanner', name='Motion Scanner Boost',
        description='Extend motion tracker detection range',
        tiers=[
            {'cost': 10, 'value': 0.25, 'desc': '+25% range'},
            {'cost': 25, 'value': 0.50, 'desc': '+50% range'},
            {'cost': 50, 'value': 1.00, 'desc': '+100% range'},
        ]
    ),
    'speed': UpgradeDef(
        key='speed', name='Combat Stims',
        description='Increase movement speed',
        tiers=[
            {'cost': 15, 'value': 0.10, 'desc': '+10% speed'},
            {'cost': 35, 'value': 0.20, 'desc': '+20% speed'},
            {'cost': 70, 'value': 0.30, 'desc': '+30% speed'},
        ]
    ),
    'scavenger': UpgradeDef(
        key='scavenger', name='Scavenger Protocol',
        description='Earn more salvage per kill',
        tiers=[
            {'cost': 10, 'value': 1, 'desc': '+1 salvage/kill'},
            {'cost': 25, 'value': 2, 'desc': '+2 salvage/kill'},
            {'cost': 50, 'value': 3, 'desc': '+3 salvage/kill'},
        ]
    ),
}

UPGRADE_ORDER = ['health', 'regen', 'ammo', 'fire_rate',
                 'acid_resist', 'scanner', 'speed', 'scavenger']


# ============ META STATE ============

class MetaState:
    """Persistent player progression state across runs."""

    def __init__(self):
        self.salvage = 0
        self.upgrades: Dict[str, int] = {k: 0 for k in UPGRADES}
        self.total_kills = 0
        self.total_runs = 0
        self.total_extractions = 0
        self.best_wave = 0
        self.unlocked_weapons = ['pulse_rifle', 'shotgun', 'flamethrower']
        self.loadout = ['pulse_rifle', 'shotgun', 'flamethrower']
        self.save_version = SAVE_VERSION
        self._load()

    def _save_path(self):
        home = os.path.expanduser('~')
        d = os.path.join(home, '.xeno_breach')
        os.makedirs(d, exist_ok=True)
        return os.path.join(d, 'save.json')

    def _backup_path(self):
        return self._save_path() + '.bak'

    def _load(self):
        path = self._save_path()
        if not os.path.exists(path):
            return
        try:
            with open(path) as f:
                data = json.load(f)
        except (json.JSONDecodeError, IOError):
            # Try backup
            if os.path.exists(self._backup_path()):
                try:
                    with open(self._backup_path()) as f:
                        data = json.load(f)
                    print("[meta] Save corrupted — restored from backup")
                except (json.JSONDecodeError, IOError):
                    pass  # Both corrupted — start fresh
                    return
            else:
                return

        # Backup before loading (in case future load corrupts something)
        try:
            import shutil
            shutil.copy2(path, self._backup_path())
        except IOError:
            pass

        # Version detection + migration
        version = data.get('save_version', 1)
        data = self._migrate(data, version)

        # Load fields (all use .get with defaults for forward compat)
        self.salvage = data.get('salvage', 0)
        self.upgrades = {k: data.get('upgrades', {}).get(k, 0) for k in UPGRADES}
        self.total_kills = data.get('total_kills', 0)
        self.total_runs = data.get('total_runs', 0)
        self.total_extractions = data.get('total_extractions', 0)
        self.best_wave = data.get('best_wave', 0)
        self.unlocked_weapons = data.get('unlocked_weapons', ['pulse_rifle', 'shotgun', 'flamethrower'])
        self.loadout = data.get('loadout', ['pulse_rifle', 'shotgun', 'flamethrower'])

    def _migrate(self, data, version):
        """Run migrations to bring save data up to current version."""
        # v1 → v2: add save_version field
        if version < 2:
            print("[meta] Migrating save from v1 → v2")
            data['save_version'] = 2

        # v2 → v3: add unlocked_weapons and loadout (default = 3 starter weapons)
        if version < 3:
            print("[meta] Migrating save from v2 → v3")
            if 'unlocked_weapons' not in data:
                data['unlocked_weapons'] = ['pulse_rifle', 'shotgun', 'flamethrower']
            if 'loadout' not in data:
                data['loadout'] = ['pulse_rifle', 'shotgun', 'flamethrower']
            data['save_version'] = 3

        # Future migrations go here:
        # if version < 3:
        #     # Example: rename 'health' to 'armor'
        #     ups = data.get('upgrades', {})
        #     if 'health' in ups and 'armor' not in ups:
        #         ups['armor'] = ups.pop('health')
        #     data['upgrades'] = ups
        #     data['save_version'] = 3

        data['save_version'] = SAVE_VERSION
        return data

    def save(self):
        data = {
            'save_version': SAVE_VERSION,
            'salvage': self.salvage,
            'upgrades': self.upgrades,
            'total_kills': self.total_kills,
            'total_runs': self.total_runs,
            'total_extractions': self.total_extractions,
            'best_wave': self.best_wave,
            'unlocked_weapons': self.unlocked_weapons,
            'loadout': self.loadout,
        }
        with open(self._save_path(), 'w') as f:
            json.dump(data, f, indent=2)

    # ============ UPGRADE LOGIC ============

    def get_tier(self, key):
        return self.upgrades.get(key, 0)

    def get_next_tier_cost(self, key):
        tier = self.get_tier(key)
        upgrade = UPGRADES.get(key)
        if not upgrade or tier >= upgrade.max_tier:
            return None
        return upgrade.tiers[tier]['cost']

    def can_purchase(self, key):
        cost = self.get_next_tier_cost(key)
        return cost is not None and self.salvage >= cost

    def purchase(self, key):
        if not self.can_purchase(key):
            return False
        cost = self.get_next_tier_cost(key)
        self.salvage -= cost
        self.upgrades[key] += 1
        self.save()
        return True

    def is_maxed(self, key):
        upgrade = UPGRADES.get(key)
        if not upgrade:
            return True
        return self.get_tier(key) >= upgrade.max_tier

    # ============ UPGRADE VALUE GETTERS ============

    def get_value(self, key):
        """Get the cumulative effect value for an upgrade."""
        tier = self.get_tier(key)
        if tier == 0:
            return 0
        upgrade = UPGRADES[key]
        return upgrade.tiers[tier - 1]['value']

    @property
    def bonus_health(self):
        return int(self.get_value('health'))

    @property
    def regen_rate(self):
        return self.get_value('regen')

    @property
    def ammo_mult(self):
        return 1.0 + self.get_value('ammo')

    @property
    def fire_rate_mult(self):
        return 1.0 + self.get_value('fire_rate')

    @property
    def acid_resist(self):
        return self.get_value('acid_resist')

    @property
    def scanner_range_mult(self):
        return 1.0 + self.get_value('scanner')

    @property
    def speed_mult(self):
        return 1.0 + self.get_value('speed')

    @property
    def salvage_per_kill(self):
        return 1 + self.get_value('scavenger')

    # ============ RUN TRACKING ============

    def add_salvage(self, amount):
        self.salvage += amount

    def record_run_end(self, kills, waves_survived, extracted):
        self.total_runs += 1
        self.total_kills += kills
        self.best_wave = max(self.best_wave, waves_survived)
        if extracted:
            self.total_extractions += 1
        self.save()

    # ============ WEAPON UNLOCKS ============

    def is_weapon_unlocked(self, name):
        return name in self.unlocked_weapons

    def get_weapon_unlock_cost(self, name):
        from combat.weapons import WEAPON_UNLOCK_COST
        return WEAPON_UNLOCK_COST.get(name)

    def can_unlock_weapon(self, name):
        if self.is_weapon_unlocked(name):
            return False
        cost = self.get_weapon_unlock_cost(name)
        return cost is not None and self.salvage >= cost

    def unlock_weapon(self, name):
        if not self.can_unlock_weapon(name):
            return False
        cost = self.get_weapon_unlock_cost(name)
        self.salvage -= cost
        self.unlocked_weapons.append(name)
        self.save()
        return True

    # ============ LOADOUT ============

    def set_loadout(self, weapons):
        """Set the 3-weapon loadout for the next run."""
        # Validate: must be 3 weapons, all unlocked
        if len(weapons) != 3:
            return False
        for w in weapons:
            if not self.is_weapon_unlocked(w):
                return False
        self.loadout = list(weapons)
        self.save()
        return True

    def get_loadout(self):
        """Get the current loadout (list of 3 weapon names)."""
        # Ensure loadout only contains unlocked weapons
        valid = [w for w in self.loadout if self.is_weapon_unlocked(w)]
        while len(valid) < 3:
            for w in ['pulse_rifle', 'shotgun', 'flamethrower']:
                if w not in valid:
                    valid.append(w)
                    break
        return valid[:3]
