# Static Bloom — FL Studio 2025 setup guide

A sad glitch-pop ballad in F minor, ~4:05, 76 bars of 4/4 at 76 BPM, built
around a grand piano. Half-time drums, an 808 sub, and a glitch vocabulary
that is written into the note data rather than left to plugins.

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
   what brings in the sustain pedal, the 808 glides, the tape stops and the
   sidechain curves.
4. Let FL create **one channel per MIDI channel**; track names carry over.

## Channel map

GM program numbers below are the 1-indexed ones FL displays.

| Ch | Track | GM program | Role | Suggested FL instrument |
|---|---|---|---|---|
| 1 | **Grand Piano** | 1 — Acoustic Grand | **The song.** Melody, rolled voicings, pedal | A good piano library; keep it close and fairly dry |
| 2 | Glitch Piano | 4 — Honky-tonk | Chopped echoes of the grand, an eighth behind | Same piano, then bit-crush it hard |
| 3 | Rhodes Bed | 5 — Electric Piano 1 | Warm harmonic bed under the piano | FLEX Rhodes, or a DirectWave EP |
| 4 | Sub 808 | 39 — Synth Bass 1 | 808 sub with glides into each root | 3xOsc sine, or an 808 sample with portamento |
| 5 | Glass Bells | 10 — Glockenspiel | Arpeggio bursts, later pure ratchets | FLEX bells / celesta |
| 6 | Vox Pad | 55 — Voice Oohs | The wordless stand-in for a vocal | FLEX vocal pad, Harmor, Sytrus choir |
| 7 | Granular Texture | 97 — FX 1 (rain) | Air and grit, almost subliminal | Any noisy pad; keep it very low |
| 8 | Reverse FX | 120 — Reverse Cymbal | Swells resolving on section downbeats | Reversed crash or reversed piano |
| 9 | Blip Lead | 81 — Lead 1 (square) | The flare: chiptune counter-melody | 3xOsc square, no filter, short decay |
| 10 | Glitch Drums | Standard Kit | Half-time kit, trap hats, glitch fills | FPC, or your own one-shots |

Channel 10 uses GM drum mapping: 36 kick, 40 electric snare, 39 clap, 37 rim,
42 closed hat, 46 open hat, 49 crash, 70 shaker.

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
808 glides barely move. Set it in the plugin.

**2. Sustain pedal.** The grand piano's part is written assuming CC64 — the
comping is deliberately cut short so repeated notes retrigger cleanly, and the
pedal is what makes it ring. If your piano ignores CC64 the part will sound
clipped and staccato. Either map CC64, or lengthen the notes in the piano roll.

## Production notes — the lo-fi side

The arrangement leaves room for the treatment; most of the character comes from
what you do next.

- **Sidechain.** CC11 curves are already in the file. If your instruments don't
  read CC11, delete those clips and use Fruity Peak Controller off the kick
  instead — same result, less fiddly.
- **Bit-crush the Glitch Piano channel** (ch 2) and nothing else. That channel
  exists to be destroyed: Fruity Squeeze, heavy, with the bit depth low. It is
  the piano's damaged reflection, so keep it quieter and further back.
- **Keep the grand piano clean.** Short reverb, light compression, close and
  intimate. Everything around it can be filtered, crushed and smeared — the
  contrast is the point. Resist the urge to lo-fi the thing carrying the tune.
- **The 808 needs saturation** or it disappears on phones. Fruity Fast Dist or
  Fruity Waveshaper, then a high-pass on everything else below ~90 Hz.
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
| 9–24 | Verse 1 | 808 and Rhodes join; drums enter at 13 |
| 25–40 | Chorus 1 | Gated vox pad, bells, full kit, filters open |
| 41–48 | Breakdown | The glitch zone; tape stop at 48 |
| 49–56 | Verse 2 | Sparser than the first, more electronic |
| 57–68 | Chorus 2 | Biggest; square lead, beat repeat at 64 |
| 69–76 | Outro | Back to solo piano, stutter, tape stop, ritardando |

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

The melody phrases (`PHRASE_A`, `PHRASE_CHORUS`, …), the chord voicings
(`CHORDS`), the form (`PROG`) and the glitch helpers (`stutter`, `ratchet`,
`gate_bar`, `tape_stop`, `pitch_glitch`, `sidechain`) are all separate and
readable, so you can re-cut the arrangement without touching the MIDI writer.
Humanisation is seeded, so regenerating gives byte-identical output.
