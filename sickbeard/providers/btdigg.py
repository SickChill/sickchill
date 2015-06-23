# Author: Jodi Jones <venom@gen-x.co.nz>
# URL: http://code.google.com/p/sickbeard/
#
#Ported to sickrage by: matigonkas
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
#  GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Sick Beard.  If not, see <http://www.gnu.org/licenses/>.

import re
import requests
import sys
import datetime
import os
import exceptions
import sickbeard
import generic
import json

from operator import itemgetter
from xml.sax.saxutils import escape
from sickbeard.common import Quality
from sickbeard import logger
from sickbeard import tvcache
from sickbeard import helpers
from sickbeard import show_name_helpers
from sickbeard import db
from sickbeard.common import Overview
from sickbeard.exceptions import ex

class BTDIGGProvider(generic.TorrentProvider):
    def __init__(self):
		generic.TorrentProvider.__init__(self, "BTDigg")
		
		self.supportsBacklog = True
		self.url = 'https://api.btdigg.org/'
		
    def isEnabled(self):
        return self.enabled
   
   
    def imageName(self):
        return 'btdigg.png'
   

    def _get_airbydate_season_range(self, season):       
        if season == None:
            return ()       
        year, month = map(int, season.split('-'))
        min_date = datetime.date(year, month, 1)
        if month == 12:
            max_date = datetime.date(year, month, 31)
        else:   
            max_date = datetime.date(year, month+1, 1) -  datetime.timedelta(days=1)
        return (min_date, max_date)   


    def _get_season_search_strings(self, show, season=None):
        search_string = []
   
        if not show:
            return []
     
        myDB = db.DBConnection()
       
        if show.air_by_date:
            (min_date, max_date) = self._get_airbydate_season_range(season)
            sqlResults = myDB.select("SELECT * FROM tv_episodes WHERE showid = ? AND airdate >= ? AND airdate <= ?", [show.tvdbid,  min_date.toordinal(), max_date.toordinal()])
        else:
            sqlResults = myDB.select("SELECT * FROM tv_episodes WHERE showid = ? AND season = ?", [show.tvdbid, season])
           
        for sqlEp in sqlResults:
            if show.getOverview(int(sqlEp["status"])) in (Overview.WANTED, Overview.QUAL):
                if show.air_by_date:
                    for show_name in set(show_name_helpers.allPossibleShowNames(show)):
                        ep_string = show_name_helpers.sanitizeSceneName(show_name) +' '+ str(datetime.date.fromordinal(sqlEp["airdate"])).replace('-', '.')
                        search_string.append(ep_string)
                else:
                    for show_name in set(show_name_helpers.allPossibleShowNames(show)):
                        ep_string = show_name_helpers.sanitizeSceneName(show_name) +' '+ sickbeard.config.naming_ep_type[2] % {'seasonnumber': season, 'episodenumber': int(sqlEp["episode"])}
                        search_string.append(ep_string)                      
        return search_string


    def _get_episode_search_strings(self, ep_obj, add_string=''):
       
        search_string = []
      
        if not ep_obj:
            return []
        if ep_obj.show.air_by_date:
            for show_name in set(show_name_helpers.allPossibleShowNames(ep_obj.show)):
                ep_string = show_name_helpers.sanitizeSceneName(show_name) +' '+ str(ep_obj.airdate).replace('-', '.')
		if len(add_string):
			ep_string += ' %s' % add_string

                search_string.append(ep_string)

        else:
            for show_name in set(show_name_helpers.allPossibleShowNames(ep_obj.show)):
                ep_string = show_name_helpers.sanitizeSceneName(show_name) +' '+ sickbeard.config.naming_ep_type[2] % {'seasonnumber': ep_obj.season, 'episodenumber': ep_obj.episode}
		if len(add_string):
			ep_string += ' %s' % add_string
                search_string.append(ep_string)
        return search_string   

    def _doSearch(self, search_params, searchUrl, search_mode='eponly', epcount=0, age=0, epObj=None):
		search_params = search_params.replace('+',' ')
		logger.log("Performing Search: {0}".format(search_params))
		searchUrl = self.url + "api/private-341ada3245790954/s02?q=" + search_params + "&p=0&order=0"
		logger.log("Performing Search on URL: {0}".format(searchUrl))
		return self.parseResults(searchUrl)
   

    def _get_title_and_url(self, item):
        return item
   
    def parseResults(self, searchUrl):
		jdata = self.getURL(searchUrl, json=True)
		results=[]
		tmp_results=[]
		if jdata:
			logger.log("URL to be parsed: " + searchUrl, logger.DEBUG)
			for torrent in sorted(jdata, key=itemgetter('reqs'), reverse=True):
				found=0
               
				if torrent['ff'] > 0.0:
					continue
                              
				torrent['name'] = torrent['name'].replace('|', '.').replace(' ','.').replace('_','.')
               
				item = (torrent['name'],torrent['magnet'], torrent['reqs'])               
				for r in tmp_results:
					if r[0].lower() == torrent['name'].lower():
						found=1
						if r[2] < torrent['reqs']:
							tmp_results[tmp_results.index(r)]=item
                           
				if not found:
					tmp_results.append(item)
				logger.log("Parsed Result Title: " + torrent['name'], logger.DEBUG)
           
			for r in tmp_results:
				item=(r[0],r[1])
				results.append(item)
		else:
			logger.log("No data returned to be parsed!!!")
		return results


provider = BTDIGGProvider()