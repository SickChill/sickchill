# !/usr/bin/env python2
# encoding:utf-8
# author:dbr/Ben
#project:tvdb_api
#repository:http://github.com/dbr/tvdb_api
#license:unlicense (http://unlicense.org/)

from functools import wraps
import traceback

__author__ = "dbr/Ben"
__version__ = "1.9"

import os
import re
import time
import getpass
import StringIO
import tempfile
import warnings
import logging
import zipfile
import datetime as dt
import requests

import xmltodict

try:
    import xml.etree.cElementTree as ElementTree
except ImportError:
    import xml.etree.ElementTree as ElementTree

try:
    import gzip
except ImportError:
    gzip = None

from dateutil.parser import parse
from cachecontrol import CacheControl, caches

from tvdb_ui import BaseUI, ConsoleUI
from tvdb_exceptions import (tvdb_error, tvdb_userabort, tvdb_shownotfound, tvdb_showincomplete,
                             tvdb_seasonnotfound, tvdb_episodenotfound, tvdb_attributenotfound)


def log():
    return logging.getLogger("tvdb_api")


def retry(ExceptionToCheck, tries=4, delay=3, backoff=2, logger=None):
    """Retry calling the decorated function using an exponential backoff.

    http://www.saltycrane.com/blog/2009/11/trying-out-retry-decorator-python/
    original from: http://wiki.python.org/moin/PythonDecoratorLibrary#Retry

    :param ExceptionToCheck: the exception to check. may be a tuple of
        exceptions to check
    :type ExceptionToCheck: Exception or tuple
    :param tries: number of times to try (not retry) before giving up
    :type tries: int
    :param delay: initial delay between retries in seconds
    :type delay: int
    :param backoff: backoff multiplier e.g. value of 2 will double the delay
        each retry
    :type backoff: int
    :param logger: logger to use. If None, print
    :type logger: logging.Logger instance
    """

    def deco_retry(f):

        @wraps(f)
        def f_retry(*args, **kwargs):
            mtries, mdelay = tries, delay
            while mtries > 1:
                try:
                    return f(*args, **kwargs)
                except ExceptionToCheck, e:
                    msg = "%s, Retrying in %d seconds..." % (str(e), mdelay)
                    if logger:
                        logger.warning(msg)
                    else:
                        print msg
                    time.sleep(mdelay)
                    mtries -= 1
                    mdelay *= backoff
            return f(*args, **kwargs)

        return f_retry  # true decorator

    return deco_retry


class ShowContainer(dict):
    """Simple dict that holds a series of Show instances
    """

    def __init__(self):
        self._stack = []
        self._lastgc = time.time()

    def __setitem__(self, key, value):
        self._stack.append(key)

        #keep only the 100th latest results
        if time.time() - self._lastgc > 20:
            for o in self._stack[:-100]:
                del self[o]

            self._stack = self._stack[-100:]

            self._lastgc = time.time()

        super(ShowContainer, self).__setitem__(key, value)


class Show(dict):
    """Holds a dict of seasons, and show data.
    """

    def __init__(self):
        dict.__init__(self)
        self.data = {}

    def __repr__(self):
        return "<Show %s (containing %s seasons)>" % (
            self.data.get(u'seriesname', 'instance'),
            len(self)
        )

    def __getattr__(self, key):
        if key in self:
            # Key is an episode, return it
            return self[key]

        if key in self.data:
            # Non-numeric request is for show-data
            return self.data[key]

        raise AttributeError

    def __getitem__(self, key):
        if key in self:
            # Key is an episode, return it
            return dict.__getitem__(self, key)

        if key in self.data:
            # Non-numeric request is for show-data
            return dict.__getitem__(self.data, key)

        # Data wasn't found, raise appropriate error
        if isinstance(key, int) or key.isdigit():
            # Episode number x was not found
            raise tvdb_seasonnotfound("Could not find season %s" % (repr(key)))
        else:
            # If it's not numeric, it must be an attribute name, which
            # doesn't exist, so attribute error.
            raise tvdb_attributenotfound("Cannot find attribute %s" % (repr(key)))

    def airedOn(self, date):
        ret = self.search(str(date), 'firstaired')
        if len(ret) == 0:
            raise tvdb_episodenotfound("Could not find any episodes that aired on %s" % date)
        return ret

    def search(self, term=None, key=None):
        """
        Search all episodes in show. Can search all data, or a specific key (for
        example, episodename)

        Always returns an array (can be empty). First index contains the first
        match, and so on.

        Each array index is an Episode() instance, so doing
        search_results[0]['episodename'] will retrieve the episode name of the
        first match.

        Search terms are converted to lower case (unicode) strings.

        # Examples

        These examples assume t is an instance of Tvdb():

        >>> t = Tvdb()
        >>>

        To search for all episodes of Scrubs with a bit of data
        containing "my first day":

        >>> t['Scrubs'].search("my first day")
        [<Episode 01x01 - My First Day>]
        >>>

        Search for "My Name Is Earl" episode named "Faked His Own Death":

        >>> t['My Name Is Earl'].search('Faked His Own Death', key = 'episodename')
        [<Episode 01x04 - Faked His Own Death>]
        >>>

        To search Scrubs for all episodes with "mentor" in the episode name:

        >>> t['scrubs'].search('mentor', key = 'episodename')
        [<Episode 01x02 - My Mentor>, <Episode 03x15 - My Tormented Mentor>]
        >>>

        # Using search results

        >>> results = t['Scrubs'].search("my first")
        >>> print results[0]['episodename']
        My First Day
        >>> for x in results: print x['episodename']
        My First Day
        My First Step
        My First Kill
        >>>
        """
        results = []
        for cur_season in self.values():
            searchresult = cur_season.search(term=term, key=key)
            if len(searchresult) != 0:
                results.extend(searchresult)

        return results


class Season(dict):
    def __init__(self, show=None):
        """The show attribute points to the parent show
        """
        self.show = show

    def __repr__(self):
        return "<Season instance (containing %s episodes)>" % (
            len(self.keys())
        )

    def __getattr__(self, episode_number):
        if episode_number in self:
            return self[episode_number]
        raise AttributeError

    def __getitem__(self, episode_number):
        if episode_number not in self:
            raise tvdb_episodenotfound("Could not find episode %s" % (repr(episode_number)))
        else:
            return dict.__getitem__(self, episode_number)

    def search(self, term=None, key=None):
        """Search all episodes in season, returns a list of matching Episode
        instances.

        >>> t = Tvdb()
        >>> t['scrubs'][1].search('first day')
        [<Episode 01x01 - My First Day>]
        >>>

        See Show.search documentation for further information on search
        """
        results = []
        for ep in self.values():
            searchresult = ep.search(term=term, key=key)
            if searchresult is not None:
                results.append(
                    searchresult
                )
        return results


class Episode(dict):
    def __init__(self, season=None):
        """The season attribute points to the parent season
        """
        self.season = season

    def __repr__(self):
        seasno = int(self.get(u'seasonnumber', 0))
        epno = int(self.get(u'episodenumber', 0))
        epname = self.get(u'episodename')
        if epname is not None:
            return "<Episode %02dx%02d - %s>" % (seasno, epno, epname)
        else:
            return "<Episode %02dx%02d>" % (seasno, epno)

    def __getattr__(self, key):
        if key in self:
            return self[key]
        raise AttributeError

    def __getitem__(self, key):
        try:
            return dict.__getitem__(self, key)
        except KeyError:
            raise tvdb_attributenotfound("Cannot find attribute %s" % (repr(key)))

    def search(self, term=None, key=None):
        """Search episode data for term, if it matches, return the Episode (self).
        The key parameter can be used to limit the search to a specific element,
        for example, episodename.

        This primarily for use use by Show.search and Season.search. See
        Show.search for further information on search

        Simple example:

        >>> e = Episode()
        >>> e['episodename'] = "An Example"
        >>> e.search("examp")
        <Episode 00x00 - An Example>
        >>>

        Limiting by key:

        >>> e.search("examp", key = "episodename")
        <Episode 00x00 - An Example>
        >>>
        """
        if term == None:
            raise TypeError("must supply string to search for (contents)")

        term = unicode(term).lower()
        for cur_key, cur_value in self.items():
            cur_key, cur_value = unicode(cur_key).lower(), unicode(cur_value).lower()
            if key is not None and cur_key != key:
                # Do not search this key
                continue
            if cur_value.find(unicode(term).lower()) > -1:
                return self


class Actors(list):
    """Holds all Actor instances for a show
    """
    pass


class Actor(dict):
    """Represents a single actor. Should contain..

    id,
    image,
    name,
    role,
    sortorder
    """

    def __repr__(self):
        return "<Actor \"%s\">" % (self.get("name"))


class Tvdb:
    """Create easy-to-use interface to name of season/episode name
    >>> t = Tvdb()
    >>> t['Scrubs'][1][24]['episodename']
    u'My Last Day'
    """

    def __init__(self,
                 interactive=False,
                 select_first=False,
                 debug=False,
                 cache=True,
                 banners=False,
                 actors=False,
                 custom_ui=None,
                 language=None,
                 search_all_languages=False,
                 apikey=None,
                 forceConnect=False,
                 useZip=False,
                 dvdorder=False,
                 proxy=None):

        """interactive (True/False):
            When True, uses built-in console UI is used to select the correct show.
            When False, the first search result is used.

        select_first (True/False):
            Automatically selects the first series search result (rather
            than showing the user a list of more than one series).
            Is overridden by interactive = False, or specifying a custom_ui

        debug (True/False) DEPRECATED:
             Replaced with proper use of logging module. To show debug messages:

                 >>> import logging
                 >>> logging.basicConfig(level = logging.DEBUG)

        cache (True/False/str/unicode/urllib2 opener):
            Retrieved XML are persisted to to disc. If true, stores in
            tvdb_api folder under your systems TEMP_DIR, if set to
            str/unicode instance it will use this as the cache
            location. If False, disables caching.  Can also be passed
            an arbitrary Python object, which is used as a urllib2
            opener, which should be created by urllib2.build_opener

        banners (True/False):
            Retrieves the banners for a show. These are accessed
            via the _banners key of a Show(), for example:

            >>> Tvdb(banners=True)['scrubs']['_banners'].keys()
            ['fanart', 'poster', 'series', 'season']

        actors (True/False):
            Retrieves a list of the actors for a show. These are accessed
            via the _actors key of a Show(), for example:

            >>> t = Tvdb(actors=True)
            >>> t['scrubs']['_actors'][0]['name']
            u'Zach Braff'

        custom_ui (tvdb_ui.BaseUI subclass):
            A callable subclass of tvdb_ui.BaseUI (overrides interactive option)

        language (2 character language abbreviation):
            The language of the returned data. Is also the language search
            uses. Default is "en" (English). For full list, run..

            >>> Tvdb().config['valid_languages'] #doctest: +ELLIPSIS
            ['da', 'fi', 'nl', ...]

        search_all_languages (True/False):
            By default, Tvdb will only search in the language specified using
            the language option. When this is True, it will search for the
            show in and language

        apikey (str/unicode):
            Override the default thetvdb.com API key. By default it will use
            tvdb_api's own key (fine for small scripts), but you can use your
            own key if desired - this is recommended if you are embedding
            tvdb_api in a larger application)
            See http://thetvdb.com/?tab=apiregister to get your own key

        forceConnect (bool):
            If true it will always try to connect to theTVDB.com even if we
            recently timed out. By default it will wait one minute before
            trying again, and any requests within that one minute window will
            return an exception immediately.

        useZip (bool):
            Download the zip archive where possibale, instead of the xml.
            This is only used when all episodes are pulled.
            And only the main language xml is used, the actor and banner xml are lost.
        """

        self.shows = ShowContainer()  # Holds all Show classes
        self.corrections = {}  # Holds show-name to show_id mapping

        self.config = {}

        if apikey is not None:
            self.config['apikey'] = apikey
        else:
            self.config['apikey'] = "0629B785CE550C8D"  # tvdb_api's API key

        self.config['debug_enabled'] = debug  # show debugging messages

        self.config['custom_ui'] = custom_ui

        self.config['interactive'] = interactive  # prompt for correct series?

        self.config['select_first'] = select_first

        self.config['search_all_languages'] = search_all_languages

        self.config['useZip'] = useZip

        self.config['dvdorder'] = dvdorder

        self.config['proxy'] = proxy

        if cache is True:
            self.config['cache_enabled'] = True
            self.config['cache_location'] = self._getTempDir()
        elif cache is False:
            self.config['cache_enabled'] = False
        elif isinstance(cache, basestring):
            self.config['cache_enabled'] = True
            self.config['cache_location'] = cache
        else:
            raise ValueError("Invalid value for Cache %r (type was %s)" % (cache, type(cache)))

        self.config['session'] = requests.Session()

        self.config['banners_enabled'] = banners
        self.config['actors_enabled'] = actors

        if self.config['debug_enabled']:
            warnings.warn("The debug argument to tvdb_api.__init__ will be removed in the next version. "
                          "To enable debug messages, use the following code before importing: "
                          "import logging; logging.basicConfig(level=logging.DEBUG)")
            logging.basicConfig(level=logging.DEBUG)


        # List of language from http://thetvdb.com/api/0629B785CE550C8D/languages.xml
        # Hard-coded here as it is realtively static, and saves another HTTP request, as
        # recommended on http://thetvdb.com/wiki/index.php/API:languages.xml
        self.config['valid_languages'] = [
            "da", "fi", "nl", "de", "it", "es", "fr", "pl", "hu", "el", "tr",
            "ru", "he", "ja", "pt", "zh", "cs", "sl", "hr", "ko", "en", "sv", "no"
        ]

        # thetvdb.com should be based around numeric language codes,
        # but to link to a series like http://thetvdb.com/?tab=series&id=79349&lid=16
        # requires the language ID, thus this mapping is required (mainly
        # for usage in tvdb_ui - internally tvdb_api will use the language abbreviations)
        self.config['langabbv_to_id'] = {'el': 20, 'en': 7, 'zh': 27,
                                         'it': 15, 'cs': 28, 'es': 16, 'ru': 22, 'nl': 13, 'pt': 26, 'no': 9,
                                         'tr': 21, 'pl': 18, 'fr': 17, 'hr': 31, 'de': 14, 'da': 10, 'fi': 11,
                                         'hu': 19, 'ja': 25, 'he': 24, 'ko': 32, 'sv': 8, 'sl': 30}

        if language is None:
            self.config['language'] = 'en'
        else:
            if language not in self.config['valid_languages']:
                raise ValueError("Invalid language %s, options are: %s" % (
                    language, self.config['valid_languages']
                ))
            else:
                self.config['language'] = language

        # The following url_ configs are based of the
        # http://thetvdb.com/wiki/index.php/Programmers_API
        self.config['base_url'] = "http://thetvdb.com"

        if self.config['search_all_languages']:
            self.config['url_getSeries'] = u"%(base_url)s/api/GetSeries.php" % self.config
            self.config['params_getSeries'] = {"seriesname": "", "language": "all"}
        else:
            self.config['url_getSeries'] = u"%(base_url)s/api/GetSeries.php" % self.config
            self.config['params_getSeries'] = {"seriesname": "", "language": self.config['language']}

        self.config['url_epInfo'] = u"%(base_url)s/api/%(apikey)s/series/%%s/all/%%s.xml" % self.config
        self.config['url_epInfo_zip'] = u"%(base_url)s/api/%(apikey)s/series/%%s/all/%%s.zip" % self.config

        self.config['url_seriesInfo'] = u"%(base_url)s/api/%(apikey)s/series/%%s/%%s.xml" % self.config
        self.config['url_actorsInfo'] = u"%(base_url)s/api/%(apikey)s/series/%%s/actors.xml" % self.config

        self.config['url_seriesBanner'] = u"%(base_url)s/api/%(apikey)s/series/%%s/banners.xml" % self.config
        self.config['url_artworkPrefix'] = u"%(base_url)s/banners/%%s" % self.config

        self.config['url_updates_all'] = u"%(base_url)s/api/%(apikey)s/updates_all.zip" % self.config
        self.config['url_updates_month'] = u"%(base_url)s/api/%(apikey)s/updates_month.zip" % self.config
        self.config['url_updates_week'] = u"%(base_url)s/api/%(apikey)s/updates_week.zip" % self.config
        self.config['url_updates_day'] = u"%(base_url)s/api/%(apikey)s/updates_day.zip" % self.config

    def _getTempDir(self):
        """Returns the [system temp dir]/tvdb_api-u501 (or
        tvdb_api-myuser)
        """
        if hasattr(os, 'getuid'):
            uid = "u%d" % (os.getuid())
        else:
            # For Windows
            try:
                uid = getpass.getuser()
            except ImportError:
                return os.path.join(tempfile.gettempdir(), "tvdb_api")

        return os.path.join(tempfile.gettempdir(), "tvdb_api-%s" % (uid))

    @retry(tvdb_error)
    def _loadUrl(self, url, params=None, language=None):
        try:
            log().debug("Retrieving URL %s" % url)

            # get response from TVDB
            if self.config['cache_enabled']:

                session = CacheControl(sess=self.config['session'], cache=caches.FileCache(self.config['cache_location'], use_dir_lock=True), cache_etags=False)
                if self.config['proxy']:
                    log().debug("Using proxy for URL: %s" % url)
                    session.proxies = {
                        "http": self.config['proxy'],
                        "https": self.config['proxy'],
                    }

                resp = session.get(url.strip(), params=params)
            else:
                resp = requests.get(url.strip(), params=params)

            resp.raise_for_status()
        except requests.exceptions.HTTPError, e:
            raise tvdb_error("HTTP error " + str(e.errno) + " while loading URL " + str(url))
        except requests.exceptions.ConnectionError, e:
            raise tvdb_error("Connection error " + str(e.message) + " while loading URL " + str(url))
        except requests.exceptions.Timeout, e:
            raise tvdb_error("Connection timed out " + str(e.message) + " while loading URL " + str(url))
        except Exception as e:
            raise tvdb_error("Unknown exception while loading URL " + url + ": " + repr(e))

        def process(path, key, value):
            key = key.lower()

            # clean up value and do type changes
            if value:
                try:
                    if key == 'firstaired' and value in "0000-00-00":
                        new_value = str(dt.date.fromordinal(1))
                        new_value = re.sub("([-]0{2}){1,}", "", new_value)
                        fixDate = parse(new_value, fuzzy=True).date()
                        value = fixDate.strftime("%Y-%m-%d")
                    elif key == 'firstaired':
                        value = parse(value, fuzzy=True).date()
                        value = value.strftime("%Y-%m-%d")

                        #if key == 'airs_time':
                        #    value = parse(value).time()
                        #    value = value.strftime("%I:%M %p")
                except:
                    pass

            return key, value

        if 'application/zip' in resp.headers.get("Content-Type", ''):
            try:
                log().debug("We recived a zip file unpacking now ...")
                zipdata = StringIO.StringIO()
                zipdata.write(resp.content)
                myzipfile = zipfile.ZipFile(zipdata)
                return xmltodict.parse(myzipfile.read('%s.xml' % language), postprocessor=process)
            except zipfile.BadZipfile:
                raise tvdb_error("Bad zip file received from thetvdb.com, could not read it")
        else:
            try:
                return xmltodict.parse(resp.content.decode('utf-8'), postprocessor=process)
            except:
                return dict([(u'data', None)])

    def _getetsrc(self, url, params=None, language=None):
        """Loads a URL using caching, returns an ElementTree of the source
        """
        try:
            return self._loadUrl(url, params=params, language=language).values()[0]
        except Exception, e:
            raise tvdb_error(e)

    def _setItem(self, sid, seas, ep, attrib, value):
        """Creates a new episode, creating Show(), Season() and
        Episode()s as required. Called by _getShowData to populate show

        Since the nice-to-use tvdb[1][24]['name] interface
        makes it impossible to do tvdb[1][24]['name] = "name"
        and still be capable of checking if an episode exists
        so we can raise tvdb_shownotfound, we have a slightly
        less pretty method of setting items.. but since the API
        is supposed to be read-only, this is the best way to
        do it!
        The problem is that calling tvdb[1][24]['episodename'] = "name"
        calls __getitem__ on tvdb[1], there is no way to check if
        tvdb.__dict__ should have a key "1" before we auto-create it
        """
        if sid not in self.shows:
            self.shows[sid] = Show()
        if seas not in self.shows[sid]:
            self.shows[sid][seas] = Season(show=self.shows[sid])
        if ep not in self.shows[sid][seas]:
            self.shows[sid][seas][ep] = Episode(season=self.shows[sid][seas])
        self.shows[sid][seas][ep][attrib] = value

    def _setShowData(self, sid, key, value):
        """Sets self.shows[sid] to a new Show instance, or sets the data
        """
        if sid not in self.shows:
            self.shows[sid] = Show()
        self.shows[sid].data[key] = value

    def _cleanData(self, data):
        """Cleans up strings returned by TheTVDB.com

        Issues corrected:
        - Replaces &amp; with &
        - Trailing whitespace
        """

        data = unicode(data).replace(u"&amp;", u"&")
        data = data.strip()
        return data

    def search(self, series):
        """This searches TheTVDB.com for the series name
        and returns the result list
        """
        series = series.encode("utf-8")
        log().debug("Searching for show %s" % series)
        self.config['params_getSeries']['seriesname'] = series

        results = self._getetsrc(self.config['url_getSeries'], self.config['params_getSeries'])
        if not results:
            return

        return results.values()[0]

    def _getSeries(self, series):
        """This searches TheTVDB.com for the series name,
        If a custom_ui UI is configured, it uses this to select the correct
        series. If not, and interactive == True, ConsoleUI is used, if not
        BaseUI is used to select the first result.
        """
        allSeries = self.search(series)
        if not allSeries:
            log().debug('Series result returned zero')
            raise tvdb_shownotfound("Show search returned zero results (cannot find show on TVDB)")

        if not isinstance(allSeries, list):
            allSeries = [allSeries]

        if self.config['custom_ui'] is not None:
            log().debug("Using custom UI %s" % (repr(self.config['custom_ui'])))
            CustomUI = self.config['custom_ui']
            ui = CustomUI(config=self.config)
        else:
            if not self.config['interactive']:
                log().debug('Auto-selecting first search result using BaseUI')
                ui = BaseUI(config=self.config)
            else:
                log().debug('Interactively selecting show using ConsoleUI')
                ui = ConsoleUI(config=self.config)

        return ui.selectSeries(allSeries)

    def _parseBanners(self, sid):
        """Parses banners XML, from
        http://thetvdb.com/api/[APIKEY]/series/[SERIES ID]/banners.xml

        Banners are retrieved using t['show name]['_banners'], for example:

        >>> t = Tvdb(banners = True)
        >>> t['scrubs']['_banners'].keys()
        ['fanart', 'poster', 'series', 'season']
        >>> t['scrubs']['_banners']['poster']['680x1000']['35308']['_bannerpath']
        u'http://thetvdb.com/banners/posters/76156-2.jpg'
        >>>

        Any key starting with an underscore has been processed (not the raw
        data from the XML)

        This interface will be improved in future versions.
        """
        log().debug('Getting season banners for %s' % (sid))
        bannersEt = self._getetsrc(self.config['url_seriesBanner'] % (sid))

        if not bannersEt:
            log().debug('Banners result returned zero')
            return

        banners = {}
        for cur_banner in bannersEt['banner'] if isinstance(bannersEt['banner'], list) else [bannersEt['banner']]:
            bid = cur_banner['id']
            btype = cur_banner['bannertype']
            btype2 = cur_banner['bannertype2']
            if btype is None or btype2 is None:
                continue
            if not btype in banners:
                banners[btype] = {}
            if not btype2 in banners[btype]:
                banners[btype][btype2] = {}
            if not bid in banners[btype][btype2]:
                banners[btype][btype2][bid] = {}

            for k, v in cur_banner.items():
                if k is None or v is None:
                    continue

                k, v = k.lower(), v.lower()
                banners[btype][btype2][bid][k] = v

            for k, v in banners[btype][btype2][bid].items():
                if k.endswith("path"):
                    new_key = "_%s" % (k)
                    log().debug("Transforming %s to %s" % (k, new_key))
                    new_url = self.config['url_artworkPrefix'] % (v)
                    banners[btype][btype2][bid][new_key] = new_url

        self._setShowData(sid, "_banners", banners)

    def _parseActors(self, sid):
        """Parsers actors XML, from
        http://thetvdb.com/api/[APIKEY]/series/[SERIES ID]/actors.xml

        Actors are retrieved using t['show name]['_actors'], for example:

        >>> t = Tvdb(actors = True)
        >>> actors = t['scrubs']['_actors']
        >>> type(actors)
        <class 'tvdb_api.Actors'>
        >>> type(actors[0])
        <class 'tvdb_api.Actor'>
        >>> actors[0]
        <Actor "Zach Braff">
        >>> sorted(actors[0].keys())
        ['id', 'image', 'name', 'role', 'sortorder']
        >>> actors[0]['name']
        u'Zach Braff'
        >>> actors[0]['image']
        u'http://thetvdb.com/banners/actors/43640.jpg'

        Any key starting with an underscore has been processed (not the raw
        data from the XML)
        """
        log().debug("Getting actors for %s" % (sid))
        actorsEt = self._getetsrc(self.config['url_actorsInfo'] % (sid))

        if not actorsEt:
            log().debug('Actors result returned zero')
            return

        cur_actors = Actors()
        for cur_actor in actorsEt['actor'] if isinstance(actorsEt['actor'], list) else [actorsEt['actor']]:
            curActor = Actor()
            for k, v in cur_actor.items():
                if k is None or v is None:
                    continue

                k = k.lower()
                if k == "image":
                    v = self.config['url_artworkPrefix'] % (v)
                else:
                    v = self._cleanData(v)

                curActor[k] = v
            cur_actors.append(curActor)
        self._setShowData(sid, '_actors', cur_actors)

    def _getShowData(self, sid, language, getEpInfo=False):
        """Takes a series ID, gets the epInfo URL and parses the TVDB
        XML file into the shows dict in layout:
        shows[series_id][season_number][episode_number]
        """

        if self.config['language'] is None:
            log().debug('Config language is none, using show language')
            if language is None:
                raise tvdb_error("config['language'] was None, this should not happen")
            getShowInLanguage = language
        else:
            log().debug(
                'Configured language %s override show language of %s' % (
                    self.config['language'],
                    language
                )
            )
            getShowInLanguage = self.config['language']

        # Parse show information
        log().debug('Getting all series data for %s' % (sid))
        seriesInfoEt = self._getetsrc(
            self.config['url_seriesInfo'] % (sid, getShowInLanguage)
        )

        if not seriesInfoEt:
            log().debug('Series result returned zero')
            raise tvdb_error("Series result returned zero")

        # get series data
        for k, v in seriesInfoEt['series'].items():
            if v is not None:
                if k in ['banner', 'fanart', 'poster']:
                    v = self.config['url_artworkPrefix'] % (v)
                else:
                    v = self._cleanData(v)

            self._setShowData(sid, k, v)

        # get episode data
        if getEpInfo:
            # Parse banners
            if self.config['banners_enabled']:
                self._parseBanners(sid)

            # Parse actors
            if self.config['actors_enabled']:
                self._parseActors(sid)

            # Parse episode data
            log().debug('Getting all episodes of %s' % (sid))
            if self.config['useZip']:
                url = self.config['url_epInfo_zip'] % (sid, language)
            else:
                url = self.config['url_epInfo'] % (sid, language)
            epsEt = self._getetsrc(url, language=language)

            if not epsEt:
                log().debug('Series results incomplete')
                raise tvdb_showincomplete("Show search returned incomplete results (cannot find complete show on TVDB)")

            if 'episode' not in epsEt:
                return False

            episodes = epsEt["episode"]
            if not isinstance(episodes, list):
                episodes = [episodes]

            for cur_ep in episodes:
                if self.config['dvdorder']:
                    log().debug('Using DVD ordering.')
                    use_dvd = cur_ep['dvd_season'] != None and cur_ep['dvd_episodenumber'] != None
                else:
                    use_dvd = False

                if use_dvd:
                    seasnum, epno = cur_ep['dvd_season'], cur_ep['dvd_episodenumber']
                else:
                    seasnum, epno = cur_ep['seasonnumber'], cur_ep['episodenumber']

                if seasnum is None or epno is None:
                    log().warning("An episode has incomplete season/episode number (season: %r, episode: %r)" % (
                        seasnum, epno))
                    continue  # Skip to next episode

                # float() is because https://github.com/dbr/tvnamer/issues/95 - should probably be fixed in TVDB data
                seas_no = int(float(seasnum))
                ep_no = int(float(epno))

                for k, v in cur_ep.items():
                    k = k.lower()

                    if v is not None:
                        if k == 'filename':
                            v = self.config['url_artworkPrefix'] % (v)
                        else:
                            v = self._cleanData(v)

                    self._setItem(sid, seas_no, ep_no, k, v)

        return True

    def _nameToSid(self, name):
        """Takes show name, returns the correct series ID (if the show has
        already been grabbed), or grabs all episodes and returns
        the correct SID.
        """
        if name in self.corrections:
            log().debug('Correcting %s to %s' % (name, self.corrections[name]))
            return self.corrections[name]
        else:
            log().debug('Getting show %s' % (name))
            selected_series = self._getSeries(name)
            if isinstance(selected_series, dict):
                selected_series = [selected_series]
            sids = list(int(x['id']) for x in selected_series if
                        self._getShowData(int(x['id']), self.config['language']))
            self.corrections.update(dict((x['seriesname'], int(x['id'])) for x in selected_series))
            return sids

    def __getitem__(self, key):
        """Handles tvdb_instance['seriesname'] calls.
        The dict index should be the show id
        """
        if isinstance(key, (int, long)):
            # Item is integer, treat as show id
            if key not in self.shows:
                self._getShowData(key, self.config['language'], True)
            return self.shows[key]

        key = str(key).lower()
        self.config['searchterm'] = key
        selected_series = self._getSeries(key)
        if isinstance(selected_series, dict):
            selected_series = [selected_series]
        [[self._setShowData(show['id'], k, v) for k, v in show.items()] for show in selected_series]
        return selected_series

    def __repr__(self):
        return str(self.shows)

def main():
    """Simple example of using tvdb_api - it just
    grabs an episode name interactively.
    """
    import logging

    logging.basicConfig(level=logging.DEBUG)

    tvdb_instance = Tvdb(interactive=True, cache=False)
    print tvdb_instance['Lost']['seriesname']
    print tvdb_instance['Lost'][1][4]['episodename']


if __name__ == '__main__':
    main()
