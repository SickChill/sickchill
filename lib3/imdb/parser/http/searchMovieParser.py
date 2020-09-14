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
the results of a search for a given title.

For example, when searching for the title "the passion", the parsed page
would be:

http://www.imdb.com/find?q=the+passion&s=tt
"""

from __future__ import absolute_import, division, print_function, unicode_literals

from imdb.utils import analyze_title

from .piculet import Path, Rule, Rules, reducers
from .utils import DOMParserBase, analyze_imdbid


class DOMHTMLSearchMovieParser(DOMParserBase):
    """A parser for the title search page."""

    rules = [
        Rule(
            key='data',
            extractor=Rules(
                foreach='//td[@class="result_text"]',
                rules=[
                    Rule(
                        key='link',
                        extractor=Path('./a/@href', reduce=reducers.first)
                    ),
                    Rule(
                        key='info',
                        extractor=Path('.//text()')
                    ),
                    Rule(
                        key='akas',
                        extractor=Path(foreach='./i', path='./text()')
                    ),
                    Rule(
                        key='cover url',
                        extractor=Path('../td[@class="primary_photo"]/a/img/@src')
                    )
                ],
                transform=lambda x: (
                    analyze_imdbid(x.get('link')),
                    analyze_title(x.get('info', '')),
                    x.get('akas'),
                    x.get('cover url')
                )
            )
        )
    ]

    def _init(self):
        self.url = ''
        self.img_type = 'cover url'

    def _reset(self):
        self.url = ''

    def postprocess_data(self, data):
        if 'data' not in data:
            data['data'] = []
        results = getattr(self, 'results', None)
        if results is not None:
            data['data'][:] = data['data'][:results]
        # Horrible hack to support AKAs.
            data['data'] = [x for x in data['data'] if x[0] and x[1]]
        if data and data['data'] and len(data['data'][0]) == 4 and isinstance(data['data'][0], tuple):
            for idx, datum in enumerate(data['data']):
                if not isinstance(datum, tuple):
                    continue
                if not datum[0] and datum[1]:
                    continue
                if datum[2] is not None:
                    akas = [aka[1:-1] for aka in datum[2]]  # remove the quotes
                    datum[1]['akas'] = akas
                if datum[3] is not None:
                    datum[1][self.img_type] = datum[3]
                data['data'][idx] = (datum[0], datum[1])
        return data

    def add_refs(self, data):
        return data


_OBJECTS = {
    'search_movie_parser': ((DOMHTMLSearchMovieParser,), None)
}
