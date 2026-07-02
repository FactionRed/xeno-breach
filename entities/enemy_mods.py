"""Elite enemy modifiers — overlay system applied to any enemy type.

5% chance per spawn to roll an elite variant. Modifiers change stats,
visual tint, and add special behaviors without changing the AI.
"""
import random


class EliteMod:
    """Base elite modifier."""
    name = 'none'
    tint = (255, 255, 255)  # color multiplier
    glow_color = (0, 0, 0)

    def apply(self, enemy):
        """Modify enemy stats on spawn."""
        pass

    def on_update(self, enemy, dt):
        """Per-frame behavior (e.g. acid trail)."""
        pass


class GammaMod(EliteMod):
    """Gamma — glowing green, +50% HP, 3× salvage value."""
    name = 'gamma'
    tint = (0.7, 1.0, 0.7)
    glow_color = (0, 255, 100)

    def apply(self, enemy):
        enemy.hp = int(enemy.hp * 1.5)
        enemy.max_hp = enemy.hp
        enemy.salvage_value = getattr(enemy, 'salvage_value', 1) * 3
        enemy.elite = 'gamma'


class AlphaMod(EliteMod):
    """Alpha — glowing red, +100% HP, enraged (always fast)."""
    name = 'alpha'
    tint = (1.0, 0.6, 0.6)
    glow_color = (255, 50, 50)

    def apply(self, enemy):
        enemy.hp = int(enemy.hp * 2.0)
        enemy.max_hp = enemy.hp
        enemy.speed *= 1.3
        enemy.attack_damage = int(enemy.attack_damage * 1.2)
        enemy.salvage_value = getattr(enemy, 'salvage_value', 1) * 3
        enemy.elite = 'alpha'


class CorruptedMod(EliteMod):
    """Corrupted — glowing purple, leaves acid trail while moving."""
    name = 'corrupted'
    tint = (0.8, 0.6, 1.0)
    glow_color = (180, 80, 255)

    def apply(self, enemy):
        enemy.hp = int(enemy.hp * 1.3)
        enemy.max_hp = enemy.hp
        enemy.salvage_value = getattr(enemy, 'salvage_value', 1) * 3
        enemy.elite = 'corrupted'
        enemy._trail_timer = 0.0

    def on_update(self, enemy, dt):
        """Leave acid trail every 0.5s while moving."""
        if enemy.dead or enemy.state == 'death':
            return
        enemy._trail_timer = getattr(enemy, '_trail_timer', 0) + dt
        if enemy._trail_timer >= 0.5:
            enemy._trail_timer = 0.0
            if hasattr(enemy, 'on_trail'):
                enemy.on_trail(enemy.x, enemy.y)


ELITE_MODS = [GammaMod, AlphaMod, CorruptedMod]


def maybe_roll_elite(enemy, chance=0.05):
    """5% chance to apply a random elite mod to an enemy."""
    if random.random() < chance:
        mod_cls = random.choice(ELITE_MODS)
        mod = mod_cls()
        mod.apply(enemy)
        enemy.elite_mod = mod
        return mod
    enemy.elite_mod = None
    enemy.elite = None
    enemy.salvage_value = getattr(enemy, 'salvage_value', 1)
    return None
