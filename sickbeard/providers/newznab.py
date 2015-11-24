# coding=utf-8
# Author: Nic Wolfe <nic@wolfeden.ca>
# URL: http://code.google.com/p/sickbeard/
#
# Rewrite: Dustyn Gibson (miigotu) <miigotu@gmail.com>
# URL: http://sickrage.github.io
#
# This file is part of SickRage.
#
# SickRage is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SickRage is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.
# pylint: disable=R0902,R0913

import os
import re
import urllib
import datetime
from bs4 import BeautifulSoup

import sickbeard
from sickbeard import classes
from sickbeard import helpers
from sickbeard import scene_exceptions
from sickbeard import logger
from sickbeard import tvcache
from sickbeard import db
from sickbeard.common import Quality
from sickbeard.providers import generic
from sickrage.helper.encoding import ek
from sickbeard.common import USER_AGENT


class NewznabProvider(generic.NZBProvider):
    """
    Generic provider for built in and custom providers who expose a newznab
    compatible api.
    Tested with: newznab, nzedb, spotweb, torznab
    """
    def __init__(self, name, url, key='0', catIDs='5030,5040', search_mode='eponly',
                 search_fallback=False, enable_daily=True, enable_backlog=False):

        generic.NZBProvider.__init__(self, name)

        self.headers.update({'User-Agent': USER_AGENT})

        self.urls = {'base_url': url}
        self.url = self.urls['base_url']

        self.key = key

        self.search_mode = search_mode
        self.search_fallback = search_fallback
        self.enable_daily = enable_daily
        self.enable_backlog = enable_backlog

        self.supportsBacklog = True

        # 0 in the key spot indicates that no key is needed
        self.needs_auth = self.key != '0'
        self.public = not self.needs_auth

        self.catIDs = catIDs if catIDs else '5030,5040'

        self.default = False

        self.cache = NewznabCache(self)

    def configStr(self):
        """
        Generates a '|' delimited string of instance attributes, for saving to config.ini
        """
        return self.name + '|' + self.url + '|' + self.key + '|' + self.catIDs + '|' + str(
            int(self.enabled)) + '|' + self.search_mode + '|' + str(int(self.search_fallback)) + '|' + str(
                int(self.enable_daily)) + '|' + str(int(self.enable_backlog))

    def imageName(self):
        """
        Checks if we have an image for this provider already.
        Returns found image or the default newznab image
        """
        if ek(os.path.isfile,
              ek(os.path.join, sickbeard.PROG_DIR, 'gui', sickbeard.GUI_NAME, 'images', 'providers',
                 self.getID() + '.png')):
            return self.getID() + '.png'
        return 'newznab.png'

    def get_newznab_categories(self):
        """
        Uses the newznab provider url and apikey to get the capabilities.
        Makes use of the default newznab caps param. e.a. http://yournewznab/api?t=caps&apikey=skdfiw7823sdkdsfjsfk
        Returns a tuple with (succes or not, array with dicts [{"id": "5070", "name": "Anime"},
        {"id": "5080", "name": "Documentary"}, {"id": "5020", "name": "Foreign"}...etc}], error message)
        """
        return_categories = []

        if not self._checkAuth():
            return False, return_categories, "Provider requires auth and your key is not set"

        params = {"t": "caps"}
        if self.needs_auth and self.key:
            params['apikey'] = self.key

        url = os.path.join(self.url, 'api?') +  urllib.urlencode(params)
        data = self.getURL(url)
        if not data:
            error_string = u"Error getting xml for [%s]" % url
            logger.log(error_string, logger.WARNING)
            return False, return_categories, error_string

        data = BeautifulSoup(data, features=["html5lib", "permissive"])
        if not self._checkAuthFromData(data):
            data.decompose()
            error_string = u"Error parsing xml for [%s]" % (self.name)
            logger.log(error_string, logger.DEBUG)
            return False, return_categories, error_string

        for category in data.caps.categories.findAll('category'):
            if hasattr(category, 'attrs') and 'TV' in category.attrs['name']:
                return_categories.append({'id': category.attrs['id'], 'name': category.attrs['name']})
                for subcat in category.findAll('subcat'):
                    return_categories.append({'id': subcat.attrs['id'], 'name': subcat.attrs['name']})

        data.decompose()
        return True, return_categories, ""

    def _get_season_search_strings(self, ep_obj):
        """
        Makes objects to pass to _doSearch for manual and backlog season pack searching
        Returns a list containing dicts of search parameters
        """
        to_return = []
        params = {}
        if not ep_obj:
            return to_return

        params['maxage'] = (datetime.datetime.now() - datetime.datetime.combine(ep_obj.airdate, datetime.datetime.min.time())).days + 1
        params['tvdbid'] = ep_obj.show.indexerid

        if ep_obj.show.air_by_date or ep_obj.show.sports:
            date_str = str(ep_obj.airdate).split('-')[0]
            params['season'] = date_str
            params['q'] = date_str.replace('-', '.')
        else:
            params['season'] = str(ep_obj.scene_season)

        save_q = ' ' + params['q'] if 'q' in params else ''

        name_exceptions = list(set([ep_obj.show.name] + scene_exceptions.get_scene_exceptions(ep_obj.show.indexerid)))
        for cur_exception in name_exceptions:
            params['q'] = helpers.sanitizeSceneName(cur_exception) + save_q
            to_return.append(dict(params))

        return to_return

    def _get_episode_search_strings(self, ep_obj, add_string=''):
        """
        Makes objects to pass to _doSearch for manual and backlog season pack searching
        Returns a list containing dicts of search parameters
        """
        to_return = []
        params = {}
        if not ep_obj:
            return to_return

        params['maxage'] = (datetime.datetime.now() - datetime.datetime.combine(ep_obj.airdate, datetime.datetime.min.time())).days + 1
        params['tvdbid'] = ep_obj.show.indexerid

        if ep_obj.show.air_by_date or ep_obj.show.sports:
            date_str = str(ep_obj.airdate)
            params['season'] = date_str.partition('-')[0]
            params['ep'] = date_str.partition('-')[2].replace('-', '/')
        else:
            params['season'] = ep_obj.scene_season
            params['ep'] = ep_obj.scene_episode

        name_exceptions = list(set([ep_obj.show.name] + scene_exceptions.get_scene_exceptions(ep_obj.show.indexerid)))
        for cur_exception in name_exceptions:
            params['q'] = helpers.sanitizeSceneName(cur_exception)
            if add_string:
                params['q'] += ' ' + add_string

            to_return.append(dict(params))

        return to_return

    def _checkAuth(self):
        """
        Checks that user has set their api key if it is needed
        Returns: True/False
        """
        if self.needs_auth and not self.key:
            logger.log(u"Invalid api key. Check your settings", logger.WARNING)
            return False

        return True

    def _checkAuthFromData(self, data):
        """
        Checks that the returned data is valid
        Returns: _checkAuth if valid otherwise False if there is an error
        """
        if data.findAll('categories') + data.findAll('item'):
            return self._checkAuth()

        try:
            err_code = int(data.error.attrs['code'])
            err_desc = data.error.attrs['description']
            if not (err_code or err_desc):
                raise
        except (AssertionError, AttributeError, ValueError):
            return self._checkAuth()

        if err_code == 100:
            logger.log(u'Your API key for %s is incorrect, please check your config.' % self.name)
        elif err_code == 101:
            logger.log(u'Your account on %s has been suspended, contact the administrator.' % self.name)
        elif err_code == 102:
            logger.log(u'Your account is not allowed to use the API on %s, contact the administrator' % self.name)
        elif err_code == 500:
            logger.log(u'Your account for %s has reached the api limit' % self.name)
        else:
            logger.log(u'Unknown error: %s' % err_desc, logger.ERROR)

        return False

    def _doSearch(self, search_params, search_mode='eponly', epcount=0, age=0, epObj=None): # pylint: disable=R0913,R0914
        """
        Searches indexer using the params in search_params, either for latest releases, or a string/id search
        Returns: list of results in dict form
        """
        results = []
        if not self._checkAuth():
            return results

        params = {
            "t": "tvsearch",
            "maxage": (4, age)[age],
            "limit": 100,
            "offset": 0,
            "cat": self.catIDs.strip(', ')
        }

        if self.needs_auth and self.key:
            params['apikey'] = self.key

        if search_params:
            params.update(search_params)

        params['maxage'] = min(params['maxage'], sickbeard.USENET_RETENTION)

        search_url = os.path.join(self.url, 'api?') + urllib.urlencode(params)
        logger.log(u"Search url: %s" % search_url, logger.DEBUG)
        data = self.getURL(search_url)
        if not data:
            return results

        data = BeautifulSoup(data, features=["html5lib", "permissive"])

        try:
            torznab = 'xmlns:torznab' in data.rss.attrs.keys()
        except AttributeError:
            torznab = False

        if not self._checkAuthFromData(data):
            data.decompose()
            return results

        for item in data.findAll('item'):
            try:
                title = item.title.next.strip()
                download_url = item.link.next.strip()
            except (AttributeError, TypeError):
                continue

            if not (title and download_url):
                continue

            seeders = leechers = None
            size = helpers.tryInt(item.size, -1)
            for attr in item.findAll('newznab:attr') + item.findAll('torznab:attr'):
                size = helpers.tryInt(attr['value'], -1) if attr['name'] == 'size' else size
                seeders = helpers.tryInt(attr['value'], 1) if attr['name'] == 'seeders' else seeders
                leechers = helpers.tryInt(attr['value'], 0) if attr['name'] == 'peers' else leechers

            if not size or (torznab and (seeders is None or leechers is None)):
                continue

            result = {'title': title, 'link': download_url, 'size': size, 'seeders': seeders, 'leechers': leechers}
            results.append(result)

        data.decompose()

        if torznab:
            results.sort(key=lambda d: d.get('seeders', 0) or 0, reverse=True)

        return results


    def _get_size(self, item):
        """
        Gets size info from a result item
        Returns int size or -1
        """
        return helpers.tryInt(item.get('size', -1), -1)


    def findPropers(self, search_date=datetime.datetime.today()):
        """
        Searches providers for PROPER or REPACK releases
        Returns a list of objects of type classes.Proper
        """
        results = []

        myDB = db.DBConnection()
        sqlResults = myDB.select(
            'SELECT s.show_name, e.showid, e.season, e.episode, e.status, e.airdate FROM tv_episodes AS e' +
            ' INNER JOIN tv_shows AS s ON (e.showid = s.indexer_id)' +
            ' WHERE e.airdate >= ' + str(search_date.toordinal()) +
            ' AND (e.status IN (' + ','.join([str(x) for x in Quality.DOWNLOADED]) + ')' +
            ' OR (e.status IN (' + ','.join([str(x) for x in Quality.SNATCHED]) + ')))'
        )

        if not sqlResults:
            return results

        for sqlshow in sqlResults:
            self.show = helpers.findCertainShow(sickbeard.showList, int(sqlshow["showid"]))
            if self.show:
                curEp = self.show.getEpisode(int(sqlshow["season"]), int(sqlshow["episode"]))
                searchStrings = self._get_episode_search_strings(curEp, add_string='PROPER|REPACK')
                for searchString in searchStrings:
                    for item in self._doSearch(searchString):
                        title, url = self._get_title_and_url(item)
                        if re.match(r'.*(REPACK|PROPER).*', title, re.I):
                            results.append(classes.Proper(title, url, datetime.datetime.today(), self.show))

        return results


class NewznabCache(tvcache.TVCache):
    def __init__(self, provider_obj):

        tvcache.TVCache.__init__(self, provider_obj)

        # only poll newznab providers every 30 minutes
        self.minTime = 30

    def _getRSSData(self):
        return {'entries': self.provider._doSearch({})}
