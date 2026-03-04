from midiutil import MIDIFile

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
# SONG STRUCTURE MAPPING
# ---------------------------------------------------------
current_beat = 0

def play_verse(num_times):
    global current_beat
    for _ in range(num_times):
        # Bar 1: Bm for 4 beats
        add_chord(MyMIDI, 'Bm', current_beat, 4)
        current_beat += 4
        # Bar 2: Esus2 (2 beats) -> Bm (2 beats)
        add_chord(MyMIDI, 'Esus2', current_beat, 2)
        add_chord(MyMIDI, 'Bm', current_beat + 2, 2)
        current_beat += 4
        # Bar 3: Bm for 4 beats
        add_chord(MyMIDI, 'Bm', current_beat, 4)
        current_beat += 4
        # Bar 4: Esus2 (2 beats) -> Bm (2 beats)
        add_chord(MyMIDI, 'Esus2', current_beat, 2)
        add_chord(MyMIDI, 'Bm', current_beat + 2, 2)
        current_beat += 4

def play_chorus(num_times):
    global current_beat
    for _ in range(num_times):
        # Bm (4) -> G (4) -> D (4) -> A (4)
        for c in ['Bm', 'G', 'D', 'A']:
            add_chord(MyMIDI, c, current_beat, 4)
            current_beat += 4

# BUILD THE SONG
play_verse(2)   # Intro
play_verse(4)   # Verse 1
play_chorus(2)  # Chorus 1
play_verse(4)   # Verse 2
play_chorus(4)  # Chorus 2 & Outro

# Save the file
with open("Hurt_Sequence.mid", "wb") as output_file:
    MyMIDI.writeFile(output_file)

print("MIDI file 'Hurt_Sequence.mid' generated successfully!")