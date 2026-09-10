# Hollow Hour — FL Studio 2025 setup guide

A dark, haunting ballad in D minor, ~4:43, 64 bars of 4/4 at roughly 58 BPM
with sectional rubato and a closing ritardando.

## Files

| File | Use it when |
|---|---|
| `midi/hollow_hour.mid` | **Start here.** Full performance: pitch-bend glides, vibrato, CC11 swells, mod wheel. |
| `midi/hollow_hour_clean.mid` | Notes, tempo and program changes only. Easier to edit by hand, or if your instruments react badly to dense controller data. |

Both are Standard MIDI File format 1, 480 PPQ, one instrument per MIDI channel.

## Importing

1. **File → Import → MIDI file…** (or drag the `.mid` onto the Playlist).
2. In the import dialog, keep **tempo / time-signature import** enabled — the
   tempo map carries the rubato and the final ritardando, and without it the
   ending loses its collapse.
3. Enable **controller / automation import** if you loaded `hollow_hour.mid`.
   That is what turns the theremin's pitch bend and expression into automation
   clips. If you skip it you get the notes but a flat, keyboard-ish lead.
4. Let FL create **one channel per MIDI channel**. Track names come across, so
   the Channel Rack will already read "Theremin Lead", "Music Box", and so on.

## Channel map

GM program numbers below are the 1-indexed ones FL displays.

| Ch | Track | GM program | Role in the arrangement | Suggested FL instrument |
|---|---|---|---|---|
| 1 | Theremin Lead | 86 — Lead 6 (voice) | The voice of the piece | Sytrus or 3xOsc, single sine, **mono + portamento** |
| 2 | Glass Armonica | 99 — FX 3 (crystal) | Answers the theremin in its silences | Sakura, Ogun, or FLEX glass/bell |
| 3 | Bowed Glass Pad | 93 — Pad 5 (bowed) | The cold sustained fabric | Sakura bowed, Harmor pad, FLEX strings |
| 4 | Ghost Choir | 53 — Choir Aahs | Enters when the floor drops away | FLEX vocal pad, Sytrus choir |
| 5 | Harp | 47 — Orchestral Harp | Rolling broken chords | FLEX harp, DirectWave harp |
| 6 | Music Box | 11 — Music Box | The fragile hook: opens and closes the piece | FLEX music box / celesta |
| 7 | Contrabass Drone | 44 — Contrabass | The lament bass, D–C–B♭–A | Bowed bass, or a sine sub under a cello |
| 8 | Atmosphere | 100 — FX 4 (atmosphere) | Near-subliminal open fifth | Any drone pad, keep it very low in the mix |
| 9 | Reverse Cymbal Risers | 120 — Reverse Cymbal | Swells that land on each section downbeat | Reverse cymbal sample, or a reversed crash |
| 10 | Heartbeat Percussion | Standard Kit | Kick heartbeat, low toms, dark cymbals, triangle | FPC / any GM-mapped kit |

Channel 10 uses GM drum mapping: 36 kick, 41 low tom, 45/48 toms, 49 crash,
52 Chinese cymbal, 81 open triangle.

## Making the theremin actually sound like a theremin

A theremin has no keys. Three things in the MIDI create that illusion, and one
of them needs a setting on your side.

**1. Set the lead's pitch bend range to 12 semitones.** This is the one thing
worth doing by hand. The file sends RPN 0 (bend range = 12) on channel 1, but
plenty of plugins ignore RPN and sit at the ±2 default. If yours does, the
glides still work — they just scoop a fraction of the way instead of sweeping
the full interval, which sounds timid rather than eerie. In Sytrus, Harmor and
FLEX it's a pitch-bend-range control in the plugin; for FL's own per-channel
pitch automation it's the range on the Channel Settings pitch knob.

*Fallback if you can't get bend range to behave:* load
`hollow_hour_clean.mid` instead and switch the lead channel to **mono with
portamento/slide** turned up. FL will glide between the notes itself. You lose
the hand vibrato and the swells, so add an LFO on pitch (~4.5 Hz, delayed about
a third of a second so it fades in) and an LFO or envelope on volume.

**2. Vibrato is already written in** as a 4.6 Hz pitch-bend LFO that widens the
longer a note is held — the way a player's hand steadies and then opens up.
Mod wheel (CC1) tracks the same curve, so if your synth maps mod → vibrato you
get it twice; pull CC1 back if it doubles up too strongly.

**3. The volume hand is CC11.** Every note blooms and fades instead of starting
abruptly. Map CC11 to the lead's volume (not the mixer fader) so the swells
survive. Without it the lead will sound correct but blunt.

The long note at bars 55–56 is a deliberate octave fall to silence — the
theremin's last gesture before the music box is left alone.

## Mixing suggestions

- Long reverb on everything. Fruity Convolver with a cathedral/hall impulse, or
  Fruity Reeverb 2 with a long decay and the high end rolled off.
- A long, dark delay (Fruity Delay 3) on the theremin and armonica; feedback
  high enough that phrases smear into each other.
- Roll the low end off the pad and choir so the contrabass has the bottom.
- Keep the atmosphere channel almost inaudible — you should notice it only when
  you mute it.
- The heartbeat should be felt, not heard. Low-passed kick, no click.

## Arrangement map

| Bars | Section | What happens |
|---|---|---|
| 1–8 | I. Winding | Music box alone; pad and drone breathe in at bar 5 |
| 9–24 | II. The Lament | Theremin states the descending theme; harp enters at 13 |
| 25–32 | III. The Hollow | Choir and heartbeat enter, armonica answers, Neapolitan E♭ |
| 33–48 | IV. Apex | Full arrangement; the theremin climbs to F6 at bar 42 |
| 49–56 | V. Collapse | Isolated sighs, then one long fall into silence |
| 57–64 | VI. Music Box Alone | The box winds down and sags flat on the last note |

Harmony is the lament bass — a descending tetrachord D–C–B♭–A — voiced so the
upper parts barely move while the bass falls. The bridge borrows E♭ major, the
Neapolitan, which is where most of the dread comes from.

## Regenerating

`src/generate_hollow_hour.py` is plain Python 3 with no dependencies:

```sh
python3 src/generate_hollow_hour.py            # -> midi/hollow_hour.mid
python3 src/generate_hollow_hour.py --clean    # -> midi/hollow_hour_clean.mid
python3 src/generate_hollow_hour.py -o /path/to/other.mid
```

Melody, harmony and arrangement live in readable tables near the top
(`THEREMIN`, `CHORDS`, `PROG`), so it is easy to transpose, re-voice, or
re-cut the form without touching the MIDI writer. Humanisation is seeded, so
regenerating gives byte-identical output.
