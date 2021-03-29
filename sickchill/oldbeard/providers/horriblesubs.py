import re
from urllib.parse import urljoin

from sickchill import logger
from sickchill.helper.common import try_int
from sickchill.oldbeard import tvcache
from sickchill.oldbeard.bs4_parser import BS4Parser
from sickchill.providers.torrent.TorrentProvider import TorrentProvider


class Provider(TorrentProvider):
    def __init__(self):

        super().__init__("HorribleSubs")

        self.public = True
        self.supports_absolute_numbering = True
        self.anime_only = True

        self.minseed = 0
        self.minleech = 0

        self.url = "https://horriblesubs.info"
        self.urls = {"search": urljoin(self.url, "api.php"), "rss": "http://www.horriblesubs.info/rss.php"}

        self.cache = tvcache.TVCache(self, min_time=15)  # only poll HorribleSubs every 15 minutes max

    def search(self, search_strings, age=0, ep_obj=None):
        results = []
        if self.show and not self.show.is_anime:
            return results

        for mode in search_strings:
            items = []
            logger.debug(_("Search Mode: {mode}".format(mode=mode)))

            for search_string in {*search_strings[mode]}:
                if mode == "RSS":
                    entries = self.__rssFeed()
                else:
                    entries = self.__getShow(search_string)

                items.extend(entries)

            # For each search mode sort all the items by seeders if available
            items.sort(key=lambda d: try_int(d.get("seeders", 0)), reverse=True)
            results.extend(items)

        return results

    def __rssFeed(self):
        entries = []

        rss_params = {"res": "all"}

        target_url = self.urls["rss"]

        data = self.get_url(target_url, params=rss_params, returns="text")
        if not data:
            return entries

        entries = self.__parseRssFeed(data)

        return entries

    @staticmethod
    def __parseRssFeed(data):
        entries = []
        with BS4Parser(data, "html5lib") as soup:
            items = soup.findAll("item")

            for item in items:
                title = item.find("title").text
                download_url = item.find("link").text

                entry = {"title": title, "link": download_url, "size": 333, "seeders": 1, "leechers": 1, "hash": ""}
                logger.debug(_("Found result: {title}".format(title=title)))

                entries.append(entry)

        return entries

    def __getShow(self, search_string):
        entries = []

        search_params = {"method": "search", "value": search_string}

        logger.debug(_("Search String: {search_string}".format(search_string=search_string)))
        target_url = self.urls["search"]

        data = self.get_url(target_url, params=search_params, returns="text")
        if not data:
            return entries

        entries = self.__parseSearchResult(data, target_url)

        return entries

    def __parseSearchResult(self, data, target_url):
        results = []
        with BS4Parser(data, "html5lib") as soup:
            lists = soup.find_all("ul")

            list_items = []
            for ul_list in lists:
                curr_list_item = ul_list("li") if ul_list else []
                list_items.extend(curr_list_item)

            # Continue only if one Release is found
            if len(list_items) < 1:
                logger.debug("Data returned from provider does not contain any torrents")
                return []

            for list_item in list_items:
                title = "{0}{1}".format(str(list_item.find("span").next_sibling), str(list_item.find("strong").text))
                logger.debug("Found title {0}".format(title))
                episode_url = "/#".join(list_item.find("a")["href"].rsplit("#", 1))
                episode = episode_url.split("#", 1)[1]

                page_url = "{0}{1}".format(self.url, episode_url)
                show_id = self.__getShowId(page_url)

                if not show_id:
                    logger.debug("Could not find show ID")
                    continue

                fetch_params = {"method": "getshows", "type": "show", "mode": "filter", "showid": show_id, "value": episode}

                entries = self.__fetchUrls(target_url, fetch_params, title)
                results.extend(entries)

        return results

    def __getShowId(self, target_url):
        data = self.get_url(target_url, returns="text")
        if not data:
            logger.debug("Could not fetch url: {0}".format(target_url))
            return None

        with BS4Parser(data, "html5lib") as soup:
            show_id = re.sub(r"[^0-9]", "", soup(text=re.compile("hs_showid"))[0])
            logger.debug("show id: {0}".format(show_id))

        return show_id

    def __fetchUrls(self, target_url, params, title):
        entries = []

        data = self.get_url(target_url, params=params, returns="text")
        if not data:
            return entries

        with BS4Parser(data, "html5lib") as soup:
            for div in soup.findAll("div", attrs={"class": "rls-link"}):
                quality = div.find("span", attrs={"class": "rls-link-label"}).get_text(strip=True)

                link = div.find("span", class_="hs-torrent-link")
                download_url = link.find("a")["href"] if link and link.find("a") else None

                if not download_url:
                    # fallback to magnet link
                    link = div.find("span", class_="hs-magnet-link")
                    download_url = link.find("a")["href"] if link and link.find("a") else None

                release_title = "[HorribleSubs] {0}.[{1}]".format(title, quality)
                item = {"title": release_title, "link": download_url, "size": 333, "seeders": 1, "leechers": 1, "hash": ""}
                logger.debug(_("Found result: ") + f"{release_title}")

                entries.append(item)

        return entries
