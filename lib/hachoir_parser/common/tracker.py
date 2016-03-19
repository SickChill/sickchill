"""
Shared code for tracker parser.
"""

NOTE_NAME = {}
NOTES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "G#", "A", "A#", "B")
for octave in xrange(10):
    for index, note in enumerate(NOTES):
        NOTE_NAME[octave*12+index] = "{0!s} (octave {1!s})".format(note, octave)

