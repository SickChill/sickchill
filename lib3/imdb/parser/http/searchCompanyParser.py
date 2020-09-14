# Copyright 2008-2018 Davide Alberani <da@erlug.linux.it>
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
the results of a search for a given company.

For example, when searching for the name "Columbia Pictures", the parsed page
would be:

http://www.imdb.com/find?q=Columbia+Pictures&s=co
"""

from __future__ import absolute_import, division, print_function, unicode_literals

from imdb.utils import analyze_company_name

from .piculet import Path, Rule, Rules, reducers
from .searchMovieParser import DOMHTMLSearchMovieParser
from .utils import analyze_imdbid


class DOMHTMLSearchCompanyParser(DOMHTMLSearchMovieParser):
    """A parser for the company search page."""

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
                        key='name',
                        extractor=Path('./a/text()')
                    ),
                    Rule(
                        key='notes',
                        extractor=Path('./text()')
                    )
                ],
                transform=lambda x: (
                    analyze_imdbid(x.get('link')),
                    analyze_company_name(x.get('name') + x.get('notes', ''), stripNotes=True)
                )
            )
        )
    ]


_OBJECTS = {
    'search_company_parser': ((DOMHTMLSearchCompanyParser,), {'kind': 'company'})
}
