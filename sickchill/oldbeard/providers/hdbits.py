import datetime
import json
from urllib.parse import urlencode, urljoin

from sickchill import logger
from sickchill.helper.exceptions import AuthException
from sickchill.oldbeard import classes, tvcache
from sickchill.providers.torrent.TorrentProvider import TorrentProvider


class Provider(TorrentProvider):
    def __init__(self):

        super().__init__("HDBits")

        self.username = None
        self.passkey = None

        self.cache = HDBitsCache(self, min_time=15)  # only poll HDBits every 15 minutes max

        self.url = "https://hdbits.org"
        self.urls = {"search": urljoin(self.url, "/api/torrents"), "rss": urljoin(self.url, "/api/torrents"), "download": urljoin(self.url, "/download.php")}

    def _check_auth(self):

        if not self.username or not self.passkey:
            raise AuthException("Your authentication credentials for " + self.name + " are missing, check your config.")

        return True

    @staticmethod
    def _check_auth_from_data(parsed_json):
        """ Check that we are authenticated. """

        if "status" in parsed_json and "message" in parsed_json and parsed_json.get("status") == 5:
            logger.warning("Invalid username or password. Check your settings")

        return True

    def get_season_search_strings(self, ep_obj):
        season_search_string = [self.make_post_data_JSON(show=ep_obj.show, season=ep_obj)]
        return season_search_string

    def get_episode_search_strings(self, ep_obj, add_string=""):
        episode_search_string = [self.make_post_data_JSON(show=ep_obj.show, episode=ep_obj)]
        return episode_search_string

    def _get_title_and_url(self, item):
        title = item.get("name", "").replace(" ", ".")
        url = self.urls["download"] + "?" + urlencode({"id": item["id"], "passkey": self.passkey})

        return title, url

    def search(self, search_params, age=0, ep_obj=None):

        # FIXME
        results = []

        logger.debug("Search string: {0}".format(search_params))

        self._check_auth()

        parsed_json = self.get_url(self.urls["search"], post_data=search_params, returns="json")
        if not parsed_json:
            return []

        if self._check_auth_from_data(parsed_json):
            if parsed_json and "data" in parsed_json:
                items = parsed_json["data"]
            else:
                logger.exception("Resulting JSON from provider isn't correct, not parsing it")
                items = []

            for item in items:
                results.append(item)
        # FIXME SORTING
        return results

    def find_propers(self, search_date=None):
        results = []

        search_terms = [" proper ", " repack "]

        for term in search_terms:
            for item in self.search(self.make_post_data_JSON(search_term=term)):
                if item["utadded"]:
                    try:
                        result_date = datetime.datetime.fromtimestamp(int(item["utadded"]))
                    except Exception:
                        result_date = None

                    if result_date and (not search_date or result_date > search_date):
                        title, url = self._get_title_and_url(item)
                        results.append(classes.Proper(title, url, result_date, self.show))

        return results

    def make_post_data_JSON(self, show=None, episode=None, season=None, search_term=None):

        post_data = {
            "username": self.username,
            "passkey": self.passkey,
            "category": [2],
            # TV Category
        }

        if episode:
            if show.air_by_date:
                post_data["tvdb"] = {"id": show.indexerid, "episode": str(episode.airdate).replace("-", "|")}
            elif show.sports:
                post_data["tvdb"] = {"id": show.indexerid, "episode": episode.airdate.strftime("%b")}
            elif show.anime:
                post_data["tvdb"] = {"id": show.indexerid, "episode": "{0:d}".format(int(episode.scene_absolute_number))}
            else:
                post_data["tvdb"] = {"id": show.indexerid, "season": episode.scene_season, "episode": episode.scene_episode}

        if season:
            if show.air_by_date or show.sports:
                post_data["tvdb"] = {
                    "id": show.indexerid,
                    "season": str(season.airdate)[:7],
                }
            elif show.anime:
                post_data["tvdb"] = {
                    "id": show.indexerid,
                    "season": "{0:d}".format(season.scene_absolute_number),
                }
            else:
                post_data["tvdb"] = {
                    "id": show.indexerid,
                    "season": season.scene_season,
                }

        if search_term:
            post_data["search"] = search_term

        return json.dumps(post_data)


class HDBitsCache(tvcache.TVCache):
    def _get_rss_data(self):
        self.search_params = None  # HDBits cache does not use search_params so set it to None
        results = []

        try:
            parsed_json = self.provider.get_url(self.provider.urls["rss"], post_data=self.provider.make_post_data_JSON(), returns="json")

            if self.provider._check_auth_from_data(parsed_json):
                results = parsed_json["data"]
        except Exception:
            pass

        return {"entries": results}
