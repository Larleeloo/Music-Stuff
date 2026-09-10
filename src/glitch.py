# -*- coding: utf-8 -*-
"""
Glitch primitives shared by the pieces in this repo.

These write note and controller data rather than relying on an effect, so the
gesture survives export and shows up in the piano roll where it can be edited.
"""


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


def pitch_glitch(tr, start, end, count, rnd, spread=5.0):
    """Stair-stepped bend jumps - a sampler losing its place."""
    choices = [-spread, -spread * 0.5, 0.0, spread * 0.5, spread, spread * 1.4]
    for k in range(count):
        tr.bend(start + (end - start) * k / float(count), rnd.choice(choices))
    tr.bend(end, 0.0)
