from midiutil import MIDIFile
from midiutil.MidiFile import Text
import struct

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
    notes = CHORDS[chord_name]
    for note in notes:
        midi_obj.addNote(track, channel, note, start_time, duration_beats, volume)

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

def play_section(pattern, num_bars, section_label=None, lyrics=None):
    """Play a chord pattern for num_bars repetitions.
    section_label — adds a Marker on Reaper's timeline at the section start.
    lyrics        — list of (bar_index, beat_offset, text) for lyric events.
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
            add_chord(MyMIDI, chord, current_beat, beats)
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
    (0, 0, "I hurt my-"),     (0, 2, "self to-"),   (0, 4, "day"),
    (1, 0, "to see if"),      (1, 2, "I still"),    (1, 4, "feel"),
    (2, 0, "I focus"),        (2, 2, "on the"),     (2, 4, "pain"),
    (3, 0, "the only"),       (3, 2, "thing that's"),(3, 4, "real"),
]

CHORUS1_LYRICS = [
    (0, 0, "What have I be-"),  (0, 4, "come"),
    (0, 8, "my sweetest"),      (0, 12, "friend?"),
    (1, 0, "Every-one I"),      (1, 4, "know"),
    (1, 8, "goes a-way"),       (1, 12, "in the end"),
]

VERSE2_LYRICS = [
    (0, 0, "I wear this"),    (0, 2, "crown of"),   (0, 4, "thorns"),
    (1, 0, "upon my"),        (1, 2, "liar's"),     (1, 4, "chair"),
    (2, 0, "full of"),        (2, 2, "broken"),     (2, 4, "thoughts"),
    (3, 0, "I cannot"),       (3, 2, "re-"),        (3, 4, "pair"),
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
play_section(VERSE,  2, "Intro")
play_section(VERSE,  4, "Verse 1",  VERSE1_LYRICS)
play_section(CHORUS, 2, "Chorus 1", CHORUS1_LYRICS)
play_section(VERSE,  4, "Verse 2",  VERSE2_LYRICS)
play_section(CHORUS, 2, "Chorus 2", CHORUS2_LYRICS)
play_section(BRIDGE, 2, "Bridge",   BRIDGE_LYRICS)
play_section(VERSE,  2, "Outro")

# Save the file
with open("Hurt_Sequence.mid", "wb") as output_file:
    MyMIDI.writeFile(output_file)

print("MIDI file 'Hurt_Sequence.mid' generated successfully!")