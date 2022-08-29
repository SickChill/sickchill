import re
import time
import traceback

from sickchill import logger, settings
from sickchill.helper.common import try_int
from sickchill.oldbeard import tvcache
from sickchill.oldbeard.bs4_parser import BS4Parser
from sickchill.oldbeard.common import cpu_presets
from sickchill.providers.torrent.TorrentProvider import TorrentProvider


class Provider(TorrentProvider):
    def __init__(self):

        super().__init__("EliteTorrent")

        self.onlyspasearch = None
        self.minseed = 0
        self.minleech = 0
        self.cache = tvcache.TVCache(self)  # Only poll EliteTorrent every 20 minutes max

        self.urls = {"base_url": "https://www.elitetorrent.eu", "search": "https://www.elitetorrent.eu/torrents.php"}

        self.url = self.urls["base_url"]

    def search(self, search_strings, age=0, ep_obj=None):
        results = []
        lang_info = "" if not ep_obj or not ep_obj.show else ep_obj.show.lang

        """
        Search query:
        https://www.elitetorrent.eu/torrents.php?cat=4&modo=listado&orden=fecha&pag=1&buscar=fringe

        cat = 4 => Shows
        modo = listado => display results mode
        orden = fecha => order
        buscar => Search show
        pag = 1 => page number
        """

        search_params = {"cat": 4, "modo": "listado", "orden": "fecha", "pag": 1, "buscar": ""}

        for mode in search_strings:
            items = []
            logger.debug(_("Search Mode: {mode}").format(mode=mode))

            # Only search if user conditions are true
            if self.onlyspasearch and lang_info != "es" and mode != "RSS":
                logger.debug("Show info is not spanish, skipping provider search")
                continue

            for search_string in {*search_strings[mode]}:
                if mode != "RSS":
                    logger.debug("Search string: {0}".format(search_string))

                search_string = re.sub(r"S0*(\d*)E(\d*)", r"\1x\2", search_string)
                search_params["buscar"] = search_string.strip() if mode != "RSS" else ""

                time.sleep(cpu_presets[settings.CPU_PRESET])
                data = self.get_url(self.urls["search"], params=search_params, returns="text")
                if not data:
                    continue

                try:
                    with BS4Parser(data) as html:
                        torrent_table = html.find("table", class_="fichas-listado")
                        torrent_rows = torrent_table("tr") if torrent_table else []

                        if len(torrent_rows) < 2:
                            logger.debug("Data returned from provider does not contain any torrents")
                            continue

                        for row in torrent_rows[1:]:
                            try:
                                download_url = self.urls["base_url"] + row.find("a")["href"]

                                """
                                Transform from
                                https://elitetorrent.eu/torrent/40142/la-zona-1x02
                                to
                                https://elitetorrent.eu/get-torrent/40142
                                """

                                download_url = re.sub(r"/torrent/(\d*)/.*", r"/get-torrent/\1", download_url)

                                """
                                Trick for accents for this provider.

                                - data = self.get_url(self.urls['search'], params=search_params, returns='text') -
                                returns latin1 coded text and this makes that the title used for the search
                                and the title retrieved from the parsed web page doesn't match so I get
                                "No needed episodes found during backlog search for: XXXX"

                                This is not the best solution but it works.

                                First encode latin1 and then decode utf8 to remains str
                                """
                                row_title = row.find("a", class_="nombre")["title"]
                                title = self._processTitle(row_title.encode("latin-1").decode("utf8"))

                                seeders = try_int(row.find("td", class_="semillas").get_text(strip=True))
                                leechers = try_int(row.find("td", class_="clientes").get_text(strip=True))

                                # seeders are not well reported. Set 1 in case of 0
                                seeders = max(1, seeders)

                                # Provider does not provide size
                                size = -1

                            except (AttributeError, TypeError, KeyError, ValueError):
                                continue

                            if not all([title, download_url]):
                                continue

                            # Filter unseeded torrent
                            if seeders < self.minseed or leechers < self.minleech:
                                if mode != "RSS":
                                    logger.debug(
                                        "Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format(
                                            title, seeders, leechers
                                        )
                                    )
                                continue

                            item = {"title": title, "link": download_url, "size": size, "seeders": seeders, "leechers": leechers, "hash": ""}
                            if mode != "RSS":
                                logger.debug("Found result: {0} with {1} seeders and {2} leechers".format(title, seeders, leechers))

                            items.append(item)

                except Exception:
                    logger.warning("Failed parsing provider. Traceback: {0}".format(traceback.format_exc()))

            # For each search mode sort all the items by seeders if available
            items.sort(key=lambda d: try_int(d.get("seeders", 0)), reverse=True)

            results += items

        return results

    @staticmethod
    def _processTitle(title):

        # Quality, if no literal is defined it's HDTV
        if "calidad" not in title:
            title += " HDTV x264"

        title = title.replace("(calidad baja)", "HDTV x264")
        title = title.replace("(Buena calidad)", "720p HDTV x264")
        title = title.replace("(Alta calidad)", "720p HDTV x264")
        title = title.replace("(calidad regular)", "DVDrip x264")
        title = title.replace("(calidad media)", "DVDrip x264")

        # Language, all results from this provider have spanish audio, we append it to title (avoid to download undesired torrents)
        title += " SPANISH AUDIO"
        title += "-ELITETORRENT"

        return title.strip()
