# Author: Dieter Blomme <dieterblomme@gmail.com>
# URL: http://code.google.com/p/sickbeard/
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

import sickbeard
from sickbeard import logger
from sickbeard.exceptions import ex
from lib.trakt import TraktAPI
from lib.trakt.exceptions import traktException, traktServerBusy, traktAuthException

class TraktNotifier:
    """
    A "notifier" for trakt.tv which keeps track of what has and hasn't been added to your library.
    """

    def notify_snatch(self, ep_name):
        pass

    def notify_download(self, ep_name):
        pass

    def notify_subtitle_download(self, ep_name, lang):
        pass

    def notify_git_update(self, new_version):
        pass

    def update_library(self, ep_obj):
        """
        Sends a request to trakt indicating that the given episode is part of our library.
        
        ep_obj: The TVEpisode object to add to trakt
        """

        trakt_id = sickbeard.indexerApi(ep_obj.show.indexer).config['trakt_id']
        trakt_api = TraktAPI(sickbeard.TRAKT_API, sickbeard.TRAKT_USERNAME, sickbeard.TRAKT_PASSWORD)

        if sickbeard.USE_TRAKT:
            try:
                # URL parameters
                data = {
                    'title': ep_obj.show.name,
                    'year': ep_obj.show.startyear,
                    'episodes': [{
                                     'season': ep_obj.season,
                                     'episode': ep_obj.episode
                                 }]
                }

                if trakt_id == 'tvdb_id':
                    data[trakt_id] = ep_obj.show.indexerid

                # update library
                trakt_api.traktRequest("show/episode/library/%APIKEY%", data, method='POST')

                # remove from watchlist
                if sickbeard.TRAKT_REMOVE_WATCHLIST:
                    trakt_api.traktRequest("show/episode/unwatchlist/%APIKEY%", data, method='POST')

                if sickbeard.TRAKT_REMOVE_SERIESLIST:
                    data = {
                        'shows': [
                            {
                                'title': ep_obj.show.name,
                                'year': ep_obj.show.startyear
                            }
                        ]
                    }

                    if trakt_id == 'tvdb_id':
                        data['shows'][0][trakt_id] = ep_obj.show.indexerid

                    trakt_api.traktRequest("show/unwatchlist/%APIKEY%", data, method='POST')

                    # Remove all episodes from episode watchlist
                    # Start by getting all episodes in the watchlist
                    watchlist = trakt_api.traktRequest("user/watchlist/episodes.json/%APIKEY%/%USER%")

                    # Convert watchlist to only contain current show
                    if watchlist:
                        for show in watchlist:
                            if show[trakt_id] == ep_obj.show.indexerid:
                                data_show = {
                                    'title': show['title'],
                                    trakt_id: show[trakt_id],
                                    'episodes': []
                                }

                                # Add series and episode (number) to the array
                                for episodes in show['episodes']:
                                    ep = {'season': episodes['season'], 'episode': episodes['number']}
                                    data_show['episodes'].append(ep)

                                trakt_api.traktRequest("show/episode/unwatchlist/%APIKEY%", data_show, method='POST')
            except (traktException, traktAuthException, traktServerBusy) as e:
                logger.log(u"Could not connect to Trakt service: %s" % ex(e), logger.WARNING)

    def test_notify(self, api, username, password):
        """
        Sends a test notification to trakt with the given authentication info and returns a boolean
        representing success.
        
        api: The api string to use
        username: The username to use
        password: The password to use
        
        Returns: True if the request succeeded, False otherwise
        """

        trakt_api = TraktAPI(api, username, password)

        try:
            if trakt_api.validateAccount():
                return "Test notice sent successfully to Trakt"
        except (traktException, traktAuthException, traktServerBusy) as e:
            logger.log(u"Could not connect to Trakt service: %s" % ex(e), logger.WARNING)

        return "Test notice failed to Trakt: %s" % ex(e)

notifier = TraktNotifier
