"""Legacy compatibility shim — re-exports from enemy_base and enemy_types.

The original monolithic Xenomorph class has been split into:
  - Enemy (base class)         → entities/enemy_base.py
  - Drone, Runner, Brute, Spitter → entities/enemy_types.py
  - AcidPool, AcidProjectile   → entities/enemy_base.py

This file keeps old imports working:
    from entities.xenomorph import Xenomorph, AcidPool
"""
from entities.enemy_base import AcidPool, AcidProjectile, Enemy, EnemyState
from entities.enemy_types import Drone as Xenomorph
from entities.enemy_types import Drone, Runner, Brute, Spitter, create_enemy

__all__ = ['Xenomorph', 'AcidPool', 'AcidProjectile', 'Enemy',
           'Drone', 'Runner', 'Brute', 'Spitter', 'create_enemy']
