"""Characterization + drift-guard tests for MetaState save/load.

These tests isolate the save directory by monkeypatching os.path.expanduser
to a pytest tmp_path, so the real ~/.xeno_breach/save.json is NEVER touched.
Written BEFORE the META_SCHEMA refactor to lock current behavior.
"""
import json
import os

import game.meta_progression as mp

# Fields MetaState is expected to persist (excludes save_version meta key).
FIELDS = ['salvage', 'upgrades', 'total_kills', 'total_runs',
          'total_extractions', 'best_wave', 'unlocked_weapons', 'loadout']


def _fresh(tmp_path, monkeypatch):
    """Build a MetaState whose save dir is isolated under tmp_path."""
    monkeypatch.setattr(os.path, 'expanduser', lambda p: str(tmp_path))
    return mp.MetaState()


def _save_file(tmp_path):
    return tmp_path / '.xeno_breach' / 'save.json'


def test_save_contains_every_persisted_field(tmp_path, monkeypatch):
    m = _fresh(tmp_path, monkeypatch)
    m.save()
    with open(_save_file(tmp_path)) as f:
        data = json.load(f)
    for key in FIELDS:
        assert key in data, f"{key} missing from save() output"
    assert data['save_version'] == mp.SAVE_VERSION


def test_round_trip_preserves_state(tmp_path, monkeypatch):
    m = _fresh(tmp_path, monkeypatch)
    m.salvage = 123
    m.total_kills = 9
    m.upgrades['health'] = 2
    m.unlocked_weapons = ['pulse_rifle', 'shotgun', 'flamethrower', 'smg']
    m.loadout = ['smg', 'shotgun', 'flamethrower']
    m.save()

    m2 = _fresh(tmp_path, monkeypatch)
    assert m2.salvage == 123
    assert m2.total_kills == 9
    assert m2.get_tier('health') == 2
    assert 'smg' in m2.unlocked_weapons
    assert m2.loadout == ['smg', 'shotgun', 'flamethrower']


def test_defaults_when_no_save(tmp_path, monkeypatch):
    m = _fresh(tmp_path, monkeypatch)
    assert m.salvage == 0
    assert m.upgrades == {k: 0 for k in mp.UPGRADES}
    assert m.unlocked_weapons == ['pulse_rifle', 'shotgun', 'flamethrower']
    assert m.loadout == ['pulse_rifle', 'shotgun', 'flamethrower']


def test_v1_save_migrates(tmp_path, monkeypatch):
    d = tmp_path / '.xeno_breach'
    d.mkdir()
    # v1 = no save_version key at all
    (d / 'save.json').write_text(json.dumps({'salvage': 5, 'total_kills': 3}))
    m = _fresh(tmp_path, monkeypatch)
    assert m.salvage == 5
    assert m.total_kills == 3
    # v3 defaults injected by migration
    assert m.unlocked_weapons == ['pulse_rifle', 'shotgun', 'flamethrower']
    assert m.loadout == ['pulse_rifle', 'shotgun', 'flamethrower']


def test_v2_save_migrates(tmp_path, monkeypatch):
    d = tmp_path / '.xeno_breach'
    d.mkdir()
    (d / 'save.json').write_text(json.dumps({
        'save_version': 2, 'salvage': 50, 'upgrades': {'health': 1},
    }))
    m = _fresh(tmp_path, monkeypatch)
    assert m.salvage == 50
    assert m.get_tier('health') == 1
    assert m.unlocked_weapons == ['pulse_rifle', 'shotgun', 'flamethrower']


def test_schema_and_save_agree(tmp_path, monkeypatch):
    """Drift guard: every META_SCHEMA field must land in save() output and
    vice-versa. Fails if a field is added to the schema but forgotten in
    save(), or an orphan key is written that the schema doesn't declare."""
    m = _fresh(tmp_path, monkeypatch)
    m.save()
    with open(_save_file(tmp_path)) as f:
        data = json.load(f)
    schema_fields = {name for name, _ in mp.META_SCHEMA}
    saved_fields = set(data) - {'save_version'}
    assert schema_fields == saved_fields
