import random

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
# Each entry: (beat_offset, direction, velocity_scale, is_muted)

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
