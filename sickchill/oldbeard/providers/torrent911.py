import re
from urllib.parse import urljoin

import validators

from sickchill import logger
from sickchill.helper.common import convert_size, try_int
from sickchill.oldbeard import tvcache
from sickchill.oldbeard.bs4_parser import BS4Parser
from sickchill.oldbeard.show_name_helpers import allPossibleShowNames
from sickchill.providers.torrent.TorrentProvider import TorrentProvider


class Provider(TorrentProvider):
    def __init__(self):

        super().__init__("Torrent911")

        self.public = True
        self.minseed = 0
        self.minleech = 0
        self._original_url = "https://www.torrent911.cc"
        self._custom_url = None
        self._used_url = None
        self._recheck_url = True

        self.proper_strings = ["PROPER", "REPACK"]
        self.cache = tvcache.TVCache(self)
        self.ability_status = self.PROVIDER_BACKLOG

    def _retrieve_dllink_from_url(self, inner_url):
        data = self.get_url(urljoin(self.url, inner_url), returns="text")
        regex = r".*?function\s+redirect\(\).+?= '([^']+)'"
        with BS4Parser(data, "html5lib") as html:
            scripts = html.head.findAll("script")
            if len(scripts):
                script = scripts[-1].get("src")
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
            logger.debug(_("Search Mode: {mode}").format(mode=mode))
            for search_string in {*search_strings[mode]}:
                if mode != "RSS":
                    logger.debug(_("Search String: {search_string}").format(search_string=search_string))

                    search_url = self.url + "/recherche/" + search_string
                else:
                    search_url = self.url + "/torrents/series"

                data = self.get_url(search_url, returns="text")
                if not data:
                    continue

                with BS4Parser(data, "html5lib") as html:
                    # Skip column headers
                    for result in html.select("table.table-hover tr")[1:]:
                        try:
                            title = result.select_one(".maxi").get_text(strip=True).replace("HDTV", "HDTV x264-Torrent911")
                            title = re.sub(r" Saison", " Season", title, flags=re.I)
                            download_url = self._retrieve_dllink_from_url(result.select_one("a").get("href"))
                            if not all([title, download_url]):
                                logger.debug(_("Could not find title and download url for result"))
                                continue

                            seeders = try_int(result.find(attrs={"src": re.compile(r".*.uploader\.png")}).parent.get_text(strip=True))
                            leechers = try_int(result.find(attrs={"src": re.compile(r".*.downloader\.png")}).parent.get_text(strip=True))
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

    def get_season_search_strings(self, episode):
        search_string = {"Season": []}

        for show_name in allPossibleShowNames(episode.show, season=episode.scene_season):
            season_string = show_name + " "

            if episode.show.air_by_date or episode.show.sports:
                season_string += str(episode.airdate).split("-")[0]
            elif episode.show.anime:
                # use string below if you really want to search on season with number
                # season_string += 'Season ' + '{0:d}'.format(int(episode.scene_season))
                season_string += "Saison" # ignore season number to get all seasons in all formats
            else:
                season_string += "Saison {0:0d}".format(int(episode.scene_season))
                search_string["Season"].append(season_string.strip())

        return [search_string]
