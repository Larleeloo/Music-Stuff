#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
"Static Bloom" - a sad glitch-pop ballad built around a grand piano.

Generates a Standard MIDI File (format 1, 480 PPQ) for FL Studio 2025.
Pure standard library: no external dependencies.

The piano is the song.  It plays a real part - rolled voicings, a top-line
melody, pedalling, and velocity that moves - and everything electronic is
arranged around it rather than on top of it.  The glitch vocabulary is written
into the note data itself, so it survives the export:

  * stutters     retriggered notes at 1/16 -> 1/32 -> 1/64, accelerating and
                 decaying, on phrase ends and section seams
  * ratchets     subdivided bursts with velocity ramps (hats, bells)
  * gating       sustained pad chopped into a 16th-note on/off pattern
  * tape stops   pitch bend falling on an accelerating curve, doubled by a
                 real tempo ritardando so the whole grid drags to a halt
  * beat repeat  one 16th slice of a bar re-fired across the last beat
  * pitch glitch stair-stepped bend jumps, like a sampler losing its place
  * 808 glides   pitch bend sliding into each new bass root
  * sidechain    CC11 ducking curves keyed to the kick, so the electronics
                 breathe against the piano

Form (76 bars, 4/4, 76 BPM with a tape stop at 48 and a ritardando at the end):

    bars  1- 8  Intro       solo grand piano, first stutter at the seam
    bars  9-24  Verse 1     808 + Rhodes join; drums enter at 13
    bars 25-40  Chorus 1    gated pad, bells, full kit
    bars 41-48  Breakdown   the glitch zone; drums out, tape stop at 48
    bars 49-56  Verse 2     sparser, more electronic than the first
    bars 57-68  Chorus 2    biggest; square-wave counter-melody, beat repeat
    bars 69-76  Outro       back to solo piano, one last stutter, tape stop

Key is F minor throughout: i - VI - III - VII in the verses, VI - VII - v - i
in the choruses, with a borrowed Gb major in the breakdown.

Usage:
    python3 generate_static_bloom.py             # full version
    python3 generate_static_bloom.py --clean     # notes only, no controllers
"""

import argparse
import bisect
import collections
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from smf import (BAR, BEAT, B, P_SETUP, T, Track,  # noqa: E402
                 make_tick_to_sec, tempo_meta, write_smf)

SIXTEENTH = BEAT // 4
THIRTYSECOND = BEAT // 8

# --------------------------------------------------------------------------
# harmony - F minor
# --------------------------------------------------------------------------
# Each entry carries a ready-made voicing per instrument so the arrangement
# code never has to think about spelling chords.
#   sub    808 root          lh/rh  grand piano left and right hand
#   rhodes electric piano    pad    wordless voice pad
#   bells  ascending pool for arpeggios and ratchets

CHORDS = {
    "Fm9":     dict(sub=29, lh=[41, 48], rh=[56, 60, 63, 67],
                    rhodes=[56, 60, 63, 67], pad=[63, 68, 72],
                    bells=[72, 75, 79, 80, 84, 87]),
    "Dbmaj7":  dict(sub=25, lh=[37, 44], rh=[53, 56, 60, 65],
                    rhodes=[53, 56, 60, 65], pad=[60, 65, 72],
                    bells=[68, 72, 77, 80, 84, 89]),
    "Abadd9":  dict(sub=32, lh=[44, 51], rh=[58, 60, 63, 68],
                    rhodes=[58, 63, 68, 72], pad=[63, 68, 75],
                    bells=[68, 70, 75, 79, 82, 87]),
    "Ebadd9":  dict(sub=27, lh=[39, 46], rh=[55, 58, 63, 65],
                    rhodes=[55, 58, 65, 70], pad=[65, 70, 75],
                    bells=[70, 75, 77, 82, 87, 89]),
    "Bbm7":    dict(sub=34, lh=[46, 53], rh=[56, 61, 65, 68],
                    rhodes=[56, 61, 65, 70], pad=[61, 65, 70],
                    bells=[73, 77, 80, 82, 85, 89]),
    "Cm7":     dict(sub=36, lh=[48, 55], rh=[58, 63, 67, 70],
                    rhodes=[58, 63, 67, 72], pad=[63, 67, 70],
                    bells=[72, 75, 79, 82, 84, 87]),
    "Gbmaj7":  dict(sub=30, lh=[42, 49], rh=[58, 61, 65, 70],
                    rhodes=[58, 61, 65, 70], pad=[61, 65, 70],
                    bells=[70, 73, 77, 82, 85, 89]),
}

VERSE = ["Fm9", "Dbmaj7", "Abadd9", "Ebadd9"]        # i  - VI  - III - VII
CHORUS = ["Dbmaj7", "Ebadd9", "Cm7", "Fm9"]          # VI - VII - v   - i
BRIDGE = ["Gbmaj7", "Fm9", "Dbmaj7", "Cm7"]          # borrowed bII

PROG = {}


def _lay(first, names):
    for i, n in enumerate(names):
        PROG[first + i] = n


for b in (1, 5, 9, 13, 17, 21, 49, 53, 69):
    _lay(b, VERSE)
for b in (25, 29, 33, 37, 57, 61, 65):
    _lay(b, CHORUS)
_lay(41, BRIDGE)
_lay(45, ["Gbmaj7", "Fm9", "Dbmaj7", "Ebadd9"])
_lay(73, ["Fm9", "Dbmaj7", "Fm9", "Fm9"])

LAST_BAR = 76


def ch(bar):
    return CHORDS[PROG[bar]]


# --------------------------------------------------------------------------
# glitch vocabulary
# --------------------------------------------------------------------------

def stutter(tr, tick, pitch, vel, count, step, decay=0.87, accel=1.0,
            gate=0.88):
    """Retrigger one pitch.  accel < 1 speeds the repeats up (a ratcheting
    stutter); decay fades them.  Returns the tick after the last repeat."""
    t, s, v = float(tick), float(step), float(vel)
    for _ in range(count):
        # the note must always end inside its own step, however far accel has
        # shrunk it, or the repeats collide and truncate each other
        tr.note(t, min(s * gate, max(2.0, s - 2.0)), pitch, v)
        t += s
        s *= accel
        v *= decay
    return t


def ratchet(tr, tick, span, pitch, vel, divs, rising=True):
    """Subdivide `span` into `divs` hits with a velocity ramp."""
    step = span / float(divs)
    for i in range(divs):
        u = i / max(1.0, divs - 1.0)
        v = vel * (0.5 + 0.5 * u) if rising else vel * (1.0 - 0.5 * u)
        tr.note(tick + i * step, step * 0.85, pitch, v)


def steps(pattern):
    """'1..1' -> [0, 3].  Patterns are one bar of sixteenths."""
    assert len(pattern) == 16, "pattern must be 16 sixteenths: %r" % pattern
    return [i for i, c in enumerate(pattern) if c == "1"]


def gate_bar(tr, bar, pitches, pattern, vel, rnd):
    """Chop a sustained voicing into a rhythmic on/off figure."""
    for i in steps(pattern):
        t = T(bar) + i * SIXTEENTH
        for j, p in enumerate(pitches):
            tr.note(t + j * 3, SIXTEENTH * 0.92, p,
                    vel - 4 * j + rnd.randint(-4, 4))


def tape_stop(tr, start, end, depth=-11.5, curve=2.4, steps_=56):
    """Pitch falling away on an accelerating curve, then back to centre."""
    for k in range(steps_ + 1):
        u = k / float(steps_)
        tr.bend(start + u * (end - start), depth * (u ** curve))
    tr.bend(end + 4, 0.0)


def pitch_glitch(tr, start, end, count, rnd, spread=5.0):
    """Stair-stepped bend jumps - a sampler losing its place."""
    choices = [-spread, -spread * 0.5, 0.0, spread * 0.5, spread, spread * 1.4]
    for k in range(count):
        tr.bend(start + (end - start) * k / float(count), rnd.choice(choices))
    tr.bend(end, 0.0)


def sidechain(tr, kick_ticks, start, end, depth=0.70, tau=210.0, step=24):
    """CC11 ducking keyed to the kick, so the electronics pump under it."""
    ks = sorted(kick_ticks)
    if not ks:
        return
    t = start
    while t <= end:
        i = bisect.bisect_right(ks, t) - 1
        duck = depth * math.exp(-(t - ks[i]) / tau) if i >= 0 else 0.0
        tr.cc(t, 11, 100.0 * (1.0 - duck))
        t += step
    tr.cc(end, 11, 100)


def sweep(tr, start, end, lo, hi, step=48):
    """CC74 brightness sweep - a filter opening or closing."""
    n = max(1, (end - start) // step)
    for k in range(n + 1):
        u = k / float(n)
        tr.cc(start + k * step, 74, lo + (hi - lo) * u)


# --------------------------------------------------------------------------
# the grand piano
# --------------------------------------------------------------------------
# (bar offset within the phrase, beat, duration in beats, pitch, velocity)

PHRASE_A = [
    (0, 2.0, 1.0, 68, 70), (0, 3.0, 2.0, 72, 76),
    (1, 1.0, 1.5, 73, 80), (1, 2.5, 0.5, 72, 68), (1, 3.0, 2.0, 68, 72),
    (2, 1.0, 1.0, 75, 78), (2, 2.0, 1.0, 72, 70), (2, 3.0, 2.0, 70, 74),
    (3, 1.0, 2.0, 67, 70), (3, 3.0, 1.0, 70, 68), (3, 4.0, 1.0, 72, 72),
]

PHRASE_A2 = [                       # the lift: same shape, higher
    (0, 1.0, 1.5, 72, 78), (0, 2.5, 1.5, 75, 82), (0, 4.0, 1.0, 77, 80),
    (1, 1.0, 2.0, 80, 88), (1, 3.0, 1.0, 79, 78), (1, 4.0, 1.0, 77, 76),
    (2, 1.0, 2.5, 75, 82), (2, 3.5, 0.5, 77, 70), (2, 4.0, 1.0, 75, 74),
    (3, 1.0, 3.0, 72, 76), (3, 4.0, 1.0, 70, 68),
]

PHRASE_A3 = [                       # the descent, left hanging on the 9th
    (0, 2.0, 1.0, 68, 66), (0, 3.0, 2.0, 72, 72),
    (1, 1.0, 1.5, 73, 76), (1, 2.5, 0.5, 72, 64), (1, 3.0, 2.0, 68, 68),
    (2, 1.0, 2.0, 70, 70), (2, 3.0, 2.0, 68, 66),
    (3, 1.0, 2.0, 67, 66), (3, 3.0, 2.0, 65, 62),
]

PHRASE_CHORUS = [                   # eight bars over VI - VII - v - i, twice
    (0, 1.0, 1.5, 77, 86), (0, 2.5, 1.5, 80, 90), (0, 4.0, 1.0, 84, 88),
    (1, 1.0, 3.0, 82, 94), (1, 4.0, 1.0, 80, 82),
    (2, 1.0, 2.0, 79, 86), (2, 3.0, 2.0, 75, 80),
    (3, 1.0, 2.5, 77, 84), (3, 3.5, 0.5, 75, 72), (3, 4.0, 1.0, 72, 76),
    (4, 1.0, 1.5, 77, 88), (4, 2.5, 1.5, 80, 92), (4, 4.0, 1.0, 85, 94),
    (5, 1.0, 3.5, 84, 100),                       # apex
    (6, 1.0, 2.0, 82, 92), (6, 3.0, 2.0, 79, 84),
    (7, 1.0, 2.5, 80, 88), (7, 3.5, 0.5, 79, 74), (7, 4.0, 1.0, 77, 78),
]

PHRASE_BRIDGE = [                   # fragments; the glitches finish the lines
    (0, 1.0, 1.0, 77, 78), (0, 3.0, 1.0, 82, 74),
    (1, 1.0, 2.0, 80, 76),
    (2, 2.0, 1.0, 77, 70),
    (3, 1.0, 2.0, 75, 72),
    (4, 1.0, 1.0, 82, 80), (4, 2.5, 0.5, 85, 76),
    (5, 1.0, 3.0, 80, 78),
    (6, 1.0, 2.0, 84, 82),
    (7, 1.0, 4.0, 82, 76),
]

PHRASE_OUTRO = [
    (0, 1.0, 2.0, 68, 62), (0, 3.0, 2.0, 72, 66),
    (1, 1.0, 4.0, 73, 64),
    (2, 1.0, 3.0, 68, 58),
    (3, 1.0, 4.0, 65, 52),
]

# where each melodic phrase starts, and which glitch echo treatment it gets
MELODY_PLAN = [
    (5, PHRASE_A), (9, PHRASE_A), (13, PHRASE_A2), (17, PHRASE_A),
    (21, PHRASE_A3), (25, PHRASE_CHORUS), (33, PHRASE_CHORUS),
    (41, PHRASE_BRIDGE), (49, PHRASE_A), (53, PHRASE_A3),
    (57, PHRASE_CHORUS), (65, PHRASE_CHORUS[:10]), (69, PHRASE_A3),
    (73, PHRASE_OUTRO),
]

# comping rhythm per section: which beats the right hand re-strikes
COMP = {
    "intro": [1.0, 3.0],
    "verse": [1.0, 2.5, 4.0],
    "chorus": [1.0, 2.5, 3.5],
    "bridge": [1.0],
    "outro": [1.0],
}


def section_of(bar):
    if bar <= 8:
        return "intro"
    if bar <= 24:
        return "verse"
    if bar <= 40:
        return "chorus"
    if bar <= 48:
        return "bridge"
    if bar <= 56:
        return "verse"
    if bar <= 68:
        return "chorus"
    return "outro"


def roll(tr, tick, pitches, vel, dur, rnd, spread=16):
    """Arpeggiate a voicing the way a hand does - bottom up, slightly uneven."""
    for j, p in enumerate(pitches):
        tr.note(tick + j * spread + rnd.randint(-3, 3), dur, p,
                vel + j * 2 + rnd.randint(-4, 4))


def melody_pitches_by_bar():
    """A pianist does not double the tune in the comping hand, and a doubled
    pitch would also cut itself short - the first note-off stops both."""
    out = collections.defaultdict(set)
    for first, phrase in MELODY_PLAN:
        for off, _beat, _dur, pitch, _vel in phrase:
            out[first + off].add(pitch)
    return out


def build_piano(tr, rnd, expressive=True):
    """Left hand, comping right hand, pedal - the melody is added separately."""
    melody = melody_pitches_by_bar()
    for bar in range(1, LAST_BAR + 1):
        c = ch(bar)
        sec = section_of(bar)
        base = {"intro": 52, "verse": 56, "chorus": 64,
                "bridge": 50, "outro": 46}[sec]

        # left hand: root and fifth, let the pedal hold them
        for j, p in enumerate(c["lh"]):
            tr.note(T(bar) + j * 14 + rnd.randint(-4, 4), B(3.9), p,
                    base - 4 + j * 3 + rnd.randint(-4, 4))

        voicing = [p for p in c["rh"] if p not in melody[bar]] or c["rh"][:2]

        # right hand comping.  Each strike is cut off just before the next one
        # so a repeated pitch never truncates itself; the pedal holds the sound.
        beats = COMP[sec]
        for k, beat in enumerate(beats):
            nxt = beats[k + 1] if k + 1 < len(beats) else 5.0
            span = nxt - beat - 0.25
            vel = base - 10 if k else base
            if beat == 1.0:
                roll(tr, T(bar, beat), voicing, vel, B(min(span, 3.6)), rnd)
            else:
                for j, p in enumerate(voicing[1:]):
                    tr.note(T(bar, beat) + j * 8 + rnd.randint(-6, 6),
                            B(min(span, 0.8)), p, vel - 12 + rnd.randint(-5, 5))

        if expressive:
            # pedal down just after the chord lands, up just before the next
            tr.cc(T(bar) + 24, 64, 127)
            tr.cc(T(bar + 1) - 36, 64, 0)

    for first, phrase in MELODY_PLAN:
        for off, beat, dur, pitch, vel in phrase:
            tr.note(T(first + off, beat) + rnd.randint(-9, 9), B(dur) - 20,
                    pitch, vel + rnd.randint(-5, 5))


# --------------------------------------------------------------------------
# glitch piano - chopped echoes of the grand, one eighth behind
# --------------------------------------------------------------------------

ECHO_SOURCES = [(13, PHRASE_A2), (25, PHRASE_CHORUS), (33, PHRASE_CHORUS),
                (57, PHRASE_CHORUS), (65, PHRASE_CHORUS[:10])]


def build_glitch_piano(tr, rnd, grnd, expressive=True):
    # Echoes can pile onto a pitch that is still ringing, which would make the
    # first note-off cut the second short.  Track when each pitch frees up and
    # push a colliding echo an octave clear, or drop it.
    busy = {}

    def echo(tick, pitch, vel, count, step, decay, accel):
        for cand in (pitch, pitch + 12):
            if busy.get(cand, -1) <= tick:
                end = stutter(tr, tick, cand, vel, count, step,
                              decay=decay, accel=accel)
                busy[cand] = end
                return

    for first, phrase in ECHO_SOURCES:
        for idx, (off, beat, dur, pitch, vel) in enumerate(phrase):
            if idx % 3:                       # only every third note echoes
                continue
            t = T(first + off, beat) + B(0.5)
            up = 12 if rnd.random() < 0.4 else 0
            echo(t, pitch + up, vel * 0.44, 3, THIRTYSECOND * 2, 0.78, 0.82)

    # the seams: a stutter that accelerates into the next section
    for bar, count, pitch in ((8, 6, 72), (24, 8, 75), (40, 10, 80),
                              (56, 8, 77), (68, 12, 84)):
        c = ch(bar)
        echo(T(bar, 4.0), pitch, 82, count, SIXTEENTH, 0.90, 0.80)
        echo(T(bar, 4.0) + 40, c["rh"][1], 54, max(3, count // 2),
             SIXTEENTH * 2, 0.85, 0.85)

    # the glitch zone: the piano fragments come apart
    for bar in range(41, 49):
        c = ch(bar)
        if bar % 2:
            stutter(tr, T(bar, 2.5), c["bells"][2], 70, 5, THIRTYSECOND * 3,
                    decay=0.86, accel=0.78)
        else:
            ratchet(tr, T(bar, 3.0), B(1.0), c["rh"][2], 64, 6)
        if expressive and bar in (43, 47):
            pitch_glitch(tr, T(bar, 3.0), T(bar, 4.5), 10, grnd, spread=4.0)

    # outro: the last phrase disintegrates
    stutter(tr, T(75, 3.0), 68, 60, 7, SIXTEENTH, decay=0.80, accel=0.86)


# --------------------------------------------------------------------------
# electronics
# --------------------------------------------------------------------------

SUB_BARS = list(range(9, 49)) + list(range(49, 69)) + [69, 70, 71, 72]


def build_sub(tr, rnd, expressive=True):
    """808-style sub: one long root per bar, gliding into each new pitch."""
    prev = None
    for bar in sorted(set(SUB_BARS)):
        p = ch(bar)["sub"]
        sec = section_of(bar)
        vel = {"verse": 96, "chorus": 108, "bridge": 88, "outro": 74}.get(sec, 90)
        ghost = None
        if sec == "chorus" and bar % 2 == 0:
            ghost = 3.75
        elif sec == "verse" and bar % 4 == 3:
            ghost = 4.5
        dur = B(3.7) if sec != "bridge" else B(3.2)
        if ghost is not None:
            # stop the root before its own ghost, or the ghost gets cut short
            dur = min(dur, B(ghost - 1.0 - 0.15))
        tr.note(T(bar), dur, p, vel + rnd.randint(-4, 4))
        if expressive and prev is not None and prev != p:
            # slide into the new root from the old one
            delta = max(-11.5, min(11.5, prev - p))
            for k in range(13):
                u = k / 12.0
                tr.bend(T(bar) + u * B(0.28), delta * (1.0 - u) ** 1.8)
            tr.bend(T(bar) + B(0.30), 0.0)
        prev = p
        # syncopated ghost hit, trap-style
        if ghost is not None:
            tr.note(T(bar, ghost), B(0.7 if ghost < 4.0 else 0.4), p,
                    vel - (26 if ghost < 4.0 else 34))


def build_rhodes(tr, rnd):
    for bar in list(range(9, 49)) + list(range(49, 69)):
        c = ch(bar)
        sec = section_of(bar)
        vel = 54 if sec == "verse" else 62
        if sec == "bridge":
            vel = 44
        for j, p in enumerate(c["rhodes"]):
            tr.note(T(bar) + j * 10 + rnd.randint(-5, 5), B(3.8), p,
                    vel - 3 * j + rnd.randint(-4, 4))


GATE_A = "1.1.11..1.1.1..1"
GATE_B = "1.111..11.1.11.1"


def build_pad(tr, rnd):
    # verses: sustained, ducked by the sidechain
    for first, last in ((9, 24), (49, 56)):
        bar = first
        while bar <= last:
            c = ch(bar)
            for j, p in enumerate(c["pad"]):
                tr.note(T(bar) + j * 20, B(3.9), p, 46 - 3 * j + rnd.randint(-4, 4))
            bar += 1
    # choruses: chopped into a gate pattern
    for bar in list(range(25, 41)) + list(range(57, 69)):
        pat = GATE_B if bar % 4 == 3 else GATE_A
        gate_bar(tr, bar, ch(bar)["pad"], pat, 58, rnd)
    # breakdown: one long smear, no rhythm at all
    for bar in (41, 45):
        for j, p in enumerate(ch(bar)["pad"]):
            tr.note(T(bar) + j * 30, B(15.5), p, 40 - 3 * j)


def build_bells(tr, rnd, grnd, expressive=True):
    """Glockenspiel: sixteenth arpeggio bursts and, later, pure ratchets."""
    for bar in list(range(27, 41, 2)) + list(range(57, 69, 2)):
        pool = ch(bar)["bells"]
        start = T(bar, 3.0) if bar % 4 == 3 else T(bar, 1.0)
        for i in range(6):
            tr.note(start + i * SIXTEENTH + rnd.randint(-5, 5),
                    SIXTEENTH * 1.6, pool[i], 62 - i * 3 + rnd.randint(-5, 5))

    for bar in range(41, 49):
        pool = ch(bar)["bells"]
        ratchet(tr, T(bar, 1.0), B(0.75), pool[4], 70, 3 if bar % 2 else 6)
        ratchet(tr, T(bar, 3.5), B(1.0), pool[5], 66, 8, rising=False)
        if expressive and bar in (44, 48):
            pitch_glitch(tr, T(bar, 1.0), T(bar, 2.0), 8, grnd, spread=6.0)

    # the beat-repeat bar: one slice fired eight times
    stutter(tr, T(64, 4.0), ch(64)["bells"][3], 74, 8, THIRTYSECOND,
            decay=0.92, accel=0.94)


BLIP = [  # (bar offset, beat, duration, pitch) - a chiptune counter-melody
    (0, 1.0, 0.25, 84), (0, 1.5, 0.25, 87), (0, 2.0, 0.25, 89),
    (0, 3.0, 0.25, 84), (0, 3.5, 0.25, 80),
    (1, 1.0, 0.25, 82), (1, 1.75, 0.25, 87), (1, 2.5, 0.25, 82),
    (1, 4.0, 0.5, 79),
    (2, 1.0, 0.25, 87), (2, 1.5, 0.25, 84), (2, 2.0, 0.25, 79),
    (2, 3.0, 0.5, 75),
    (3, 1.0, 0.25, 77), (3, 2.0, 0.25, 80), (3, 3.0, 0.25, 84),
    (3, 4.0, 0.25, 89),
]


def build_blip(tr, rnd, grnd, expressive=True):
    """The flare: a square-wave line that only shows up when it counts."""
    for first in (45, 61, 65):
        for off, beat, dur, pitch in BLIP:
            if first == 45 and rnd.random() < 0.3:
                continue                        # holes in the breakdown pass
            tr.note(T(first + off, beat) + rnd.randint(-4, 4), B(dur),
                    pitch, 62 + rnd.randint(-8, 8))
    for bar in (48, 68):
        # Eb6, not F6: the riff itself lands on F6 on beat 4 of both bars
        ratchet(tr, T(bar, 3.0), B(2.0), 87, 74, 16)
        if expressive:
            pitch_glitch(tr, T(bar, 3.0), T(bar, 5.0), 16, grnd, spread=7.0)


def build_texture(tr, rnd):
    for bar in range(9, 69, 4):
        c = ch(bar)
        tr.note(T(bar) + rnd.randint(0, 40), B(15.6), c["pad"][-1] + 12, 30)
        tr.note(T(bar) + rnd.randint(0, 60), B(15.6), c["pad"][0] + 12, 26)


def build_reverse(tr):
    """Reverse swells that resolve on the downbeat of each new section."""
    # each swell starts two beats before the downbeat it resolves onto; the
    # bar-49 entry is already the one that runs into the bar-48 tape stop
    for bar, vel in ((9, 62), (25, 84), (41, 74), (49, 88), (57, 92), (69, 58)):
        tr.note(T(bar, 3.0) - BAR, B(2.0), 72, vel)


# --------------------------------------------------------------------------
# drums - half time, trap-leaning, deliberately sparse
# --------------------------------------------------------------------------

KICK, SNARE, CLAP, RIM = 36, 40, 39, 37
HAT, OPEN_HAT, SHAKER = 42, 46, 70

KICK_A = "1..........1...."
KICK_B = "1.....1....1...."
KICK_C = "1..........1..1."
SNARE_P = "........1......."
HAT_8 = "1.1.1.1.1.1.1.1."
HAT_16 = "1.111.1.1.11.1.1"


# Where a fill takes over, the written pattern stops: bar -> first sixteenth
# the fill owns.  Without this the fill hits stack on top of the groove and
# every shared pitch truncates itself.
FILL_TAKEOVER = {24: 12, 32: 14, 40: 8, 56: 12, 64: 12, 68: 8}


def build_drums(tr, rnd, expressive=True):
    """Returns the kick ticks, so the sidechain curves can key off them."""
    kicks = []

    def hit(bar, idx, pitch, vel, dur=0.4, jitter=6):
        t = T(bar) + idx * SIXTEENTH + rnd.randint(-jitter, jitter)
        tr.note(t, B(dur), pitch, vel + rnd.randint(-5, 5))
        return t

    plan = []
    for bar in range(13, 25):
        plan.append((bar, KICK_A if bar % 4 else KICK_B, HAT_8, 84, 44))
    for bar in range(25, 41):
        plan.append((bar, KICK_B if bar % 2 else KICK_C, HAT_16, 100, 54))
    for bar in range(49, 57):
        plan.append((bar, KICK_A, HAT_8, 88, 46))
    for bar in range(57, 69):
        plan.append((bar, KICK_C if bar % 2 else KICK_B, HAT_16, 104, 58))

    for bar, kick_pat, hat_pat, kv, hv in plan:
        cut = FILL_TAKEOVER.get(bar, 99)
        for i in steps(kick_pat):
            if i < cut:
                kicks.append(hit(bar, i, KICK, kv, dur=0.22, jitter=4))
        for i in steps(SNARE_P):
            if i < cut:
                hit(bar, i, SNARE, kv - 10, dur=0.5, jitter=4)
                hit(bar, i, CLAP, kv - 22, dur=0.4, jitter=9)
        for i in steps(hat_pat):
            if i < cut:
                hit(bar, i, HAT, hv + (12 if i % 4 == 0 else 0), dur=0.18)
        if bar % 8 == 5 and 14 < cut:
            hit(bar, 14, OPEN_HAT, hv + 8, dur=0.5)
        if bar % 4 == 2 and 6 < cut:
            hit(bar, 6, RIM, 40, dur=0.2)
        for i in (2, 10):
            if i < cut:
                hit(bar, i, SHAKER, 30, dur=0.2, jitter=12)

    # --- glitch fills -----------------------------------------------------
    ratchet(tr, T(24, 4.0), B(1.0), HAT, 70, 8)
    stutter(tr, T(24, 4.5), SNARE, 74, 4, THIRTYSECOND, decay=0.9, accel=0.85)

    ratchet(tr, T(32, 4.5), B(0.5), HAT, 72, 6)

    # bar 40: everything comes apart on the way into the breakdown
    ratchet(tr, T(40, 3.0), B(1.0), HAT, 78, 12)
    stutter(tr, T(40, 4.0), SNARE, 92, 8, THIRTYSECOND, decay=0.93, accel=0.86)

    # the breakdown keeps only a skeleton
    for bar in (42, 44, 46):
        kicks.append(hit(bar, 0, KICK, 78, dur=0.22))
        hit(bar, 8, RIM, 52, dur=0.2)
    ratchet(tr, T(47, 3.0), B(2.0), HAT, 64, 16)

    ratchet(tr, T(56, 4.0), B(1.0), HAT, 74, 12)
    stutter(tr, T(56, 4.5), CLAP, 78, 4, THIRTYSECOND, decay=0.9)

    # bar 64: beat repeat - one sixteenth slice re-fired across beat 4
    for k in range(8):
        t = T(64, 4.0) + k * THIRTYSECOND
        tr.note(t, B(0.09), KICK if k % 4 == 0 else HAT, 96 - k * 4)
        if k % 4 == 0:
            kicks.append(t)

    # bar 68: the biggest glitch, straight into the outro
    ratchet(tr, T(68, 3.0), B(1.0), HAT, 84, 16)
    stutter(tr, T(68, 4.0), SNARE, 100, 10, THIRTYSECOND, decay=0.94,
            accel=0.88)
    tr.note(T(69, 1.0), B(1.0), 49, 96)           # crash on the downbeat
    return kicks


# --------------------------------------------------------------------------
# tempo
# --------------------------------------------------------------------------

def build_tempo_map():
    tm = [(T(1), 74.0), (T(9), 76.0), (T(25), 76.5), (T(41), 74.0)]
    # bar 48 beat 4: the tape stop drags the grid to a halt with the pitch
    for k in range(9):
        u = k / 8.0
        tm.append((T(48, 4.0) + int(u * BEAT), 74.0 - 40.0 * (u ** 1.7)))
    tm.append((T(49), 76.0))
    tm += [(T(57), 77.0), (T(69), 74.0), (T(73), 70.0)]
    # closing ritardando
    for k in range(12):
        u = k / 11.0
        tm.append((T(75) + k * (BEAT // 2), 68.0 - 34.0 * (u ** 1.5)))
    tm.append((T(77), 26.0))
    tm.sort(key=lambda x: x[0])
    return tm


def build_conductor(tempo_map):
    tr = Track("Static Bloom - Conductor")
    tr.text(0, 0x03, "Static Bloom - Conductor")
    tr.text(0, 0x02, "Static Bloom - sad glitch-pop ballad in F minor")
    tr.meta(0, 0x58, bytes([4, 2, 24, 8]))                # 4/4
    tr.meta(0, 0x59, bytes([256 - 4, 1]))                 # sf=-4 (4 flats), minor
    for tick, bpm in tempo_map:
        tempo_meta(tr, tick, bpm)
    for bar, name in ((1, "Intro"), (9, "Verse 1"), (25, "Chorus 1"),
                      (41, "Breakdown / Glitch Zone"), (49, "Verse 2"),
                      (57, "Chorus 2"), (69, "Outro")):
        tr.text(T(bar), 0x06, name)
    return tr


# --------------------------------------------------------------------------
# assembly
# --------------------------------------------------------------------------

def build(expressive=True, seed=71624):
    rnd = random.Random(seed)
    # Controller randomness runs on its own stream so that --clean, which skips
    # it, still produces exactly the same notes as the full version.
    grnd = random.Random(seed ^ 0xC1A5)
    tempo_map = build_tempo_map()
    t2s = make_tick_to_sec(tempo_map)

    conductor = build_conductor(tempo_map)

    piano = Track("Grand Piano", 0, "Acoustic Grand Piano")
    gpiano = Track("Glitch Piano", 1, "Honky-tonk Piano (chopped)")
    rhodes = Track("Rhodes Bed", 2, "Electric Piano 1")
    sub = Track("Sub 808", 3, "Synth Bass 1")
    bells = Track("Glass Bells", 4, "Glockenspiel")
    pad = Track("Vox Pad", 5, "Voice Oohs")
    tex = Track("Granular Texture", 6, "FX 1 (rain)")
    rev = Track("Reverse FX", 7, "Reverse Cymbal")
    blip = Track("Blip Lead", 8, "Lead 1 (square)")
    drums = Track("Glitch Drums", 9, "Standard Kit")

    piano.voice(0, 108, 64, reverb=64, chorus=8)
    gpiano.voice(3, 74, 46, reverb=98, chorus=44)
    rhodes.voice(4, 82, 80, reverb=92, chorus=40)
    sub.voice(38, 110, 64, reverb=24, chorus=0)
    bells.voice(9, 72, 92, reverb=104, chorus=24)
    pad.voice(54, 70, 64, reverb=118, chorus=52)
    tex.voice(96, 48, 64, reverb=127, chorus=64)
    rev.voice(119, 76, 64, reverb=127, chorus=32)
    blip.voice(80, 68, 36, reverb=72, chorus=20)
    drums.voice(0, 100, 64, reverb=40, chorus=0)

    if expressive:
        for tr in (piano, gpiano, sub, bells, blip):
            tr.bend_range(12)

    build_piano(piano, rnd, expressive)
    build_glitch_piano(gpiano, rnd, grnd, expressive)
    build_rhodes(rhodes, rnd)
    build_sub(sub, rnd, expressive)
    build_bells(bells, rnd, grnd, expressive)
    build_pad(pad, rnd)
    build_texture(tex, rnd)
    build_reverse(rev)
    build_blip(blip, rnd, grnd, expressive)
    kicks = build_drums(drums, rnd, expressive)

    if expressive:
        # electronics pump against the kick; the piano never does
        for tr in (rhodes, pad, tex):
            sidechain(tr, kicks, T(13), T(41))
            sidechain(tr, kicks, T(49), T(69))
        # filters open into each chorus and shut for the breakdown
        for tr in (pad, tex):
            sweep(tr, T(23), T(25), 30, 112)
            sweep(tr, T(40), T(41), 112, 24)
            sweep(tr, T(55), T(57), 34, 118)
            sweep(tr, T(68), T(69), 118, 20)
        # the tape stop at bar 48, and the one that ends the record
        for tr in (piano, gpiano, bells, blip, sub):
            tape_stop(tr, T(48, 4.0), T(49) - 8)
        for tr in (piano, gpiano):
            tape_stop(tr, T(76, 2.0), T(77) - 8, depth=-9.0, curve=2.8)

    tracks = [conductor, piano, gpiano, rhodes, sub, bells, pad, tex, rev,
              blip, drums]
    return tracks, tempo_map, t2s


def main():
    ap = argparse.ArgumentParser(description="Generate the Static Bloom MIDI.")
    ap.add_argument("-o", "--out", default=None, help="output .mid path")
    ap.add_argument("--clean", action="store_true",
                    help="omit pitch bend / CC data (notes and tempo only)")
    args = ap.parse_args()

    here = os.path.dirname(os.path.abspath(__file__))
    default = os.path.join(here, os.pardir, "midi",
                           "static_bloom_clean.mid" if args.clean
                           else "static_bloom.mid")
    out = os.path.abspath(args.out or default)

    tracks, _tempo_map, t2s = build(expressive=not args.clean)
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
