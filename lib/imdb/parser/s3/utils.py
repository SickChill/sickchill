# Copyright 2018 Davide Alberani <da@erlug.linux.it>
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
This package provides utilities for the s3 dataset.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import re
import sqlalchemy
from difflib import SequenceMatcher
from imdb.utils import canonicalName, canonicalTitle, _unicodeArticles

SOUNDEX_LENGTH = 5
RO_THRESHOLD = 0.6
STRING_MAXLENDIFFER = 0.7
re_imdbids = re.compile(r'(nm|tt)')
re_characters = re.compile(r'"(.+?)"')


def transf_imdbid(x):
    return int(x[2:])


def transf_multi_imdbid(x):
    if not x:
        return x
    return re_imdbids.sub('', x)


def transf_multi_character(x):
    if not x:
        return x
    ' / '.join(re_characters.findall(x))


def transf_int(x):
    try:
        return int(x)
    except:
        return None


def transf_float(x):
    try:
        return float(x)
    except:
        return None


def transf_bool(x):
    try:
        return x == '1'
    except:
        return None


KIND = {
    'tvEpisode': 'episode',
    'tvMiniSeries': 'tv mini series',
    'tvSeries': 'tv series',
    'tvShort': 'tv short',
    'tvSpecial': 'tv special',
    'videoGame': 'video game'
}

def transf_kind(x):
    return KIND.get(x, x)


# Database mapping.
# 'type' force a conversion to a specific SQL type
# 'transform' applies a conversion to the content (changes the data in the database)
# 'rename' is applied when reading the column names (the columns names are unchanged, in the database)
# 'index' mark the columns that need to be indexed
# 'length' is applied to VARCHAR fields
DB_TRANSFORM = {
    'title_basics': {
        'tconst': {'type': sqlalchemy.Integer, 'transform': transf_imdbid,
                   'rename': 'movieID', 'index': True},
        'titleType': {'type': sqlalchemy.String, 'transform': transf_kind,
                      'rename': 'kind', 'length': 16, 'index': True},
        'primaryTitle': {'rename': 'title'},
        'originalTitle': {'rename': 'original title'},
        'isAdult': {'type': sqlalchemy.Boolean, 'transform': transf_bool, 'rename': 'adult', 'index': True},
        'startYear': {'type': sqlalchemy.Integer, 'transform': transf_int, 'index': True},
        'endYear': {'type': sqlalchemy.Integer, 'transform': transf_int},
        'runtimeMinutes': {'type': sqlalchemy.Integer, 'transform': transf_int,
                           'rename': 'runtimes', 'index': True},
        't_soundex': {'type': sqlalchemy.String, 'length': 5, 'index': True}
    },
    'name_basics': {
        'nconst': {'type': sqlalchemy.Integer, 'transform': transf_imdbid,
                   'rename': 'personID', 'index': True},
        'primaryName': {'rename': 'name'},
        'birthYear': {'type': sqlalchemy.Integer, 'transform': transf_int,
                      'rename': 'birth date', 'index': True},
        'deathYear': {'type': sqlalchemy.Integer, 'transform': transf_int,
                      'rename': 'death date', 'index': True},
        'primaryProfession': {'rename': 'primary profession'},
        'knownForTitles': {'transform': transf_multi_imdbid, 'rename': 'known for'},
        'ns_soundex': {'type': sqlalchemy.String, 'length': 5, 'index': True},
        'sn_soundex': {'type': sqlalchemy.String, 'length': 5, 'index': True},
        's_soundex': {'type': sqlalchemy.String, 'length': 5, 'index': True},
    },
    'title_akas': {
        'titleId': {'type': sqlalchemy.Integer, 'transform': transf_imdbid,
                   'rename': 'movieID', 'index': True},
        'ordering': {'type': sqlalchemy.Integer, 'transform': transf_int},
        'title': {},
        'region': {'type': sqlalchemy.String, 'length': 5, 'index': True},
        'language': {'type': sqlalchemy.String, 'length': 5, 'index': True},
        'types': {'type': sqlalchemy.String, 'length': 31, 'index': True},
        'attributes': {'type': sqlalchemy.String, 'length': 127},
        'isOriginalTitle': {'type': sqlalchemy.Boolean, 'transform': transf_bool,
                            'rename': 'original', 'index': True},
        't_soundex': {'type': sqlalchemy.String, 'length': 5, 'index': True}
    },
    'title_crew': {
        'tconst': {'type': sqlalchemy.Integer, 'transform': transf_imdbid,
                   'rename': 'movieID', 'index': True},
        'directors': {'transform': transf_multi_imdbid, 'rename': 'director'},
        'writers': {'transform': transf_multi_imdbid, 'rename': 'writer'}
    },
    'title_episode': {
        'tconst': {'type': sqlalchemy.Integer, 'transform': transf_imdbid,
                   'rename': 'movieID', 'index': True},
        'parentTconst': {'type': sqlalchemy.Integer, 'transform': transf_imdbid, 'index': True},
        'seasonNumber': {'type': sqlalchemy.Integer, 'transform': transf_int,
                         'rename': 'seasonNr'},
        'episodeNumber': {'type': sqlalchemy.Integer, 'transform': transf_int,
                          'rename': 'episodeNr'}
    },
    'title_principals': {
        'tconst': {'type': sqlalchemy.Integer, 'transform': transf_imdbid,
                   'rename': 'movieID', 'index': True},
        'ordering': {'type': sqlalchemy.Integer, 'transform': transf_int},
        'nconst': {'type': sqlalchemy.Integer, 'transform': transf_imdbid,
                   'rename': 'personID', 'index': True},
        'category': {'type': sqlalchemy.String, 'length': 64},
        'job': {'type': sqlalchemy.String, 'length': 1024},
        'characters': {'type': sqlalchemy.String, 'length': 1024,
                       'transform': transf_multi_character}
    },
    'title_ratings': {
        'tconst': {'type': sqlalchemy.Integer, 'transform': transf_imdbid,
                   'rename': 'movieID', 'index': True},
        'averageRating': {'type': sqlalchemy.Float, 'transform': transf_float,
                          'rename': 'rating', 'index': True},
        'numVotes': {'type': sqlalchemy.Integer, 'transform': transf_int,
                     'rename': 'votes', 'index': True}
    }
}


_translate = dict(B='1', C='2', D='3', F='1', G='2', J='2', K='2', L='4',
                    M='5', N='5', P='1', Q='2', R='6', S='2', T='3', V='1',
                    X='2', Z='2')
_translateget = _translate.get
_re_non_ascii = re.compile(r'^[^a-z]*', re.I)


def soundex(s, length=SOUNDEX_LENGTH):
    """Return the soundex code for the given string.

    :param s: the string to convert to soundex
    :type s: str
    :param length: length of the soundex code to generate
    :type length: int
    :returns: the soundex code
    :rtype: str"""
    s = _re_non_ascii.sub('', s)
    if not s:
        return None
    s = s.upper()
    soundCode = s[0]
    count = 1
    for c in s[1:]:
        if count >= length:
            break
        cw = _translateget(c, '0')
        if cw != '0' and soundCode[-1] != cw:
            soundCode += cw
            count += 1
    return soundCode or None


def title_soundex(title):
    """Return the soundex code for the given title; the (optional) starting article is pruned.

    :param title: movie title
    :type title: str
    :returns: soundex of the title (without the article, if any)
    :rtype: str
    """
    if not title:
        return None
    title = canonicalTitle(title)
    ts = title.split(', ')
    if ts[-1].lower() in _unicodeArticles:
        title = ', '.join(ts[:-1])
    return soundex(title)


def name_soundexes(name):
    """Return three soundex codes for the given name.
    :param name: person name
    :type name: str
    :returns: tuple of soundex codes: (S(Name Surname), S(Surname Name), S(Surname))
    :rtype: tuple
    """
    if not name:
        return None, None, None
    s1 = soundex(name)
    canonical_name = canonicalName(name)
    s2 = soundex(canonical_name)
    if s1 == s2:
        s2 = None
    s3 = soundex(canonical_name.split(', ')[0])
    if s3 and s3 in (s1, s2):
        s3 = None
    return s1, s2, s3


def ratcliff(s1, s2, sm):
    """Ratcliff-Obershelp similarity.

    :param s1: first string to compare
    :type s1: str
    :param s2: second string to compare
    :type s2: str
    :param sm: sequence matcher to use for the comparison
    :type sm: :class:`difflib.SequenceMatcher`
    :returns: 0.0-1.0 similarity
    :rtype: float"""
    s1len = len(s1)
    s2len = len(s2)
    if s1len < s2len:
        threshold = float(s1len) / s2len
    else:
        threshold = float(s2len) / s1len
    if threshold < STRING_MAXLENDIFFER:
        return 0.0
    sm.set_seq2(s2.lower())
    return sm.ratio()


def scan_names(name_list, name, results=0, ro_threshold=RO_THRESHOLD):
    """Scan a list of names, searching for best matches against some variations.

    :param name_list: list of (personID, {person_data}) tuples
    :type name_list: list
    :param name: searched name
    :type name: str
    :results: returns at most as much results (all, if 0)
    :type results: int
    :param ro_threshold: ignore results with a score lower than this value
    :type ro_threshold: float
    :returns: list of results sorted by similarity
    :rtype: list"""
    canonical_name = canonicalName(name).replace(',', '')
    sm1 = SequenceMatcher()
    sm2 = SequenceMatcher()
    sm1.set_seq1(name.lower())
    sm2.set_seq1(canonical_name.lower())
    resd = {}
    for i, n_data in name_list:
        nil = n_data['name']
        # Distance with the canonical name.
        ratios = [ratcliff(name, nil, sm1) + 0.1,
                  ratcliff(name, canonicalName(nil).replace(',', ''), sm2)]
        ratio = max(ratios)
        if ratio >= ro_threshold:
            if i in resd:
                if ratio > resd[i][0]:
                    resd[i] = (ratio, (i, n_data))
            else:
                resd[i] = (ratio, (i, n_data))
    res = list(resd.values())
    res.sort()
    res.reverse()
    if results > 0:
        res[:] = res[:results]
    return res


def strip_article(title):
    no_article_title = canonicalTitle(title)
    t2s = no_article_title.split(', ')
    if t2s[-1].lower() in _unicodeArticles:
        no_article_title = ', '.join(t2s[:-1])
    return no_article_title


def scan_titles(titles_list, title, results=0, ro_threshold=RO_THRESHOLD):
    """Scan a list of titles, searching for best matches amongst some variations.

    :param titles_list: list of (movieID, {movie_data}) tuples
    :type titles_list: list
    :param title: searched title
    :type title: str
    :results: returns at most as much results (all, if 0)
    :type results: int
    :param ro_threshold: ignore results with a score lower than this value
    :type ro_threshold: float
    :returns: list of results sorted by similarity
    :rtype: list"""
    no_article_title = strip_article(title)
    sm1 = SequenceMatcher()
    sm1.set_seq1(title.lower())
    sm2 = SequenceMatcher()
    sm2.set_seq2(no_article_title.lower())
    resd = {}
    for i, t_data in titles_list:
        til = t_data['title']
        ratios = [ratcliff(title, til, sm1) + 0.1,
                  ratcliff(no_article_title, strip_article(til), sm2)]
        ratio = max(ratios)
        if t_data.get('kind') == 'episode':
            ratio -= .2
        if ratio >= ro_threshold:
            if i in resd:
                if ratio > resd[i][0]:
                    resd[i] = (ratio, (i, t_data))
            else:
                resd[i] = (ratio, (i, t_data))
    res = list(resd.values())
    res.sort()
    res.reverse()
    if results > 0:
        res[:] = res[:results]
    return res

