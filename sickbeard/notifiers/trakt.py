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

from libtrakt import TraktAPI
from libtrakt.exceptions import traktException, traktServerBusy, traktAuthException

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
        trakt_api = TraktAPI(sickbeard.SSL_VERIFY, sickbeard.TRAKT_TIMEOUT)

        if sickbeard.USE_TRAKT:
            try:
                # URL parameters
                data = {
                    'shows': [
                        {
                            'title': ep_obj.show.name,
                            'year': ep_obj.show.startyear,
                            'ids': {},
                        }
                    ]
                }

                if trakt_id == 'tvdb_id':
                    data['shows'][0]['ids']['tvdb'] = ep_obj.show.indexerid
                else:
                    data['shows'][0]['ids']['tvrage'] = ep_obj.show.indexerid

                if sickbeard.TRAKT_SYNC_WATCHLIST:
                    if sickbeard.TRAKT_REMOVE_SERIESLIST:
                        trakt_api.traktRequest("sync/watchlist/remove", data, method='POST')

                # Add Season and Episode + Related Episodes
                data['shows'][0]['seasons']=[{'number': ep_obj.season,'episodes': [] }]

                for relEp_Obj in [ep_obj] + ep_obj.relatedEps:
                    data['shows'][0]['seasons'][0]['episodes'].append({'number': relEp_Obj.episode})

                if sickbeard.TRAKT_SYNC_WATCHLIST:
                    if sickbeard.TRAKT_REMOVE_WATCHLIST:
                        trakt_api.traktRequest("sync/watchlist/remove", data, method='POST')

                # update library
                trakt_api.traktRequest("sync/collection", data, method='POST')

            except (traktException, traktAuthException, traktServerBusy) as e:
                logger.log(u"Could not connect to Trakt service: %s" % ex(e), logger.WARNING)

    def update_watchlist (self, show_obj = None, s = None, e = None, data_show = None, data_episode = None, update = "add"):

        """
        Sends a request to trakt indicating that the given episode is part of our library.

        show_obj: The TVShow object to add to trakt
        s: season number
        e: episode number
        data_show: structured object of shows traktv type
        data_episode: structured object of episodes traktv type
        update: type o action add or remove
        """

        trakt_api = TraktAPI(sickbeard.SSL_VERIFY, sickbeard.TRAKT_TIMEOUT)

        if sickbeard.USE_TRAKT:

            data = {}
            try:
                # URL parameters
                if show_obj is not None:
                    trakt_id = sickbeard.indexerApi(show_obj.indexer).config['trakt_id']
                    data = {
                        'shows': [
                            {
                                'title': show_obj.name,
                                'year': show_obj.startyear,
                                'ids': {},
                            }
                        ]
                     }

                    if trakt_id == 'tvdb_id':
                        data['shows'][0]['ids']['tvdb'] = show_obj.indexerid
                    else:
                        data['shows'][0]['ids']['tvrage'] = show_obj.indexerid
                elif data_show is not None:
                    data.update(data_show)
                else:
                    logger.log(u"there's a coding problem contact developer. It's needed to be provided at lest one of the two: data_show or show_obj", logger.WARNING)
                    return False

                if data_episode is not None:
                    data['shows'][0].update(data_episode)

                elif s is not None:
                    # traktv URL parameters
                    season = {
                        'season': [
                            {
                                'number': s,
                            }
                        ]
                     }

                    if e is not None:
                        # traktv URL parameters
                        episode = {
                            'episodes': [
                                {
                                    'number': e
                                }
                            ]
                         }

                        season['season'][0].update(episode)

                    data['shows'][0].update(season)

                trakt_url = "sync/watchlist"
                if update=="remove":
                    trakt_url += "/remove"

                trakt_api.traktRequest(trakt_url, data, method='POST')

            except (traktException, traktAuthException, traktServerBusy) as e:
                logger.log(u"Could not connect to Trakt service: %s" % ex(e), logger.WARNING)
                return False

        return True

    def trakt_show_data_generate(self, data):

        showList = []
        for indexer, indexerid, title, year in data:
            trakt_id = sickbeard.indexerApi(indexer).config['trakt_id']
            show = {'title': title, 'year': year, 'ids': {}}
            if trakt_id == 'tvdb_id':
                show['ids']['tvdb'] = indexerid
            else:
                show['ids']['tvrage'] = indexerid
            showList.append(show)

        post_data = {'shows': showList}

        return post_data

    def trakt_episode_data_generate(self, data):

        # Find how many unique season we have
        uniqueSeasons = []
        for season, episode in data:
            if season not in uniqueSeasons:
                uniqueSeasons.append(season)

        #build the query
        seasonsList = []
        for searchedSeason in uniqueSeasons:
            episodesList = []
            for season, episode in data:
                if season == searchedSeason:
                    episodesList.append({'number': episode})
            seasonsList.append({'number': searchedSeason, 'episodes': episodesList})

        post_data = {'seasons': seasonsList}

        return post_data

    def test_notify(self, username, blacklist_name=None):
        """
        Sends a test notification to trakt with the given authentication info and returns a boolean
        representing success.

        api: The api string to use
        username: The username to use
        blacklist_name: slug of trakt list used to hide not interested show

        Returns: True if the request succeeded, False otherwise
        """
        try:
            trakt_api = TraktAPI(sickbeard.SSL_VERIFY, sickbeard.TRAKT_TIMEOUT)
            trakt_api.validateAccount()
            if blacklist_name and blacklist_name is not None:
                trakt_lists = trakt_api.traktRequest("users/" + username + "/lists")
                found = False
                for trakt_list in trakt_lists:
                    if (trakt_list['ids']['slug'] == blacklist_name):
                        return "Test notice sent successfully to Trakt"
                if not found:
                    return "Trakt blacklist doesn't exists"
            else:
                return "Test notice sent successfully to Trakt"
        except (traktException, traktAuthException, traktServerBusy) as e:
            logger.log(u"Could not connect to Trakt service: %s" % ex(e), logger.WARNING)
            return "Test notice failed to Trakt: %s" % ex(e)

notifier = TraktNotifier
