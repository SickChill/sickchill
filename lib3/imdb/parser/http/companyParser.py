# Copyright 2008-2019 Davide Alberani <da@erlug.linux.it>
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
the IMDb pages on the www.imdb.com server about a company.

For example, for "Columbia Pictures [us]" the referred page would be:

main details
    http://www.imdb.com/company/co0071509/
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import re

from .piculet import Path, Rule, Rules
from .utils import DOMParserBase, analyze_imdbid, build_movie


_re_company_name = re.compile(r'With\s+(.+)\s+\(Sorted by.*', re.I | re.M)


def clean_company_title(title):
    """Extract company name"""
    name = _re_company_name.findall(title or '')
    if name and name[0]:
        return name[0]


class DOMCompanyParser(DOMParserBase):
    """Parser for the main page of a given company.
    The page should be provided as a string, as taken from
    the www.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example::

        cparser = DOMCompanyParser()
        result = cparser.parse(company_html_string)
    """
    _containsObjects = True

    rules = [
        Rule(
            key='name',
            extractor=Path(
                '//h1[@class="header"]/text()',
                transform=lambda x: clean_company_title(x)
            )
        ),
        Rule(
            key='filmography',
            extractor=Rules(
                foreach='//b/a[@name]',
                rules=[
                    Rule(
                        key=Path('./text()', transform=str.lower),
                        extractor=Rules(
                            foreach='../following-sibling::ol[1]/li',
                            rules=[
                                Rule(
                                    key='link',
                                    extractor=Path('./a[1]/@href')
                                ),
                                Rule(
                                    key='title',
                                    extractor=Path('./a[1]/text()')
                                ),
                                Rule(
                                    key='year',
                                    extractor=Path('./text()[1]')
                                )
                            ],
                            transform=lambda x: build_movie(
                                '%s %s' % (x.get('title'), x.get('year').strip()),
                                movieID=analyze_imdbid(x.get('link') or ''),
                                _parsingCompany=True
                            )
                        )
                    )
                ]
            )
        )
    ]

    preprocessors = [
        (re.compile('(<b><a name=)', re.I), r'</p>\1')
    ]

    def postprocess_data(self, data):
        for key in ['name']:
            if (key in data) and isinstance(data[key], dict):
                subdata = data[key]
                del data[key]
                data.update(subdata)
        for key in list(data.keys()):
            new_key = key.replace('company', 'companies')
            new_key = new_key.replace('other', 'miscellaneous')
            new_key = new_key.replace('distributor', 'distributors')
            if new_key != key:
                data[new_key] = data[key]
                del data[key]
        return data


_OBJECTS = {
    'company_main_parser': ((DOMCompanyParser,), None)
}
