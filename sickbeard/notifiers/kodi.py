# coding=utf-8

# Author: Dustyn Gibson <miigotu@gmail.com>
# URL: https://sickchill.github.io
#
# This file is part of SickChill.
#
# SickChill is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SickChill is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickChill. If not, see <http://www.gnu.org/licenses/>.

from __future__ import absolute_import, print_function, unicode_literals

# Stdlib Imports
from urllib2 import URLError

# Third Party Imports
from beekeeper.exceptions import RequestTimeout
from kodipydent import Kodi

# First Party Imports
import sickbeard
from sickbeard import common, logger


class Notifier(object):
    def __init__(self):
        self._connections = list()

    def setup(self, hosts=None, username=None, password=None):
        self._connections = []
        for host in (x.strip() for x in (hosts or sickbeard.KODI_HOST or '').split(",") if x.strip()):
            try:
                if ':' in host:
                    bare_host, port = host.split(':')
                    kodi = Kodi(bare_host, username or sickbeard.KODI_USERNAME, password or sickbeard.KODI_PASSWORD, port=port)
                else:
                    kodi = Kodi(host, username or sickbeard.KODI_USERNAME, password or sickbeard.KODI_PASSWORD)
                kodi.host = kodi.variables()['hostname']['value']
                kodi.name = kodi.Settings.GetSettingValue(setting="services.devicename")['result']['value']
                if kodi not in self._connections:
                    self._connections.append(kodi)
            except (URLError, RequestTimeout):
                pass
                # logger.log('Unable to connect to Kodi host as {0}, make sure the username and password is correct and that the http control is enabled'.format(host))

    @property
    def connections(self):
        if not self._connections:
            self.setup()
        return self._connections

    @connections.setter
    def connections(self, value):
        self._connections = value

    @staticmethod
    def success(result):
        try:
            return result['result'] == 'OK'
        except (AttributeError, KeyError, ValueError):
            print(result['error'])

        return False

    def _notify_kodi(self, message, title="SickChill", hosts=None, username=None, password=None, force=False, dest_app="KODI"):
        """Internal wrapper for the notify_snatch and notify_download functions

        Detects JSON-RPC version then branches the logic for either the JSON-RPC or legacy HTTP API methods.

        Args:
            message: Message body of the notice to send
            title: Title of the notice to send
            hosts: KODI webserver host:port
            username: KODI webserver username
            password: KODI webserver password
            force: Used for the Test method to override config saftey checks

        Returns:
            Returns a list results in the format of host:ip:result
            The result will either be 'OK' or False, this is used to be parsed by the calling function.

        """

        self.setup(hosts=hosts, username=username, password=password)
        results = dict()
        for connection in self.connections:
            logger.log("Sending {0} notification to '{1}' - {2}".format(dest_app, connection.host, message), logger.DEBUG)
            response = connection.GUI.ShowNotification(title=title.encode("utf-8"), message=message.encode("utf-8"), image=sickbeard.LOGO_URL)
            if response and response.get('result'):
                results[connection.host] = self.success(response)
            else:
                if sickbeard.KODI_ALWAYS_ON or force:
                    logger.log("Failed to send notification to {0} for '{1}', check configuration and try again.".format(dest_app, self.hostname(connection)),
                               logger.WARNING)
                results[connection.host] = False

        for host in [x.strip() for x in (hosts or sickbeard.KODI_HOST or '').split(",") if x.strip()]:
            if host not in results:
                results[host] = False

        return results

    def update_library(self, show_name=None):
        if not (sickbeard.USE_KODI and sickbeard.KODI_UPDATE_LIBRARY):
            return False

        if not sickbeard.KODI_HOST:
            logger.log("No KODI hosts specified, check your settings", logger.DEBUG)
            return False

        result = 0
        for connection in self.connections:
            try:
                logger.log("Updating KODI library on host: " + connection.host, logger.DEBUG)

                if show_name:
                    tvshowid = -1
                    path = ''

                    logger.log("Updating library in KODI for show " + show_name, logger.DEBUG)

                    # let's try letting kodi filter the shows
                    response = connection.VideoLibrary.GetTVShows(filter={"field": "title", "operator": "is", "value": show_name}, properties=["file"])
                    if response and "result" in response and "tvshows" in response["result"]:
                        shows = response["result"]["tvshows"]
                    else:
                        # fall back to retrieving the entire show list
                        response = connection.VideoLibrary.GetTVShows(properties=["file"])
                        if response and "result" in response and "tvshows" in response["result"]:
                            shows = response["result"]["tvshows"]
                        else:
                            logger.log("KODI: No tvshows in KODI TV show list", logger.DEBUG)
                            continue

                    for show in shows:
                        if ("label" in show and show["label"] == show_name) or ("title" in show and show["title"] == show_name):
                            tvshowid = show["tvshowid"]
                            path = show["file"]
                            break

                    del shows

                    # we didn't find the show (exact match), thus revert to just doing a full update if enabled
                    if tvshowid == -1:
                        logger.log('Exact show name not matched in KODI TV show list', logger.DEBUG)

                    if not path:
                        logger.log("No valid path found for " + show_name + " with ID: " + str(tvshowid) + " on " + connection.host, logger.WARNING)

                    if path and tvshowid != -1:
                        logger.log("KODI Updating " + show_name + " with ID: " + str(tvshowid) + " at " + path + " on " + connection.host, logger.DEBUG)
                        response = connection.VideoLibrary.Scan(directory=path)
                        if not self.success(response):
                            logger.log("Update of show directory failed on " + show_name + " on " + connection.host + " at " + path, logger.WARNING)
                        else:
                            if sickbeard.KODI_UPDATE_ONLYFIRST:
                                logger.log("Successfully updated '" + connection.host + "', stopped sending update library commands.", logger.DEBUG)
                                return True

                            result += 1
                            continue

                logger.log("Doing Full Library KODI update on host: " + connection.host, logger.DEBUG)
                response = connection.VideoLibrary.Scan()
                if not response:
                    logger.log("KODI Full Library update failed on: " + connection.host, logger.WARNING)
                elif self.success(response):
                    if sickbeard.KODI_UPDATE_ONLYFIRST:
                        logger.log("Successfully updated '" + connection.host + "', stopped sending update library commands.", logger.DEBUG)
                        return True

                    result += 1
            except (URLError, RequestTimeout):
                pass

        return result > 0

    def play_episode(self, episode, connection_index=0):
        """Handles updating KODI host via HTTP JSON-RPC

        Attempts to update the KODI video library for a specific tv show if passed,
        otherwise update the whole library if enabled.

        Args:
            host: KODI webserver host:port
            show_name: Name of a TV show to specifically target the library update for

        Returns:
            Returns True or False

        """
        try:
            connection = self.connections[int(connection_index)]
        except IndexError:
            logger.log('Incorrect KODI host passed to play an episode, aborting play', logger.WARNING)
            return False

        logger.log("Trying to play episode on Kodi for host: " + connection.host, logger.DEBUG)

        response = connection.VideoLibrary.GetTVShows(filter={"field": "title", "operator": "is", "value": episode.show.name})
        if response and "result" in response and "tvshows" in response["result"]:
            shows = response["result"]["tvshows"]

        for show in shows:
            if ("label" in show and show["label"] == episode.show.name) or ("title" in show and show["title"] == episode.show.name):
                tvshowid = show["tvshowid"]

        response = connection.VideoLibrary.GetEpisodes(
            filter={"field": "title", "operator": "is", "value": episode.name},
            season=episode.season,
            tvshowid=tvshowid,
            properties=["file"]
        )

        if response and "result" in response and "episodes" in response["result"]:
            episodes = response["result"]["episodes"]

            if len(episodes) > 1:
                logger.log('Could not play the item, too many files were returned as options and we could not choose')

            if episodes:
                connection.Player.Open(item={'file': episodes[0]['file']})
            else:
                logger.log('Could not find the episode on Kodi to play')

    def notify_snatch(self, ep_name):
        if sickbeard.KODI_NOTIFY_ONSNATCH:
            self._notify_kodi(ep_name, common.notifyStrings[common.NOTIFY_SNATCH])

    def notify_download(self, ep_name):
        if sickbeard.KODI_NOTIFY_ONDOWNLOAD:
            self._notify_kodi(ep_name, common.notifyStrings[common.NOTIFY_DOWNLOAD])

    def notify_subtitle_download(self, ep_name, lang):
        if sickbeard.KODI_NOTIFY_ONSUBTITLEDOWNLOAD:
            self._notify_kodi(ep_name + ": " + lang, common.notifyStrings[common.NOTIFY_SUBTITLE_DOWNLOAD])

    def notify_git_update(self, new_version="??"):
        if sickbeard.USE_KODI:
            update_text = common.notifyStrings[common.NOTIFY_GIT_UPDATE_TEXT]
            title = common.notifyStrings[common.NOTIFY_GIT_UPDATE]
            self._notify_kodi(update_text + new_version, title)

    def notify_login(self, ipaddress=""):
        if sickbeard.USE_KODI:
            update_text = common.notifyStrings[common.NOTIFY_LOGIN_TEXT]
            title = common.notifyStrings[common.NOTIFY_LOGIN]
            self._notify_kodi(update_text.format(ipaddress), title)

    def test_notify(self, host, username, password):
        return self._notify_kodi("Testing KODI notifications from SickChill", "Test Notification", hosts=host, username=username, password=password, force=True)
