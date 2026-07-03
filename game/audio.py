"""Audio system — procedural sound effects via numpy synthesis.

Generates all SFX at startup from numpy waveforms — no external audio files.
Uses pygame.mixer for playback.

Channels:
  - 8 SFX channels (gunfire, hits, aliens, UI, movement)
  - 1 ambient loop channel
"""
import math
import numpy as np
import pygame

SAMPLE_RATE = 44100


# ============ SYNTHESIS HELPERS ============

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


def _noise_burst(n, sr=SAMPLE_RATE, filter_type='white'):
    """Generate filtered noise."""
    noise = np.random.randn(n)
    if filter_type == 'white':
        return noise
    elif filter_type == 'pink':
        # Simple pink noise approximation
        pink = np.cumsum(noise)
        pink = pink / np.max(np.abs(pink)) if np.max(np.abs(pink)) > 0 else pink
        return pink
    return noise


def _saw(freq, t):
    """Sawtooth wave."""
    return 2 * (t * freq - np.floor(0.5 + t * freq))


def _square(freq, t):
    """Square wave."""
    return np.sign(np.sin(2 * np.pi * freq * t))


def _distort(x, amount=0.5):
    """Soft distortion."""
    return np.tanh(x * (1 + amount * 4))


# ============ WEAPON SOUNDS ============

def make_pulse_rifle():
    """Layered: sharp crack + bass punch + mechanical clack."""
    dur = 0.12
    n = int(dur * SAMPLE_RATE)
    t = np.linspace(0, dur, n)

    # Layer 1: Sharp high-frequency crack (noise + high tone)
    crack_noise = np.random.randn(n) * 0.5
    crack_tone = np.sin(2 * np.pi * 2200 * t) * 0.2
    crack_env = _envelope(n, attack=0.0005, decay=0.025)
    crack = (crack_noise + crack_tone) * crack_env * 0.6

    # Layer 2: Bass punch (low sine with fast decay)
    bass = np.sin(2 * np.pi * 120 * t) * 0.5
    bass += np.sin(2 * np.pi * 80 * t) * 0.3
    bass_env = _envelope(n, attack=0.001, decay=0.04)
    bass = bass * bass_env * 0.5

    # Layer 3: Mechanical clack (mid-frequency click)
    clack_t = t - 0.005
    clack = np.exp(-clack_t * 300) * np.sin(2 * np.pi * 800 * t) * 0.2
    clack[clack_t < 0] = 0

    return _to_sound(crack + bass + clack)


def make_shotgun():
    """Deep boom + pump ring — recognizable shotgun character."""
    dur = 0.35
    n = int(dur * SAMPLE_RATE)
    t = np.linspace(0, dur, n)

    # Layer 1: Deep boom (low-frequency body)
    boom = np.sin(2 * np.pi * 70 * t) * 0.8
    boom += np.sin(2 * np.pi * 45 * t) * 0.5
    boom_env = _envelope(n, attack=0.003, decay=0.12)
    boom = boom * boom_env

    # Layer 2: Sharp crack (noise burst at start for the "bang")
    crack = np.random.randn(n) * 0.3
    crack_env = _envelope(n, attack=0.001, decay=0.03)
    crack = crack * crack_env

    # Layer 3: Metallic ring (high frequency, slow decay)
    ring = np.sin(2 * np.pi * 2800 * t) * 0.08 * np.exp(-t * 20)
    ring += np.sin(2 * np.pi * 4200 * t) * 0.04 * np.exp(-t * 25)

    return _to_sound((boom + crack + ring) * 0.45)


def make_flamethrower():
    """Layered: ignition burst + sustained whoosh + crackle."""
    dur = 0.4
    n = int(dur * SAMPLE_RATE)
    t = np.linspace(0, dur, n)

    # Layer 1: Ignition burst (short percussive start)
    ign_noise = np.random.randn(n) * 0.6
    ign_env = _envelope(n, attack=0.001, decay=0.03)
    ign = ign_noise * ign_env * 0.5

    # Layer 2: Sustained whoosh (filtered noise with low rumble)
    whoosh_noise = np.random.randn(n) * 0.3
    whoosh_rumble = np.sin(2 * np.pi * 45 * t) * 0.25
    whoosh_env = np.ones(n)
    whoosh_env[:int(0.05 * SAMPLE_RATE)] = np.linspace(0, 1, int(0.05 * SAMPLE_RATE))
    whoosh_env[-int(0.08 * SAMPLE_RATE):] = np.linspace(1, 0, int(0.08 * SAMPLE_RATE))
    whoosh = (whoosh_noise + whoosh_rumble) * whoosh_env * 0.4

    # Layer 3: Crackle (random pops)
    crackle = np.zeros(n)
    for _ in range(8):
        pop_pos = np.random.randint(0, n)
        pop_len = 20
        if pop_pos + pop_len < n:
            crackle[pop_pos:pop_pos+pop_len] += np.random.randn(pop_len) * 0.3 * np.exp(-np.linspace(0, 10, pop_len))

    return _to_sound(ign + whoosh + crackle)


def make_reload():
    """Two metallic clicks — recognizable mag swap."""
    dur = 0.5
    n = int(dur * SAMPLE_RATE)
    t = np.linspace(0, dur, n)

    # Click 1: mag out (short metallic tick at 0.08s)
    c1_t = t - 0.08
    c1 = np.exp(-c1_t * 400) * np.sin(2 * np.pi * 900 * t) * 0.15
    c1[c1_t < 0] = 0

    # Click 2: mag in + charge (heavier clack at 0.25s)
    c2_t = t - 0.25
    c2 = np.exp(-c2_t * 300) * np.sin(2 * np.pi * 600 * t) * 0.2
    c2[c2_t < 0] = 0
    c2 += np.exp(-c2_t * 250) * np.sin(2 * np.pi * 400 * t) * 0.1

    return _to_sound((c1 + c2) * 0.5)


# ============ ALIEN SOUNDS ============

def make_xeno_screech():
    """Descending chitter with detuned harmonics + formant shift."""
    dur = 0.5
    n = int(dur * SAMPLE_RATE)
    t = np.linspace(0, dur, n)

    # Base frequency with detune
    freq1 = 900 - 700 * t / dur
    freq2 = freq1 * 1.01  # slight detune

    wave = np.sin(2 * np.pi * freq1 * t) * 0.3
    wave += np.sin(2 * np.pi * freq2 * t) * 0.2
    # Detuned harmonics
    wave += np.sin(2 * np.pi * freq1 * 2.1 * t) * 0.1
    wave += np.sin(2 * np.pi * freq1 * 3.3 * t) * 0.05
    # Formant shift (vowel-like quality)
    formant = np.sin(2 * np.pi * 1500 * t) * 0.08 * np.exp(-t * 2)
    wave += formant
    # Noise component
    wave += np.random.randn(n) * 0.08

    env = _envelope(n, attack=0.01, decay=0.45)
    return _to_sound(wave * env * 0.45)


def make_xeno_death():
    """Wet crunch + gurgle + acid hiss."""
    dur = 0.6
    n = int(dur * SAMPLE_RATE)
    t = np.linspace(0, dur, n)

    # Wet crunch (low noise burst with fast decay)
    crunch_noise = np.random.randn(n) * 0.5
    crunch_low = np.sin(2 * np.pi * 50 * t) * 0.4
    crunch_env = _envelope(n, attack=0.005, decay=0.1)
    crunch = (crunch_noise + crunch_low) * crunch_env * 0.5

    # Gurgle (low-frequency modulation of noise)
    gurgle_freq = 30 + 20 * np.sin(2 * np.pi * 5 * t)
    gurgle = np.sin(2 * np.pi * gurgle_freq * t) * 0.2
    gurgle_env = _envelope(n, attack=0.05, decay=0.4)
    gurgle = gurgle * gurgle_env * 0.3

    # Acid hiss (high-frequency noise with slow decay)
    hiss_noise = np.random.randn(n) * 0.2
    hiss_env = _envelope(n, attack=0.1, decay=0.5)
    hiss = hiss_noise * hiss_env * 0.15

    return _to_sound(crunch + gurgle + hiss)


# ============ PLAYER SOUNDS ============

def make_player_hurt():
    """Pain grunt with distortion + breath out."""
    dur = 0.3
    n = int(dur * SAMPLE_RATE)
    t = np.linspace(0, dur, n)

    # Grit layer (distorted low tone)
    freq = 180 - 80 * t / dur
    grit = _distort(np.sin(2 * np.pi * freq * t), 0.7) * 0.4
    grit_env = _envelope(n, attack=0.005, decay=0.2)
    grit = grit * grit_env

    # Breath out (noise burst)
    breath = np.random.randn(n) * 0.15
    breath_env = _envelope(n, attack=0.08, decay=0.15)
    breath = breath * breath_env * 0.2

    return _to_sound(grit + breath)


def make_footstep():
    """Soft crunch on rocky terrain."""
    dur = 0.08
    n = int(dur * SAMPLE_RATE)
    t = np.linspace(0, dur, n)
    noise = np.random.randn(n) * 0.2
    low = np.sin(2 * np.pi * 100 * t) * 0.1
    env = _envelope(n, attack=0.002, decay=0.06)
    return _to_sound((noise + low) * env * 0.25)


# ============ UI / SYSTEM SOUNDS ============

def make_hit_marker():
    """Sharp high-pitched confirmation blip."""
    dur = 0.06
    n = int(dur * SAMPLE_RATE)
    t = np.linspace(0, dur, n)
    wave = np.sin(2 * np.pi * 1400 * t) * 0.25
    wave += np.sin(2 * np.pi * 2100 * t) * 0.1
    env = _envelope(n, attack=0.001, decay=0.05)
    return _to_sound(wave * env)


def make_ping():
    """Motion tracker ping — distinctive descending tone."""
    dur = 0.15
    n = int(dur * SAMPLE_RATE)
    t = np.linspace(0, dur, n)
    freq = 1000 + 500 * np.exp(-t * 25)
    wave = np.sin(2 * np.pi * freq * t) * 0.15
    env = _envelope(n, attack=0.01, decay=0.12)
    return _to_sound(wave * env)


def make_ui_click():
    """UI button click — short tone."""
    dur = 0.04
    n = int(dur * SAMPLE_RATE)
    t = np.linspace(0, dur, n)
    wave = np.sin(2 * np.pi * 800 * t) * 0.2
    env = _envelope(n, attack=0.001, decay=0.03)
    return _to_sound(wave * env)


def make_extraction():
    """Sweeping beacon alarm — layered sweep + warning tone."""
    dur = 1.5
    n = int(dur * SAMPLE_RATE)
    t = np.linspace(0, dur, n)

    # Sweep (frequency modulation)
    sweep_freq = 400 + 200 * np.sin(2 * np.pi * 2 * t)
    sweep = np.sin(2 * np.pi * sweep_freq * t) * 0.2

    # Warning tone (steady)
    warning = np.sin(2 * np.pi * 880 * t) * 0.15
    warning *= (0.5 + 0.5 * np.sin(2 * np.pi * 4 * t))  # amplitude modulation

    # Envelope
    env = np.ones(n)
    env[:int(0.1 * SAMPLE_RATE)] = np.linspace(0, 1, int(0.1 * SAMPLE_RATE))

    return _to_sound((sweep + warning) * env * 0.3)


def make_wave_alarm():
    """Wave start alarm — urgent warning."""
    dur = 0.8
    n = int(dur * SAMPLE_RATE)
    t = np.linspace(0, dur, n)

    # Two-tone alarm (alternating)
    tone1 = np.sin(2 * np.pi * 600 * t) * 0.3
    tone2 = np.sin(2 * np.pi * 800 * t) * 0.3
    switch = (np.sin(2 * np.pi * 4 * t) > 0).astype(float)
    alarm = tone1 * switch + tone2 * (1 - switch)

    env = _envelope(n, attack=0.02, decay=0.7)
    return _to_sound(alarm * env * 0.4)


# ============ AUDIO SYSTEM ============

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

        # Try loading processed WAV files first, fall back to procedural
        import os as _os
        audio_dir = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)),
                                  '..', 'assets', 'audio')
        if getattr(__import__('sys'), 'frozen', False):
            audio_dir = _os.path.join(__import__('sys')._MEIPASS, 'assets', 'audio')

        self.sfx = {}
        wav_sounds = ['pulse_rifle', 'shotgun', 'flamethrower', 'reload']
        for name in wav_sounds:
            wav_path = _os.path.join(audio_dir, f'{name}.wav')
            if _os.path.exists(wav_path):
                try:
                    self.sfx[name] = pygame.mixer.Sound(wav_path)
                    continue
                except pygame.error:
                    pass
            # Fallback to procedural
            self.sfx[name] = self._make_procedural(name)

        # Always-procedural sounds
        self.sfx['xeno_screech'] = make_xeno_screech()
        self.sfx['xeno_death'] = make_xeno_death()
        self.sfx['hit_marker'] = make_hit_marker()
        self.sfx['player_hurt'] = make_player_hurt()
        self.sfx['footstep'] = make_footstep()
        self.sfx['ping'] = make_ping()
        self.sfx['ui_click'] = make_ui_click()
        self.sfx['extraction'] = make_extraction()
        self.sfx['wave_alarm'] = make_wave_alarm()
        print("[audio] Ready.")

        # Ping timer
        self.ping_timer = 0.0
        # Footstep timer
        self.footstep_timer = 0.0
        self.footstep_interval = 0.35

    def _make_procedural(self, name):
        """Fallback procedural sound generator."""
        makers = {
            'pulse_rifle': make_pulse_rifle,
            'shotgun': make_shotgun,
            'flamethrower': make_flamethrower,
            'reload': make_reload,
        }
        fn = makers.get(name)
        return fn() if fn else make_ui_click()

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

    def update_footsteps(self, dt, moving, sprinting):
        """Play footstep sounds when moving."""
        if not self.enabled or self.muted:
            return
        if not moving:
            self.footstep_timer = 0.0
            return
        interval = self.footstep_interval * (0.6 if sprinting else 1.0)
        self.footstep_timer += dt
        if self.footstep_timer >= interval:
            self.footstep_timer = 0.0
            self.play('footstep', volume=0.3)

    def toggle_mute(self):
        self.muted = not self.muted
        return self.muted
