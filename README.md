# Music-Stuff

Music and MIDIs. Each piece ships as a Standard MIDI File plus the
dependency-free Python that generated it, so the arrangement stays editable.

```
midi/     the .mid files - this is what you import
src/      generators plus three shared modules (Python 3, stdlib only)
docs/     per-piece FL Studio setup and sound-design guides
```

## Pieces

### Hollow Hour — dark ballad · D minor · ~4:43

A theremin-style lead over a lament bass, with glass armonica, bowed glass pad,
ghost choir, harp, music box and a contrabass drone. The theremin has no keys,
so the glides, hand vibrato and volume swells are written into the MIDI itself.

`midi/hollow_hour.mid` · [setup guide](docs/HOLLOW_HOUR.md)

### Static Bloom — sad glitch-pop · F minor · ~4:05

A grand piano ballad with everything else arranged around it rather than on top
of it: a whirring ethereal bass drone, a string orchestra that enters section by
section, Rhodes, gated vox pad, glockenspiel ratchets and a square-wave
counter-melody. Stutters, beat repeats, pitch glitches and two tape stops — one
of which drags the tempo map down with it.

`midi/static_bloom.mid` · [setup guide](docs/STATIC_BLOOM.md)

### Ashfall — cinematic ballad · C# minor · ~6:06

A grand piano against a Blade Runner 2049 palette: a CS-80 lead sliding between
notes, a detuned brass wall, choir, strings, taiko and timpani, an ondes-style
wail, and rain running underneath the whole thing. The bass holds one pedal
note for 64 of 76 bars — when it finally moves, the floor drops out.

`midi/ashfall.mid` · [setup guide](docs/ASHFALL.md)

## Using them

Import the `.mid` into your DAW with **tempo import enabled** — all three use
tempo as a compositional device, not just a speed setting — and with
**controller/automation import enabled**, which is what carries the pitch bend
and the volume shaping. Each piece also ships a `*_clean.mid` with identical
notes but no controller data, for hand-editing.

**Read the setup guide before importing.** All three need their lead
instrument's **pitch bend range set to 12 semitones**; the files request it via
RPN 0, but plenty of plugins ignore that and stay at ±2, which quietly flattens
every glide, tape stop and detune in the piece.

## Shared modules

| Module | What it is |
|---|---|
| `src/smf.py` | The MIDI writer. Format 1, 480 PPQ, no running status, with event priorities so a note-off always lands before the bend reset before the next note-on. |
| `src/expressive.py` | Portamento, vibrato and CC11 swells for keyless instruments. One engine, retuned by its `Voice` fields — it drives Hollow Hour's theremin, Ashfall's CS-80 and Ashfall's ondes. |
| `src/glitch.py` | Stutters, ratchets and stair-stepped pitch glitches. |

## Regenerating

```sh
python3 src/generate_hollow_hour.py            # add --clean for the notes-only file
python3 src/generate_static_bloom.py
python3 src/generate_ashfall.py
```

Output is deterministic — humanisation is seeded, so regenerating produces
byte-identical files.
