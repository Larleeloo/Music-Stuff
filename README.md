# Music-Stuff

Music and MIDIs.

## Hollow Hour

A dark, haunting ballad in D minor for FL Studio 2025 — 64 bars, ~4:43, led by
a theremin-style voice with pitch-bend glides, hand vibrato and volume swells
written into the MIDI.

```
midi/hollow_hour.mid          full performance (bend, vibrato, CC11 swells)
midi/hollow_hour_clean.mid    notes + tempo only, easier to hand-edit
src/generate_hollow_hour.py   the generator (Python 3, no dependencies)
docs/FL_STUDIO_SETUP.md       import steps, channel map, sound-design notes
```

Ten instrument channels: theremin lead, glass armonica, bowed glass pad, ghost
choir, harp, music box, contrabass drone, atmosphere, reverse-cymbal risers and
a heartbeat percussion track. Harmony is the lament bass — a descending
tetrachord D–C–B♭–A — with a Neapolitan E♭ in the bridge.

**Read [`docs/FL_STUDIO_SETUP.md`](docs/FL_STUDIO_SETUP.md) before importing.**
One setting matters: the lead's pitch bend range must be **12 semitones** or the
theremin glides come out timid.

Regenerate with:

```sh
python3 src/generate_hollow_hour.py
python3 src/generate_hollow_hour.py --clean
```

Output is deterministic — humanisation is seeded, so regenerating produces
byte-identical files.
