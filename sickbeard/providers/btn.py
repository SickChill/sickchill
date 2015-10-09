# coding=utf-8
# Author: Daniel Heimans
# URL: http://code.google.com/p/sickbeard
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

import time
import socket
import math
import sickbeard
import generic
import itertools

from sickbeard import classes
from sickbeard import scene_exceptions
from sickbeard import logger
from sickbeard import tvcache
from sickbeard.helpers import sanitizeSceneName
from sickbeard.common import MULTI_EP_RESULT
from sickbeard.common import SEASON_RESULT
from sickbeard import db
from sickbeard.name_parser.parser import NameParser, InvalidNameException, InvalidShowException
from sickbeard.common import Quality, cpu_presets
from sickrage.helper.exceptions import AuthException, ex

import jsonrpclib
from datetime import datetime


class BTNProvider(generic.TorrentProvider):
    def __init__(self):
        generic.TorrentProvider.__init__(self, "BTN")

        self.supportsBacklog = True
        self.public = False
        self.supportsAbsoluteNumbering = True

        self.enabled = False
        self.api_key = None
        self.ratio = None

        self.cache = BTNCache(self)

        self.urls = {'base_url': u'http://api.btnapps.net',
                     'website': u'http://broadcasthe.net/',}

        self.url = self.urls['website']

    def isEnabled(self):
        return self.enabled

    def _checkAuth(self):
        if not self.api_key:
            logger.log(u"Invalid api key. Check your settings", logger.WARNING)

        return True

    def _checkAuthFromData(self, parsedJSON):

        if parsedJSON is None:
            return self._checkAuth()

        if 'api-error' in parsedJSON:
            logger.log(u"Incorrect authentication credentials: % s" % parsedJSON['api-error'], logger.DEBUG)
            raise AuthException(
                "Your authentication credentials for " + self.name + " are incorrect, check your config.")

        return True

    def _doSearch(self, search_params, search_mode='eponly', epcount=0, age=0, epObj=None):

        self._checkAuth()

        results = []
        params = {}
        apikey = self.api_key

        # age in seconds
        if age:
            params['age'] = "<=" + str(int(age))

        if search_params:
            params.update(search_params)
            logger.log(u"Search string: %s" %  search_params, logger.DEBUG)

        parsedJSON = self._api_call(apikey, params)
        if not parsedJSON:
            logger.log("No data returned from provider", logger.DEBUG)
            return results

        if self._checkAuthFromData(parsedJSON):

            if 'torrents' in parsedJSON:
                found_torrents = parsedJSON['torrents']
            else:
                found_torrents = {}

            # We got something, we know the API sends max 1000 results at a time.
            # See if there are more than 1000 results for our query, if not we
            # keep requesting until we've got everything.
            # max 150 requests per hour so limit at that. Scan every 15 minutes. 60 / 15 = 4.
            max_pages = 150
            results_per_page = 1000

            if 'results' in parsedJSON and int(parsedJSON['results']) >= results_per_page:
                pages_needed = int(math.ceil(int(parsedJSON['results']) / results_per_page))
                if pages_needed > max_pages:
                    pages_needed = max_pages

                # +1 because range(1,4) = 1, 2, 3
                for page in range(1, pages_needed + 1):
                    parsedJSON = self._api_call(apikey, params, results_per_page, page * results_per_page)
                    # Note that this these are individual requests and might time out individually. This would result in 'gaps'
                    # in the results. There is no way to fix this though.
                    if 'torrents' in parsedJSON:
                        found_torrents.update(parsedJSON['torrents'])

            for torrentid, torrent_info in found_torrents.iteritems():
                (title, url) = self._get_title_and_url(torrent_info)

                if title and url:
                    logger.log(u"Found result: %s " % title, logger.DEBUG)
                    results.append(torrent_info)

        #FIXME SORT RESULTS
        return results

    def _api_call(self, apikey, params={}, results_per_page=1000, offset=0):

        server = jsonrpclib.Server(self.urls['base_url'])
        parsedJSON = {}

        try:
            parsedJSON = server.getTorrents(apikey, params, int(results_per_page), int(offset))
            time.sleep(cpu_presets[sickbeard.CPU_PRESET])

        except jsonrpclib.jsonrpc.ProtocolError, error:
            if error.message == 'Call Limit Exceeded':
                logger.log(u"You have exceeded the limit of 150 calls per hour, per API key which is unique to your user account", logger.WARNING)
            else:
                logger.log(u"JSON-RPC protocol error while accessing provicer. Error: %s " % repr(error), logger.ERROR)
            parsedJSON = {'api-error': ex(error)}
            return parsedJSON

        except socket.timeout:
            logger.log(u"Timeout while accessing provider", logger.WARNING)

        except socket.error, error:
            # Note that sometimes timeouts are thrown as socket errors
            logger.log(u"Socket error while accessing provider. Error: %s " % error[1], logger.WARNING)

        except Exception, error:
            errorstring = str(error)
            if (errorstring.startswith('<') and errorstring.endswith('>')):
                errorstring = errorstring[1:-1]
            logger.log(u"Unknown error while accessing provider. Error: %s " % errorstring, logger.WARNING)

        return parsedJSON

    def _get_title_and_url(self, parsedJSON):

        # The BTN API gives a lot of information in response,
        # however SickRage is built mostly around Scene or
        # release names, which is why we are using them here.

        if 'ReleaseName' in parsedJSON and parsedJSON['ReleaseName']:
            title = parsedJSON['ReleaseName']

        else:
            # If we don't have a release name we need to get creative
            title = u''
            if 'Series' in parsedJSON:
                title += parsedJSON['Series']
            if 'GroupName' in parsedJSON:
                title += '.' + parsedJSON['GroupName'] if title else parsedJSON['GroupName']
            if 'Resolution' in parsedJSON:
                title += '.' + parsedJSON['Resolution'] if title else parsedJSON['Resolution']
            if 'Source' in parsedJSON:
                title += '.' + parsedJSON['Source'] if title else parsedJSON['Source']
            if 'Codec' in parsedJSON:
                title += '.' + parsedJSON['Codec'] if title else parsedJSON['Codec']
            if title:
                title = title.replace(' ', '.')

        url = None
        if 'DownloadURL' in parsedJSON:
            url = parsedJSON['DownloadURL']
            if url:
                # unescaped / is valid in JSON, but it can be escaped
                url = url.replace("\\/", "/")

        return (title, url)

    def _get_season_search_strings(self, ep_obj):
        search_params = []
        current_params = {'category': 'Season'}

        # Search for entire seasons: no need to do special things for air by date or sports shows
        if ep_obj.show.air_by_date or ep_obj.show.sports:
            # Search for the year of the air by date show
            current_params['name'] = str(ep_obj.airdate).split('-')[0]
        elif ep_obj.show.is_anime:
            current_params['name'] = "%d" % ep_obj.scene_absolute_number
        else:
            current_params['name'] = 'Season ' + str(ep_obj.scene_season)

        # search
        if ep_obj.show.indexer == 1:
            current_params['tvdb'] = ep_obj.show.indexerid
            search_params.append(current_params)
        else:
            name_exceptions = list(
                set(scene_exceptions.get_scene_exceptions(ep_obj.show.indexerid) + [ep_obj.show.name]))
            for name in name_exceptions:
                # Search by name if we don't have tvdb id
                current_params['series'] = sanitizeSceneName(name)
                search_params.append(current_params)

        return search_params

    def _get_episode_search_strings(self, ep_obj, add_string=''):

        if not ep_obj:
            return [{}]

        to_return = []
        search_params = {'category': 'Episode'}

        # episode
        if ep_obj.show.air_by_date or ep_obj.show.sports:
            date_str = str(ep_obj.airdate)

            # BTN uses dots in dates, we just search for the date since that
            # combined with the series identifier should result in just one episode
            search_params['name'] = date_str.replace('-', '.')
        elif ep_obj.show.anime:
            search_params['name'] = "%i" % int(ep_obj.scene_absolute_number)
        else:
            # Do a general name search for the episode, formatted like SXXEYY
            search_params['name'] = "S%02dE%02d" % (ep_obj.scene_season, ep_obj.scene_episode)

        # search
        if ep_obj.show.indexer == 1:
            search_params['tvdb'] = ep_obj.show.indexerid
            to_return.append(search_params)
        else:
            # add new query string for every exception
            name_exceptions = list(
                set(scene_exceptions.get_scene_exceptions(ep_obj.show.indexerid) + [ep_obj.show.name]))
            for cur_exception in name_exceptions:
                search_params['series'] = sanitizeSceneName(cur_exception)
                to_return.append(search_params)

        return to_return

    def _doGeneralSearch(self, search_string):
        # 'search' looks as broad is it can find. Can contain episode overview and title for example,
        # use with caution!
        return self._doSearch({'search': search_string})

    def findPropers(self, search_date=None):
        results = []

        search_terms = ['%.proper.%', '%.repack.%']

        for term in search_terms:
            for item in self._doSearch({'release': term}, age=4 * 24 * 60 * 60):
                if item['Time']:
                    try:
                        result_date = datetime.fromtimestamp(float(item['Time']))
                    except TypeError:
                        result_date = None

                    if result_date:
                        if not search_date or result_date > search_date:
                            title, url = self._get_title_and_url(item)
                            results.append(classes.Proper(title, url, result_date, self.show))

        return results

    def seedRatio(self):
        return self.ratio

    def findSearchResults(self, show, episodes, search_mode, manualSearch=False, downCurQuality=False):

        self._checkAuth()
        self.show = show

        results = {}
        itemList = []

        searched_scene_season = None
        for epObj in episodes:
            # search cache for episode result
            cacheResult = self.cache.searchCache(epObj, manualSearch, downCurQuality)
            if cacheResult:
                if epObj.episode not in results:
                    results[epObj.episode] = cacheResult
                else:
                    results[epObj.episode].extend(cacheResult)

                # found result, search next episode
                continue

            # skip if season already searched
            if len(episodes) > 1 and search_mode == 'sponly' and searched_scene_season == epObj.scene_season:
                continue

            # mark season searched for season pack searches so we can skip later on
            searched_scene_season = epObj.scene_season

            if search_mode == 'sponly':
                # get season search results
                for curString in self._get_season_search_strings(epObj):
                    itemList += self._doSearch(curString, search_mode, len(episodes))
            else:
                # get single episode search results
                for curString in self._get_episode_search_strings(epObj):
                    itemList += self._doSearch(curString, search_mode, len(episodes))

        # if we found what we needed already from cache then return results and exit
        if len(results) == len(episodes):
            return results

        # sort list by quality
        if len(itemList):
            items = {}
            itemsUnknown = []
            for item in itemList:
                quality = self.getQuality(item, anime=show.is_anime)
                if quality == Quality.UNKNOWN:
                    itemsUnknown += [item]
                else:
                    if quality not in items:
                        items[quality] = [item]
                    else:
                        items[quality].append(item)

            itemList = list(itertools.chain(*[v for (k, v) in sorted(items.iteritems(), reverse=True)]))
            itemList += itemsUnknown if itemsUnknown else []

        # filter results
        cl = []
        for item in itemList:
            (title, url) = self._get_title_and_url(item)

            # parse the file name
            try:
                myParser = NameParser(False)
                parse_result = myParser.parse(title)
            except InvalidNameException:
                logger.log(u"Unable to parse the filename %s into a valid episode" % title, logger.DEBUG)
                continue
            except InvalidShowException:
                logger.log(u"Unable to parse the filename %s into a valid show" % title, logger.DEBUG)
                continue

            showObj = parse_result.show
            quality = parse_result.quality
            release_group = parse_result.release_group
            version = parse_result.version

            addCacheEntry = False
            if not (showObj.air_by_date or showObj.sports):
                if search_mode == 'sponly':
                    if len(parse_result.episode_numbers):
                        logger.log(
                            u"This is supposed to be a season pack search but the result %s is not a valid season pack, skipping it" % title, logger.DEBUG)
                        addCacheEntry = True
                    if len(parse_result.episode_numbers) and (
                                    parse_result.season_number not in set([ep.season for ep in episodes]) or not [ep for ep in episodes if
                                                                                 ep.scene_episode in parse_result.episode_numbers]):
                        logger.log(
                            u"The result %s doesn't seem to be a valid episode that we are trying to snatch, ignoring" % title,
                            logger.DEBUG)
                        addCacheEntry = True
                else:
                    if not len(parse_result.episode_numbers) and parse_result.season_number and not [ep for ep in
                                                                                                     episodes if
                                                                                                     ep.season == parse_result.season_number and ep.episode in parse_result.episode_numbers]:
                        logger.log(
                            u"The result " + title + " doesn't seem to be a valid season that we are trying to snatch, ignoring",
                            logger.DEBUG)
                        addCacheEntry = True
                    elif len(parse_result.episode_numbers) and not [ep for ep in episodes if
                                                                    ep.season == parse_result.season_number and ep.episode in parse_result.episode_numbers]:
                        logger.log(
                            u"The result %s doesn't seem to be a valid episode that we are trying to snatch, ignoring" % title,
                            logger.DEBUG)
                        addCacheEntry = True

                if not addCacheEntry:
                    # we just use the existing info for normal searches
                    actual_season = parse_result.season_number
                    actual_episodes = parse_result.episode_numbers
            else:
                if not (parse_result.is_air_by_date):
                    logger.log(
                        u"This is supposed to be a date search but the result %s didn't parse as one, skipping it" % title,
                        logger.DEBUG)
                    addCacheEntry = True
                else:
                    airdate = parse_result.air_date.toordinal()
                    myDB = db.DBConnection()
                    sql_results = myDB.select(
                        "SELECT season, episode FROM tv_episodes WHERE showid = ? AND airdate = ?",
                        [showObj.indexerid, airdate])

                    if len(sql_results) != 1:
                        logger.log(
                            u"Tried to look up the date for the episode %s but the database didn't give proper results, skipping it" % title,
                            logger.WARNING)
                        addCacheEntry = True

                if not addCacheEntry:
                    actual_season = int(sql_results[0]["season"])
                    actual_episodes = [int(sql_results[0]["episode"])]

            # add parsed result to cache for usage later on
            if addCacheEntry:
                logger.log(u"Adding item from search to cache: %s " % title, logger.DEBUG)
                ci = self.cache._addCacheEntry(title, url, parse_result=parse_result)
                if ci is not None:
                    cl.append(ci)
                continue

            # make sure we want the episode
            wantEp = True
            for epNo in actual_episodes:
                if not showObj.wantEpisode(actual_season, epNo, quality, manualSearch, downCurQuality):
                    wantEp = False
                    break

            if not wantEp:
                logger.log(
                    u"Ignoring result %s because we don't want an episode that is %s" % (title, Quality.qualityStrings[quality]), logger.DEBUG)

                continue

            logger.log(u"Found result: %s " % title, logger.DEBUG)

            # make a result object
            epObj = []
            for curEp in actual_episodes:
                epObj.append(showObj.getEpisode(actual_season, curEp))

            result = self.getResult(epObj)
            result.show = showObj
            result.url = url
            result.name = title
            result.quality = quality
            result.release_group = release_group
            result.version = version
            result.content = None

            if len(epObj) == 1:
                epNum = epObj[0].episode
                logger.log(u"Single episode result", logger.DEBUG)
            elif len(epObj) > 1:
                epNum = MULTI_EP_RESULT
                logger.log(u"Separating multi-episode result to check for later - result contains episodes: %s" % parse_result.episode_numbers,logger.DEBUG)
            elif len(epObj) == 0:
                epNum = SEASON_RESULT
                logger.log(u"Separating full season result to check for later", logger.DEBUG)

            if epNum not in results:
                results[epNum] = [result]
            else:
                results[epNum].append(result)

        # check if we have items to add to cache
        if len(cl) > 0:
            myDB = self.cache._getDB()
            myDB.mass_action(cl)

        return results


class BTNCache(tvcache.TVCache):
    def __init__(self, provider):
        tvcache.TVCache.__init__(self, provider)

        # At least 15 minutes between queries
        self.minTime = 15

    def _getRSSData(self):
        # Get the torrents uploaded since last check.
        seconds_since_last_update = math.ceil(time.time() - time.mktime(self._getLastUpdate().timetuple()))

        # default to 15 minutes
        seconds_minTime = self.minTime * 60
        if seconds_since_last_update < seconds_minTime:
            seconds_since_last_update = seconds_minTime

        # Set maximum to 24 hours (24 * 60 * 60 = 86400 seconds) of "RSS" data search, older things will need to be done through backlog
        if seconds_since_last_update > 86400:
            logger.log(
                u"The last known successful update was more than 24 hours ago, only trying to fetch the last 24 hours!",
                logger.DEBUG)
            seconds_since_last_update = 86400

        return {'entries': self.provider._doSearch(search_params=None, age=seconds_since_last_update)}


provider = BTNProvider()
