from chords import CHORDS
from midi_lib import (
    VERSE_STRUM, CHORUS_STRUM, BRIDGE_STRUM, SPARSE_STRUM,
    build_song,
)

# ---------------------------------------------------------
# Nine Inch Nails — "Hurt"
# ---------------------------------------------------------
TEMPO = 90
SEPARATE_CHORD_TRACK = True

# -- Chord patterns (chord_name, duration in beats) --
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
    (7, 0, "but I re-"),      (7, 2, "member"),      (7, 4, "everything"),
]

CHORUS1_LYRICS = [
    (0, 0, "What have I be-"),  (0, 4, "come"),
    (0, 8, "my sweetest"),      (0, 12, "friend?"),
    (1, 0, "Every-one I"),      (1, 4, "know"),
    (1, 8, "goes a-way"),       (1, 12, "in the end"),
    (2, 0, "And you could"),    (2, 4, "have it"),
    (2, 8, "all"),              (2, 12, "my empire of dirt"),
    (3, 0, "I will let"),       (3, 4, "you"),
    (3, 8, "down"),             (3, 12, "I will make you hurt"),
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
    (0, 0, "What have I be-"),  (0, 4, "come"),
    (0, 8, "my sweetest"),      (0, 12, "friend?"),
    (1, 0, "Every-one I"),      (1, 4, "know"),
    (1, 8, "goes a-way"),       (1, 12, "in the end"),
    (2, 0, "And you could"),    (2, 4, "have it"),
    (2, 8, "all"),              (2, 12, "my empire of dirt"),
    (3, 0, "I will let"),       (3, 4, "you"),
    (3, 8, "down"),             (3, 12, "I will make you hurt"),
]

BRIDGE_LYRICS = [
    (0, 0, "If I could"),     (0, 4, "start a-"),
    (0, 8, "gain"),           (0, 12, "a million"),
    (1, 0, "miles a-"),       (1, 4, "way"),
    (1, 8, "I would"),        (1, 12, "keep myself"),
]

# ---------------------------------------------------------
# SONG STRUCTURE
# ---------------------------------------------------------
SECTIONS = [
    {'pattern': VERSE,  'repeats': 2, 'label': 'Intro',    'strum': SPARSE_STRUM},
    {'pattern': VERSE,  'repeats': 8, 'label': 'Verse 1',  'strum': VERSE_STRUM,  'lyrics': VERSE1_LYRICS},
    {'pattern': CHORUS, 'repeats': 4, 'label': 'Chorus 1', 'strum': CHORUS_STRUM, 'lyrics': CHORUS1_LYRICS},
    {'pattern': VERSE,  'repeats': 8, 'label': 'Verse 2',  'strum': VERSE_STRUM,  'lyrics': VERSE2_LYRICS},
    {'pattern': CHORUS, 'repeats': 4, 'label': 'Chorus 2', 'strum': CHORUS_STRUM, 'lyrics': CHORUS2_LYRICS},
    {'pattern': BRIDGE, 'repeats': 2, 'label': 'Bridge',   'strum': BRIDGE_STRUM, 'lyrics': BRIDGE_LYRICS},
    {'pattern': VERSE,  'repeats': 4, 'label': 'Outro',    'strum': SPARSE_STRUM},
]


def generate():
    build_song(
        chords=CHORDS,
        sections=SECTIONS,
        tempo=TEMPO,
        separate_chord_track=SEPARATE_CHORD_TRACK,
        sequence_file="Hurt_Sequence.mid",
        chords_file="Hurt_Chords.mid",
    )


if __name__ == "__main__":
    generate()
