from urllib.error import URLError
from urllib.parse import unquote_plus

from beekeeper.exceptions import RequestTimeout
from kodipydent import Kodi

from sickchill import logger, settings
from sickchill.helper import try_int
from sickchill.oldbeard import common


class Notifier(object):
    def __init__(self):
        self._connections = list()

    def setup(self, hosts=None, username=None, password=None):
        self._connections = []
        for host in (x.strip() for x in (hosts or settings.KODI_HOST or "").split(",") if x.strip()):
            try:
                if ":" in host:
                    bare_host, port = host.split(":")
                    kodi = Kodi(bare_host, username or settings.KODI_USERNAME, password or settings.KODI_PASSWORD, port=try_int(port, 8080))
                else:
                    kodi = Kodi(host, username or settings.KODI_USERNAME, password or settings.KODI_PASSWORD)
                kodi.host = kodi.variables()["hostname"]["value"]
                try:
                    server_name = kodi.Settings.GetSettingValue(setting="services.devicename")["result"]["value"]
                    kodi.name = server_name
                except:
                    pass

                if kodi not in self._connections:
                    self._connections.append(kodi)
            except (URLError, RequestTimeout, KeyError, IndexError):
                pass
                # logger.info('Unable to connect to Kodi host as {0}, make sure the username and password is correct and that the http control is enabled'.format(host))

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
            return result["result"] == "OK"
        except (AttributeError, KeyError, ValueError):
            print(result["error"])

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
            logger.debug("Sending {0} notification to '{1}' - {2}".format(dest_app, connection.host, message))
            response = connection.GUI.ShowNotification(title=title, message=message, image=settings.LOGO_URL)
            if response and response.get("result"):
                results[connection.host] = self.success(response)
            else:
                if settings.KODI_ALWAYS_ON or force:
                    logger.warning("Failed to send notification to {0} for '{1}', check configuration and try again.".format(dest_app, connection.host))
                results[connection.host] = False

        for host in [x.strip() for x in (hosts or settings.KODI_HOST or "").split(",") if x.strip()]:
            base_host = host.split(":")[0]
            if base_host not in results and host not in results:
                results[host] = False

        return results

    def update_library(self, show_name=None):
        if not (settings.USE_KODI and settings.KODI_UPDATE_LIBRARY):
            return False

        if not settings.KODI_HOST:
            logger.debug("No KODI hosts specified, check your settings")
            return False

        result = 0
        for connection in self.connections:
            try:
                logger.debug("Updating KODI library on host: " + connection.host)

                if show_name:
                    tvshowid = -1
                    path = ""

                    logger.debug("Updating library in KODI for show " + show_name)

                    # let's try letting kodi filter the shows
                    response = connection.VideoLibrary.GetTVShows(
                        filter={"field": "title", "operator": "is", "value": unquote_plus(show_name)}, properties=["file"]
                    )
                    if response and "result" in response and "tvshows" in response["result"]:
                        shows = response["result"]["tvshows"]
                    else:
                        # fall back to retrieving the entire show list
                        response = connection.VideoLibrary.GetTVShows(properties=["file"])
                        if response and "result" in response and "tvshows" in response["result"]:
                            shows = response["result"]["tvshows"]
                        else:
                            logger.debug("KODI: No tvshows in KODI TV show list")
                            continue

                    check = (show_name, unquote_plus(show_name))
                    for show in shows:
                        if ("label" in show and show["label"] in check) or ("title" in show and show["title"] in check):
                            tvshowid = show["tvshowid"]
                            path = show["file"]
                            break

                    del shows

                    # we didn't find the show (exact match), thus revert to just doing a full update if enabled
                    if tvshowid == -1:
                        logger.debug("Exact show name not matched in KODI TV show list")

                    if not path:
                        logger.warning("No valid path found for " + show_name + " with ID: " + str(tvshowid) + " on " + connection.host)

                    if path and tvshowid != -1:
                        logger.debug("KODI Updating " + show_name + " with ID: " + str(tvshowid) + " at " + path + " on " + connection.host)
                        response = connection.VideoLibrary.Scan(directory=path)
                        if not self.success(response):
                            logger.warning("Update of show directory failed on " + show_name + " on " + connection.host + " at " + path)
                        else:
                            if settings.KODI_UPDATE_ONLYFIRST:
                                logger.debug("Successfully updated '" + connection.host + "', stopped sending update library commands.")
                                return True

                            result += 1
                            continue

                if show_name and not settings.KODI_UPDATE_FULL:
                    continue

                logger.debug("Doing Full Library KODI update on host: " + connection.host)
                response = connection.VideoLibrary.Scan()
                if not response:
                    logger.warning("KODI Full Library update failed on: " + connection.host)
                elif self.success(response):
                    if settings.KODI_UPDATE_ONLYFIRST:
                        logger.debug("Successfully updated '" + connection.host + "', stopped sending update library commands.")
                        return True

                    result += 1
            except (URLError, RequestTimeout):
                pass

        return result > 0

    def play_episode(self, episode, connection_index=0):
        """Handles playing videos on a KODI host via HTTP JSON-RPC

        Attempts to play an episode on a KODI host.

        Args:
            episode: The episode to play
            connection_index: Index of the selected host to play the episode on

        Returns:
            Returns True or False

        """
        try:
            connection = self.connections[int(connection_index)]
        except IndexError:
            logger.warning("Incorrect KODI host passed to play an episode, aborting play")
            return False

        logger.debug("Trying to play episode on Kodi for host: " + connection.host)

        response = connection.VideoLibrary.GetTVShows(filter={"field": "title", "operator": "is", "value": episode.show.name})

        shows = []
        tvshowid = None
        if response and "result" in response and "tvshows" in response["result"]:
            shows = response["result"]["tvshows"]

        check = (episode.show.name, unquote_plus(episode.show.name))
        for show in shows:
            if ("label" in show and show["label"] in check) or ("title" in show and show["title"] in check):
                tvshowid = show["tvshowid"]

        del shows

        if tvshowid is None:
            logger.info("Could not play the item, could not find the show on Kodi")
            return

        response = connection.VideoLibrary.GetEpisodes(
            filter={"field": "title", "operator": "is", "value": episode.name}, season=episode.season, tvshowid=tvshowid, properties=["file"]
        )

        if response and "result" in response and "episodes" in response["result"]:
            episodes = response["result"]["episodes"]

            if len(episodes) > 1:
                logger.info("Could not play the item, too many files were returned as options and we could not choose")

            if episodes:
                connection.Player.Open(item={"file": episodes[0]["file"]})
            else:
                logger.info("Could not find the episode on Kodi to play")

    def notify_snatch(self, ep_name):
        if settings.KODI_NOTIFY_ONSNATCH:
            self._notify_kodi(ep_name, common.notifyStrings[common.NOTIFY_SNATCH])

    def notify_download(self, ep_name):
        if settings.KODI_NOTIFY_ONDOWNLOAD:
            self._notify_kodi(ep_name, common.notifyStrings[common.NOTIFY_DOWNLOAD])

    def notify_subtitle_download(self, ep_name, lang):
        if settings.KODI_NOTIFY_ONSUBTITLEDOWNLOAD:
            self._notify_kodi(ep_name + ": " + lang, common.notifyStrings[common.NOTIFY_SUBTITLE_DOWNLOAD])

    def notify_git_update(self, new_version="??"):
        if settings.USE_KODI:
            update_text = common.notifyStrings[common.NOTIFY_GIT_UPDATE_TEXT]
            title = common.notifyStrings[common.NOTIFY_GIT_UPDATE]
            self._notify_kodi(update_text + new_version, title)

    def notify_login(self, ipaddress=""):
        if settings.USE_KODI:
            update_text = common.notifyStrings[common.NOTIFY_LOGIN_TEXT]
            title = common.notifyStrings[common.NOTIFY_LOGIN]
            self._notify_kodi(update_text.format(ipaddress), title)

    def test_notify(self, host, username, password):
        return self._notify_kodi("Testing KODI notifications from SickChill", "Test Notification", hosts=host, username=username, password=password, force=True)
