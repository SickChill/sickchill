import re
import traceback

from sickchill import logger
from sickchill.helper.common import convert_size, try_int
from sickchill.helper.exceptions import AuthException
from sickchill.oldbeard import db, tvcache
from sickchill.oldbeard.bs4_parser import BS4Parser
from sickchill.oldbeard.common import Quality
from sickchill.oldbeard.name_parser.parser import InvalidNameException, InvalidShowException, NameParser
from sickchill.providers.torrent.TorrentProvider import TorrentProvider

category_excluded = {
    "Sport": 22,
    "Teatro": 23,
    "Video Musicali": 21,
    "Film": 4,
    "Musica": 2,
    "Students Releases": 13,
    "E Books": 3,
    "Linux": 6,
    "Macintosh": 9,
    "Windows Software": 10,
    "Pc Game": 11,
    "Playstation 2": 12,
    "Wrestling": 24,
    "Varie": 25,
    "Xbox": 26,
    "Immagini sfondi": 27,
    "Altri Giochi": 28,
    "Fumetteria": 30,
    "Trash": 31,
    "PlayStation 1": 32,
    "PSP Portable": 33,
    "A Book": 34,
    "Podcast": 35,
    "Edicola": 36,
    "Mobile": 37,
}


class Provider(TorrentProvider):
    def __init__(self):

        super().__init__("TNTVillage")

        self._uid = None
        self._hash = None
        self.username = None
        self.password = None
        self.cat = None
        self.engrelease = None
        self.page = 10
        self.subtitle = None
        self.minseed = 0
        self.minleech = 0

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

        self.category_dict = {"Serie TV": 29, "Cartoni": 8, "Anime": 7, "Programmi e Film TV": 1, "Documentari": 14, "All": 0}

        self.urls = {
            "base_url": "http://forum.tntvillage.scambioetico.org",
            "login": "http://forum.tntvillage.scambioetico.org/index.php?act=Login&CODE=01",
            "detail": "http://forum.tntvillage.scambioetico.org/index.php?showtopic=%s",
            "search": "http://forum.tntvillage.scambioetico.org/?act=allreleases&%s",
            "search_page": "http://forum.tntvillage.scambioetico.org/?act=allreleases&st={0}&{1}",
            "download": "http://forum.tntvillage.scambioetico.org/index.php?act=Attach&type=post&id=%s",
        }

        self.url = self.urls["base_url"]

        self.sub_string = ["sub", "softsub"]

        self.proper_strings = ["PROPER", "REPACK"]

        self.categories = "cat=29"

        self.cache = tvcache.TVCache(self, min_time=30)  # only poll TNTVillage every 30 minutes max

    def _check_auth(self):

        if not self.username or not self.password:
            raise AuthException("Your authentication credentials for " + self.name + " are missing, check your config.")

        return True

    def login(self):
        if len(self.session.cookies) >= 3:
            if self.session.cookies.get("pass_hash", "") not in ("0", 0) and self.session.cookies.get("member_id") not in ("0", 0):
                return True

        login_params = {"UserName": self.username, "PassWord": self.password, "CookieDate": 1, "submit": "Connettiti al Forum"}

        response = self.get_url(self.urls["login"], post_data=login_params, returns="text")
        if not response:
            logger.warning("Unable to connect to provider")
            return False

        if re.search("Sono stati riscontrati i seguenti errori", response) or re.search("<title>Connettiti</title>", response):
            logger.warning("Invalid username or password. Check your settings")
            return False

        return True

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
        file_quality = ""

        img_all = (torrent_rows("td"))[1]("img")

        if img_all:
            for img_type in img_all:
                try:
                    file_quality = file_quality + " " + img_type["src"].replace("style_images/mkportal-636/", "").replace(".gif", "").replace(".png", "")
                except Exception:
                    logger.exception("Failed parsing quality. Traceback: {0}".format(traceback.format_exc()))

        else:
            file_quality = (torrent_rows("td"))[1].get_text()
            logger.debug("Episode quality: {0}".format(file_quality))

        def checkName(options, func):
            return func([re.search(option, file_quality, re.I) for option in options])

        dvdOptions = checkName(["dvd", "dvdrip", "dvdmux", "DVD9", "DVD5"], any)
        bluRayOptions = checkName(["BD", "BDmux", "BDrip", "BRrip", "Bluray"], any)
        sdOptions = checkName(["h264", "divx", "XviD", "tv", "TVrip", "SATRip", "DTTrip", "Mpeg2"], any)
        hdOptions = checkName(["720p"], any)
        fullHD = checkName(["1080p", "fullHD"], any)

        if img_all:
            file_quality = (torrent_rows("td"))[1].get_text()

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

    def _is_italian(self, torrent_rows):

        name = str(torrent_rows("td")[1].find("b").find("span"))
        if not name or name == "None":
            return False

        subFound = italian = False
        for sub in self.sub_string:
            if re.search(sub, name, re.I):
                subFound = True
            else:
                continue

            if re.search("[ -_.|]ita[ -_.|]", name.lower().split(sub)[0], re.I):
                logger.debug("Found Italian release:  " + name)
                italian = True
                break

        if not subFound and re.search("ita", name, re.I):
            logger.debug("Found Italian release:  " + name)
            italian = True

        return italian

    @staticmethod
    def _is_english(torrent_rows):

        name = str(torrent_rows("td")[1].find("b").find("span"))
        if not name or name == "None":
            return False

        english = False
        if re.search("eng", name, re.I):
            logger.debug("Found English release:  " + name)
            english = True

        return english

    @staticmethod
    def _is_season_pack(name):

        try:
            parse_result = NameParser(tryIndexers=True).parse(name)
        except (InvalidNameException, InvalidShowException) as error:
            logger.debug("{0}".format(error))
            return False

        main_db_con = db.DBConnection()
        sql_selection = "select count(*) as count from tv_episodes where showid = ? and season = ?"
        episodes = main_db_con.select(sql_selection, [parse_result.show.indexerid, parse_result.season_number])
        if int(episodes[0]["count"]) == len(parse_result.episode_numbers):
            return True

    def search(self, search_params, age=0, ep_obj=None):
        results = []
        if not self.login():
            return results

        self.categories = "cat=" + str(self.cat)

        for mode in search_params:
            items = []
            logger.debug(_("Search Mode: {mode}".format(mode=mode)))
            for search_string in search_params[mode]:

                if mode == "RSS":
                    self.page = 2

                last_page = 0
                y = int(self.page)

                if search_string == "":
                    continue

                search_string = str(search_string).replace(".", " ")

                for x in range(0, y):
                    z = x * 20
                    if last_page:
                        break

                    if mode != "RSS":
                        search_url = (self.urls["search_page"] + "&filter={2}").format(z, self.categories, search_string)
                    else:
                        search_url = self.urls["search_page"].format(z, self.categories)

                    if mode != "RSS":
                        logger.debug(_("Search String: {search_string}".format(search_string=search_string)))

                    data = self.get_url(search_url, returns="text")
                    if not data:
                        logger.debug("No data returned from provider")
                        continue

                    try:
                        with BS4Parser(data, "html5lib") as html:
                            torrent_table = html.find("table", class_="copyright")
                            torrent_rows = torrent_table("tr") if torrent_table else []

                            # Continue only if one Release is found
                            if len(torrent_rows) < 3:
                                logger.debug("Data returned from provider does not contain any torrents")
                                last_page = 1
                                continue

                            if len(torrent_rows) < 42:
                                last_page = 1

                            for result in torrent_table("tr")[2:]:

                                try:
                                    link = result.find("td").find("a")
                                    title = link.string
                                    download_url = self.urls["download"] % result("td")[8].find("a")["href"][-8:]
                                    leechers = result("td")[3]("td")[0].text
                                    leechers = int(leechers.strip("[]"))
                                    seeders = result("td")[3]("td")[1].text
                                    seeders = int(seeders.strip("[]"))
                                    torrent_size = result("td")[3]("td")[3].text.strip("[]") + " GB"
                                    size = convert_size(torrent_size) or -1
                                except (AttributeError, TypeError):
                                    continue

                                filename_qt = self._reverseQuality(self._episodeQuality(result))
                                for text in self.hdtext:
                                    title1 = title
                                    title = title.replace(text, filename_qt)
                                    if title != title1:
                                        break

                                if Quality.nameQuality(title) == Quality.UNKNOWN:
                                    title += filename_qt

                                if not self._is_italian(result) and not self.subtitle:
                                    logger.debug("Torrent is subtitled, skipping: {0} ".format(title))
                                    continue

                                if self.engrelease and not self._is_english(result):
                                    logger.debug("Torrent isnt english audio/subtitled , skipping: {0} ".format(title))
                                    continue

                                search_show = re.split(r"([Ss][\d{1,2}]+)", search_string)[0]
                                show_title = search_show
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
                        logger.exception("Failed parsing provider. Traceback: {0}".format(traceback.format_exc()))

                # For each search mode sort all the items by seeders if available if available
                items.sort(key=lambda d: try_int(d.get("seeders", 0)), reverse=True)

                results += items

        return results
