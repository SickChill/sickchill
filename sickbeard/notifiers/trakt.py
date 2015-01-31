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
        trakt_api = TraktAPI(sickbeard.TRAKT_API_KEY, sickbeard.TRAKT_USERNAME, sickbeard.TRAKT_PASSWORD, sickbeard.TRAKT_DISABLE_SSL_VERIFY, sickbeard.TRAKT_TIMEOUT)

        if sickbeard.USE_TRAKT:
            try:
                # URL parameters
                data = {
                    'shows': [
                        {
                            'title': ep_obj.show.name,
                            'year': ep_obj.show.startyear,
                            'ids': {},
                            'seasons': [
                                {
                                    'number': ep_obj.season,
                                    'episodes': [
                                        {
                                            'number': ep_obj.episode
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                }

                if trakt_id == 'tvdb_id':
                    data['shows'][0]['ids']['tvdb'] = ep_obj.show.indexerid
                else:
                    data['shows'][0]['ids']['tvrage'] = ep_obj.show.indexerid

                # update library
                trakt_api.traktRequest("sync/collection", data, method='POST')

                # remove from watchlist
                if sickbeard.TRAKT_REMOVE_WATCHLIST:
                    trakt_api.traktRequest("sync/watchlist/remove", data, method='POST')

                if sickbeard.TRAKT_REMOVE_SERIESLIST:
                    data = {
                        'shows': [
                            {
                                'title': ep_obj.show.name,
                                'year': ep_obj.show.startyear,
                                'ids': {}
                            }
                        ]
                    }

                    if trakt_id == 'tvdb_id':
                        data['shows'][0]['ids']['tvdb'] = ep_obj.show.indexerid
                    else:
                        data['shows'][0]['ids']['tvrage'] = ep_obj.show.indexerid

                    trakt_api.traktRequest("sync/watchlist/remove", data, method='POST')

            except (traktException, traktAuthException, traktServerBusy) as e:
                logger.log(u"Could not connect to Trakt service: %s" % ex(e), logger.WARNING)

    def test_notify(self, username, password, disable_ssl):
        """
        Sends a test notification to trakt with the given authentication info and returns a boolean
        representing success.

        api: The api string to use
        username: The username to use
        password: The password to use

        Returns: True if the request succeeded, False otherwise
        """
        try:
            trakt_api = TraktAPI(sickbeard.TRAKT_API_KEY, username, password, disable_ssl, sickbeard.TRAKT_TIMEOUT)
            trakt_api.validateAccount()
            return "Test notice sent successfully to Trakt"
        except (traktException, traktAuthException, traktServerBusy) as e:
            logger.log(u"Could not connect to Trakt service: %s" % ex(e), logger.WARNING)
            return "Test notice failed to Trakt: %s" % ex(e)

notifier = TraktNotifier
