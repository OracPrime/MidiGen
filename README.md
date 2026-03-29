# midiGen

Generate guitar-style MIDI files from Python song definitions.

This project does not run inside Reaper. You run Python scripts to generate `.mid` files, then import those MIDI files into Reaper.

## What It Produces

The default entry point generates four files for Nine Inch Nails "Hurt":

- `Hurt_Sequence.mid`: strummed guitar-note sequence with markers/lyrics.
- `Hurt_Chords.mid`: cue/label track with chord names over time.
- `Hurt_Barre_Sequence.mid`: same sequence using barre voicings.
- `Hurt_Barre_Chords.mid`: same chord track for barre voicings.

## Quick Start

1. Install Python 3.10+.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Generate MIDI files:

```bash
python main.py
```

`main.py` currently calls `hurt.generate()`.

## Reaper Workflow

1. Run `python main.py` (or another song module) in this repo.
2. Open Reaper.
3. Import one or both generated MIDI files.
4. Assign your instrument/VST (for example, a guitar patch) to the sequence track.
5. Use the chord/marker track as arrangement guidance.

Important: Reaper is the destination for playback/editing. Python is the generation step.

## Project Files

- `main.py`: project entry point.
- `hurt.py`: "Hurt" song definition (sections, lyrics, output names).
- `midi_lib.py`: MIDI builder, marker/lyric/cue meta-event support.
- `strums.py`: strum engine and reusable strum patterns.
- `chords.py`: guitar chord voicings as MIDI note lists.

## How Chords Work

`chords.py` defines chord dictionaries:

- `OPEN_CHORDS`: open voicings when available.
- `BARRE_CHORDS`: barre-only voicings.
- `SPECIAL_CHORDS`: slash chords and custom cases (for example, `G/B`).

Song builders pass either a single chord dict or a list of dicts to `build_song(...)`.

Example from `hurt.py`:

- `chords=[OPEN_CHORDS, SPECIAL_CHORDS]`
- `chords=[BARRE_CHORDS, SPECIAL_CHORDS]`

The builder merges these so earlier dictionaries in the list have priority, while later dictionaries fill missing chord names.

Each chord maps to MIDI note numbers, for example:

```python
'Em': [40, 47, 52, 55, 59, 64]
```

## How Patterns And Song Structure Work

Chord progressions are lists of `(chord_name, duration_in_beats)` tuples:

```python
VERSE = [('G', 2), ('A', 2), ('Em', 4)]
```

Sections define how those progressions are arranged:

```python
{
    'pattern': VERSE,
    'repeats': 8,
    'label': 'Verse 1',
    'strum': VERSE_STRUM,
    'lyrics': VERSE1_LYRICS,
}
```

- `pattern`: the chord progression.
- `repeats`: how many bars/iterations of that progression.
- `label`: timeline marker text.
- `strum`: strum pattern from `strums.py`.
- `lyrics`: optional lyric events.

Lyric entries use `(bar_index_within_section, beat_offset, text)`:

```python
(0, 0, "I hurt my-")
```

## How Strums Work

`strums.py` describes strum feel using entries like:

```python
(beat_offset, direction, velocity_scale, is_muted)
```

Example:

```python
(1.5, 'up', 0.55, False)
```

The engine humanizes timing and velocity for a less mechanical result.

## Add A New Song

Use this flow to add another song generator.

1. Create a new module, for example `my_song.py`.
2. Import chord sets, strum patterns, and `build_song`.
3. Define tempo, progression patterns, optional lyric tuples, and `SECTIONS`.
4. Implement `generate()` calling `build_song(...)`.
5. Update `main.py` to call your new `generate()` function.
6. Run `python main.py` and import the output `.mid` files into Reaper.

Starter template:

```python
from chords import OPEN_CHORDS, SPECIAL_CHORDS
from strums import VERSE_STRUM, CHORUS_STRUM
from midi_lib import build_song

TEMPO = 100
SEPARATE_CHORD_TRACK = True

VERSE = [('Em', 4), ('C', 4), ('G', 4), ('D', 4)]
CHORUS = [('C', 4), ('G', 4), ('D', 4), ('Em', 4)]

SECTIONS = [
    {'pattern': VERSE, 'repeats': 4, 'label': 'Verse', 'strum': VERSE_STRUM},
    {'pattern': CHORUS, 'repeats': 2, 'label': 'Chorus', 'strum': CHORUS_STRUM},
]

def generate():
    build_song(
        chords=[OPEN_CHORDS, SPECIAL_CHORDS],
        sections=SECTIONS,
        tempo=TEMPO,
        separate_chord_track=SEPARATE_CHORD_TRACK,
        sequence_file='MySong_Sequence.mid',
        chords_file='MySong_Chords.mid',
    )
```

If you need new chord names, add them to `SPECIAL_CHORDS` or one of the main chord dictionaries in `chords.py`.

## Notes

- Tempo is set per song module.
- Markers/cues/lyrics are embedded as MIDI meta events for DAW visibility.
- Generated files are standard MIDI and can be imported into other DAWs, not only Reaper.