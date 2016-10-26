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

        self.urls = {'base_url': 'https://www.zone-telechargement.com',
                     'search': 'https://www.zone-telechargement.com/telecharger-series.html?q=%s&displaychangeto=list',
                     'rss': 'https://www.zone-telechargement.com/rss.xml'}

        self.url = self.urls['base_url']

        self.headers.update({'User-Agent': USER_AGENT})

        self.storageProviderAllow = {
            'Uptobox': False,
            'Uplea': False,
            '1fichier': False,
            'Uploaded': False,
            'Rapidgator': False,
            'TurboBit': False
        }


    def convertTitleVersion(self, x):
        return {
            'vostfr': 'VOSTFR.HDTV',
            'vf': 'FRENCH.HDTV',
            'vostfr-hd':'VOSTFR.720P.HDTV.x264',
            'vf-hd': 'FRENCH.720P.HDTV.x264',
            'vostfr-1080p': 'VOSTFR.1080P.HDTV.x264',
            'vf-1080p': 'FRENCH.1080P.HDTV.x264'
        }.get(x, '')

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

                search_urlS = [self.urls['search'] % search_string_for_url]
                for search_url in search_urlS:

                    dataSearch = self.get_url(search_url, verify=False)
                    if not dataSearch:
                        continue

                    with BS4Parser(dataSearch, 'html5lib') as html:
                        serie_rows = html(class_=re.compile('listnews'))

                        for result_rows in serie_rows:
                            try:
                                links_page = result_rows.find_all('a')
                                logger.log(links_page[0].get('href'), logger.DEBUG)
                                
                                seasonNameDetect = links_page[0].get_text()
                                if not seasonNameDetect.find("Saison "+str(int(seasonVersion))) >= 0:
                                    continue

                                dataPage = self.get_url(links_page[0].get('href'), verify=False)

                                with BS4Parser(dataPage, 'html5lib') as htmlPage:

                                     # TODO
                                    # Parse 'Nom de la release' to get real name
                                    finalUrl = htmlPage.find(attrs={"rel":"canonical"}).get('href')
                                    titleVersion = re.search('.*zone-telechargement.com\/series\/(.*)/.*', finalUrl).group(1)
                                    title = search_string.replace(" ",".") +"."+ self.convertTitleVersion(titleVersion)

                                    content_page = htmlPage(class_=re.compile('contentl'))

                                    matchesProviderDDL = re.finditer('(<span style="color:.*?>(.*?)</span>)(.*?)(<br/><br/>|<br/></b>)', str(content_page), re.MULTILINE | re.IGNORECASE)
                                    for matchNum, providerDDL in enumerate(matchesProviderDDL):
                                        if len(providerDDL.groups()) <= 3:
                                            continue

                                        providerDDLName = providerDDL.group(2)
                                        providerDDLHrefRaw = providerDDL.group(3)

                                        matchesLinks = re.finditer('<a\s+(?:[^>]*?\s+)?href="([^"]*)"[^>]*?>(.*?)<', providerDDLHrefRaw)
                                        for matchNum, linksMatched in enumerate(matchesLinks):
                                            providerDDLLink = linksMatched.group(1)
                                            providerDDLEpisode = linksMatched.group(2)

                                            if providerDDLName in self.storageProviderAllow and \
                                            self.storageProviderAllow[providerDDLName] == 1 and \
                                            providerDDLEpisode.startswith("Episode "+str(int(episodeVersion))):
                                                logger.log(providerDDLName, logger.DEBUG)
                                                logger.log(providerDDLLink, logger.DEBUG)

                                                item = {'title': title, 'link': providerDDLLink}
                                                items.append(item)
                            except Exception:
                                logger.log(u'Failed doing webui callback: {0}'.format((traceback.format_exc())), logger.ERROR)
            results += items

        return results

provider = ZoneTelechargementProvider()
