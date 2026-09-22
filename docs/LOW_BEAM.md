# Low Beam — FL Studio 2025 setup guide

A night-drive synthwave track in F# minor, ~5:13, 112 bars of 4/4 at a
constant 86 BPM.

This one is not a finished piece. It is a bed with two holes cut in it: a
vocal, processed the way the "Nightcall" vocal is, and an acoustic guitar in
the closing refrain. Both are written out as guide parts so you can learn
them, and both are meant to be muted and replaced by your own recording.

## Files

| File | Use it when |
|---|---|
| `midi/low_beam.mid` | **Start here.** Everything: the tape stop, the sidechain pumping, the filter sweeps, the guide vocal's phrasing. |
| `midi/low_beam_clean.mid` | Identical notes and tempo, no controller data. |

Both are Standard MIDI File format 1, 480 PPQ, one instrument per channel,
and all sixteen channels are used. The two files contain **exactly the same
4,430 notes** — only the controllers differ.

## Read this first

**The tempo never moves.** Not at the end, not into the refrain, not
anywhere: one tempo event at tick 0 and nothing after it. A ritardando is the
obvious gesture for the last four bars and it is deliberately absent, because
you are going to record into this and a moving grid breaks tempo-synced
delays, defeats punch-ins, and makes comping a nightmare. If you want the
piece to breathe at the end, do it after the vocal and the guitar are
committed, not before.

**Pitch bend range = 12 semitones** on channels 1–9. The file asks via RPN 0
and plenty of plugins ignore that and stay at ±2. At ±2 the tape stop that
kills the track at bar 89 becomes a small wobble instead of the floor falling
out, and it is the whole hinge of the arrangement.

**Three channels are guides, not parts.** Channels 6, 7 and 11 exist to show
you the tune and the timing. Mute them the moment your own take is down.

## Recording into it

A `.mid` file cannot hold audio — there is no room in the format for it. So
the MIDI gets imported **once**, and from then on your FL project is the
song. Your takes live in that project as audio clips, next to the instruments
the MIDI is driving. The `.mid` never changes.

Two numbers that look related and are not: **MIDI channel 6** is the Lead
Vocal guide. **Mixer insert 6** is wherever you happen to record. They are
different systems that both start counting at one. Rename your mixer inserts
(double-click the name) the moment you create them and the confusion goes
away for good.

"Replacing" a guide means one action: **mute the guide channel in the Channel
Rack.** You do not put audio into it. The guide is a MIDI channel driving a
synth and your take is an audio clip; FL keeps those as separate objects, and
seeing them separated in the Channel Rack is correct, not a symptom.

### If a plugin seems to do nothing

Don't judge by ear — the test is ambiguous and you will waste an evening.
**Pull the insert's volume fader to zero and press play.**

- The recording goes silent → routing is right, the problem is the plugin
  (check the small LED beside the slot, and that you are in Song mode).
- The recording still plays → your audio is not passing through that insert
  at all, and no plugin there will ever touch it.

To find where it actually is, play back and watch **which insert's meter
moves**. That is the ground truth, and it sidesteps every version-specific
routing menu.

## The chains, as numbers

Every value below is a starting point that works, not a law. Set them in
order, top to bottom, on the insert your take plays through.

Plugin names and availability shift between FL editions and versions. Where
you cannot find one, the *intent* column tells you what to substitute.

### Lead vocal — the Nightcall chain

| # | Plugin | Setting | Intent |
|---|---|---|---|
| 1 | Fruity Parametric EQ 2 | Band 1 → **Low cut**, **120 Hz** | Keep bass out of the distortion. Non-negotiable — see below |
| 2 | Fruity Blood Overdrive | Preband ~9 o'clock · **Gain ~70%** · Tone centre · Postband centre · Volume down to compensate | The grit |
| 3 | Fruity Squeeze | **Sample rate** reduction first, until it sounds cheap; bit depth only a little | Digital artefacts |
| 4 | Fruity Parametric EQ 2 | Band 1 → **High cut**, **6 kHz** | Kill the fizz the distortion just made |
| 5 | Fruity Limiter (**COMP** tab) | Ratio **4:1** · Attack **20 ms** · Release **80 ms** · Threshold for **4–6 dB** of gain reduction | Level it, *after* the dirt |
| 6 | Fruity Chorus | Depth ~30%, rate slow | 1980s width |
| 7 | Fruity Delay 3 | Sync **3/16** (dotted 1/8 = **523 ms** at 86 BPM) · feedback ~25% | The throw the phrasing leaves room for |
| 8 | Fruity Reeverb 2 | Short bright plate, ~1.2 s, low mix | Air, not a hall |

**Slot 1 before slot 2 is the entire trick.** High-passing after the
distortion instead of before is the difference between a machine voice and a
blown speaker, because low frequencies entering a distortion stage
intermodulate with everything above them.

If it ends up too unintelligible, move slots 2–4 onto a separate insert, send
this one to it, and blend — the words survive on the clean path.

### Lead vocal — the pitch drop

The distortion alone will not do it; the octave drop is at least half the
sound. Right-click the audio clip → **Edison**, then `Tools → Time/pitch
stretch`, pitch **−12 semitones**, formants **not** preserved. Pitcher and
NewTone are easier but live in the higher FL bundles; Edison is the route
that always exists.

You sing the verse and chorus guides **an octave above** written pitch so
that this drop lands them back in key.

### Acoustic guitar — the refrain

Much shorter, because the point of the section is that almost nothing is done
to it.

| # | Plugin | Setting | Intent |
|---|---|---|---|
| 1 | Fruity Parametric EQ 2 | Band 1 → **Low cut**, **90 Hz** | Stay out of the upright bass |
| 2 | Fruity Parametric EQ 2 | Optional dip, **−3 dB around 250 Hz** | Only if it sounds boxy |
| 3 | Fruity Limiter (**COMP** tab) | Ratio **2.5:1** · Attack **30 ms** · Release **150 ms** · **2–3 dB** of reduction | Even out the picking |

**No reverb. No delay. Nothing else.** If it sounds naked, turn the tape
noise on channel 15 up — that bed is what puts the guitar in a room, and it
is the reason the arrangement has one.

## Do this once, not every time

You do not have to rebuild any of the above ever again:

- **Save a chain:** right-click the mixer insert → *Save mixer track state
  as…* → it writes an `.fst`. Load it onto any insert, in any project, and
  the whole chain comes back with its settings.
- **Save the whole song setup:** once the instruments, routing and chains are
  how you want them, `File → Save as template`. Every new session then opens
  with all of it already in place.
- **Save versions as you go:** `low_beam_01.flp`, `_02`, and so on. FL has no
  undo history across sessions, and one bad experiment can cost an evening.

## Channel map

GM program numbers below are the 1-indexed ones FL displays.

| Ch | Track | GM program | Role | Suggested FL instrument |
|---|---|---|---|---|
| 1 | Saw Bass | 39 — Synth Bass 1 | The engine. Eighths, with octave jumps everywhere except the verses | Two detuned saws, short decay, a little glide |
| 2 | **Synth Lead** | 82 — Lead 2 (sawtooth) | The hook. Never plays under a verse | Sytrus/Harmor, saw+square, **glide on**, slow-ish attack |
| 3 | New Age Pad | 89 — Pad 1 (new age) | The wash. High voicing only in the verses | Juno-style poly, slow attack, heavy chorus |
| 4 | FM Bells | 99 — FX 3 (crystal) | 80s sparkle on section tops | A DX7 bell preset, or FM8/Sytrus |
| 5 | **Vocoder Carrier** | 63 — SynthBrass 1 | **Not a part.** See below | Detuned saws — routed *into* the vocoder |
| 6 | **Lead Vocal GUIDE** | 86 — Lead 6 (voice) | The tune you sing. Mute after recording | Anything you can hear over the track |
| 7 | **Answer Vocal GUIDE** | 55 — Voice Oohs | The high second voice. Mute after recording | Anything |
| 8 | Arp Sequence | 81 — Lead 1 (square) | Sixteenths. Jumps an octave in Verse 2 to clear the vocal | Short square/pulse pluck, ping-pong delay |
| 9 | Sub | 40 — Synth Bass 2 | One sine a bar under the saw | Pure sine, no filter movement |
| 10 | Gated Kit | Standard Kit | The gated snare, and it stops dead at bar 89 | See "The snare" below |
| 11 | **Acoustic Guitar GUIDE** | 26 — Acoustic (steel) | The part you play for real. Mute after recording | Any acoustic patch, just to learn it |
| 12 | Upright Bass | 33 — Acoustic Bass | Refrain only, an octave under the guitar | Upright/double bass, finger-style |
| 13 | Felt Piano | 1 — Acoustic Grand | Refrain only, and only above C#5 | Felt or upright piano, soft |
| 14 | Refrain Strings | 49 — String Ensemble 1 | Joins at bar 101, quiet | Small section, not a Hollywood pad |
| 15 | Tape Noise | 123 — Seashore | Hiss and road noise, all 112 bars | **Swap this for real vinyl crackle or tape hiss** |
| 16 | Click | 116 — Woodblock | Count-ins and the refrain pulse. Mute at mixdown | Any click |

## The vocal

The guide on channel 6 is written at **sounding pitch** — what you want to
hear after processing, not what you sing. It is a narrow, repetitive,
speech-like line on purpose; that idiom lives on repetition and menace, not
on range.

| Section | Written (sounding) | You sing (Route A) |
|---|---|---|
| Verses | B2–B3 | B3–B4 |
| Choruses | F#3–E4 | F#4–E5 |
| Refrain | B3–A4 | B3–A4 — as written |

### Getting the pitch right

You cannot simply pitch a take down five semitones the way the stories
suggest, because that also transposes it out of the key. Two routes work:

**Route A — the octave drop (recommended).** Sing the verse and chorus guides
**one octave above** the written pitch, then pitch the recording **down 12
semitones with formant preservation OFF**. It lands exactly on the written
notes, in key, with the formants dragged down into monster territory. In FL:
NewTone, or Edison's pitch shifter with formants unlinked. Not Pitcher with
formant correction on — that is precisely the thing you are trying to defeat.

**Route B — formants only.** Sing at the written pitch and apply a
**formant-only shift of −4 to −6 semitones** with no transposition at all.
You keep the key, you keep your own performance, and you get a much bigger
throat without the octave-down artefacts.

Record both and blend them if you can. Route A has the character, Route B has
the intelligibility.

Note the happy accident in the table: in Route A the verse is sung B3–B4 and
the refrain is sung B3–A4. **They are the same register.** The refrain is
literally the same performance, with nothing done to it — which is the point
of the section.

### The distortion chain

Order matters more than plugin choice here. Left to right:

1. **High-pass at 120 Hz — before anything else.** This is the single most
   important item on the page. Low frequencies entering a distortion stage
   intermodulate with everything above them and turn the whole signal to
   mud. Distorting a full-range vocal is why most attempts at this sound
   like a broken speaker instead of a machine.
2. **Waveshaper or overdrive.** Fruity Waveshaper with a hard S-curve, Blood
   Overdrive, or Fruity Distortion. Drive it until it is unpleasant, then
   back off about a fifth.
3. **Bitcrush.** Fruity Bit Crusher. Reach for **sample-rate reduction
   before bit-depth reduction** — the aliasing is what reads as "cheap
   digital", where bit-crushing alone just reads as noise.
4. **Low-pass at 6 kHz, after the distortion.** Distortion manufactures
   enormous amounts of high harmonic content and almost none of it is
   useful; without this the vocal is all fizz and no weight.
5. **Compress *after* the distortion, never before.** A distortion stage is
   already a compressor. Levelling the signal first just feeds it something
   flat, and it comes out lifeless.
6. **Run it in parallel.** Put steps 1–5 on a send and blend it under the
   pitched vocal rather than replacing it. You control how much of the word
   survives.
7. **Chorus/ensemble**, wide, for the period.

### The vocoder

Channel 5 is not a part and should never reach the master on its own. It is
the **carrier** a vocoder needs: wide chords spanning the vocal's register,
playing only where the vocal sings. In Vocodex, set the **carrier** to
channel 5 and the **modulator** to your vocal, then blend the vocoded result
in alongside the distorted and pitched copies. If you are not vocoding at
all, mute channel 5 — it will sound like a stray brass pad otherwise.

### Delay times at 86 BPM

The tempo is constant, so these are exact for the whole track:

| | ms |
|---|---|
| 1/4 | 697.7 |
| dotted 1/8 | 523.3 |
| 1/8 | 348.8 |
| 1/16 | 174.4 |

Use the dotted eighth on the vocal. The guide phrases stop early in almost
every bar specifically to give that throw somewhere to land — if you sing
through the rests you will lose the effect you are setting up.

## Room for the voice

The arrangement is carved around the vocal rather than laid on top of it, and
in the verses this is exact: **nothing that reaches the mix sounds between B2
and F#4 in bars 17–32 or 57–72 except the voice.** Three things buy that gap:

- the pad drops to a high voicing that bottoms out on F#4
- the bass gives up its octave jumps, which would otherwise land on F#3 —
  the vocal's own note
- the arp in Verse 2 moves up an octave

The kit, the tape hiss and the vocoder carrier are the only things in that
span, and the carrier is going into the vocoder rather than to the mix.

In the choruses the two do sound together, and there the separation is
vertical instead: the synth lead's lowest note is **fourteen semitones above
the vocal's highest**, so the hook doubles the voice instead of masking it.
The lead does not appear in a verse at all.

## The acoustic refrain

### The blackout

Bar 89 is a single F# minor chord hit hard and then dragged down by a
pitch-only tape stop — pitch only, because the tempo map is not allowed to
move. Bars 90, 91 and 92 are **completely empty** on every channel but the
hiss and the click. That is a little over ten seconds of nothing, and it
exists for one reason: an eight-second reverb tail on a synthwave chorus has
to be gone before a dry guitar starts, or the guitar is playing into a room
it does not belong in.

Do not fill those bars. Do not shorten them. They are the transition.

### Playing it

**Capo the second fret.** The progression is then all open shapes:

| Bars | Sounding | You play |
|---|---|---|
| 93–100 | F#m – D – A – E | **Em – C – G – D** (`022000` `x32010` `320003` `xx0232`) |
| 101–108 | F#m – D – Bm7 – E | **Em – C – Am7 – D** (`022000` `x32010` `x02010` `xx0232`) |
| 109–112 | F#m | **Em**, one strum, left to ring |

One bar per chord. This is why the track is in F# minor rather than a key a
synth would have preferred.

The guide is fingerpicked in straight eighths and holds one pattern for
sixteen bars without variation:

```
beat   1    &    2    &    3    &    4    &
string bass top  3rd  2nd  5th  top  3rd  2nd
```

where "bass" is the lowest note of the shape, "5th" the second-lowest, and
"top / 3rd / 2nd" count down from the highest string of the shape. It is
deliberately plain — the guide only has to show you where the chords change,
and a part that shows off is a part you then have to reproduce.

### Recording it dry

**No reverb on this channel.** The file says so in the only language it has:
CC91 is 0 on channel 11, and near-zero on the rest of the refrain.

That raises the obvious problem — a close-miked acoustic guitar in silence
sounds naked. The answer is already in the arrangement. **Channel 15, the
tape noise, swells up under the refrain**, and that bed is what places the
guitar in a room without putting it in a hall. Swap the GM "Seashore" for
real vinyl crackle or tape hiss and this does more for the section than any
reverb would. If you still want depth, use a very short room impulse (under
40 ms) or a slapback — something that reads as walls, not as space.

Everything else in the section is arranged to leave the guitar alone:

| | Range | |
|---|---|---|
| Upright bass | D1–B1 | an octave below the guitar's lowest string |
| **Acoustic guitar** | **F#2–A4** | **the whole middle, uncontested** |
| Felt piano | C#5–B5 | entirely above the guitar |
| Strings | A4–G#5 | and they do not enter until bar 101 |

Bars 93–100 are **guitar, bass and voice and nothing else**. That is the only
way a dry guitar gets to be the loudest thing in a mix.

Practical notes: point the mic at the **12th fret**, not the soundhole — the
soundhole is where the boom lives and you have no reverb to hide it in.
High-pass around 90 Hz to stay clear of the upright. Double-tracking and
panning hard left and right is the usual way to get width without reverb, but
a single centred take is more intimate and this section can carry it.

### There are no drums after bar 88

None. Not a shaker, not a rim, nothing. A gated snare anywhere near a dry
acoustic guitar would undo the entire point of the section.

## The click

Channel 16. Four loud beats in the bar before **every entry you have to
play** — bars 16, 32, 56, 72 and 92 — and then a quiet quarter-note pulse
from bar 89 all the way to the end.

That second part matters. The drums stop at bar 88 and never come back, so
from the blackout onward there is nothing in the arrangement to lock to. You
will be playing the entire acoustic refrain against hiss. Leave the click up
while you track and mute it at mixdown.

## Mixing

- **The gated snare is the period.** Send the snare on channel 10 to a bright
  plate of 1.8–2.4 s and put a noise gate on the *return*, keyed to the
  snare, closing in about 200 ms. That is the sound — a huge reverb cut off
  before it decays, not a big snare.
- **Sidechain everything electronic to the kick.** The pad, arp, bells and
  carrier already carry CC11 ducking curves keyed to the kick ticks; if your
  instruments respond to CC11 you may not need a compressor at all. The
  acoustic section has no pumping anywhere and must not get any.
- **Do not clean up the bass.** The saw and the sine sub are meant to overlap
  and smear. High-pass everything else instead.
- **Leave headroom.** No channel volume in the file exceeds 100 of 127,
  because the two loudest things in the finished record — your vocal and your
  guitar — are not in the file yet.
- **The refrain is a different record.** Narrower, drier, closer, quieter.
  Resist the urge to match its level to the choruses; the drop in scale is
  the payoff for the preceding four minutes.

## Arrangement map

| Bars | Section | What happens |
|---|---|---|
| 1–8 | Intro | Pad, bells and hiss; bass at 5, the hook's first half at 5 |
| 9–16 | Drive | Four on the floor, the full hook, gated snare. Count-in at 16 |
| 17–32 | Verse 1 | Lead vocal. The synth lead is out; the midrange is empty |
| 33–48 | Chorus 1 | Answer vocal to 40, then the hook an octave-plus above to 48 |
| 49–56 | Interlude | The hook alone. No voice anywhere. Count-in at 56 |
| 57–72 | Verse 2 | Lead vocal again, now over the arp, which has moved up an octave |
| 73–88 | Chorus 2 | The biggest one. Tom fill from beat 2 of 88 |
| 89–92 | **Blackout** | One chord, tape-stopped, then three empty bars |
| 93–108 | **Acoustic Refrain** | Guitar, upright, dry voice; piano at 97, strings at 101 |
| 109–112 | Outro | One F#m, left to ring, hiss fading to nothing |

The main loop is **i – VI – III – VII** (F#m9 – Dmaj9 – Aadd9 – E), one bar
per chord. The choruses run **VI – VII – v – i** and the refrain's second
half swaps the III for a **Bm7** (iv), which is the only new chord in the
piece and arrives four minutes in.

## Regenerating

```sh
python3 src/generate_low_beam.py           # -> midi/low_beam.mid
python3 src/generate_low_beam.py --clean   # -> midi/low_beam_clean.mid
```

The chord table (`CHORDS`, one row per chord covering every instrument), the
form (`PROG`, `LOOP_A`, `LOOP_B`, `LOOP_C`) and the melodies (`VERSE_VOX`,
`CHORUS_VOX`, `ANSWER_VOX`, `REFRAIN_END`, `HOOK_A`, `HOOK_B`) are all
separate and readable. The guitar voicings live in the `gtr` field of each
chord and are the literal capo-2 open shapes, which is why they are uneven
lengths — a G shape has six strings and a D shape has four. Humanisation is
seeded, so output is byte-identical on regeneration.

The synth lead and both vocal guides are rendered by `src/expressive.py`, the
same portamento/vibrato/swell engine that drives Hollow Hour's theremin and
Ashfall's CS-80, retuned three ways: quick and wide for the lead, deep-scoop
and late-vibrato for the guide vocal, and nearly straight for the refrain,
where there is no processing left to hide behind.
