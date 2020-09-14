# Copyright 2004-2018 Davide Alberani <da@erlug.linux.it>
#           2008-2018 H. Turgut Uyar <uyar@tekir.org>
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
the the contents of a list.

For example, when you want to parse the list "Golden Globes 2020: Trending Titles" 
the corresponding url would be:

https://www.imdb.com/list/ls091843609/
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import string

from imdb.utils import analyze_title

from .piculet import Path, Rule, Rules, reducers
from .utils import DOMParserBase, analyze_imdbid

non_numeric_chars = ''.join(set(string.printable) - set(string.digits))

class DOMHTMLListParser(DOMParserBase):
    """A parser for the title search page."""

    rules = [
        Rule(
            key='chart',
            extractor=Rules(
                foreach='//div[@class="lister-item mode-detail"]',
                rules=[
                    Rule(
                        key='link',
                        extractor=Path('.//h3[@class="lister-item-header"]/a/@href')
                    ),
                    Rule(
                        key='rank',
                        extractor=Path('.//span[@class="lister-item-index unbold text-primary"]/text()',
                                       reduce=reducers.first,
                                       transform=lambda x: int(''.join(i for i in x if i.isdigit())))
                    ),
                    Rule(
                        key='rating',
                        extractor=Path('.//span[@class="ipl-rating-star__rating"]/text()',
                                       reduce=reducers.first,
                                       transform=lambda x: round(float(x), 1))
                    ),
                    Rule(
                        key='movieID',
                        extractor=Path('.//h3[@class="lister-item-header"]/a/@href')
                    ),
                    Rule(
                        key='title',
                        extractor=Path('.//h3[@class="lister-item-header"]/a/text()')
                    ),
                    Rule(
                        key='year',
                        extractor=Path('.//span[@class="lister-item-year text-muted unbold"]/text()', 
                                        transform=lambda x: int(''.join(i for i in x if i.isdigit())[:4]) )
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

            movie_id = analyze_imdbid(entry['movieID']) # actually url parser to filter out id
            if movie_id is None:
                continue
            del entry['movieID']

            title = analyze_title(entry['title'])
            entry.update(title)

            movies.append((movie_id, entry))
        return movies

_OBJECTS = {
    'list_parser': ((DOMHTMLListParser,), None)
}
