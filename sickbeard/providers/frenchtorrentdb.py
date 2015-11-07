# Authors: Yannick Croissant <yannick.croissant@gmail.com>
#          adaur <adaur.underground@gmail.com>
# URL: http://code.google.com/p/sickbeard/
#
# This file is part of SickRage.
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
from sickbeard.providers import generic

from sickbeard.bs4_parser import BS4Parser
from sickbeard import logger
from sickbeard import tvcache

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

        self.username = None
        self.password = None
        self.ratio = None
        self.minseed = None
        self.minleech = None

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

    def _doSearch(self, search_strings, search_mode='eponly', epcount=0, age=0, epObj=None):

        results = []
        items = {'Season': [], 'Episode': [], 'RSS': []}

        # check for auth
        if not self._doLogin():
            return results

        for mode in search_strings.keys():
            logger.log(u"Search Mode: %s" % mode, logger.DEBUG)
            for search_string in search_strings[mode]:

                if mode is not 'RSS':
                    logger.log(u"Search string: %s " % search_string, logger.DEBUG)

                self.search_params['name'] = search_string

                r = self.getURL(self.url, params=self.search_params)
                with BS4Parser(r, features=["html5lib", "permissive"]) as html:
                    resultsTable = html.find("div", {"class": "DataGrid"})

                    if resultsTable:
                        rows = resultsTable.findAll("ul")

                        for row in rows:
                            link = row.find("a", title=True)
                            title = link['title']
                            # FIXME
                            size = -1
                            seeders = 1
                            leechers = 0

                            autogetURL = self.url + '/' + (row.find("li", {"class": "torrents_name"}).find('a')['href'][1:]).replace('#FTD_MENU', '&menu=4')
                            r = self.getURL(autogetURL)
                            with BS4Parser(r, features=["html5lib", "permissive"]) as html:

                                download_url = html.find("div", {"class" : "autoget"}).find('a')['href']

                                if not all([title, download_url]):
                                    continue

                                # Filter unseeded torrent
                                # if seeders < self.minseed or leechers < self.minleech:
                                #    if mode is not 'RSS':
                                #        logger.log(u"Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format(title, seeders, leechers), logger.DEBUG)
                                #    continue

                                item = title, download_url, size, seeders, leechers
                                if mode is not 'RSS':
                                    logger.log(u"Found result: %s " % title, logger.DEBUG)

                                items[mode].append(item)

            # For each search mode sort all the items by seeders if available
            items[mode].sort(key=lambda tup: tup[3], reverse=True)

            results += items[mode]

        return results

    def seedRatio(self):
        return self.ratio


class FrenchTorrentDBCache(tvcache.TVCache):
    def __init__(self, provider_obj):
        tvcache.TVCache.__init__(self, provider_obj)

        # Only poll FTDB every 10 minutes max
        self.minTime = 10

    def _getRSSData(self):
        search_strings = {'RSS': ['']}
        return {'entries': self.provider._doSearch(search_strings)}

provider = FrenchTorrentDBProvider()
