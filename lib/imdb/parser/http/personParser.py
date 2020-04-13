# Copyright 2004-2019 Davide Alberani <da@erlug.linux.it>
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
the IMDb pages on the www.imdb.com server about a person.

For example, for "Mel Gibson" the referred pages would be:

categorized
    http://www.imdb.com/name/nm0000154/maindetails

biography
    http://www.imdb.com/name/nm0000154/bio

...and so on.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import re

from imdb.utils import analyze_name

from .movieParser import (
    DOMHTMLAwardsParser,
    DOMHTMLNewsParser,
    DOMHTMLOfficialsitesParser,
    DOMHTMLTechParser
)
from .piculet import Path, Rule, Rules, transformers
from .utils import DOMParserBase, analyze_imdbid, build_movie


_re_spaces = re.compile(r'\s+')
_reRoles = re.compile(r'(<li>.*? \.\.\.\. )(.*?)(</li>|<br>)', re.I | re.M | re.S)


class DOMHTMLMaindetailsParser(DOMParserBase):
    """Parser for the "categorized" (maindetails) page of a given person.
    The page should be provided as a string, as taken from
    the www.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example::

        cparser = DOMHTMLMaindetailsParser()
        result = cparser.parse(categorized_html_string)
    """
    _containsObjects = True
    _name_imdb_index = re.compile(r'\([IVXLCDM]+\)')

    _birth_rules = [
        Rule(
            key='birth date',
            extractor=Path('.//time[@itemprop="birthDate"]/@datetime')
        ),
        Rule(
            key='birth place',
            extractor=Path('.//a[starts-with(@href, "/search/name?birth_place=")]/text()')
        )
    ]

    _death_rules = [
        Rule(
            key='death date',
            extractor=Path('.//time[@itemprop="deathDate"]/@datetime')
        ),
        Rule(
            key='death place',
            extractor=Path('.//a[starts-with(@href, "/search/name?death_place=")]/text()')
        )
    ]

    _film_rules = [
        Rule(
            key='link',
            extractor=Path('./b/a[1]/@href')
        ),
        Rule(
            key='title',
            extractor=Path('./b/a[1]/text()')
        ),
        Rule(
            key='notes',
            extractor=Path('./b/following-sibling::text()')
        ),
        Rule(
            key='year',
            extractor=Path('./span[@class="year_column"]/text()')
        ),
        Rule(
            key='status',
            extractor=Path('./a[@class="in_production"]/text()')
        ),
        Rule(
            key='rolesNoChar',
            extractor=Path('.//br/following-sibling::text()')
        ),
        Rule(
            key='chrRoles',
            extractor=Path('./a[@imdbpyname]/@imdbpyname')
        )
    ]

    rules = [
        Rule(
            key='name',
            extractor=Path(
                '//h1[@class="header"]//text()',
                transform=lambda x: analyze_name(x)
            )
        ),
        Rule(
            key='name_index',
            extractor=Path('//h1[@class="header"]/span[1]/text()')
        ),
        Rule(
            key='birth info',
            extractor=Rules(
                section='//div[h4="Born:"]',
                rules=_birth_rules
            )
        ),
        Rule(
            key='death info',
            extractor=Rules(
                section='//div[h4="Died:"]',
                rules=_death_rules,
            )
        ),
        Rule(
            key='headshot',
            extractor=Path('//td[@id="img_primary"]//div[@class="image"]/a/img/@src')
        ),
        Rule(
            key='akas',
            extractor=Path(
                '//div[h4="Alternate Names:"]/text()',
                transform=lambda x: x.strip().split('  ')
            )
        ),
        Rule(
            key='filmography',
            extractor=Rules(
                foreach='//div[starts-with(@id, "filmo-head-")]',
                rules=[
                    Rule(
                        key=Path(
                            './a[@name]/text()',
                            transform=lambda x: x.lower().replace(': ', ' ')
                        ),
                        extractor=Rules(
                            foreach='./following-sibling::div[1]/div[starts-with(@class, "filmo-row")]',
                            rules=_film_rules,
                            transform=lambda x: build_movie(
                                x.get('title') or '',
                                year=x.get('year'),
                                movieID=analyze_imdbid(x.get('link') or ''),
                                rolesNoChar=(x.get('rolesNoChar') or '').strip(),
                                chrRoles=(x.get('chrRoles') or '').strip(),
                                additionalNotes=x.get('notes'),
                                status=x.get('status') or None
                            )
                        )
                    )
                ]
            )
        ),
        Rule(
            key='in development',
            extractor=Rules(
                foreach='//div[starts-with(@class,"devitem")]',
                rules=[
                    Rule(
                        key='link',
                        extractor=Path('./a/@href')
                    ),
                    Rule(
                        key='title',
                        extractor=Path('./a/text()')
                    )
                ],
                transform=lambda x: build_movie(
                    x.get('title') or '',
                    movieID=analyze_imdbid(x.get('link') or ''),
                    roleID=(x.get('roleID') or '').split('/'),
                    status=x.get('status') or None
                )
            )
        )
    ]

    preprocessors = [
        ('<div class="clear"/> </div>', ''), ('<br/>', '<br />')
    ]

    def postprocess_data(self, data):
        for key in ['name']:
            if (key in data) and isinstance(data[key], dict):
                subdata = data[key]
                del data[key]
                data.update(subdata)
        for what in 'birth date', 'death date':
            if what in data and not data[what]:
                del data[what]
        name_index = (data.get('name_index') or '').strip()
        if name_index:
            if self._name_imdb_index.match(name_index):
                data['imdbIndex'] = name_index[1:-1]
            del data['name_index']
        # XXX: the code below is for backwards compatibility
        # probably could be removed
        for key in list(data.keys()):
            if key.startswith('actor '):
                if 'actor' not in data:
                    data['actor'] = []
                data['actor'].extend(data[key])
                del data[key]
            if key.startswith('actress '):
                if 'actress' not in data:
                    data['actress'] = []
                data['actress'].extend(data[key])
                del data[key]
            if key.startswith('self '):
                if 'self' not in data:
                    data['self'] = []
                data['self'].extend(data[key])
                del data[key]
            if key == 'birth place':
                data['birth notes'] = data[key]
                del data[key]
            if key == 'death place':
                data['death notes'] = data[key]
                del data[key]
        return data


class DOMHTMLBioParser(DOMParserBase):
    """Parser for the "biography" page of a given person.
    The page should be provided as a string, as taken from
    the www.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example::

        bioparser = DOMHTMLBioParser()
        result = bioparser.parse(biography_html_string)
    """
    _defGetRefs = True

    _birth_rules = [
        Rule(
            key='birth date',
            extractor=Path(
                './time/@datetime',
                transform=lambda s: '%4d-%02d-%02d' % tuple(map(int, s.split('-')))
            )
        ),
        Rule(
            key='birth notes',
            extractor=Path('./a[starts-with(@href, "/search/name?birth_place=")]/text()')
        )
    ]

    _death_rules = [
        Rule(
            key='death date',
            extractor=Path(
                './time/@datetime',
                transform=lambda s: '%4d-%02d-%02d' % tuple(map(int, s.split('-')))
            )
        ),
        Rule(
            key='death cause',
            extractor=Path(
                './text()',
                transform=lambda x: ''.join(x).strip()[2:].lstrip()
            )
        ),
        Rule(
            key='death notes',
            extractor=Path(
                '..//text()',
                transform=lambda x: _re_spaces.sub(' ', (x or '').strip().split('\n')[-1])
            )
        )
    ]

    rules = [
        Rule(
            key='headshot',
            extractor=Path('//img[@class="poster"]/@src')
        ),
        Rule(
            key='birth info',
            extractor=Rules(
                section='//table[@id="overviewTable"]'
                        '//td[text()="Born"]/following-sibling::td[1]',
                rules=_birth_rules
            )
        ),
        Rule(
            key='death info',
            extractor=Rules(
                section='//table[@id="overviewTable"]'
                        '//td[text()="Died"]/following-sibling::td[1]',
                rules=_death_rules
            )
        ),
        Rule(
            key='nick names',
            extractor=Path(
                '//table[@id="overviewTable"]'
                '//td[starts-with(text(), "Nickname")]/following-sibling::td[1]/text()',
                reduce=lambda xs: '|'.join(xs),
                transform=lambda x: [
                    n.strip().replace(' (', '::(', 1)
                    for n in x.split('|') if n.strip()
                ]
            )
        ),
        Rule(
            key='birth name',
            extractor=Path(
                '//table[@id="overviewTable"]'
                '//td[text()="Birth Name"]/following-sibling::td[1]/text()',
                transform=lambda x: x.strip()
            )
        ),
        Rule(
            key='height',
            extractor=Path(
                '//table[@id="overviewTable"]'
                '//td[text()="Height"]/following-sibling::td[1]/text()',
                transform=transformers.strip
            )
        ),
        Rule(
            key='mini biography',
            extractor=Rules(
                foreach='//h4[starts-with(text(), "Mini Bio")]/following-sibling::div',
                rules=[
                    Rule(
                        key='bio',
                        extractor=Path('.//text()')
                    ),
                    Rule(
                        key='by',
                        extractor=Path('.//a[@name="ba"]//text()')
                    )
                ],
                transform=lambda x: "%s::%s" % (
                    (x.get('bio') or '').split('- IMDb Mini Biography By:')[0].strip(),
                    (x.get('by') or '').strip() or 'Anonymous'
                )
            )
        ),
        Rule(
            key='spouse',
            extractor=Rules(
                foreach='//a[@name="spouse"]/following::table[1]//tr',
                rules=[
                    Rule(
                        key='name',
                        extractor=Path('./td[1]//text()')
                    ),
                    Rule(
                        key='info',
                        extractor=Path('./td[2]//text()')
                    )
                ],
                transform=lambda x: ("%s::%s" % (
                    x.get('name').strip(),
                    (_re_spaces.sub(' ', x.get('info') or '')).strip())).strip(':')
            )
        ),
        Rule(
            key='trade mark',
            extractor=Path(
                foreach='//div[@class="_imdbpyh4"]/h4[starts-with(text(), "Trade Mark")]'
                        '/.././div[contains(@class, "soda")]',
                path='.//text()',
                transform=transformers.strip
            )
        ),
        Rule(
            key='trivia',
            extractor=Path(
                foreach='//div[@class="_imdbpyh4"]/h4[starts-with(text(), "Trivia")]'
                        '/.././div[contains(@class, "soda")]',
                path='.//text()',
                transform=transformers.strip
            )
        ),
        Rule(
            key='quotes',
            extractor=Path(
                foreach='//div[@class="_imdbpyh4"]/h4[starts-with(text(), "Personal Quotes")]'
                        '/.././div[contains(@class, "soda")]',
                path='.//text()',
                transform=transformers.strip
            )
        ),
        Rule(
            key='salary history',
            extractor=Rules(
                foreach='//a[@name="salary"]/following::table[1]//tr',
                rules=[
                    Rule(
                        key='title',
                        extractor=Path('./td[1]//text()')
                    ),
                    Rule(
                        key='info',
                        extractor=Path('./td[2]//text()')
                    )
                ],
                transform=lambda x: "%s::%s" % (
                    x.get('title').strip(),
                    _re_spaces.sub(' ', (x.get('info') or '')).strip())
            )
        )
    ]

    preprocessors = [
        (re.compile('(<h5>)', re.I), r'</div><div class="_imdbpy">\1'),
        (re.compile('(<h4)', re.I), r'</div><div class="_imdbpyh4">\1'),
        (re.compile('(</table>\n</div>\s+)</div>', re.I + re.DOTALL), r'\1'),
        (re.compile('(<div id="tn15bot">)'), r'</div>\1'),
        (re.compile('\.<br><br>([^\s])', re.I), r'. \1')
    ]

    def postprocess_data(self, data):
        for key in ['birth info', 'death info']:
            if key in data and isinstance(data[key], dict):
                subdata = data[key]
                del data[key]
                data.update(subdata)
        for what in 'birth date', 'death date', 'death cause':
            if what in data and not data[what]:
                del data[what]
        return data


class DOMHTMLOtherWorksParser(DOMParserBase):
    """Parser for the "other works" page of a given person.
    The page should be provided as a string, as taken from
    the www.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example::

        owparser = DOMHTMLOtherWorksParser()
        result = owparser.parse(otherworks_html_string)
    """
    _defGetRefs = True

    rules = [
        Rule(
            key='other works',
            extractor=Path(
                foreach='//li[@class="ipl-zebra-list__item"]',
                path='.//text()',
                transform=transformers.strip
            )
        )
    ]


class DOMHTMLPersonGenresParser(DOMParserBase):
    """Parser for the "by genre" and "by keywords" pages of a given person.
    The page should be provided as a string, as taken from
    the www.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example::

        gparser = DOMHTMLPersonGenresParser()
        result = gparser.parse(bygenre_html_string)
    """
    kind = 'genres'
    _containsObjects = True

    rules = [
        Rule(
            key='genres',
            extractor=Rules(
                foreach='//b/a[@name]/following-sibling::a[1]',
                rules=[
                    Rule(
                        key=Path('./text()', transform=str.lower),
                        extractor=Rules(
                            foreach='../../following-sibling::ol[1]/li//a[1]',
                            rules=[
                                Rule(
                                    key='link',
                                    extractor=Path('./@href')
                                ),
                                Rule(
                                    key='title',
                                    extractor=Path('./text()')
                                ),
                                Rule(
                                    key='info',
                                    extractor=Path('./following-sibling::text()')
                                )
                            ],
                            transform=lambda x: build_movie(
                                x.get('title') + x.get('info').split('[')[0],
                                analyze_imdbid(x.get('link')))
                        )
                    )
                ]
            )
        )
    ]

    def postprocess_data(self, data):
        if len(data) == 0:
            return {}
        return {self.kind: data}


_OBJECTS = {
    'maindetails_parser': ((DOMHTMLMaindetailsParser,), None),
    'bio_parser': ((DOMHTMLBioParser,), None),
    'otherworks_parser': ((DOMHTMLOtherWorksParser,), None),
    'person_officialsites_parser': ((DOMHTMLOfficialsitesParser,), None),
    'person_awards_parser': ((DOMHTMLAwardsParser,), {'subject': 'name'}),
    'publicity_parser': ((DOMHTMLTechParser,), {'kind': 'publicity'}),
    'person_contacts_parser': ((DOMHTMLTechParser,), {'kind': 'contacts'}),
    'person_genres_parser': ((DOMHTMLPersonGenresParser,), None),
    'person_keywords_parser': ((DOMHTMLPersonGenresParser,), {'kind': 'keywords'}),
    'news_parser': ((DOMHTMLNewsParser,), None),
}
