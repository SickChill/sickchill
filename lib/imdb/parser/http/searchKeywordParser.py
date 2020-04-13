# Copyright 2009-2018 Davide Alberani <da@erlug.linux.it>
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
the results of a search for a given keyword.

For example, when searching for the keyword "alabama", the parsed page
would be:

http://www.imdb.com/find?q=alabama&s=kw
"""

from __future__ import absolute_import, division, print_function, unicode_literals

from imdb.utils import analyze_title

from .piculet import Path, Rule, Rules, reducers
from .searchMovieParser import DOMHTMLSearchMovieParser
from .utils import analyze_imdbid


class DOMHTMLSearchKeywordParser(DOMHTMLSearchMovieParser):
    """A parser for the keyword search page."""

    rules = [
        Rule(
            key='data',
            extractor=Path(
                foreach='//td[@class="result_text"]',
                path='./a/text()'
            )
        )
    ]


def custom_analyze_title4kwd(title, yearNote, outline):
    """Return a dictionary with the needed info."""
    title = title.strip()
    if not title:
        return {}
    if yearNote:
        yearNote = '%s)' % yearNote.split(' ')[0]
        title = title + ' ' + yearNote
    retDict = analyze_title(title)
    if outline:
        retDict['plot outline'] = outline
    return retDict


class DOMHTMLSearchMovieKeywordParser(DOMHTMLSearchMovieParser):
    """A parser for the movie search by keyword page."""

    rules = [
        Rule(
            key='data',
            extractor=Rules(
                foreach='//h3[@class="lister-item-header"]',
                rules=[
                    Rule(
                        key='link',
                        extractor=Path('./a/@href', reduce=reducers.first)
                    ),
                    Rule(
                        key='info',
                        extractor=Path('./a//text()')
                    ),
                    Rule(
                        key='ynote',
                        extractor=Path('./span[@class="lister-item-year text-muted unbold"]/text()')
                    ),
                    Rule(
                        key='outline',
                        extractor=Path('./span[@class="outline"]//text()')
                    )
                ],
                transform=lambda x: (
                    analyze_imdbid(x.get('link')),
                    custom_analyze_title4kwd(
                        x.get('info', ''),
                        x.get('ynote', ''),
                        x.get('outline', '')
                    )
                )
            )
        )
    ]

    def preprocess_string(self, html_string):
        return html_string.replace(' + >', '>')


_OBJECTS = {
    'search_keyword_parser': ((DOMHTMLSearchKeywordParser,), {'kind': 'keyword'}),
    'search_moviekeyword_parser': ((DOMHTMLSearchMovieKeywordParser,), None)
}
