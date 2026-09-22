#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
"Low Beam" - a night-drive synthwave track built to be recorded into.

Generates a Standard MIDI File (format 1, 480 PPQ) for FL Studio 2025.
Pure standard library: no external dependencies.

Unlike the other pieces in this repo this one is a bed, not a finished
arrangement.  Two parts are written to be muted and replaced by your own
recordings, and every decision in the file follows from that:

  * the vocal, carried as a guide melody plus a separate vocoder carrier, and
    processed the way the "Nightcall" vocal is - dropped an octave, vocoded,
    then driven into a band-limited distortion
  * the acoustic guitar in the closing refrain, written out as a fingerpicked
    guide so you can learn it, then muted and played for real - dry, with no
    reverb on it at all

What that costs the arrangement, deliberately:

  * The tempo never moves.  Not once, not even at the end.  A ritardando is
    the natural gesture here and it is left out on purpose, because a moving
    grid breaks tempo-synced delays and makes punch-ins impossible.
  * The synth lead never plays under a verse - the vocal gets those sixteen
    bars to itself - and in the choruses, where the two do sound together,
    the lead's lowest note is fourteen semitones above the vocal's
    highest, so the hook doubles the voice rather than masking it.  In the
    verses the pad plays a high voicing only, the bass drops its octave jumps
    and the arp moves up one, so that B2 to F#4 is empty except for the
    voice - kit, tape hiss and vocoder carrier aside, and the carrier goes
    into the vocoder rather than to the mix.
  * Phrases stop early.  Almost every vocal line leaves a beat or more before
    the next one, so a dotted-eighth throw has somewhere to land instead of
    smearing into the following word.
  * Nothing peaks near full.  Channel volumes top out at 100 so there is gain
    left for a saturated vocal and a close-miked guitar.
  * The whole synth world is killed by a pitch-only tape stop at bar 89 - no
    tempo ritard, unlike the one in Static Bloom - which buys three silent
    bars for the tails to decay before the acoustic refrain starts dry.

Form (112 bars, 4/4, a constant 86 BPM):

    bars   1-  8  Intro       pad, bells, tape hiss; bass at 5
    bars   9- 16  Drive       four on the floor, the hook, gated snare
    bars  17- 32  Verse 1     lead vocal; the synth lead sits out entirely
    bars  33- 48  Chorus 1    answer vocal to 40, then the hook to 48
    bars  49- 56  Interlude   the hook alone - no voice anywhere
    bars  57- 72  Verse 2     lead vocal again, now over the arp
    bars  73- 88  Chorus 2    the biggest one
    bars  89- 92  Blackout    tape stop, then three bars of nothing but hiss
    bars  93-108  Refrain     acoustic: guitar, upright, felt piano, dry vocal
    bars 109-112  Outro       one chord, left to ring

Key is F# minor throughout: i - VI - III - VII in the verses and the refrain,
VI - VII - v - i in the choruses.  Capo the second fret and that progression
is Em - C - G - D, which is the whole reason the key is F# minor and not
something a synth would have preferred.

Usage:
    python3 generate_low_beam.py             # full version
    python3 generate_low_beam.py --clean     # notes only, no controllers
"""

import argparse
import bisect
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from smf import (BAR, BEAT, B, T, Track,  # noqa: E402
                 make_tick_to_sec, tempo_meta, write_smf)
from expressive import Voice, note as enote, render  # noqa: E402
from glitch import pitch_glitch, ratchet  # noqa: E402

SIXTEENTH = BEAT // 4
THIRTYSECOND = BEAT // 8

TEMPO = 86.0
LAST_BAR = 112

# --------------------------------------------------------------------------
# harmony - F# minor
# --------------------------------------------------------------------------
# One row per chord, carrying a ready-made voicing for every instrument, so
# the arrangement code never has to spell a chord itself.
#
#   bass     the driving eighth-note synth bass (the sub doubles it -12)
#   pad      full voicing, choruses only
#   padhi    the verse voicing - deliberately starts above the vocal's top
#   arp      four notes for the sixteenth sequence
#   bells    ascending pool for cascades and flourishes
#   carrier  wide voicing for the vocoder carrier, spanning the vocal range
#   gtr      a real acoustic guitar voicing: open shapes with a capo at 2
#   upright  acoustic bass root, an octave below the guitar's lowest string
#   felt     felt piano in the refrain - high, so the guitar keeps the middle
#   refstr   the small string layer that joins the refrain late

CHORDS = {
    "F#m9":   dict(bass=42, upright=30,
                   pad=[57, 61, 64, 68], padhi=[68, 73, 76],
                   arp=[57, 61, 66, 69], bells=[73, 76, 78, 81, 85, 88],
                   carrier=[54, 61, 66, 69, 73],
                   gtr=[42, 49, 54, 57, 61, 66],
                   felt=[73, 78, 81], refstr=[69, 73, 78]),
    "Dmaj9":  dict(bass=38, upright=26,
                   pad=[57, 61, 62, 66], padhi=[66, 69, 73],
                   arp=[57, 62, 66, 69], bells=[74, 78, 81, 86, 88, 90],
                   carrier=[54, 62, 66, 69, 74],
                   gtr=[50, 54, 57, 62, 66],
                   felt=[74, 78, 81], refstr=[69, 74, 78]),
    "Aadd9":  dict(bass=45, upright=33,
                   pad=[57, 61, 64, 71], padhi=[69, 73, 76],
                   arp=[57, 61, 64, 69], bells=[73, 76, 81, 85, 88, 93],
                   carrier=[57, 61, 64, 69, 73],
                   gtr=[45, 49, 52, 57, 61, 69],
                   felt=[73, 76, 81], refstr=[69, 73, 76]),
    "E":      dict(bass=40, upright=28,
                   pad=[56, 59, 64, 68], padhi=[68, 71, 76],
                   arp=[56, 59, 64, 68], bells=[76, 80, 83, 88, 92, 95],
                   carrier=[52, 59, 64, 68, 71],
                   gtr=[52, 59, 64, 68],
                   felt=[76, 80, 83], refstr=[71, 76, 80]),
    "C#m7":   dict(bass=37, upright=25,
                   pad=[56, 59, 64, 68], padhi=[68, 71, 76],
                   arp=[56, 61, 64, 68], bells=[73, 76, 80, 85, 88, 92],
                   carrier=[52, 61, 64, 68, 73],
                   gtr=[49, 56, 61, 64, 68],
                   felt=[73, 76, 80], refstr=[68, 73, 76]),
    "Bm7":    dict(bass=35, upright=35,
                   pad=[57, 62, 66, 71], padhi=[66, 69, 74],
                   arp=[59, 62, 66, 71], bells=[74, 78, 81, 83, 86, 90],
                   carrier=[54, 59, 62, 66, 71],
                   gtr=[47, 54, 57, 62, 66],
                   felt=[74, 78, 83], refstr=[71, 74, 78]),
}

LOOP_A = ["F#m9", "Dmaj9", "Aadd9", "E"]        # i  - VI  - III - VII
LOOP_B = ["Dmaj9", "E", "C#m7", "F#m9"]         # VI - VII - v   - i
LOOP_C = ["F#m9", "Dmaj9", "Bm7", "E"]          # the refrain turns iv-ward

PROG = {}


def _lay(first, names):
    for i, n in enumerate(names):
        PROG[first + i] = n


for b in (1, 5, 9, 13, 17, 21, 25, 29, 49, 53, 57, 61, 65, 69, 93, 97):
    _lay(b, LOOP_A)
for b in (33, 37, 41, 45, 73, 77, 81, 85):
    _lay(b, LOOP_B)
for b in (101, 105):
    _lay(b, LOOP_C)
_lay(89, ["F#m9"] * 4)                          # the blackout holds the tonic
_lay(109, ["F#m9"] * 4)


def ch(bar):
    return CHORDS[PROG[bar]]


SECTIONS = [(8, "intro"), (16, "drive"), (32, "verse"), (48, "chorus"),
            (56, "interlude"), (72, "verse"), (88, "chorus"),
            (92, "blackout"), (108, "refrain"), (LAST_BAR, "outro")]


def section_of(bar):
    for last, name in SECTIONS:
        if bar <= last:
            return name
    return "outro"


# --------------------------------------------------------------------------
# shared gestures
# --------------------------------------------------------------------------
# Kept local rather than pushed into glitch.py: these are arrangement
# helpers, not glitch primitives, and Static Bloom carries its own copies for
# the same reason.

def steps(pattern):
    """'1..1' -> [0, 3].  Patterns are one bar of sixteenths."""
    assert len(pattern) == 16, "pattern must be 16 sixteenths: %r" % pattern
    return [i for i, c in enumerate(pattern) if c == "1"]


def nudge(tick, rnd, lo, hi, floor=None):
    """Humanising jitter, with an optional floor it may not be dragged under.

    A few ticks either side of the beat is the whole point and is left alone
    everywhere it does no harm.  It does harm in exactly one place: the first
    downbeat of the acoustic refrain, where drifting fifteen milliseconds
    early puts a note inside the silence that the section depends on.
    """
    t = tick + rnd.randint(lo, hi)
    return t if floor is None else max(floor, t)


def sidechain(tr, kick_ticks, start, end, depth=0.62, tau=190.0, step=24):
    """CC11 ducking keyed to the kick.  This is most of what makes the synths
    read as 80s rather than as a chord being held down."""
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


def fade(tr, start, end, lo, hi, step=48):
    """CC11 ramp, for entries and for the long decay into the refrain."""
    n = max(1, (end - start) // step)
    for k in range(n + 1):
        u = k / float(n)
        tr.cc(start + k * step, 11, lo + (hi - lo) * u)


def tape_stop(tr, start, end, depth=-11.0, curve=2.3, frames=56):
    """Pitch falling away on an accelerating curve, then back to centre.

    Pitch only.  Static Bloom drags the tempo map down with its tape stops;
    this one must not, because a recording is about to happen.
    """
    for k in range(frames + 1):
        u = k / float(frames)
        tr.bend(start + u * (end - start), depth * (u ** curve))
    tr.bend(end + 4, 0.0)


# --------------------------------------------------------------------------
# the voices, for src/expressive.py
# --------------------------------------------------------------------------

# A polysynth lead played on the wheel: quicker than Ashfall's CS-80, wider
# than Hollow Hour's theremin.  Notes swell over a beat rather than a bar,
# because there is a drum track to stay in front of.
SYNTH_LEAD = dict(
    vib_rate=5.4, vib_delay=0.45, vib_ramp=0.90,
    vib_base=0.10, vib_growth=0.16, vib_ref=B(4),
    scoop_depth=1.1, scoop_max=B(0.35), scoop_frac=0.18, scoop_exp=2.0,
    glide_max=B(0.45), glide_frac=0.28, glide_exp=1.8,
    expr_base=30.0, expr_scale=0.76, expr_cold=14.0, expr_legato=0.80,
    atk_max=B(0.7), atk_frac=0.25, atk_exp=0.8,
    rel_max=B(1.2), rel_frac=0.40, rel_floor=0.12, rel_exp=1.5,
    breath_depth=3.5, breath_rate=0.40, tail=18,
    mod_peak=84.0, mod_min_dur=B(1.0),
)

# The guide vocal.  A singer scoops up into a phrase, holds dead straight for
# most of a beat, and only then lets the vibrato in - so the scoop is deep and
# short and the vibrato arrives late.  This is a guide, not a part: it exists
# so you can hear the tune and the timing before you sing it.
VOX = dict(
    vib_rate=5.1, vib_delay=0.55, vib_ramp=0.85,
    vib_base=0.07, vib_growth=0.15, vib_ref=B(3),
    scoop_depth=1.4, scoop_max=B(0.30), scoop_frac=0.22, scoop_exp=2.4,
    glide_max=B(0.28), glide_frac=0.20, glide_exp=2.0,
    expr_base=34.0, expr_scale=0.72, expr_cold=16.0, expr_legato=0.78,
    atk_max=B(0.5), atk_frac=0.20, atk_exp=0.7,
    rel_max=B(1.0), rel_frac=0.35, rel_floor=0.10, rel_exp=1.4,
    breath_depth=4.5, breath_rate=0.50, tail=16,
    mod_peak=54.0, mod_min_dur=B(2.0),
)

# The same voice in the refrain.  Nothing is done to it there - no pitch
# shift, no vocoder, no distortion - so it has nothing to hide behind, and
# the scoops and the vibrato shrink accordingly.
VOX_DRY = dict(VOX, scoop_depth=0.7, vib_base=0.05, vib_growth=0.10,
               breath_depth=3.0, mod_peak=30.0)


# --------------------------------------------------------------------------
# the vocal
# --------------------------------------------------------------------------
# (bar offset within the phrase, beat, duration in beats, pitch, velocity)
#
# Written at SOUNDING pitch - what you want to hear, after processing.  The
# range is B2-E4, which is not where you sing it; see the setup guide.  The
# line is deliberately narrow and repetitive, closer to speech than to a tune,
# and it stops early in almost every bar to leave the delay somewhere to go.

VERSE_VOX = [
    (0, 1.5, 1.0, 54, 82), (0, 2.5, 0.5, 54, 74), (0, 3.0, 1.5, 52, 78),
    (1, 1.0, 1.0, 54, 80), (1, 2.0, 2.0, 50, 76),
    (2, 1.5, 0.5, 52, 78), (2, 2.0, 1.0, 54, 82), (2, 3.0, 2.0, 49, 74),
    (3, 1.0, 3.0, 52, 78),
    (4, 1.5, 1.0, 57, 86), (4, 2.5, 0.5, 57, 78), (4, 3.0, 1.5, 54, 82),
    (5, 1.0, 1.0, 57, 84), (5, 2.0, 2.0, 54, 80),
    (6, 1.5, 0.5, 56, 80), (6, 2.0, 1.0, 57, 86), (6, 3.0, 2.0, 52, 76),
    (7, 1.0, 2.0, 52, 78), (7, 3.0, 1.0, 47, 68),
]

VERSE_VOX_B = [                     # the answering half: same shape, opened up
    (0, 1.5, 1.0, 54, 84), (0, 2.5, 0.5, 56, 76), (0, 3.0, 1.5, 57, 82),
    (1, 1.0, 2.0, 54, 80), (1, 3.5, 0.5, 52, 70),
    (2, 1.0, 1.0, 54, 82), (2, 2.0, 1.0, 57, 84), (2, 3.0, 2.0, 56, 78),
    (3, 1.0, 2.0, 52, 76),
    (4, 1.5, 1.0, 57, 88), (4, 2.5, 1.5, 59, 86), (4, 4.0, 1.0, 57, 80),
    (5, 1.0, 3.0, 54, 82),
    (6, 1.5, 0.5, 57, 82), (6, 2.0, 1.0, 59, 86), (6, 3.0, 2.0, 57, 80),
    (7, 1.0, 2.0, 54, 76),
]

CHORUS_VOX = [                      # over VI - VII - v - i, twice
    (0, 1.0, 1.5, 57, 92), (0, 2.5, 1.5, 54, 86), (0, 4.0, 1.0, 57, 84),
    (1, 1.0, 3.0, 59, 96), (1, 4.0, 1.0, 56, 84),
    (2, 1.0, 2.0, 61, 98), (2, 3.0, 2.0, 56, 88),
    (3, 1.0, 3.0, 54, 86),
    (4, 1.0, 1.5, 57, 94), (4, 2.5, 1.5, 61, 96), (4, 4.0, 1.0, 59, 88),
    (5, 1.0, 3.5, 64, 104),         # the top of the record
    (6, 1.0, 2.0, 61, 96), (6, 3.0, 2.0, 59, 88),
    (7, 1.0, 4.0, 54, 84),
]

# The second voice: high, clean, barely processed.  It only ever appears in
# the first half of a chorus, where the synth lead is out, so the top of the
# mix is never contested.
ANSWER_VOX = [
    (0, 3.0, 2.0, 69, 62),
    (1, 2.0, 3.0, 71, 66),
    (2, 1.0, 2.0, 73, 70), (2, 3.5, 1.5, 71, 60),
    (3, 2.0, 2.0, 69, 62),
    (4, 3.0, 2.0, 73, 68),
    (5, 2.0, 3.0, 76, 74),
    (6, 1.0, 2.5, 73, 70), (6, 4.0, 1.0, 71, 60),
    (7, 1.0, 4.0, 69, 64),
]

# The refrain melody.  The first eight bars are the verse tune at written
# pitch - which is to say, exactly the notes you already sang for the verse
# take, with nothing done to them afterwards.  That is the whole point of the
# section: the machine voice turns out to have been a person.
REFRAIN_END = [
    (0, 1.5, 1.0, 66, 74), (0, 2.5, 0.5, 66, 68), (0, 3.0, 2.0, 64, 72),
    (1, 1.0, 1.0, 66, 72), (1, 2.0, 2.5, 62, 70),
    (2, 1.5, 0.5, 64, 70), (2, 2.0, 1.0, 66, 74), (2, 3.0, 2.0, 62, 68),
    (3, 1.0, 3.0, 64, 70),
    (4, 1.5, 1.0, 69, 78), (4, 2.5, 0.5, 69, 72), (4, 3.0, 1.5, 66, 74),
    (5, 1.0, 3.0, 62, 72),
    (6, 1.5, 0.5, 66, 72), (6, 2.0, 1.0, 69, 76), (6, 3.0, 2.0, 66, 70),
    (7, 1.0, 4.0, 66, 68),           # F# over E, hanging on the tonic to come
]

VOX_PLAN = [(17, VERSE_VOX), (25, VERSE_VOX_B), (33, CHORUS_VOX),
            (41, CHORUS_VOX), (57, VERSE_VOX), (65, VERSE_VOX_B),
            (73, CHORUS_VOX), (81, CHORUS_VOX)]

# (first bar, phrase, transpose) - the refrain sings the verse an octave up
REFRAIN_VOX_PLAN = [(93, VERSE_VOX, 12), (101, REFRAIN_END, 0)]

ANSWER_PLAN = [(33, ANSWER_VOX), (73, ANSWER_VOX)]


def build_vox(tr, rnd, t2s, expressive=True):
    """The guide melody, rendered with scoops and a late vibrato so it reads
    as sung.  Mute this channel once your take is down."""
    notes = []
    for first, phrase in VOX_PLAN:
        for off, beat, dur, pitch, vel in phrase:
            notes.append(enote(T(first + off, beat) + rnd.randint(-8, 8),
                               B(dur) - 24, pitch, vel + rnd.randint(-4, 4)))
    render(tr, notes, t2s, Voice(**VOX), expressive)

    dry = []
    for first, phrase, shift in REFRAIN_VOX_PLAN:
        for off, beat, dur, pitch, vel in phrase:
            dry.append(enote(T(first + off, beat) + rnd.randint(-6, 6),
                             B(dur) - 24, pitch + shift,
                             vel + rnd.randint(-4, 4)))
    render(tr, dry, t2s, Voice(**VOX_DRY), expressive)


def build_answer(tr, rnd, t2s, expressive=True):
    notes = []
    for first, phrase in ANSWER_PLAN:
        for off, beat, dur, pitch, vel in phrase:
            notes.append(enote(T(first + off, beat) + rnd.randint(-10, 10),
                               B(dur) - 30, pitch, vel + rnd.randint(-4, 4)))
    render(tr, notes, t2s, Voice(**VOX), expressive)


# The carrier a vocoder needs: held chords spanning the vocal's register, so
# the voice has something harmonic to modulate.  Silent wherever the vocal is.
def build_carrier(tr, rnd, grnd, expressive=True):
    for first, _phrase in VOX_PLAN:
        for bar in range(first, first + 8):
            for j, p in enumerate(ch(bar)["carrier"]):
                tr.note(T(bar) + j * 12 + rnd.randint(-4, 4), B(3.9), p,
                        56 - 3 * j + rnd.randint(-4, 4))
    if expressive:
        # the carrier is where the digital artefacts live, so that the guide
        # vocal's own bend stream is left alone
        for bar in (48, 88):
            pitch_glitch(tr, T(bar, 3.0), T(bar, 4.75), 9, grnd, spread=4.5)


# --------------------------------------------------------------------------
# the synth lead
# --------------------------------------------------------------------------
# Never in the same bar as the vocal, and in the choruses more than an octave
# above it.  This is the single biggest thing keeping the midrange clear.

HOOK_A = [                          # over i - VI - III - VII, twice
    (0, 1.0, 1.5, 73, 84), (0, 2.5, 1.5, 78, 88), (0, 4.0, 1.0, 76, 82),
    (1, 1.0, 3.0, 78, 90), (1, 4.0, 1.0, 74, 80),
    (2, 1.0, 2.0, 76, 86), (2, 3.0, 2.0, 73, 82),
    (3, 1.0, 4.0, 71, 84),
    (4, 1.0, 1.5, 73, 86), (4, 2.5, 1.5, 78, 90), (4, 4.0, 1.0, 81, 88),
    (5, 1.0, 3.5, 85, 98),
    (6, 1.0, 2.0, 81, 90), (6, 3.0, 2.0, 76, 84),
    (7, 1.0, 4.0, 76, 86),
]

HOOK_B = [                          # over VI - VII - v - i, twice
    (0, 1.0, 2.0, 78, 88), (0, 3.0, 2.0, 81, 90),
    (1, 1.0, 3.0, 83, 94), (1, 4.0, 1.0, 80, 84),
    (2, 1.0, 2.0, 85, 96), (2, 3.0, 2.0, 80, 88),
    (3, 1.0, 4.0, 78, 86),
    (4, 1.0, 2.0, 81, 92), (4, 3.0, 2.0, 85, 96),
    (5, 1.0, 3.5, 88, 102),
    (6, 1.0, 2.0, 85, 94), (6, 3.0, 2.0, 83, 88),
    (7, 1.0, 4.0, 78, 86),
]

# (first bar, phrase, velocity scale).  Bars 5-8 get the first half only.
LEAD_PLAN = [(5, [n for n in HOOK_A if n[0] < 4], 0.62),
             (9, HOOK_A, 1.00),
             (41, HOOK_B, 0.94),
             (49, HOOK_A, 1.00),
             (81, HOOK_B, 1.00)]


def build_lead(tr, rnd, t2s, expressive=True):
    notes = []
    for first, phrase, scale in LEAD_PLAN:
        for off, beat, dur, pitch, vel in phrase:
            notes.append(enote(T(first + off, beat) + rnd.randint(-6, 6),
                               B(dur) - 20, pitch,
                               vel * scale + rnd.randint(-4, 4)))
    render(tr, notes, t2s, Voice(**SYNTH_LEAD), expressive)


# --------------------------------------------------------------------------
# the engine: bass, sub, arp
# --------------------------------------------------------------------------

BASS_DRIVE = "1.1.1.1.1.1.1.1."      # straight eighths
BASS_VERSE = "1...1.1.1...1.1."      # holes, so the voice has the bar
BASS_OCT = "......1.......1."        # which eighths jump the octave


def build_bass(tr, rnd):
    oct_steps = set(steps(BASS_OCT))
    for bar in range(5, 89):
        sec = section_of(bar)
        pat = BASS_DRIVE if sec in ("drive", "chorus", "interlude") \
            else BASS_VERSE
        vel = {"intro": 70, "drive": 98, "verse": 86, "chorus": 102,
               "interlude": 94}[sec]
        p = ch(bar)["bass"]
        for i in steps(pat):
            # the octave jump lands on F#3, which is exactly where the vocal
            # lives - so the verses do without it and stay under B2
            up = 12 if (i in oct_steps and sec != "verse") else 0
            tr.note(T(bar) + i * SIXTEENTH + rnd.randint(-4, 4), B(0.42),
                    p + up, vel + (8 if i % 4 == 0 else 0)
                    + rnd.randint(-5, 5))


def build_sub(tr, rnd):
    """A sine under the saw.  One note a bar, nothing clever - it exists to
    give the bass a fundamental, not to play a part."""
    for bar in range(9, 89):
        tr.note(T(bar) + rnd.randint(-4, 4), B(3.9), ch(bar)["bass"] - 12,
                82 + rnd.randint(-4, 4))


ARP_BARS = (list(range(9, 17)) + list(range(33, 57)) + list(range(57, 89)))
ARP_ORDER = [0, 1, 2, 3, 2, 3, 1, 2]     # up, then folded back on itself


def build_arp(tr, rnd):
    for bar in ARP_BARS:
        pool = ch(bar)["arp"]
        sec = section_of(bar)
        vel = {"drive": 56, "chorus": 64, "interlude": 58, "verse": 48}[sec]
        for i in range(16):
            p = pool[ARP_ORDER[i % len(ARP_ORDER)]]
            if i % 8 == 0:
                p += 12
            if sec == "verse":
                p += 12          # clears the vocal in Verse 2 by an octave
            tr.note(T(bar) + i * SIXTEENTH + rnd.randint(-3, 3),
                    SIXTEENTH * 0.9, p,
                    vel + (10 if i % 4 == 0 else 0) + rnd.randint(-6, 6))


# --------------------------------------------------------------------------
# pad and bells
# --------------------------------------------------------------------------

def build_pad(tr, rnd):
    """In the verses this plays the high voicing only, bottoming out on F#4.
    Everything else that reaches the mix is under B2 there; the gap between
    is the vocal's, and nothing is allowed to move into it."""
    for bar in range(1, 89):
        sec = section_of(bar)
        if sec == "verse":
            voicing, vel = ch(bar)["padhi"], 44
        elif sec == "chorus":
            voicing, vel = ch(bar)["pad"] + ch(bar)["padhi"], 52
        elif sec == "intro":
            voicing, vel = ch(bar)["pad"], 40
        else:
            voicing, vel = ch(bar)["pad"], 48
        for j, p in enumerate(voicing):
            tr.note(T(bar) + j * 16 + rnd.randint(-6, 6), B(3.92), p,
                    vel - 2 * j + rnd.randint(-4, 4))


def build_bells(tr, rnd):
    """Cascades in the intro, a flourish at the top of each four-bar unit in
    the choruses, and nothing at all once the acoustic section starts."""
    for bar in range(1, 9):
        pool = ch(bar)["bells"]
        for i in range(4):
            tr.note(T(bar, 1.0 + i * 1.0) + rnd.randint(-8, 8), B(1.4),
                    pool[(i * 2) % len(pool)], 50 - i * 3 + rnd.randint(-5, 5))

    for bar in list(range(33, 49, 4)) + list(range(73, 89, 4)):
        pool = ch(bar)["bells"]
        for i in range(6):
            tr.note(T(bar, 1.0) + i * SIXTEENTH + rnd.randint(-4, 4),
                    SIXTEENTH * 1.7, pool[i], 62 - i * 3 + rnd.randint(-5, 5))

    for bar in (52, 56):
        ratchet(tr, T(bar, 3.0), B(1.5), ch(bar)["bells"][4], 58, 6)


def build_noise(tr, rnd, expressive=True):
    """Tape hiss and road noise, running the whole length of the piece.

    It matters most where you would least expect it: under the acoustic
    refrain.  A close-miked guitar with no reverb on it sounds naked in
    silence, and this is what puts it in a room without putting it in a hall.
    """
    bar = 1
    while bar <= LAST_BAR:
        tr.note(T(bar) + rnd.randint(0, 40), B(4 * 8 + 1.0), 60,
                44 + rnd.randint(-4, 4))
        bar += 8
    if not expressive:
        return
    fade(tr, T(1), T(9), 20, 74)               # up out of nothing
    fade(tr, T(9), T(89), 74, 58)              # ducked under the band
    fade(tr, T(89), T(93), 58, 96)             # the blackout: all that is left
    fade(tr, T(93), T(109), 96, 62)            # room tone for the guitar
    fade(tr, T(109), T(LAST_BAR + 1), 62, 0)


# --------------------------------------------------------------------------
# drums
# --------------------------------------------------------------------------

KICK, SNARE, CLAP, RIM = 36, 40, 39, 37
HAT, OPEN_HAT, CRASH = 42, 46, 49
TOM_H, TOM_M, TOM_L = 50, 47, 43

KICK_FOUR = "1...1...1...1..."
KICK_PUSH = "1...1...1...1.1."
KICK_HALF = "1.......1......."
KICK_HALF2 = "1......11......."
SNARE_P = "....1.......1..."
HAT_8 = "1.1.1.1.1.1.1.1."
HAT_16 = "1.111.1.1.111.1."
HAT_OFF = "..1...1...1...1."

# Where a fill takes over, the written pattern stops: bar -> first sixteenth
# the fill owns.  Without this the fill hits stack on the groove and every
# shared pitch truncates itself.
FILL_TAKEOVER = {16: 8, 32: 8, 48: 8, 56: 12, 72: 8, 88: 4}

CRASH_BARS = (9, 33, 49, 57, 73)


def tom_fill(tr, bar, start, rnd, vel=96):
    """The gated tom fill, high to low across the back of the bar.  The one
    unambiguously 1984 gesture in the file."""
    shape = [TOM_H, TOM_H, TOM_M, TOM_M, TOM_L, TOM_L, TOM_L, TOM_L]
    n = 16 - start
    for k in range(n):
        p = shape[min(k * len(shape) // max(1, n), len(shape) - 1)]
        tr.note(T(bar) + (start + k) * SIXTEENTH + rnd.randint(-4, 4),
                B(0.42), p, vel - k * 2 + rnd.randint(-5, 5))


def build_drums(tr, rnd):
    """Returns the kick ticks so the sidechain curves can key off them.

    Stops dead at bar 88 and never comes back.  The acoustic refrain has no
    percussion at all - a gated snare anywhere near a dry guitar would undo
    the entire point of the section.
    """
    kicks = []

    def hit(bar, idx, pitch, vel, dur=0.4, jitter=5):
        t = T(bar) + idx * SIXTEENTH + rnd.randint(-jitter, jitter)
        tr.note(t, B(dur), pitch, vel + rnd.randint(-5, 5))
        return t

    plan = []
    for bar in range(9, 17):
        plan.append((bar, KICK_FOUR, HAT_8, 104, 56))
    for bar in range(17, 33):
        plan.append((bar, KICK_HALF2 if bar % 4 == 3 else KICK_HALF,
                     HAT_OFF, 96, 44))
    for bar in range(33, 49):
        plan.append((bar, KICK_PUSH if bar % 2 else KICK_FOUR, HAT_16,
                     108, 60))
    for bar in range(49, 57):
        plan.append((bar, KICK_FOUR, HAT_8, 102, 56))
    for bar in range(57, 73):
        plan.append((bar, KICK_HALF2 if bar % 2 else KICK_HALF, HAT_8,
                     98, 50))
    for bar in range(73, 89):
        plan.append((bar, KICK_PUSH if bar % 2 else KICK_FOUR, HAT_16,
                     110, 62))

    for bar, kick_pat, hat_pat, kv, hv in plan:
        cut = FILL_TAKEOVER.get(bar, 99)
        for i in steps(kick_pat):
            if i < cut:
                kicks.append(hit(bar, i, KICK, kv, dur=0.2, jitter=3))
        # the snare is on 2 and 4 for all 80 bars it exists, without variation
        for i in steps(SNARE_P):
            if i < cut:
                hit(bar, i, SNARE, kv - 6, dur=0.9, jitter=3)
                hit(bar, i, CLAP, kv - 20, dur=0.6, jitter=8)
        for i in steps(hat_pat):
            if i < cut:
                hit(bar, i, HAT, hv + (12 if i % 4 == 0 else 0), dur=0.16)
        if bar % 4 == 1 and 14 < cut:
            hit(bar, 14, OPEN_HAT, hv + 10, dur=0.5)
        if bar % 8 == 3 and 6 < cut:
            hit(bar, 6, RIM, 46, dur=0.2)

    for bar, start, vel in ((16, 8, 92), (32, 8, 94), (48, 8, 100),
                            (56, 12, 90), (72, 8, 96), (88, 4, 108)):
        tom_fill(tr, bar, start, rnd, vel)

    for bar in CRASH_BARS:
        tr.note(T(bar), B(2.0), CRASH, 104)
    return kicks


# --------------------------------------------------------------------------
# the blackout at bar 89
# --------------------------------------------------------------------------
# One chord, hit hard, then dragged down by a pitch-only tape stop.  Bars
# 90-92 are empty on every channel but the hiss and the click, which at 86 BPM
# is a little over ten seconds - enough for an eight-second synth tail to be
# gone before the guitar starts.

BLACKOUT_TRACKS = ("bass", "sub", "pad", "arp", "bells", "carrier")
TAPE_START, TAPE_END = T(89, 1.0), T(90) - 8


def build_blackout(tracks, rnd):
    c = CHORDS["F#m9"]
    tracks["bass"].note(T(89), B(3.0), c["bass"], 104)
    tracks["sub"].note(T(89), B(3.5), c["bass"] - 12, 96)
    for j, p in enumerate(c["pad"] + c["padhi"]):
        tracks["pad"].note(T(89) + j * 14, B(3.4), p, 62 - 2 * j)
    for j, p in enumerate(c["carrier"]):
        tracks["carrier"].note(T(89) + j * 10, B(3.2), p, 58 - 3 * j)
    for i in range(8):
        tracks["arp"].note(T(89) + i * SIXTEENTH + rnd.randint(-3, 3),
                           SIXTEENTH * 0.9, c["arp"][i % 4], 60 - i * 4)
    for i in range(4):
        tracks["bells"].note(T(89) + i * SIXTEENTH, B(1.2), c["bells"][i],
                             64 - i * 6)
    tracks["drums"].note(T(89), B(3.0), CRASH, 110)


# --------------------------------------------------------------------------
# the acoustic refrain
# --------------------------------------------------------------------------
# Capo 2.  F#m is an Em shape, D is a C shape, A is a G shape, E is a D shape,
# Bm7 is an Am7 shape.  The voicings below are those open shapes at sounding
# pitch, which is why they are uneven lengths - a G shape has six strings and
# a D shape has four.
#
# The picking pattern indexes from the bottom for the bass notes and from the
# top for the treble, so it lands on the right strings whatever the shape.

PICK = [(1.0, 0), (1.5, -1), (2.0, -3), (2.5, -2),
        (3.0, 1), (3.5, -1), (4.0, -3), (4.5, -2)]


def build_guitar(tr, rnd):
    """The part to learn, then mute and play yourself.

    Fingerpicked, one pattern held for sixteen bars without variation.  That
    is on purpose: a written part that shows off is a part you have to
    reproduce, and this one only has to show you where the chords change.
    """
    for bar in range(93, 109):
        v = ch(bar)["gtr"]
        for beat, idx in PICK:
            vel = 76 if beat == 1.0 else (66 if beat == 3.0 else 58)
            tr.note(nudge(T(bar, beat), rnd, -10, 10, floor=T(93)), B(1.6),
                    v[idx], vel + rnd.randint(-6, 6))
    # the last chord, strummed once and left alone
    for j, p in enumerate(CHORDS["F#m9"]["gtr"]):
        tr.note(T(109) + j * 22 + rnd.randint(-4, 4), B(14.0), p,
                70 - 2 * j + rnd.randint(-4, 4))


def build_upright(tr, rnd):
    """Roots, and a fifth where the bar is long enough to want one.  An
    octave below the guitar's bottom string, so the two never trade paint."""
    for bar in range(93, 109):
        p = ch(bar)["upright"]
        tr.note(nudge(T(bar), rnd, -8, 8, floor=T(93)), B(2.4), p,
                78 + rnd.randint(-5, 5))
        if bar % 2 == 0:
            tr.note(T(bar, 3.0) + rnd.randint(-8, 8), B(1.8), p + 7,
                    68 + rnd.randint(-5, 5))
    tr.note(T(109), B(14.0), CHORDS["F#m9"]["upright"], 72)


def build_felt(tr, rnd):
    """High and sparse.  The guitar owns everything from F#2 to A4 in this
    section and the piano is not allowed into it - two instruments picking
    the same notes in the same octave is how acoustic sections turn to mush."""
    for bar in range(97, 109):
        v = ch(bar)["felt"]
        if bar % 2:
            for j, p in enumerate(v):
                tr.note(T(bar, 3.0) + j * 18 + rnd.randint(-8, 8), B(2.0), p,
                        46 - 3 * j + rnd.randint(-4, 4))
        else:
            tr.note(T(bar, 2.0) + rnd.randint(-10, 10), B(1.5), v[-1],
                    42 + rnd.randint(-4, 4))
    for j, p in enumerate([54] + CHORDS["F#m9"]["felt"]):
        tr.note(T(109) + j * 26, B(13.0), p, 48 - 4 * j)


def build_refrain_strings(tr, rnd, expressive=True):
    """Sixteen bars is a long time for two instruments, so a small string
    layer joins at 101 - but not before.  The first eight bars of the refrain
    are guitar, bass and voice and nothing else, which is the only way a dry
    guitar gets to be the loudest thing in a mix."""
    for bar in range(101, 109):
        for j, p in enumerate(ch(bar)["refstr"]):
            tr.note(T(bar) + j * 24 + rnd.randint(-10, 10), B(3.9), p,
                    38 - 3 * j + rnd.randint(-4, 4))
    for j, p in enumerate(CHORDS["F#m9"]["refstr"]):
        tr.note(T(109) + j * 30, B(12.0), p, 36 - 3 * j)
    if expressive:
        fade(tr, T(101), T(105), 0, 78)
        fade(tr, T(105), T(109), 78, 92)
        fade(tr, T(109), T(LAST_BAR + 1), 92, 0)


# --------------------------------------------------------------------------
# the click
# --------------------------------------------------------------------------
# Four loud beats in the bar before every entry you have to play, and then a
# quiet quarter-note pulse from the blackout to the end - because once the
# drums stop at 88 there is nothing left to lock to, and the whole acoustic
# refrain is played against nothing but hiss.

CLICK_PITCH = 84
COUNT_IN = (16, 32, 56, 72, 92)


def build_click(tr):
    for bar in COUNT_IN:
        for beat in (1.0, 2.0, 3.0, 4.0):
            tr.note(T(bar, beat), B(0.2), CLICK_PITCH,
                    104 if beat == 1.0 else 88)
    for bar in range(89, LAST_BAR + 1):
        if bar in COUNT_IN:
            continue
        for beat in (1.0, 2.0, 3.0, 4.0):
            tr.note(T(bar, beat), B(0.2), CLICK_PITCH,
                    76 if beat == 1.0 else 58)


# --------------------------------------------------------------------------
# conductor
# --------------------------------------------------------------------------

def build_conductor():
    tr = Track("Low Beam - Conductor")
    tr.text(0, 0x03, "Low Beam - Conductor")
    tr.text(0, 0x02, "Low Beam - synthwave night drive in F# minor")
    tr.meta(0, 0x58, bytes([4, 2, 24, 8]))                # 4/4
    tr.meta(0, 0x59, bytes([3, 1]))                       # 3 sharps, minor
    tempo_meta(tr, 0, TEMPO)                              # and never again
    for bar, name in ((1, "Intro"), (9, "Drive"), (17, "Verse 1"),
                      (33, "Chorus 1"), (49, "Interlude"), (57, "Verse 2"),
                      (73, "Chorus 2"), (89, "Blackout - tails decay"),
                      (93, "Acoustic Refrain - record here"),
                      (109, "Outro")):
        tr.text(T(bar), 0x06, name)
    return tr


# --------------------------------------------------------------------------
# assembly
# --------------------------------------------------------------------------

def build(expressive=True, seed=48210):
    rnd = random.Random(seed)
    # Controller randomness runs on its own stream so that --clean, which
    # skips it, still produces exactly the same notes as the full version.
    grnd = random.Random(seed ^ 0x5EC0)
    tempo_map = [(0, TEMPO)]
    t2s = make_tick_to_sec(tempo_map)

    conductor = build_conductor()

    bass = Track("Saw Bass", 0, "Synth Bass 1")
    lead = Track("Synth Lead", 1, "Lead 2 (sawtooth)")
    pad = Track("New Age Pad", 2, "Pad 1 (new age)")
    bells = Track("FM Bells", 3, "FX 3 (crystal)")
    carrier = Track("Vocoder Carrier", 4, "SynthBrass 1")
    vox = Track("Lead Vocal GUIDE", 5, "Lead 6 (voice)")
    answer = Track("Answer Vocal GUIDE", 6, "Voice Oohs")
    arp = Track("Arp Sequence", 7, "Lead 1 (square)")
    sub = Track("Sub", 8, "Synth Bass 2")
    drums = Track("Gated Kit", 9, "Standard Kit")
    guitar = Track("Acoustic Guitar GUIDE", 10, "Acoustic Guitar (steel)")
    upright = Track("Upright Bass", 11, "Acoustic Bass")
    felt = Track("Felt Piano", 12, "Acoustic Grand Piano")
    refstr = Track("Refrain Strings", 13, "String Ensemble 1")
    noise = Track("Tape Noise", 14, "Seashore")
    click = Track("Click", 15, "Woodblock")

    # Volumes stop at 100, not 127.  The two loudest things in the finished
    # record are not in this file yet.
    bass.voice(38, 96, 64, reverb=46, chorus=48)
    lead.voice(81, 88, 58, reverb=104, chorus=72)
    pad.voice(88, 74, 64, reverb=118, chorus=64)
    bells.voice(98, 66, 88, reverb=112, chorus=40)
    carrier.voice(62, 70, 64, reverb=72, chorus=56)
    vox.voice(85, 92, 64, reverb=88, chorus=32)
    answer.voice(54, 78, 76, reverb=110, chorus=48)
    arp.voice(80, 68, 40, reverb=92, chorus=36)
    sub.voice(39, 92, 64, reverb=20, chorus=0)
    drums.voice(0, 100, 64, reverb=64, chorus=0)
    # CC91 = 0 on the guitar is the file asking, in the only language it has,
    # for no reverb on that channel.  The rest of the refrain is nearly dry
    # too, or the guitar would be the only thing in the room without a room.
    guitar.voice(25, 88, 64, reverb=0, chorus=0)
    upright.voice(32, 86, 64, reverb=14, chorus=0)
    felt.voice(0, 80, 70, reverb=26, chorus=0)
    refstr.voice(48, 62, 56, reverb=44, chorus=16)
    noise.voice(122, 42, 64, reverb=30, chorus=0)
    click.voice(115, 72, 64, reverb=0, chorus=0)

    if expressive:
        for tr in (bass, lead, carrier, vox, answer, arp, pad, bells, sub):
            tr.bend_range(12)

    build_bass(bass, rnd)
    build_sub(sub, rnd)
    build_arp(arp, rnd)
    build_pad(pad, rnd)
    build_bells(bells, rnd)
    build_lead(lead, rnd, t2s, expressive)
    build_vox(vox, rnd, t2s, expressive)
    build_answer(answer, rnd, t2s, expressive)
    build_carrier(carrier, rnd, grnd, expressive)
    kicks = build_drums(drums, rnd)
    build_blackout(dict(bass=bass, sub=sub, pad=pad, arp=arp, bells=bells,
                        carrier=carrier, drums=drums), rnd)
    build_guitar(guitar, rnd)
    build_upright(upright, rnd)
    build_felt(felt, rnd)
    build_refrain_strings(refstr, rnd, expressive)
    build_noise(noise, rnd, expressive)
    build_click(click)

    if expressive:
        # the synths pump against the kick; the acoustic section never does
        for tr in (pad, arp, bells, carrier):
            sidechain(tr, kicks, T(9), T(89))
        for tr in (pad, arp):
            sweep(tr, T(1), T(9), 22, 86)          # the intro filter opening
            sweep(tr, T(31), T(33), 40, 116)
            sweep(tr, T(71), T(73), 40, 120)
            sweep(tr, T(88), T(90), 120, 8)        # and slamming shut
        # the tape stop: pitch only, so the grid underneath it never moves
        for tr in (bass, sub, pad, arp, bells, carrier):
            tape_stop(tr, TAPE_START, TAPE_END)

    tracks = [conductor, bass, lead, pad, bells, carrier, vox, answer, arp,
              sub, drums, guitar, upright, felt, refstr, noise, click]
    return tracks, tempo_map, t2s


def main():
    ap = argparse.ArgumentParser(description="Generate the Low Beam MIDI.")
    ap.add_argument("-o", "--out", default=None, help="output .mid path")
    ap.add_argument("--clean", action="store_true",
                    help="omit pitch bend / CC data (notes and tempo only)")
    args = ap.parse_args()

    here = os.path.dirname(os.path.abspath(__file__))
    default = os.path.join(here, os.pardir, "midi",
                           "low_beam_clean.mid" if args.clean
                           else "low_beam.mid")
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
