#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
"Hollow Hour" - a dark, haunting ballad in D minor.

Generates a Standard MIDI File (format 1, 480 PPQ) intended for import into
FL Studio 2025.  Pure standard library: no external dependencies.

The centrepiece is a theremin-style lead.  A theremin has no keys and no
discrete notes, so the illusion is built from three things that are baked
into the MIDI data:

  * portamento glides  - pitch bend ramps from each note into the next
  * hand vibrato       - a ~4.6 Hz pitch-bend LFO that widens as a note is held
  * volume-hand swells - CC11 expression envelopes, so notes bloom and fade
                         instead of starting abruptly

Everything else in the arrangement is chosen for the same cold, glassy,
"haunted parlour" colour: bowed glass pad, glass armonica, music box,
ghost choir, harp, contrabass drone, atmosphere and a heartbeat pulse.

Form (64 bars, 4/4, ~58 BPM drifting to a closing ritardando):

    bars  1- 8  I.   Winding        music box alone, then the pad breathes in
    bars  9-24  II.  The Lament     theremin states the descending theme
    bars 25-32  III. The Hollow     choir + heartbeat enter, armonica answers
    bars 33-48  IV.  Apex           full arrangement, theremin climbs to F6
    bars 49-56  V.   Collapse       isolated sighs, a long fall into silence
    bars 57-64  VI.  Music Box      the box alone, winding down and drooping

Harmony is the lament bass (a descending tetrachord D-C-Bb-A) with a
Neapolitan Eb in the bridge.

Usage:
    python3 generate_hollow_hour.py                 # full expressive version
    python3 generate_hollow_hour.py --clean         # notes only (easy to edit)
"""

import argparse
import math
import os
import random
import struct

# --------------------------------------------------------------------------
# timing
# --------------------------------------------------------------------------

PPQ = 480
BEAT = PPQ
BAR = 4 * BEAT


def T(bar, beat=1.0):
    """Absolute tick of a musical position (1-indexed bars and beats)."""
    return int(round((bar - 1) * BAR + (beat - 1.0) * BEAT))


def B(beats):
    """Beats -> ticks."""
    return int(round(beats * BEAT))


# Event ordering inside a single tick.  Note-offs must precede note-ons so a
# repeated pitch retriggers, and a pitch-bend reset must land between them.
P_META, P_SETUP, P_OFF, P_CTRL, P_ON = 0, 1, 2, 3, 4


def vlq(n):
    """Variable-length quantity used for delta times and meta lengths."""
    if n < 0:
        n = 0
    out = [n & 0x7F]
    n >>= 7
    while n:
        out.append((n & 0x7F) | 0x80)
        n >>= 7
    return bytes(reversed(out))


class Track:
    """One MTrk chunk.  Events are collected unordered and sorted on write."""

    def __init__(self, name, channel=None, instrument=None):
        self.name = name
        self.channel = channel
        self.instrument = instrument
        self._ev = []
        self._seq = 0

    # -- low level ---------------------------------------------------------
    def add(self, tick, prio, data):
        self._ev.append((max(0, int(round(tick))), prio, self._seq, bytes(data)))
        self._seq += 1

    def meta(self, tick, mtype, payload):
        self.add(tick, P_META, bytes([0xFF, mtype]) + vlq(len(payload)) + payload)

    def text(self, tick, mtype, s):
        self.meta(tick, mtype, s.encode("utf-8"))

    # -- channel messages --------------------------------------------------
    def program(self, tick, prog):
        self.add(tick, P_SETUP, [0xC0 | self.channel, prog & 0x7F])

    def cc(self, tick, num, val, prio=P_CTRL):
        v = max(0, min(127, int(round(val))))
        self.add(tick, prio, [0xB0 | self.channel, num & 0x7F, v])

    def bend(self, tick, semitones, rng=12.0):
        v = 8192 + int(round(semitones / rng * 8192.0))
        v = max(0, min(16383, v))
        self.add(tick, P_CTRL, [0xE0 | self.channel, v & 0x7F, (v >> 7) & 0x7F])
        return v

    def note(self, tick, dur, pitch, vel):
        pitch = max(0, min(127, int(round(pitch))))
        vel = max(1, min(127, int(round(vel))))
        t0 = max(0, int(round(tick)))
        t1 = max(t0 + 1, int(round(tick + dur)))
        self.add(t0, P_ON, [0x90 | self.channel, pitch, vel])
        self.add(t1, P_OFF, [0x80 | self.channel, pitch, 64])

    # -- setup helper ------------------------------------------------------
    def voice(self, prog, volume, pan, reverb=110, chorus=32):
        self.text(0, 0x03, self.name)
        if self.instrument:
            self.text(0, 0x04, self.instrument)
        self.program(0, prog)
        self.cc(0, 7, volume, prio=P_SETUP)    # channel volume
        self.cc(0, 10, pan, prio=P_SETUP)      # pan
        self.cc(0, 91, reverb, prio=P_SETUP)   # reverb send
        self.cc(0, 93, chorus, prio=P_SETUP)   # chorus send
        self.cc(0, 11, 100, prio=P_SETUP)      # expression starts open

    def bend_range(self, semitones=12):
        """RPN 0: widen pitch bend so the theremin can glide a full octave."""
        self.cc(0, 101, 0, prio=P_SETUP)
        self.cc(0, 100, 0, prio=P_SETUP)
        self.cc(0, 6, semitones, prio=P_SETUP)
        self.cc(0, 38, 0, prio=P_SETUP)
        self.cc(0, 101, 127, prio=P_SETUP)
        self.cc(0, 100, 127, prio=P_SETUP)

    # -- output ------------------------------------------------------------
    def serialize(self):
        evs = sorted(self._ev, key=lambda e: (e[0], e[1], e[2]))
        buf = bytearray()
        last = 0
        for tick, _p, _s, data in evs:
            buf += vlq(tick - last)
            buf += data
            last = tick
        buf += vlq(0) + bytes([0xFF, 0x2F, 0x00])
        return b"MTrk" + struct.pack(">I", len(buf)) + bytes(buf)


def write_smf(path, tracks):
    head = b"MThd" + struct.pack(">IHHH", 6, 1, len(tracks), PPQ)
    with open(path, "wb") as fh:
        fh.write(head)
        for tr in tracks:
            fh.write(tr.serialize())


# --------------------------------------------------------------------------
# tempo
# --------------------------------------------------------------------------

def build_tempo_map():
    """(tick, bpm) pairs.  Sectional rubato plus a closing ritardando."""
    tm = [
        (T(1), 58.0),
        (T(5), 57.0),
        (T(9), 60.0),
        (T(17), 61.0),
        (T(21), 60.0),
        (T(24, 3), 56.0),          # breath at the end of the verse
        (T(25), 62.0),
        (T(32, 3), 58.0),
        (T(33), 63.0),
        (T(41), 64.0),             # apex pushes forward
        (T(45), 62.0),
        (T(48, 3), 57.0),
        (T(49), 56.0),
        (T(53), 53.0),
        (T(57), 50.0),
        (T(59), 47.0),
    ]
    # bars 61-64: the music box winds down, one tempo step per beat
    steps = 16
    for i in range(steps):
        u = i / float(steps - 1)
        bpm = 46.0 - 18.0 * (u ** 1.5)
        tm.append((T(61) + i * BEAT, bpm))
    tm.append((T(65), 26.0))       # final chord hangs
    tm.sort(key=lambda x: x[0])
    return tm


def make_tick_to_sec(tempo_map):
    pts = list(tempo_map)
    cum = [0.0]
    for i in range(1, len(pts)):
        dt = pts[i][0] - pts[i - 1][0]
        cum.append(cum[-1] + dt / float(PPQ) * (60.0 / pts[i - 1][1]))

    def f(tick):
        lo = 0
        for i, (tk, _bpm) in enumerate(pts):
            if tk <= tick:
                lo = i
            else:
                break
        return cum[lo] + (tick - pts[lo][0]) / float(PPQ) * (60.0 / pts[lo][1])

    return f


# --------------------------------------------------------------------------
# harmony
# --------------------------------------------------------------------------
# Voicings are deliberately near-static so the descending bass does the work:
# the pad holds D-F-A under Dm / Dm7/C / Bbmaj7 and only moves to C#-E-G for
# the A7.  That suspended stillness is what makes the lament ache.

CHORDS = {
    #            bass  pad             choir           harp arpeggio (8 asc.)
    "Dm":   dict(bass=38, pad=[62, 65, 69], choir=[74, 77, 81],
                 harp=[50, 57, 62, 65, 69, 74, 77, 81]),
    "Dm/C": dict(bass=36, pad=[62, 65, 69], choir=[72, 77, 81],
                 harp=[48, 53, 57, 62, 65, 69, 72, 74]),
    "Bb":   dict(bass=34, pad=[62, 65, 69], choir=[74, 77, 82],
                 harp=[46, 53, 58, 62, 65, 69, 70, 74]),
    "A7":   dict(bass=33, pad=[61, 64, 67], choir=[73, 76, 79],
                 harp=[45, 52, 57, 61, 64, 67, 69, 73]),
    "Gm":   dict(bass=43, pad=[62, 67, 70], choir=[74, 79, 82],
                 harp=[43, 50, 55, 58, 62, 67, 70, 74]),
    "Eb":   dict(bass=39, pad=[62, 67, 70], choir=[74, 79, 82],
                 harp=[39, 46, 51, 58, 62, 67, 70, 74]),
}

LAMENT = ["Dm", "Dm/C", "Bb", "A7"]
HOLLOW = ["Gm", "Eb", "Bb", "A7"]

PROG = {}                                   # bar number -> chord name
for b in range(1, 7):
    PROG[b] = "Dm"
PROG[7], PROG[8] = "Bb", "A7"
for start in (9, 13, 17, 21, 33, 37, 45, 49, 53):
    for i, c in enumerate(LAMENT):
        PROG[start + i] = c
for start in (25, 29, 41):
    for i, c in enumerate(HOLLOW):
        PROG[start + i] = c
for b in range(57, 61):
    PROG[b] = "Dm"
PROG[61], PROG[62], PROG[63], PROG[64] = "Bb", "A7", "Dm", "Dm"


def chord(bar):
    return CHORDS[PROG[bar]]


# --------------------------------------------------------------------------
# the theremin lead
# --------------------------------------------------------------------------

def tn(bar, beat, dur, pitch, vel, fall=False):
    return dict(t=T(bar, beat), d=B(dur), p=pitch, v=vel, fall=fall)


THEREMIN = [
    # -- II. The Lament: a descending line with an upper-neighbour sigh -----
    tn(9, 1.5, 2.5, 81, 62), tn(9, 4.0, 1.0, 82, 66),
    tn(10, 1.0, 3.0, 81, 68), tn(10, 4.0, 1.0, 79, 64),
    tn(11, 1.0, 3.0, 77, 70), tn(11, 4.0, 1.0, 76, 64),
    tn(12, 1.0, 2.0, 74, 66), tn(12, 3.0, 2.0, 73, 60),

    tn(13, 1.5, 2.5, 81, 66), tn(13, 4.0, 1.0, 82, 70),
    tn(14, 1.0, 3.0, 81, 72), tn(14, 4.0, 1.0, 79, 66),
    tn(15, 1.0, 2.0, 77, 72), tn(15, 3.0, 2.0, 79, 70),
    tn(16, 1.0, 2.0, 81, 74), tn(16, 3.0, 2.0, 85, 78),

    # answering phrase: rises to the first apex
    tn(17, 1.0, 1.5, 74, 68), tn(17, 2.5, 1.5, 77, 70),
    tn(17, 4.0, 1.0, 81, 74),
    tn(18, 1.0, 3.0, 84, 80), tn(18, 4.0, 1.0, 81, 72),
    tn(19, 1.0, 3.5, 86, 86), tn(19, 4.5, 0.5, 84, 74),
    tn(20, 1.0, 2.0, 82, 76), tn(20, 3.0, 2.0, 81, 68),

    tn(21, 1.5, 2.5, 81, 64), tn(21, 4.0, 1.0, 82, 68),
    tn(22, 1.0, 3.0, 81, 70), tn(22, 4.0, 1.0, 79, 64),
    tn(23, 1.0, 3.0, 77, 68), tn(23, 4.0, 1.0, 76, 62),
    tn(24, 1.0, 3.0, 74, 60),

    # -- III. The Hollow ---------------------------------------------------
    tn(27, 1.0, 3.0, 82, 70), tn(27, 4.0, 1.0, 84, 76),
    tn(28, 1.0, 4.0, 85, 84),                       # leading tone, held, wailing
    tn(29, 1.0, 3.0, 86, 88), tn(29, 4.0, 1.0, 84, 76),
    tn(30, 1.0, 3.0, 82, 78), tn(30, 4.0, 1.0, 79, 70),
    tn(31, 1.0, 2.0, 81, 72), tn(31, 3.0, 2.0, 77, 66),
    tn(32, 1.0, 3.5, 76, 62),

    # -- IV. Apex ----------------------------------------------------------
    tn(33, 1.5, 2.5, 81, 70), tn(33, 4.0, 1.0, 82, 74),
    tn(34, 1.0, 2.5, 81, 76), tn(34, 3.5, 0.5, 79, 66),
    tn(34, 4.0, 1.0, 81, 72),
    tn(35, 1.0, 3.0, 77, 76), tn(35, 4.0, 1.0, 76, 68),
    tn(36, 1.0, 2.0, 74, 72), tn(36, 3.0, 2.0, 73, 66),

    tn(37, 1.0, 1.0, 74, 72), tn(37, 2.0, 1.0, 77, 76),
    tn(37, 3.0, 1.0, 81, 80), tn(37, 4.0, 1.0, 86, 86),
    tn(38, 1.0, 3.0, 84, 88), tn(38, 4.0, 1.0, 81, 78),
    tn(39, 1.0, 3.0, 82, 84), tn(39, 4.0, 1.0, 81, 76),
    tn(40, 1.0, 4.0, 79, 80),

    tn(41, 1.0, 3.5, 86, 94), tn(41, 4.5, 0.5, 88, 88),
    tn(42, 1.0, 4.0, 89, 100),                      # F6 - the apex
    tn(43, 1.0, 2.0, 86, 90), tn(43, 3.0, 2.0, 84, 84),
    tn(44, 1.0, 2.0, 82, 80), tn(44, 3.0, 2.0, 79, 74),

    tn(45, 1.0, 3.0, 81, 76), tn(45, 4.0, 1.0, 79, 70),
    tn(46, 1.0, 3.0, 77, 72), tn(46, 4.0, 1.0, 76, 66),
    tn(47, 1.0, 3.0, 74, 68), tn(47, 4.0, 1.0, 72, 62),
    tn(48, 1.0, 4.0, 73, 64),

    # -- V. Collapse: isolated sighs, then one long fall -------------------
    tn(49, 2.0, 3.0, 74, 58),
    tn(50, 2.0, 3.0, 72, 54),
    tn(51, 2.0, 3.0, 70, 50),
    tn(52, 2.0, 3.0, 69, 46),
    tn(53, 2.0, 2.0, 65, 44),
    tn(54, 2.0, 2.0, 64, 40),
    tn(55, 1.0, 8.0, 62, 46, fall=True),
]

VIB_RATE = 4.6          # Hz - a real theremin player's hand vibrato
BEND_RANGE = 12.0       # semitones (set on the channel via RPN 0)
BEND_STEP = 12          # ticks between pitch-bend frames
EXPR_STEP = 24          # ticks between CC11 frames


def render_theremin(tr, notes, t2s, expressive=True):
    """Notes plus the glide / vibrato / swell data that sells the theremin."""
    notes = sorted(notes, key=lambda n: n["t"])
    n = len(notes)

    # Legato pairs are butt-joined exactly so the bend reset can slot between
    # the note-off and the next note-on without an audible blip.
    for i in range(n - 1):
        gap = notes[i + 1]["t"] - (notes[i]["t"] + notes[i]["d"])
        if 0 < gap <= B(0.25):
            notes[i]["d"] = notes[i + 1]["t"] - notes[i]["t"]

    for i, nt in enumerate(notes):
        t0, t1 = nt["t"], nt["t"] + nt["d"]
        prv = notes[i - 1] if i > 0 else None
        nxt = notes[i + 1] if i < n - 1 else None

        legato_prev = bool(prv and prv["t"] + prv["d"] >= t0 - 2)
        interval = 0
        legato_next = False
        if nxt and nxt["t"] <= t1 + 2:
            interval = nxt["p"] - nt["p"]
            legato_next = abs(interval) <= 12 and interval != 0

        tr.note(t0, nt["d"], nt["p"], nt["v"])
        if not expressive:
            continue

        dur = float(nt["d"])
        scoop_len = min(B(0.5), 0.40 * dur)
        glide_len = min(B(0.6), 0.45 * dur)
        fall_len = min(B(5.0), 0.62 * dur)
        vib_max = 0.20 + 0.20 * min(1.0, dur / B(3))
        phase = (i * 1.7) % (2 * math.pi)
        sec0 = t2s(t0)

        # ---- pitch: scoop in, vibrato through, glide out -----------------
        last = None
        tick = t0
        while tick <= t1:
            semis = 0.0
            if not legato_prev and scoop_len > 0 and tick - t0 < scoop_len:
                u = (tick - t0) / scoop_len
                semis -= 1.6 * (1.0 - u) ** 2
            secs = t2s(tick) - sec0
            depth = vib_max * max(0.0, min(1.0, (secs - 0.35) / 1.10))
            semis += depth * math.sin(2 * math.pi * VIB_RATE * secs + phase)
            if legato_next and tick > t1 - glide_len:
                u = (tick - (t1 - glide_len)) / glide_len
                semis += interval * (u ** 2.2)
            if nt["fall"] and tick > t1 - fall_len:
                u = (tick - (t1 - fall_len)) / fall_len
                semis -= 11.5 * (u ** 1.6)
            semis = max(-BEND_RANGE + 0.1, min(BEND_RANGE - 0.1, semis))
            v = tr.bend(tick, semis, BEND_RANGE)
            if v == last:
                tr._ev.pop()                    # drop redundant frames
            else:
                last = v
            tick += BEND_STEP
        tr.bend(t1, 0.0, BEND_RANGE)            # ordered after the note-off

        # ---- the volume hand: CC11 swells --------------------------------
        peak = min(127, 38 + nt["v"] * 0.72)
        start = 0.75 * peak if legato_prev else 10.0
        atk = max(1.0, min(B(0.9), 0.35 * dur))
        rel = max(1.0, min(B(1.6), 0.50 * dur))
        tick = t0
        while tick <= t1:
            if tick - t0 < atk:
                val = start + (peak - start) * ((tick - t0) / atk) ** 0.75
            else:
                val = peak
            val += 4.0 * math.sin(2 * math.pi * 0.55 * (t2s(tick) - sec0))
            if not legato_next and tick > t1 - rel:
                u = (tick - (t1 - rel)) / rel
                val = peak * (0.14 + 0.86 * (1.0 - u) ** 1.6)
            if nt["fall"] and tick > t1 - fall_len:
                u = (tick - (t1 - fall_len)) / fall_len
                val *= max(0.0, 1.0 - u ** 1.2)
            tr.cc(tick, 11, val)
            tick += EXPR_STEP
        tr.cc(t1, 11, 0 if nt["fall"] else 24)

        # ---- mod wheel tracks the vibrato, for synths that map it --------
        if dur >= B(1.5):
            tick = t0
            while tick <= t1:
                secs = t2s(tick) - sec0
                tr.cc(tick, 1, 90 * max(0.0, min(1.0, (secs - 0.35) / 1.10)))
                tick += 96
            tr.cc(t1, 1, 0)


# --------------------------------------------------------------------------
# supporting parts
# --------------------------------------------------------------------------

def hold_runs(bars, key):
    """Group consecutive bars sharing a voicing so pads sustain across them."""
    runs = []
    for bar in bars:
        v = tuple(chord(bar)[key])
        if runs and runs[-1][2] == v and runs[-1][1] + 1 == bar:
            runs[-1][1] = bar
        else:
            runs.append([bar, bar, v])
    return runs


def build_pad(tr, rnd):
    """Bowed glass: the cold sustained fabric under everything."""
    sections = [
        (range(5, 25), 52),
        (range(25, 33), 60),
        (range(33, 49), 68),
        (range(49, 57), 46),
        (range(61, 65), 40),
    ]
    for bars, vel in sections:
        for first, last, voicing in hold_runs(list(bars), "pad"):
            dur = B(4.0 * (last - first + 1)) - B(0.1)
            if last >= 63:
                dur = B(4.0 * (last - first + 1)) + B(6.0)   # final chord rings
            for j, p in enumerate(voicing):
                tr.note(T(first) + rnd.randint(0, 14), dur,
                        p, vel + rnd.randint(-4, 4) - 2 * j)


def build_choir(tr, rnd):
    """Ghost voices - they only appear once the floor drops away."""
    sections = [(range(25, 33), 44), (range(41, 49), 58),
                (range(53, 57), 38), (range(61, 65), 34)]
    for bars, vel in sections:
        for first, last, voicing in hold_runs(list(bars), "choir"):
            dur = B(4.0 * (last - first + 1)) - B(0.15)
            if last >= 63:
                dur = B(4.0 * (last - first + 1)) + B(6.0)
            for j, p in enumerate(voicing):
                tr.note(T(first) + rnd.randint(0, 30), dur,
                        p, vel + rnd.randint(-5, 5) - 2 * j)


def build_bass(tr, rnd):
    """The lament bass: D - C - Bb - A, one whole note per bar."""
    for bar in list(range(5, 57)) + [61, 62]:
        vel = 58
        if 33 <= bar <= 48:
            vel = 70
        elif bar >= 49:
            vel = 48
        tr.note(T(bar) + rnd.randint(0, 10), B(3.85),
                chord(bar)["bass"], vel + rnd.randint(-4, 4))
    # final low D, doubled an octave down
    tr.note(T(63), B(10.0), 38, 52)
    tr.note(T(63) + 6, B(10.0), 26, 44)


def build_harp(tr, rnd):
    """Broken chords rolling upward - gothic, not sparkly."""
    plan = {}
    for bar in range(13, 25):
        plan[bar] = 46
    for bar in range(29, 33):
        plan[bar] = 50
    for bar in range(33, 49):
        plan[bar] = 58
    for bar in range(49, 53):
        plan[bar] = 40
    for bar, base in sorted(plan.items()):
        pool = chord(bar)["harp"]
        for step in range(8):
            beat = 1.0 + step * 0.5
            vel = base + int(6 * math.sin(math.pi * step / 7.0)) + rnd.randint(-5, 5)
            tr.note(T(bar, beat) + rnd.randint(-12, 12), B(2.5),
                    pool[step], vel)


MB_MOTIF = [  # (bar offset, beat, duration, pitch)
    (0, 1.0, 1.0, 81), (0, 2.0, 1.0, 77), (0, 3.0, 1.0, 74), (0, 4.0, 1.0, 77),
    (1, 1.0, 1.5, 76), (1, 2.5, 1.5, 73), (1, 4.0, 1.0, 74),
]


def music_box(tr, bar, vel, rnd, variant=False, keep=None):
    """The fragile hook.  `variant` sours E to Eb; `keep` thins it out."""
    for idx, (off, beat, dur, p) in enumerate(MB_MOTIF):
        if keep is not None and idx not in keep:
            continue
        pitch = 75 if (variant and p == 76) else p
        tr.note(T(bar + off, beat) + rnd.randint(-10, 14), B(dur),
                pitch, vel + rnd.randint(-6, 6))


def build_music_box(tr, rnd, expressive=True):
    music_box(tr, 1, 64, rnd)
    music_box(tr, 3, 60, rnd, variant=True)
    music_box(tr, 5, 48, rnd, keep=[0, 2, 4, 6])
    music_box(tr, 7, 40, rnd, keep=[0, 4])
    music_box(tr, 49, 42, rnd, keep=[0, 2, 4])          # a memory, mid-collapse
    music_box(tr, 57, 62, rnd)
    music_box(tr, 59, 56, rnd, variant=True)
    music_box(tr, 61, 44, rnd, keep=[0, 2, 4])
    # the spring runs out
    tr.note(T(63, 1.0), B(1.2), 81, 36)
    tr.note(T(63, 3.0), B(1.4), 77, 30)
    tr.note(T(64, 1.0), B(8.0), 74, 26)
    if expressive:
        # the last note sags flat, like a box winding down
        for k in range(41):
            u = k / 40.0
            tr.bend(T(64, 1.0) + int(u * B(7.0)), -1.9 * (u ** 1.7), BEND_RANGE)


ARMONICA = [  # (bar, beat, duration, pitch, velocity)
    (12, 3.0, 2.0, 86, 44), (13, 1.0, 1.5, 81, 38),
    (16, 3.0, 1.0, 81, 42), (16, 4.0, 1.5, 85, 46),
    (20, 3.0, 1.5, 86, 46), (20, 4.5, 1.0, 84, 40),
    (24, 2.0, 1.5, 86, 48), (24, 3.5, 1.5, 81, 42),
    # the armonica answers the theremin's silence across the bridge
    (25, 1.0, 1.5, 86, 54), (25, 2.5, 1.0, 82, 48), (25, 4.0, 1.0, 79, 44),
    (26, 1.0, 2.0, 82, 50), (26, 3.0, 1.0, 79, 44), (26, 4.0, 1.0, 86, 52),
    (32, 3.0, 1.0, 88, 50), (32, 4.0, 1.5, 85, 46),
    (40, 2.0, 1.5, 86, 52), (40, 4.0, 1.5, 89, 56),
    (44, 3.0, 1.0, 86, 50), (44, 4.0, 1.5, 84, 44),
    (48, 3.0, 2.0, 81, 44),
    (52, 1.0, 4.0, 86, 40),
    (56, 1.0, 4.0, 85, 34),
    (64, 1.0, 8.0, 86, 28),
]


def build_armonica(tr, rnd):
    for bar, beat, dur, p, vel in ARMONICA:
        tr.note(T(bar, beat) + rnd.randint(-14, 14), B(dur), p,
                vel + rnd.randint(-4, 4))


def build_atmosphere(tr, rnd):
    """A near-subliminal open fifth, re-struck every eight bars."""
    for bar in range(1, 57, 8):
        # just short of eight bars: same-pitch re-strikes must not overlap,
        # or the new note is cut off by the old one's note-off
        tr.note(T(bar), B(31.5), 50, 30 + rnd.randint(-3, 3))
        tr.note(T(bar) + 20, B(31.4), 57, 27 + rnd.randint(-3, 3))
    for bar in (41, 45):                     # high shimmer at the apex
        tr.note(T(bar), B(16.0), 74, 26)
        tr.note(T(bar) + 30, B(16.0), 81, 24)
    tr.note(T(63), B(12.0), 50, 30)
    tr.note(T(63) + 20, B(12.0), 57, 28)


def build_risers(tr):
    """Reverse cymbal swells that resolve exactly on each section downbeat."""
    for bar, vel in ((9, 64), (25, 78), (33, 82), (41, 90), (49, 70), (57, 56)):
        tr.note(T(bar, 3.0) - BAR, B(2.0), 72, vel)


KICK, SNARE, LOW_TOM, MID_TOM, HI_TOM = 36, 38, 41, 45, 48
CRASH, CHINESE, TRIANGLE = 49, 52, 81


def build_percussion(tr, rnd):
    """A heartbeat, not a groove."""
    def hit(bar, beat, pitch, vel, dur=0.4):
        tr.note(T(bar, beat) + rnd.randint(-8, 10), B(dur), pitch,
                vel + rnd.randint(-5, 5))

    for bar in range(25, 33):
        hit(bar, 1.0, KICK, 60)
        hit(bar, 1.75, KICK, 42)
    for bar in range(33, 49):
        hit(bar, 1.0, KICK, 70)
        hit(bar, 1.75, KICK, 50)
        if bar % 4 == 3:
            hit(bar, 3.0, KICK, 40)
    for bar in range(49, 53):
        vel = 54 - (bar - 49) * 6
        hit(bar, 1.0, KICK, vel)
        hit(bar, 1.75, KICK, max(28, vel - 14))
    hit(53, 1.0, KICK, 36)

    for bar in (25, 33, 41, 45):
        hit(bar, 1.0, LOW_TOM, 74, dur=1.2)
    hit(25, 1.0, CHINESE, 52, dur=3.0)
    hit(41, 1.0, CHINESE, 66, dur=3.0)
    hit(33, 1.0, CRASH, 54, dur=3.0)

    for beat, pitch, vel in ((3.0, LOW_TOM, 40), (3.5, MID_TOM, 48),
                             (4.0, MID_TOM, 56), (4.5, HI_TOM, 66)):
        hit(40, beat, pitch, vel, dur=0.45)

    for bar, beat in ((3, 4.0), (7, 4.0), (59, 4.0), (63, 3.0)):
        hit(bar, beat, TRIANGLE, 26, dur=1.5)


def build_conductor(tempo_map):
    tr = Track("Hollow Hour - Conductor")
    tr.text(0, 0x03, "Hollow Hour - Conductor")
    tr.text(0, 0x02, "Hollow Hour - dark ballad in D minor")
    tr.meta(0, 0x58, bytes([4, 2, 24, 8]))              # 4/4
    tr.meta(0, 0x59, bytes([256 - 1, 1]))               # sf=-1 (1 flat), minor
    for tick, bpm in tempo_map:
        us = int(round(60000000.0 / bpm))
        tr.meta(tick, 0x51, bytes([(us >> 16) & 0xFF, (us >> 8) & 0xFF, us & 0xFF]))
    for bar, name in ((1, "I. Winding"), (9, "II. The Lament"),
                      (25, "III. The Hollow"), (33, "IV. Apex"),
                      (49, "V. Collapse"), (57, "VI. Music Box Alone")):
        tr.text(T(bar), 0x06, name)
    return tr


def final_fade(tracks, expressive):
    """Ride expression down to nothing across the last chord."""
    if not expressive:
        return
    for tr in tracks:
        start, end = T(63), T(65, 3)
        steps = 48
        for k in range(steps + 1):
            u = k / float(steps)
            tr.cc(start + int(u * (end - start)), 11, 100 * (1.0 - u) ** 1.4)


# --------------------------------------------------------------------------
# assembly
# --------------------------------------------------------------------------

def build(expressive=True, seed=20260910):
    rnd = random.Random(seed)
    tempo_map = build_tempo_map()
    t2s = make_tick_to_sec(tempo_map)

    conductor = build_conductor(tempo_map)

    # GM program numbers are 0-indexed here; the comment gives the GM name.
    theremin = Track("Theremin Lead", 0, "Lead 6 (voice) - theremin substitute")
    armonica = Track("Glass Armonica", 1, "FX 3 (crystal)")
    pad = Track("Bowed Glass Pad", 2, "Pad 5 (bowed)")
    choir = Track("Ghost Choir", 3, "Choir Aahs")
    harp = Track("Harp", 4, "Orchestral Harp")
    box = Track("Music Box", 5, "Music Box")
    bass = Track("Contrabass Drone", 6, "Contrabass")
    atmos = Track("Atmosphere", 7, "FX 4 (atmosphere)")
    riser = Track("Reverse Cymbal Risers", 8, "Reverse Cymbal")
    perc = Track("Heartbeat Percussion", 9, "Standard Kit")

    theremin.voice(85, 102, 64, reverb=112, chorus=48)
    armonica.voice(98, 78, 90, reverb=124, chorus=40)
    pad.voice(92, 72, 64, reverb=127, chorus=56)
    choir.voice(52, 68, 52, reverb=127, chorus=44)
    harp.voice(46, 76, 38, reverb=112, chorus=24)
    box.voice(10, 84, 78, reverb=118, chorus=20)
    bass.voice(43, 88, 64, reverb=78, chorus=16)
    atmos.voice(99, 56, 64, reverb=127, chorus=64)
    riser.voice(119, 70, 64, reverb=127, chorus=32)
    perc.voice(0, 80, 64, reverb=92, chorus=8)

    if expressive:
        theremin.bend_range(int(BEND_RANGE))
        box.bend_range(int(BEND_RANGE))

    render_theremin(theremin, THEREMIN, t2s, expressive=expressive)
    build_armonica(armonica, rnd)
    build_pad(pad, rnd)
    build_choir(choir, rnd)
    build_harp(harp, rnd)
    build_music_box(box, rnd, expressive=expressive)
    build_bass(bass, rnd)
    build_atmosphere(atmos, rnd)
    build_risers(riser)
    build_percussion(perc, rnd)
    final_fade([pad, choir, bass, atmos, armonica], expressive)

    tracks = [conductor, theremin, armonica, pad, choir, harp, box, bass,
              atmos, riser, perc]
    return tracks, tempo_map, t2s


def main():
    ap = argparse.ArgumentParser(description="Generate the Hollow Hour MIDI.")
    ap.add_argument("-o", "--out", default=None, help="output .mid path")
    ap.add_argument("--clean", action="store_true",
                    help="omit pitch bend / expression data (notes only)")
    args = ap.parse_args()

    here = os.path.dirname(os.path.abspath(__file__))
    default = os.path.join(here, os.pardir, "midi",
                           "hollow_hour_clean.mid" if args.clean
                           else "hollow_hour.mid")
    out = os.path.abspath(args.out or default)

    tracks, tempo_map, t2s = build(expressive=not args.clean)
    write_smf(out, tracks)

    notes = sum(1 for tr in tracks for e in tr._ev if e[3][0] & 0xF0 == 0x90)
    end = max((e[0] for tr in tracks for e in tr._ev), default=0)
    secs = t2s(end)
    print("wrote %s" % out)
    print("  tracks %d   notes %d   events %d   %.1f KB"
          % (len(tracks), notes, sum(len(tr._ev) for tr in tracks),
             os.path.getsize(out) / 1024.0))
    print("  length %d bars, %d:%02d" % (end // BAR + 1, int(secs) // 60,
                                         int(secs) % 60))


if __name__ == "__main__":
    main()
