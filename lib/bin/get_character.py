#!/home/dusted/Envs/ok/bin/python
# -*- coding: utf-8 -*-
"""
get_character.py

Usage: get_character "character_id"

Show some info about the character with the given character_id (e.g. '0000001'
for "Jesse James", using 'http' or 'mobile').
Notice that character_id, using 'sql', are not the same IDs used on the web.
"""

import sys

# Import the IMDbPY package.
try:
    import imdb
except ImportError:
    print('You bad boy!  You need to install the IMDbPY package!')
    sys.exit(1)


if len(sys.argv) != 2:
    print('Only one argument is required:')
    print('  %s "character_id"' % sys.argv[0])
    sys.exit(2)

character_id = sys.argv[1]

i = imdb.IMDb()

try:
    # Get a character object with the data about the character identified by
    # the given character_id.
    character = i.get_character(character_id)
except imdb.IMDbError as e:
    print("Probably you're not connected to Internet.  Complete error report:")
    print(e)
    sys.exit(3)


if not character:
    print(("It seems that there's no character"
           ' with character_id "%s"' % character_id))
    sys.exit(4)

# XXX: this is the easier way to print the main info about a character;
# calling the summary() method of a character object will returns a string
# with the main information about the character.
# Obviously it's not really meaningful if you want to know how
# to access the data stored in a character object, so look below; the
# commented lines show some ways to retrieve information from a
# character object.
print(character.summary())
