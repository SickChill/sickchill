import re
from urllib.parse import urljoin

from sickchill import logger
from sickchill.helper.common import convert_size
from sickchill.oldbeard import helpers, tvcache
from sickchill.oldbeard.bs4_parser import BS4Parser
from sickchill.providers.torrent.TorrentProvider import TorrentProvider


class Provider(TorrentProvider):
    def __init__(self):

        super().__init__("Newpct")

        self.onlyspasearch = None

        self.url = "http://www.newpct.com"
        self.urls = {"search": urljoin(self.url, "index.php")}

        self.cache = tvcache.TVCache(self, min_time=20)

    def search(self, search_strings, age=0, ep_obj=None):
        """
        Search query:
        http://www.newpct.com/index.php?l=doSearch&q=fringe&category_=All&idioma_=1&bus_de_=All
        q => Show name
        category_ = Category 'Shows' (767)
        idioma_ = Language Spanish (1), All
        bus_de_ = Date from (All, mes, semana, ayer, hoy)
        """
        results = []

        # Only search if user conditions are true
        lang_info = "" if not ep_obj or not ep_obj.show else ep_obj.show.lang

        search_params = {"l": "doSearch", "q": "", "category_": "All", "idioma_": 1, "bus_de_": "All"}

        for mode in search_strings:
            items = []
            logger.debug(_("Search Mode: {mode}".format(mode=mode)))

            if self.onlyspasearch:
                search_params["idioma_"] = 1
            else:
                search_params["idioma_"] = "All"

            # Only search if user conditions are true
            if self.onlyspasearch and lang_info != "es" and mode != "RSS":
                logger.debug("Show info is not spanish, skipping provider search")
                continue

            search_params["bus_de_"] = "All" if mode != "RSS" else "semana"

            for search_string in {*search_strings[mode]}:
                if mode != "RSS":
                    logger.debug(_("Search String: {search_string}".format(search_string=search_string)))

                search_params["q"] = search_string

                data = self.get_url(self.urls["search"], params=search_params, returns="text")
                if not data:
                    continue

                with BS4Parser(data, "html5lib") as html:
                    torrent_table = html.find("table", id="categoryTable")
                    torrent_rows = torrent_table("tr") if torrent_table else []

                    # Continue only if at least one Release is found
                    if len(torrent_rows) < 3:  # Headers + 1 Torrent + Pagination
                        logger.debug("Data returned from provider does not contain any torrents")
                        continue

                    # 'Fecha', 'Título', 'Tamaño', ''
                    # Date, Title, Size
                    labels = [label.get_text(strip=True) for label in torrent_rows[0]("th")]
                    for row in torrent_rows[1:-1]:
                        try:
                            cells = row("td")

                            torrent_row = row.find("a")
                            download_url = torrent_row.get("href", "")
                            title = self._processTitle(torrent_row.get("title", ""), download_url)
                            if not all([title, download_url]):
                                continue

                            # Provider does not provide seeders/leechers
                            seeders = 1
                            leechers = 0
                            # 2 is the 'Tamaño' column.
                            torrent_size = cells[2].get_text(strip=True)

                            size = convert_size(torrent_size) or -1
                            item = {"title": title, "link": download_url, "size": size, "seeders": seeders, "leechers": leechers, "hash": ""}
                            if mode != "RSS":
                                logger.debug(_("Found result: ") + f"{title}")

                            items.append(item)
                        except (AttributeError, TypeError):
                            continue

            results += items

        return results

    def get_url(self, url, post_data=None, params=None, timeout=30, **kwargs):
        """
        returns='content' when trying access to torrent info (For calling torrent client). Previously we must parse
        the URL to get torrent file
        """
        trickery = kwargs.pop("returns", "")
        if trickery == "content":
            kwargs["returns"] = "text"
            data = super().get_url(url, post_data=post_data, params=params, timeout=timeout, **kwargs)
            url = re.search(r"http://tumejorserie.com/descargar/.+\.torrent", data, re.DOTALL).group()
            url = urljoin(self.url, url.rsplit("=", 1)[-1])

        kwargs["returns"] = trickery
        return super().get_url(url, post_data=post_data, params=params, timeout=timeout, **kwargs)

    def download_result(self, result):
        """
        Save the result to disk.
        """

        # check for auth
        if not self.login():
            return False

        urls, filename = self._make_url(result)

        for url in urls:
            # Search results don't return torrent files directly, it returns show sheets so we must parse showSheet to access torrent.
            data = self.get_url(url, returns="text")
            url_torrent = re.search(r"http://tumejorserie.com/descargar/.+\.torrent", data, re.DOTALL).group()

            if url_torrent.startswith("http"):
                self.headers.update({"Referer": "/".join(url_torrent.split("/")[:3]) + "/"})

            logger.info("Downloading a result from {0}".format(url))

            if helpers.download_file(url_torrent, filename, session=self.session, headers=self.headers):
                if self._verify_download(filename):
                    logger.info("Saved result to {0}".format(filename))
                    return True
                else:
                    logger.warning("Could not download {0}".format(url))
                    helpers.remove_file_failed(filename)

        if urls:
            logger.warning("Failed to download any results")

        return False

    @staticmethod
    def _processTitle(title, url):
        # Remove 'Mas informacion sobre ' literal from title
        title = title[22:]
        title = re.sub(r"[ ]{2,}", " ", title, flags=re.I)

        # Quality - Use re module to avoid case sensitive problems with replace
        title = re.sub(r"\[HDTV 1080p?[^\[]*]", "1080p HDTV x264", title, flags=re.I)
        title = re.sub(r"\[HDTV 720p?[^\[]*]", "720p HDTV x264", title, flags=re.I)
        title = re.sub(r"\[ALTA DEFINICION 720p?[^\[]*]", "720p HDTV x264", title, flags=re.I)
        title = re.sub(r"\[HDTV]", "HDTV x264", title, flags=re.I)
        title = re.sub(r"\[DVD[^\[]*]", "DVDrip x264", title, flags=re.I)
        title = re.sub(r"\[BluRay 1080p?[^\[]*]", "1080p BluRay x264", title, flags=re.I)
        title = re.sub(r"\[BluRay Rip 1080p?[^\[]*]", "1080p BluRay x264", title, flags=re.I)
        title = re.sub(r"\[BluRay Rip 720p?[^\[]*]", "720p BluRay x264", title, flags=re.I)
        title = re.sub(r"\[BluRay MicroHD[^\[]*]", "1080p BluRay x264", title, flags=re.I)
        title = re.sub(r"\[MicroHD 1080p?[^\[]*]", "1080p BluRay x264", title, flags=re.I)
        title = re.sub(r"\[BLuRay[^\[]*]", "720p BluRay x264", title, flags=re.I)
        title = re.sub(r"\[BRrip[^\[]*]", "720p BluRay x264", title, flags=re.I)
        title = re.sub(r"\[BDrip[^\[]*]", "720p BluRay x264", title, flags=re.I)

        # detect hdtv/bluray by url
        # hdtv 1080p example url: http://www.newpct.com/descargar-seriehd/foo/capitulo-610/hdtv-1080p-ac3-5-1/
        # hdtv 720p example url: http://www.newpct.com/descargar-seriehd/foo/capitulo-26/hdtv-720p-ac3-5-1/
        # hdtv example url: http://www.newpct.com/descargar-serie/foo/capitulo-214/hdtv/
        # bluray compilation example url: http://www.newpct.com/descargar-seriehd/foo/capitulo-11/bluray-1080p/
        title_hdtv = re.search(r"HDTV", title, flags=re.I)
        title_720p = re.search(r"720p", title, flags=re.I)
        title_1080p = re.search(r"1080p", title, flags=re.I)
        title_x264 = re.search(r"x264", title, flags=re.I)
        title_bluray = re.search(r"bluray", title, flags=re.I)
        title_serie_hd = re.search(r"descargar-seriehd", title, flags=re.I)
        url_hdtv = re.search(r"HDTV", url, flags=re.I)
        url_720p = re.search(r"720p", url, flags=re.I)
        url_1080p = re.search(r"1080p", url, flags=re.I)
        url_bluray = re.search(r"bluray", url, flags=re.I)

        if not title_hdtv and url_hdtv:
            title += " HDTV"
            if not title_x264:
                title += " x264"
        if not title_bluray and url_bluray:
            title += " BluRay"
            if not title_x264:
                title += " x264"
        if not title_1080p and url_1080p:
            title += " 1080p"
            title_1080p = True
        if not title_720p and url_720p:
            title += " 720p"
            title_720p = True
        if not (title_720p or title_1080p) and title_serie_hd:
            title += " 720p"

        # Language
        title = re.sub(r"\[Spanish[^\[]*]", "SPANISH AUDIO", title, flags=re.I)
        title = re.sub(r"\[Castellano[^\[]*]", "SPANISH AUDIO", title, flags=re.I)
        title = re.sub(r"\[Español[^\[]*]", "SPANISH AUDIO", title, flags=re.I)
        title = re.sub(r"\[AC3 5\.1 Español[^\[]*]", "SPANISH AUDIO", title, flags=re.I)

        if re.search(r"\[V.O.[^\[]*]", title, flags=re.I):
            title += "-NEWPCTVO"
        else:
            title += "-NEWPCT"

        return title.strip()
