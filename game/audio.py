"""Audio system — procedural sound effects via numpy synthesis.

Generates all SFX at startup from numpy waveforms — no external audio files.
Uses pygame.mixer for playback.

Channels:
  - 6 SFX channels (gunfire, hits, aliens, UI)
  - 1 ambient loop channel
  - 1 music channel (placeholder)
"""
import math
import numpy as np
import pygame

SAMPLE_RATE = 22050


def _to_sound(samples):
    """Convert numpy float array [-1,1] to pygame Sound."""
    samples = np.clip(samples, -1, 1)
    stereo = np.column_stack([samples, samples])
    audio = (stereo * 32767).astype(np.int16)
    return pygame.sndarray.make_sound(audio)


def _envelope(n, attack=0.01, decay=0.3, sr=SAMPLE_RATE):
    """ADSR-like envelope (attack + exponential decay)."""
    env = np.ones(n)
    a = int(attack * sr)
    d = int(decay * sr)
    if a > 0:
        env[:a] = np.linspace(0, 1, a)
    if d > 0 and a + d < n:
        env[a:a+d] = np.exp(-np.linspace(0, 5, d))
        env[a+d:] = 0
    elif a < n:
        env[a:] = np.exp(-np.linspace(0, 5, n - a))
    return env


def make_pulse_rifle():
    """Sharp metallic crack — short noise burst with high-pass character."""
    dur = 0.08
    n = int(dur * SAMPLE_RATE)
    t = np.linspace(0, dur, n)
    # Noise burst
    noise = np.random.randn(n) * 0.6
    # Tone component
    tone = np.sin(2 * np.pi * 180 * t) * 0.3
    # Combine with fast decay
    env = _envelope(n, attack=0.001, decay=0.06)
    return _to_sound((noise + tone) * env * 0.7)


def make_shotgun():
    """Heavy thump + metallic ring."""
    dur = 0.25
    n = int(dur * SAMPLE_RATE)
    t = np.linspace(0, dur, n)
    noise = np.random.randn(n) * 0.8
    low = np.sin(2 * np.pi * 80 * t) * 0.5
    ring = np.sin(2 * np.pi * 400 * t) * 0.2 * np.exp(-t * 15)
    env = _envelope(n, attack=0.002, decay=0.2)
    return _to_sound((noise + low + ring) * env * 0.8)


def make_flamethrower():
    """Sustained whoosh."""
    dur = 0.3
    n = int(dur * SAMPLE_RATE)
    t = np.linspace(0, dur, n)
    noise = np.random.randn(n) * 0.4
    rumble = np.sin(2 * np.pi * 50 * t) * 0.3
    env = np.ones(n)
    env[:int(0.05 * SAMPLE_RATE)] = np.linspace(0, 1, int(0.05 * SAMPLE_RATE))
    env[-int(0.1 * SAMPLE_RATE):] = np.linspace(1, 0, int(0.1 * SAMPLE_RATE))
    return _to_sound((noise + rumble) * env * 0.5)


def make_reload():
    """Metallic click-clack."""
    dur = 0.3
    n = int(dur * SAMPLE_RATE)
    t = np.linspace(0, dur, n)
    # Two clicks
    click1 = np.exp(-(t - 0.02) * 200) * np.sin(2 * np.pi * 2000 * t) * 0.5
    click2 = np.exp(-(t - 0.15) * 200) * np.sin(2 * np.pi * 1500 * t) * 0.5
    return _to_sound(click1 + click2)


def make_xeno_screech():
    """Descending chitter."""
    dur = 0.4
    n = int(dur * SAMPLE_RATE)
    t = np.linspace(0, dur, n)
    freq = 800 - 600 * t / dur  # descending
    wave = np.sin(2 * np.pi * freq * t) * 0.4
    # Add harmonics
    wave += np.sin(2 * np.pi * freq * 2 * t) * 0.15
    # Add noise
    wave += np.random.randn(n) * 0.1
    env = _envelope(n, attack=0.01, decay=0.35)
    return _to_sound(wave * env * 0.5)


def make_xeno_death():
    """Wet crunch + gurgle."""
    dur = 0.5
    n = int(dur * SAMPLE_RATE)
    t = np.linspace(0, dur, n)
    noise = np.random.randn(n) * 0.5
    low = np.sin(2 * np.pi * 60 * t) * 0.4 * np.exp(-t * 3)
    env = _envelope(n, attack=0.005, decay=0.45)
    return _to_sound((noise + low) * env * 0.6)


def make_hit_marker():
    """Short blip for hit confirmation."""
    dur = 0.05
    n = int(dur * SAMPLE_RATE)
    t = np.linspace(0, dur, n)
    wave = np.sin(2 * np.pi * 1200 * t) * 0.3
    env = _envelope(n, attack=0.001, decay=0.04)
    return _to_sound(wave * env)


def make_player_hurt():
    """Pain grunt."""
    dur = 0.2
    n = int(dur * SAMPLE_RATE)
    t = np.linspace(0, dur, n)
    freq = 200 - 100 * t / dur
    wave = np.sin(2 * np.pi * freq * t) * 0.5
    env = _envelope(n, attack=0.005, decay=0.18)
    return _to_sound(wave * env * 0.5)


def make_ping():
    """Motion tracker ping."""
    dur = 0.15
    n = int(dur * SAMPLE_RATE)
    t = np.linspace(0, dur, n)
    freq = 800 + 400 * np.exp(-t * 20)
    wave = np.sin(2 * np.pi * freq * t) * 0.2
    env = _envelope(n, attack=0.01, decay=0.12)
    return _to_sound(wave * env)


def make_ui_click():
    """UI button click."""
    dur = 0.05
    n = int(dur * SAMPLE_RATE)
    t = np.linspace(0, dur, n)
    wave = np.sin(2 * np.pi * 600 * t) * 0.3
    env = _envelope(n, attack=0.001, decay=0.04)
    return _to_sound(wave * env)


def make_extraction():
    """Extraction beacon activated."""
    dur = 1.0
    n = int(dur * SAMPLE_RATE)
    t = np.linspace(0, dur, n)
    wave = np.sin(2 * np.pi * 440 * t) * 0.3
    wave += np.sin(2 * np.pi * 660 * t) * 0.2
    env = np.ones(n)
    env[:int(0.1 * SAMPLE_RATE)] = np.linspace(0, 1, int(0.1 * SAMPLE_RATE))
    return _to_sound(wave * env * 0.4)


class AudioSystem:
    """Manages all game audio."""
    def __init__(self):
        self.enabled = False
        self.muted = False
        try:
            pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=2, buffer=512)
            pygame.mixer.set_num_channels(8)
            self.enabled = True
        except pygame.error:
            print("[audio] Mixer init failed — running silent")
            return

        print("[audio] Generating SFX...")
        self.sfx = {
            'pulse_rifle': make_pulse_rifle(),
            'shotgun': make_shotgun(),
            'flamethrower': make_flamethrower(),
            'reload': make_reload(),
            'xeno_screech': make_xeno_screech(),
            'xeno_death': make_xeno_death(),
            'hit_marker': make_hit_marker(),
            'player_hurt': make_player_hurt(),
            'ping': make_ping(),
            'ui_click': make_ui_click(),
            'extraction': make_extraction(),
        }
        print("[audio] Ready.")

        # Ping timer
        self.ping_timer = 0.0

    def play(self, name, volume=1.0):
        if not self.enabled or self.muted:
            return
        s = self.sfx.get(name)
        if s:
            s.set_volume(volume)
            s.play()

    def update(self, dt, enemies_near):
        """Play motion tracker ping periodically."""
        if not self.enabled or self.muted:
            return
        self.ping_timer += dt
        interval = max(0.8, 2.0 - enemies_near * 0.2)
        if self.ping_timer >= interval:
            self.ping_timer = 0.0
            self.play('ping', volume=0.15)

    def toggle_mute(self):
        self.muted = not self.muted
        return self.muted
