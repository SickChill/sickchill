import datetime
import re
import time

from sickchill import logger, settings
from sickchill.helper.common import convert_size, try_int
from sickchill.oldbeard import tvcache
from sickchill.oldbeard.common import cpu_presets
from sickchill.providers.torrent.TorrentProvider import TorrentProvider


class Provider(TorrentProvider):
    def __init__(self):

        super().__init__("Rarbg")

        self.public = True
        self.minseed = 0
        self.ranked = None
        self.sorting = None
        self.minleech = 0
        self.token = None
        self.token_expires = None
        self.supports_movies = True

        # Spec: https://torrentapi.org/apidocs_v2.txt
        self.url = "https://rarbg.to"
        self.urls = {"api": "http://torrentapi.org/pubapi_v2.php"}

        self.proper_strings = ["{{PROPER|REPACK}}"]

        self.cache = tvcache.TVCache(self, min_time=10)  # only poll RARBG every 10 minutes max

    def login(self):
        if self.token and self.token_expires and datetime.datetime.now() < self.token_expires:
            return True

        login_params = {"get_token": "get_token", "format": "json", "app_id": "sickchill"}

        response = self.get_url(self.urls["api"], params=login_params, returns="json")
        if not response:
            logger.warning("Unable to connect to provider")
            return False

        self.token = response.get("token")
        self.token_expires = datetime.datetime.now() + datetime.timedelta(minutes=14) if self.token else None
        return self.token is not None

    def search(self, search_strings, age=0, ep_obj=None):
        results = []
        if not self.login():
            return results

        search_params = {
            "app_id": "sickchill",
            "min_seeders": try_int(self.minseed),
            "min_leechers": try_int(self.minleech),
            "limit": 100,
            "format": "json_extended",
            "ranked": try_int(self.ranked),
            "token": self.token,
        }

        if ep_obj is not None:
            ep_indexerid = ep_obj.show.indexerid
            ep_indexer = ep_obj.idxr.slug
        else:
            ep_indexerid = None
            ep_indexer = None

        for mode in search_strings:
            items = []
            logger.debug(_("Search Mode: {mode}".format(mode=mode)))
            if mode == "RSS":
                search_params["sort"] = "last"
                search_params["mode"] = "list"
                search_params.pop("search_string", None)
                search_params.pop("search_tvdb", None)
                if settings.movie_list and settings.movie_list.query.count():
                    search_params["category[]"] = ["17", "18"]
                else:
                    search_params["category"] = ["tv"]
            else:
                search_params["category"] = ("tv", "movies")[mode == "Movie"]
                search_params["sort"] = self.sorting if self.sorting else "seeders"
                search_params["mode"] = "search"

                if ep_indexer == "tvdb" and ep_indexerid:
                    search_params["search_tvdb"] = ep_indexerid
                else:
                    search_params.pop("search_tvdb", None)

            for search_string in {*search_strings[mode]}:
                if mode != "RSS":
                    search_string = re.sub(r"\((\d{4})\)", r"\1", search_string).replace(" ", ".")
                    search_params["search_string"] = search_string
                    logger.debug(_("Search String: {search_string}".format(search_string=search_string)))

                time.sleep(cpu_presets[settings.CPU_PRESET] + 2)
                data = self.get_url(self.urls["api"], params=search_params, returns="json")
                if not isinstance(data, dict):
                    logger.debug("No data returned from provider")
                    continue

                error = data.get("error")
                error_code = data.get("error_code")
                # Don't log when {"error":"No results found","error_code":20}
                # List of errors: https://github.com/rarbg/torrentapi/issues/1#issuecomment-114763312
                if error:
                    if try_int(error_code) != 20:
                        logger.info(error)
                    continue

                torrent_results = data.get("torrent_results")
                if not torrent_results:
                    logger.debug("Data returned from provider does not contain any torrents")
                    continue

                for item in torrent_results:
                    try:
                        title = item.pop("title")
                        download_url = item.pop("download")
                        if not all([title, download_url]):
                            continue

                        seeders = item.pop("seeders")
                        leechers = item.pop("leechers")
                        if seeders < self.minseed or leechers < self.minleech:
                            if mode != "RSS":
                                logger.debug(
                                    "Discarding torrent because it doesn't meet the"
                                    " minimum seeders or leechers: {0} (S:{1} L:{2})".format(title, seeders, leechers)
                                )
                            continue

                        torrent_size = item.pop("size", -1)
                        size = convert_size(torrent_size) or -1
                        torrent_hash = self.hash_from_magnet(download_url)

                        if mode != "RSS":
                            logger.debug("Found result: {0} with {1} seeders and {2} leechers".format(title, seeders, leechers))

                        result = {"title": title, "link": download_url, "size": size, "seeders": seeders, "leechers": leechers, "hash": torrent_hash}
                        items.append(result)
                    except Exception as e:
                        logger.info(e)

                    continue

            # For each search mode sort all the items by seeders
            items.sort(key=lambda d: try_int(d.get("seeders", 0)), reverse=True)
            results += items

        return results
