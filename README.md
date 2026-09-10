# Music-Stuff

Music and MIDIs. Each piece ships as a Standard MIDI File plus the
dependency-free Python that generated it, so the arrangement stays editable.

```
midi/     the .mid files - this is what you import
src/      generators (Python 3, standard library only)
docs/     per-piece FL Studio setup and sound-design guides
```

## Pieces

### Hollow Hour — dark ballad · D minor · ~4:43

A theremin-style lead over a lament bass, with glass armonica, bowed glass pad,
ghost choir, harp, music box and a contrabass drone. The theremin has no keys,
so the glides, hand vibrato and volume swells are written into the MIDI itself.

`midi/hollow_hour.mid` · [setup guide](docs/HOLLOW_HOUR.md)

### Static Bloom — sad glitch-pop · F minor · ~4:05

A grand piano ballad with the electronics arranged around it rather than on top
of it: 808 sub with glides, Rhodes, gated vox pad, glockenspiel ratchets and a
square-wave counter-melody. Stutters, beat repeats, pitch glitches and two tape
stops — one of which drags the tempo map down with it.

`midi/static_bloom.mid` · [setup guide](docs/STATIC_BLOOM.md)

## Using them

Import the `.mid` into your DAW with **tempo import enabled** — both pieces use
tempo as a compositional device, not just a speed setting. Each piece also ships
a `*_clean.mid` with identical notes but no controller data, for hand-editing.

**Read the setup guide before importing.** Both pieces need the lead
instrument's **pitch bend range set to 12 semitones**; the files request it via
RPN 0, but plenty of plugins ignore that and stay at ±2, which quietly flattens
the glides and tape stops.

## Regenerating

```sh
python3 src/generate_hollow_hour.py            # add --clean for the notes-only file
python3 src/generate_static_bloom.py
```

`src/smf.py` is the shared MIDI writer. Output is deterministic — humanisation
is seeded, so regenerating produces byte-identical files.
