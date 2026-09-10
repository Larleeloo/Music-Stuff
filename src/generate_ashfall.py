#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
"Ashfall" - a sad cinematic ballad in the Blade Runner 2049 idiom, built
around a grand piano.

Generates a Standard MIDI File (format 1, 480 PPQ) for FL Studio 2025.
Pure standard library: no external dependencies.

The 2049 sound is less about patches than about four structural habits, and
all four are written into the data here rather than left to the mix:

  * a pedal that refuses to move.  The sub sits on C# for fifty bars while
    the harmony changes above it, so chords that would otherwise resolve
    just re-colour the same note.  The bass only starts moving at the
    climax, and that alone reads as the ground opening up.
  * voicings that barely move.  C#m9, Amaj9 and F#m11 share four common
    tones, so the strings can hold one chord shape across three chord
    changes.  Only the bass tells you the harmony moved.
  * detuning as an instrument.  The brass wall and the sub drone each carry
    a slow pitch drift of a few cents, at rates that beat against each
    other.  Nothing is in tune with anything for very long.
  * everything swells.  Almost no part starts at its own volume; CC11 does
    the attack, so entries bloom out of the rain rather than beginning.

The lead is a CS-80 played on the ribbon - long portamento slides, delayed
vibrato that widens as a note is held, and swells that take most of a bar.
An ondes-Martenot-style voice wails above it at the climax.  Both come from
`expressive.py`, the same engine that drives Hollow Hour's theremin, tuned
slower and wider.

Form (76 bars, 4/4, ~54 BPM):

    bars  1- 8  I.   Rain          sub, rain, then the piano alone
    bars  9-24  II.  First Light   the theme; strings and the pulse arrive
    bars 25-40  III. The Wall      detuned brass, choir, taiko
    bars 41-52  IV.  Hologram      everything drops away; the flicker
    bars 53-68  V.   Ascension     the bass finally moves; CS-80 and ondes
    bars 69-76  VI.  Ashfall       back to piano and rain

Key is C# minor: i - VI - iv - bII in the main loop, with the Neapolitan D
major as the chord that does not belong.

Usage:
    python3 generate_ashfall.py             # full version
    python3 generate_ashfall.py --clean     # notes only, no controllers
"""

import argparse
import collections
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import expressive  # noqa: E402
from glitch import pitch_glitch, ratchet, stutter  # noqa: E402
from smf import (BAR, BEAT, B, T, Track,  # noqa: E402
                 make_tick_to_sec, tempo_meta, write_smf)

SIXTEENTH = BEAT // 4
THIRTYSECOND = BEAT // 8
BEND_RANGE = 12

# --------------------------------------------------------------------------
# harmony - C# minor
# --------------------------------------------------------------------------
# The three central chords share the tones E, G#, B: C#m9 hears them as
# 3-5-7, Amaj9 as 5-7-9, F#m11 as 7-9-11.  Voicings are chosen so the upper
# parts can hold still while the bass moves, which is the whole trick.
#
#   root  bass root      lh/rh  grand piano hands      brass  the wall
#   strings  high sustain   cello  low sustain   choir  wordless voices
#   timp  timpani pitch (kept inside the drum's real range)

CHORDS = {
    "C#m9":   dict(root=25, lh=[37, 44], rh=[56, 61, 64, 68],
                   brass=[37, 44, 49, 56], strings=[64, 68, 71, 76],
                   cello=[49, 56], choir=[68, 71, 75], timp=49),
    "Amaj9":  dict(root=33, lh=[45, 52], rh=[57, 61, 64, 68],
                   brass=[33, 40, 45, 52], strings=[64, 68, 71, 76],
                   cello=[45, 52], choir=[68, 71, 73], timp=45),
    "F#m11":  dict(root=30, lh=[42, 49], rh=[57, 61, 64, 66],
                   brass=[30, 37, 42, 49], strings=[64, 69, 71, 76],
                   cello=[42, 49], choir=[66, 71, 73], timp=42),
    "Dmaj7":  dict(root=26, lh=[38, 45], rh=[57, 62, 66, 69],
                   brass=[26, 33, 38, 45], strings=[62, 66, 69, 74],
                   cello=[38, 45], choir=[66, 69, 73], timp=50),
    "Emaj9":  dict(root=28, lh=[40, 47], rh=[56, 59, 64, 66],
                   brass=[28, 35, 40, 47], strings=[64, 68, 71, 76],
                   cello=[40, 47], choir=[68, 71, 76], timp=40),
    "Bsus4":  dict(root=35, lh=[47, 54], rh=[59, 64, 66, 71],
                   brass=[35, 42, 47, 54], strings=[64, 66, 71, 78],
                   cello=[47, 54], choir=[66, 71, 76], timp=47),
}

PEDAL = 25                      # C#1 - the note the piece refuses to leave

# two bars per chord: the harmonic rhythm is deliberately glacial
LOOP_A = ["C#m9", "C#m9", "Amaj9", "Amaj9",
          "F#m11", "F#m11", "Dmaj7", "Dmaj7"]        # i - VI - iv - bII
LOOP_B = ["Emaj9", "Emaj9", "Bsus4", "Bsus4",
          "C#m9", "C#m9", "Amaj9", "Amaj9"]          # III - VII - i - VI

PROG = {}


def _lay(first, names):
    for i, n in enumerate(names):
        PROG[first + i] = n


_lay(1, ["C#m9"] * 6 + ["Amaj9"] * 2)
for b in (9, 17, 25, 33, 61):
    _lay(b, LOOP_A)
_lay(41, ["C#m9"] * 4 + ["Dmaj7"] * 2 + ["C#m9"] * 2
     + ["Amaj9"] * 2 + ["Bsus4"] * 2)
_lay(53, LOOP_B)
_lay(69, ["C#m9", "C#m9", "Amaj9", "Amaj9"] + ["C#m9"] * 4)

LAST_BAR = 76

SECTIONS = [("rain", 1, 8), ("light", 9, 24), ("wall", 25, 40),
            ("hologram", 41, 52), ("ascension", 53, 68), ("ashfall", 69, 76)]


def ch(bar):
    return CHORDS[PROG[bar]]


def section_of(bar):
    for name, first, last in SECTIONS:
        if first <= bar <= last:
            return name
    return "ashfall"


# The bass holds the tonic pedal everywhere except the climax.  That single
# decision is most of what makes the last section feel like it lifts off.
def bass_root(bar):
    return ch(bar)["root"] if 53 <= bar <= 68 else PEDAL


# --------------------------------------------------------------------------
# shared shaping helpers
# --------------------------------------------------------------------------

def sustained(tr, bars, key, vel_fn, rnd, gap=0.3, stagger=22, spread=8):
    """Lay a voicing across bars, merging neighbours that share it.

    Merging is what lets the strings hold one shape through three chord
    changes.  The gap at the end of each run matters: neighbouring voicings
    often share pitches, and without it the outgoing note-off would cut the
    incoming note short.
    """
    bars = list(bars)
    i = 0
    while i < len(bars):
        voicing = ch(bars[i])[key]
        j = i
        while (j + 1 < len(bars) and bars[j + 1] == bars[j] + 1
               and ch(bars[j + 1])[key] == voicing):
            j += 1
        start, end = T(bars[i]), T(bars[j] + 1)
        dur = end - start - B(gap)
        vel = vel_fn(bars[i])
        for k, p in enumerate(voicing):
            tr.note(start + k * stagger + rnd.randint(-spread, spread), dur,
                    p, vel - 3 * k + rnd.randint(-4, 4))
        i = j + 1


def swell(tr, first, last, lo, peak, curve=0.85, step=60, shape="arc"):
    """CC11 across a span.  "arc" blooms and fades; "rise" only grows."""
    start, end = T(first), T(last + 1)
    tick = start
    while tick <= end:
        u = (tick - start) / float(end - start)
        g = math.sin(math.pi * (u ** curve)) if shape == "arc" else u ** curve
        tr.cc(tick, 11, lo + (peak - lo) * g)
        tick += step
    tr.cc(end, 11, lo)


def drift(tr, first, last, lfos, step=48):
    """Slow pitch drift in semitones - analogue oscillators refusing to stay
    in tune.  Rates are chosen not to share factors, so the beating between
    two drifting parts never settles into a pattern."""
    start, end = T(first), T(last + 1)
    tick, last_val = start, None
    while tick <= end:
        # Deliberately clocked off a nominal 54 BPM rather than the tempo map:
        # a drifting oscillator does not know what the tempo is doing, and
        # tying the drift to the rubato would make it feel intentional.
        secs = tick / float(BEAT) * (60.0 / 54.0)
        semis = sum(d * math.sin(2 * math.pi * r * secs + ph)
                    for r, d, ph in lfos)
        val = tr.bend(tick, semis, BEND_RANGE)
        if val == last_val:
            tr.pop_last()
        else:
            last_val = val
        tick += step
    tr.bend(end, 0.0, BEND_RANGE)


# --------------------------------------------------------------------------
# the grand piano
# --------------------------------------------------------------------------
# (bar offset within the phrase, beat, duration in beats, pitch, velocity)

INTRO_THEME = [
    (0, 3.0, 2.0, 68, 46), (1, 1.0, 4.0, 73, 52),
    (2, 2.0, 3.0, 71, 48), (3, 1.0, 4.0, 68, 44),
]

THEME_A = [                                   # over LOOP_A
    (0, 3.0, 2.0, 68, 58),
    (1, 1.0, 3.0, 71, 64), (1, 4.0, 1.0, 73, 58),
    (2, 1.0, 4.0, 71, 62),
    (3, 1.0, 2.0, 68, 56), (3, 3.0, 2.0, 64, 52),
    (4, 1.0, 3.0, 66, 60), (4, 4.0, 1.0, 69, 56),
    (5, 1.0, 4.0, 73, 66),
    (6, 1.0, 3.0, 74, 70), (6, 4.0, 1.0, 73, 60),   # D natural: the bII
    (7, 1.0, 4.0, 69, 58),
]

THEME_A2 = [                                  # the same shape, higher
    (0, 1.0, 4.0, 73, 68),
    (1, 1.0, 3.0, 76, 74), (1, 4.0, 1.0, 75, 64),
    (2, 1.0, 4.0, 73, 70),
    (3, 1.0, 2.0, 71, 62), (3, 3.0, 2.0, 68, 58),
    (4, 1.0, 4.0, 69, 66),
    (5, 1.0, 3.0, 76, 76), (5, 4.0, 1.0, 78, 70),
    (6, 1.0, 4.0, 78, 78),
    (7, 1.0, 2.0, 74, 68), (7, 3.0, 2.0, 73, 62),
]

THEME_B = [                                   # over LOOP_B - the climax
    (0, 1.0, 4.0, 71, 66),
    (1, 1.0, 3.0, 80, 78), (1, 4.0, 1.0, 78, 68),
    (2, 1.0, 4.0, 78, 72),
    (3, 1.0, 2.0, 76, 66), (3, 3.0, 2.0, 71, 62),
    (4, 1.0, 4.0, 73, 72),
    (5, 1.0, 3.0, 80, 82), (5, 4.0, 1.0, 83, 76),
    (6, 1.0, 4.0, 81, 86),                          # apex
    (7, 1.0, 2.0, 80, 76), (7, 3.0, 2.0, 76, 68),
]

HOLOGRAM = [                                  # twelve bars, nearly empty
    (0, 1.0, 4.0, 73, 48), (1, 3.0, 2.0, 68, 42),
    (2, 1.0, 4.0, 64, 44), (3, 2.0, 3.0, 71, 46),
    (4, 1.0, 4.0, 78, 50), (5, 1.0, 2.0, 74, 44),
    (6, 1.0, 4.0, 73, 48), (7, 3.0, 2.0, 71, 42),
    (8, 1.0, 4.0, 73, 46), (9, 1.0, 2.0, 76, 44),
    (10, 1.0, 4.0, 78, 48), (11, 1.0, 4.0, 76, 44),
]

OUTRO = [
    (0, 1.0, 4.0, 68, 46), (1, 1.0, 4.0, 73, 48),
    (2, 2.0, 3.0, 71, 44), (3, 1.0, 4.0, 68, 40),
    (4, 1.0, 4.0, 64, 38), (5, 1.0, 6.0, 73, 42),
    (7, 1.0, 8.0, 61, 36),                          # the last note
]

MELODY_PLAN = [(5, INTRO_THEME), (9, THEME_A), (17, THEME_A2),
               (25, THEME_A), (33, THEME_A2), (41, HOLOGRAM),
               (53, THEME_B), (61, THEME_A2), (69, OUTRO)]

# which beats the right hand re-strikes, per section
COMP = {"rain": [1.0], "light": [1.0, 3.0], "wall": [1.0, 3.0],
        "hologram": [1.0], "ascension": [1.0, 3.0], "ashfall": [1.0]}


def melody_pitches_by_bar():
    out = collections.defaultdict(set)
    for first, phrase in MELODY_PLAN:
        for off, _beat, _dur, pitch, _vel in phrase:
            out[first + off].add(pitch)
    return out


def build_piano(tr, rnd, expressive_=True):
    melody = melody_pitches_by_bar()
    for bar in range(1, LAST_BAR + 1):
        c = ch(bar)
        sec = section_of(bar)
        base = {"rain": 40, "light": 50, "wall": 58,
                "hologram": 42, "ascension": 62, "ashfall": 40}[sec]
        if bar < 5:
            continue                       # the piano waits for the rain

        for k, p in enumerate(c["lh"]):
            tr.note(T(bar) + k * 16 + rnd.randint(-5, 5), B(3.9), p,
                    base - 6 + k * 3 + rnd.randint(-4, 4))

        # never double the melody in the comping hand: a pianist would not,
        # and the shared note would cut itself short at the first note-off
        voicing = [p for p in c["rh"] if p not in melody[bar]] or c["rh"][:2]
        beats = COMP[sec]
        for k, beat in enumerate(beats):
            nxt = beats[k + 1] if k + 1 < len(beats) else 5.0
            span = nxt - beat - 0.25
            vel = base if k == 0 else base - 9
            if beat == 1.0:
                for j, p in enumerate(voicing):
                    tr.note(T(bar, beat) + j * 24 + rnd.randint(-4, 4),
                            B(min(span, 3.6)), p,
                            vel + j * 2 + rnd.randint(-4, 4))
            else:
                for j, p in enumerate(voicing[1:]):
                    tr.note(T(bar, beat) + j * 10 + rnd.randint(-6, 6),
                            B(min(span, 1.6)), p,
                            vel - 10 + rnd.randint(-4, 4))

        if expressive_:
            tr.cc(T(bar) + 24, 64, 127)
            tr.cc(T(bar + 1) - 40, 64, 0)

    for first, phrase in MELODY_PLAN:
        for off, beat, dur, pitch, vel in phrase:
            tr.note(T(first + off, beat) + rnd.randint(-10, 10),
                    B(dur) - 24, pitch, vel + rnd.randint(-4, 4))


# --------------------------------------------------------------------------
# the CS-80 lead and the ondes wail
# --------------------------------------------------------------------------
# Both are two-bar notes butt-joined into unbroken lines, so every note
# change is a slide rather than an attack.

CS80_LINE = [                    # (bar, pitch, velocity)
    (29, 73, 74), (31, 69, 78), (33, 68, 82),
    (35, 71, 86), (37, 73, 90), (39, 74, 94),
    (53, 68, 70), (55, 66, 74), (57, 68, 80), (59, 69, 86),
    (61, 73, 92), (63, 76, 98), (65, 78, 104), (67, 74, 96),
]

ONDES_LINE = [
    (49, 85, 58), (51, 83, 54),
    (61, 85, 72), (63, 88, 80), (65, 90, 88), (67, 86, 78),
]

ONDES_VOICE = dict(
    vib_rate=5.4, vib_delay=0.70, vib_ramp=1.80,
    vib_base=0.14, vib_growth=0.24, vib_ref=B(6),
    scoop_depth=1.3, scoop_max=B(0.9), scoop_frac=0.20,
    glide_max=B(1.1), glide_frac=0.26, glide_exp=1.8,
    expr_base=26.0, atk_max=B(2.0), atk_frac=0.36,
    rel_max=B(2.6), rel_frac=0.45, breath_rate=0.30, tail=10,
)


def lead_notes(line):
    return [expressive.note(T(bar), B(8.0), pitch, vel)
            for bar, pitch, vel in line]


# --------------------------------------------------------------------------
# the low end
# --------------------------------------------------------------------------

def drone_runs():
    runs = []
    for bar in range(1, LAST_BAR + 1):
        p = bass_root(bar)
        if runs and runs[-1][1] == bar - 1 and runs[-1][2] == p:
            runs[-1][1] = bar
        else:
            runs.append([bar, bar, p])
    return runs


def build_drone(tr, rnd, expressive_=True):
    """The pedal.  One continuous note per root, overlapping into the next,
    so the low end never stops for the length of the piece."""
    runs = drone_runs()
    for i, (first, last, p) in enumerate(runs):
        start = T(first)
        end = T(last + 1) + (B(1.0) if i + 1 < len(runs) else B(6.0))
        vel = 54 if section_of(first) in ("rain", "hologram", "ashfall") else 74
        tr.note(start, end - start, p, vel - 12 + rnd.randint(-3, 3))
        tr.note(start + 9, end - start, p + 12, vel + rnd.randint(-3, 3))

    if not expressive_:
        return
    # very slow, very shallow: this is the floor of the mix moving under
    # everything else, not an effect you should be able to point at
    drift(tr, 1, LAST_BAR, ((0.047, 0.09, 0.0), (0.031, 0.06, 1.7)))
    swell(tr, 1, 8, 12, 70, shape="rise")
    swell(tr, 9, 40, 70, 104, shape="rise")
    swell(tr, 41, 52, 46, 66)
    swell(tr, 53, 68, 78, 120, shape="rise")
    swell(tr, 69, LAST_BAR, 60, 4, shape="rise")


def build_pulse(tr, rnd):
    """A machine heartbeat, not a groove: two throbs a bar, no backbeat."""
    for first, last, vel in ((13, 24, 74), (25, 40, 92),
                             (53, 60, 96), (61, 68, 108)):
        for bar in range(first, last + 1):
            p = bass_root(bar)
            tr.note(T(bar) + rnd.randint(-6, 6), B(1.6), p, vel)
            tr.note(T(bar, 3.0) + rnd.randint(-6, 6), B(1.2), p, vel - 22)
            if bar >= 61:
                tr.note(T(bar, 4.5) + rnd.randint(-4, 4), B(0.4), p, vel - 34)


# --------------------------------------------------------------------------
# the wall
# --------------------------------------------------------------------------

def build_brass(tr, rnd, expressive_=True):
    """Open fifths, no thirds - the chord identity comes from the strings.
    Fifths at this width just sound like mass."""
    def vel(bar):
        return 58 if bar <= 40 else 74
    sustained(tr, range(25, 41), "brass", vel, rnd, gap=0.35, stagger=30)
    sustained(tr, range(57, 69), "brass", vel, rnd, gap=0.35, stagger=30)
    if not expressive_:
        return
    drift(tr, 25, 40, ((0.083, 0.14, 0.4), (0.129, 0.10, 2.9)))
    drift(tr, 57, 68, ((0.083, 0.17, 0.4), (0.129, 0.12, 2.9)))
    swell(tr, 25, 32, 8, 96)
    swell(tr, 33, 40, 14, 112)
    swell(tr, 57, 62, 10, 108, shape="rise")
    swell(tr, 63, 68, 40, 127, shape="rise")


def build_strings(tr, rnd, expressive_=True):
    def vel(bar):
        return {"light": 44, "wall": 58, "ascension": 70}.get(
            section_of(bar), 40)
    sustained(tr, range(17, 41), "strings", vel, rnd)
    sustained(tr, range(53, 69), "strings", vel, rnd)
    sustained(tr, range(69, 73), "strings", vel, rnd)
    if expressive_:
        swell(tr, 17, 24, 16, 80)
        swell(tr, 25, 40, 30, 110, shape="rise")
        swell(tr, 53, 68, 34, 124, shape="rise")
        swell(tr, 69, 72, 70, 6, shape="rise")


def build_cello(tr, rnd, expressive_=True):
    def vel(bar):
        return 62 if 53 <= bar <= 68 else 50
    sustained(tr, range(25, 41), "cello", vel, rnd, gap=0.4)
    sustained(tr, range(53, 69), "cello", vel, rnd, gap=0.4)
    sustained(tr, range(69, 77), "cello", vel, rnd, gap=0.4)
    if expressive_:
        swell(tr, 25, 40, 24, 96, shape="rise")
        swell(tr, 53, 68, 40, 118, shape="rise")
        swell(tr, 69, LAST_BAR, 74, 4, shape="rise")


def build_choir(tr, rnd, expressive_=True):
    def vel(bar):
        return 56 if 53 <= bar <= 68 else 44
    sustained(tr, range(29, 41), "choir", vel, rnd, gap=0.4, stagger=34)
    sustained(tr, range(53, 69), "choir", vel, rnd, gap=0.4, stagger=34)
    sustained(tr, range(69, 73), "choir", vel, rnd, gap=0.4, stagger=34)
    if expressive_:
        swell(tr, 29, 40, 10, 92)
        swell(tr, 53, 68, 24, 118, shape="rise")
        swell(tr, 69, 72, 66, 4, shape="rise")


# --------------------------------------------------------------------------
# percussion
# --------------------------------------------------------------------------

KICK, LOW_TOM, MID_TOM = 36, 41, 45
CRASH, CHINESE, SPLASH = 49, 52, 55

TAIKO_LOW, TAIKO_HIGH = 30, 37


def build_percussion(tr, rnd):
    """Enormous and rare.  No kit pattern - just impacts and air."""
    def hit(bar, beat, pitch, vel, dur=1.0):
        tr.note(T(bar, beat) + rnd.randint(-8, 8), B(dur), pitch,
                vel + rnd.randint(-4, 4))

    for bar in range(25, 41, 2):
        hit(bar, 1.0, KICK, 96, dur=0.8)
    for bar in range(53, 69):
        hit(bar, 1.0, KICK, 104, dur=0.8)
        if bar >= 61:
            hit(bar, 3.0, KICK, 78, dur=0.6)
    for bar in (29, 37, 57, 65):
        hit(bar, 3.0, LOW_TOM, 82, dur=1.4)
    for bar, vel in ((25, 72), (41, 54), (53, 88), (61, 104)):
        hit(bar, 1.0, CRASH, vel, dur=4.0)
    hit(33, 1.0, CHINESE, 70, dur=4.0)
    hit(65, 1.0, CHINESE, 96, dur=4.0)
    hit(69, 1.0, SPLASH, 60, dur=4.0)


def build_taiko(tr, rnd):
    for bar in range(25, 41, 4):
        tr.note(T(bar) + rnd.randint(-10, 10), B(2.0), TAIKO_LOW, 96)
        tr.note(T(bar, 3.0) + rnd.randint(-10, 10), B(1.5), TAIKO_HIGH, 74)
    for bar in range(53, 69, 2):
        tr.note(T(bar) + rnd.randint(-10, 10), B(2.0), TAIKO_LOW, 110)
        if bar >= 61:
            tr.note(T(bar, 3.5) + rnd.randint(-8, 8), B(1.0), TAIKO_HIGH, 84)
    tr.note(T(69), B(3.0), TAIKO_LOW, 88)


def build_timpani(tr, rnd):
    """Rolls that arrive on a downbeat, plus single hits on the bII."""
    for bar in (24, 40, 52, 60, 68):
        ratchet(tr, T(bar, 3.0), B(2.0), ch(bar)["timp"], 76, 16)
    for bar in (31, 39, 67):                 # the Neapolitan, marked
        tr.note(T(bar) + rnd.randint(-8, 8), B(3.0), ch(bar)["timp"], 88)
    for bar in (25, 53, 61):
        tr.note(T(bar) + rnd.randint(-6, 6), B(3.5), ch(bar)["timp"], 96)


def build_reverse(tr):
    """Swells that resolve on the downbeat they lead into."""
    for bar, vel, beats in ((9, 54, 2.0), (17, 60, 2.0), (25, 88, 4.0),
                            (41, 62, 2.0), (53, 92, 4.0), (61, 104, 4.0),
                            (69, 56, 2.0)):
        tr.note(T(bar) - B(beats), B(beats), 72, vel)


# --------------------------------------------------------------------------
# hologram flicker - the one glitch element, and it belongs to the story
# --------------------------------------------------------------------------

def build_flicker(tr, rnd, grnd, expressive_=True):
    """A projection failing to hold. Restrained everywhere but the breakdown."""
    for bar in (24, 40, 68):                 # a stutter at the seams
        stutter(tr, T(bar, 4.0), 85, 56, 5, SIXTEENTH,
                decay=0.82, accel=0.84)

    for bar in range(41, 53):
        if bar % 2:
            stutter(tr, T(bar, 2.5), 85 + rnd.choice((0, 3, 7)), 52, 4,
                    THIRTYSECOND * 2, decay=0.8, accel=0.8)
        else:
            ratchet(tr, T(bar, 3.5), B(1.0), 88 + rnd.choice((0, -3)), 46, 6,
                    rising=False)
        if expressive_ and bar in (44, 48, 52):
            pitch_glitch(tr, T(bar, 1.0), T(bar, 2.5), 9, grnd, spread=6.0)

    # one last failure as the piece ends
    stutter(tr, T(74, 3.0), 85, 40, 6, SIXTEENTH, decay=0.74, accel=0.88)


def build_rain(tr, rnd, expressive_=True):
    """A continuous wash under the whole piece - the one thing that never
    stops.  Re-struck every eight bars, just short of overlapping itself."""
    for bar in range(1, LAST_BAR + 1, 8):
        # the last block is clipped: at the closing tempo an extra two bars
        # of rain alone costs the better part of a minute
        dur = min(B(31.4), T(79) - T(bar))
        tr.note(T(bar), dur, 60, 30 + rnd.randint(-3, 3))
        tr.note(T(bar) + 24, dur - 8, 67, 26 + rnd.randint(-3, 3))
    if expressive_:
        swell(tr, 1, 8, 40, 88, shape="rise")
        swell(tr, 9, 40, 74, 52)
        swell(tr, 41, 52, 52, 96)
        swell(tr, 53, 68, 60, 40)
        swell(tr, 69, LAST_BAR, 56, 100, shape="rise")


# --------------------------------------------------------------------------
# tempo
# --------------------------------------------------------------------------

def build_tempo_map():
    tm = [(T(1), 50.0), (T(5), 52.0), (T(9), 54.0), (T(25), 54.0),
          (T(41), 51.0), (T(53), 56.0), (T(61), 57.0), (T(69), 53.0),
          (T(73), 50.0)]
    for k in range(12):                      # the closing ritardando
        u = k / 11.0
        tm.append((T(74) + k * (BEAT // 2), 49.0 - 21.0 * (u ** 1.5)))
    tm.append((T(77), 28.0))
    tm.sort(key=lambda x: x[0])
    return tm


def build_conductor(tempo_map):
    tr = Track("Ashfall - Conductor")
    tr.text(0, 0x03, "Ashfall - Conductor")
    tr.text(0, 0x02, "Ashfall - cinematic ballad in C# minor")
    tr.meta(0, 0x58, bytes([4, 2, 24, 8]))               # 4/4
    tr.meta(0, 0x59, bytes([4, 1]))                      # sf=+4 (4 sharps), minor
    for tick, bpm in tempo_map:
        tempo_meta(tr, tick, bpm)
    for name, first, _last in SECTIONS:
        tr.text(T(first), 0x06, name.title())
    return tr


# --------------------------------------------------------------------------
# assembly
# --------------------------------------------------------------------------

def build(expressive_=True, seed=204977):
    rnd = random.Random(seed)
    grnd = random.Random(seed ^ 0x2049)      # controller-only randomness
    tempo_map = build_tempo_map()
    t2s = make_tick_to_sec(tempo_map)

    conductor = build_conductor(tempo_map)

    piano = Track("Grand Piano", 0, "Acoustic Grand Piano")
    cs80 = Track("CS-80 Lead", 1, "SynthBrass 1")
    brass = Track("Brass Wall", 2, "SynthBrass 2")
    drone = Track("Sub Drone", 3, "Pad 2 (warm)")
    pulse = Track("Sub Pulse", 4, "Synth Bass 1")
    choir = Track("Choir", 5, "Choir Aahs")
    strings = Track("Strings", 6, "String Ensemble 1")
    cello = Track("Cellos", 7, "Cello")
    ondes = Track("Ondes Wail", 8, "Lead 6 (voice)")
    perc = Track("Impacts", 9, "Standard Kit")
    taiko = Track("Taiko", 10, "Taiko Drum")
    timp = Track("Timpani", 11, "Timpani")
    rev = Track("Reverse Swells", 12, "Reverse Cymbal")
    flicker = Track("Hologram Flicker", 13, "FX 8 (sci-fi)")
    rain = Track("Rain Bed", 14, "Seashore")

    piano.voice(0, 110, 64, reverb=96, chorus=10)
    cs80.voice(62, 96, 58, reverb=118, chorus=64)
    brass.voice(63, 104, 70, reverb=124, chorus=72)
    drone.voice(89, 112, 64, reverb=64, chorus=40)
    pulse.voice(38, 100, 64, reverb=30, chorus=0)
    choir.voice(52, 76, 46, reverb=127, chorus=52)
    strings.voice(48, 88, 78, reverb=122, chorus=44)
    cello.voice(42, 84, 52, reverb=112, chorus=32)
    ondes.voice(85, 82, 88, reverb=127, chorus=56)
    perc.voice(0, 100, 64, reverb=110, chorus=0)
    taiko.voice(116, 106, 64, reverb=104, chorus=0)
    timp.voice(47, 92, 56, reverb=112, chorus=0)
    rev.voice(119, 84, 64, reverb=127, chorus=32)
    flicker.voice(103, 62, 100, reverb=96, chorus=40)
    rain.voice(122, 52, 64, reverb=127, chorus=24)

    if expressive_:
        for tr in (cs80, brass, drone, ondes, flicker):
            tr.bend_range(BEND_RANGE)

    build_piano(piano, rnd, expressive_)
    expressive.render(cs80, lead_notes(CS80_LINE), t2s,
                      expressive.Voice(**expressive.CS80), expressive_)
    expressive.render(ondes, lead_notes(ONDES_LINE), t2s,
                      expressive.Voice(**ONDES_VOICE), expressive_)
    build_brass(brass, rnd, expressive_)
    build_drone(drone, rnd, expressive_)
    build_pulse(pulse, rnd)
    build_choir(choir, rnd, expressive_)
    build_strings(strings, rnd, expressive_)
    build_cello(cello, rnd, expressive_)
    build_percussion(perc, rnd)
    build_taiko(taiko, rnd)
    build_timpani(timp, rnd)
    build_reverse(rev)
    build_flicker(flicker, rnd, grnd, expressive_)
    build_rain(rain, rnd, expressive_)

    tracks = [conductor, piano, cs80, brass, drone, pulse, choir, strings,
              cello, ondes, perc, taiko, timp, rev, flicker, rain]
    return tracks, tempo_map, t2s


def main():
    ap = argparse.ArgumentParser(description="Generate the Ashfall MIDI.")
    ap.add_argument("-o", "--out", default=None, help="output .mid path")
    ap.add_argument("--clean", action="store_true",
                    help="omit pitch bend / CC data (notes and tempo only)")
    args = ap.parse_args()

    here = os.path.dirname(os.path.abspath(__file__))
    default = os.path.join(here, os.pardir, "midi",
                           "ashfall_clean.mid" if args.clean else "ashfall.mid")
    out = os.path.abspath(args.out or default)

    tracks, _tempo_map, t2s = build(expressive_=not args.clean)
    write_smf(out, tracks)

    end = max(tr.end_tick() for tr in tracks)
    secs = t2s(end)
    print("wrote %s" % out)
    print("  tracks %d   notes %d   events %d   %.1f KB"
          % (len(tracks), sum(tr.note_count() for tr in tracks),
             sum(tr.event_count() for tr in tracks),
             os.path.getsize(out) / 1024.0))
    print("  length %d bars, %d:%02d" % (end // BAR + 1, int(secs) // 60,
                                         int(secs) % 60))


if __name__ == "__main__":
    main()
