import os
import re

import bencodepy
from requests.utils import add_dict_to_cookiejar

from sickchill import logger, settings
from sickchill.oldbeard import helpers, tvcache
from sickchill.providers.torrent.TorrentProvider import TorrentProvider


class TorrentRssProvider(TorrentProvider):
    def __init__(self, name, url, cookies="", titleTAG="title", search_mode="eponly", search_fallback=False, enable_daily=False, enable_backlog=False):

        super().__init__(name)

        self.cache = TorrentRssCache(self, min_time=15)
        self.url = url.rstrip("/")

        self.supports_backlog = False

        self.search_mode = search_mode
        self.search_fallback = search_fallback
        self.enable_daily = enable_daily
        self.enable_backlog = enable_backlog
        self.enable_cookies = True
        self.cookies = cookies
        self.titleTAG = titleTAG

    def configStr(self):
        return "{0}|{1}|{2}|{3}|{4}|{5}|{6}|{7}|{8}".format(
            self.name or "",
            self.url or "",
            self.cookies or "",
            self.titleTAG or "",
            int(self.enabled),
            self.search_mode or "",
            int(self.search_fallback),
            int(self.enable_daily),
            int(self.enable_backlog),
        )

    @staticmethod
    def providers_list(data):
        providers_list = [x for x in (TorrentRssProvider._make_provider(x) for x in data.split("!!!")) if x]
        seen_values = set()
        providers_set = []

        for provider in providers_list:
            value = provider.name

            if value not in seen_values:
                providers_set.append(provider)
                seen_values.add(value)

        return [x for x in providers_set if x]

    def image_name(self):
        if os.path.isfile(os.path.join(settings.PROG_DIR, "gui", settings.GUI_NAME, "images", "providers", self.get_id() + ".png")):
            return self.get_id() + ".png"
        return "torrentrss.png"

    def _get_title_and_url(self, item):

        title = item.get(self.titleTAG, "").replace(" ", ".")

        attempt_list = [lambda: item.get("torrent_magneturi"), lambda: item.enclosures[0].href, lambda: item.get("link")]

        url = None
        for cur_attempt in attempt_list:
            try:
                url = cur_attempt()
            except Exception:
                continue

            if title and url:
                break

        return title, url

    @staticmethod
    def _make_provider(config):
        if not config:
            return None

        cookies = None
        enable_backlog = 0
        enable_daily = 0
        search_fallback = 0
        search_mode = "eponly"
        title_tag = "title"

        try:
            values = config.split("|")

            if len(values) == 9:
                name, url, cookies, title_tag, enabled, search_mode, search_fallback, enable_daily, enable_backlog = values
            elif len(values) == 8:
                name, url, cookies, enabled, search_mode, search_fallback, enable_daily, enable_backlog = values
            else:
                enabled = values[4]
                name = values[0]
                url = values[1]
        except ValueError:
            logger.exception("Skipping RSS Torrent provider string: {0}, incorrect format".format(config))
            return None

        new_provider = TorrentRssProvider(
            name,
            url,
            cookies=cookies,
            titleTAG=title_tag,
            search_mode=search_mode,
            search_fallback=search_fallback,
            enable_daily=enable_daily,
            enable_backlog=enable_backlog,
        )
        new_provider.enabled = enabled == "1"

        return new_provider

    def validateRSS(self):

        try:
            if self.cookies:
                success, status = self.add_cookies_from_ui()
                if not success:
                    return False, status

            # Access to a protected member of a client class
            data = self.cache._get_rss_data()["entries"]
            if not data:
                return False, "No items found in the RSS feed {0}".format(self.url)

            title, url = self._get_title_and_url(data[0])

            if not title:
                return False, "Unable to get title from first item"

            if not url:
                return False, "Unable to get torrent url from first item"

            if url.startswith("magnet:") and re.search(r"urn:btih:([\w]{32,40})", url):
                return True, "RSS feed Parsed correctly"
            else:
                torrent_file = self.get_url(url, returns="content")
                try:
                    bencodepy.decode(torrent_file)
                except (bencodepy.exceptions.BencodeDecodeError, Exception) as error:
                    self.dumpHTML(torrent_file)
                    return False, "Torrent link is not a valid torrent file: {0}".format(error)

            return True, "RSS feed Parsed correctly"

        except Exception as error:
            return False, f"Error when trying to load RSS: {error}"

    @staticmethod
    def dumpHTML(data):
        dumpName = os.path.join(settings.CACHE_DIR, "custom_torrent.html")

        try:
            fileOut = open(dumpName, "wb")
            fileOut.write(data)
            fileOut.close()
            helpers.chmodAsParent(dumpName)
        except IOError as error:
            logger.exception(f"Unable to save the file: {error}")
            return False

        logger.info(f"Saved custom_torrent html dump {dumpName}")
        return True


class TorrentRssCache(tvcache.TVCache):
    def _get_rss_data(self):
        if self.provider.cookies:
            add_dict_to_cookiejar(self.provider.session.cookies, dict(x.rsplit("=", 1) for x in self.provider.cookies.split(";")))

        return self.get_rss_feed(self.provider.url)


Provider = TorrentRssProvider
