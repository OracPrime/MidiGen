"""
Metallica — "Master of Puppets" (title track)
Generates separate MIDI files for each instrument:
  - Rhythm Guitar   (palm-muted power-chord thrash)
  - Lead Guitar     (harmonies, solos, clean melodies)
  - Bass Guitar     (Cliff Burton style — gallop + clean section)
  - Drums           (Lars Ulrich — thrash beats, double bass, dynamics)
  - Vocal Melody    (guide track for singing)
  - Lyrics / Chord Cues (markers, lyrics, cue points)

All note-on velocities are chosen to reflect real performance dynamics.
Guitar parts use short durations for palm mutes vs. sustained for open chords.
Drums use GM standard mapping on channel 9.
"""

from midiutil import MIDIFile
from midi_lib import add_marker, add_lyric, add_cue
import random

# ========================  CONSTANTS  ========================

TEMPO_FAST  = 212       # thrash sections
TEMPO_CLEAN = 112       # interlude / clean section
TICKS_PER_BEAT = 960    # high resolution

# GM Drum map
KICK        = 36
SNARE       = 38
SNARE_RIM   = 37
HH_CLOSED   = 42
HH_OPEN     = 46
HH_PEDAL    = 44
RIDE        = 51
RIDE_BELL   = 53
CRASH1      = 49
CRASH2      = 57
CHINA       = 52
TOM_HI      = 48
TOM_MID     = 45
TOM_LOW     = 41
TOM_FLOOR   = 43

# Power chord voicings (root on low E / A string) -- drop voicings for metal
def power_chord(root, string='E'):
    """Return [root, fifth, octave] for a power chord."""
    return [root, root + 7, root + 12]

def power_chord_5th_string(root):
    """Power chord rooted on A string."""
    return [root, root + 7, root + 12]

# Common power chords used in MoP
E5  = power_chord(40)          # E2
F5  = power_chord(41)          # F2
F5s = power_chord(42)          # F#2
G5  = power_chord(43)          # G2
Ab5 = power_chord(44)          # Ab2
A5  = power_chord(45)          # A2
Bb5 = power_chord(46)          # Bb2
B5  = power_chord(47)          # B2
C5  = power_chord_5th_string(48)  # C3
D5  = power_chord_5th_string(50)  # D3
Eb5 = power_chord_5th_string(51)  # Eb3

# Clean chord voicings for interlude
Am_clean  = [45, 52, 57, 60, 64]         # Am open
G_clean   = [43, 47, 55, 59, 62, 67]     # G open variant
Em_clean  = [40, 47, 52, 55, 59, 64]     # Em open
C_clean   = [48, 52, 55, 60, 64]         # C open
D_clean   = [50, 57, 62, 66]             # D open
B7_clean  = [47, 54, 57, 63, 66]         # B7

# Single notes for bass
E2 = 40; F2 = 41; Fs2 = 42; G2 = 43; Ab2 = 44; A2 = 45
Bb2 = 46; B2 = 47; C3 = 48; D3 = 50; Eb3 = 51; E3 = 52

# ========================  HUMANIZE  ========================

HUMANIZE_TIME = 0.008
HUMANIZE_VEL  = 6

def _h_time():
    return random.uniform(-HUMANIZE_TIME, HUMANIZE_TIME)

def _h_vel(v, spread=HUMANIZE_VEL):
    return max(1, min(127, v + random.randint(-spread, spread)))

# ========================  NOTE HELPERS  ========================

def add_note(midi, track, ch, pitch, time, dur, vel):
    """Add a single note with humanization."""
    midi.addNote(track, ch, pitch, max(0, time + _h_time()), dur, _h_vel(vel))

def add_chord(midi, track, ch, pitches, time, dur, vel, strum=0.01):
    """Add a chord with slight strum spread."""
    for i, p in enumerate(pitches):
        add_note(midi, track, ch, p, time + i * strum, dur, vel - i * 2)

def add_pm_chord(midi, track, ch, pitches, time, vel):
    """Palm-muted power chord — very short duration."""
    for i, p in enumerate(pitches):
        add_note(midi, track, ch, p, time + i * 0.008, 0.08, vel - i * 2)

def add_drum(midi, track, pitch, time, vel, dur=0.15):
    """Add a drum hit on channel 9."""
    midi.addNote(track, 9, pitch, max(0, time + _h_time()), dur, _h_vel(vel, 4))


# ================================================================
#  SONG SECTION BEAT LENGTHS  (at 212 BPM in 4/4)
#
#  The song is ~8:36.  We'll define beat positions for each section.
#  1 bar = 4 beats.
# ================================================================

# Section lengths in bars (at TEMPO_FAST unless noted)
# These are approximate but musically faithful lengths.

INTRO_BARS        = 4      # feedback/harmonics build
MAIN_RIFF_BARS    = 8      # "duh duh duh" gallop riff (x2)
VERSE1_BARS       = 16     # verse riff under vocals
PRECHORUS1_BARS   = 4      # ascending power chords
CHORUS1_BARS      = 8      # "Master! Master!"
INTERLUDE1_BARS   = 4      # transition to verse 2
VERSE2_BARS       = 16
PRECHORUS2_BARS   = 4
CHORUS2_BARS      = 8
CLEAN_BARS        = 32     # clean interlude section (at TEMPO_CLEAN)
BUILDUP_BARS      = 8      # accelerating back to thrash
SOLO_BARS         = 16     # Kirk's solo
VERSE3_BARS       = 8      # abbreviated verse 3
PRECHORUS3_BARS   = 4
CHORUS3_BARS      = 8
OUTRO_BARS        = 8      # main riff + ending hits


# ================================================================
#  RHYTHM GUITAR
# ================================================================

def _rhythm_intro(midi, t, ch, beat):
    """Intro: feedback build into first downbeat chord stabs."""
    # Let ring E5 with building intensity
    for bar in range(INTRO_BARS):
        b = beat + bar * 4
        vel = 50 + bar * 15   # crescendo
        add_chord(midi, t, ch, E5, b, 3.5, vel)
        if bar >= 2:
            add_pm_chord(midi, t, ch, E5, b + 3.5, vel - 10)
    return beat + INTRO_BARS * 4

def _rhythm_main_riff(midi, t, ch, beat, bars, vel_base=100):
    """Main riff: E5 gallop pattern — down-down-up palm muted chugging
    with chromatic walk-downs.

    The iconic pattern per bar:
      beat 1: PM chord, beat 1+: PM, beat 1.5: PM
      beat 2: PM, 2+: PM, 2.5: PM
      beat 3: open chord hit or walk-down note
      beat 4: PM PM PM (gallop)
    """
    riff_sequence = [
        # (chord, is_palm_muted, beat_offset, duration, velocity_scale)
        # Bar pattern A (E5 gallop)
        (E5, True,  0.0,   0.08, 1.0),
        (E5, True,  0.25,  0.08, 0.85),
        (E5, True,  0.5,   0.08, 0.9),
        (E5, True,  0.75,  0.08, 0.8),
        (E5, True,  1.0,   0.08, 0.95),
        (E5, True,  1.25,  0.08, 0.8),
        (E5, True,  1.5,   0.08, 0.9),
        (E5, True,  1.75,  0.08, 0.75),
        (E5, False, 2.0,   0.5,  1.0),    # open hit
        (F5, True,  2.5,   0.08, 0.85),
        (F5, True,  2.75,  0.08, 0.8),
        (E5, True,  3.0,   0.08, 0.95),
        (E5, True,  3.25,  0.08, 0.8),
        (E5, True,  3.5,   0.08, 0.9),
        (E5, True,  3.75,  0.08, 0.75),
    ]

    # Alternate every other bar with a slight variation (walk to F5/G5)
    riff_sequence_b = list(riff_sequence)
    riff_sequence_b[8] = (G5, False, 2.0, 0.5, 1.0)
    riff_sequence_b[9] = (F5s, True, 2.5, 0.08, 0.85)
    riff_sequence_b[10] = (F5, True, 2.75, 0.08, 0.8)

    for bar in range(bars):
        b = beat + bar * 4
        pattern = riff_sequence if bar % 2 == 0 else riff_sequence_b
        for chord, pm, off, dur, vs in pattern:
            v = int(vel_base * vs)
            if pm:
                add_pm_chord(midi, t, ch, chord, b + off, v)
            else:
                add_chord(midi, t, ch, chord, b + off, dur, v)
    return beat + bars * 4

def _rhythm_verse(midi, t, ch, beat, bars, vel_base=95):
    """Verse riff: similar to main riff but slightly pulled back dynamically.
    Tighter palm muting, mostly E5 with chromatic neighbor tones."""
    for bar in range(bars):
        b = beat + bar * 4
        # Tight 16th-note palm-muted chugging on E5
        for sixteenth in range(16):
            off = sixteenth * 0.25
            # Accent pattern: 1, &-of-2, 3, &-of-4
            if sixteenth in (0, 5, 8, 13):
                v = int(vel_base * 1.0)
            elif sixteenth % 2 == 0:
                v = int(vel_base * 0.85)
            else:
                v = int(vel_base * 0.7)

            # Walk-down on beats 3-4 of every other bar
            if bar % 2 == 1 and sixteenth >= 12:
                chord = [F5, F5, E5, E5][sixteenth - 12]
            elif bar % 4 == 3 and sixteenth >= 8:
                walk = [G5, F5s, F5, E5, G5, F5s, F5, E5]
                chord = walk[sixteenth - 8]
            else:
                chord = E5
            add_pm_chord(midi, t, ch, chord, b + off, v)
    return beat + bars * 4

def _rhythm_prechorus(midi, t, ch, beat, bars, vel_base=105):
    """Pre-chorus: ascending power chord progression C5-D5-E5 with
    rhythmic stabs — building tension."""
    prog = [C5, D5, Eb5, E5]
    for bar in range(bars):
        b = beat + bar * 4
        chord = prog[bar % len(prog)]
        v = vel_base + bar * 3  # crescendo through pre-chorus
        # Staccato stabs on 1, &-of-2, 3
        add_chord(midi, t, ch, chord, b + 0.0, 0.4, v)
        add_chord(midi, t, ch, chord, b + 1.5, 0.3, int(v * 0.85))
        add_chord(midi, t, ch, chord, b + 2.0, 0.4, int(v * 0.9))
        # Quick gallop into next bar
        add_pm_chord(midi, t, ch, chord, b + 3.0, int(v * 0.8))
        add_pm_chord(midi, t, ch, chord, b + 3.25, int(v * 0.7))
        add_pm_chord(midi, t, ch, chord, b + 3.5, int(v * 0.85))
        add_pm_chord(midi, t, ch, chord, b + 3.75, int(v * 0.7))
    return beat + bars * 4

def _rhythm_chorus(midi, t, ch, beat, bars, vel_base=115):
    """Chorus: 'Master! Master!' — aggressive open power chords.
    B5 - A5 - G5 - F#5 descending, then E5 anchor."""
    prog = [
        (B5, 2), (A5, 2),    # bar 1
        (G5, 2), (F5s, 2),   # bar 2
        (E5, 4),              # bar 3
        (E5, 2), (F5, 1), (F5s, 1),  # bar 4 (turnaround)
    ]
    pattern_len = sum(d for _, d in prog)  # 16 beats = 4 bars

    total_beats = bars * 4
    pos = 0
    while pos < total_beats:
        for chord, dur in prog:
            if pos >= total_beats:
                break
            b = beat + pos
            # Full open chord on downbeat, gallop fill
            add_chord(midi, t, ch, chord, b, dur * 0.8, vel_base)
            if dur >= 2:
                # Add rhythmic hits within
                add_chord(midi, t, ch, chord, b + 1.0, 0.3, int(vel_base * 0.85))
                add_pm_chord(midi, t, ch, chord, b + 1.5, int(vel_base * 0.75))
            pos += dur
    return beat + total_beats

def _rhythm_clean_section(midi, t, ch, beat, bars):
    """Clean interlude: arpeggiated Am - G - Em - C progression.
    Gentle finger-picked feel — lower velocity, longer sustain."""
    prog = [
        (Am_clean, 8),   # 2 bars
        (G_clean,  8),   # 2 bars
        (Em_clean, 8),   # 2 bars
        (C_clean,  4),   # 1 bar
        (D_clean,  4),   # 1 bar
    ]
    pattern_len = sum(d for _, d in prog)  # 32 beats = 8 bars

    pos = 0
    total_beats = bars * 4
    while pos < total_beats:
        for chord_notes, dur in prog:
            if pos >= total_beats:
                break
            b = beat + pos
            # Arpeggiate through the chord
            arp_dur = 2.0  # each arpeggio cycle
            for cycle_start in range(0, dur, 2):
                if pos + cycle_start >= total_beats:
                    break
                cb = b + cycle_start
                for i, note in enumerate(chord_notes):
                    note_time = cb + i * (arp_dur / len(chord_notes))
                    vel = 55 + random.randint(-5, 5)
                    if i == 0:
                        vel = 65  # accent root
                    add_note(midi, t, ch, note, note_time, 1.5, vel)
            pos += dur
    return beat + total_beats

def _rhythm_buildup(midi, t, ch, beat, bars, vel_base=90):
    """Build-up from clean back to thrash: accelerating palm mutes on E5."""
    for bar in range(bars):
        b = beat + bar * 4
        v = vel_base + bar * 4  # crescendo
        # Increasing density: start with quarters, end with 16ths
        if bar < 2:
            divisions = 4  # quarter notes
        elif bar < 4:
            divisions = 8  # 8th notes
        elif bar < 6:
            divisions = 12
        else:
            divisions = 16  # 16th notes
        step = 4.0 / divisions
        for i in range(divisions):
            accent = 1.0 if i % 4 == 0 else 0.8
            add_pm_chord(midi, t, ch, E5, b + i * step, int(v * accent))
    return beat + bars * 4

def _rhythm_interlude(midi, t, ch, beat, bars, vel_base=100):
    """Transition bars — main riff style."""
    return _rhythm_main_riff(midi, t, ch, beat, bars, vel_base)

def _rhythm_outro(midi, t, ch, beat, bars, vel_base=110):
    """Outro: main riff repeated then final chord stabs."""
    pos = _rhythm_main_riff(midi, t, ch, beat, bars - 2, vel_base)
    # Final 2 bars: big E5 stabs
    for hit in range(4):
        b = pos + hit * 2
        add_chord(midi, t, ch, E5, b, 1.5, 120)
    # Final sustained E5
    add_chord(midi, t, ch, E5, pos + 8 - 0.5, 4.0, 125)
    return beat + bars * 4


def build_rhythm_guitar():
    """Generate the complete rhythm guitar MIDI file."""
    midi = MIDIFile(1, ticks_per_quarternote=TICKS_PER_BEAT)
    t, ch = 0, 0
    midi.addTempo(t, 0, TEMPO_FAST)
    midi.addProgramChange(t, ch, 0, 30)  # Overdriven Guitar

    beat = 0.0
    # Intro
    add_marker(midi, t, beat, "Intro")
    beat = _rhythm_intro(midi, t, ch, beat)

    # Main Riff
    add_marker(midi, t, beat, "Main Riff")
    beat = _rhythm_main_riff(midi, t, ch, beat, MAIN_RIFF_BARS)

    # Verse 1
    add_marker(midi, t, beat, "Verse 1")
    beat = _rhythm_verse(midi, t, ch, beat, VERSE1_BARS)

    # Pre-Chorus 1
    add_marker(midi, t, beat, "Pre-Chorus 1")
    beat = _rhythm_prechorus(midi, t, ch, beat, PRECHORUS1_BARS)

    # Chorus 1
    add_marker(midi, t, beat, "Chorus 1")
    beat = _rhythm_chorus(midi, t, ch, beat, CHORUS1_BARS)

    # Interlude 1
    add_marker(midi, t, beat, "Interlude")
    beat = _rhythm_interlude(midi, t, ch, beat, INTERLUDE1_BARS)

    # Verse 2
    add_marker(midi, t, beat, "Verse 2")
    beat = _rhythm_verse(midi, t, ch, beat, VERSE2_BARS)

    # Pre-Chorus 2
    add_marker(midi, t, beat, "Pre-Chorus 2")
    beat = _rhythm_prechorus(midi, t, ch, beat, PRECHORUS2_BARS)

    # Chorus 2
    add_marker(midi, t, beat, "Chorus 2")
    beat = _rhythm_chorus(midi, t, ch, beat, CHORUS2_BARS)

    # Clean Section — tempo change
    add_marker(midi, t, beat, "Clean Interlude")
    midi.addTempo(t, beat, TEMPO_CLEAN)
    beat = _rhythm_clean_section(midi, t, ch, beat, CLEAN_BARS)

    # Build-up — ramp tempo back
    add_marker(midi, t, beat, "Build-up")
    # Gradual tempo increase over buildup bars
    for bar in range(BUILDUP_BARS):
        tempo = TEMPO_CLEAN + (TEMPO_FAST - TEMPO_CLEAN) * (bar / BUILDUP_BARS)
        midi.addTempo(t, beat + bar * 4, int(tempo))
    beat = _rhythm_buildup(midi, t, ch, beat, BUILDUP_BARS)
    midi.addTempo(t, beat, TEMPO_FAST)

    # Guitar Solo
    add_marker(midi, t, beat, "Guitar Solo")
    beat = _rhythm_verse(midi, t, ch, beat, SOLO_BARS, vel_base=100)

    # Verse 3
    add_marker(midi, t, beat, "Verse 3")
    beat = _rhythm_verse(midi, t, ch, beat, VERSE3_BARS, vel_base=100)

    # Pre-Chorus 3
    add_marker(midi, t, beat, "Pre-Chorus 3")
    beat = _rhythm_prechorus(midi, t, ch, beat, PRECHORUS3_BARS)

    # Chorus 3
    add_marker(midi, t, beat, "Chorus 3")
    beat = _rhythm_chorus(midi, t, ch, beat, CHORUS3_BARS)

    # Outro
    add_marker(midi, t, beat, "Outro")
    beat = _rhythm_outro(midi, t, ch, beat, OUTRO_BARS)

    add_marker(midi, t, beat, "END")

    with open("MoP_Rhythm_Guitar.mid", "wb") as f:
        midi.writeFile(f)
    print("  ✓ MoP_Rhythm_Guitar.mid")


# ================================================================
#  LEAD GUITAR
# ================================================================

def _lead_intro_harmonics(midi, t, ch, beat, bars):
    """Intro: feedback harmonics and whammy-bar dives."""
    # High harmonics ringing out — natural harmonic at 12th fret
    harmonics = [64, 71, 76]  # E4, B4, E5 — natural harmonics
    for bar in range(bars):
        b = beat + bar * 4
        vel = 40 + bar * 12  # crescendo
        for i, h in enumerate(harmonics):
            add_note(midi, t, ch, h, b + i * 1.2, 3.0, vel + i * 3)
    return beat + bars * 4

def _lead_main_riff_harmony(midi, t, ch, beat, bars):
    """Harmony line over main riff — 3rds above key notes."""
    # Play harmony hits on the accent points of the main riff
    for bar in range(bars):
        b = beat + bar * 4
        # Harmonize the open chord hit at beat 3
        if bar % 2 == 0:
            add_note(midi, t, ch, 64, b + 2.0, 0.5, 95)  # E4
            add_note(midi, t, ch, 65, b + 2.5, 0.3, 85)   # F4
        else:
            add_note(midi, t, ch, 67, b + 2.0, 0.5, 95)   # G4
            add_note(midi, t, ch, 66, b + 2.5, 0.3, 85)   # F#4
            add_note(midi, t, ch, 65, b + 2.75, 0.3, 80)   # F4
    return beat + bars * 4

def _lead_verse_fills(midi, t, ch, beat, bars):
    """Sparse fills during verses — bends and short licks between vocal lines."""
    # Every 4 bars, throw in a quick fill
    for bar in range(0, bars, 4):
        b = beat + (bar + 3) * 4  # fill in 4th bar of each group
        if b < beat + bars * 4:
            # Quick blues-scale lick
            lick = [(64, 0.25, 90), (67, 0.25, 95), (69, 0.25, 100),
                    (67, 0.5, 95), (64, 0.5, 85)]
            pos = b + 2.0
            for note, dur, vel in lick:
                add_note(midi, t, ch, note, pos, dur, vel)
                pos += dur
    return beat + bars * 4

def _lead_prechorus_line(midi, t, ch, beat, bars):
    """Pre-chorus lead: ascending runs matching the chord progression."""
    scales = {
        0: [48, 50, 52, 55, 57, 60, 62, 64],  # C
        1: [50, 52, 53, 55, 57, 59, 62, 64],  # D
        2: [51, 53, 55, 56, 58, 60, 63, 65],  # Eb
        3: [52, 55, 57, 59, 60, 62, 64, 67],  # E
    }
    for bar in range(bars):
        b = beat + bar * 4
        scale = scales.get(bar % 4, scales[0])
        # Ascending run in last 2 beats
        for i, note in enumerate(scale):
            add_note(midi, t, ch, note + 12, b + 2.0 + i * 0.25, 0.3, 90 + i * 2)
    return beat + bars * 4

def _lead_chorus_melody(midi, t, ch, beat, bars):
    """Chorus lead: rhythmic power chord stabs doubling rhythm + melody hooks."""
    # Simple melodic hook between "Master" shouts
    hook = [
        (71, 0.0, 0.5, 100),   # B4
        (69, 0.5, 0.5, 95),    # A4
        (67, 1.0, 0.5, 100),   # G4
        (66, 1.5, 0.5, 95),    # F#4
        (64, 2.0, 1.5, 105),   # E4 (resolve)
    ]
    for bar_group in range(0, bars, 4):
        for i in range(min(4, bars - bar_group)):
            b = beat + (bar_group + i) * 4
            if i < 2:
                for note, off, dur, vel in hook:
                    add_note(midi, t, ch, note, b + off, dur, vel)
            else:
                # Sustained note on last 2 bars of group
                add_note(midi, t, ch, 64, b, 3.5, 100)
    return beat + bars * 4

def _lead_clean_melody(midi, t, ch, beat, bars):
    """Clean interlude: beautiful melodic line over arpeggiated chords.
    This is one of the most iconic parts of the song."""
    # Melody phrase structure: 8-bar phrases
    melody_phrase_1 = [
        # (note, beat_offset, duration, velocity)
        (64, 0.0, 2.0, 70),     # E4
        (67, 2.0, 1.0, 75),     # G4
        (69, 3.0, 1.0, 72),     # A4
        (71, 4.0, 2.0, 78),     # B4
        (72, 6.0, 1.0, 80),     # C5
        (71, 7.0, 1.0, 75),     # B4
        (69, 8.0, 2.0, 73),     # A4
        (67, 10.0, 1.0, 70),    # G4
        (64, 11.0, 1.0, 68),    # E4
        (67, 12.0, 2.0, 72),    # G4
        (69, 14.0, 2.0, 75),    # A4
        (71, 16.0, 3.0, 80),    # B4
        (69, 19.0, 1.0, 72),    # A4
        (67, 20.0, 2.0, 70),    # G4
        (64, 22.0, 2.0, 68),    # E4
        (62, 24.0, 2.0, 65),    # D4
        (64, 26.0, 2.0, 70),    # E4
        (67, 28.0, 4.0, 75),    # G4 (long sustain)
    ]

    melody_phrase_2 = [
        (69, 0.0, 1.5, 72),     # A4
        (71, 1.5, 1.5, 78),     # B4
        (72, 3.0, 1.0, 80),     # C5
        (74, 4.0, 2.0, 83),     # D5
        (76, 6.0, 2.0, 85),     # E5 — climax
        (74, 8.0, 1.0, 80),     # D5
        (72, 9.0, 1.0, 78),     # C5
        (71, 10.0, 2.0, 75),    # B4
        (69, 12.0, 1.5, 72),    # A4
        (67, 13.5, 1.5, 70),    # G4
        (69, 15.0, 1.0, 72),    # A4
        (71, 16.0, 3.0, 78),    # B4
        (72, 19.0, 1.0, 80),    # C5
        (74, 20.0, 2.0, 82),    # D5
        (72, 22.0, 2.0, 78),    # C5
        (71, 24.0, 2.0, 75),    # B4
        (69, 26.0, 2.0, 72),    # A4
        (67, 28.0, 4.0, 70),    # G4
    ]

    pos = 0
    total = bars * 4
    phrase_idx = 0
    phrases = [melody_phrase_1, melody_phrase_2]
    while pos < total:
        phrase = phrases[phrase_idx % 2]
        for note, off, dur, vel in phrase:
            if pos + off < total:
                add_note(midi, t, ch, note, beat + pos + off, dur, vel)
        pos += 32  # each phrase is 32 beats (8 bars)
        phrase_idx += 1
    return beat + total

def _lead_solo(midi, t, ch, beat, bars):
    """Guitar solo: Kirk Hammett's pentatonic/minor scale shredding.
    Fast runs, bends, vibrato — expressed through velocity and note density."""
    # E minor pentatonic: E4(64), G4(67), A4(69), B4(71), D5(74), E5(76)
    # E minor scale: E4(64), F#4(66), G4(67), A4(69), B4(71), C5(72), D5(74), E5(76)

    solo_phrases = [
        # Phrase 1: opening bend and run (bars 1-2)
        [(64, 0.0, 0.5, 100), (67, 0.5, 0.25, 105), (69, 0.75, 0.25, 108),
         (71, 1.0, 1.0, 112), (74, 2.0, 0.5, 110), (76, 2.5, 0.5, 115),
         (74, 3.0, 0.25, 108), (71, 3.25, 0.25, 105), (69, 3.5, 0.25, 100),
         (67, 3.75, 0.25, 95),
         (64, 4.0, 0.5, 105), (69, 4.5, 0.5, 108), (71, 5.0, 0.5, 110),
         (76, 5.5, 0.5, 115), (79, 6.0, 2.0, 118)],  # high G5 bend

        # Phrase 2: fast 16th note run (bars 3-4)
        [(76, 0.0, 0.25, 110), (74, 0.25, 0.25, 105), (72, 0.5, 0.25, 108),
         (71, 0.75, 0.25, 105), (69, 1.0, 0.25, 108), (67, 1.25, 0.25, 105),
         (66, 1.5, 0.25, 100), (64, 1.75, 0.25, 95),
         (62, 2.0, 0.5, 90), (64, 2.5, 0.5, 95),
         (67, 3.0, 0.25, 100), (69, 3.25, 0.25, 105), (71, 3.5, 0.25, 108),
         (74, 3.75, 0.25, 110),
         (76, 4.0, 1.0, 115), (74, 5.0, 0.5, 108), (76, 5.5, 0.25, 110),
         (79, 5.75, 0.25, 112), (81, 6.0, 2.0, 120)],  # climactic A5

        # Phrase 3: wah-inflected pattern (bars 5-6)
        [(76, 0.0, 0.5, 105), (79, 0.5, 0.5, 110), (76, 1.0, 0.5, 108),
         (74, 1.5, 0.5, 105), (71, 2.0, 1.0, 100), (69, 3.0, 0.5, 95),
         (71, 3.5, 0.5, 100),
         (74, 4.0, 0.5, 108), (76, 4.5, 0.25, 110), (79, 4.75, 0.25, 112),
         (76, 5.0, 0.25, 108), (74, 5.25, 0.25, 105), (71, 5.5, 0.25, 100),
         (69, 5.75, 0.25, 95),
         (67, 6.0, 1.0, 100), (69, 7.0, 1.0, 105)],

        # Phrase 4: climactic ending (bars 7-8)
        [(71, 0.0, 0.25, 110), (74, 0.25, 0.25, 112), (76, 0.5, 0.25, 115),
         (79, 0.75, 0.25, 118), (81, 1.0, 0.5, 120), (83, 1.5, 0.5, 122),
         (81, 2.0, 0.25, 118), (79, 2.25, 0.25, 115), (76, 2.5, 0.5, 112),
         (74, 3.0, 0.5, 108), (71, 3.5, 0.5, 105),
         (76, 4.0, 0.5, 115), (79, 4.5, 0.5, 118), (81, 5.0, 0.5, 120),
         (83, 5.5, 0.5, 122), (84, 6.0, 2.0, 125)],  # high E6 — peak
    ]

    pos = beat
    for phrase in solo_phrases:
        for note, off, dur, vel in phrase:
            add_note(midi, t, ch, note, pos + off, dur, vel)
        pos += 4 * 4  # 4 bars per phrase

    # If more bars, repeat with variation
    remaining = bars - 16
    if remaining > 0:
        pos2 = pos
        for phrase in solo_phrases[:remaining // 4 + 1]:
            for note, off, dur, vel in phrase:
                if pos2 + off < beat + bars * 4:
                    add_note(midi, t, ch, note + 12, pos2 + off, dur, min(127, vel + 5))
            pos2 += 4 * 4

    return beat + bars * 4


def build_lead_guitar():
    """Generate the complete lead guitar MIDI file."""
    midi = MIDIFile(1, ticks_per_quarternote=TICKS_PER_BEAT)
    t, ch = 0, 0
    midi.addTempo(t, 0, TEMPO_FAST)
    midi.addProgramChange(t, ch, 0, 30)  # Overdriven Guitar

    beat = 0.0

    add_marker(midi, t, beat, "Intro")
    beat = _lead_intro_harmonics(midi, t, ch, beat, INTRO_BARS)

    add_marker(midi, t, beat, "Main Riff")
    beat = _lead_main_riff_harmony(midi, t, ch, beat, MAIN_RIFF_BARS)

    add_marker(midi, t, beat, "Verse 1")
    beat = _lead_verse_fills(midi, t, ch, beat, VERSE1_BARS)

    add_marker(midi, t, beat, "Pre-Chorus 1")
    beat = _lead_prechorus_line(midi, t, ch, beat, PRECHORUS1_BARS)

    add_marker(midi, t, beat, "Chorus 1")
    beat = _lead_chorus_melody(midi, t, ch, beat, CHORUS1_BARS)

    add_marker(midi, t, beat, "Interlude")
    beat = _lead_main_riff_harmony(midi, t, ch, beat, INTERLUDE1_BARS)

    add_marker(midi, t, beat, "Verse 2")
    beat = _lead_verse_fills(midi, t, ch, beat, VERSE2_BARS)

    add_marker(midi, t, beat, "Pre-Chorus 2")
    beat = _lead_prechorus_line(midi, t, ch, beat, PRECHORUS2_BARS)

    add_marker(midi, t, beat, "Chorus 2")
    beat = _lead_chorus_melody(midi, t, ch, beat, CHORUS2_BARS)

    # Clean interlude
    add_marker(midi, t, beat, "Clean Interlude")
    midi.addTempo(t, beat, TEMPO_CLEAN)
    beat = _lead_clean_melody(midi, t, ch, beat, CLEAN_BARS)

    add_marker(midi, t, beat, "Build-up")
    for bar in range(BUILDUP_BARS):
        tempo = TEMPO_CLEAN + (TEMPO_FAST - TEMPO_CLEAN) * (bar / BUILDUP_BARS)
        midi.addTempo(t, beat + bar * 4, int(tempo))
    # Buildup: sustained feedback notes
    for bar in range(BUILDUP_BARS):
        b = beat + bar * 4
        vel = 80 + bar * 5
        add_note(midi, t, ch, 64, b, 3.5, vel)
    beat += BUILDUP_BARS * 4
    midi.addTempo(t, beat, TEMPO_FAST)

    add_marker(midi, t, beat, "Guitar Solo")
    beat = _lead_solo(midi, t, ch, beat, SOLO_BARS)

    add_marker(midi, t, beat, "Verse 3")
    beat = _lead_verse_fills(midi, t, ch, beat, VERSE3_BARS)

    add_marker(midi, t, beat, "Pre-Chorus 3")
    beat = _lead_prechorus_line(midi, t, ch, beat, PRECHORUS3_BARS)

    add_marker(midi, t, beat, "Chorus 3")
    beat = _lead_chorus_melody(midi, t, ch, beat, CHORUS3_BARS)

    add_marker(midi, t, beat, "Outro")
    beat = _lead_main_riff_harmony(midi, t, ch, beat, OUTRO_BARS)

    add_marker(midi, t, beat, "END")

    with open("MoP_Lead_Guitar.mid", "wb") as f:
        midi.writeFile(f)
    print("  ✓ MoP_Lead_Guitar.mid")


# ================================================================
#  BASS GUITAR
# ================================================================

def _bass_gallop(midi, t, ch, root, beat, bars, vel_base=100):
    """Galloping 8th-note bass pattern — Cliff Burton style.
    root-root-fifth-root repeated, with ghost notes."""
    fifth = root + 7
    for bar in range(bars):
        b = beat + bar * 4
        for sub_beat in range(4):
            sb = b + sub_beat
            # Gallop: dotted-8th + 16th + 8th
            add_note(midi, t, ch, root, sb + 0.0, 0.3, vel_base)
            add_note(midi, t, ch, root, sb + 0.375, 0.12, int(vel_base * 0.7))
            add_note(midi, t, ch, fifth, sb + 0.5, 0.3, int(vel_base * 0.85))
            add_note(midi, t, ch, root, sb + 0.75, 0.12, int(vel_base * 0.65))
    return beat + bars * 4

def _bass_verse(midi, t, ch, beat, bars, vel_base=95):
    """Verse bass: tight 8th-note pulse on root, with chromatic walk-downs."""
    for bar in range(bars):
        b = beat + bar * 4
        root = E2
        # Walk-down on every 4th bar
        if bar % 4 == 3:
            walk_notes = [G2, Fs2, F2, E2]
            for i, note in enumerate(walk_notes):
                sb = b + i
                add_note(midi, t, ch, note, sb + 0.0, 0.4, vel_base)
                add_note(midi, t, ch, note, sb + 0.5, 0.3, int(vel_base * 0.75))
        else:
            for eighth in range(8):
                off = eighth * 0.5
                v = vel_base if eighth % 2 == 0 else int(vel_base * 0.7)
                add_note(midi, t, ch, root, b + off, 0.35, v)
    return beat + bars * 4

def _bass_prechorus(midi, t, ch, beat, bars, vel_base=105):
    """Pre-chorus bass: follows chord roots with driving 8ths."""
    roots = [C3, D3, Eb3, E3]
    for bar in range(bars):
        b = beat + bar * 4
        root = roots[bar % len(roots)]
        for eighth in range(8):
            off = eighth * 0.5
            v = vel_base + bar * 2 if eighth % 2 == 0 else int(vel_base * 0.75)
            add_note(midi, t, ch, root, b + off, 0.35, v)
    return beat + bars * 4

def _bass_chorus(midi, t, ch, beat, bars, vel_base=110):
    """Chorus bass: follows descending chord progression with gallop feel."""
    prog = [
        (B2, 2), (A2, 2),
        (G2, 2), (Fs2, 2),
        (E2, 4),
        (E2, 2), (F2, 1), (Fs2, 1),
    ]
    total = bars * 4
    pos = 0
    while pos < total:
        for root, dur in prog:
            if pos >= total:
                break
            b = beat + pos
            # Driving 8th notes
            steps = int(dur / 0.5)
            for i in range(steps):
                v = vel_base if i % 2 == 0 else int(vel_base * 0.75)
                add_note(midi, t, ch, root, b + i * 0.5, 0.4, v)
            pos += dur
    return beat + total

def _bass_clean(midi, t, ch, beat, bars):
    """Clean section bass: melodic, sustained — Cliff's lyrical style."""
    prog = [
        (A2, 8), (G2, 8), (E2, 8), (C3, 4), (D3, 4),
    ]
    total = bars * 4
    pos = 0
    while pos < total:
        for root, dur in prog:
            if pos >= total:
                break
            b = beat + pos
            # Whole notes with melodic passing tones
            add_note(midi, t, ch, root, b, 3.5, 65)
            if dur >= 8:
                # Add a melodic walk
                add_note(midi, t, ch, root + 2, b + 4.0, 1.5, 60)
                add_note(midi, t, ch, root + 4, b + 5.5, 1.5, 62)
                add_note(midi, t, ch, root + 5, b + 7.0, 1.0, 58)
            pos += dur
    return beat + total

def _bass_buildup(midi, t, ch, beat, bars, vel_base=90):
    """Build-up: accelerating 8th notes on E."""
    for bar in range(bars):
        b = beat + bar * 4
        v = vel_base + bar * 4
        divisions = 8 if bar < 4 else 16
        step = 4.0 / divisions
        for i in range(divisions):
            accent = v if i % 4 == 0 else int(v * 0.75)
            add_note(midi, t, ch, E2, b + i * step, step * 0.8, accent)
    return beat + bars * 4


def build_bass_guitar():
    """Generate the complete bass guitar MIDI file."""
    midi = MIDIFile(1, ticks_per_quarternote=TICKS_PER_BEAT)
    t, ch = 0, 0
    midi.addTempo(t, 0, TEMPO_FAST)
    midi.addProgramChange(t, ch, 0, 34)  # Finger Bass (electric)

    beat = 0.0

    add_marker(midi, t, beat, "Intro")
    # Intro: sustained low E with crescendo
    for bar in range(INTRO_BARS):
        b = beat + bar * 4
        add_note(midi, t, ch, E2, b, 3.5, 50 + bar * 12)
    beat += INTRO_BARS * 4

    add_marker(midi, t, beat, "Main Riff")
    beat = _bass_gallop(midi, t, ch, E2, beat, MAIN_RIFF_BARS)

    add_marker(midi, t, beat, "Verse 1")
    beat = _bass_verse(midi, t, ch, beat, VERSE1_BARS)

    add_marker(midi, t, beat, "Pre-Chorus 1")
    beat = _bass_prechorus(midi, t, ch, beat, PRECHORUS1_BARS)

    add_marker(midi, t, beat, "Chorus 1")
    beat = _bass_chorus(midi, t, ch, beat, CHORUS1_BARS)

    add_marker(midi, t, beat, "Interlude")
    beat = _bass_gallop(midi, t, ch, E2, beat, INTERLUDE1_BARS)

    add_marker(midi, t, beat, "Verse 2")
    beat = _bass_verse(midi, t, ch, beat, VERSE2_BARS)

    add_marker(midi, t, beat, "Pre-Chorus 2")
    beat = _bass_prechorus(midi, t, ch, beat, PRECHORUS2_BARS)

    add_marker(midi, t, beat, "Chorus 2")
    beat = _bass_chorus(midi, t, ch, beat, CHORUS2_BARS)

    add_marker(midi, t, beat, "Clean Interlude")
    midi.addTempo(t, beat, TEMPO_CLEAN)
    beat = _bass_clean(midi, t, ch, beat, CLEAN_BARS)

    add_marker(midi, t, beat, "Build-up")
    for bar in range(BUILDUP_BARS):
        tempo = TEMPO_CLEAN + (TEMPO_FAST - TEMPO_CLEAN) * (bar / BUILDUP_BARS)
        midi.addTempo(t, beat + bar * 4, int(tempo))
    beat = _bass_buildup(midi, t, ch, beat, BUILDUP_BARS)
    midi.addTempo(t, beat, TEMPO_FAST)

    add_marker(midi, t, beat, "Guitar Solo")
    beat = _bass_verse(midi, t, ch, beat, SOLO_BARS, vel_base=100)

    add_marker(midi, t, beat, "Verse 3")
    beat = _bass_verse(midi, t, ch, beat, VERSE3_BARS)

    add_marker(midi, t, beat, "Pre-Chorus 3")
    beat = _bass_prechorus(midi, t, ch, beat, PRECHORUS3_BARS)

    add_marker(midi, t, beat, "Chorus 3")
    beat = _bass_chorus(midi, t, ch, beat, CHORUS3_BARS)

    add_marker(midi, t, beat, "Outro")
    beat = _bass_gallop(midi, t, ch, E2, beat, OUTRO_BARS - 2)
    # Final hits
    for i in range(4):
        add_note(midi, t, ch, E2, beat + i * 2, 1.5, 120)
    add_note(midi, t, ch, E2, beat + 8 - 0.5, 4.0, 125)
    beat += 8

    add_marker(midi, t, beat, "END")

    with open("MoP_Bass_Guitar.mid", "wb") as f:
        midi.writeFile(f)
    print("  ✓ MoP_Bass_Guitar.mid")


# ================================================================
#  DRUMS
# ================================================================

def _drums_intro(midi, t, beat, bars):
    """Intro: building from nothing — sparse hits to full kit."""
    for bar in range(bars):
        b = beat + bar * 4
        vel = 50 + bar * 18
        if bar == 0:
            # Just ride hits
            for q in range(4):
                add_drum(midi, t, HH_CLOSED, b + q, vel - 10)
        elif bar == 1:
            for q in range(4):
                add_drum(midi, t, HH_CLOSED, b + q, vel - 5)
            add_drum(midi, t, KICK, b + 0, vel)
            add_drum(midi, t, KICK, b + 2, vel)
        else:
            # Full beat with crash on bar 3
            if bar == 2:
                add_drum(midi, t, CRASH1, b, vel + 10)
            for q in range(8):
                add_drum(midi, t, HH_CLOSED, b + q * 0.5, vel - 15 + (q % 2) * 5)
            add_drum(midi, t, KICK, b + 0, vel)
            add_drum(midi, t, KICK, b + 1, vel - 5)
            add_drum(midi, t, SNARE, b + 1, vel)
            add_drum(midi, t, KICK, b + 2, vel)
            add_drum(midi, t, SNARE, b + 3, vel)
    return beat + bars * 4

def _drums_thrash_beat(midi, t, beat, bars, vel_base=105, double_kick=True):
    """Standard thrash metal beat: fast kick patterns, snare on 2&4,
    hi-hat 8ths or 16ths. With dynamic accents."""
    for bar in range(bars):
        b = beat + bar * 4
        # Crash on first beat of every 4-bar phrase
        if bar % 4 == 0:
            add_drum(midi, t, CRASH1, b, vel_base + 10)

        # Hi-hat: 8th notes with accent on downbeats
        for eighth in range(8):
            off = eighth * 0.5
            hh_vel = vel_base - 15 if eighth % 2 == 0 else vel_base - 25
            add_drum(midi, t, HH_CLOSED, b + off, hh_vel)

        # Snare on 2 and 4
        add_drum(midi, t, SNARE, b + 1, vel_base)
        add_drum(midi, t, SNARE, b + 3, vel_base)

        # Kick pattern: galloping
        if double_kick:
            # 16th-note double kick pattern
            kick_pattern = [0, 0.25, 0.5, 1.5, 2.0, 2.25, 2.5, 3.5]
            for k in kick_pattern:
                kv = vel_base if k in (0, 2.0) else vel_base - 12
                add_drum(midi, t, KICK, b + k, kv)
        else:
            add_drum(midi, t, KICK, b + 0, vel_base)
            add_drum(midi, t, KICK, b + 2, vel_base - 5)

        # Occasional ghost snare hits
        if bar % 2 == 1:
            add_drum(midi, t, SNARE, b + 0.75, vel_base - 35)  # ghost note
            add_drum(midi, t, SNARE, b + 2.75, vel_base - 35)
    return beat + bars * 4

def _drums_verse(midi, t, beat, bars, vel_base=100):
    """Verse drums: slightly pulled back, tight — supportive groove."""
    for bar in range(bars):
        b = beat + bar * 4
        if bar % 8 == 0:
            add_drum(midi, t, CRASH1, b, vel_base + 5)

        # Hi-hat 8ths with varied dynamics
        for eighth in range(8):
            off = eighth * 0.5
            if eighth % 4 == 0:
                hh_vel = vel_base - 10  # downbeat accent
            elif eighth % 2 == 0:
                hh_vel = vel_base - 18
            else:
                hh_vel = vel_base - 25
            add_drum(midi, t, HH_CLOSED, b + off, hh_vel)

        # Snare: 2 and 4
        add_drum(midi, t, SNARE, b + 1, vel_base - 3)
        add_drum(midi, t, SNARE, b + 3, vel_base)

        # Kick: driving 8ths with accents
        kick_hits = [0, 0.5, 2.0, 2.5]
        if bar % 2 == 1:
            kick_hits = [0, 0.5, 1.5, 2.0, 2.5, 3.5]
        for k in kick_hits:
            kv = vel_base - 5 if k == int(k) else vel_base - 15
            add_drum(midi, t, KICK, b + k, kv)

        # Ghost snares for groove
        if bar % 4 >= 2:
            add_drum(midi, t, SNARE, b + 0.5, vel_base - 38)
            add_drum(midi, t, SNARE, b + 2.5, vel_base - 38)
    return beat + bars * 4

def _drums_prechorus(midi, t, beat, bars, vel_base=108):
    """Pre-chorus drums: building intensity with crashes and fills."""
    for bar in range(bars):
        b = beat + bar * 4
        v = vel_base + bar * 3  # crescendo

        add_drum(midi, t, CRASH1, b, v + 5)

        # 16th-note hi-hat
        for sixteenth in range(16):
            off = sixteenth * 0.25
            hh_v = v - 20 if sixteenth % 4 == 0 else v - 30
            if sixteenth % 2 == 1:
                hh_v -= 8
            add_drum(midi, t, HH_CLOSED, b + off, hh_v)

        add_drum(midi, t, SNARE, b + 1, v)
        add_drum(midi, t, SNARE, b + 3, v + 3)

        # Double kick 16ths
        for sixteenth in [0, 1, 2, 3, 8, 9, 10, 11]:
            kv = v - 5 if sixteenth % 4 == 0 else v - 15
            add_drum(midi, t, KICK, b + sixteenth * 0.25, kv)

        # Fill on last bar
        if bar == bars - 1:
            add_drum(midi, t, TOM_HI, b + 3.0, v)
            add_drum(midi, t, TOM_MID, b + 3.25, v - 3)
            add_drum(midi, t, TOM_LOW, b + 3.5, v - 5)
            add_drum(midi, t, TOM_FLOOR, b + 3.75, v - 3)
    return beat + bars * 4

def _drums_chorus(midi, t, beat, bars, vel_base=115):
    """Chorus drums: full power — crashes, driving double kick, hard snare."""
    for bar in range(bars):
        b = beat + bar * 4
        # Crash every 2 bars
        if bar % 2 == 0:
            add_drum(midi, t, CRASH1, b, vel_base + 10)
        if bar % 4 == 0:
            add_drum(midi, t, CRASH2, b, vel_base + 5)

        # Ride on 8ths (when no crash)
        for eighth in range(8):
            off = eighth * 0.5
            if bar % 2 != 0 or eighth > 0:
                rv = vel_base - 15 if eighth % 2 == 0 else vel_base - 22
                add_drum(midi, t, RIDE, b + off, rv)

        # Hard snare on 2 and 4
        add_drum(midi, t, SNARE, b + 1, vel_base + 5)
        add_drum(midi, t, SNARE, b + 3, vel_base + 5)

        # Relentless double kick
        for sixteenth in range(16):
            off = sixteenth * 0.25
            if sixteenth % 2 == 0:
                kv = vel_base if sixteenth % 4 == 0 else vel_base - 8
                add_drum(midi, t, KICK, b + off, kv)

        # Snare ghost notes
        add_drum(midi, t, SNARE, b + 0.5, vel_base - 30)
        add_drum(midi, t, SNARE, b + 2.5, vel_base - 30)
    return beat + bars * 4

def _drums_clean(midi, t, beat, bars):
    """Clean interlude drums: half-time feel, soft — brushes/ride vibe.
    Dynamics way down."""
    vel_base = 55
    for bar in range(bars):
        b = beat + bar * 4
        # Ride with bell accents
        for q in range(4):
            off = q
            if q == 0:
                add_drum(midi, t, RIDE_BELL, b + off, vel_base)
            else:
                add_drum(midi, t, RIDE, b + off, vel_base - 12)
            # Ghost ride between quarters
            add_drum(midi, t, RIDE, b + off + 0.5, vel_base - 22)

        # Snare on 3 only (half-time)
        add_drum(midi, t, SNARE, b + 2, vel_base - 5)

        # Kick on 1 and sometimes &-of-3
        add_drum(midi, t, KICK, b + 0, vel_base)
        if bar % 2 == 0:
            add_drum(midi, t, KICK, b + 2.5, vel_base - 12)

        # Ghost snare
        add_drum(midi, t, SNARE, b + 1.0, vel_base - 35)
        add_drum(midi, t, SNARE, b + 3.5, vel_base - 38)

        # HH pedal on off-beats
        add_drum(midi, t, HH_PEDAL, b + 1, vel_base - 25)
        add_drum(midi, t, HH_PEDAL, b + 3, vel_base - 25)

        # Occasional tom fill every 8 bars
        if bar % 8 == 7:
            add_drum(midi, t, TOM_HI, b + 3.0, vel_base + 5)
            add_drum(midi, t, TOM_MID, b + 3.25, vel_base + 3)
            add_drum(midi, t, TOM_LOW, b + 3.5, vel_base)
            add_drum(midi, t, TOM_FLOOR, b + 3.75, vel_base)

        # Dynamic swell in second half of clean section
        if bar >= bars // 2:
            vel_base = min(75, 55 + (bar - bars // 2) * 2)
    return beat + bars * 4

def _drums_buildup(midi, t, beat, bars, vel_base=85):
    """Build-up: snare roll building to full thrash. Huge crescendo."""
    for bar in range(bars):
        b = beat + bar * 4
        v = vel_base + bar * 6  # big crescendo

        # Increasing snare density
        if bar < 2:
            # Quarter note snare
            for q in range(4):
                add_drum(midi, t, SNARE, b + q, v)
                add_drum(midi, t, KICK, b + q, v - 5)
        elif bar < 4:
            # 8th note snare roll
            for e in range(8):
                add_drum(midi, t, SNARE, b + e * 0.5, v - (e % 2) * 8)
            for e in range(8):
                add_drum(midi, t, KICK, b + e * 0.5, v - 8)
        elif bar < 6:
            # 16th note snare roll
            for s in range(16):
                sv = v if s % 4 == 0 else v - 12
                add_drum(midi, t, SNARE, b + s * 0.25, sv)
            for s in range(16):
                add_drum(midi, t, KICK, b + s * 0.25, v - 10)
        else:
            # Full 16th snare + kick  — wall of sound
            for s in range(16):
                sv = min(127, v + 5) if s % 4 == 0 else v
                add_drum(midi, t, SNARE, b + s * 0.25, sv)
                add_drum(midi, t, KICK, b + s * 0.25, sv - 5)
            # Crashes
            add_drum(midi, t, CRASH1, b, min(127, v + 10))
            add_drum(midi, t, CRASH2, b + 2, min(127, v + 8))

        # China on last bar
        if bar == bars - 1:
            add_drum(midi, t, CHINA, b + 3.5, min(127, v + 10))
    return beat + bars * 4

def _drums_solo(midi, t, beat, bars, vel_base=108):
    """Solo section drums: driving beat supporting the guitar solo.
    Slightly more open than verse — ride cymbal."""
    for bar in range(bars):
        b = beat + bar * 4
        if bar % 4 == 0:
            add_drum(midi, t, CRASH1, b, vel_base + 10)
            add_drum(midi, t, CHINA, b, vel_base + 5)

        # Ride bell on quarters, ride on 8ths
        for eighth in range(8):
            off = eighth * 0.5
            if eighth % 2 == 0:
                add_drum(midi, t, RIDE_BELL, b + off, vel_base - 10)
            else:
                add_drum(midi, t, RIDE, b + off, vel_base - 18)

        # Hard snare
        add_drum(midi, t, SNARE, b + 1, vel_base + 3)
        add_drum(midi, t, SNARE, b + 3, vel_base + 5)

        # Double kick gallop
        kick_hits = [0, 0.25, 0.5, 1.5, 2.0, 2.25, 2.5, 3.5]
        for k in kick_hits:
            kv = vel_base if k == int(k) else vel_base - 10
            add_drum(midi, t, KICK, b + k, kv)

        # Ghost snares
        add_drum(midi, t, SNARE, b + 0.75, vel_base - 32)
        add_drum(midi, t, SNARE, b + 2.75, vel_base - 32)

        # Tom fills every 4 bars
        if bar % 4 == 3:
            add_drum(midi, t, TOM_HI, b + 3.0, vel_base + 3)
            add_drum(midi, t, TOM_HI, b + 3.125, vel_base)
            add_drum(midi, t, TOM_MID, b + 3.25, vel_base + 3)
            add_drum(midi, t, TOM_MID, b + 3.375, vel_base)
            add_drum(midi, t, TOM_LOW, b + 3.5, vel_base + 3)
            add_drum(midi, t, TOM_FLOOR, b + 3.625, vel_base)
            add_drum(midi, t, TOM_FLOOR, b + 3.75, vel_base + 5)
    return beat + bars * 4

def _drums_fill_4beat(midi, t, beat, vel=110):
    """One-bar drum fill: toms descending."""
    add_drum(midi, t, CRASH1, beat, vel + 10)
    add_drum(midi, t, SNARE, beat, vel)
    add_drum(midi, t, TOM_HI, beat + 0.5, vel - 3)
    add_drum(midi, t, TOM_HI, beat + 0.75, vel - 5)
    add_drum(midi, t, TOM_MID, beat + 1.0, vel)
    add_drum(midi, t, TOM_MID, beat + 1.25, vel - 3)
    add_drum(midi, t, TOM_MID, beat + 1.5, vel - 5)
    add_drum(midi, t, TOM_LOW, beat + 2.0, vel)
    add_drum(midi, t, TOM_LOW, beat + 2.25, vel - 3)
    add_drum(midi, t, TOM_FLOOR, beat + 2.5, vel)
    add_drum(midi, t, TOM_FLOOR, beat + 2.75, vel - 3)
    add_drum(midi, t, KICK, beat + 3.0, vel + 5)
    add_drum(midi, t, KICK, beat + 3.25, vel + 3)
    add_drum(midi, t, SNARE, beat + 3.5, vel + 5)
    add_drum(midi, t, CRASH1, beat + 3.75, vel + 8)


def build_drums():
    """Generate the complete drum MIDI file."""
    midi = MIDIFile(1, ticks_per_quarternote=TICKS_PER_BEAT)
    t = 0
    midi.addTempo(t, 0, TEMPO_FAST)

    beat = 0.0

    add_marker(midi, t, beat, "Intro")
    beat = _drums_intro(midi, t, beat, INTRO_BARS)

    add_marker(midi, t, beat, "Main Riff")
    beat = _drums_thrash_beat(midi, t, beat, MAIN_RIFF_BARS, vel_base=108)

    add_marker(midi, t, beat, "Verse 1")
    beat = _drums_verse(midi, t, beat, VERSE1_BARS, vel_base=100)

    add_marker(midi, t, beat, "Pre-Chorus 1")
    beat = _drums_prechorus(midi, t, beat, PRECHORUS1_BARS)

    add_marker(midi, t, beat, "Chorus 1")
    beat = _drums_chorus(midi, t, beat, CHORUS1_BARS)

    # Fill into interlude
    _drums_fill_4beat(midi, t, beat - 4, 112)

    add_marker(midi, t, beat, "Interlude")
    beat = _drums_thrash_beat(midi, t, beat, INTERLUDE1_BARS, vel_base=105)

    add_marker(midi, t, beat, "Verse 2")
    beat = _drums_verse(midi, t, beat, VERSE2_BARS)

    add_marker(midi, t, beat, "Pre-Chorus 2")
    beat = _drums_prechorus(midi, t, beat, PRECHORUS2_BARS)

    add_marker(midi, t, beat, "Chorus 2")
    beat = _drums_chorus(midi, t, beat, CHORUS2_BARS)

    # Fill into clean section
    _drums_fill_4beat(midi, t, beat - 4, 115)

    add_marker(midi, t, beat, "Clean Interlude")
    midi.addTempo(t, beat, TEMPO_CLEAN)
    beat = _drums_clean(midi, t, beat, CLEAN_BARS)

    add_marker(midi, t, beat, "Build-up")
    for bar in range(BUILDUP_BARS):
        tempo = TEMPO_CLEAN + (TEMPO_FAST - TEMPO_CLEAN) * (bar / BUILDUP_BARS)
        midi.addTempo(t, beat + bar * 4, int(tempo))
    beat = _drums_buildup(midi, t, beat, BUILDUP_BARS)
    midi.addTempo(t, beat, TEMPO_FAST)

    add_marker(midi, t, beat, "Guitar Solo")
    beat = _drums_solo(midi, t, beat, SOLO_BARS)

    add_marker(midi, t, beat, "Verse 3")
    beat = _drums_verse(midi, t, beat, VERSE3_BARS, vel_base=105)

    add_marker(midi, t, beat, "Pre-Chorus 3")
    beat = _drums_prechorus(midi, t, beat, PRECHORUS3_BARS)

    add_marker(midi, t, beat, "Chorus 3")
    beat = _drums_chorus(midi, t, beat, CHORUS3_BARS, vel_base=118)

    add_marker(midi, t, beat, "Outro")
    beat = _drums_thrash_beat(midi, t, beat, OUTRO_BARS - 2, vel_base=112)
    # Ending hits
    b = beat
    for i in range(4):
        add_drum(midi, t, CRASH1, b + i * 2, 125)
        add_drum(midi, t, KICK, b + i * 2, 125)
        add_drum(midi, t, SNARE, b + i * 2, 120)
    # Final crash
    add_drum(midi, t, CRASH1, b + 7.5, 127)
    add_drum(midi, t, CRASH2, b + 7.5, 127)
    add_drum(midi, t, KICK, b + 7.5, 127)
    add_drum(midi, t, SNARE, b + 7.5, 127)
    beat += 8

    add_marker(midi, t, beat, "END")

    with open("MoP_Drums.mid", "wb") as f:
        midi.writeFile(f)
    print("  ✓ MoP_Drums.mid")


# ================================================================
#  VOCAL MELODY (guide track for singing)
# ================================================================

# Lyrics with melody notes and timing
# Format: (section_label, section_beat_offset,
#           [(lyric_text, relative_beat, note, duration, velocity), ...])

VERSE1_VOCAL = [
    # "End of passion play, crumbling away"
    ("End", 0.0, 64, 0.5, 85),         # E4
    ("of", 0.5, 64, 0.25, 75),
    ("pas-", 1.0, 67, 0.5, 90),        # G4
    ("sion", 1.5, 67, 0.5, 85),
    ("play,", 2.0, 69, 1.0, 95),       # A4
    ("crum-", 4.0, 67, 0.5, 88),
    ("bling", 4.5, 64, 0.5, 82),
    ("a-", 5.0, 62, 0.5, 80),          # D4
    ("way", 5.5, 64, 1.5, 85),         # E4

    # "I'm your source of self-destruction"
    ("I'm", 8.0, 64, 0.5, 85),
    ("your", 8.5, 64, 0.25, 75),
    ("source", 9.0, 67, 0.5, 90),
    ("of", 9.5, 67, 0.25, 78),
    ("self-", 10.0, 69, 0.5, 92),
    ("de-", 10.5, 71, 0.5, 95),        # B4
    ("struc-", 11.0, 69, 0.5, 90),
    ("tion", 11.5, 67, 1.5, 85),

    # "Veins that pump with fear, sucking darkest clear"
    ("Veins", 16.0, 64, 0.5, 88),
    ("that", 16.5, 64, 0.25, 78),
    ("pump", 17.0, 67, 0.5, 92),
    ("with", 17.5, 67, 0.25, 80),
    ("fear,", 18.0, 69, 1.0, 95),
    ("suck-", 20.0, 67, 0.5, 88),
    ("ing", 20.5, 64, 0.5, 82),
    ("dark-", 21.0, 62, 0.5, 85),
    ("est", 21.5, 64, 0.5, 80),
    ("clear", 22.0, 64, 1.5, 85),

    # "Leading on your death's construction"
    ("Lead-", 24.0, 64, 0.5, 85),
    ("ing", 24.5, 64, 0.25, 78),
    ("on", 25.0, 67, 0.5, 88),
    ("your", 25.5, 67, 0.25, 78),
    ("death's", 26.0, 69, 0.5, 95),
    ("con-", 26.5, 71, 0.5, 98),
    ("struc-", 27.0, 69, 0.5, 92),
    ("tion", 27.5, 67, 1.5, 85),

    # "Taste me you will see, more is all you need"
    ("Taste", 32.0, 71, 0.5, 95),      # B4
    ("me", 32.5, 69, 0.5, 88),
    ("you", 33.0, 67, 0.5, 85),
    ("will", 33.5, 67, 0.25, 78),
    ("see,", 34.0, 69, 1.0, 92),
    ("more", 36.0, 71, 0.5, 95),
    ("is", 36.5, 69, 0.5, 85),
    ("all", 37.0, 67, 0.5, 88),
    ("you", 37.5, 67, 0.25, 78),
    ("need", 38.0, 69, 1.5, 90),

    # "Dedicated to how I'm killing you"
    ("Ded-", 40.0, 64, 0.5, 85),
    ("i-", 40.5, 64, 0.25, 78),
    ("cat-", 41.0, 67, 0.5, 90),
    ("ed", 41.5, 67, 0.25, 80),
    ("to", 42.0, 64, 0.5, 82),
    ("how", 42.5, 67, 0.5, 88),
    ("I'm", 43.0, 69, 0.5, 92),
    ("kill-", 43.5, 71, 0.5, 98),
    ("ing", 44.0, 69, 0.5, 90),
    ("you", 44.5, 67, 2.0, 85),
]

CHORUS_VOCAL = [
    # "Come crawling faster"
    ("Come", 0.0, 71, 0.5, 105),        # B4
    ("crawl-", 0.5, 71, 0.5, 100),
    ("ing", 1.0, 69, 0.5, 95),
    ("fas-", 1.5, 71, 0.5, 105),
    ("ter,", 2.0, 72, 1.5, 108),        # C5

    # "Obey your master"
    ("O-", 4.0, 71, 0.5, 100),
    ("bey", 4.5, 72, 0.5, 105),
    ("your", 5.0, 71, 0.5, 98),
    ("Mas-", 5.5, 74, 0.5, 115),        # D5 — peak
    ("ter!", 6.0, 76, 1.5, 120),        # E5 — "MASTER!"

    # "Your life burns faster"
    ("Your", 8.0, 71, 0.5, 100),
    ("life", 8.5, 71, 0.5, 95),
    ("burns", 9.0, 69, 0.5, 100),
    ("fas-", 9.5, 71, 0.5, 105),
    ("ter,", 10.0, 72, 1.5, 108),

    # "Obey your MASTER! MASTER!"
    ("O-", 12.0, 71, 0.5, 105),
    ("bey", 12.5, 72, 0.5, 108),
    ("your", 13.0, 71, 0.5, 100),
    ("Mas-", 13.5, 74, 0.5, 118),
    ("ter!", 14.0, 76, 0.75, 122),
    ("Mas-", 15.0, 74, 0.5, 120),
    ("ter!", 15.5, 76, 1.5, 125),       # big "MASTER!"
]

VERSE2_VOCAL = [
    # "Master of puppets I'm pulling your strings"
    ("Mas-", 0.0, 64, 0.5, 88),
    ("ter", 0.5, 64, 0.25, 80),
    ("of", 1.0, 64, 0.25, 78),
    ("pup-", 1.25, 67, 0.5, 92),
    ("pets", 1.75, 67, 0.5, 88),
    ("I'm", 2.25, 67, 0.25, 80),
    ("pull-", 2.5, 69, 0.5, 95),
    ("ing", 3.0, 69, 0.25, 85),
    ("your", 3.25, 67, 0.25, 80),
    ("strings", 3.5, 64, 1.5, 90),

    # "Twisting your mind and smashing your dreams"
    ("Twist-", 8.0, 64, 0.5, 88),
    ("ing", 8.5, 64, 0.25, 80),
    ("your", 9.0, 64, 0.25, 78),
    ("mind", 9.25, 67, 0.75, 92),
    ("and", 10.0, 67, 0.25, 78),
    ("smash-", 10.25, 69, 0.5, 95),
    ("ing", 10.75, 69, 0.25, 85),
    ("your", 11.0, 67, 0.25, 80),
    ("dreams", 11.25, 64, 1.75, 90),

    # "Blinded by me, you can't see a thing"
    ("Blind-", 16.0, 64, 0.5, 88),
    ("ed", 16.5, 64, 0.25, 80),
    ("by", 17.0, 67, 0.5, 85),
    ("me,", 17.5, 69, 1.0, 92),
    ("you", 19.0, 67, 0.25, 80),
    ("can't", 19.25, 67, 0.5, 85),
    ("see", 19.75, 69, 0.5, 90),
    ("a", 20.25, 67, 0.25, 78),
    ("thing", 20.5, 64, 2.0, 88),

    # "Just call my name 'cause I'll hear you scream"
    ("Just", 24.0, 64, 0.5, 85),
    ("call", 24.5, 67, 0.5, 90),
    ("my", 25.0, 67, 0.25, 80),
    ("name", 25.5, 69, 0.75, 95),
    ("'cause", 26.25, 67, 0.25, 80),
    ("I'll", 26.5, 67, 0.5, 85),
    ("hear", 27.0, 69, 0.5, 92),
    ("you", 27.5, 71, 0.5, 100),
    ("scream!", 28.0, 72, 2.0, 108),    # C5 — high intensity

    # "Needle work the way, never you betray"
    ("Nee-", 32.0, 71, 0.5, 95),
    ("dle", 32.5, 69, 0.5, 88),
    ("work", 33.0, 67, 0.5, 90),
    ("the", 33.5, 67, 0.25, 78),
    ("way,", 34.0, 69, 1.0, 92),
    ("nev-", 36.0, 71, 0.5, 95),
    ("er", 36.5, 69, 0.5, 88),
    ("you", 37.0, 67, 0.5, 85),
    ("be-", 37.5, 69, 0.5, 90),
    ("tray", 38.0, 67, 1.5, 88),

    # "Life of death becoming clearer"
    ("Life", 40.0, 64, 0.5, 85),
    ("of", 40.5, 64, 0.25, 78),
    ("death", 41.0, 67, 0.5, 92),
    ("be-", 41.5, 67, 0.25, 80),
    ("com-", 42.0, 69, 0.5, 90),
    ("ing", 42.5, 67, 0.5, 85),
    ("clear-", 43.0, 69, 0.5, 92),
    ("er", 43.5, 67, 1.5, 85),
]

PRECHORUS_VOCAL = [
    # "Pain monopoly, ritual misery"
    ("Pain", 0.0, 69, 0.5, 95),
    ("mo-", 0.5, 71, 0.5, 98),
    ("nop-", 1.0, 72, 0.5, 100),
    ("o-", 1.5, 71, 0.25, 92),
    ("ly,", 2.0, 69, 1.0, 95),
    ("ri-", 4.0, 69, 0.5, 92),
    ("tu-", 4.5, 71, 0.5, 95),
    ("al", 5.0, 72, 0.5, 98),
    ("mis-", 5.5, 74, 0.5, 102),
    ("er-", 6.0, 72, 0.5, 98),
    ("y", 6.5, 71, 1.5, 92),

    # "Chop your breakfast on a mirror"
    ("Chop", 8.0, 71, 0.5, 95),
    ("your", 8.5, 71, 0.25, 85),
    ("break-", 9.0, 72, 0.5, 98),
    ("fast", 9.5, 71, 0.5, 92),
    ("on", 10.0, 69, 0.5, 88),
    ("a", 10.5, 67, 0.25, 78),
    ("mir-", 11.0, 69, 0.5, 92),
    ("ror", 11.5, 71, 1.5, 95),
]

CLEAN_VOCAL = [
    # "Master, Master, where's the dreams that I've been after?"
    ("Mas-", 0.0, 64, 1.0, 65),
    ("ter,", 1.0, 67, 1.5, 62),
    ("Mas-", 4.0, 64, 1.0, 65),
    ("ter,", 5.0, 67, 1.5, 62),
    ("where's", 8.0, 69, 0.5, 68),
    ("the", 8.5, 67, 0.5, 60),
    ("dreams", 9.0, 69, 1.0, 72),
    ("that", 10.0, 67, 0.5, 62),
    ("I've", 10.5, 64, 0.5, 65),
    ("been", 11.0, 62, 0.5, 68),
    ("af-", 11.5, 64, 0.5, 70),
    ("ter?", 12.0, 67, 3.0, 65),

    # "Master, Master, you promised only lies"
    ("Mas-", 16.0, 64, 1.0, 65),
    ("ter,", 17.0, 67, 1.5, 62),
    ("Mas-", 20.0, 64, 1.0, 65),
    ("ter,", 21.0, 67, 1.5, 62),
    ("you", 24.0, 64, 0.5, 60),
    ("prom-", 24.5, 67, 0.5, 65),
    ("ised", 25.0, 69, 0.5, 68),
    ("on-", 25.5, 67, 0.5, 65),
    ("ly", 26.0, 64, 0.5, 62),
    ("lies", 26.5, 62, 3.5, 68),

    # "Laughter, laughter, all I hear or see is laughter"
    ("Laugh-", 32.0, 69, 1.0, 68),
    ("ter,", 33.0, 67, 1.5, 65),
    ("laugh-", 36.0, 69, 1.0, 70),
    ("ter,", 37.0, 67, 1.5, 65),
    ("all", 40.0, 64, 0.5, 62),
    ("I", 40.5, 64, 0.5, 60),
    ("hear", 41.0, 67, 0.5, 65),
    ("or", 41.5, 67, 0.25, 58),
    ("see", 42.0, 69, 0.5, 68),
    ("is", 42.5, 67, 0.25, 60),
    ("laugh-", 43.0, 69, 0.75, 72),
    ("ter", 43.75, 67, 3.0, 65),

    # "Laughter, laughter, laughing at my cries"
    ("Laugh-", 48.0, 69, 1.0, 70),
    ("ter,", 49.0, 67, 1.5, 65),
    ("laugh-", 52.0, 69, 1.0, 72),
    ("ter,", 53.0, 67, 1.5, 65),
    ("laugh-", 56.0, 71, 0.5, 75),     # B4 — building
    ("ing", 56.5, 69, 0.5, 70),
    ("at", 57.0, 67, 0.5, 65),
    ("my", 57.5, 69, 0.5, 68),
    ("cries", 58.0, 71, 4.0, 78),      # sustained — emotional peak
]


def _add_vocal_phrase(midi, t, ch, beat, phrase):
    """Add a vocal phrase (list of (text, rel_beat, note, dur, vel))."""
    for text, rel_beat, note, dur, vel in phrase:
        add_note(midi, t, ch, note, beat + rel_beat, dur, vel)


def build_vocal_melody():
    """Generate the vocal melody guide track."""
    midi = MIDIFile(1, ticks_per_quarternote=TICKS_PER_BEAT)
    t, ch = 0, 0
    midi.addTempo(t, 0, TEMPO_FAST)
    midi.addProgramChange(t, ch, 0, 54)  # Synth Voice (or Ahh Choir)

    beat = 0.0

    # Intro (no vocals)
    add_marker(midi, t, beat, "Intro")
    beat += INTRO_BARS * 4

    # Main riff (no vocals)
    add_marker(midi, t, beat, "Main Riff")
    beat += MAIN_RIFF_BARS * 4

    # Verse 1
    add_marker(midi, t, beat, "Verse 1")
    _add_vocal_phrase(midi, t, ch, beat, VERSE1_VOCAL)
    beat += VERSE1_BARS * 4

    # Pre-Chorus 1
    add_marker(midi, t, beat, "Pre-Chorus 1")
    _add_vocal_phrase(midi, t, ch, beat, PRECHORUS_VOCAL)
    beat += PRECHORUS1_BARS * 4

    # Chorus 1
    add_marker(midi, t, beat, "Chorus 1")
    _add_vocal_phrase(midi, t, ch, beat, CHORUS_VOCAL)
    beat += CHORUS1_BARS * 4

    # Interlude (no vocals)
    add_marker(midi, t, beat, "Interlude")
    beat += INTERLUDE1_BARS * 4

    # Verse 2
    add_marker(midi, t, beat, "Verse 2")
    _add_vocal_phrase(midi, t, ch, beat, VERSE2_VOCAL)
    beat += VERSE2_BARS * 4

    # Pre-Chorus 2
    add_marker(midi, t, beat, "Pre-Chorus 2")
    _add_vocal_phrase(midi, t, ch, beat, PRECHORUS_VOCAL)
    beat += PRECHORUS2_BARS * 4

    # Chorus 2
    add_marker(midi, t, beat, "Chorus 2")
    _add_vocal_phrase(midi, t, ch, beat, CHORUS_VOCAL)
    beat += CHORUS2_BARS * 4

    # Clean section — tempo change
    add_marker(midi, t, beat, "Clean Interlude")
    midi.addTempo(t, beat, TEMPO_CLEAN)
    _add_vocal_phrase(midi, t, ch, beat, CLEAN_VOCAL)
    beat += CLEAN_BARS * 4

    # Build-up (no vocals, or screams — we skip melody)
    add_marker(midi, t, beat, "Build-up")
    for bar in range(BUILDUP_BARS):
        tempo = TEMPO_CLEAN + (TEMPO_FAST - TEMPO_CLEAN) * (bar / BUILDUP_BARS)
        midi.addTempo(t, beat + bar * 4, int(tempo))
    beat += BUILDUP_BARS * 4
    midi.addTempo(t, beat, TEMPO_FAST)

    # Solo (no vocals)
    add_marker(midi, t, beat, "Guitar Solo")
    beat += SOLO_BARS * 4

    # Verse 3 (abbreviated — reuse verse 1 first half)
    add_marker(midi, t, beat, "Verse 3")
    # Use just the first 32 beats worth of verse 1 vocal
    v3_phrase = [(txt, rb, n, d, v) for txt, rb, n, d, v in VERSE1_VOCAL if rb < 32]
    _add_vocal_phrase(midi, t, ch, beat, v3_phrase)
    beat += VERSE3_BARS * 4

    # Pre-Chorus 3
    add_marker(midi, t, beat, "Pre-Chorus 3")
    _add_vocal_phrase(midi, t, ch, beat, PRECHORUS_VOCAL)
    beat += PRECHORUS3_BARS * 4

    # Chorus 3
    add_marker(midi, t, beat, "Chorus 3")
    _add_vocal_phrase(midi, t, ch, beat, CHORUS_VOCAL)
    beat += CHORUS3_BARS * 4

    # Outro (no vocals)
    add_marker(midi, t, beat, "Outro")
    beat += OUTRO_BARS * 4

    add_marker(midi, t, beat, "END")

    with open("MoP_Vocal_Melody.mid", "wb") as f:
        midi.writeFile(f)
    print("  ✓ MoP_Vocal_Melody.mid")


# ================================================================
#  LYRICS & CHORD CUE TRACK
# ================================================================

def build_lyrics_chords():
    """Generate the lyrics/chord cue track with markers, lyrics, and cue points."""
    midi = MIDIFile(1, ticks_per_quarternote=TICKS_PER_BEAT)
    t = 0
    midi.addTempo(t, 0, TEMPO_FAST)

    beat = 0.0

    # ---- Intro ----
    add_marker(midi, t, beat, "Intro")
    for bar in range(INTRO_BARS):
        add_cue(midi, t, beat + bar * 4, "E5")
    beat += INTRO_BARS * 4

    # ---- Main Riff ----
    add_marker(midi, t, beat, "Main Riff")
    for bar in range(MAIN_RIFF_BARS):
        add_cue(midi, t, beat + bar * 4, "E5")
        if bar % 2 == 1:
            add_cue(midi, t, beat + bar * 4 + 2, "G5")
    beat += MAIN_RIFF_BARS * 4

    # ---- Verse 1 + lyrics ----
    add_marker(midi, t, beat, "Verse 1")
    for bar in range(VERSE1_BARS):
        add_cue(midi, t, beat + bar * 4, "E5")
    for txt, rb, _, _, _ in VERSE1_VOCAL:
        add_lyric(midi, t, beat + rb, txt)
    beat += VERSE1_BARS * 4

    # ---- Pre-Chorus 1 ----
    add_marker(midi, t, beat, "Pre-Chorus 1")
    pc_chords = ["C5", "D5", "Eb5", "E5"]
    for bar in range(PRECHORUS1_BARS):
        add_cue(midi, t, beat + bar * 4, pc_chords[bar % 4])
    for txt, rb, _, _, _ in PRECHORUS_VOCAL:
        add_lyric(midi, t, beat + rb, txt)
    beat += PRECHORUS1_BARS * 4

    # ---- Chorus 1 ----
    add_marker(midi, t, beat, "Chorus 1")
    chorus_chords = [("B5", 0), ("A5", 2), ("G5", 4), ("F#5", 6),
                     ("E5", 8), ("E5", 12), ("F5", 14), ("F#5", 15)]
    for name, off in chorus_chords:
        if off < CHORUS1_BARS * 4:
            add_cue(midi, t, beat + off, name)
    for txt, rb, _, _, _ in CHORUS_VOCAL:
        add_lyric(midi, t, beat + rb, txt)
    beat += CHORUS1_BARS * 4

    # ---- Interlude ----
    add_marker(midi, t, beat, "Interlude")
    for bar in range(INTERLUDE1_BARS):
        add_cue(midi, t, beat + bar * 4, "E5")
    beat += INTERLUDE1_BARS * 4

    # ---- Verse 2 + lyrics ----
    add_marker(midi, t, beat, "Verse 2")
    for bar in range(VERSE2_BARS):
        add_cue(midi, t, beat + bar * 4, "E5")
    for txt, rb, _, _, _ in VERSE2_VOCAL:
        add_lyric(midi, t, beat + rb, txt)
    beat += VERSE2_BARS * 4

    # ---- Pre-Chorus 2 ----
    add_marker(midi, t, beat, "Pre-Chorus 2")
    for bar in range(PRECHORUS2_BARS):
        add_cue(midi, t, beat + bar * 4, pc_chords[bar % 4])
    for txt, rb, _, _, _ in PRECHORUS_VOCAL:
        add_lyric(midi, t, beat + rb, txt)
    beat += PRECHORUS2_BARS * 4

    # ---- Chorus 2 ----
    add_marker(midi, t, beat, "Chorus 2")
    for name, off in chorus_chords:
        if off < CHORUS2_BARS * 4:
            add_cue(midi, t, beat + off, name)
    for txt, rb, _, _, _ in CHORUS_VOCAL:
        add_lyric(midi, t, beat + rb, txt)
    beat += CHORUS2_BARS * 4

    # ---- Clean Interlude ----
    add_marker(midi, t, beat, "Clean Interlude")
    midi.addTempo(t, beat, TEMPO_CLEAN)
    clean_chords = [("Am", 0), ("Am", 8), ("G", 16), ("G", 24),
                    ("Em", 32), ("Em", 40), ("C", 48), ("D", 52)]
    for name, off in clean_chords:
        if off < CLEAN_BARS * 4:
            add_cue(midi, t, beat + off, name)
    for txt, rb, _, _, _ in CLEAN_VOCAL:
        add_lyric(midi, t, beat + rb, txt)
    beat += CLEAN_BARS * 4

    # ---- Build-up ----
    add_marker(midi, t, beat, "Build-up")
    for bar in range(BUILDUP_BARS):
        tempo = TEMPO_CLEAN + (TEMPO_FAST - TEMPO_CLEAN) * (bar / BUILDUP_BARS)
        midi.addTempo(t, beat + bar * 4, int(tempo))
    for bar in range(BUILDUP_BARS):
        add_cue(midi, t, beat + bar * 4, "E5")
    beat += BUILDUP_BARS * 4
    midi.addTempo(t, beat, TEMPO_FAST)

    # ---- Guitar Solo ----
    add_marker(midi, t, beat, "Guitar Solo")
    for bar in range(SOLO_BARS):
        add_cue(midi, t, beat + bar * 4, "E5")
    beat += SOLO_BARS * 4

    # ---- Verse 3 ----
    add_marker(midi, t, beat, "Verse 3")
    for bar in range(VERSE3_BARS):
        add_cue(midi, t, beat + bar * 4, "E5")
    v3_phrase = [(txt, rb, n, d, v) for txt, rb, n, d, v in VERSE1_VOCAL if rb < 32]
    for txt, rb, _, _, _ in v3_phrase:
        add_lyric(midi, t, beat + rb, txt)
    beat += VERSE3_BARS * 4

    # ---- Pre-Chorus 3 ----
    add_marker(midi, t, beat, "Pre-Chorus 3")
    for bar in range(PRECHORUS3_BARS):
        add_cue(midi, t, beat + bar * 4, pc_chords[bar % 4])
    for txt, rb, _, _, _ in PRECHORUS_VOCAL:
        add_lyric(midi, t, beat + rb, txt)
    beat += PRECHORUS3_BARS * 4

    # ---- Chorus 3 ----
    add_marker(midi, t, beat, "Chorus 3")
    for name, off in chorus_chords:
        if off < CHORUS3_BARS * 4:
            add_cue(midi, t, beat + off, name)
    for txt, rb, _, _, _ in CHORUS_VOCAL:
        add_lyric(midi, t, beat + rb, txt)
    beat += CHORUS3_BARS * 4

    # ---- Outro ----
    add_marker(midi, t, beat, "Outro")
    for bar in range(OUTRO_BARS):
        add_cue(midi, t, beat + bar * 4, "E5")
    beat += OUTRO_BARS * 4

    add_marker(midi, t, beat, "END")

    with open("MoP_Lyrics_Chords.mid", "wb") as f:
        midi.writeFile(f)
    print("  ✓ MoP_Lyrics_Chords.mid")


# ================================================================
#  MAIN ENTRY POINT
# ================================================================

def generate():
    """Generate all Master of Puppets MIDI files."""
    print("Generating Master of Puppets MIDI files...")
    build_rhythm_guitar()
    build_lead_guitar()
    build_bass_guitar()
    build_drums()
    build_vocal_melody()
    build_lyrics_chords()
    print("Done! 6 MIDI files generated.")


if __name__ == "__main__":
    generate()
