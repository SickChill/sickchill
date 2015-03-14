# Author: seedboy
# URL: https://github.com/seedboy
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
#  GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

import re
import traceback
import datetime
import urlparse
import itertools

import sickbeard
import generic
from sickbeard.common import Quality
from sickbeard import logger
from sickbeard import tvcache
from sickbeard import db
from sickbeard import classes
from sickbeard import helpers
from sickbeard import show_name_helpers
from sickbeard.exceptions import ex, AuthException
from sickbeard import clients
from lib import requests
from lib.requests import exceptions
from sickbeard.bs4_parser import BS4Parser
from lib.unidecode import unidecode
from sickbeard.helpers import sanitizeSceneName
from sickbeard.show_name_helpers import allPossibleShowNames
from sickbeard.name_parser.parser import NameParser, InvalidNameException, InvalidShowException


class IPTorrentsProvider(generic.TorrentProvider):
    def __init__(self):

        generic.TorrentProvider.__init__(self, "IPTorrents")

        self.supportsBacklog = True

        self.enabled = False
        self.username = None
        self.password = None
        self.ratio = None
        self.freeleech = False

        self.cache = IPTorrentsCache(self)

        self.urls = {'base_url': 'https://iptorrents.eu',
                'login': 'https://iptorrents.eu/torrents/',
                'search': 'https://iptorrents.eu/torrents/?%s%s&q=%s&qf=ti',
        }

        self.url = self.urls['base_url']

        self.categorie = 'l73=1&l78=1&l66=1&l65=1&l79=1&l5=1&l4=1'

    def isEnabled(self):
        return self.enabled

    def imageName(self):
        return 'iptorrents.png'

    def getQuality(self, item, anime=False):

        quality = Quality.sceneQuality(item[0], anime)
        return quality

    def _checkAuth(self):

        if not self.username or not self.password:
            raise AuthException("Your authentication credentials for " + self.name + " are missing, check your config.")

        return True

    def _doLogin(self):

        login_params = {'username': self.username,
                        'password': self.password,
                        'login': 'submit',
        }

        try:
            response = self.session.post(self.urls['login'], data=login_params, timeout=30, verify=False)
        except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError), e:
            logger.log(u'Unable to connect to ' + self.name + ' provider: ' + ex(e), logger.ERROR)
            return False

        if re.search('tries left', response.text) \
                or re.search('<title>IPT</title>', response.text) \
                or response.status_code == 401:
            logger.log(u'Invalid username or password for ' + self.name + ', Check your settings!', logger.ERROR)
            return False

        return True

    def _get_episode_search_strings(self, ep_obj, add_string=''):

        search_string = {'Episode': []}

        if not ep_obj:
            return []

        if self.show.air_by_date:
            for show_name in set(allPossibleShowNames(self.show)):
                ep_string = sanitizeSceneName(show_name) + ' ' + \
                            str(ep_obj.airdate).replace('-', '|')
                search_string['Episode'].append(ep_string)
        elif self.show.sports:
            for show_name in set(allPossibleShowNames(self.show)):
                ep_string = sanitizeSceneName(show_name) + ' ' + \
                            str(ep_obj.airdate).replace('-', '|') + '|' + \
                            ep_obj.airdate.strftime('%b')
                search_string['Episode'].append(ep_string)
        elif self.show.anime:
            for show_name in set(show_name_helpers.allPossibleShowNames(self.show)):
                ep_string = sanitizeSceneName(show_name) + ' ' + \
                            "%i" % int(ep_obj.scene_absolute_number)
                search_string['Episode'].append(ep_string)
        else:
            for show_name in set(show_name_helpers.allPossibleShowNames(self.show)):
                ep_string = show_name_helpers.sanitizeSceneName(show_name) + ' ' + \
                            sickbeard.config.naming_ep_type[2] % {'seasonnumber': ep_obj.scene_season,
                                                                  'episodenumber': ep_obj.scene_episode} + ' %s' % add_string

                search_string['Episode'].append(re.sub('\s+', ' ', ep_string))

        return [search_string]

    def findSearchResults(self, show, episodes, search_mode, manualSearch=False):

        self._checkAuth()
        self.show = show

        results = {}
        itemList = []

        if search_mode == 'sponly':
            logger.log(u"This provider doesn't support season pack. Consider setting Season search mode to episodes only and unchecked Season search fallback", logger.WARNING)
            search_mode = 'eponly'

        for epObj in episodes:
            # search cache for episode result
            cacheResult = self.cache.searchCache(epObj, manualSearch)
            if cacheResult:
                if epObj.episode not in results:
                    results[epObj.episode] = cacheResult
                else:
                    results[epObj.episode].extend(cacheResult)

                # found result, search next episode
                continue

            for curString in self._get_episode_search_strings(epObj):
                itemList += self._doSearch(curString, 'eponly', len(episodes))

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

            itemList = list(itertools.chain(*[v for (k, v) in sorted(items.items(), reverse=True)]))
            itemList += itemsUnknown if itemsUnknown else []

        # filter results
        cl = []
        for item in itemList:
            (title, url) = self._get_title_and_url(item)

            # parse the file name
            try:
                myParser = NameParser(False, convert=True)
                parse_result = myParser.parse(title)
            except InvalidNameException:
                logger.log(u"Unable to parse the filename " + title + " into a valid episode", logger.DEBUG)
                continue
            except InvalidShowException:
                logger.log(u"Unable to parse the filename " + title + " into a valid show", logger.DEBUG)
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
                            u"This is supposed to be a season pack search but the result " + title + " is not a valid season pack, skipping it",
                            logger.DEBUG)
                        addCacheEntry = True
                    if len(parse_result.episode_numbers) and (
                                    parse_result.season_number not in set([ep.season for ep in episodes]) or not [ep for ep in episodes if
                                                                                 ep.scene_episode in parse_result.episode_numbers]):
                        logger.log(
                            u"The result " + title + " doesn't seem to be a valid episode that we are trying to snatch, ignoring",
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
                            u"The result " + title + " doesn't seem to be a valid episode that we are trying to snatch, ignoring",
                            logger.DEBUG)
                        addCacheEntry = True

                if not addCacheEntry:
                    # we just use the existing info for normal searches
                    actual_season = parse_result.season_number
                    actual_episodes = parse_result.episode_numbers
            else:
                if not (parse_result.is_air_by_date):
                    logger.log(
                        u"This is supposed to be a date search but the result " + title + " didn't parse as one, skipping it",
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
                            u"Tried to look up the date for the episode " + title + " but the database didn't give proper results, skipping it",
                            logger.WARNING)
                        addCacheEntry = True

                if not addCacheEntry:
                    actual_season = int(sql_results[0]["season"])
                    actual_episodes = [int(sql_results[0]["episode"])]

            # add parsed result to cache for usage later on
            if addCacheEntry:
                logger.log(u"Adding item from search to cache: " + title, logger.DEBUG)
                ci = self.cache._addCacheEntry(title, url, parse_result=parse_result)
                if ci is not None:
                    cl.append(ci)
                continue

            # make sure we want the episode
            wantEp = True
            for epNo in actual_episodes:
                if not showObj.wantEpisode(actual_season, epNo, quality, manualSearch):
                    wantEp = False
                    break

            if not wantEp:
                logger.log(
                    u"Ignoring result " + title + " because we don't want an episode that is " +
                    Quality.qualityStrings[
                        quality], logger.DEBUG)

                continue

            logger.log(u"Found result " + title + " at " + url, logger.DEBUG)

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
                logger.log(u"Single episode result.", logger.DEBUG)
            elif len(epObj) > 1:
                epNum = MULTI_EP_RESULT
                logger.log(u"Separating multi-episode result to check for later - result contains episodes: " + str(
                    parse_result.episode_numbers), logger.DEBUG)
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

    def _doSearch(self, search_params, search_mode='eponly', epcount=0, age=0):

        results = []
        items = {'Season': [], 'Episode': [], 'RSS': []}

        freeleech = '&free=on' if self.freeleech else ''

        if not self._doLogin():
            return results

        for mode in search_params.keys():
            for search_string in search_params[mode]:
                if isinstance(search_string, unicode):
                    search_string = unidecode(search_string)

                # URL with 50 tv-show results, or max 150 if adjusted in IPTorrents profile
                searchURL = self.urls['search'] % (self.categorie, freeleech, search_string)
                searchURL += ';o=seeders' if mode != 'RSS' else ''

                logger.log(u"" + self.name + " search page URL: " + searchURL, logger.DEBUG)

                data = self.getURL(searchURL)
                if not data:
                    continue

                try:
                    data = re.sub(r'(?im)<button.+?<[\/]button>', '', data, 0)
                    with BS4Parser(data, features=["html5lib", "permissive"]) as html:
                        if not html:
                            logger.log(u"Invalid HTML data: " + str(data), logger.DEBUG)
                            continue

                        if html.find(text='No Torrents Found!'):
                            logger.log(u"No results found for: " + search_string + " (" + searchURL + ")", logger.DEBUG)
                            continue

                        torrent_table = html.find('table', attrs={'class': 'torrents'})
                        torrents = torrent_table.find_all('tr') if torrent_table else []

                        #Continue only if one Release is found
                        if len(torrents) < 2:
                            logger.log(u"The Data returned from " + self.name + " do not contains any torrent",
                                       logger.WARNING)
                            continue

                        for result in torrents[1:]:

                            try:
                                torrent = result.find_all('td')[1].find('a')
                                torrent_name = torrent.string
                                torrent_download_url = self.urls['base_url'] + (result.find_all('td')[3].find('a'))['href']
                                torrent_details_url = self.urls['base_url'] + torrent['href']
                                torrent_seeders = int(result.find('td', attrs={'class': 'ac t_seeders'}).string)
                                ## Not used, perhaps in the future ##
                                #torrent_id = int(torrent['href'].replace('/details.php?id=', ''))
                                #torrent_leechers = int(result.find('td', attrs = {'class' : 'ac t_leechers'}).string)
                            except (AttributeError, TypeError):
                                continue

                            # Filter unseeded torrent and torrents with no name/url
                            if mode != 'RSS' and torrent_seeders == 0:
                                continue

                            if not torrent_name or not torrent_download_url:
                                continue

                            item = torrent_name, torrent_download_url
                            logger.log(u"Found result: " + torrent_name + " (" + torrent_details_url + ")", logger.DEBUG)
                            items[mode].append(item)

                except Exception, e:
                    logger.log(u"Failed parsing " + self.name + " Traceback: " + traceback.format_exc(), logger.ERROR)

            results += items[mode]

        return results

    def _get_title_and_url(self, item):

        title, url = item

        if title:
            title = u'' + title
            title = title.replace(' ', '.')

        if url:
            url = str(url).replace('&amp;', '&')

        return (title, url)

    def findPropers(self, search_date=datetime.datetime.today()):

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
            return []

        for sqlshow in sqlResults:
            self.show = helpers.findCertainShow(sickbeard.showList, int(sqlshow["showid"]))
            if self.show:
                curEp = self.show.getEpisode(int(sqlshow["season"]), int(sqlshow["episode"]))
                searchString = self._get_episode_search_strings(curEp, add_string='PROPER|REPACK')

                for item in self._doSearch(searchString[0]):
                    title, url = self._get_title_and_url(item)
                    results.append(classes.Proper(title, url, datetime.datetime.today(), self.show))

        return results

    def seedRatio(self):
        return self.ratio

class IPTorrentsCache(tvcache.TVCache):
    def __init__(self, provider):

        tvcache.TVCache.__init__(self, provider)

        # Only poll IPTorrents every 10 minutes max
        self.minTime = 10

    def _getRSSData(self):
        search_params = {'RSS': ['']}
        return {'entries': self.provider._doSearch(search_params)}


provider = IPTorrentsProvider()
