import re
from typing import Dict, List, TYPE_CHECKING
from urllib.parse import urljoin

from sickchill import logger, settings
from sickchill.helper.common import valid_url
from sickchill.oldbeard import tvcache
from sickchill.oldbeard.bs4_parser import BS4Parser
from sickchill.oldbeard.show_name_helpers import all_possible_show_names
from sickchill.providers.torrent.TorrentProvider import TorrentProvider

if TYPE_CHECKING:
    from sickchill.tv import TVEpisode


class FrenchTorrentProvider(TorrentProvider):
    def __init__(self, name, url):
        super().__init__(name)

        self.proper_strings = ["PROPER", "REPACK"]
        self.cache = tvcache.TVCache(self)

        self.public = True
        self.minseed = 0
        self.minleech = 0

        self._original_url = url
        self._custom_url = None
        self._used_url = None
        self._recheck_url = True

    def _retrieve_dllink_from_url(self, inner_url):
        data = self.get_url(urljoin(self.url, inner_url), returns="text")
        regex = r".*?function\s+redirect\(\).+?= '([^']+)'"

        magnet_classes = ["btn-magnet", "magnet-btn"]
        file_classes = ["btn-download", "download-btn"]

        # Always prefer magnets, unless using black hole.
        check_classes = magnet_classes + file_classes

        if settings.TORRENT_METHOD == "blackhole":
            check_classes.reverse()

        with BS4Parser(data) as html:
            scripts = html.head.find_all("script")
            if len(scripts):
                script = scripts[-1].get("src")
                matches = re.match(regex, script, re.S)
                if matches:
                    return urljoin(self.url, matches[1])

            download_btns = html.find_all("div", {"class": check_classes})
            for btn in download_btns:
                link = btn.find("a").get("href")
                if link.startswith("javascript"):
                    return ""
                if link.startswith("magnet"):
                    return link
                else:
                    return urljoin(self.url, link)

        return ""

    @property
    def custom_url(self):
        return self._custom_url

    @custom_url.setter
    def custom_url(self, url):
        if self._custom_url != url:
            self._custom_url = url
            self._recheck_url = True

    @property
    def url(self):
        if self._recheck_url:
            if self.custom_url:
                if valid_url(self.custom_url):
                    self._used_url = self.custom_url
                else:
                    logger.warning("Invalid custom url set, please check your settings")

            self._used_url = self._original_url

        return self._used_url

    @url.setter
    def url(self, url):
        self._used_url = url

    def get_season_search_strings(self, episode: "TVEpisode") -> List[Dict]:
        search_string = {"Season": set()}
        for show_name in all_possible_show_names(episode.show, season=episode.scene_season):
            season = int(episode.scene_season)
            if episode.show.air_by_date or episode.show.sports:
                year = str(episode.airdate).split("-")[0]
                season_string = f"{show_name} {year}"
            elif episode.show.anime:
                season_string = f"{show_name} Saison"  # ignore season number to get all seasons in all formats
            else:
                season_string = f"{show_name} Saison {season:0d}"

            search_string["Season"].add(season_string)

        return [search_string]
