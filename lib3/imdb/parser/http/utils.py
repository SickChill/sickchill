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
This module provides miscellaneous utilities used by the components
in the :mod:`imdb.parser.http` package.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import re

from imdb import PY2
from imdb.Character import Character
from imdb.Movie import Movie
from imdb.Person import Person
from imdb.utils import _Container, flatten
from imdb.parser.http.logging import logger

from .piculet import _USE_LXML, ElementTree, Rules, build_tree, html_to_xhtml
from .piculet import xpath as piculet_xpath
from .piculet import Rule, Path


if PY2:
    from collections import Callable
else:
    from collections.abc import Callable


# Year, imdbIndex and kind.
re_yearKind_index = re.compile(
    r'(\([0-9\?]{4}(?:/[IVXLCDM]+)?\)(?: \(mini\)| \(TV\)| \(V\)| \(VG\))?)'
)

# Match imdb ids in href tags
re_imdbid = re.compile(r'(title/tt|name/nm|company/co|user/ur)([0-9]+)')


def analyze_imdbid(href):
    """Return an imdbID from an URL."""
    if not href:
        return None
    match = re_imdbid.search(href)
    if not match:
        return None
    return str(match.group(2))


_modify_keys = list(Movie.keys_tomodify_list) + list(Person.keys_tomodify_list)


def _putRefs(d, re_titles, re_names, lastKey=None):
    """Iterate over the strings inside list items or dictionary values,
    substitutes movie titles and person names with the (qv) references."""
    if isinstance(d, list):
        for i in range(len(d)):
            if isinstance(d[i], str):
                if lastKey in _modify_keys:
                    if re_names:
                        d[i] = re_names.sub(r"'\1' (qv)", d[i])
                    if re_titles:
                        d[i] = re_titles.sub(r'_\1_ (qv)', d[i])
            elif isinstance(d[i], (list, dict)):
                _putRefs(d[i], re_titles, re_names, lastKey=lastKey)
    elif isinstance(d, dict):
        for k, v in list(d.items()):
            lastKey = k
            if isinstance(v, str):
                if lastKey in _modify_keys:
                    if re_names:
                        d[k] = re_names.sub(r"'\1' (qv)", v)
                    if re_titles:
                        d[k] = re_titles.sub(r'_\1_ (qv)', v)
            elif isinstance(v, (list, dict)):
                _putRefs(d[k], re_titles, re_names, lastKey=lastKey)


_b_p_logger = logger.getChild('build_person')


def build_person(txt, personID=None, billingPos=None,
                 roleID=None, accessSystem='http', modFunct=None, headshot=None):
    """Return a Person instance from the tipical <tr>...</tr> strings
    found in the IMDb's web site."""
    # if personID is None
    #     _b_p_logger.debug('empty name or personID for "%s"', txt)
    notes = ''
    role = ''
    # Search the (optional) separator between name and role/notes.
    if txt.find('....') != -1:
        sep = '....'
    elif txt.find('...') != -1:
        sep = '...'
    else:
        sep = '...'
        # Replace the first parenthesis, assuming there are only notes, after.
        # Rationale: no imdbIndex is (ever?) showed on the web site.
        txt = txt.replace('(', '...(', 1)
    txt_split = txt.split(sep, 1)
    if isinstance(roleID, list):
        roleID = [r for r in roleID if r]
        if not roleID:
            roleID = ['']
    name = txt_split[0].strip()
    if len(txt_split) == 2:
        role_comment = re_spaces.sub(' ', txt_split[1]).strip()
        re_episodes = re.compile(r'(\d+ episodes.*)', re.I | re.M | re.S)
        ep_match = re_episodes.search(role_comment)
        if ep_match and (not ep_match.start() or role_comment[ep_match.start() - 1] != '('):
            role_comment = re_episodes.sub(r'(\1)', role_comment)
        # Strip common endings.
        if role_comment[-4:] == ' and':
            role_comment = role_comment[:-4].rstrip()
        elif role_comment[-2:] == ' &':
            role_comment = role_comment[:-2].rstrip()
        elif role_comment[-6:] == '& ....':
            role_comment = role_comment[:-6].rstrip()
        # Get the notes.
        if roleID is not None:
            if not isinstance(roleID, list):
                cmt_idx = role_comment.find('(')
                if cmt_idx != -1:
                    role = role_comment[:cmt_idx].rstrip()
                    notes = role_comment[cmt_idx:]
                else:
                    # Just a role, without notes.
                    role = role_comment
            else:
                role = role_comment
        else:
            # We're managing something that doesn't have a 'role', so
            # everything are notes.
            notes = role_comment
    if role == '....':
        role = ''
    roleNotes = []
    # Manages multiple roleIDs.
    if isinstance(roleID, list):
        rolesplit = role.split('/')
        role = []
        for r in rolesplit:
            nidx = r.find('(')
            if nidx != -1:
                role.append(r[:nidx].rstrip())
                roleNotes.append(r[nidx:])
            else:
                role.append(r)
                roleNotes.append(None)
        lr = len(role)
        lrid = len(roleID)
        if lr > lrid:
            roleID += [None] * (lrid - lr)
        elif lr < lrid:
            roleID = roleID[:lr]
        for i, rid in enumerate(roleID):
            if rid is not None:
                roleID[i] = str(rid)
        if lr == 1:
            role = role[0]
            roleID = roleID[0]
            notes = roleNotes[0] or ''
    elif roleID is not None:
        roleID = str(roleID)
    if personID is not None:
        personID = str(personID)
    if (not name) or (personID is None):
        # Set to 'debug', since build_person is expected to receive some crap.
        _b_p_logger.debug('empty name or personID for "%s"', txt)
    if role:
        if isinstance(role, list):
            role = [r.strip() for r in role]
        else:
            role = role.strip()
    if notes:
        if isinstance(notes, list):
            notes = [n.strip() for n in notes]
        else:
            notes = notes.strip()
    # XXX: return None if something strange is detected?
    data = {}
    if headshot:
        data['headshot'] = headshot
    person = Person(name=name, personID=personID, currentRole=role,
                    roleID=roleID, notes=notes, billingPos=billingPos,
                    modFunct=modFunct, accessSystem=accessSystem, data=data)
    if roleNotes and len(roleNotes) == len(roleID):
        for idx, role in enumerate(person.currentRole):
            if roleNotes[idx]:
                role.notes = roleNotes[idx]
    elif person.currentRole and isinstance(person.currentRole, Character) and \
            not person.currentRole.notes and notes:
        person.currentRole.notes = notes
    return person


_re_chrIDs = re.compile('[0-9]{7}')

_b_m_logger = logger.getChild('build_movie')

# To shrink spaces.
re_spaces = re.compile(r'\s+')


def build_movie(txt, movieID=None, roleID=None, status=None,
                accessSystem='http', modFunct=None, _parsingCharacter=False,
                _parsingCompany=False, year=None, chrRoles=None,
                rolesNoChar=None, additionalNotes=None):
    """Given a string as normally seen on the "categorized" page of
    a person on the IMDb's web site, returns a Movie instance."""
    # FIXME: Oook, lets face it: build_movie and build_person are now
    # two horrible sets of patches to support the new IMDb design.  They
    # must be rewritten from scratch.
    if _parsingCompany:
        _defSep = ' ... '
    else:
        _defSep = ' .... '
    title = re_spaces.sub(' ', txt).strip()
    # Split the role/notes from the movie title.
    tsplit = title.split(_defSep, 1)
    role = ''
    notes = ''
    roleNotes = []
    if len(tsplit) == 2:
        title = tsplit[0].rstrip()
        role = tsplit[1].lstrip()
    if title[-9:] == 'TV Series':
        title = title[:-9].rstrip()
    # elif title[-7:] == '(short)':
    #     title = title[:-7].rstrip()
    # elif title[-11:] == '(TV series)':
    #     title = title[:-11].rstrip()
    # elif title[-10:] == '(TV movie)':
    #     title = title[:-10].rstrip()
    elif title[-14:] == 'TV mini-series':
        title = title[:-14] + ' (mini)'
    if title and title.endswith(_defSep.rstrip()):
        title = title[:-len(_defSep) + 1]
    # Try to understand where the movie title ends.
    while True:
        if year:
            break
        if title[-1:] != ')':
            # Ignore the silly "TV Series" notice.
            if title[-9:] == 'TV Series':
                title = title[:-9].rstrip()
                continue
            else:
                # Just a title: stop here.
                break
        # Try to match paired parentheses; yes: sometimes there are
        # parentheses inside comments...
        nidx = title.rfind('(')
        while nidx != -1 and title[nidx:].count('(') != title[nidx:].count(')'):
            nidx = title[:nidx].rfind('(')
        # Unbalanced parentheses: stop here.
        if nidx == -1:
            break
        # The last item in parentheses seems to be a year: stop here.
        first4 = title[nidx + 1:nidx + 5]
        if (first4.isdigit() or first4 == '????') and title[nidx + 5:nidx + 6] in (')', '/'):
            break
        # The last item in parentheses is a known kind: stop here.
        if title[nidx + 1:-1] in ('TV', 'V', 'mini', 'VG', 'TV movie', 'TV series', 'short'):
            break
        # Else, in parentheses there are some notes.
        # XXX: should the notes in the role half be kept separated
        #      from the notes in the movie title half?
        if notes:
            notes = '%s %s' % (title[nidx:], notes)
        else:
            notes = title[nidx:]
        title = title[:nidx].rstrip()
    if year:
        year = year.strip()
        if title[-1:] == ')':
            fpIdx = title.rfind('(')
            if fpIdx != -1:
                if notes:
                    notes = '%s %s' % (title[fpIdx:], notes)
                else:
                    notes = title[fpIdx:]
                title = title[:fpIdx].rstrip()
        title = '%s (%s)' % (title, year)
    if not roleID:
        roleID = None
    elif len(roleID) == 1:
        roleID = roleID[0]
    if not role and chrRoles and isinstance(roleID, str):
        roleID = _re_chrIDs.findall(roleID)
        role = ' / '.join([_f for _f in chrRoles.split('@@') if _f])
    # Manages multiple roleIDs.
    if isinstance(roleID, list):
        tmprole = role.split('/')
        role = []
        for r in tmprole:
            nidx = r.find('(')
            if nidx != -1:
                role.append(r[:nidx].rstrip())
                roleNotes.append(r[nidx:])
            else:
                role.append(r)
                roleNotes.append(None)
        lr = len(role)
        lrid = len(roleID)
        if lr > lrid:
            roleID += [None] * (lrid - lr)
        elif lr < lrid:
            roleID = roleID[:lr]
        for i, rid in enumerate(roleID):
            if rid is not None:
                roleID[i] = str(rid)
        if lr == 1:
            role = role[0]
            roleID = roleID[0]
    elif roleID is not None:
        roleID = str(roleID)
    if movieID is not None:
        movieID = str(movieID)
    if (not title) or (movieID is None):
        _b_m_logger.error('empty title or movieID for "%s"', txt)
    if rolesNoChar:
        rolesNoChar = [_f for _f in [x.strip() for x in rolesNoChar.split('/')] if _f]
        if not role:
            role = []
        elif not isinstance(role, list):
            role = [role]
        role += rolesNoChar
    notes = notes.strip()
    if additionalNotes:
        additionalNotes = re_spaces.sub(' ', additionalNotes).strip()
        if notes:
            notes += ' '
        notes += additionalNotes
    m = Movie(title=title, movieID=movieID, notes=notes, currentRole=role,
              roleID=roleID, roleIsPerson=_parsingCharacter,
              modFunct=modFunct, accessSystem=accessSystem)
    if additionalNotes:
        if '(TV Series)' in additionalNotes:
            m['kind'] = 'tv series'
        elif '(Video Game)' in additionalNotes:
            m['kind'] = 'video game'
        elif '(TV Movie)' in additionalNotes:
            m['kind'] = 'tv movie'
        elif '(TV Short)' in additionalNotes:
            m['kind'] = 'tv short'
    if roleNotes and len(roleNotes) == len(roleID):
        for idx, role in enumerate(m.currentRole):
            try:
                if roleNotes[idx]:
                    role.notes = roleNotes[idx]
            except IndexError:
                break
    # Status can't be checked here, and must be detected by the parser.
    if status:
        m['status'] = status
    return m


class DOMParserBase(object):
    """Base parser to handle HTML data from the IMDb's web server."""
    _defGetRefs = False
    _containsObjects = False

    preprocessors = []
    rules = []

    _logger = logger.getChild('domparser')

    def __init__(self):
        """Initialize the parser."""
        self._modFunct = None
        self._as = 'http'
        self._cname = self.__class__.__name__
        self._init()
        self.reset()

    def reset(self):
        """Reset the parser."""
        # Names and titles references.
        self._namesRefs = {}
        self._titlesRefs = {}
        self._reset()

    def _init(self):
        """Subclasses can override this method, if needed."""
        pass

    def _reset(self):
        """Subclasses can override this method, if needed."""
        pass

    def parse(self, html_string, getRefs=None, **kwds):
        """Return the dictionary generated from the given html string;
        getRefs can be used to force the gathering of movies/persons
        references."""
        self.reset()
        if getRefs is not None:
            self.getRefs = getRefs
        else:
            self.getRefs = self._defGetRefs
        if PY2 and isinstance(html_string, str):
            html_string = html_string.decode('utf-8')
        # Temporary fix: self.parse_dom must work even for empty strings.
        html_string = self.preprocess_string(html_string)
        if html_string:
            html_string = html_string.replace('&nbsp;', ' ')
            dom = self.get_dom(html_string)
            try:
                dom = self.preprocess_dom(dom)
            except Exception:
                self._logger.error('%s: caught exception preprocessing DOM',
                                   self._cname, exc_info=True)
            if self.getRefs:
                try:
                    self.gather_refs(dom)
                except Exception:
                    self._logger.warn('%s: unable to gather refs',
                                      self._cname, exc_info=True)
            data = self.parse_dom(dom)
        else:
            data = {}
        try:
            data = self.postprocess_data(data)
        except Exception:
            self._logger.error('%s: caught exception postprocessing data',
                               self._cname, exc_info=True)
        if self._containsObjects:
            self.set_objects_params(data)
        data = self.add_refs(data)
        return data

    def get_dom(self, html_string):
        """Return a dom object, from the given string."""
        try:
            if not _USE_LXML:
                html_string = html_to_xhtml(html_string, omit_tags={"script"})
            dom = build_tree(html_string, force_html=True)
            if dom is None:
                dom = build_tree('')
                self._logger.error('%s: using a fake empty DOM', self._cname)
            return dom
        except Exception:
            self._logger.error('%s: caught exception parsing DOM',
                               self._cname, exc_info=True)
            return build_tree('')

    def xpath(self, element, path):
        """Return elements matching the given XPath."""
        try:
            return piculet_xpath(element, path)
        except Exception:
            self._logger.error('%s: caught exception extracting XPath "%s"',
                               self._cname, path, exc_info=True)
            return []

    def tostring(self, element):
        """Convert the element to a string."""
        if isinstance(element, str):
            return str(element)
        else:
            try:
                return ElementTree.tostring(element, encoding='utf8')
            except Exception:
                self._logger.error('%s: unable to convert to string',
                                   self._cname, exc_info=True)
                return ''

    def clone(self, element):
        """Clone an element."""
        return build_tree(self.tostring(element))

    def preprocess_string(self, html_string):
        """Here we can modify the text, before it's parsed."""
        if not html_string:
            return html_string
        try:
            preprocessors = self.preprocessors
        except AttributeError:
            return html_string
        for src, sub in preprocessors:
            # re._pattern_type is present only since Python 2.5.
            if isinstance(getattr(src, 'sub', None), Callable):
                html_string = src.sub(sub, html_string)
            elif isinstance(src, str) or isinstance(src, unicode):
                html_string = html_string.replace(src, sub)
            elif isinstance(src, Callable):
                try:
                    html_string = src(html_string)
                except Exception:
                    _msg = '%s: caught exception preprocessing html'
                    self._logger.error(_msg, self._cname, exc_info=True)
                    continue
        return html_string

    def gather_refs(self, dom):
        """Collect references."""
        grParser = GatherRefs()
        grParser._as = self._as
        grParser._modFunct = self._modFunct
        refs = grParser.parse_dom(dom)
        refs = grParser.postprocess_data(refs)
        self._namesRefs = refs['names refs']
        self._titlesRefs = refs['titles refs']

    def preprocess_dom(self, dom):
        """Last chance to modify the dom, before the rules are applied."""
        return dom

    def parse_dom(self, dom):
        """Parse the given dom according to the rules specified in self.rules."""
        return Rules(self.rules).extract(dom)

    def postprocess_data(self, data):
        """Here we can modify the data."""
        return data

    def set_objects_params(self, data):
        """Set parameters of Movie/Person/... instances, since they are
        not always set in the parser's code."""
        for obj in flatten(data, yieldDictKeys=True, scalar=_Container):
            obj.accessSystem = self._as
            obj.modFunct = self._modFunct

    def add_refs(self, data):
        """Modify data according to the expected output."""
        if self.getRefs:
            titl_re = r'(%s)' % '|'.join(
                [re.escape(x) for x in list(self._titlesRefs.keys())]
            )
            if titl_re != r'()':
                re_titles = re.compile(titl_re, re.U)
            else:
                re_titles = None
            nam_re = r'(%s)' % '|'.join(
                [re.escape(x) for x in list(self._namesRefs.keys())]
            )
            if nam_re != r'()':
                re_names = re.compile(nam_re, re.U)
            else:
                re_names = None
            _putRefs(data, re_titles, re_names)
        return {'data': data,
                'titlesRefs': self._titlesRefs,
                'namesRefs': self._namesRefs
                }


def _parse_ref(text, link, info):
    """Manage links to references."""
    if link.find('/title/tt') != -1:
        yearK = re_yearKind_index.match(info)
        if yearK and yearK.start() == 0:
            text += ' %s' % info[:yearK.end()]
    return text.replace('\n', ' '), link


class GatherRefs(DOMParserBase):
    """Parser used to gather references to movies, persons."""
    _common_rules = [
        Rule(
            key='text',
            extractor=Path('./text()')
        ),
        Rule(
            key='link',
            extractor=Path('./@href')
        ),
        Rule(
            key='info',
            extractor=Path('./following::text()[1]')
        )
    ]

    _common_transform = lambda x: _parse_ref(
        x.get('text') or '',
        x.get('link') or '',
        (x.get('info') or '').strip()
    )

    rules = [
        Rule(
            key='names refs',
            extractor=Rules(
                foreach='//a[starts-with(@href, "/name/nm")]',
                rules=_common_rules,
                transform=_common_transform
            )
        ),
        Rule(
            key='titles refs',
            extractor=Rules(
                foreach='//a[starts-with(@href, "/title/tt")]',
                rules=_common_rules,
                transform=_common_transform
            )
        )
    ]

    def postprocess_data(self, data):
        result = {}
        for item in ('names refs', 'titles refs'):
            result[item] = {}
            for k, v in data.get(item, []):
                k = k.strip()
                v = v.strip()
                if not (k and v):
                    continue
                imdbID = analyze_imdbid(v)
                if item == 'names refs':
                    obj = Person(personID=imdbID, name=k,
                                 accessSystem=self._as, modFunct=self._modFunct)
                elif item == 'titles refs':
                    obj = Movie(movieID=imdbID, title=k,
                                accessSystem=self._as, modFunct=self._modFunct)
                result[item][k] = obj
        return result

    def add_refs(self, data):
        return data
