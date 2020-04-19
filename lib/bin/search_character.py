#!/home/dusted/Envs/ok/bin/python
# -*- coding: utf-8 -*-
"""
search_character.py

Usage: search_character "character name"

Search for the given name and print the results.
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
    print('  %s "character name"' % sys.argv[0])
    sys.exit(2)

name = sys.argv[1]


i = imdb.IMDb()

out_encoding = sys.stdout.encoding or sys.getdefaultencoding()

try:
    # Do the search, and get the results (a list of character objects).
    results = i.search_character(name)
except imdb.IMDbError as e:
    print("Probably you're not connected to Internet.  Complete error report:")
    print(e)
    sys.exit(3)

# Print the results.
print('    %s result%s for "%s":' % (len(results),
                                     ('', 's')[len(results) != 1],
                                     name))
print('characterID\t: imdbID : name')

# Print the long imdb name for every character.
for character in results:
    outp = '%s\t\t: %s : %s' % (character.characterID,
                                 i.get_imdbID(character),
                                 character['long imdb name'])
    print(outp)
