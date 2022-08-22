import re
import validators

from sickchill import logger
from sickchill.helper.common import convert_size, try_int
from sickchill.oldbeard import tvcache
from sickchill.oldbeard.bs4_parser import BS4Parser
from sickchill.providers.torrent.TorrentProvider import TorrentProvider
from urllib.parse import urljoin

class Provider(TorrentProvider):
    def __init__(self):

        super().__init__("Cpasbien")

        self.public = True
        self.minseed = 0
        self.minleech = 0
        self._original_url = "https://www.cpasbien.ch"
        self._custom_url = None
        self._used_url = None
        self._recheck_url = True

        self.proper_strings = ["PROPER", "REPACK"]
        self.cache = tvcache.TVCache(self)
        self.ability_status = self.PROVIDER_BACKLOG

    def _retrieve_dllink_from_url(self, inner_url, _type="torrent"):
        # for instance, no magnet
        if _type != "torrent":
            return ""
        data = self.get_url(inner_url, returns="text")
        # js
        mapt = {"torrent": r"redirect", "magnet": r"redir"}
        regex = r".*?function\s+" + mapt[_type] + r"\(\).+?= '([^']+)'"
        # href
        res = {"torrent": "", "magnet": ""}
        with BS4Parser(data, "html5lib") as html:
            # for manual testing:
            # data = open('test.html', 'r').read()
            # html = BeautifulSoup(data, "html5lib")
            # try js
            scripts = html.head.findAll("script")
            if len(scripts):
                script = scripts[-1].string
                matches = re.match(regex, script, re.S)
                if matches:
                    return matches[1]
            # try href
            download_btns = html.findAll("div", {"class": "btn-download"})
            for btn in download_btns:
                link = btn.find("a")["href"]
                if link.startswith("javascript"):
                    return ""
                if link.startswith("magnet"):
                    res["magnet"] = link
                else:
                    res["torrent"] = link
        return res[_type]

    def _get_custom_url(self):
        return self._custom_url

    def _set_custom_url(self, url):
        if self._custom_url != url:
            self._custom_url = url
            self._recheck_url = True

    def _get_provider_url(self):
        if self._recheck_url:
            if self.custom_url:
                if validators.url(self.custom_url):
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
            logger.debug(_(f"Search Mode: {mode}"))
            for search_string in {*search_strings[mode]}:
                if mode == "Season":
                    search_string = re.sub(r"(.*)S[0-9]", r"\1Saison ", search_string)

                if mode != "RSS":
                    logger.debug(_(f"Search String: {search_string}"))

                    search_url = self.url + "/recherche/" + search_string
                else:
                    search_url = self.url + "/torrents/series"

                data = self.get_url(search_url, returns="text")
                if not data:
                    continue

                with BS4Parser(data, "html5lib") as html:
                    torrent_table = html.find("table", {"class": "table-corps"})
                    if torrent_table:
                        torrent_rows = torrent_table.findAll("tr")
                    else:
                        torrent_rows = None

                    if not torrent_rows:
                        continue
                    for result in torrent_rows:
                        try:
                            title = result.find(class_="titre").get_text(strip=True).replace("HDTV", "HDTV x264-CPasBien")
                            title = re.sub(r" Saison", " Season", title, flags=re.I)
                            tmp = result.find("a")["href"]
                            download_url = urljoin(self.url, self._retrieve_dllink_from_url(urljoin(self.url, tmp)))
                            if not all([title, download_url]):
                                continue

                            seeders = try_int(result.find(class_="seed_ok").get_text(strip=True))
                            leechers = try_int(result.find(class_="down").get_text(strip=True))
                            if seeders < self.minseed or leechers < self.minleech:
                                if mode != "RSS":
                                    logger.debug(f"Discarding torrent because it doesn't meet the minimum seeders or "
                                                 f"leechers: {title} (S:{seeders} L:{leechers})")
                                continue

                            torrent_size = result.find(class_="poid").get_text(strip=True)

                            units = ["o", "Ko", "Mo", "Go", "To", "Po"]
                            size = convert_size(torrent_size, units=units) or -1

                            item = {"title": title, "link": download_url, "size": size, "seeders": seeders, "leechers": leechers, "hash": ""}
                            if mode != "RSS":
                                logger.debug(f"Found result: {title} with {seeders} seeders and {leechers} leechers")

                            items.append(item)
                        except Exception:
                            continue

            # For each search mode sort all the items by seeders if available
            items.sort(key=lambda d: try_int(d.get("seeders", 0)), reverse=True)
            results += items

        return results
