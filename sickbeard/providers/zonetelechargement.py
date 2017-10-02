# coding=utf-8
# Author: djoole <bobby.djoole@gmail.com>
#
# URL: https://sickrage.github.io
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage. If not, see <http://www.gnu.org/licenses/>.

import time
import traceback
import re

from sickbeard import logger, tvcache
from sickbeard.common import USER_AGENT
from sickrage.helper.common import try_int
from sickrage.helper.common import convert_size
from sickrage.providers.ddl.DDLProvider import DDLProvider
from sickbeard.bs4_parser import BS4Parser

class ZoneTelechargementProvider(DDLProvider):  # pylint: disable=too-many-instance-attributes

    def __init__(self):

        DDLProvider.__init__(self, "ZoneTelechargement")

        self.cache = tvcache.TVCache(self, min_time=0)  # Only poll ZoneTelechargement every 10 minutes max

        self.urls = {'base_url': 'https://www.zone-telechargement.ws',
                     'search': 'https://www.zone-telechargement.ws/index.php?do=search',
                     'rss': 'https://www.zone-telechargement.ws/rss.xml'}

        self.url = self.urls['base_url']

        self.headers.update({'User-Agent': USER_AGENT})

        self.storageProviderAllow = {}


        self.titleVersion = {
            'vostfr': {
                'keywords': ["vostfr", "hdtv"],
                'suffix': 'VOSTFR.HDTV'
            },
            'vf': {
                'keywords': ["french", "hdtv"],
                'suffix': 'FRENCH.HDTV'
            },
            'vostfr-hd': {
                'keywords': ["720p","vostfr"],
                'suffix': 'VOSTFR.720P.HDTV.x264'
            },
            'vf-hd': {
                'keywords': ["french", "720p"],
                'suffix': 'FRENCH.720P.HDTV.x264'
            },
            'vostfr-1080p': {
                'keywords': ["vostfr", "hd1080p"],
                'suffix': 'VOSTFR.1080P.HDTV.x264'
            },
            'vf-1080p': {
                'keywords': ["french", "hd1080p"],
                'suffix': 'FRENCH.1080P.HDTV.x264'
            }
        }

    def getTitleVersion(self, x):
        return titleVersion.get(x, '')

    def canUseProvider(self, data):
        for key,value in self.storageProviderAllow.items():
            if key == data and value:
                return True
        return False


    def search(self, search_params, age=0, ep_obj=None):  # pylint: disable=too-many-branches, too-many-locals, too-many-statements
        results = []

        for mode in search_params:
            # Don't support RSS
            if mode == 'RSS':
                continue

            items = []

            logger.log(u"Search Mode: {0}".format(mode), logger.DEBUG)

            for search_string in search_params[mode]:
                    
                detectSeasonEpisode = re.search('(\d{1,2})[^\d]{1,2}(\d{1,2})(?:[^\d]{1,2}(\d{1,2}))?.*', search_string)
                seasonVersion = detectSeasonEpisode.group(1)
                episodeVersion = detectSeasonEpisode.group(2)

                search_string_for_url = search_string.replace(search_string.split(" ")[-1],"")

                logger.log(u"Search string: {0}".format
                           (search_string.decode("utf-8")), logger.DEBUG)

                logger.log(u"search_string_for_url: {0}".format
                           (search_string_for_url.decode("utf-8")), logger.DEBUG)

                # #HEADER BYPASS
                # dataPage = self.get_url("https://www.zone-telechargement.ws/telecharger-series/26988-telecharger-game-of-thrones-saison-7-vostfr-hdtv-6vbrh4y7el25.html", verify=False)
                # with BS4Parser(dataPage, 'html5lib') as htmlPage:

                #     #BYPASS HERE

                #     #TRYHARD DATA*
                #     url = "https://www.zone-telechargement.ws/telecharger-series/26988-telecharger-game-of-thrones-saison-7-vostfr-hdtv-6vbrh4y7el25.html"
                #     for key, tv in self.titleVersion.items():
                #         if any(keyword in url for keyword in tv["keywords"]):
                #             title = search_string.replace(" ",".") +"."+ tv["suffix"]
                #             break;


                #     content_page = htmlPage(class_=re.compile('postinfo'))
                #     bTags = content_page[0].find_all('b')
                #     providerDDLName = ""
                #     for bTag in bTags:
                #         if self.canUseProvider(bTag.text):
                #             providerDDLName = bTag.text

                #         if  self.canUseProvider(providerDDLName) and \
                #             bTag.text.startswith("Episode "+str(int(episodeVersion))):
                #             providerDDLLink = bTag.find_all('a')[0]['href']
                #             logger.log(providerDDLName, logger.DEBUG)
                #             logger.log(providerDDLLink, logger.DEBUG)

                #             item = {'title': title, 'link': providerDDLLink}
                #             items.append(item)
                #             providerDDLName = ""
                
                # continue
                # END

                search_urlS = [self.urls['search']]
                for search_url in search_urlS:

                    data = {}
                    data["do"] = "search"
                    data["subaction"] = "search"
                    data["story"] = search_string_for_url

                    dataSearch = self.get_url(search_url, post_data=data)
                    #dataSearch = self.get_url(search_url, verify=False)
                    if not dataSearch:
                        continue

                    with BS4Parser(dataSearch, 'html5lib') as html:
                        serie_rows = html(class_=re.compile('cover_infos_title'))

                        for result_rows in serie_rows:
                            try:
                                links_page = result_rows.find_all('a')
                                logger.log(links_page[0].get('href'), logger.DEBUG)
                                
                                seasonNameDetect = links_page[0].get_text()
                                if not seasonNameDetect.find("Saison "+str(int(seasonVersion))) >= 0:
                                    continue

                                dataPage = self.get_url(links_page[0].get('href'), verify=False)
                                with BS4Parser(dataPage, 'html5lib') as htmlPage:
                                    url = links_page[0].get('href')
                                    for key, tv in self.titleVersion.items():
                                        if all(keyword in url for keyword in tv["keywords"]):
                                            title = search_string.replace(" ",".") +"."+ tv["suffix"]
                                            break;

                                    content_page = htmlPage(class_=re.compile('postinfo'))
                                    bTags = content_page[0].find_all('b')
                                    providerDDLName = ""
                                    for bTag in bTags:
                                        if self.canUseProvider(bTag.text):
                                            providerDDLName = bTag.text

                                        if  self.canUseProvider(providerDDLName) and \
                                            bTag.text.startswith("Episode "+str(int(episodeVersion))):
                                            providerDDLLink = bTag.find_all('a')[0]['href']
                                            logger.log(providerDDLName, logger.DEBUG)
                                            logger.log(title, logger.DEBUG)
                                            logger.log(providerDDLLink, logger.DEBUG)

                                            item = {'title': title, 'link': providerDDLLink}
                                            items.append(item)
                                            providerDDLName = ""



                                    # OLD
                                    # matchesProviderDDL = re.finditer('(<span style="color:.*?>(.*?)</span>)(.*?)(<br/><br/>|<br/></b>)', str(content_page), re.MULTILINE | re.IGNORECASE)
                                    # for matchNum, providerDDL in enumerate(matchesProviderDDL):
                                    #     if len(providerDDL.groups()) <= 3:
                                    #         continue

                                    #     providerDDLName = providerDDL.group(2)
                                    #     providerDDLHrefRaw = providerDDL.group(3)

                                    #     matchesLinks = re.finditer('<a\s+(?:[^>]*?\s+)?href="([^"]*)"[^>]*?>(.*?)<', providerDDLHrefRaw)
                                    #     for matchNum, linksMatched in enumerate(matchesLinks):
                                    #         providerDDLLink = linksMatched.group(1)
                                    #         providerDDLEpisode = linksMatched.group(2)

                                    #         if providerDDLName in self.storageProviderAllow and \
                                    #         self.storageProviderAllow[providerDDLName] == 1 and \
                                    #         providerDDLEpisode.startswith("Episode "+str(int(episodeVersion))):
                                    #             logger.log(providerDDLName, logger.DEBUG)
                                    #             logger.log(providerDDLLink, logger.DEBUG)

                                    #             item = {'title': title, 'link': providerDDLLink}
                                    #             items.append(item)
                            except Exception:
                                logger.log(u'Failed doing webui callback: {0}'.format((traceback.format_exc())), logger.ERROR)
            results += items

        return results

provider = ZoneTelechargementProvider()
