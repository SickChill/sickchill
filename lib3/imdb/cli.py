# Copyright 2017 H. Turgut Uyar <uyar@tekir.org>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

"""
This module provides the command line interface for IMDbPY.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import sys
from argparse import ArgumentParser

from imdb import VERSION, IMDb


DEFAULT_RESULT_SIZE = 20


def list_results(items, type_, n=None):
    field = 'title' if type_ == 'movie' else 'name'
    print('  # IMDb id %s' % field)
    print('=== ======= %s' % ('=' * len(field),))
    for i, item in enumerate(items[:n]):
        print('%(index)3d %(imdb_id)7s %(title)s' % {
            'index': i + 1,
            'imdb_id': getattr(item, type_ + 'ID'),
            'title': item['long imdb ' + field]
        })


def search_item(args):
    connection = IMDb()
    n = args.n if args.n is not None else DEFAULT_RESULT_SIZE
    if args.type == 'keyword':
        items = connection.search_keyword(args.key)
        if args.first:
            items = connection.get_keyword(items[0])
            list_results(items, type_='movie', n=n)
        else:
            print('  # keyword')
            print('=== =======')
            for i, keyword in enumerate(items[:n]):
                print('%(index)3d %(kw)s' % {'index': i + 1, 'kw': keyword})
    else:
        if args.type == 'movie':
            items = connection.search_movie(args.key)
        elif args.type == 'person':
            items = connection.search_person(args.key)
        elif args.type == 'character':
            items = connection.search_character(args.key)
        elif args.type == 'company':
            items = connection.search_company(args.key)

        if args.first:
            connection.update(items[0])
            print(items[0].summary())
        else:
            list_results(items, type_=args.type, n=args.n)


def get_item(args):
    connection = IMDb()
    if args.type == 'keyword':
        n = args.n if args.n is not None else DEFAULT_RESULT_SIZE
        items = connection.get_keyword(args.key, results=n)
        list_results(items, type_='movie')
    else:
        if args.type == 'movie':
            item = connection.get_movie(args.key)
        elif args.type == 'person':
            item = connection.get_person(args.key)
        elif args.type == 'character':
            item = connection.get_character(args.key)
        elif args.type == 'company':
            item = connection.get_company(args.key)
        print(item.summary())


def list_ranking(items, n=None):
    print('  # rating   votes IMDb id title')
    print('=== ====== ======= ======= =====')
    n = n if n is not None else DEFAULT_RESULT_SIZE
    for i, movie in enumerate(items[:n]):
        print('%(index)3d    %(rating)s %(votes)7s %(imdb_id)7s %(title)s' % {
            'index': i + 1,
            'rating': movie.get('rating'),
            'votes': movie.get('votes'),
            'imdb_id': movie.movieID,
            'title': movie.get('long imdb title')
        })


def get_top_movies(args):
    connection = IMDb()
    items = connection.get_top250_movies()
    if args.first:
        connection.update(items[0])
        print(items[0].summary())
    else:
        list_ranking(items, n=args.n)


def get_bottom_movies(args):
    connection = IMDb()
    items = connection.get_bottom100_movies()
    if args.first:
        connection.update(items[0])
        print(items[0].summary())
    else:
        list_ranking(items, n=args.n)


def make_parser(prog):
    parser = ArgumentParser(prog)
    parser.add_argument('--version', action='version', version='%(prog)s ' + VERSION)

    command_parsers = parser.add_subparsers(metavar='command', dest='command')
    command_parsers.required = True

    command_search_parser = command_parsers.add_parser('search', help='search for items')
    command_search_parser.add_argument('type', help='type of item to search for',
                                       choices=['movie', 'person', 'character', 'company', 'keyword'])
    command_search_parser.add_argument('key', help='title or name of item to search for')
    command_search_parser.add_argument('-n', type=int, help='number of items to list')
    command_search_parser.add_argument('--first', action='store_true', help='display only the first result')
    command_search_parser.set_defaults(func=search_item)

    command_get_parser = command_parsers.add_parser('get', help='retrieve information about an item')
    command_get_parser.add_argument('type', help='type of item to retrieve',
                                    choices=['movie', 'person', 'character', 'company', 'keyword'])
    command_get_parser.add_argument('key', help='IMDb id (or keyword name) of item to retrieve')
    command_get_parser.add_argument('-n', type=int, help='number of movies to list (only for keywords)')
    command_get_parser.set_defaults(func=get_item)

    command_top_parser = command_parsers.add_parser('top', help='get top ranked movies')
    command_top_parser.add_argument('-n', type=int, help='number of movies to list')
    command_top_parser.add_argument('--first', action='store_true', help='display only the first result')
    command_top_parser.set_defaults(func=get_top_movies)

    command_bottom_parser = command_parsers.add_parser('bottom', help='get bottom ranked movies')
    command_bottom_parser.add_argument('-n', type=int, help='number of movies to list')
    command_bottom_parser.add_argument('--first', action='store_true', help='display only the first result')
    command_bottom_parser.set_defaults(func=get_bottom_movies)

    return parser


def main(argv=None):
    argv = argv if argv is not None else sys.argv
    parser = make_parser(prog='imdbpy')
    arguments = parser.parse_args(argv[1:])
    arguments.func(arguments)


if __name__ == '__main__':
    main()
