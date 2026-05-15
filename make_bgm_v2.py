#!/usr/bin/env python3
"""
審美眼 BGM v2 — Dark Luxury Cinematic
Pure numpy synthesis: no MIDI, no soundfont.
Style: Hans Zimmer × luxury brand commercial
Key: D minor  BPM: 116  Duration: ~67s
"""

import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfilt

SR     = 44100
BPM    = 116
SPB    = 60.0 / BPM          # seconds per beat ≈ 0.517s
BARS   = 68                  # total bars (4/4)
BEATS  = BARS * 4
DUR    = BEATS * SPB + 4.0   # +4s tail
N      = int(DUR * SR)
rng    = np.random.default_rng(42)

print(f"SR={SR}Hz  BPM={BPM}  Duration={DUR:.1f}s  Samples={N:,}")

# ── DSP helpers ────────────────────────────────────────────

def lpf(x, cut, order=2):
    sos = butter(order, np.clip(cut/(SR/2), 1e-4, 0.999), btype='low', output='sos')
    return sosfilt(sos, x)

def hpf(x, cut, order=2):
    sos = butter(order, np.clip(cut/(SR/2), 1e-4, 0.999), btype='high', output='sos')
    return sosfilt(sos, x)

def bpf(x, lo, hi, order=2):
    sos = butter(order, [np.clip(lo/(SR/2),1e-4,0.499), np.clip(hi/(SR/2),0.501,0.999)],
                 btype='band', output='sos')
    return sosfilt(sos, x)

def tanh_clip(x, drive=1.0):
    return np.tanh(x * drive) / drive

def freq(midi):
    return 440.0 * 2.0 ** ((midi - 69) / 12.0)

def adsr_env(n, a_s, d_s, sus, r_s):
    e = np.zeros(n)
    a = min(int(a_s * SR), n)
    d = min(int(d_s * SR), n - a)
    r = min(int(r_s * SR), n)
    s = max(0, n - a - d - r)
    if a > 0: e[:a]       = np.linspace(0, 1, a)
    if d > 0: e[a:a+d]    = np.linspace(1, sus, d)
    e[a+d:a+d+s]           = sus
    if r > 0 and a+d+s < n:
        e[a+d+s:a+d+s+r]  = np.linspace(sus, 0, min(r, n-(a+d+s)))
    return np.clip(e, 0, 1)

def simple_reverb(x, mix=0.35):
    """Comb-filter reverb approximation"""
    taps = [int(SR * t) for t in [0.029, 0.051, 0.073, 0.097, 0.131, 0.173]]
    g    = [0.45, 0.38, 0.32, 0.26, 0.20, 0.15]
    wet  = np.zeros(len(x))
    for t, gv in zip(taps, g):
        if t < len(x):
            wet[t:] += x[:-t] * gv
    return x * (1 - mix) + wet * mix

def stereo_width(mono, delay_ms=12):
    """Mid-side spread via micro-delay"""
    d = int(delay_ms * SR / 1000)
    L = mono.copy()
    R = np.zeros(len(mono))
    if d < len(mono):
        R[d:] = mono[:-d]
    return L, R

# ── Oscillators ───────────────────────────────────────────

def supersaw(f, n, voices=7, detune=0.013, amp=1.0):
    """Band-limited supersaw via additive harmonics"""
    t   = np.arange(n, dtype=np.float64) / SR
    out = np.zeros(n)
    for v in range(voices):
        d = 1.0 + (v - voices // 2) * detune
        s = np.zeros(n)
        for h in range(1, 10):
            s += np.sin(2*np.pi * f*d*h * t) / h * ((-1)**(h+1))
        out += s
    return out * amp * (2 / np.pi) / voices

def sine(f, n, amp=1.0, phase=0.0):
    t = np.arange(n, dtype=np.float64) / SR
    return amp * np.sin(2*np.pi*f*t + phase)

def warm_bass(f, n, amp=1.0):
    """Sub bass: sine + 2nd harmonic, filtered"""
    t  = np.arange(n, dtype=np.float64) / SR
    s  = np.sin(2*np.pi*f*t) + 0.35*np.sin(4*np.pi*f*t)
    s  = tanh_clip(s, 1.8)
    return lpf(s, min(f * 4, 400)) * amp

# ── Drum synthesis ─────────────────────────────────────────

def make_kick():
    dur = 0.5
    n   = int(dur * SR)
    t   = np.arange(n) / SR
    # Pitch: 90 Hz → 38 Hz exponential decay
    pitch = 90 * np.exp(-22 * t) + 38
    ph    = 2*np.pi * np.cumsum(pitch) / SR
    tone  = np.sin(ph) * np.exp(-7 * t)
    sub   = sine(38, n) * np.exp(-4 * t) * 0.5
    click = lpf(rng.standard_normal(n) * np.exp(-180 * t) * 0.18, 4000)
    s     = tone + sub + click
    return tanh_clip(s, 1.5) * 0.95

def make_snare():
    dur = 0.25
    n   = int(dur * SR)
    t   = np.arange(n) / SR
    noise = rng.standard_normal(n) * np.exp(-16 * t)
    body  = bpf(noise, 180, 5000) * 0.8
    snap  = hpf(rng.standard_normal(n) * np.exp(-120 * t), 5000) * 0.5
    tone  = (sine(195, n) + sine(290, n)) * np.exp(-22 * t) * 0.25
    s     = body + snap + tone
    return tanh_clip(s, 1.2) * 0.85

def make_hihat(dur=0.055):
    n  = int(dur * SR)
    t  = np.arange(n) / SR
    s  = hpf(rng.standard_normal(n), 8000) * np.exp(-50 * t)
    return s * 0.55

def make_hihat_open():
    n  = int(0.22 * SR)
    t  = np.arange(n) / SR
    s  = hpf(rng.standard_normal(n), 7000) * np.exp(-9 * t)
    return s * 0.45

def make_clap():
    n  = int(0.18 * SR)
    t  = np.arange(n) / SR
    s  = bpf(rng.standard_normal(n), 700, 7000) * (np.exp(-18*t) + 0.4*np.exp(-80*(t-0.008)**2))
    return tanh_clip(s, 1.1) * 0.75

# ── Pad synthesis ──────────────────────────────────────────

def make_pad(midi_notes, dur_s, vel=0.55, atk=1.8):
    n   = int(dur_s * SR)
    out = np.zeros(n)
    for m in midi_notes:
        f   = freq(m)
        osc = supersaw(f, n, voices=5, detune=0.016, amp=vel)
        env = adsr_env(n, atk, 0.2, 0.8, min(2.5, dur_s * 0.35))
        out += lpf(osc * env, 2800)
    return out

# ── Lead synth ─────────────────────────────────────────────

def make_lead(midi_note, dur_s, vol=0.55):
    n   = int(dur_s * SR)
    f   = freq(midi_note)
    t   = np.arange(n) / SR
    # Vibrato kicks in after 0.25s
    vib = 1 + 0.003 * np.sin(2*np.pi*5.2*t) * np.minimum(t / 0.25, 1.0)
    ph  = 2*np.pi * f * np.cumsum(vib) / SR
    s   = (np.sin(ph)
           + 0.45 * np.sin(2*ph)
           + 0.18 * np.sin(3*ph)
           + 0.06 * np.sin(4*ph))
    env = adsr_env(n, 0.06, 0.08, 0.82, min(0.45, dur_s * 0.3))
    return lpf(s * env * vol, 5000)

# ── Mix bus ────────────────────────────────────────────────

L_bus = np.zeros(N)
R_bus = np.zeros(N)

def place(mono, t_s, vol=1.0, pan=0.0):
    start = int(t_s * SR)
    slen  = min(len(mono), N - start)
    if slen <= 0:
        return
    lv = vol * np.clip(1.0 - pan, 0, 1.4)
    rv = vol * np.clip(1.0 + pan, 0, 1.4)
    L_bus[start:start+slen] += mono[:slen] * lv
    R_bus[start:start+slen] += mono[:slen] * rv

def place_stereo(l, r, t_s, vol=1.0):
    start = int(t_s * SR)
    slen  = min(len(l), N - start)
    if slen <= 0:
        return
    L_bus[start:start+slen] += l[:slen] * vol
    R_bus[start:start+slen] += r[:slen] * vol

def b(bar, beat_num=0, sub=1):
    """Time in seconds: bar (0-indexed), beat (0-3), subdivision"""
    return (bar * 4 + beat_num) * SPB + (SPB / sub if sub > 1 else 0)

# ── Pre-bake one-shots ─────────────────────────────────────

print("  Baking drums...")
K  = make_kick()
S  = make_snare()
HH = make_hihat()
HO = make_hihat_open()
CL = make_clap()

# ── DRUM PATTERN ──────────────────────────────────────────
# Intro: bars 0-3  (no drums, or very soft)
# Buildup: bars 4-7  (kick only)
# Beat: bars 8+    (full pattern)
# Climax: bars 20+ (16th hi-hats)

print("  Placing drums...")
for bar in range(BARS):
    prog   = bar / BARS
    t0     = b(bar)

    if bar < 4:
        continue   # pure intro

    if bar < 8:    # kick only, growing
        v = 0.5 + 0.5 * (bar - 4) / 4
        place(K, b(bar, 0), v)
        place(K, b(bar, 2), v * 0.85)
        for e in range(8):
            place(HH, t0 + e * SPB / 2, 0.15 + 0.05 * (bar-4)/4, pan=0.25)
        continue

    # Full beat
    vk = min(1.0, 0.85 + prog * 0.15)
    vs = min(1.0, 0.72 + prog * 0.28)
    vh = min(0.65, 0.4 + prog * 0.25)

    # Kick: 1, 3  + ghost on 2.75 in last beat of phrase
    place(K, b(bar, 0), vk)
    place(K, b(bar, 2), vk * 0.9)
    if bar % 4 == 3:
        place(K, t0 + 2.75 * SPB, vk * 0.6)

    # Snare+clap on 2, 4
    place(S,  b(bar, 1), vs * 0.85, pan=0.12)
    place(CL, b(bar, 1), vs * 0.55, pan=-0.12)
    place(S,  b(bar, 3), vs,        pan=0.12)
    place(CL, b(bar, 3), vs * 0.65, pan=-0.12)

    # Hi-hats: 8th notes until bar 20, then 16th
    if bar >= 20:
        for e in range(16):
            on_beat = (e % 4 == 0)
            if e % 4 == 2:
                place(HO, t0 + e * SPB / 4, vh * 0.55, pan=0.3)
            else:
                place(HH, t0 + e * SPB / 4,
                      vh * (0.75 if on_beat else 0.35), pan=0.3)
    else:
        for e in range(8):
            place(HH, t0 + e * SPB / 2,
                  vh * (0.7 if e % 2 == 0 else 0.38), pan=0.3)

# ── BASS LINE ─────────────────────────────────────────────
# Chord progression (2 bars each):
#   Dm  Bb  F  Am  (dark, cinematic minor)
# MIDI: D2=38  Bb1=34  F2=41  A2=45
# Use D2, Bb2(46-12=34→too low)... use D2=38, Bb2=46-12+12=46, F2=41, A2=45

BASS_PROG = [38, 46, 41, 45]   # D2, Bb2, F2, A2 — half-step adjusted

print("  Placing bass...")
bar = 0
while bar * SPB * 4 < DUR - 2:
    chord_idx = (bar // 2) % len(BASS_PROG)
    note      = BASS_PROG[chord_idx]
    f         = freq(note)
    prog      = bar / BARS
    v         = min(1.1, 0.55 + prog * 0.55)

    for beat_n in range(4):
        t_s = b(bar, beat_n)
        if t_s >= DUR - 1:
            break
        dur_beat = SPB * 0.82
        bn  = warm_bass(f, int(dur_beat * SR), amp=v)
        env = adsr_env(len(bn), 0.008, 0.04, 0.85, 0.15)
        bn  = lpf(bn * env, 300)
        place(bn, t_s, 1.1)

    bar += 1

# ── PAD CHORDS ────────────────────────────────────────────
# Voicings (mid-range, warm)
# Dm: D3 F3 A3  Bb: Bb2 D3 F3  F: F3 A3 C4  Am: A3 C#4 E4
PAD_CHORDS = [
    [50, 53, 57],          # Dm  (D3 F3 A3)
    [46, 50, 53],          # Bb  (Bb2 D3 F3)
    [53, 57, 60],          # F   (F3 A3 C4)
    [57, 61, 64],          # Am  (A3 C#4 E4)
]

print("  Placing pads...")
pad_bar_dur = 2 * 4 * SPB   # 2 bars per chord

t_pad = 0.0
chord_i = 0
while t_pad < DUR - 3:
    chord     = PAD_CHORDS[chord_i % len(PAD_CHORDS)]
    prog      = t_pad / DUR
    # Pads fade in over first 8 bars
    v_pad     = min(0.7, prog * 3.5) if t_pad < 8 * SPB * 4 else 0.65 + 0.1 * min(1, (t_pad - 8*SPB*4) / 24)
    dur_chunk = min(pad_bar_dur + 3.0, DUR - t_pad + 3.0)
    atk       = 1.2 if t_pad < 4 else 0.8

    pad = make_pad(chord, dur_chunk, vel=0.48, atk=atk)
    pad = simple_reverb(pad, mix=0.4)
    lp, rp = stereo_width(pad, delay_ms=14)

    place_stereo(lp, rp, t_pad, v_pad)

    t_pad   += pad_bar_dur
    chord_i += 1

# ── LEAD MELODY ───────────────────────────────────────────
# Enters at bar 8 (~18s), builds to climax
# D minor scale: D E F G A Bb C
D4, E4, F4, G4, A4 = 62, 64, 65, 67, 69
Bb4, C5, D5        = 70, 72, 74
A3, F3             = 57, 53

# (start_bar, beat, note_midi, duration_beats)
melody = [
    # Theme A — bar 8–15
    (8,  0,   D4,  1),
    (8,  1,   D4,  0.5),
    (8,  1.5, A4,  1.5),
    (8,  3,   F4,  1),
    (9,  0,   D4,  2),
    (9,  2,   F4,  1),
    (9,  3,   G4,  1),
    (10, 0,   A4,  2),
    (10, 2,   G4,  1),
    (10, 3,   F4,  1),
    (11, 0,   D4,  4),

    (12, 0,   F4,  1),
    (12, 1,   G4,  1),
    (12, 2,   A4,  2),
    (13, 0,   Bb4, 1.5),
    (13, 1.5, A4,  1),
    (13, 2.5, G4,  0.5),
    (13, 3,   F4,  1),
    (14, 0,   D4,  4),

    # Theme B — bar 16–23 (higher, louder)
    (16, 0,   A4,  1),
    (16, 1,   A4,  0.5),
    (16, 1.5, D5,  1.5),
    (16, 3,   C5,  1),
    (17, 0,   A4,  2),
    (17, 2,   Bb4, 1),
    (17, 3,   A4,  1),
    (18, 0,   G4,  2),
    (18, 2,   F4,  2),
    (19, 0,   D4,  4),

    (20, 0,   F4,  0.5),
    (20, 0.5, G4,  0.5),
    (20, 1,   A4,  1),
    (20, 2,   Bb4, 1.5),
    (20, 3.5, A4,  0.5),
    (21, 0,   G4,  1),
    (21, 1,   A4,  1),
    (21, 2,   D5,  2),
    (22, 0,   C5,  1.5),
    (22, 1.5, Bb4, 0.5),
    (22, 2,   A4,  2),
    (23, 0,   D4,  4),

    # Climax — bar 24–31
    (24, 0,   D5,  1),
    (24, 1,   C5,  1),
    (24, 2,   Bb4, 1),
    (24, 3,   A4,  1),
    (25, 0,   G4,  2),
    (25, 2,   A4,  2),
    (26, 0,   D5,  4),
    (27, 0,   C5,  2),
    (27, 2,   Bb4, 2),

    (28, 0,   A4,  1),
    (28, 1,   G4,  1),
    (28, 2,   A4,  2),
    (29, 0,   D5,  2),
    (29, 2,   F4,  0.5),
    (29, 2.5, G4,  0.5),
    (29, 3,   A4,  1),
    (30, 0,   Bb4, 2),
    (30, 2,   A4,  2),
    (31, 0,   D4,  4),

    # Resolution — bar 32–39
    (32, 0,   D4,  2),
    (32, 2,   F4,  2),
    (33, 0,   A4,  4),
    (34, 0,   G4,  2),
    (34, 2,   F4,  2),
    (35, 0,   D4,  6),
    (36, 2,   A3,  4),
    (38, 0,   D4,  8),
]

print("  Placing melody...")
for (bar_n, beat_n, note, dur_b) in melody:
    t_s  = bar_n * 4 * SPB + beat_n * SPB
    if t_s >= DUR:
        break
    prog = t_s / DUR
    # Lead fades in, peaks at climax
    if bar_n < 16:
        v = 0.42 + 0.15 * (bar_n - 8) / 8
    elif bar_n < 24:
        v = 0.57 + 0.18 * (bar_n - 16) / 8
    else:
        v = 0.75 - 0.25 * max(0, (bar_n - 32) / 8)

    dur_s = dur_b * SPB
    ln    = make_lead(note, min(dur_s + 0.3, DUR - t_s), vol=v)
    ln    = simple_reverb(ln, mix=0.38)
    ll, lr = stereo_width(ln, delay_ms=8)
    place_stereo(ll, lr, t_s, 1.0)

# ── MASTER ────────────────────────────────────────────────

print("  Mastering...")

# Gentle master compression (RMS limiting)
def rms_compress(x, threshold=0.5, ratio=4.0, attack_s=0.01, release_s=0.1):
    out   = x.copy()
    rms   = 0.0
    a_c   = np.exp(-1.0 / (attack_s * SR))
    r_c   = np.exp(-1.0 / (release_s * SR))
    gain  = np.ones(len(x))
    for i in range(len(x)):
        rms = max(abs(x[i]), rms * r_c if abs(x[i]) < rms else rms * a_c + abs(x[i]) * (1 - a_c))
        if rms > threshold:
            g = (threshold + (rms - threshold) / ratio) / rms
        else:
            g = 1.0
        gain[i] = g
    return out * gain

# Smooth fade-in / fade-out
fade_in_n  = int(2.0 * SR)
fade_out_n = int(4.0 * SR)

L = L_bus.copy()
R = R_bus.copy()

L[:fade_in_n]  *= np.linspace(0, 1, fade_in_n)
R[:fade_in_n]  *= np.linspace(0, 1, fade_in_n)
L[-fade_out_n:] *= np.linspace(1, 0, fade_out_n)
R[-fade_out_n:] *= np.linspace(1, 0, fade_out_n)

# Normalize + soft clip
peak = max(np.max(np.abs(L)), np.max(np.abs(R)), 1e-6)
L = np.tanh(L / peak * 1.1) * 0.95
R = np.tanh(R / peak * 1.1) * 0.95

stereo = np.column_stack([L, R])
out16  = (stereo * 32767).astype(np.int16)

OUT = "/home/user/fuyusou.project/bgm_v2.wav"
wavfile.write(OUT, SR, out16)

import os
size_mb = os.path.getsize(OUT) / 1024 / 1024
print(f"\n✓ Saved: {OUT}  ({size_mb:.1f}MB  {DUR:.1f}s)")
