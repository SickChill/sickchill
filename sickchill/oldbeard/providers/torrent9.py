import re
from urllib.parse import urljoin

import validators

from sickchill import logger
from sickchill.helper.common import convert_size, try_int
from sickchill.oldbeard import tvcache
from sickchill.oldbeard.bs4_parser import BS4Parser
from sickchill.providers.torrent.TorrentProvider import TorrentProvider


class Provider(TorrentProvider):
    def __init__(self):

        super().__init__("Torrent9")

        self.public = True
        self.minseed = 0
        self.minleech = 0
        self._original_url = "https://ww1.torrent9.re"
        self._custom_url = None
        self._used_url = None
        self._recheck_url = True

        self.proper_strings = ["PROPER", "REPACK"]
        self.cache = tvcache.TVCache(self)

    def _retrieve_dllink_from_url(self, inner_url):
        data = self.get_url(urljoin(self.url, inner_url), returns="text")
        regex = r".*?function\s+redirect\(\).+?= '([^']+)'"
        with BS4Parser(data, "html5lib") as html:
            scripts = html.head.findAll("script")
            if len(scripts):
                script = scripts[-1].string
                matches = re.match(regex, script, re.S)
                if matches:
                    return urljoin(self.url, matches[1])

            # try href
            download_btns = html.findAll("div", {"class": "btn-download"})
            for btn in download_btns:
                link = btn.find("a").get("href")
                if link.startswith("javascript"):
                    return ""
                if link.startswith("magnet"):
                    continue
                else:
                    return urljoin(self.url, link)

        return ""

    def _get_custom_url(self):
        return self._custom_url

    def _set_custom_url(self, url):
        if self._custom_url != url:
            self._custom_url = url
            self._recheck_url = True

    def _get_provider_url(self):
        if self._recheck_url:
            if self.custom_url:
                if validators.url(self.custom_url) == True:
                    self._used_url = self.custom_url
                else:
                    logger.warning("Invalid custom url set, please check your settings")

            self._used_url = self._original_url

        return self._used_url

    def _set_provider_url(self, url):
        self._used_url = url

    url = property(_get_provider_url, _set_provider_url)
    custom_url = property(_get_custom_url, _set_custom_url)

    def search(self, search_strings, age=0, ep_obj=None):
        results = []
        for mode in search_strings:
            items = []
            logger.debug(_("Search Mode: {mode}").format(mode=mode))
            for search_string in {*search_strings[mode]}:
                if mode == "Season":
                    search_string = re.sub(r"(.*)S[0-9]", r"\1Saison ", search_string)

                if mode != "RSS":
                    logger.debug(_("Search String: {search_string}").format(search_string=search_string))

                    search_url = self.url
                    post_data = {"torrentSearch": search_string}
                else:
                    search_url = self.url + "/torrents/series"
                    post_data = None

                data = self.get_url(search_url, post_data, returns="text")
                if not data:
                    continue

                with BS4Parser(data, "html5lib") as html:
                    for result in html.select("div.table-responsive tr"):
                        try:

                            link = result.select_one("a")
                            title = link.get_text(strip=False).replace("HDTV", "HDTV x264-Torrent9")
                            title = re.sub(r" Saison", " Season", title, flags=re.I)
                            download_url = self._retrieve_dllink_from_url(link.get("href"))
                            if not all([title, download_url]):
                                logger.debug(_("Could not find title and download url for result"))
                                continue

                            seeders = try_int(result.find(attrs={"src": re.compile(r".*.up\.jpg")}).parent.get_text(strip=True))
                            leechers = try_int(result.find(attrs={"src": re.compile(r".*.down\.jpg")}).parent.get_text(strip=True))
                            if seeders < self.minseed or leechers < self.minleech:
                                if mode != "RSS":
                                    logger.debug(
                                        f"Discarding torrent because it doesn't meet the minimum seeders or leechers: {title} (S:{seeders} L:{leechers})"
                                    )
                                continue

                            size = convert_size(result.find("td", text=re.compile(r"[\d0-9]* [KMG]B")).get_text(strip=True), -1) or -1

                            item = {"title": title, "link": download_url, "size": size, "seeders": seeders, "leechers": leechers, "hash": ""}
                            if mode != "RSS":
                                logger.debug(f"Found result: {title} with {seeders} seeders and {leechers} leechers")

                            items.append(item)
                        except Exception as error:
                            logger.debug(f"Error parsing results {error}")
                            continue

            # For each search mode sort all the items by seeders if available
            items.sort(key=lambda d: try_int(d.get("seeders", 0)), reverse=True)
            results += items

        return results
