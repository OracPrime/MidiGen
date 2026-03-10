from midiutil import MIDIFile
from midiutil.MidiFile import Text
import struct

from strums import (  # noqa: F401 — re-exported for backward compat
    strum_chord, add_strummed_chord,
    VERSE_STRUM, CHORUS_STRUM, BRIDGE_STRUM, SPARSE_STRUM,
)

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
# Song builder helpers
# ---------------------------------------------------------------------------
def build_song(chords, sections, tempo, separate_chord_track=True,
               sequence_file="output_sequence.mid",
               chords_file="output_chords.mid"):
    """Build MIDI files from a song definition.

    chords  — dict *or* list of dicts mapping chord names to MIDI note
              lists.  When a list is given earlier dicts take priority;
              later dicts only fill in keys not already present.
    sections — list of dicts:
        { 'pattern': [('chord', beats), ...],
          'repeats': int,
          'label':   str or None,
          'lyrics':  [(bar, beat_off, text), ...] or None,
          'strum':   strum pattern list }
    """
    if isinstance(chords, (list, tuple)):
        merged = {}
        for d in reversed(chords):
            merged.update(d)
        chords = merged
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
