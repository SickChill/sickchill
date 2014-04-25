#!/usr/bin/env python2
#encoding:utf-8
#author:echel0n
#project:tvrage_api
#repository:http://github.com/echel0n/tvrage_api
#license:unlicense (http://unlicense.org/)

"""
Modified from http://github.com/dbr/tvrage_api
Simple-to-use Python interface to The TVRage's API (tvrage.com)
"""
from functools import wraps

__author__ = "echel0n"
__version__ = "1.0"

import os
import re
import time
import getpass
import tempfile
import warnings
import logging
import datetime as dt
import requests
import cachecontrol

try:
    import xml.etree.cElementTree as ElementTree
except ImportError:
    import xml.etree.ElementTree as ElementTree

from lib.dateutil.parser import parse
from cachecontrol import caches

from tvrage_ui import BaseUI
from tvrage_exceptions import (tvrage_error, tvrage_userabort, tvrage_shownotfound,
    tvrage_seasonnotfound, tvrage_episodenotfound, tvrage_attributenotfound)

def log():
    return logging.getLogger("tvrage_api")

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
            tbd = self._stack[:-100]
            i = 0
            for o in tbd:
                del self[o]
                del self._stack[i]
                i += 1

            _lastgc = time.time()
            del tbd
                    
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
            raise tvrage_seasonnotfound("Could not find season %s" % (repr(key)))
        else:
            # If it's not numeric, it must be an attribute name, which
            # doesn't exist, so attribute error.
            raise tvrage_attributenotfound("Cannot find attribute %s" % (repr(key)))

    def airedOn(self, date):
        ret = self.search(str(date), 'firstaired')
        if len(ret) == 0:
            raise tvrage_episodenotfound("Could not find any episodes that aired on %s" % date)
        return ret

    def search(self, term = None, key = None):
        """
        Search all episodes in show. Can search all data, or a specific key (for
        example, episodename)

        Always returns an array (can be empty). First index contains the first
        match, and so on.

        Each array index is an Episode() instance, so doing
        search_results[0]['episodename'] will retrieve the episode name of the
        first match.

        Search terms are converted to lower case (unicode) strings.
        """
        results = []
        for cur_season in self.values():
            searchresult = cur_season.search(term = term, key = key)
            if len(searchresult) != 0:
                results.extend(searchresult)

        return results


class Season(dict):
    def __init__(self, show = None):
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
            raise tvrage_episodenotfound("Could not find episode %s" % (repr(episode_number)))
        else:
            return dict.__getitem__(self, episode_number)

    def search(self, term = None, key = None):
        """Search all episodes in season, returns a list of matching Episode
        instances.
        """
        results = []
        for ep in self.values():
            searchresult = ep.search(term = term, key = key)
            if searchresult is not None:
                results.append(
                    searchresult
                )
        return results


class Episode(dict):
    def __init__(self, season = None):
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
            raise tvrage_attributenotfound("Cannot find attribute %s" % (repr(key)))

    def search(self, term = None, key = None):
        """Search episode data for term, if it matches, return the Episode (self).
        The key parameter can be used to limit the search to a specific element,
        for example, episodename.
        
        This primarily for use use by Show.search and Season.search.
        """
        if term == None:
            raise TypeError("must supply string to search for (contents)")

        term = unicode(term).lower()
        for cur_key, cur_value in self.items():
            cur_key, cur_value = unicode(cur_key).lower(), unicode(cur_value).lower()
            if key is not None and cur_key != key:
                # Do not search this key
                continue
            if cur_value.find( unicode(term).lower() ) > -1:
                return self

class TVRage:
    """Create easy-to-use interface to name of season/episode name"""
    def __init__(self,
                interactive = False,
                select_first = False,
                debug = False,
                cache = True,
                banners = False,
                actors = False,
                custom_ui = None,
                language = None,
                search_all_languages = False,
                apikey = None,
                forceConnect=False,
                useZip=False,
                dvdorder=False):

        """
        cache (True/False/str/unicode/urllib2 opener):
            Retrieved XML are persisted to to disc. If true, stores in
            tvrage_api folder under your systems TEMP_DIR, if set to
            str/unicode instance it will use this as the cache
            location. If False, disables caching.  Can also be passed
            an arbitrary Python object, which is used as a urllib2
            opener, which should be created by urllib2.build_opener

        forceConnect (bool):
            If true it will always try to connect to tvrage.com even if we
            recently timed out. By default it will wait one minute before
            trying again, and any requests within that one minute window will
            return an exception immediately.
        """

        self.shows = ShowContainer() # Holds all Show classes
        self.corrections = {} # Holds show-name to show_id mapping
        self.sess = requests.session() # HTTP Session

        self.config = {}

        if apikey is not None:
            self.config['apikey'] = apikey
        else:
            self.config['apikey'] = "Uhewg1Rr0o62fvZvUIZt" # tvdb_api's API key

        self.config['debug_enabled'] = debug # show debugging messages

        self.config['custom_ui'] = custom_ui

        if cache is True:
            self.config['cache_enabled'] = True
            self.sess = cachecontrol.CacheControl(cache=caches.FileCache(self._getTempDir()))
        elif cache is False:
            self.config['cache_enabled'] = False
        elif isinstance(cache, basestring):
            self.config['cache_enabled'] = True
            self.sess = cachecontrol.CacheControl(cache=caches.FileCache(cache))
        else:
            raise ValueError("Invalid value for Cache %r (type was %s)" % (cache, type(cache)))

        if self.config['debug_enabled']:
            warnings.warn("The debug argument to tvrage_api.__init__ will be removed in the next version. "
            "To enable debug messages, use the following code before importing: "
            "import logging; logging.basicConfig(level=logging.DEBUG)")
            logging.basicConfig(level=logging.DEBUG)


        # List of language from http://tvrage.com/api/0629B785CE550C8D/languages.xml
        # Hard-coded here as it is realtively static, and saves another HTTP request, as
        # recommended on http://tvrage.com/wiki/index.php/API:languages.xml
        self.config['valid_languages'] = [
            "da", "fi", "nl", "de", "it", "es", "fr","pl", "hu","el","tr",
            "ru","he","ja","pt","zh","cs","sl", "hr","ko","en","sv","no"
        ]

        # tvrage.com should be based around numeric language codes,
        # but to link to a series like http://tvrage.com/?tab=series&id=79349&lid=16
        # requires the language ID, thus this mapping is required (mainly
        # for usage in tvrage_ui - internally tvrage_api will use the language abbreviations)
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
        # http://tvrage.com/wiki/index.php/Programmers_API

        self.config['base_url'] = "http://services.tvrage.com"

        self.config['url_getSeries'] = u"%(base_url)s/feeds/search.php" % self.config
        self.config['params_getSeries'] = {"show": ""}

        self.config['url_epInfo'] = u"%(base_url)s/myfeeds/episode_list.php" % self.config
        self.config['params_epInfo'] = {"key": self.config['apikey'], "sid": ""}

        self.config['url_seriesInfo'] = u"%(base_url)s/myfeeds/showinfo.php" % self.config
        self.config['params_seriesInfo'] = {"key": self.config['apikey'], "sid": ""}

    def _getTempDir(self):
        """Returns the [system temp dir]/tvrage_api-u501 (or
        tvrage_api-myuser)
        """
        if hasattr(os, 'getuid'):
            uid = "u%d" % (os.getuid())
        else:
            # For Windows
            try:
                uid = getpass.getuser()
            except ImportError:
                return os.path.join(tempfile.gettempdir(), "tvrage_api")

        return os.path.join(tempfile.gettempdir(), "tvrage_api-%s" % (uid))

    @retry(tvrage_error)
    def _loadUrl(self, url, params=None):
        try:
            log().debug("Retrieving URL %s" % url)

            # get response from TVRage
            if self.config['cache_enabled']:
                resp = self.sess.get(url, cache_auto=True, params=params)
            else:
                resp = requests.get(url, params=params)

        except requests.HTTPError, e:
            raise tvrage_error("HTTP error " + str(e.errno) + " while loading URL " + str(url))

        except requests.ConnectionError, e:
            raise tvrage_error("Connection error " + str(e.message) + " while loading URL " + str(url))

        except requests.Timeout, e:
            raise tvrage_error("Connection timed out " + str(e.message) + " while loading URL " + str(url))

        return resp.content if resp.ok else None

    def _getetsrc(self, url, params=None):
        """Loads a URL using caching, returns an ElementTree of the source
        """
        reDict = {
            'showid': 'id',
            'showname': 'seriesname',
            'name': 'seriesname',
            'summary': 'overview',
            'started': 'firstaired',
            'genres': 'genre',
            'airtime': 'airs_time',
            'airday': 'airs_dayofweek',
            'image': 'fanart',
            'epnum': 'id',
            'title': 'episodename',
            'airdate': 'firstaired',
            'screencap': 'filename',
            'seasonnum': 'episodenumber',
        }

        robj = re.compile('|'.join(reDict.keys()))
        src = self._loadUrl(url, params)
        try:
            # TVRAGE doesn't sanitize \r (CR) from user input in some fields,
            # remove it to avoid errors. Change from SickBeard, from will14m
            xml = ElementTree.fromstring(src.rstrip("\r"))
            tree = ElementTree.ElementTree(xml)
            for elm in tree.findall('.//*'):
                elm.tag = robj.sub(lambda m: reDict[m.group(0)], elm.tag)

                if elm.tag in 'firstaired':
                    try:
                        if elm.text in "0000-00-00":
                            elm.text = str(dt.date.fromordinal(1))
                        elm.text = re.sub("([-]0{2}){1,}", "", elm.text)
                        fixDate = parse(elm.text, fuzzy=True).date()
                        elm.text = fixDate.strftime("%Y-%m-%d")
                    except:
                        pass
            return ElementTree.fromstring(ElementTree.tostring(xml))
        except SyntaxError:
            src = self._loadUrl(url, params)
            try:
                xml = ElementTree.fromstring(src.rstrip("\r"))
                tree = ElementTree.ElementTree(xml)
                for elm in tree.findall('.//*'):
                    elm.tag = robj.sub(lambda m: reDict[m.group(0)], elm.tag)

                    if elm.tag in 'firstaired' and elm.text:
                        if elm.text == "0000-00-00":
                            elm.text = str(dt.date.fromordinal(1))
                        try:
                            #month = strptime(match.group('air_month')[:3],'%b').tm_mon
                            #day = re.sub("(st|nd|rd|th)", "", match.group('air_day'))
                            #dtStr = '%s/%s/%s' % (year, month, day)

                            fixDate = parse(elm.text, fuzzy=True)
                            elm.text = fixDate.strftime("%Y-%m-%d")
                        except:
                            pass
                    return ElementTree.fromstring(ElementTree.tostring(xml))
            except SyntaxError, exceptionmsg:
                errormsg = "There was an error with the XML retrieved from tvrage.com:\n%s" % (
                    exceptionmsg
                )

                if self.config['cache_enabled']:
                    errormsg += "\nFirst try emptying the cache folder at..\n%s" % (
                        self.config['cache_location']
                    )

                errormsg += "\nIf this does not resolve the issue, please try again later. If the error persists, report a bug on\n"
                raise tvrage_error(errormsg)

    def _setItem(self, sid, seas, ep, attrib, value):
        """Creates a new episode, creating Show(), Season() and
        Episode()s as required. Called by _getShowData to populate show

        Since the nice-to-use tvrage[1][24]['name] interface
        makes it impossible to do tvrage[1][24]['name] = "name"
        and still be capable of checking if an episode exists
        so we can raise tvrage_shownotfound, we have a slightly
        less pretty method of setting items.. but since the API
        is supposed to be read-only, this is the best way to
        do it!
        The problem is that calling tvrage[1][24]['episodename'] = "name"
        calls __getitem__ on tvrage[1], there is no way to check if
        tvrage.__dict__ should have a key "1" before we auto-create it
        """
        if sid not in self.shows:
            self.shows[sid] = Show()
        if seas not in self.shows[sid]:
            self.shows[sid][seas] = Season(show = self.shows[sid])
        if ep not in self.shows[sid][seas]:
            self.shows[sid][seas][ep] = Episode(season = self.shows[sid][seas])
        self.shows[sid][seas][ep][attrib] = value

    def _setShowData(self, sid, key, value):
        """Sets self.shows[sid] to a new Show instance, or sets the data
        """
        if sid not in self.shows:
            self.shows[sid] = Show()
        self.shows[sid].data[key] = value

    def _cleanData(self, data):
        """Cleans up strings returned by tvrage.com

        Issues corrected:
        - Replaces &amp; with &
        - Trailing whitespace
        """
        if isinstance(data, str):
            data = data.replace(u"&amp;", u"&")
            data = data.strip()
        return data

    def search(self, series):
        """This searches tvrage.com for the series name
        and returns the result list
        """
        series = series.encode("utf-8")
        log().debug("Searching for show %s" % series)
        self.config['params_getSeries']['show'] = series
        seriesEt = self._getetsrc(self.config['url_getSeries'], self.config['params_getSeries'])
        allSeries = list(dict((s.tag.lower(),s.text) for s in x.getchildren()) for x in seriesEt)

        return allSeries

    def _getSeries(self, series):
        """This searches tvrage.com for the series name,
        If a custom_ui UI is configured, it uses this to select the correct
        series. If not, and interactive == True, ConsoleUI is used, if not
        BaseUI is used to select the first result.
        """
        allSeries = self.search(series)

        if len(allSeries) == 0:
            log().debug('Series result returned zero')
            raise tvrage_shownotfound("Show-name search returned zero results (cannot find show on TVRAGE)")

        if self.config['custom_ui'] is not None:
            log().debug("Using custom UI %s" % (repr(self.config['custom_ui'])))
            ui = self.config['custom_ui'](config = self.config)
        else:
            log().debug('Auto-selecting first search result using BaseUI')
            ui = BaseUI(config = self.config)

        return ui.selectSeries(allSeries)

    def _getShowData(self, sid, seriesSearch=False):
        """Takes a series ID, gets the epInfo URL and parses the TVRAGE
        XML file into the shows dict in layout:
        shows[series_id][season_number][episode_number]
        """

        # Parse show information
        log().debug('Getting all series data for %s' % (sid))
        self.config['params_seriesInfo']['sid'] = sid
        seriesInfoEt = self._getetsrc(
            self.config['url_seriesInfo'],
            self.config['params_seriesInfo']
        )

        if seriesInfoEt is None: return False
        for curInfo in seriesInfoEt:
            tag = curInfo.tag.lower()
            value = curInfo.text

            if tag == 'seriesname' and value is None:
                return False

            if tag == 'id':
                value = int(value)

            if value is not None:
                value = self._cleanData(value)

            self._setShowData(sid, tag, value)
        if seriesSearch: return True

        try:
            # Parse genre data
            log().debug('Getting genres of %s' % (sid))
            for genre in seriesInfoEt.find('genres'):
                tag = genre.tag.lower()

                value = genre.text
                if value is not None:
                    value = self._cleanData(value)

                self._setShowData(sid, tag, value)
        except Exception:
            log().debug('No genres for %s' % (sid))

        # Parse episode data
        log().debug('Getting all episodes of %s' % (sid))

        self.config['params_epInfo']['sid'] = sid
        epsEt = self._getetsrc(self.config['url_epInfo'], self.config['params_epInfo'])
        for cur_list in epsEt.findall("Episodelist"):
            for cur_seas in cur_list:
                try:
                    seas_no = int(cur_seas.attrib['no'])
                    for cur_ep in cur_seas:
                        ep_no = int(cur_ep.find('episodenumber').text)
                        self._setItem(sid, seas_no, ep_no, 'seasonnumber', seas_no)
                        for cur_item in cur_ep:
                            tag = cur_item.tag.lower()

                            value = cur_item.text
                            if value is not None:
                                if tag == 'id':
                                    value = int(value)

                                value = self._cleanData(value)

                            self._setItem(sid, seas_no, ep_no, tag, value)
                except:
                    continue
        return True

    def _nameToSid(self, name):
        """Takes show name, returns the correct series ID (if the show has
        already been grabbed), or grabs all episodes and returns
        the correct SID.
        """
        if name in self.corrections:
            log().debug('Correcting %s to %s' % (name, self.corrections[name]) )
            return self.corrections[name]
        else:
            log().debug('Getting show %s' % (name))
            selected_series = self._getSeries(name)
            if isinstance(selected_series, dict):
                selected_series = [selected_series]
            sids = list(int(x['id']) for x in selected_series if self._getShowData(int(x['id']), seriesSearch=True))
            self.corrections.update(dict((x['seriesname'], int(x['id'])) for x in selected_series))
            return sids

    def __getitem__(self, key):
        """Handles tvrage_instance['seriesname'] calls.
        The dict index should be the show id
        """
        if isinstance(key, (int, long)):
            # Item is integer, treat as show id
            if key not in self.shows:
                self._getShowData(key)
            return self.shows[key]

        key = str(key).lower()
        self.config['searchterm'] = key
        selected_series = self._getSeries(key)
        if isinstance(selected_series, dict):
            selected_series = [selected_series]
        [[self._setShowData(show['id'], k, v) for k, v in show.items()] for show in selected_series]
        return selected_series
        #test = self._getSeries(key)
        #sids = self._nameToSid(key)
        #return list(self.shows[sid] for sid in sids)

    def __repr__(self):
        return str(self.shows)


def main():
    """Simple example of using tvrage_api - it just
    grabs an episode name interactively.
    """
    import logging
    logging.basicConfig(level=logging.DEBUG)

    tvrage_instance = TVRage(cache=False)
    print tvrage_instance['Lost']['seriesname']
    print tvrage_instance['Lost'][1][4]['episodename']

if __name__ == '__main__':
    main()
