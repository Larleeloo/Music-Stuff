# -*- coding: utf-8 -*-
"""
A small Standard MIDI File writer, shared by the pieces in this repo.

Pure standard library.  Writes format 1 files at 480 PPQ with no running
status, which keeps the output easy to diff and easy for any DAW to parse.

The one subtlety worth knowing about is event ordering.  Several messages can
land on the same tick, and the order matters:

    note-off  ->  pitch-bend reset  ->  note-on

A repeated pitch only retriggers if its note-off comes first, and a portamento
glide only resets cleanly if the bend lands between the two notes.  Events are
therefore tagged with a priority and sorted on write, so callers can add them
in whatever order is convenient.
"""

import struct

PPQ = 480
BEAT = PPQ
BAR = 4 * BEAT


def T(bar, beat=1.0):
    """Absolute tick of a musical position (1-indexed bars and beats)."""
    return int(round((bar - 1) * BAR + (beat - 1.0) * BEAT))


def B(beats):
    """Beats -> ticks."""
    return int(round(beats * BEAT))


# Ordering of events that share a tick.  See the module docstring.
P_META, P_SETUP, P_OFF, P_CTRL, P_ON = 0, 1, 2, 3, 4


def vlq(n):
    """Variable-length quantity, used for delta times and meta lengths."""
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

    def pop_last(self):
        """Discard the most recently added event (used to drop redundant
        controller frames without re-deriving them)."""
        self._ev.pop()

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
        """Write a pitch bend in semitones; returns the raw 14-bit value so
        callers can skip frames that would repeat the previous one."""
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

    # -- setup helpers -----------------------------------------------------
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
        """RPN 0 - widen pitch bend beyond the usual +/-2 default."""
        self.cc(0, 101, 0, prio=P_SETUP)
        self.cc(0, 100, 0, prio=P_SETUP)
        self.cc(0, 6, semitones, prio=P_SETUP)
        self.cc(0, 38, 0, prio=P_SETUP)
        self.cc(0, 101, 127, prio=P_SETUP)
        self.cc(0, 100, 127, prio=P_SETUP)

    # -- introspection -----------------------------------------------------
    def note_count(self):
        return sum(1 for e in self._ev
                   if e[3][0] & 0xF0 == 0x90 and e[3][2] > 0)

    def event_count(self):
        return len(self._ev)

    def end_tick(self):
        return max((e[0] for e in self._ev), default=0)

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


def tempo_meta(track, tick, bpm):
    us = int(round(60000000.0 / bpm))
    track.meta(tick, 0x51,
               bytes([(us >> 16) & 0xFF, (us >> 8) & 0xFF, us & 0xFF]))


def make_tick_to_sec(tempo_map):
    """Build a tick -> seconds function from a sorted [(tick, bpm)] map."""
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
