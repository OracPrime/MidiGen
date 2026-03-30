"""MidiGen — entry point.  Run this to generate MIDI files."""

from hurt import generate as generate_hurt
from master_of_puppets import generate as generate_mop

if __name__ == "__main__":
    generate_hurt()
    print()
    generate_mop()