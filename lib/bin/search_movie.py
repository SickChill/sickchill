#!/usr/bin/python2
# -*- coding: utf-8 -*-
"""
search_movie.py

Usage: search_movie "movie title"

Search for the given title and print the results.
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
    print('  %s "movie title"' % sys.argv[0])
    sys.exit(2)

title = sys.argv[1]


i = imdb.IMDb()

out_encoding = sys.stdout.encoding or sys.getdefaultencoding()

try:
    # Do the search, and get the results (a list of Movie objects).
    results = i.search_movie(title)
except imdb.IMDbError as e:
    print("Probably you're not connected to Internet.  Complete error report:")
    print(e)
    sys.exit(3)

# Print the results.
print('    %s result%s for "%s":' % (len(results),
                                     ('', 's')[len(results) != 1],
                                     title))
print('movieID\t: imdbID : title')

# Print the long imdb title for every movie.
for movie in results:
    outp = '%s\t: %s : %s' % (movie.movieID, i.get_imdbID(movie),
                               movie['long imdb title'])
    print(outp)
