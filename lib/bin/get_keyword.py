#!/home/dusted/Envs/ok/bin/python
# -*- coding: utf-8 -*-
"""
get_keyword.py

Usage: get_keyword "keyword"

search for movies tagged with the given keyword and print the results.
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
    print('  %s "keyword"' % sys.argv[0])
    sys.exit(2)

name = sys.argv[1]


i = imdb.IMDb()

try:
    # Do the search, and get the results (a list of movies).
    results = i.get_keyword(name, results=20)
except imdb.IMDbError as e:
    print("Probably you're not connected to Internet.  Complete error report:")
    print(e)
    sys.exit(3)

# Print the results.
print('    %s result%s for "%s":' % (len(results),
                                     ('', 's')[len(results) != 1],
                                     name))
print(' : movie title')

# Print the long imdb title for every movie.
for idx, movie in enumerate(results):
    outp = '%d: %s' % (idx+1, movie['long imdb title'])
    print(outp)
