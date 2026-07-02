"""Meta-progression system — salvage currency, upgrade tree, save/load.

Salvage is earned during runs (kills, objectives, extraction bonus) and
spent in the armory between runs on permanent upgrades.

Save file: ~/.xeno_breach/save.json
"""
import json
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional


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
        self._load()

    def _save_path(self):
        home = os.path.expanduser('~')
        d = os.path.join(home, '.xeno_breach')
        os.makedirs(d, exist_ok=True)
        return os.path.join(d, 'save.json')

    def _load(self):
        path = self._save_path()
        if not os.path.exists(path):
            return
        try:
            with open(path) as f:
                data = json.load(f)
            self.salvage = data.get('salvage', 0)
            self.upgrades = {k: data.get('upgrades', {}).get(k, 0) for k in UPGRADES}
            self.total_kills = data.get('total_kills', 0)
            self.total_runs = data.get('total_runs', 0)
            self.total_extractions = data.get('total_extractions', 0)
            self.best_wave = data.get('best_wave', 0)
        except (json.JSONDecodeError, IOError):
            pass  # Corrupted save — start fresh

    def save(self):
        data = {
            'salvage': self.salvage,
            'upgrades': self.upgrades,
            'total_kills': self.total_kills,
            'total_runs': self.total_runs,
            'total_extractions': self.total_extractions,
            'best_wave': self.best_wave,
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
