__author__ = 'Andrea De Marco <24erre@gmail.com>'
__version__ = '1.4.0'
__classifiers__ = [
    'Development Status :: 5 - Production/Stable',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: Apache Software License',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Topic :: Internet :: WWW/HTTP',
    'Topic :: Software Development :: Libraries',
]
__copyright__ = "2012, {0!s} ".format(__author__)
__license__ = """
   Copyright {0!s}.

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either expressed or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
""".format(__copyright__)

__docformat__ = 'restructuredtext en'

__doc__ = """
:abstract: Python interface to fanart.tv API
:version: {0!s}
:author: {1!s}
:contact: http://z4r.github.com/
:date: 2012-04-04
:copyright: {2!s}
""".format(__version__, __author__, __license__)


def values(obj):
    return [v for k, v in obj.__dict__.iteritems() if not k.startswith('_')]

BASEURL = 'http://webservice.fanart.tv/v3/%s/%s?api_key=%s'

class FORMAT(object):
    JSON = 'JSON'
    XML = 'XML'
    PHP = 'PHP'


class WS(object):
    MUSIC = 'music'
    MOVIE = 'movies'
    TV = 'tv'


class TYPE(object):
    ALL = 'all'

    class TV(object):
        LOGO = 'clearlogo'
        CHARACTER = 'characterart'
        BACKGROUND = 'showbackground'
        HDLOGO = 'hdtvlogo'
        HDART = 'hdclearart'
        ART = 'clearart'
        THUMB = 'tvthumb'
        POSTER = 'tvposter'
        BANNER = 'tvbanner'
        SEASONTHUMB = 'seasonthumb'
        SEASONPOSTER = 'seasonposter'
        SEASONBANNER = 'seasonbanner'

    class MUSIC(object):
        DISC = 'cdart'
        LOGO = 'musiclogo'
        BACKGROUND = 'artistbackground'
        COVER = 'albumcover'
        THUMB = 'artistthumb'

    class MOVIE(object):
        ART = 'movieart'
        LOGO = 'movielogo'
        DISC = 'moviedisc'
        POSTER = 'movieposter'
        BACKGROUND = 'moviebackground'
        HDLOGO = 'hdmovielogo'
        HDART = 'hdmovieclearart'
        BANNER = 'moviebanner'
        THUMB = 'moviethumb'


class SORT(object):
    POPULAR = 1
    NEWEST = 2
    OLDEST = 3


class LIMIT(object):
    ONE = 1
    ALL = 2

FORMAT_LIST = values(FORMAT)
WS_LIST = values(WS)
TYPE_LIST = values(TYPE.MUSIC) + values(TYPE.TV) + values(TYPE.MOVIE) + [TYPE.ALL]
MUSIC_TYPE_LIST = values(TYPE.MUSIC) + [TYPE.ALL]
TV_TYPE_LIST = values(TYPE.TV) + [TYPE.ALL]
MOVIE_TYPE_LIST = values(TYPE.MOVIE) + [TYPE.ALL]
SORT_LIST = values(SORT)
LIMIT_LIST = values(LIMIT)
