from midiutil import MIDIFile
from midiutil.MidiFile import Text
import struct
import random

# ---------------------------------------------------------------------------
# Custom MIDI meta events for Reaper markers & lyrics
# ---------------------------------------------------------------------------
class Marker(Text):
    """MIDI Marker meta event (0x06) — appears on Reaper's timeline."""
    evtname = 'Marker'
    def serialize(self, previous_event_tick):
        from midiutil.MidiFile import writeVarLength
        midibytes = b""
        varTime = writeVarLength(self.tick - previous_event_tick)
        for b in varTime:
            midibytes += struct.pack('>B', b)
        midibytes += struct.pack('>BB', 0xFF, 0x06)          # meta marker
        payload = writeVarLength(len(self.text))
        for b in payload:
            midibytes += struct.pack('B', b)
        midibytes += self.text
        return midibytes

class Lyric(Text):
    """MIDI Lyric meta event (0x05) — shown in Reaper MIDI editor."""
    evtname = 'Lyric'
    def serialize(self, previous_event_tick):
        from midiutil.MidiFile import writeVarLength
        midibytes = b""
        varTime = writeVarLength(self.tick - previous_event_tick)
        for b in varTime:
            midibytes += struct.pack('>B', b)
        midibytes += struct.pack('>BB', 0xFF, 0x05)          # meta lyric
        payload = writeVarLength(len(self.text))
        for b in payload:
            midibytes += struct.pack('B', b)
        midibytes += self.text
        return midibytes

class CuePoint(Text):
    """MIDI Cue Point meta event (0x07) — Reaper region/cue marker."""
    evtname = 'CuePoint'
    def serialize(self, previous_event_tick):
        from midiutil.MidiFile import writeVarLength
        midibytes = b""
        varTime = writeVarLength(self.tick - previous_event_tick)
        for b in varTime:
            midibytes += struct.pack('>B', b)
        midibytes += struct.pack('>BB', 0xFF, 0x07)          # meta cue
        payload = writeVarLength(len(self.text))
        for b in payload:
            midibytes += struct.pack('B', b)
        midibytes += self.text
        return midibytes

def _inject_event(midi_obj, track_num, evt):
    """Inject a custom meta event into the internal track event list."""
    # midiutil uses an internal offset of +1 for the data track when numTracks==1
    real_track = track_num + 1 if len(midi_obj.tracks) > 1 else track_num
    evt.insertion_order = midi_obj.event_counter
    midi_obj.event_counter += 1
    midi_obj.tracks[real_track].eventList.append(evt)

def add_marker(midi_obj, track_num, time_beats, text):
    """Add a timeline marker (visible in Reaper arrange view)."""
    tick = int(time_beats * midi_obj.ticks_per_quarternote)
    _inject_event(midi_obj, track_num, Marker(tick, text))

def add_lyric(midi_obj, track_num, time_beats, text):
    """Add a lyric event (visible in Reaper MIDI editor)."""
    tick = int(time_beats * midi_obj.ticks_per_quarternote)
    _inject_event(midi_obj, track_num, Lyric(tick, text))

def add_cue(midi_obj, track_num, time_beats, text):
    """Add a cue point (visible in Reaper as region marker)."""
    tick = int(time_beats * midi_obj.ticks_per_quarternote)
    _inject_event(midi_obj, track_num, CuePoint(tick, text))

# MIDI setup
track    = 0
channel  = 0
time     = 0    # In beats
duration = 1    # In beats
volume   = 100  # 0-127
tempo    = 90   # Standard NIN tempo is around 90-95 BPM

# Define the Chords (MIDI note numbers) — open guitar voicings
CHORDS = {
    # Bm  (X24432): B2 F#3 B3 D4 F#4
    'Bm':    [47, 54, 59, 62, 66],
    # D   (XX0232): D3 A3 D4 F#4
    'D':     [50, 57, 62, 66],
    # Em  (022000): E2 B2 E3 G3 B3 E4
    'Em':    [40, 47, 52, 55, 59, 64],
    # Esus2 (024400): E2 B2 F#3 B3 E4
    'Esus2': [40, 47, 54, 59, 64],
    # G   (320003): G2 B2 D3 G3 B3 G4
    'G':     [43, 47, 50, 55, 59, 67],
    # A   (X02220): A2 E3 A3 C#4 E4
    'A':     [45, 52, 57, 61, 64],
    # C   (X32010): C3 E3 G3 C4 E4
    'C':     [48, 52, 55, 60, 64],
    # Am  (X02210): A2 E3 A3 C4 E4
    'Am':    [45, 52, 57, 60, 64],
    # G/B (X20003): B2 D3 G3 B3 G4
    'G/B':   [47, 50, 55, 59, 67],
    # F   (133211): F2 C3 F3 A3 C4 F4
    'F':     [41, 48, 53, 57, 60, 65],
    # Dsus2 (XX0230): D3 A3 D4 E4
    'Dsus2': [50, 57, 62, 64],
}

def add_chord(midi_obj, chord_name, start_time, duration_beats):
    """Legacy block-chord (no strum). Kept for reference."""
    notes = CHORDS[chord_name]
    for note in notes:
        midi_obj.addNote(track, channel, note, start_time, duration_beats, volume)


# ---------------------------------------------------------------------------
# STRUM ENGINE — realistic guitar feel for SampleTank
# ---------------------------------------------------------------------------
# Strum offset per string in beats (at 90 BPM, 1 beat = 667ms, so 0.012 ≈ 8ms)
STRUM_SPREAD   = 0.012   # time between each string hit (beats)
BASE_VELOCITY  = 90      # centre velocity for strums
HUMANIZE_TIME  = 0.006   # random timing jitter per note (beats)
HUMANIZE_VEL   = 12      # random velocity jitter (+/-)

def strum_chord(midi_obj, chord_name, start_time, duration_beats,
                direction='down', velocity=None, muted=False):
    """Add a strummed chord with per-string offset and velocity shaping.

    direction: 'down' = low→high, 'up' = high→low
    velocity:  override base velocity (useful for accents / ghost strums)
    muted:     short duration for percussive muted strums
    """
    notes = CHORDS[chord_name]
    if direction == 'up':
        notes = list(reversed(notes))

    vel = velocity or BASE_VELOCITY
    note_dur = 0.08 if muted else duration_beats  # muted = very short

    for i, note in enumerate(notes):
        # Stagger each string
        t = start_time + i * STRUM_SPREAD
        # Humanize timing slightly
        t += random.uniform(-HUMANIZE_TIME, HUMANIZE_TIME)
        # Velocity: first string loudest on downstroke, shape across strings
        if direction == 'down':
            v = vel - i * 3            # bass strings a bit louder
        else:
            v = vel - (len(notes) - 1 - i) * 3  # treble strings louder on up
        v += random.randint(-HUMANIZE_VEL, HUMANIZE_VEL)
        v = max(30, min(127, v))       # clamp to MIDI range

        midi_obj.addNote(track, channel, note, max(0, t), note_dur, v)


# ---------------------------------------------------------------------------
# STRUM PATTERNS — define rhythmic patterns per section style
# ---------------------------------------------------------------------------
# Each entry: (beat_offset, direction, velocity_scale, is_muted)
# Velocity scale is multiplied by BASE_VELOCITY.

# Verse: gentle fingerpick / soft strum — "Hurt" is very sparse
VERSE_STRUM = [
    (0.0,  'down', 0.75, False),    # beat 1 — soft down
    (1.5,  'up',   0.55, False),    # & of 2 — ghost up
    (2.0,  'down', 0.65, False),    # beat 3 — medium down
    (3.0,  'up',   0.50, False),    # beat 4 — light up
]

# Chorus: builds intensity
CHORUS_STRUM = [
    (0.0,  'down', 0.90, False),    # beat 1 — accent
    (1.0,  'down', 0.60, False),    # beat 2 — lighter
    (1.5,  'up',   0.55, False),    # & of 2
    (2.0,  'down', 0.80, False),    # beat 3
    (2.5,  'up',   0.50, False),    # & of 3
    (3.0,  'down', 0.70, False),    # beat 4
    (3.5,  'up',   0.55, False),    # & of 4
]

# Bridge: most intensity
BRIDGE_STRUM = [
    (0.0,  'down', 1.00, False),    # beat 1 — full accent
    (0.5,  'up',   0.60, False),
    (1.0,  'down', 0.85, False),
    (1.5,  'up',   0.55, False),
    (2.0,  'down', 0.90, False),
    (2.5,  'up',   0.60, False),
    (3.0,  'down', 0.80, False),
    (3.5,  'up',   0.55, False),
]

# Intro / outro: very sparse, just a couple of gentle strums
SPARSE_STRUM = [
    (0.0,  'down', 0.60, False),
    (2.0,  'down', 0.50, False),
]

def add_strummed_chord(midi_obj, chord_name, start_time, chord_duration,
                        strum_pattern=None):
    """Apply a strum pattern across the duration of one chord."""
    pattern = strum_pattern or VERSE_STRUM
    for beat_off, direction, vel_scale, muted in pattern:
        if beat_off >= chord_duration:
            continue  # skip strums that fall outside chord duration
        vel = int(BASE_VELOCITY * vel_scale)
        remaining = chord_duration - beat_off
        strum_chord(midi_obj, chord_name, start_time + beat_off,
                     remaining, direction, vel, muted)

# Create the MIDIFile object
MyMIDI = MIDIFile(1) 
MyMIDI.addTempo(track, time, tempo)

# ---------------------------------------------------------
# SONG STRUCTURE — Nine Inch Nails "Hurt"
# ---------------------------------------------------------
# Verse:  G - A - Em  (quiet, arpeggiated)
# Chorus: C - G/B - Am - F  ("What have I become…")
# Bridge: Am - F - C - Dsus2 ("If I could start again…")
# ---------------------------------------------------------
current_beat = 0

def play_section(pattern, num_bars, section_label=None, lyrics=None,
                  strum_pattern=None):
    """Play a chord pattern for num_bars repetitions.
    section_label — adds a Marker on Reaper's timeline at the section start.
    lyrics        — list of (bar_index, beat_offset, text) for lyric events.
    strum_pattern — which strum rhythm to use (default: VERSE_STRUM).
    """
    global current_beat
    if section_label:
        add_marker(MyMIDI, track, current_beat, section_label)
    lyric_map = {}
    if lyrics:
        for bar_idx, beat_off, text in lyrics:
            lyric_map[(bar_idx, beat_off)] = text
    for bar in range(num_bars):
        beat_in_bar = 0
        for chord, beats in pattern:
            # Chord name as a cue point
            add_cue(MyMIDI, track, current_beat, chord)
            # Lyrics at matching positions
            key = (bar, beat_in_bar)
            if key in lyric_map:
                add_lyric(MyMIDI, track, current_beat, lyric_map[key])
            add_strummed_chord(MyMIDI, chord, current_beat, beats,
                                strum_pattern)
            current_beat += beats
            beat_in_bar += beats

# -- Patterns (chord, duration in beats) --
VERSE   = [('G', 2), ('A', 2), ('Em', 4)]               # 8 beats (2 bars of 4/4)
CHORUS  = [('C', 4), ('G/B', 4), ('Am', 4), ('F', 4)]   # 16 beats (4 bars of 4/4)
BRIDGE  = [('Am', 4), ('F', 4), ('C', 4), ('Dsus2', 4)] # 16 beats (4 bars of 4/4)

# ---------------------------------------------------------
# LYRICS  (bar_index within section, beat_offset, text)
# ---------------------------------------------------------
VERSE1_LYRICS = [
    (0, 0, "I hurt my-"),     (0, 2, "self to-"),    (0, 4, "day"),
    (1, 0, "to see if"),      (1, 2, "I still"),     (1, 4, "feel"),
    (2, 0, "I focus"),        (2, 2, "on the"),      (2, 4, "pain"),
    (3, 0, "the only"),       (3, 2, "thing that's"),(3, 4, "real"),
    (4, 0, "The needle"),     (4, 2, "tears a"),     (4, 4, "hole"),
    (5, 0, "the old fa-"),    (5, 2, "miliar"),      (5, 4, "sting"),
    (6, 0, "Try to kill"),    (6, 2, "it all a-"),   (6, 4, "way"),
    (7, 0, "but I re-"),     (7, 2, "member"),      (7, 4, "everything"),
]

CHORUS1_LYRICS = [
    (0, 0, "What have I be-"),  (0, 4, "come"),
    (0, 8, "my sweetest"),      (0, 12, "friend?"),
    (1, 0, "Every-one I"),      (1, 4, "know"),
    (1, 8, "goes a-way"),       (1, 12, "in the end"),
]

VERSE2_LYRICS = [
    (0, 0, "I wear this"),    (0, 2, "crown of"),    (0, 4, "thorns"),
    (1, 0, "upon my"),        (1, 2, "liar's"),      (1, 4, "chair"),
    (2, 0, "full of"),        (2, 2, "broken"),      (2, 4, "thoughts"),
    (3, 0, "I cannot"),       (3, 2, "re-"),         (3, 4, "pair"),
    (4, 0, "Beneath the"),    (4, 2, "stains of"),   (4, 4, "time"),
    (5, 0, "the feelings"),   (5, 2, "dis-a-"),      (5, 4, "ppear"),
    (6, 0, "You are"),        (6, 2, "someone"),     (6, 4, "else"),
    (7, 0, "I am"),           (7, 2, "still right"), (7, 4, "here"),
]

CHORUS2_LYRICS = [
    (0, 0, "And you could"),  (0, 4, "have it"),
    (0, 8, "all"),            (0, 12, "my empire of dirt"),
    (1, 0, "I will let"),     (1, 4, "you"),
    (1, 8, "down"),           (1, 12, "I will make you hurt"),
]

BRIDGE_LYRICS = [
    (0, 0, "If I could"),     (0, 4, "start a-"),
    (0, 8, "gain"),           (0, 12, "a million"),
    (1, 0, "miles a-"),       (1, 4, "way"),
    (1, 8, "I would"),        (1, 12, "keep myself"),
]

# BUILD THE SONG
play_section(VERSE,  2, "Intro",    strum_pattern=SPARSE_STRUM)
play_section(VERSE,  8, "Verse 1",  VERSE1_LYRICS,  VERSE_STRUM)
play_section(CHORUS, 2, "Chorus 1", CHORUS1_LYRICS, CHORUS_STRUM)
play_section(VERSE,  8, "Verse 2",  VERSE2_LYRICS,  VERSE_STRUM)
play_section(CHORUS, 2, "Chorus 2", CHORUS2_LYRICS, CHORUS_STRUM)
play_section(BRIDGE, 2, "Bridge",   BRIDGE_LYRICS,  BRIDGE_STRUM)
play_section(VERSE,  4, "Outro",    strum_pattern=SPARSE_STRUM)

# Save the file
with open("Hurt_Sequence.mid", "wb") as output_file:
    MyMIDI.writeFile(output_file)

print("MIDI file 'Hurt_Sequence.mid' generated successfully!")

# ---------------------------------------------------------
# CHORD LABEL TRACK — empty MIDI with just markers & cue points
# ---------------------------------------------------------
ChordMIDI = MIDIFile(1)
ChordMIDI.addTempo(0, 0, tempo)

label_beat = 0

def label_section(pattern, num_bars, section_label=None):
    """Write chord labels and section markers only — no notes."""
    global label_beat
    if section_label:
        add_marker(ChordMIDI, 0, label_beat, section_label)
    for _ in range(num_bars):
        for chord, beats in pattern:
            add_cue(ChordMIDI, 0, label_beat, chord)
            # Also add as text so it shows in the MIDI item in Reaper
            ChordMIDI.addText(0, label_beat, chord)
            label_beat += beats

label_section(VERSE,  2, "Intro")
label_section(VERSE,  8, "Verse 1")
label_section(CHORUS, 2, "Chorus 1")
label_section(VERSE,  8, "Verse 2")
label_section(CHORUS, 2, "Chorus 2")
label_section(BRIDGE, 2, "Bridge")
label_section(VERSE,  4, "Outro")

# Add an end-of-song marker so the MIDI extends to the full length
add_marker(ChordMIDI, 0, label_beat, "END")

with open("Hurt_Chords.mid", "wb") as output_file:
    ChordMIDI.writeFile(output_file)

print("MIDI file 'Hurt_Chords.mid' generated successfully!")