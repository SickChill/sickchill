# Authors: Yannick Croissant <yannick.croissant@gmail.com>
#          adaur <adaur.underground@gmail.com>
# URL: http://code.google.com/p/sickbeard/
#
# This file is part of Sick Beard.
#
# Sick Beard is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Sick Beard is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Sick Beard.  If not, see <http://www.gnu.org/licenses/>.

import re
import datetime
from requests.auth import AuthBase
import sickbeard
import generic

from sickbeard.bs4_parser import BS4Parser
from sickbeard.common import Quality
from sickbeard import logger
from sickbeard import tvcache
from sickbeard import show_name_helpers
from sickbeard import db
from sickbeard import helpers
from sickbeard import classes
from sickbeard.helpers import sanitizeSceneName

class FrenchTorrentDBProvider(generic.TorrentProvider):

    def __init__(self):

        generic.TorrentProvider.__init__(self, "FrenchTorrentDB")

        self.supportsBacklog = True

        self.urls = {
            'base_url': 'http://www.frenchtorrentdb.com',
            }

        self.url = self.urls['base_url']
        self.search_params = {
            "adv_cat%5Bs%5D%5B1%5D": 95,
            "adv_cat%5Bs%5D%5B2%5D": 190,
            "adv_cat%5Bs%5D%5B3%5D": 101,
            "adv_cat%5Bs%5D%5B4%5D": 191,
            "adv_cat%5Bs%5D%5B5%5D": 197,
            "adv_cat%5Bs%5D%5B7%5D": 199,
            "adv_cat%5Bs%5D%5B8%5D": 201,
            "adv_cat%5Bs%5D%5B9%5D": 128,
            "section": "TORRENTS",
            "exact": 1,
            "submit": "GO"
            }

        self.enabled = False
        self.username = None
        self.password = None
        self.ratio = None
        self.minseed = None
        self.minleech = None

    def isEnabled(self):
        return self.enabled

    def imageName(self):
        return 'frenchtorrentdb.png'

    def getQuality(self, item, anime=False):
        quality = Quality.sceneQuality(item[0], anime)
        return quality

    def _doLogin(self):

        params = {
            "section": "LOGIN",
            "challenge": 1
        }

        data = self.getURL(self.url, params=params, json=True)

        post_data = {
            'username'    : self.username,
            'password'    : self.password,
            'secure_login': self._getSecureLogin(data['challenge']),
            'hash'        : data['hash']
            }

        params.pop('challenge')
        params['ajax'] = 1
        self.getURL(self.url, params=params, post_data=post_data)

        return True

    def _getSecureLogin(self, challenges):

        def fromCharCode(*args):
            return ''.join(map(unichr, args))

        def decodeString(p, a, c, k, e, d):
            a = int(a)
            c = int(c)
            def e(c):
                if c < a:
                    f = ''
                else:
                    f = e(c / a)
                return f + fromCharCode(c % a + 161)
            while c:
                c -= 1
                if k[c]:
                    regex = re.compile(e(c))
                    p = re.sub(regex, k[c], p)
            return p

        def decodeChallenge(challenge):
            regexGetArgs = re.compile('\'([^\']+)\',([0-9]+),([0-9]+),\'([^\']+)\'')
            regexIsEncoded = re.compile('decodeURIComponent')
            regexUnquote = re.compile('\'')
            if challenge == 'a':
                return '05f'
            if re.match(regexIsEncoded, challenge) == None:
                return re.sub(regexUnquote, '', challenge)
            args = re.findall(regexGetArgs, challenge)
            decoded = decodeString(
                args[0][0], args[0][1],
                args[0][2], args[0][3].split('|'),
                0, {})
            return decoded

        secureLogin = ''
        for challenge in challenges:
            secureLogin += decodeChallenge(challenge)
        return secureLogin

    def _get_episode_search_strings(self, ep_obj, add_string=''):

        search_string = {'Episode': []}

        if not ep_obj:
            return []

        if self.show.air_by_date:
            for show_name in set(show_name_helpers.allPossibleShowNames(self.show)):
                ep_string = sanitizeSceneName(show_name) + '.' + \
                            str(ep_obj.airdate).replace('-', '|')
                search_string['Episode'].append(ep_string)
        elif self.show.sports:
            for show_name in set(show_name_helpers.allPossibleShowNames(self.show)):
                ep_string = sanitizeSceneName(show_name) + '.' + \
                            str(ep_obj.airdate).replace('-', '|') + '|' + \
                            ep_obj.airdate.strftime('%b')
                search_string['Episode'].append(ep_string)
        elif self.show.anime:
            for show_name in set(show_name_helpers.allPossibleShowNames(self.show)):
                ep_string = sanitizeSceneName(show_name) + '.' + \
                            "%i" % int(ep_obj.scene_absolute_number)
                search_string['Episode'].append(ep_string)
        else:
            for show_name in set(show_name_helpers.allPossibleShowNames(self.show)):
                ep_string = sanitizeSceneName(show_name) + '.' + \
                            sickbeard.config.naming_ep_type[2] % {
                                'seasonnumber': ep_obj.scene_season,
                                'episodenumber': ep_obj.scene_episode
                                } + ' %s' % add_string

                search_string['Episode'].append(re.sub(r'\s+', '.', ep_string))

        return [search_string]

    def _doSearch(self, search_strings, search_mode='eponly', epcount=0, age=0, epObj=None):
        results = []
        items = {'Season': [], 'Episode': [], 'RSS': []}

        # check for auth
        if not self._doLogin():
            return results

        for mode in search_strings.keys():
            for search_string in search_strings[mode]:
                logger.log(u"Search string: " + search_string, logger.DEBUG)
                self.search_params['name'] = search_string

                r = self.getURL(self.url, params=self.search_params)
                with BS4Parser(r, features=["html5lib", "permissive"]) as html:
                    resultsTable = html.find("div", {"class": "DataGrid"})
                    logger.log(u"Page opened", logger.DEBUG)

                    if resultsTable:
                        logger.log(u"We have results ", logger.DEBUG)
                        rows = resultsTable.findAll("ul")

                        for row in rows:
                            link = row.find("a", title=True)
                            title = link['title']

                            autogetURL = self.url +'/' + (row.find("li", {"class": "torrents_name"}).find('a')['href'][1:]).replace('#FTD_MENU' ,'&menu=4')
                            r = self.getURL(autogetURL)
                            with BS4Parser(r, features=["html5lib", "permissive"]) as html:
                                downloadURL = html.find("div", {"class" : "autoget"}).find('a')['href']
                                item = title, downloadURL
                                logger.log(u"Download URL : " + downloadURL, logger.DEBUG)

                                items[mode].append(item)

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
            return results

        for sqlshow in sqlResults:
            self.show = helpers.findCertainShow(sickbeard.showList, int(sqlshow["showid"]))
            if self.show:
                curEp = self.show.getEpisode(int(sqlshow["season"]), int(sqlshow["episode"]))
                search_params = self._get_episode_search_strings(curEp, add_string='PROPER|REPACK')

                for item in self._doSearch(search_params[0]):
                    title, url = self._get_title_and_url(item)
                    results.append(classes.Proper(title, url, datetime.datetime.today(), self.show))

        return results

    def seedRatio(self):
        return self.ratio


    def _get_season_search_strings(self, ep_obj):

        search_string = {'Season': []}
        for show_name in set(show_name_helpers.allPossibleShowNames(self.show)):
            if ep_obj.show.air_by_date or ep_obj.show.sports:
                ep_string = show_name + '.' + str(ep_obj.airdate).split('-')[0]
            elif ep_obj.show.anime:
                ep_string = show_name + '.' + "%d" % ep_obj.scene_absolute_number
            else:
                ep_string = show_name + '.S%02d' % int(ep_obj.scene_season)  # 1) showName.SXX

            search_string['Season'].append(ep_string)

        return [search_string]

class FrenchTorrentDBAuth(AuthBase):
    """Attaches HTTP Authentication to the given Request object."""
    def __init__(self, token):
        self.token = token

    def __call__(self, r):
        r.headers['Authorization'] = self.token
        return r


class FrenchTorrentDBCache(tvcache.TVCache):
    def __init__(self, provider):
        tvcache.TVCache.__init__(self, provider)

        # Only poll FTDB every 10 minutes max
        self.minTime = 10

    def _getRSSData(self):
        search_strings = {'RSS': ['']}
        return {'entries': self.provider._doSearch(search_strings)}

provider = FrenchTorrentDBProvider()
