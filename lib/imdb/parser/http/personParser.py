"""
parser.http.personParser module (imdb package).

This module provides the classes (and the instances), used to parse
the IMDb pages on the akas.imdb.com server about a person.
E.g., for "Mel Gibson" the referred pages would be:
    categorized:    http://akas.imdb.com/name/nm0000154/maindetails
    biography:      http://akas.imdb.com/name/nm0000154/bio
    ...and so on...

Copyright 2004-2013 Davide Alberani <da@erlug.linux.it>
               2008 H. Turgut Uyar <uyar@tekir.org>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
"""

import re
from imdb.Movie import Movie
from imdb.utils import analyze_name, canonicalName, normalizeName, \
                        analyze_title, date_and_notes
from utils import build_movie, DOMParserBase, Attribute, Extractor, \
                        analyze_imdbid


from movieParser import _manageRoles
_reRoles = re.compile(r'(<li>.*? \.\.\.\. )(.*?)(</li>|<br>)',
                        re.I | re.M | re.S)

def build_date(date):
    day = date.get('day')
    year = date.get('year')
    if day and year:
        return "%s %s" % (day, year)
    if day:
        return day
    if year:
        return year
    return ""

class DOMHTMLMaindetailsParser(DOMParserBase):
    """Parser for the "categorized" (maindetails) page of a given person.
    The page should be provided as a string, as taken from
    the akas.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        cparser = DOMHTMLMaindetailsParser()
        result = cparser.parse(categorized_html_string)
    """
    _containsObjects = True
    _name_imdb_index = re.compile(r'\([IVXLCDM]+\)')

    _birth_attrs = [Attribute(key='birth date',
                        path='.//time[@itemprop="birthDate"]/@datetime'),
                    Attribute(key='birth place',
                        path=".//a[starts-with(@href, " \
                                "'/search/name?birth_place=')]/text()")]
    _death_attrs = [Attribute(key='death date',
                        path='.//time[@itemprop="deathDate"]/@datetime'),
                    Attribute(key='death place',
                        path=".//a[starts-with(@href, " \
                                "'/search/name?death_place=')]/text()")]
    _film_attrs = [Attribute(key=None,
                      multi=True,
                      path={
                          'link': "./b/a[1]/@href",
                          'title': "./b/a[1]/text()",
                          'notes': "./b/following-sibling::text()",
                          'year': "./span[@class='year_column']/text()",
                          'status': "./a[@class='in_production']/text()",
                          'rolesNoChar': './/br/following-sibling::text()',
                          'chrRoles': "./a[@imdbpyname]/@imdbpyname",
                          'roleID': "./a[starts-with(@href, '/character/')]/@href"
                          },
                      postprocess=lambda x:
                          build_movie(x.get('title') or u'',
                              year=x.get('year'),
                              movieID=analyze_imdbid(x.get('link') or u''),
                              rolesNoChar=(x.get('rolesNoChar') or u'').strip(),
                              chrRoles=(x.get('chrRoles') or u'').strip(),
                              additionalNotes=x.get('notes'),
                              roleID=(x.get('roleID') or u''),
                              status=x.get('status') or None))]

    extractors = [
            Extractor(label='name',
                        path="//h1[@class='header']",
                        attrs=Attribute(key='name',
                            path=".//text()",
                            postprocess=lambda x: analyze_name(x,
                                                               canonical=1))),
            Extractor(label='name_index',
                        path="//h1[@class='header']/span[1]",
                        attrs=Attribute(key='name_index',
                            path="./text()")),

            Extractor(label='birth info',
                        path="//div[h4='Born:']",
                        attrs=_birth_attrs),

            Extractor(label='death info',
                        path="//div[h4='Died:']",
                        attrs=_death_attrs),

            Extractor(label='headshot',
                        path="//td[@id='img_primary']/div[@class='image']/a",
                        attrs=Attribute(key='headshot',
                            path="./img/@src")),

            Extractor(label='akas',
                        path="//div[h4='Alternate Names:']",
                        attrs=Attribute(key='akas',
                            path="./text()",
                            postprocess=lambda x: x.strip().split('  '))),

            Extractor(label='filmography',
                        group="//div[starts-with(@id, 'filmo-head-')]",
                        group_key="./a[@name]/text()",
                        group_key_normalize=lambda x: x.lower().replace(': ', ' '),
                        path="./following-sibling::div[1]" \
                                "/div[starts-with(@class, 'filmo-row')]",
                        attrs=_film_attrs),

            Extractor(label='indevelopment',
                        path="//div[starts-with(@class,'devitem')]",
                        attrs=Attribute(key='in development',
                            multi=True,
                            path={
                                'link': './a/@href',
                                'title': './a/text()'
                                },
                                postprocess=lambda x:
                                    build_movie(x.get('title') or u'',
                                        movieID=analyze_imdbid(x.get('link') or u''),
                                        roleID=(x.get('roleID') or u'').split('/'),
                                        status=x.get('status') or None)))
            ]

    preprocessors = [('<div class="clear"/> </div>', ''),
            ('<br/>', '<br />'),
            (re.compile(r'(<a href="/character/ch[0-9]{7}")>(.*?)</a>'),
                r'\1 imdbpyname="\2@@">\2</a>')]

    def postprocess_data(self, data):
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
        for key in data.keys():
            if key.startswith('actor '):
                if not data.has_key('actor'):
                    data['actor'] = []
                data['actor'].extend(data[key])
                del data[key]
            if key.startswith('actress '):
                if not data.has_key('actress'):
                    data['actress'] = []
                data['actress'].extend(data[key])
                del data[key]
            if key.startswith('self '):
                if not data.has_key('self'):
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
    the akas.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        bioparser = DOMHTMLBioParser()
        result = bioparser.parse(biography_html_string)
    """
    _defGetRefs = True

    _birth_attrs = [Attribute(key='birth date',
                        path={
                            'day': "./a[starts-with(@href, " \
                                    "'/search/name?birth_monthday=')]/text()",
                            'year': "./a[starts-with(@href, " \
                                    "'/search/name?birth_year=')]/text()"
                            },
                        postprocess=build_date),
                    Attribute(key='birth notes',
                        path="./a[starts-with(@href, " \
                                "'/search/name?birth_place=')]/text()")]
    _death_attrs = [Attribute(key='death date',
                        path={
                            'day': "./a[starts-with(@href, " \
                                    "'/search/name?death_monthday=')]/text()",
                            'year': "./a[starts-with(@href, " \
                                    "'/search/name?death_date=')]/text()"
                            },
                        postprocess=build_date),
                    Attribute(key='death notes',
                        path="./text()",
                        # TODO: check if this slicing is always correct
                        postprocess=lambda x: u''.join(x).strip()[2:])]
    extractors = [
            Extractor(label='headshot',
                        path="//a[@name='headshot']",
                        attrs=Attribute(key='headshot',
                            path="./img/@src")),
            Extractor(label='birth info',
                        path="//table[@id='overviewTable']//td[text()='Date of Birth']/following-sibling::td[1]",
                        attrs=_birth_attrs),
            Extractor(label='death info',
                        path="//table[@id='overviewTable']//td[text()='Date of Death']/following-sibling::td[1]",
                        attrs=_death_attrs),
            Extractor(label='nick names',
                        path="//table[@id='overviewTable']//td[text()='Nickenames']/following-sibling::td[1]",
                        attrs=Attribute(key='nick names',
                            path="./text()",
                            joiner='|',
                            postprocess=lambda x: [n.strip().replace(' (',
                                    '::(', 1) for n in x.split('|')
                                    if n.strip()])),
            Extractor(label='birth name',
                        path="//table[@id='overviewTable']//td[text()='Birth Name']/following-sibling::td[1]",
                        attrs=Attribute(key='birth name',
                            path="./text()",
                            postprocess=lambda x: canonicalName(x.strip()))),
            Extractor(label='height',
                path="//table[@id='overviewTable']//td[text()='Height']/following-sibling::td[1]",
                        attrs=Attribute(key='height',
                            path="./text()",
                            postprocess=lambda x: x.strip())),
            Extractor(label='mini biography',
                        path="//a[@name='mini_bio']/following-sibling::div[1 = count(preceding-sibling::a[1] | ../a[@name='mini_bio'])]",
                        attrs=Attribute(key='mini biography',
                            multi=True,
                            path={
                                'bio': ".//text()",
                                'by': ".//a[@name='ba']//text()"
                                },
                            postprocess=lambda x: "%s::%s" % \
                                ((x.get('bio') or u'').split('- IMDb Mini Biography By:')[0].strip(),
                                (x.get('by') or u'').strip() or u'Anonymous'))),
            Extractor(label='spouse',
                        path="//div[h5='Spouse']/table/tr",
                        attrs=Attribute(key='spouse',
                            multi=True,
                            path={
                                'name': "./td[1]//text()",
                                'info': "./td[2]//text()"
                                },
                            postprocess=lambda x: ("%s::%s" % \
                                (x.get('name').strip(),
                                (x.get('info') or u'').strip())).strip(':'))),
            Extractor(label='trade mark',
                        path="//div[h5='Trade Mark']/p",
                        attrs=Attribute(key='trade mark',
                            multi=True,
                            path=".//text()",
                            postprocess=lambda x: x.strip())),
            Extractor(label='trivia',
                        path="//div[h5='Trivia']/p",
                        attrs=Attribute(key='trivia',
                            multi=True,
                            path=".//text()",
                            postprocess=lambda x: x.strip())),
            Extractor(label='quotes',
                        path="//div[h5='Personal Quotes']/p",
                        attrs=Attribute(key='quotes',
                            multi=True,
                            path=".//text()",
                            postprocess=lambda x: x.strip())),
            Extractor(label='salary',
                        path="//div[h5='Salary']/table/tr",
                        attrs=Attribute(key='salary history',
                            multi=True,
                            path={
                                'title': "./td[1]//text()",
                                'info': "./td[2]/text()",
                                },
                            postprocess=lambda x: "%s::%s" % \
                                    (x.get('title').strip(),
                                        x.get('info').strip()))),
            Extractor(label='where now',
                        path="//div[h5='Where Are They Now']/p",
                        attrs=Attribute(key='where now',
                            multi=True,
                            path=".//text()",
                            postprocess=lambda x: x.strip())),
            ]

    preprocessors = [
        (re.compile('(<h5>)', re.I), r'</div><div class="_imdbpy">\1'),
        (re.compile('(</table>\n</div>\s+)</div>', re.I + re.DOTALL), r'\1'),
        (re.compile('(<div id="tn15bot">)'), r'</div>\1'),
        (re.compile('\.<br><br>([^\s])', re.I), r'. \1')
        ]

    def postprocess_data(self, data):
        for what in 'birth date', 'death date':
            if what in data and not data[what]:
                del data[what]
        return data


class DOMHTMLResumeParser(DOMParserBase):
    """Parser for the "resume" page of a given person.
    The page should be provided as a string, as taken from
    the akas.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        resumeparser = DOMHTMLResumeParser()
        result = resumeparser.parse(resume_html_string)
    """
    _defGetRefs = True

    extractors = [
            Extractor(label='info',
                        group="//div[@class='section_box']",
                        group_key="./h3/text()",
                        group_key_normalize=lambda x: x.lower().replace(' ', '_'),
                        path="./ul[@class='resume_section_multi_list']//li",
                        attrs=Attribute(key=None,
                            multi=True,
                            path={
                                'title': ".//b//text()",
                                'desc': ".//text()",
                                },
                            postprocess=lambda x: (x.get('title'), x.get('desc').strip().replace('\n', ' ')))),
            Extractor(label='other_info',
                        group="//div[@class='section_box']",
                        group_key="./h3/text()",
                        group_key_normalize=lambda x: x.lower().replace(' ', '_'),
                        path="./ul[@class='_imdbpy']//li",
                        attrs=Attribute(key=None,
                            multi=True,
                            path=".//text()",
                            postprocess=lambda x: x.strip().replace('\n', ' '))),
            Extractor(label='credits',
                        group="//div[@class='section_box']",
                        group_key="./h3/text()",
                        group_key_normalize=lambda x: x.lower().replace(' ', '_'),
                        path="./table[@class='credits']//tr",
                        attrs=Attribute(key=None,
                            multi=True,
                            path={
                                '0':".//td[1]//text()",
                                '1':".//td[2]//text()",
                                '2':".//td[3]//text()",
                            },
                            postprocess=lambda x: [x.get('0'),x.get('1'),x.get('2')])),
            Extractor(label='mini_info',
                        path="//div[@class='center']",
                        attrs=Attribute(key='mini_info',
                            path=".//text()",
                            postprocess=lambda x: x.strip().replace('\n', ' '))),
            Extractor(label='name',
                        path="//div[@class='center']/h1[@id='preview_user_name']",
                        attrs=Attribute(key='name',
                            path=".//text()",
                            postprocess=lambda x: x.strip().replace('\n', ' '))),
            Extractor(label='resume_bio',
                        path="//div[@id='resume_rendered_html']//p",
                        attrs=Attribute(key='resume_bio',
                            multi=True,
                            path=".//text()")),

            ]

    preprocessors = [
        (re.compile('(<ul>)', re.I), r'<ul class="_imdbpy">\1'),
        ]

    def postprocess_data(self, data):

        for key in data.keys():
            if data[key] == '':
                del data[key]
            if key in ('mini_info', 'name', 'resume_bio'):
                if key == 'resume_bio':
                    data[key] = "".join(data[key]).strip()
                continue
            if len(data[key][0]) == 3:
                for item in data[key]:
                    item[:] = [x for x in item if not x == None]
                continue

            if len(data[key][0]) == 2:
                new_key = {}
                for item in data[key]:
                    if item[0] == None:
                        continue
                    if ':' in item[0]:
                        if item[1].replace(item[0], '')[1:].strip() == '':
                            continue
                        new_key[item[0].strip().replace(':', '')] = item[1].replace(item[0], '')[1:].strip()
                    else:
                        new_key[item[0]] = item[1]
                data[key] = new_key

        new_data = {}
        new_data['resume'] = data
        return new_data


class DOMHTMLOtherWorksParser(DOMParserBase):
    """Parser for the "other works" and "agent" pages of a given person.
    The page should be provided as a string, as taken from
    the akas.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        owparser = DOMHTMLOtherWorksParser()
        result = owparser.parse(otherworks_html_string)
    """
    _defGetRefs = True
    kind = 'other works'

    # XXX: looks like the 'agent' page is no more public.
    extractors = [
            Extractor(label='other works',
                        path="//h5[text()='Other works']/" \
                                "following-sibling::div[1]",
                        attrs=Attribute(key='self.kind',
                            path=".//text()",
                            postprocess=lambda x: x.strip().split('\n\n')))
            ]

    preprocessors = [
        (re.compile('(<h5>[^<]+</h5>)', re.I),
            r'</div>\1<div class="_imdbpy">'),
        (re.compile('(</table>\n</div>\s+)</div>', re.I), r'\1'),
        (re.compile('(<div id="tn15bot">)'), r'</div>\1'),
        (re.compile('<br/><br/>', re.I), r'\n\n')
        ]


def _build_episode(link, title, minfo, role, roleA, roleAID):
    """Build an Movie object for a given episode of a series."""
    episode_id = analyze_imdbid(link)
    notes = u''
    minidx = minfo.find(' -')
    # Sometimes, for some unknown reason, the role is left in minfo.
    if minidx != -1:
        slfRole = minfo[minidx+3:].lstrip()
        minfo = minfo[:minidx].rstrip()
        if slfRole.endswith(')'):
            commidx = slfRole.rfind('(')
            if commidx != -1:
                notes = slfRole[commidx:]
                slfRole = slfRole[:commidx]
        if slfRole and role is None and roleA is None:
            role = slfRole
    eps_data = analyze_title(title)
    eps_data['kind'] = u'episode'
    # FIXME: it's wrong for multiple characters (very rare on tv series?).
    if role is None:
        role = roleA # At worse, it's None.
    if role is None:
        roleAID = None
    if roleAID is not None:
        roleAID = analyze_imdbid(roleAID)
    e = Movie(movieID=episode_id, data=eps_data, currentRole=role,
            roleID=roleAID, notes=notes)
    # XXX: are we missing some notes?
    # XXX: does it parse things as "Episode dated 12 May 2005 (12 May 2005)"?
    if minfo.startswith('('):
        pe = minfo.find(')')
        if pe != -1:
            date = minfo[1:pe]
            if date != '????':
                e['original air date'] = date
                if eps_data.get('year', '????') == '????':
                    syear = date.split()[-1]
                    if syear.isdigit():
                        e['year'] = int(syear)
    return e


class DOMHTMLSeriesParser(DOMParserBase):
    """Parser for the "by TV series" page of a given person.
    The page should be provided as a string, as taken from
    the akas.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        sparser = DOMHTMLSeriesParser()
        result = sparser.parse(filmoseries_html_string)
    """
    _containsObjects = True

    extractors = [
            Extractor(label='series',
                        group="//div[@class='filmo']/span[1]",
                        group_key="./a[1]",
                        path="./following-sibling::ol[1]/li/a[1]",
                        attrs=Attribute(key=None,
                            multi=True,
                            path={
                                'link': "./@href",
                                'title': "./text()",
                                'info': "./following-sibling::text()",
                                'role': "./following-sibling::i[1]/text()",
                                'roleA': "./following-sibling::a[1]/text()",
                                'roleAID': "./following-sibling::a[1]/@href"
                                },
                            postprocess=lambda x: _build_episode(x.get('link'),
                                x.get('title'),
                                (x.get('info') or u'').strip(),
                                x.get('role'),
                                x.get('roleA'),
                                x.get('roleAID'))))
            ]

    def postprocess_data(self, data):
        if len(data) == 0:
            return {}
        nd = {}
        for key in data.keys():
            dom = self.get_dom(key)
            link = self.xpath(dom, "//a/@href")[0]
            title = self.xpath(dom, "//a/text()")[0][1:-1]
            series = Movie(movieID=analyze_imdbid(link),
                           data=analyze_title(title),
                           accessSystem=self._as, modFunct=self._modFunct)
            nd[series] = []
            for episode in data[key]:
                # XXX: should we create a copy of 'series', to avoid
                #      circular references?
                episode['episode of'] = series
                nd[series].append(episode)
        return {'episodes': nd}


class DOMHTMLPersonGenresParser(DOMParserBase):
    """Parser for the "by genre" and "by keywords" pages of a given person.
    The page should be provided as a string, as taken from
    the akas.imdb.com server.  The final result will be a
    dictionary, with a key for every relevant section.

    Example:
        gparser = DOMHTMLPersonGenresParser()
        result = gparser.parse(bygenre_html_string)
    """
    kind = 'genres'
    _containsObjects = True

    extractors = [
            Extractor(label='genres',
                        group="//b/a[@name]/following-sibling::a[1]",
                        group_key="./text()",
                        group_key_normalize=lambda x: x.lower(),
                        path="../../following-sibling::ol[1]/li//a[1]",
                        attrs=Attribute(key=None,
                            multi=True,
                            path={
                                'link': "./@href",
                                'title': "./text()",
                                'info': "./following-sibling::text()"
                                },
                            postprocess=lambda x: \
                                    build_movie(x.get('title') + \
                                    x.get('info').split('[')[0],
                                    analyze_imdbid(x.get('link')))))
            ]

    def postprocess_data(self, data):
        if len(data) == 0:
            return {}
        return {self.kind: data}


from movieParser import DOMHTMLTechParser
from movieParser import DOMHTMLOfficialsitesParser
from movieParser import DOMHTMLAwardsParser
from movieParser import DOMHTMLNewsParser


_OBJECTS = {
    'maindetails_parser': ((DOMHTMLMaindetailsParser,), None),
    'bio_parser': ((DOMHTMLBioParser,), None),
    'resume_parser': ((DOMHTMLResumeParser,), None),
    'otherworks_parser': ((DOMHTMLOtherWorksParser,), None),
    #'agent_parser': ((DOMHTMLOtherWorksParser,), {'kind': 'agent'}),
    'person_officialsites_parser': ((DOMHTMLOfficialsitesParser,), None),
    'person_awards_parser': ((DOMHTMLAwardsParser,), {'subject': 'name'}),
    'publicity_parser': ((DOMHTMLTechParser,), {'kind': 'publicity'}),
    'person_series_parser': ((DOMHTMLSeriesParser,), None),
    'person_contacts_parser': ((DOMHTMLTechParser,), {'kind': 'contacts'}),
    'person_genres_parser': ((DOMHTMLPersonGenresParser,), None),
    'person_keywords_parser': ((DOMHTMLPersonGenresParser,),
                                {'kind': 'keywords'}),
    'news_parser': ((DOMHTMLNewsParser,), None),
}

