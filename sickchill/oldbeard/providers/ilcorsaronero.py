import re
from urllib.parse import quote_plus, urljoin

from sickchill import logger
from sickchill.helper.common import convert_size, try_int
from sickchill.oldbeard import db, tvcache
from sickchill.oldbeard.bs4_parser import BS4Parser
from sickchill.oldbeard.common import Quality
from sickchill.oldbeard.name_parser.parser import InvalidNameException, InvalidShowException, NameParser
from sickchill.providers.torrent.TorrentProvider import TorrentProvider


class Provider(TorrentProvider):
    def __init__(self):
        super().__init__("ilCorsaroNero")

        categories = [  # Categories included in searches
            15,  # Serie TV
            5,  # Anime
            1,  # BDRip
            20,  # DVD
            19,  # Screener
        ]
        categories = ",".join(map(str, categories))

        self.url = "https://ilcorsaronero.link"
        self.urls = {
            "search": urljoin(self.url, "argh.php?search={0}&order=data&by=DESC&page={1}&category=" + categories),
        }

        self.public = True
        self.minseed = 0
        self.minleech = 0

        self.engrelease = None
        self.subtitle = None
        self.max_pages = 10

        self.proper_strings = ["PROPER", "REPACK"]
        self.sub_string = ["sub", "softsub"]

        self.hdtext = [
            " - Versione 720p",
            " Versione 720p",
            " V 720p",
            " V 720",
            " V HEVC",
            " V  HEVC",
            " V 1080",
            " Versione 1080p",
            " 720p HEVC",
            " Ver 720",
            " 720p HEVC",
            " 720p",
        ]

        self.cache = tvcache.TVCache(self, min_time=30)  # only poll ilCorsaroNero every 30 minutes max

    @staticmethod
    def _reverseQuality(quality):

        quality_string = ""

        if quality == Quality.SDTV:
            quality_string = " HDTV x264"
        if quality == Quality.SDDVD:
            quality_string = " DVDRIP"
        elif quality == Quality.HDTV:
            quality_string = " 720p HDTV x264"
        elif quality == Quality.FULLHDTV:
            quality_string = " 1080p HDTV x264"
        elif quality == Quality.RAWHDTV:
            quality_string = " 1080i HDTV mpeg2"
        elif quality == Quality.HDWEBDL:
            quality_string = " 720p WEB-DL h264"
        elif quality == Quality.FULLHDWEBDL:
            quality_string = " 1080p WEB-DL h264"
        elif quality == Quality.HDBLURAY:
            quality_string = " 720p Bluray x264"
        elif quality == Quality.FULLHDBLURAY:
            quality_string = " 1080p Bluray x264"

        return quality_string

    @staticmethod
    def _episodeQuality(torrent_rows):
        """
        Return The quality from the scene episode HTML row.
        """

        file_quality = (torrent_rows("td"))[1].find("a")["href"].replace("_", " ")
        logger.debug("Episode quality: {0}".format(file_quality))

        def checkName(options, func):
            return func([re.search(option, file_quality, re.I) for option in options])

        dvdOptions = checkName(["dvd", "dvdrip", "dvdmux", "DVD9", "DVD5"], any)
        bluRayOptions = checkName(["BD", "BDmux", "BDrip", "BRrip", "Bluray"], any)
        sdOptions = checkName(["h264", "divx", "XviD", "tv", "TVrip", "SATRip", "DTTrip", "Mpeg2"], any)
        hdOptions = checkName(["720p"], any)
        fullHD = checkName(["1080p", "fullHD"], any)
        webdl = checkName(["webdl", "webmux", "webrip", "dl-webmux", "web-dlmux", "webdl-mux", "web-dl", "webdlmux", "dlmux"], any)

        if sdOptions and not dvdOptions and not fullHD and not hdOptions:
            return Quality.SDTV
        elif dvdOptions:
            return Quality.SDDVD
        elif hdOptions and not bluRayOptions and not fullHD and not webdl:
            return Quality.HDTV
        elif not hdOptions and not bluRayOptions and fullHD and not webdl:
            return Quality.FULLHDTV
        elif hdOptions and not bluRayOptions and not fullHD and webdl:
            return Quality.HDWEBDL
        elif not hdOptions and not bluRayOptions and fullHD and webdl:
            return Quality.FULLHDWEBDL
        elif bluRayOptions and hdOptions and not fullHD:
            return Quality.HDBLURAY
        elif bluRayOptions and fullHD and not hdOptions:
            return Quality.FULLHDBLURAY
        else:
            return Quality.UNKNOWN

    def _is_italian(self, name):

        if not name or name == "None":
            return False

        subFound = italian = False
        for sub in self.sub_string:
            if re.search(sub, name, re.I):
                subFound = True
            else:
                continue

            if re.search("ita", name.split(sub)[0], re.I):
                logger.debug("Found Italian release: " + name)
                italian = True
                break

        if not subFound and re.search("ita", name, re.I):
            logger.debug("Found Italian release: " + name)
            italian = True

        return italian

    @staticmethod
    def _is_english(name):

        if not name or name == "None":
            return False

        english = False
        if re.search("eng", name, re.I):
            logger.debug("Found English release: " + name)
            english = True

        return english

    @staticmethod
    def _is_season_pack(name):

        try:
            parse_result = NameParser(tryIndexers=True).parse(name)
        except (InvalidNameException, InvalidShowException) as error:
            logger.debug(f"{error}")
            return False

        main_db_con = db.DBConnection()
        sql_selection = "select count(*) as count from tv_episodes where showid = ? and season = ?"
        episodes = main_db_con.select(sql_selection, [parse_result.show.indexerid, parse_result.season_number])
        if int(episodes[0]["count"]) == len(parse_result.episode_numbers):
            return True

    @staticmethod
    def _magnet_from_result(info_hash, title):
        return "magnet:?xt=urn:btih:{hash}&dn={title}&tr={trackers}".format(
            hash=info_hash, title=quote_plus(title), trackers="http://tracker.tntvillage.scambioetico.org:2710/announce"
        )

    def search(self, search_params, age=0, ep_obj=None):
        results = []

        for mode in search_params:
            items = []
            logger.debug(_("Search Mode: {mode}").format(mode=mode))
            for search_string in search_params[mode]:
                if search_string == "":
                    continue

                search_string = str(search_string).replace(".", " ")
                logger.debug(_("Search String: {search_string}").format(search_string=search_string))

                last_page = False
                for page in range(0, self.max_pages):
                    if last_page:
                        break

                    logger.debug("Processing page {0} of results".format(page))
                    search_url = self.urls["search"].format(search_string, page)

                    data = self.get_url(search_url, returns="text")
                    if not data:
                        logger.debug(_("No data returned from provider"))
                        continue

                    try:
                        with BS4Parser(data) as html:
                            table_header = html.find("tr", class_="bordo")
                            torrent_table = table_header.find_parent("table") if table_header else None
                            if not torrent_table:
                                logger.exception("Could not find table of torrents")
                                continue

                            torrent_rows = torrent_table("tr")

                            # Continue only if one Release is found
                            if len(torrent_rows) < 6 or len(torrent_rows[2]("td")) == 1:
                                logger.debug("Data returned from provider does not contain any torrents")
                                last_page = True
                                continue

                            if len(torrent_rows) < 45:
                                last_page = True

                            for result in torrent_rows[2:-3]:
                                result_cols = result("td")
                                if len(result_cols) == 1:
                                    # Ignore empty rows in the middle of the table
                                    continue
                                try:
                                    title = result("td")[1].get_text(strip=True)
                                    torrent_size = result("td")[2].get_text(strip=True)
                                    info_hash = result("td")[3].find("input", class_="downarrow")["value"].upper()
                                    download_url = self._magnet_from_result(info_hash, title)
                                    seeders = try_int(result("td")[5].get_text(strip=True))
                                    leechers = try_int(result("td")[6].get_text(strip=True))
                                    size = convert_size(torrent_size) or -1

                                except (AttributeError, IndexError, TypeError):
                                    continue

                                filename_qt = self._reverseQuality(self._episodeQuality(result))
                                for text in self.hdtext:
                                    title1 = title
                                    title = title.replace(text, filename_qt)
                                    if title != title1:
                                        break

                                if Quality.nameQuality(title) == Quality.UNKNOWN:
                                    title += filename_qt

                                if not self._is_italian(title) and not self.subtitle:
                                    logger.debug("Torrent is subtitled, skipping: {0}".format(title))
                                    continue

                                if self.engrelease and not self._is_english(title):
                                    logger.debug("Torrent isn't english audio/subtitled, skipping: {0}".format(title))
                                    continue

                                search_show = re.split(r"([Ss][\d{1,2}]+)", search_string)[0]
                                show_title = search_show
                                ep_params = ""
                                rindex = re.search(r"([Ss][\d{1,2}]+)", title)
                                if rindex:
                                    show_title = title[: rindex.start()]
                                    ep_params = title[rindex.start() :]
                                if show_title.lower() != search_show.lower() and search_show.lower() in show_title.lower():
                                    new_title = search_show + ep_params
                                    title = new_title

                                if not all([title, download_url]):
                                    continue

                                if self._is_season_pack(title):
                                    title = re.sub(r"([Ee][\d{1,2}\-?]+)", "", title)

                                # Filter unseeded torrent
                                if seeders < self.minseed or leechers < self.minleech:
                                    logger.debug(
                                        "Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format(
                                            title, seeders, leechers
                                        )
                                    )
                                    continue

                                item = {"title": title, "link": download_url, "size": size, "seeders": seeders, "leechers": leechers, "hash": info_hash}
                                if mode != "RSS":
                                    logger.debug(
                                        _(
                                            "Found result: {title} with {seeders} seeders and {leechers} leechers".format(
                                                title=title, seeders=seeders, leechers=leechers
                                            )
                                        )
                                    )

                                items.append(item)

                    except Exception as error:
                        logger.exception("Failed parsing provider. Error: {0}".format(error))

                # For each search mode sort all the items by seeders if available
                items.sort(key=lambda d: try_int(d.get("seeders", 0)), reverse=True)

                results += items

        return results
