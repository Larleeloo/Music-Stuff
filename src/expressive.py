# -*- coding: utf-8 -*-
"""
A portamento lead: notes plus the controller data that makes a keyless
instrument sound played rather than typed.

Some instruments have no keys and no discrete note boundaries - a theremin,
a Yamaha CS-80 ribbon, an ondes Martenot.  What sells them is not the patch
but three behaviours, none of which a plain note list carries:

  * portamento  the pitch slides out of one note and into the next
  * vibrato     a hand LFO that is delayed, then widens as a note is held
  * swells      volume shaped continuously (CC11), so notes bloom and fade
                instead of starting and stopping

This module writes all three around a note list.  The defaults reproduce a
theremin; `Voice` fields retune it for other keyless instruments (see
CS80 below, which slides slowly and swells over whole bars).

Note ordering matters and is handled by the Track's event priorities: at a
legato junction the note-off lands before the bend reset, which lands before
the next note-on, so a slide resolves without a blip.
"""

import math

from smf import B, BEAT


class Voice(object):
    """Tuning for one keyless instrument.  Times in ticks, depths in
    semitones, rates in Hz, so the numbers stay readable."""

    def __init__(self, **kw):
        # pitch bend
        self.bend_range = 12.0
        self.bend_step = 12          # ticks between pitch frames
        self.expr_step = 24          # ticks between CC11 frames
        # scoop: how the pitch arrives at a phrase-opening note
        self.scoop_depth = 1.6
        self.scoop_max = B(0.5)
        self.scoop_frac = 0.40
        self.scoop_exp = 2.0
        # glide: how the pitch leaves a note that is tied to the next
        self.glide_max = B(0.6)
        self.glide_frac = 0.45
        self.glide_exp = 2.2
        # vibrato
        self.vib_rate = 4.6
        self.vib_delay = 0.35        # seconds before it starts
        self.vib_ramp = 1.10         # seconds to reach full width
        self.vib_base = 0.20
        self.vib_growth = 0.20
        self.vib_ref = B(3)          # note length at which growth maxes out
        # CC11 shape
        self.expr_base = 38.0
        self.expr_scale = 0.72
        self.expr_legato = 0.75      # fraction of peak a tied note starts at
        self.expr_cold = 10.0        # where an untied note starts
        self.atk_max = B(0.9)
        self.atk_frac = 0.35
        self.atk_exp = 0.75
        self.rel_max = B(1.6)
        self.rel_frac = 0.50
        self.rel_floor = 0.14
        self.rel_exp = 1.6
        self.breath_depth = 4.0      # slow undulation on the sustain
        self.breath_rate = 0.55
        self.tail = 24               # CC11 left behind after a phrase ends
        # the closing gesture: a long fall away to nothing
        self.fall_max = B(5.0)
        self.fall_frac = 0.62
        self.fall_depth = 11.5
        self.fall_exp = 1.6
        # mod wheel mirrors the vibrato for synths that map it
        self.mod_peak = 90.0
        self.mod_min_dur = B(1.5)
        self.mod_step = 96
        for k, v in kw.items():
            if not hasattr(self, k):
                raise TypeError("unknown Voice field %r" % k)
            setattr(self, k, v)


# A Yamaha CS-80 played on the ribbon: slower and wider than a theremin in
# every dimension.  Notes swell over whole bars, slides take most of a bar,
# and the vibrato waits nearly a second before it opens up.
CS80 = dict(
    vib_rate=4.9, vib_delay=0.90, vib_ramp=2.20,
    vib_base=0.09, vib_growth=0.20, vib_ref=B(8),
    scoop_depth=0.9, scoop_max=B(1.2), scoop_frac=0.22, scoop_exp=1.7,
    glide_max=B(1.6), glide_frac=0.30, glide_exp=1.5,
    expr_base=22.0, expr_scale=0.82, expr_cold=6.0, expr_legato=0.70,
    atk_max=B(2.6), atk_frac=0.42, atk_exp=0.95,
    rel_max=B(3.2), rel_frac=0.45, rel_floor=0.10, rel_exp=1.5,
    breath_depth=3.0, breath_rate=0.24, tail=14,
    mod_peak=72.0, mod_min_dur=B(3.0),
)


def note(bar_tick, dur_ticks, pitch, vel, fall=False):
    """One entry for `render`.  Kept as a dict so callers can build note
    lists from whatever bar/beat helper they already have."""
    return dict(t=bar_tick, d=dur_ticks, p=pitch, v=vel, fall=fall)


def render(tr, notes, t2s, voice=None, expressive=True):
    """Write `notes` to `tr` with slides, vibrato and swells.

    t2s converts ticks to seconds, so vibrato and breathing stay at a fixed
    rate in Hz even where the tempo map moves.
    """
    v = voice or Voice()
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
        scoop_len = min(v.scoop_max, v.scoop_frac * dur)
        glide_len = min(v.glide_max, v.glide_frac * dur)
        fall_len = min(v.fall_max, v.fall_frac * dur)
        vib_max = v.vib_base + v.vib_growth * min(1.0, dur / v.vib_ref)
        phase = (i * 1.7) % (2 * math.pi)
        sec0 = t2s(t0)

        # ---- pitch: scoop in, vibrato through, glide out -----------------
        last = None
        tick = t0
        while tick <= t1:
            semis = 0.0
            if not legato_prev and scoop_len > 0 and tick - t0 < scoop_len:
                u = (tick - t0) / scoop_len
                semis -= v.scoop_depth * (1.0 - u) ** v.scoop_exp
            secs = t2s(tick) - sec0
            depth = vib_max * max(0.0, min(
                1.0, (secs - v.vib_delay) / v.vib_ramp))
            semis += depth * math.sin(2 * math.pi * v.vib_rate * secs + phase)
            if legato_next and tick > t1 - glide_len:
                u = (tick - (t1 - glide_len)) / glide_len
                semis += interval * (u ** v.glide_exp)
            if nt["fall"] and tick > t1 - fall_len:
                u = (tick - (t1 - fall_len)) / fall_len
                semis -= v.fall_depth * (u ** v.fall_exp)
            semis = max(-v.bend_range + 0.1, min(v.bend_range - 0.1, semis))
            val = tr.bend(tick, semis, v.bend_range)
            if val == last:
                tr.pop_last()                   # drop redundant frames
            else:
                last = val
            tick += v.bend_step
        tr.bend(t1, 0.0, v.bend_range)          # ordered after the note-off

        # ---- the volume hand: CC11 swells --------------------------------
        peak = min(127, v.expr_base + nt["v"] * v.expr_scale)
        start = v.expr_legato * peak if legato_prev else v.expr_cold
        atk = max(1.0, min(v.atk_max, v.atk_frac * dur))
        rel = max(1.0, min(v.rel_max, v.rel_frac * dur))
        tick = t0
        while tick <= t1:
            if tick - t0 < atk:
                val = start + (peak - start) * ((tick - t0) / atk) ** v.atk_exp
            else:
                val = peak
            val += v.breath_depth * math.sin(
                2 * math.pi * v.breath_rate * (t2s(tick) - sec0))
            if not legato_next and tick > t1 - rel:
                u = (tick - (t1 - rel)) / rel
                val = peak * (v.rel_floor
                              + (1.0 - v.rel_floor) * (1.0 - u) ** v.rel_exp)
            if nt["fall"] and tick > t1 - fall_len:
                u = (tick - (t1 - fall_len)) / fall_len
                val *= max(0.0, 1.0 - u ** 1.2)
            tr.cc(tick, 11, val)
            tick += v.expr_step
        tr.cc(t1, 11, 0 if nt["fall"] else v.tail)

        # ---- mod wheel tracks the vibrato, for synths that map it --------
        if dur >= v.mod_min_dur:
            tick = t0
            while tick <= t1:
                secs = t2s(tick) - sec0
                tr.cc(tick, 1, v.mod_peak * max(0.0, min(
                    1.0, (secs - v.vib_delay) / v.vib_ramp)))
                tick += v.mod_step
            tr.cc(t1, 1, 0)
