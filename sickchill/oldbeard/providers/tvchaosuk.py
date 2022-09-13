import re

from sickchill import logger
from sickchill.helper.common import convert_size, try_int
from sickchill.helper.exceptions import AuthException
from sickchill.oldbeard import tvcache
from sickchill.oldbeard.bs4_parser import BS4Parser
from sickchill.providers.torrent.TorrentProvider import TorrentProvider


class Provider(TorrentProvider):
    def __init__(self):

        super().__init__("TvChaosUK")

        self.username = None
        self.password = None

        self.minseed = 0
        self.minleech = 0
        self.freeleech = None

        self.url = "https://www.tvchaosuk.com/"
        self.urls = {"login": self.url + "takelogin.php", "index": self.url + "index.php", "search": self.url + "browse.php"}

        self.cache = tvcache.TVCache(self)

    def _check_auth(self):
        if self.username and self.password:
            return True

        raise AuthException("Your authentication credentials for " + self.name + " are missing, check your config.")

    def login(self):
        if len(self.session.cookies) >= 4:
            return True

        login_params = {"username": self.username, "password": self.password, "logout": "no", "submit": "LOGIN", "returnto": "/browse.php"}

        response = self.get_url(self.urls["login"], post_data=login_params, returns="text")
        if not response:
            logger.warning("Unable to connect to provider")
            return False

        if re.search("Error: Username or password incorrect!", response):
            logger.warning("Invalid username or password. Check your settings")
            return False

        return True

    def search(self, search_strings, age=0, ep_obj=None):
        results = []
        if not self.login():
            return results

        # Search Params
        search_params = {"do": "search", "search_type": "t_name", "category": 0, "include_dead_torrents": "no", "submit": "search"}

        for mode in search_strings:
            items = []
            logger.debug(_("Search Mode: {mode}").format(mode=mode))

            for search_string in {*search_strings[mode]}:

                if mode == "Season":
                    search_string = re.sub(r"(.*)S0?", r"\1Series ", search_string)

                if mode != "RSS":
                    logger.debug(_("Search String: {search_string}").format(search_string=search_string))

                search_params["keywords"] = search_string
                data = self.get_url(self.urls["search"], post_data=search_params, returns="text")
                if not data:
                    logger.debug(_("No data returned from provider"))
                    continue

                with BS4Parser(data) as html:
                    torrent_table = html.find(id="sortabletable")
                    torrent_rows = torrent_table("tr") if torrent_table else []

                    # Continue only if at least one Release is found
                    if len(torrent_rows) < 2:
                        logger.debug("Data returned from provider does not contain any torrents")
                        continue

                    labels = [label.img["title"] if label.img else label.get_text(strip=True) for label in torrent_rows[0]("td")]
                    for torrent in torrent_rows[1:]:
                        try:
                            if self.freeleech and not torrent.find("img", alt=re.compile("Free Torrent")):
                                continue

                            title = torrent.find(class_="tooltip-content").div.get_text(strip=True)
                            download_url = torrent.find(title="Click to Download this Torrent!").parent["href"]
                            if not all([title, download_url]):
                                continue

                            seeders = try_int(torrent.find(title="Seeders").get_text(strip=True))
                            leechers = try_int(torrent.find(title="Leechers").get_text(strip=True))

                            # Filter unseeded torrent
                            if seeders < self.minseed or leechers < self.minleech:
                                if mode != "RSS":
                                    logger.debug(
                                        "Discarding torrent because it doesn't meet the"
                                        " minimum seeders or leechers: {0} (S:{1} L:{2})".format(title, seeders, leechers)
                                    )
                                continue

                            # Chop off tracker/channel prefix or we cant parse the result!
                            if mode != "RSS" and search_params["keywords"]:
                                show_name_first_word = re.search(r"^[^ .]+", search_params["keywords"]).group()
                                if not title.startswith(show_name_first_word):
                                    title = re.sub(r".*(" + show_name_first_word + ".*)", r"\1", title)

                            # Change title from Series to Season, or we can't parse
                            if mode == "Season":
                                title = re.sub(r"(.*)(?i)Series", r"\1Season", title)

                            # Strip year from the end or we can't parse it!
                            title = re.sub(r"(.*)[. ]?\(\d{4}\)", r"\1", title)
                            title = re.sub(r"\s+", r" ", title)

                            torrent_size = torrent("td")[labels.index("Size")].get_text(strip=True)
                            size = convert_size(torrent_size) or -1

                            if mode != "RSS":
                                logger.debug(
                                    _(
                                        "Found result: {title} with {seeders} seeders and {leechers} leechers".format(
                                            title=title, seeders=seeders, leechers=leechers
                                        )
                                    )
                                )

                            item = {"title": title + ".hdtv.x264", "link": download_url, "size": size, "seeders": seeders, "leechers": leechers}
                            items.append(item)
                        except Exception:
                            continue

            # For each search mode sort all the items by seeders if available
            items.sort(key=lambda d: try_int(d.get("seeders", 0)), reverse=True)
            results += items

        return results
