# Copyright 2009-2017 Davide Alberani <da@erlug.linux.it>
#                2018 H. Turgut Uyar <uyar@tekir.org>
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
This module provides the classes (and the instances) that are used to parse
the pages for the lists of top 250 and bottom 100 movies.

Pages:

http://www.imdb.com/chart/top

http://www.imdb.com/chart/bottom
"""

from __future__ import absolute_import, division, print_function, unicode_literals

from imdb.utils import analyze_title

from .piculet import Path, Rule, Rules, reducers
from .utils import DOMParserBase, analyze_imdbid


class DOMHTMLTop250Parser(DOMParserBase):
    """A parser for the "top 250 movies" page."""
    ranktext = 'top 250 rank'

    rules = [
        Rule(
            key='chart',
            extractor=Rules(
                foreach='//tbody[@class="lister-list"]/tr',
                rules=[
                    Rule(
                        key='rank',
                        extractor=Path('.//span[@name="rk"]/@data-value',
                                       reduce=reducers.first,
                                       transform=int)
                    ),
                    Rule(
                        key='rating',
                        extractor=Path('.//span[@name="ir"]/@data-value',
                                       reduce=reducers.first,
                                       transform=lambda x: round(float(x), 1))
                    ),
                    Rule(
                        key='movieID',
                        extractor=Path('./td[@class="titleColumn"]/a/@href', reduce=reducers.first)
                    ),
                    Rule(
                        key='title',
                        extractor=Path('./td[@class="titleColumn"]/a/text()')
                    ),
                    Rule(
                        key='year',
                        extractor=Path('./td[@class="titleColumn"]/span/text()')
                    ),
                    Rule(
                        key='votes',
                        extractor=Path('.//span[@name="nv"]/@data-value', reduce=reducers.first,
                                       transform=int)
                    )
                ]
            )
        )
    ]

    def postprocess_data(self, data):
        if (not data) or ('chart' not in data):
            return []

        movies = []
        for entry in data['chart']:
            if ('movieID' not in entry) or ('rank' not in entry) or ('title' not in entry):
                continue

            movie_id = analyze_imdbid(entry['movieID'])
            if movie_id is None:
                continue
            del entry['movieID']

            entry[self.ranktext] = entry['rank']
            del entry['rank']

            title = analyze_title(entry['title'] + ' ' + entry.get('year', ''))
            entry.update(title)

            movies.append((movie_id, entry))
        return movies


class DOMHTMLBottom100Parser(DOMHTMLTop250Parser):
    """A parser for the "bottom 100 movies" page."""
    ranktext = 'bottom 100 rank'


_OBJECTS = {
    'top250_parser': ((DOMHTMLTop250Parser,), None),
    'bottom100_parser': ((DOMHTMLBottom100Parser,), None)
}
