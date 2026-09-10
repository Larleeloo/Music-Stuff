# Static Bloom — FL Studio 2025 setup guide

A sad glitch-pop ballad in F minor, ~4:05, 76 bars of 4/4 at 76 BPM, built
around a grand piano. Half-time drums, a whirring ethereal bass drone, a string
orchestra that grows through the piece, and a glitch vocabulary written into
the note data rather than left to plugins.

## Files

| File | Use it when |
|---|---|
| `midi/static_bloom.mid` | **Start here.** Everything: pitch bend, sustain pedal, sidechain curves, filter sweeps. |
| `midi/static_bloom_clean.mid` | Identical notes and tempo, no controller data. Easier to hand-edit, or if your instruments choke on dense automation. |

Both are Standard MIDI File format 1, 480 PPQ, one instrument per MIDI channel.
The two files contain **exactly the same notes** — only the controllers differ.

## Importing

1. **File → Import → MIDI file…** (or drag the `.mid` onto the Playlist).
2. Keep **tempo import** enabled. The tempo map is load-bearing here: bar 48's
   tape stop is a real ritardando that drags the grid to a halt alongside the
   pitch bend, and the ending slows to 26 BPM. Without it you lose both.
3. Enable **controller / automation import** for `static_bloom.mid` — that is
   what brings in the sustain pedal, the bass whir and portamento, the
   tape stops and the sidechain curves.
4. Let FL create **one channel per MIDI channel**; track names carry over.

## Channel map

GM program numbers below are the 1-indexed ones FL displays.

| Ch | Track | GM program | Role | Suggested FL instrument |
|---|---|---|---|---|
| 1 | **Grand Piano** | 1 — Acoustic Grand | **The song.** Melody, rolled voicings, pedal | A good piano library; keep it close and fairly dry |
| 2 | Glitch Piano | 4 — Honky-tonk | Chopped echoes of the grand, an eighth behind | Same piano, then bit-crush it hard |
| 3 | Rhodes Bed | 5 — Electric Piano 1 | Warm harmonic bed under the piano | FLEX Rhodes, or a DirectWave EP |
| 4 | **Whirring Bass** | 96 — Pad 8 (sweep) | Sustained ethereal drone, root + octave | See the section below — this one needs the right patch |
| 5 | Glass Bells | 10 — Glockenspiel | Arpeggio bursts, later pure ratchets | FLEX bells |
| 6 | Vox Pad | 55 — Voice Oohs | The wordless stand-in for a vocal | FLEX vocal pad, Harmor, Sytrus choir |
| 7 | Granular Texture | 97 — FX 1 (rain) | Air and grit, almost subliminal | Any noisy pad; keep it very low |
| 8 | Reverse FX | 120 — Reverse Cymbal | Swells resolving on section downbeats | Reversed crash or reversed piano |
| 9 | Blip Lead | 81 — Lead 1 (square) | The flare: chiptune counter-melody | 3xOsc square, no filter, short decay |
| 10 | Glitch Drums | Standard Kit | Half-time kit, trap hats, glitch fills | FPC, or your own one-shots |
| 11 | Violins | 49 — String Ensemble 1 | Section chords, from Chorus 1 onward | Any string library; legato patch |
| 12 | Cello | 43 — Cello | Counterline against the piano | Solo cello, or a small cello section |
| 13 | Tremolo Strings | 45 — Tremolo Strings | Dread in the breakdown and last chorus | Tremolo patch, or fast-bowed strings |
| 14 | Celesta | 9 — Celesta | High sparkle; doubles the chorus peaks | FLEX celesta / music box |
| 15 | French Horn | 61 — French Horn | Warmth arriving late, from bar 61 | Horn section, or a warm brass pad |

Channel 10 uses GM drum mapping: 36 kick, 40 electric snare, 39 clap, 37 rim,
42 closed hat, 46 open hat, 49 crash, 70 shaker. Channel 16 is left free for
you to add something of your own.

## The bass

It is a drone, not a bass line, and three things in the MIDI keep it from
reading as plucked:

- **The notes tie across bar lines and overlap into each other.** Neighbouring
  bars sharing a root become one long note, and each note runs past the start
  of the next, so there is never a gap to re-attack into. The part is
  continuous from bar 9 to bar 73 with no silence anywhere in it.
- **The attack is CC11, not the note-on.** Volume swells in over about two
  beats and then breathes very slowly. If your patch has a hard attack you'll
  still hear a click on the first note, so give it a slow amp attack too.
- **Two slightly detuned pitch LFOs** (0.73 Hz and 1.09 Hz) beat against each
  other at about ±15 cents. That beating is the whir. It is deliberately below
  the level where you hear it as pitch movement — you should feel it as motion
  in the tone, not hear it as vibrato.

There is also a slow CC74 filter drift, and portamento between roots taken by
the **shortest path** — D♭ up to C slides down a semitone from the octave above
rather than swooping up eleven.

For the patch: a soft saw or triangle pad with a slow attack, a gentle chorus,
and the filter open enough to hear movement. GM's Pad 8 (sweep) is the closest
stock approximation. Because it sits low, add a clean sine sub under it if you
need weight on small speakers — the root layer is written an octave below the
main voice specifically so you can solo and reinforce it.

## The strings

They enter one section at a time so the arrangement grows rather than arriving
all at once:

| | Enters | Sits out |
|---|---|---|
| Violins | Chorus 1 (bar 25), bigger in Chorus 2 | The breakdown |
| Cello | Verse 2 (bar 49) — the counterline | Everything before it |
| Tremolo | Breakdown (41) and last chorus (61) | The rest |
| French Horn | Bar 61, the final lift | The rest |

Each part is voiced in its own register so nothing crowds the piano, which
keeps the top line throughout: cello sits at C3–E♭4, violins at B♭4–E♭6, horns
at A♭3–E♭4. The violins and tremolo carry CC11 bowing swells, so they breathe
in rather than start. **The strings ride straight through both tape stops** —
an orchestra does not tape-stop, and the contrast is the point.

## Where the glitches are

Everything below is already in the MIDI. This is a map so you know what you're
looking at in the piano roll, and where to reinforce it with effects.

| Bar | What happens |
|---|---|
| 8 · beat 4 | First stutter — accelerating retriggers into Verse 1 |
| 24 · beat 4 | Hat ratchet + snare stutter + piano stutter into Chorus 1 |
| 32 · beat 4.5 | Short 1/32 hat ratchet |
| 40 | Full disintegration into the breakdown; filter closes over the bar |
| 41–48 | **The glitch zone.** Drums drop to a skeleton, piano fragments, bells ratchet |
| 43, 44, 47, 48 | Stair-stepped pitch glitches — bend jumping between fixed offsets |
| 48 · beat 4 | **Tape stop.** Pitch bend falls on an accelerating curve *and* the tempo drops 74 → 34 across one beat |
| 56 · beat 4 | Stutter into Chorus 2 |
| 61, 65 | Square-wave counter-melody enters |
| 64 · beat 4 | **Beat repeat** — one 1/32 slice re-fired eight times |
| 68 | Biggest fill: 16-step hat ratchet + 10-hit snare stutter, filter closes |
| 75 · beat 3 | The piano's last phrase comes apart |
| 76 · beat 2 | Closing tape stop into the final ritardando |

Continuous through the drummed sections: **CC11 sidechain ducking** on the
Rhodes, pad and texture, keyed to the actual kick hits, and **CC74 filter
sweeps** opening into each chorus and slamming shut into the breakdown.

## Two settings that matter

**1. Pitch bend range = 12 semitones** on channels 1, 2, 4, 5 and 9. The file
requests it via RPN 0, but many plugins ignore RPN and stay at ±2. If yours
does, the tape stops become gentle dips instead of falling off a cliff, and the
bass portamento barely moves. Set it in the plugin.

**2. Sustain pedal.** The grand piano's part is written assuming CC64 — the
comping is deliberately cut short so repeated notes retrigger cleanly, and the
pedal is what makes it ring. If your piano ignores CC64 the part will sound
clipped and staccato. Either map CC64, or lengthen the notes in the piano roll.

## Production notes — the lo-fi side

The arrangement leaves room for the treatment; most of the character comes from
what you do next.

- **Sidechain.** CC11 curves are already in the file for the Rhodes, pad and
  texture. If your instruments don't read CC11, delete those clips and use
  Fruity Peak Controller off the kick instead — same result, less fiddly. The
  bass and the strings are deliberately *not* sidechained: the drone should be
  a constant bed, and pumping strings would fight the ballad.
- **CC11 does a lot of work here.** Besides the sidechain it carries the bass
  swell, the violin and tremolo bowing, and the horn entries. If a patch
  ignores CC11 those parts will sound flat and front-loaded — map it, or use
  the `_clean` file and draw your own volume automation.
- **Bit-crush the Glitch Piano channel** (ch 2) and nothing else. That channel
  exists to be destroyed: Fruity Squeeze, heavy, with the bit depth low. It is
  the piano's damaged reflection, so keep it quieter and further back.
- **Keep the grand piano clean.** Short reverb, light compression, close and
  intimate. Everything around it can be filtered, crushed and smeared — the
  contrast is the point. Resist the urge to lo-fi the thing carrying the tune.
- **High-pass everything except the bass** below ~90 Hz. With a drone holding
  the bottom continuously, anything else down there turns to mud fast.
- **Keep the strings behind the piano**, not beside it. They share a register
  with the melody, so roll off their top end a little and let the piano sit
  forward. If the chorus feels crowded, thin the Rhodes before you thin the
  strings.
- **Tape wobble on the master.** Slight wow/flutter and saturation glues the
  piano to the electronics. Vinyl crackle underneath, low, if you want it.
- **Reinforce the tape stops with Gross Beat** at bars 48 and 76 if you have it.
  The MIDI already bends and slows; Gross Beat on the master makes it physical.
- **Pitch the project down** a semitone or two if you want it heavier. The piano
  part survives it well.

## Arrangement map

| Bars | Section | What happens |
|---|---|---|
| 1–8 | Intro | Solo grand piano. Nothing else. |
| 9–24 | Verse 1 | The bass drone and Rhodes join; drums enter at 13 |
| 25–40 | Chorus 1 | Gated vox pad, bells, full kit, violins enter, filters open |
| 41–48 | Breakdown | The glitch zone; tremolo strings hold the dread; tape stop at 48 |
| 49–56 | Verse 2 | Sparser than the first; the cello counterline enters |
| 57–68 | Chorus 2 | Biggest; full strings, horns from 61, beat repeat at 64 |
| 69–76 | Outro | Back to piano and strings, stutter, tape stop, ritardando |

Harmony is F minor: **i – VI – III – VII** (Fm9 – D♭maj7 – A♭add9 – E♭add9) in
the verses, **VI – VII – v – i** in the choruses. The minor v rather than a
major V is most of why the choruses read as sad rather than triumphant. The
breakdown borrows **G♭ major**, the ♭II, which is the one chord in the piece
that doesn't belong.

## Regenerating

`src/generate_static_bloom.py` is plain Python 3 with no dependencies:

```sh
python3 src/generate_static_bloom.py           # -> midi/static_bloom.mid
python3 src/generate_static_bloom.py --clean   # -> midi/static_bloom_clean.mid
```

The melody phrases (`PHRASE_A`, `PHRASE_CHORUS`, `CELLO_CHORUS`, …), the chord
voicings (`CHORDS`, one row per chord covering every instrument), the form
(`PROG`) and the glitch helpers (`stutter`, `ratchet`, `gate_bar`, `tape_stop`,
`pitch_glitch`, `sidechain`) are all separate and readable, so you can re-cut
the arrangement without touching the MIDI writer. The bass whir is `WHIRR` —
two `(rate_hz, depth_semitones)` pairs.
Humanisation is seeded, so regenerating gives byte-identical output.
