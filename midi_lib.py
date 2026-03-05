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
        midibytes += struct.pack('>BB', 0xFF, 0x06)
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
        midibytes += struct.pack('>BB', 0xFF, 0x05)
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
        midibytes += struct.pack('>BB', 0xFF, 0x07)
        payload = writeVarLength(len(self.text))
        for b in payload:
            midibytes += struct.pack('B', b)
        midibytes += self.text
        return midibytes


# ---------------------------------------------------------------------------
# Event injection helpers
# ---------------------------------------------------------------------------
def _inject_event(midi_obj, track_num, evt):
    """Inject a custom meta event into the internal track event list."""
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


# ---------------------------------------------------------------------------
# STRUM ENGINE — realistic guitar feel for SampleTank
# ---------------------------------------------------------------------------
STRUM_SPREAD   = 0.012   # time between each string hit (beats)
BASE_VELOCITY  = 90      # centre velocity for strums
HUMANIZE_TIME  = 0.006   # random timing jitter per note (beats)
HUMANIZE_VEL   = 12      # random velocity jitter (+/-)

def strum_chord(midi_obj, track, channel, chord_notes, start_time,
                duration_beats, direction='down', velocity=None, muted=False):
    """Add a strummed chord with per-string offset and velocity shaping."""
    notes = list(chord_notes)
    if direction == 'up':
        notes = list(reversed(notes))

    vel = velocity or BASE_VELOCITY
    note_dur = 0.08 if muted else duration_beats

    for i, note in enumerate(notes):
        t = start_time + i * STRUM_SPREAD
        t += random.uniform(-HUMANIZE_TIME, HUMANIZE_TIME)
        if direction == 'down':
            v = vel - i * 3
        else:
            v = vel - (len(notes) - 1 - i) * 3
        v += random.randint(-HUMANIZE_VEL, HUMANIZE_VEL)
        v = max(30, min(127, v))
        midi_obj.addNote(track, channel, note, max(0, t), note_dur, v)


def add_strummed_chord(midi_obj, track, channel, chord_notes, start_time,
                        chord_duration, strum_pattern):
    """Apply a strum pattern across the duration of one chord."""
    for beat_off, direction, vel_scale, muted in strum_pattern:
        if beat_off >= chord_duration:
            continue
        vel = int(BASE_VELOCITY * vel_scale)
        remaining = chord_duration - beat_off
        strum_chord(midi_obj, track, channel, chord_notes,
                     start_time + beat_off, remaining, direction, vel, muted)


# ---------------------------------------------------------------------------
# STRUM PATTERNS
# ---------------------------------------------------------------------------
VERSE_STRUM = [
    (0.0,  'down', 0.75, False),
    (1.5,  'up',   0.55, False),
    (2.0,  'down', 0.65, False),
    (3.0,  'up',   0.50, False),
]

CHORUS_STRUM = [
    (0.0,  'down', 0.90, False),
    (1.0,  'down', 0.60, False),
    (1.5,  'up',   0.55, False),
    (2.0,  'down', 0.80, False),
    (2.5,  'up',   0.50, False),
    (3.0,  'down', 0.70, False),
    (3.5,  'up',   0.55, False),
]

BRIDGE_STRUM = [
    (0.0,  'down', 1.00, False),
    (0.5,  'up',   0.60, False),
    (1.0,  'down', 0.85, False),
    (1.5,  'up',   0.55, False),
    (2.0,  'down', 0.90, False),
    (2.5,  'up',   0.60, False),
    (3.0,  'down', 0.80, False),
    (3.5,  'up',   0.55, False),
]

SPARSE_STRUM = [
    (0.0,  'down', 0.60, False),
    (2.0,  'down', 0.50, False),
]


# ---------------------------------------------------------------------------
# Song builder helpers
# ---------------------------------------------------------------------------
def build_song(chords, sections, tempo, separate_chord_track=True,
               sequence_file="output_sequence.mid",
               chords_file="output_chords.mid"):
    """Build MIDI files from a song definition.

    chords  — dict mapping chord names to MIDI note lists
    sections — list of dicts:
        { 'pattern': [('chord', beats), ...],
          'repeats': int,
          'label':   str or None,
          'lyrics':  [(bar, beat_off, text), ...] or None,
          'strum':   strum pattern list }
    """
    track   = 0
    channel = 0

    midi = MIDIFile(1)
    midi.addTempo(track, 0, tempo)

    current_beat = 0

    for section in sections:
        pattern = section['pattern']
        repeats = section['repeats']
        label   = section.get('label')
        lyrics  = section.get('lyrics')
        strum   = section.get('strum', VERSE_STRUM)

        if label:
            add_marker(midi, track, current_beat, label)

        lyric_map = {}
        if lyrics:
            for bar_idx, beat_off, text in lyrics:
                lyric_map[(bar_idx, beat_off)] = text

        for bar in range(repeats):
            beat_in_bar = 0
            for chord_name, beats in pattern:
                if not separate_chord_track:
                    add_cue(midi, track, current_beat, chord_name)
                key = (bar, beat_in_bar)
                if key in lyric_map:
                    add_lyric(midi, track, current_beat, lyric_map[key])
                add_strummed_chord(midi, track, channel,
                                    chords[chord_name], current_beat,
                                    beats, strum)
                current_beat += beats
                beat_in_bar += beats

    with open(sequence_file, "wb") as f:
        midi.writeFile(f)
    print(f"MIDI file '{sequence_file}' generated successfully!")

    if separate_chord_track:
        chord_midi = MIDIFile(1)
        chord_midi.addTempo(0, 0, tempo)
        label_beat = 0

        for section in sections:
            pattern = section['pattern']
            repeats = section['repeats']
            label   = section.get('label')

            if label:
                add_marker(chord_midi, 0, label_beat, label)
            for _ in range(repeats):
                for chord_name, beats in pattern:
                    add_cue(chord_midi, 0, label_beat, chord_name)
                    chord_midi.addText(0, label_beat, chord_name)
                    label_beat += beats

        add_marker(chord_midi, 0, label_beat, "END")

        with open(chords_file, "wb") as f:
            chord_midi.writeFile(f)
        print(f"MIDI file '{chords_file}' generated successfully!")
