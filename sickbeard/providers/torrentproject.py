# Author: duramato <matigonkas@outlook.com>
# URL: https://github.com/SiCKRAGETV/sickrage
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

from urllib import quote_plus

from sickbeard import logger
from sickbeard import tvcache
from sickbeard import helpers
from sickbeard.providers import generic
from sickbeard.common import USER_AGENT

class TORRENTPROJECTProvider(generic.TorrentProvider):

    def __init__(self):
        generic.TorrentProvider.__init__(self, "TorrentProject")

        self.supportsBacklog = True
        self.public = True

        self.urls = {'api': u'https://torrentproject.se/',}
        self.url = self.urls['api']
        self.headers.update({'User-Agent': USER_AGENT})
        self.minseed = None
        self.minleech = None
        self.cache = TORRENTPROJECTCache(self)

    def isEnabled(self):
        return self.enabled

    def _doSearch(self, search_strings, search_mode='eponly', epcount=0, age=0, epObj=None):

        results = []
        items = {'Season': [], 'Episode': [], 'RSS': []}

        for mode in search_strings.keys(): #Mode = RSS, Season, Episode
            logger.log(u"Search Mode: %s" % mode, logger.DEBUG)
            for search_string in search_strings[mode]:
                if mode != 'RSS':
                    logger.log(u"Search string: %s " % search_string, logger.DEBUG)


                searchURL = self.urls['api'] + "?s=%s&out=json&filter=2101&num=150" % quote_plus(search_string.encode('utf-8'))

                logger.log(u"Search URL: %s" %  searchURL, logger.DEBUG)
                torrents = self.getURL(searchURL, json=True)
                if not (torrents and "total_found" in torrents and int(torrents["total_found"]) > 0):
                    logger.log(u"Data returned from provider does not contain any torrents", logger.DEBUG)
                    continue

                del torrents["total_found"]

                results = []
                for i in torrents:
                    title = torrents[i]["title"]
                    seeders = helpers.tryInt(torrents[i]["seeds"], 1)
                    leechers = helpers.tryInt(torrents[i]["leechs"], 0)
                    if seeders < self.minseed or leechers < self.minleech:
                        if mode != 'RSS':
                            logger.log("Torrent doesn't meet minimum seeds & leechers not selecting : %s" % title, logger.DEBUG)
                        continue

                    t_hash = torrents[i]["torrent_hash"]
                    size = int(torrents[i]["torrent_size"])

                    if seeders < 10:
                        if mode != 'RSS':
                            logger.log("Torrent has less than 10 seeds getting dyn trackers: " + title, logger.DEBUG)
                            trackerUrl = self.urls['api'] + "" + t_hash + "/trackers_json"
                            jdata = self.getURL(trackerUrl, json=True)
                            if jdata == "maintenance":
                                download_url = "magnet:?xt=urn:btih:" + t_hash + "&dn=" + title + "&tr=udp://tracker.openbittorrent.com:80&tr=udp://tracker.coppersurfer.tk:6969&tr=udp://open.demonii.com:1337&tr=udp://tracker.leechers-paradise.org:6969&tr=udp://exodus.desync.com:6969"
                                logger.log("Tracker url is in " + jdata + " mode, using hardcoded one" , logger.INFO)
                            else:
                                download_url = "magnet:?xt=urn:btih:" + t_hash + "&dn=" + title + "".join(["&tr=" + s for s in jdata])
                                logger.log("Dyn Magnet: " + download_url, logger.DEBUG)
                        else:
                            download_url = "magnet:?xt=urn:btih:" + t_hash + "&dn=" + title + "&tr=udp://tracker.openbittorrent.com:80&tr=udp://tracker.coppersurfer.tk:6969&tr=udp://open.demonii.com:1337&tr=udp://tracker.leechers-paradise.org:6969&tr=udp://exodus.desync.com:6969"
                            logger.log("Result has less than 10 seeds but not using Dyn Magnet becouse its from RSS" + title, logger.DEBUG)
                    else:
                        #logger.log("Torrent has more than 10 seeds using hard coded trackers", logger.DEBUG)
                        download_url = "magnet:?xt=urn:btih:" + t_hash + "&dn=" + title + "&tr=udp://tracker.openbittorrent.com:80&tr=udp://tracker.coppersurfer.tk:6969&tr=udp://open.demonii.com:1337&tr=udp://tracker.leechers-paradise.org:6969&tr=udp://exodus.desync.com:6969"


                    if not all([title, download_url]):
                        continue

                    item = title, download_url, size, seeders, leechers

                    if mode != 'RSS':
                        logger.log(u"Found result: %s" % title, logger.DEBUG)

                    items[mode].append(item)

            # For each search mode sort all the items by seeders
            items[mode].sort(key=lambda tup: tup[3], reverse=True)

            results += items[mode]

        return results

class TORRENTPROJECTCache(tvcache.TVCache):
    def __init__(self, provider_obj):

        tvcache.TVCache.__init__(self, provider_obj)

        self.minTime = 20

    def _getRSSData(self):
        
        search_params = {'RSS': ['0day']}
        return {'entries': self.provider._doSearch(search_params)}

provider = TORRENTPROJECTProvider()
