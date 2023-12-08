import math
import socket
import time
from datetime import datetime

import jsonrpclib

from sickchill import logger, settings
from sickchill.helper.common import episode_num
from sickchill.helper.exceptions import AuthException
from sickchill.oldbeard import classes, scene_exceptions, tvcache
from sickchill.oldbeard.common import cpu_presets
from sickchill.oldbeard.helpers import sanitizeSceneName
from sickchill.providers.torrent.TorrentProvider import TorrentProvider


class Provider(TorrentProvider):
    def __init__(self):
        super().__init__("BTN")

        self.supports_absolute_numbering = True

        self.api_key = None

        self.cache = BTNCache(self, min_time=15)  # Only poll BTN every 15 minutes max

        self.urls = {
            "base_url": "https://api.broadcasthe.net",
            "website": "https://broadcasthe.net/",
        }

        self.url = self.urls["website"]

    def _check_auth(self):
        if not self.api_key:
            logger.warning("Invalid api key. Check your settings")

        return True

    def _check_auth_from_data(self, data):
        if data is None:
            return self._check_auth()

        if "api-error" in data:
            logger.debug(_("Incorrect authentication credentials: {0}").format(data["api-error"]))
            raise AuthException(_("Your authentication credentials for {0} are incorrect, check your config.").format(self.name))

        return True

    def search(self, search_params, episode_object=None):
        self._check_auth()

        results = []

        if search_params:
            logger.debug(_("Search string: {0}").format(search_params))
        else:
            # age in seconds
            search_params = {"age": f"<={4 * 24 * 60 * 60}"}

        data = self._api_call(search_params)
        if not data:
            logger.debug("No data returned from provider")
            return results

        found = {}
        if self._check_auth_from_data(data):
            if "torrents" in data:
                found = data["torrents"]

            # We got something, we know the API sends max 1000 results at a time.
            # See if there are more than 1000 results for our query, if not we
            # keep requesting until we've got everything.
            # max 150 requests per hour so limit at that. Scan every 15 minutes. 60 / 15 = 4.
            max_pages = 150
            results_per_page = 1000

            if "results" in data and int(data["results"]) >= results_per_page:
                pages_needed = int(math.ceil(int(data["results"]) / results_per_page))
                if pages_needed > max_pages:
                    pages_needed = max_pages

                # +1 because range(1,4) = 1, 2, 3
                for page in range(1, pages_needed + 1):
                    data = self._api_call(search_params, results_per_page, page * results_per_page)
                    # Note that this these are individual requests and might time out individually. This would result in 'gaps'
                    # in the results. There is no way to fix this though.
                    if "torrents" in data:
                        found.update(data["torrents"])

            for keys, torrent_info in found.items():
                (title, url) = self._get_title_and_url(torrent_info)

                if title and url:
                    logger.debug("Found result: {0} ".format(title))
                    results.append(torrent_info)

        return sorted(results, key=lambda x: self._get_seeders_and_leechers(x)[0], reverse=True)

    def _api_call(self, params=None, results_per_page=1000, offset=0) -> dict:
        data = {}

        try:
            data = jsonrpclib.Server(self.urls["base_url"]).getTorrents(self.api_key, params or {}, int(results_per_page), int(offset))
            time.sleep(cpu_presets[settings.CPU_PRESET])
        except jsonrpclib.jsonrpc.ProtocolError as error:
            if error == (-32001, "Invalid API Key"):
                logger.warning("The API key you provided was rejected because it is invalid. Check your provider configuration.")
            elif error == (-32002, "Call Limit Exceeded"):
                logger.warning("You have exceeded the limit of 150 calls per hour, per API key which is unique to your user account")
            else:
                logger.exception(f"JSON-RPC protocol error while accessing provider. Error: {error} ")
            data = {"api-error": f"{error}"}
            return data

        except socket.timeout:
            logger.warning("Timeout while accessing provider")

        except socket.error as error:
            # Note that sometimes timeouts are thrown as socket errors
            logger.warning(f"Socket error while accessing provider. Error: {error}")

        except Exception as error:
            logger.warning(f"Unknown error while accessing provider. Error: {error}")

        return data

    def _get_seeders_and_leechers(self, item):
        try:
            return item.get("Seeders", -1), item.get("Leechers", -1)
        except AttributeError:
            return -1, -1

    def _get_title_and_url(self, data):
        # The BTN API gives a lot of information in response,
        # however SickChill is built mostly around Scene or
        # release names, which is why we are using them here.
        release_name = data.get("ReleaseName")
        if release_name:
            title = release_name
            append = ".".join(
                f"{part}" for part in (data.get("Resolution"), data.get("Source"), data.get("Codec")) if part and part.lower() not in release_name.lower()
            )
            if append:
                title += " [" + append + "]"

        else:
            # If we don't have a release name we need to get creative
            title = (
                ".".join(
                    f"{part}"
                    for part in (
                        data.get("Series"),
                        data.get("GroupName"),
                        data.get("Resolution"),
                        data.get("Source"),
                        data.get("Codec"),
                    )
                    if part
                )
                .replace(" ", ".")
                .replace("..", ".")
            )

        return title, data.get("DownloadURL", "").replace("\\/", "/") or None

    @staticmethod
    def __add_tvdb_or_name(params, episode):
        search_params = []
        if episode.show.indexer == 1:
            params["tvdb"] = episode.show.indexerid
            search_params.append(params)
        else:
            name_exceptions = list(set(scene_exceptions.get_scene_exceptions(episode.show.indexerid) + [episode.show.name]))
            for name in name_exceptions:
                # Search by name if we don't have tvdb id
                params["series"] = sanitizeSceneName(name)
                search_params.append(params)

        return search_params

    def get_season_search_strings(self, episode_object):
        search_params = {"category": "Season"}

        # Search for entire seasons: no need to do special things for air by date or sports shows
        if episode_object.show.air_by_date or episode_object.show.sports:
            # Search for the year of the air by date show
            search_params["name"] = str(episode_object.airdate).split("-")[0]
        else:
            # BTN uses the same format for both Anime and TV
            search_params["name"] = "Season " + str(episode_object.scene_season)

        return self.__add_tvdb_or_name(search_params, episode_object)

    def get_episode_search_strings(self, episode_object, add_string=""):
        if not episode_object:
            return [{}]

        search_params = {"category": "Episode"}

        # episode
        if episode_object.show.air_by_date or episode_object.show.sports:
            date_str = str(episode_object.airdate)

            # BTN uses dots in dates, we just search for the date since that
            # combined with the series identifier should result in just one episode
            search_params["name"] = date_str.replace("-", ".")
        else:
            # BTN uses the same format for both Anime and TV
            # Do a general name search for the episode
            search_params["name"] = episode_num(episode_object.scene_season, episode_object.scene_episode)

        # search
        return self.__add_tvdb_or_name(search_params, episode_object)

    def find_propers(self, search_date=None):
        results = []

        search_terms = ["%.proper.%", "%.repack.%"]

        for term in search_terms:
            for item in self.search({"release": term}):
                if item["Time"]:
                    try:
                        result_date = datetime.fromtimestamp(float(item["Time"]))
                    except TypeError:
                        result_date = None

                    if result_date and (not search_date or result_date > search_date):
                        title, url = self._get_title_and_url(item)
                        if title and url:
                            results.append(classes.Proper(title, url, result_date, self.show))

        return results


class BTNCache(tvcache.TVCache):
    def _get_rss_data(self):
        return {"entries": self.provider.search(search_params=None)}
