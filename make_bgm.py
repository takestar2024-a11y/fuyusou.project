"""
審美眼 Epic BGM Generator
Avengers風の壮大なオーケストラBGMをMIDIで生成し、WAVに変換する
"""

import mido
import subprocess

BPM = 130
TEMPO = int(60_000_000 / BPM)
PPQ = 480

Q  = PPQ          # quarter note
H  = PPQ * 2      # half
W  = PPQ * 4      # whole
E  = PPQ // 2     # eighth
S  = PPQ // 4     # sixteenth
DQ = Q + E        # dotted quarter
DH = H + Q        # dotted half

# MIDI notes (D major)
D2,A2,Fs2,G2      = 38,45,42,43
D3,E3,Fs3,G3,A3,B3,Cs3 = 50,52,54,55,57,59,49
D4,E4,Fs4,G4,A4,B4,Cs4 = 62,64,66,67,69,71,73
C4                 = 60
D5,E5,Fs5,G5,A5,B5 = 74,76,78,79,81,83
C5                 = 72
D6                 = 86

# Percussion (ch 9)
KICK   = 36
SNARE  = 38
CRASH  = 49
RIDE   = 51
HIHAT  = 42
TOM_L  = 41
TOM_M  = 45
TOM_H  = 48
TIMPA_L = 41  # low floor tom → timpani feel
TIMPA_H = 47  # low-mid tom

def build_track(name, ch, prog, events):
    """
    events: list of (abs_tick, pitch, velocity, duration)
    Returns MidiTrack with delta-time messages
    """
    msgs = []
    if prog is not None and ch != 9:
        msgs.append((0, mido.Message('program_change', channel=ch, program=prog, time=0)))

    for (t, pitch, vel, dur) in events:
        msgs.append((t,     mido.Message('note_on',  channel=ch, note=pitch, velocity=vel, time=0)))
        msgs.append((t+dur, mido.Message('note_off', channel=ch, note=pitch, velocity=0,   time=0)))

    msgs.sort(key=lambda x: x[0])
    track = mido.MidiTrack()
    track.name = name
    prev = 0
    for (t, msg) in msgs:
        msg.time = t - prev
        track.append(msg)
        prev = t
    return track

def rpt(pattern, n, start=0):
    """Repeat a pattern n times starting at tick 'start'"""
    result = []
    span = max(t + d for t, p, v, d in pattern)
    for i in range(n):
        offset = start + i * span
        result += [(offset + t, p, v, d) for (t, p, v, d) in pattern]
    return result

# ── 楽曲設計 ──────────────────────────────────────────────
# 130BPM, 70秒 = ~151beats = 72,480 ticks
# Structure:
#  [Intro]      0     -  8Q  (0     - 3840)  低弦+ティンパニ
#  [ThemeA]     8Q    - 24Q  (3840  - 11520) ホルン主題
#  [Build]      24Q   - 48Q  (11520 - 23040) 全弦+ブラス
#  [Climax]     48Q   - 96Q  (23040 - 46080) フルオーケストラ
#  [Resolution] 96Q   - 120Q (46080 - 57600) D major 解決
#  [Outro]     120Q   - 152Q (57600 - 73000) フェードアウト

# ── Track 1: French Horn (ch0, prog=60) ──────────────────
# 主旋律: D4-D4-A4-F#4-D5 英雄的モチーフ
horn_motif = [
    # bar1
    (0,   D4,  90, Q),
    (Q,   D4,  85, E),
    (DQ,  A4,  95, DQ),
    (3*Q, Fs4, 90, Q),
    # bar2
    (W,   D5,  100, H),
    (W+H, A4,  90,  H),
    # bar3
    (2*W,  G4,  90, Q),
    (2*W+Q,A4,  95, E),
    (2*W+DQ, B4, 95, DQ),
    (2*W+3*Q, Cs4+12, 90, Q),  # C#5
    # bar4
    (3*W,  D5, 100, W),
]
# motif span = 4 bars = 4W = 4*1920 = 7680

# Intro: no horn
# ThemeA (8Q = 2W): horn plays motif once
horn_A = [(t + 8*Q, p, v, d) for (t,p,v,d) in horn_motif]

# Build: horn repeats with higher energy
horn_B = [(t + 24*Q, p, v+5, d) for (t,p,v,d) in horn_motif]
horn_B2 = [(t + 24*Q + 4*W, p, v+5, d) for (t,p,v,d) in horn_motif]

# Climax: horn plays high and loud
climax_motif = [
    (0,   D5,  110, Q),
    (Q,   D5,  105, E),
    (DQ,  A5,  115, DQ),
    (3*Q, Fs5, 110, Q),
    (W,   D5,  115, H),
    (W+H, E5,  110, H),
    (2*W, Fs5, 115, Q),
    (2*W+Q, G5, 115, DH),
    (3*W, A5,  120, W),
]
horn_climax = [(t + 48*Q, p, v, d) for (t,p,v,d) in climax_motif]
horn_climax2 = [(t + 48*Q + 4*W, p, v, d) for (t,p,v,d) in climax_motif]
horn_climax3 = [(t + 48*Q + 8*W, p, v, d) for (t,p,v,d) in climax_motif]

# Resolution
horn_res = [
    (96*Q,      D5,  105, H),
    (96*Q+H,    Fs5, 100, H),
    (96*Q+W,    A5,  110, H),
    (96*Q+W+H,  D6,  115, W),
    (96*Q+3*W,  A5,  100, H),
    (96*Q+3*W+H,Fs5, 95,  H),
    (96*Q+4*W,  D5,  90,  DH),
    (96*Q+4*W+DH,A4, 85,  DH),
    (96*Q+5*W+Q, D5, 80,  W*2),
]
horn_outro = [
    (120*Q, D4, 70, W),
    (120*Q+W, Fs4, 65, W),
    (120*Q+2*W, A4, 60, W),
    (120*Q+3*W, D5, 55, W*2),
]

horn_events = horn_A + horn_B + horn_B2 + horn_climax + horn_climax2 + horn_climax3 + horn_res + horn_outro

# ── Track 2: Trumpet (ch1, prog=56) ──────────────────────
# ファンファーレスタブ
trump_intro = [
    (4*Q, D4, 80, E),
    (4*Q+E, E4, 80, E),
    (4*Q+Q, Fs4, 80, Q),
    (5*Q, A4, 85, H),
    (6*Q, G4, 80, E),
    (6*Q+E, Fs4, 80, E),
    (6*Q+Q, E4, 80, Q),
    (7*Q, D4, 85, Q),
]

trump_build_motif = [
    (0,   A4, 90, E),
    (E,   B4, 90, E),
    (Q,   Cs4+12, 92, Q),
    (H,   D5, 95, H),
    (W,   E5, 90, Q),
    (W+Q, D5, 88, Q),
    (W+H, Cs4+12, 85, H),
    (2*W, A4, 92, W),
]
trump_build = rpt(trump_build_motif, 3, 24*Q)

trump_climax = [
    (48*Q,       D5, 110, Q),
    (48*Q+Q,     E5, 108, Q),
    (48*Q+H,     Fs5, 112, H),
    (48*Q+W,     G5, 110, Q),
    (48*Q+W+Q,   A5, 115, H),
    (48*Q+W+3*Q, G5, 108, Q),
    (48*Q+2*W,   Fs5, 110, W),
    (48*Q+3*W,   A5, 115, W),
    # repeat higher
    (52*Q+4*W,   D5, 112, Q),
    (52*Q+4*W+Q, E5, 110, Q),
    (52*Q+4*W+H, Fs5, 114, H),
    (52*Q+5*W,   A5, 118, H),
    (52*Q+5*W+H, G5, 112, H),
    (52*Q+6*W,   Fs5, 115, W),
    (52*Q+7*W,   D5, 110, W),
]
trump_res = [
    (96*Q,  Fs5, 100, H),
    (96*Q+H,A5,  105, H),
    (96*Q+W,D6,  110, W),
    (100*Q, A5,  100, H),
    (100*Q+H, Fs5, 95, H),
    (101*Q+Q, D5, 90, W),
    (105*Q, D5, 80, W*2),
]

trump_events = trump_intro + trump_build + trump_climax + trump_res

# ── Track 3: Trombone (ch2, prog=57) ─────────────────────
# ベースライン + 対旋律
trom_intro = [
    (0, D3, 75, H),
    (H, A2, 72, H),
    (W, G2, 70, H),
    (W+H, A2, 72, H),
    (2*W, D3, 75, W),
    (3*W, A2, 72, W),
]

trom_chord_motif = [
    (0,  D3,  80, Q),
    (Q,  D3,  78, Q),
    (H,  A3,  82, H),
    (W,  G3,  80, H),
    (W+H,A3,  80, H),
    (2*W,D3,  82, W),
    (3*W,A2,  78, H),
    (3*W+H, G2, 75, H),
]
trom_mid = rpt(trom_chord_motif, 3, 24*Q)

trom_climax_motif = [
    (0,  D3, 95, Q),
    (Q,  E3, 90, Q),
    (H,  Fs3,92, H),
    (W,  G3, 90, Q),
    (W+Q,A3, 95, DH),
    (2*W+Q, G3, 88, Q),
    (2*W+H, Fs3, 90, H),
    (3*W,D3, 92, W),
]
trom_climax = rpt(trom_climax_motif, 3, 48*Q)

trom_res = [
    (96*Q, D3, 90, W),
    (96*Q+W, A3, 85, W),
    (96*Q+2*W, G3, 88, W),
    (96*Q+3*W, A2, 82, W),
    (100*Q, D3, 85, W*2),
    (104*Q, A2, 78, W*2),
    (108*Q, D2, 72, W*4),
]

trom_events = trom_intro + trom_mid + trom_climax + trom_res

# ── Track 4: String Ensemble (ch3, prog=48) ───────────────
# コード + ランニング
def str_chord(t, notes, vel, dur):
    return [(t, n, vel, dur) for n in notes]

# D major chord voicings
D_chord  = [D3, Fs3, A3, D4]
A_chord  = [A2, E3,  A3, Cs3+12]  # A major
G_chord  = [G2, B3,  D4, G4]
Fs_chord = [Fs3, Cs3+12, Fs4]
Bm_chord = [B3,  D4,  Fs4]
Em_chord = [E3,  G3,  B3]

str_intro = (
    str_chord(0,   [D3,Fs3,A3], 60, W) +
    str_chord(W,   [G2,B3,D4],  58, W) +
    str_chord(2*W, [A2,E3,A3],  60, W) +
    str_chord(3*W, [D3,Fs3,A3], 62, W)
)

# String runs (eight-note ascending scale) during build
def scale_run(start, base_oct, vel):
    scale = [D4,E4,Fs4,G4,A4,B4,Cs4+12,D5,E5,Fs5,G5,A5]
    result = []
    for i, n in enumerate(scale):
        result.append((start + i*E, n, vel, E))
    return result

str_build = (
    str_chord(24*Q,       D_chord,  70, H) +
    str_chord(24*Q+H,     G_chord,  70, H) +
    str_chord(24*Q+W,     A_chord,  72, H) +
    str_chord(24*Q+W+H,   D_chord,  72, H) +
    scale_run(24*Q+2*W,   4, 68) +
    scale_run(24*Q+2*W+W, 4, 70) +
    str_chord(24*Q+4*W,   D_chord,  74, H) +
    str_chord(24*Q+4*W+H, G_chord,  74, H) +
    str_chord(24*Q+5*W,   A_chord,  76, H) +
    str_chord(24*Q+5*W+H, D_chord,  76, H) +
    scale_run(24*Q+6*W,   4, 72) +
    scale_run(24*Q+6*W+W, 4, 75) +
    # third section build
    str_chord(24*Q+8*W,  D_chord, 78, H) +
    str_chord(24*Q+8*W+H,G_chord, 78, H) +
    str_chord(24*Q+9*W,  A_chord, 80, H) +
    str_chord(24*Q+9*W+H,Bm_chord,78, H) +
    scale_run(24*Q+10*W, 4, 76) +
    scale_run(24*Q+10*W+W, 4, 78)
)

str_climax = (
    str_chord(48*Q,      [D4,Fs4,A4,D5], 95, H) +
    str_chord(48*Q+H,    [G4,B4,D5,G5],  92, H) +
    str_chord(48*Q+W,    [A4,Cs4+12,E5,A5], 98, H) +
    str_chord(48*Q+W+H,  [D4,Fs4,A4,D5], 95, H) +
    scale_run(48*Q+2*W,  5, 85) +
    scale_run(48*Q+3*W,  5, 88) +
    str_chord(52*Q+4*W,  [D4,Fs4,A4,D5], 100, H) +
    str_chord(52*Q+4*W+H,[G4,B4,D5,G5],   97, H) +
    str_chord(52*Q+5*W,  [A4,Cs4+12,E5,A5],102,H) +
    str_chord(52*Q+5*W+H,[D4,Fs4,A4,D5], 100, H) +
    scale_run(52*Q+6*W,  5, 88) +
    scale_run(52*Q+7*W,  5, 90) +
    str_chord(60*Q+8*W,  [D4,Fs4,A4,D5], 102, H) +
    str_chord(60*Q+8*W+H,[G4,B4,D5],      98, H) +
    str_chord(60*Q+9*W,  [A4,E5,A5],      105, H) +
    str_chord(60*Q+9*W+H,[D5,Fs5,A5],     108, H) +
    scale_run(60*Q+10*W, 5, 90) +
    scale_run(60*Q+11*W, 5, 92)
)

str_res = (
    str_chord(96*Q,      [D4,Fs4,A4,D5], 90, W) +
    str_chord(96*Q+W,    [A3,E4,A4,Cs4+12], 85, W) +
    str_chord(96*Q+2*W,  [G3,B3,D4,G4],   88, W) +
    str_chord(96*Q+3*W,  [A3,E4,A4],       85, W) +
    str_chord(100*Q,     [D4,Fs4,A4,D5], 88, W) +
    str_chord(100*Q+W,   [G3,B3,D4,G4],  82, W) +
    str_chord(100*Q+2*W, [A3,Cs4+12,E4,A4], 78, W) +
    str_chord(100*Q+3*W, [D3,Fs3,A3,D4], 75, W) +
    str_chord(104*Q,     [D3,Fs3,A3,D4], 68, W*2) +
    str_chord(108*Q,     [D3,Fs3,A3,D4], 60, W*2) +
    str_chord(112*Q,     [D2,D3,Fs3,A3], 50, W*4)
)

str_events = str_intro + str_build + str_climax + str_res

# ── Track 5: Percussion (ch9) ────────────────────────────
def perc(t, note, vel, dur=S):
    return [(t, note, vel, dur)]

# Intro: timpani pulses
perc_intro = (
    perc(0,   TIMPA_L, 80, E) +
    perc(H,   TIMPA_L, 72, E) +
    perc(W,   TIMPA_L, 78, E) +
    perc(W+H, TIMPA_L, 68, E) +
    perc(2*W, TIMPA_L, 82, E) +
    perc(2*W+H, TIMPA_L, 70, E) +
    perc(3*W, TIMPA_L, 85, E) +
    perc(3*W+H, TIMPA_H, 75, E)
)

# Theme A: add kick+snare
def epic_beat(start, bars=2, vel_k=90, vel_s=85):
    result = []
    for b in range(bars * 4):
        t = start + b * Q
        result += perc(t, KICK, vel_k, E)
        if b % 4 == 0:
            result += perc(t, TIMPA_H, vel_k - 5, Q)
        if b % 2 == 1:
            result += perc(t, SNARE, vel_s, E)
        if b % 4 == 3:
            result += perc(t, CRASH, vel_k - 10, E)
    return result

perc_themeA = epic_beat(8*Q, bars=4, vel_k=88, vel_s=82)

perc_build = (
    epic_beat(24*Q, bars=4, vel_k=92, vel_s=86) +
    epic_beat(32*Q, bars=4, vel_k=95, vel_s=88) +
    epic_beat(40*Q, bars=4, vel_k=98, vel_s=90)
)

perc_climax = (
    epic_beat(48*Q, bars=4, vel_k=105, vel_s=98) +
    epic_beat(56*Q, bars=4, vel_k=108, vel_s=100) +
    epic_beat(64*Q, bars=4, vel_k=110, vel_s=102) +
    epic_beat(72*Q, bars=4, vel_k=112, vel_s=104) +
    epic_beat(80*Q, bars=4, vel_k=115, vel_s=106) +
    epic_beat(88*Q, bars=4, vel_k=118, vel_s=108)
)

perc_res = [
    *perc(96*Q,  CRASH,  115, Q),
    *perc(96*Q,  KICK,   110, E),
    *perc(100*Q, CRASH,  105, Q),
    *perc(100*Q, TIMPA_L, 95, Q),
    *perc(104*Q, CRASH,   95, Q),
    *perc(108*Q, TIMPA_L, 85, Q),
    *perc(112*Q, CRASH,   75, Q),
]

perc_events = perc_intro + perc_themeA + perc_build + perc_climax + perc_res

# ── MIDIファイル組み立て ──────────────────────────────────
mid = mido.MidiFile(type=1, ticks_per_beat=PPQ)

# Tempo track
tempo_track = mido.MidiTrack()
tempo_track.append(mido.MetaMessage('set_tempo', tempo=TEMPO, time=0))
tempo_track.append(mido.MetaMessage('time_signature', numerator=4, denominator=4, time=0))
tempo_track.append(mido.MetaMessage('key_signature', key='D', time=0))
mid.tracks.append(tempo_track)

# Add instrument tracks
mid.tracks.append(build_track("French Horn",    0, 60, horn_events))
mid.tracks.append(build_track("Trumpet",        1, 56, trump_events))
mid.tracks.append(build_track("Trombone",       2, 57, trom_events))
mid.tracks.append(build_track("Strings",        3, 48, str_events))
mid.tracks.append(build_track("Percussion",     9, None, perc_events))

mid_path = "/home/user/fuyusou.project/bgm.mid"
mid.save(mid_path)
print(f"MIDI saved: {mid_path}")
print(f"Duration: {mid.length:.1f}s")

# ── fluidsynth で WAV に変換 ──────────────────────────────
sf2 = "/usr/share/sounds/sf2/FluidR3_GM.sf2"
wav_path = "/home/user/fuyusou.project/bgm.wav"

print("Converting MIDI → WAV via fluidsynth...")
result = subprocess.run([
    "fluidsynth", "-ni",
    "-g", "1.5",   # gain
    "-F", wav_path,
    "-r", "44100",
    sf2, mid_path
], capture_output=True, text=True)

if result.returncode == 0:
    import os
    size = os.path.getsize(wav_path)
    print(f"WAV saved: {wav_path} ({size//1024}KB)")
else:
    print("Error:", result.stderr[:500])
