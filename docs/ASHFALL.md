# Ashfall — FL Studio 2025 setup guide

A sad cinematic ballad in the Blade Runner 2049 idiom, C# minor, ~6:06,
76 bars of 4/4 at roughly 54 BPM, built around a grand piano.

## Files

| File | Use it when |
|---|---|
| `midi/ashfall.mid` | **Start here.** Everything: portamento, vibrato, detune drift, swells, sustain pedal. |
| `midi/ashfall_clean.mid` | Identical notes and tempo, no controller data. |

Both are Standard MIDI File format 1, 480 PPQ, one instrument per channel. The
two files contain **exactly the same notes** — only the controllers differ.

Note that this one leans much harder on controller data than the other pieces:
the clean file is 11 KB against the full file's 102 KB. Almost every part is
shaped by CC11 rather than by note velocity, so `ashfall_clean.mid` will sound
flat and blocky by comparison. Use it for editing, not for listening.

## What makes it sound like 2049

Less about patches than about four structural habits, all written into the data:

**1. A pedal that refuses to move.** The sub sits on C#1 for 64 of the 76 bars
while the harmony changes above it. Chords that would otherwise resolve just
re-colour the same note. The bass only starts moving at bar 53 — and that one
change is most of why the last section feels like the ground opens up.

**2. Voicings that barely move.** C#m9, Amaj9 and F#m11 share the tones E, G#
and B — heard as 3-5-7, then 5-7-9, then 7-9-11. The strings hold a single
chord shape straight through those changes; only the bass tells you anything
happened. The one chord that genuinely doesn't belong is **D major**, the
Neapolitan, and it lands at the end of every eight-bar loop.

**3. Detuning as an instrument.** The brass wall drifts ±29 cents and the sub
drone ±15 cents, on slow LFOs at rates that don't share factors, so the beating
between them never settles into a pattern. Nothing is quite in tune with
anything for very long. This is deliberate — don't "fix" it.

**4. Everything swells.** Almost no part starts at its own volume. CC11 does
the attack, so entries bloom out of the rain rather than beginning. **If your
instruments ignore CC11, this piece will not work** — that is the single most
important thing on this page.

## Channel map

GM program numbers below are the 1-indexed ones FL displays.

| Ch | Track | GM program | Role | Suggested FL instrument |
|---|---|---|---|---|
| 1 | **Grand Piano** | 1 — Acoustic Grand | The theme, and the only intimate thing in the mix | A good piano library, close but with a long tail |
| 2 | **CS-80 Lead** | 63 — SynthBrass 1 | The Vangelis lead: slides, delayed vibrato, huge swells | Sytrus or Harmor, saw+square, **glide on**, slow attack |
| 3 | **Brass Wall** | 64 — SynthBrass 2 | Open fifths, detuned, enormous | Layer 2–3 detuned saw pads; no thirds |
| 4 | Sub Drone | 90 — Pad 2 (warm) | The C# pedal. Never stops for the whole piece | Sine/triangle sub + a warm pad, layered |
| 5 | Sub Pulse | 39 — Synth Bass 1 | Machine heartbeat, two throbs a bar | Soft sine with a slow attack — not a pluck |
| 6 | Choir | 53 — Choir Aahs | Wordless voices from bar 29 | Any choir; heavy reverb, no consonants |
| 7 | Strings | 49 — String Ensemble 1 | Sustained high, holds through chord changes | Legato strings, slow attack |
| 8 | Cellos | 43 — Cello | Low sustain under the wall | Cello section, sustained |
| 9 | Ondes Wail | 86 — Lead 6 (voice) | Keening above the climax | Ondes/theremin patch, or a bowed-glass lead |
| 10 | Impacts | Standard Kit | Rare, enormous hits. No kit pattern | Big room kick, floor tom, dark cymbals |
| 11 | Taiko | 117 — Taiko Drum | The low impacts at chord changes | Taiko, or any huge low drum |
| 12 | Timpani | 48 — Timpani | Rolls into downbeats, hits on the Neapolitan | Timpani; pitches stay in the real 40–53 range |
| 13 | Reverse Swells | 120 — Reverse Cymbal | Swells resolving on section downbeats | Reversed cymbal, reversed piano, reversed choir |
| 14 | Hologram Flicker | 104 — FX 8 (sci-fi) | The one glitch element | Short digital blip; bit-crush it |
| 15 | Rain Bed | 123 — Seashore | Continuous wash under the whole piece | **Swap this for an actual rain loop** |

Channel 16 is free.

## Three settings that matter

**1. CC11 must reach your instruments.** See habit 4 above. Map it to amp
volume, not to a mixer fader, on every channel except the piano and the
percussion.

**2. Pitch bend range = 12 semitones** on channels 2, 3, 4, 9 and 14. The file
requests it via RPN 0, but plenty of plugins ignore RPN and stay at ±2. At ±2
the CS-80's slides shrink to a sixth of their written size and the detune drift
becomes inaudible.

**3. Turn glide/portamento ON for the CS-80 lead** and set it slow. The MIDI
already bends between notes, so this is belt-and-braces — but a real CS-80
part is continuous, and the two together sell it. The lead is written as
unbroken two-bar notes precisely so every note change is a slide, never an
attack.

## The rain

Channel 15 is GM "Seashore", which is a stand-in. **Replace it with a real rain
loop** — that single swap does more for the atmosphere than any other change
you can make. It runs continuously from bar 1 to the end and carries its own
CC11 arc: loudest in the intro and the outro, ducked under the wall and the
climax, so it feels like the mix breathes around it rather than sitting behind
a static noise floor.

## Arrangement map

| Bars | Section | What happens |
|---|---|---|
| 1–8 | I. Rain | Sub and rain alone; the piano enters at bar 5 |
| 9–24 | II. First Light | The theme; strings at 17, the sub pulse at 13 |
| 25–40 | III. The Wall | Detuned brass, choir, taiko; CS-80 enters at 29 |
| 41–52 | IV. Hologram | Everything drops away. Piano, rain, and the flicker |
| 53–68 | V. Ascension | **The bass finally moves.** Full wall, CS-80 and ondes |
| 69–76 | VI. Ashfall | Back to piano and rain; one last flicker at 74 |

The main loop is **i – VI – iv – ♭II** (C#m9 – Amaj9 – F#m11 – Dmaj7), two bars
per chord. The climax switches to **III – VII – i – VI** and lets the bass track
it. The tempo drifts between 50 and 57 BPM by section and ritards to a halt over
the last three bars.

## Mixing suggestions

- **Reverb on a scale that is nearly silly.** 8–12 second tails on the brass,
  choir and strings; the piano gets a shorter, darker plate so it stays legible.
- **Do not tighten the low end.** The drone and the pulse are meant to overlap
  and smear. High-pass everything else aggressively instead — the piano can
  lose everything under 120 Hz and be fine.
- **Saturate the brass wall** until it distorts slightly at the peaks. Clean
  synth brass sounds small; the wall should feel like it is clipping the room.
- **The piano is the only dry thing.** Every entry it makes should feel closer
  than everything around it. That contrast is the emotional content.
- **Sidechain nothing.** There is no groove to duck against, and pumping would
  destroy the stillness.
- Keep the flicker channel quiet and hard-panned. It should read as a fault in
  the recording, not as a musical part.

## Regenerating

```sh
python3 src/generate_ashfall.py           # -> midi/ashfall.mid
python3 src/generate_ashfall.py --clean   # -> midi/ashfall_clean.mid
```

The chord table (`CHORDS`, one row per chord covering every instrument), the
form (`PROG`, `LOOP_A`, `LOOP_B`), the themes (`THEME_A`, `THEME_B`, …) and the
lead lines (`CS80_LINE`, `ONDES_LINE`) are all separate and readable. The
pedal-versus-moving-bass decision is the one-line `bass_root`. Detune rates
live in the `drift` calls. Humanisation is seeded, so output is byte-identical
on regeneration.

The CS-80 and ondes parts are rendered by `src/expressive.py`, the same
portamento/vibrato/swell engine that drives Hollow Hour's theremin — retuned
via its `Voice` fields to slide and swell several times more slowly.
