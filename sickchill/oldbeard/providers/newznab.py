import os
import re
import time
from urllib.parse import urljoin

import validators

from sickchill import logger, settings
from sickchill.helper.common import convert_size, try_int
from sickchill.oldbeard import tvcache
from sickchill.oldbeard.bs4_parser import BS4Parser
from sickchill.oldbeard.common import cpu_presets
from sickchill.providers.nzb.NZBProvider import NZBProvider


class NewznabProvider(NZBProvider):
    """
    Generic provider for built in and custom providers who expose a newznab
    compatible api.
    Tested with: newznab, nzedb, spotweb, torznab
    """

    def __init__(self, name, url, key="0", catIDs="5030,5040", search_mode="eponly", search_fallback=False, enable_daily=True, enable_backlog=False):

        super().__init__(name)

        self.url = url
        self.key = key

        self.search_mode = search_mode
        self.search_fallback = search_fallback
        self.enable_daily = enable_daily
        self.enable_backlog = enable_backlog

        # 0 in the key spot indicates that no key is needed
        self.needs_auth = self.key != "0"
        self.public = not self.needs_auth

        self.catIDs = catIDs if catIDs else "5030,5040"

        self.default = False

        self._caps = False
        self.use_tv_search = None
        self.cap_tv_search = None
        # self.cap_search = None
        # self.cap_movie_search = None
        # self.cap_audio_search = None

        self.cache = tvcache.TVCache(self, min_time=30)  # only poll newznab providers every 30 minutes max

    def configStr(self):
        """
        Generates a '|' delimited string of instance attributes, for saving to config.ini
        """
        return (
            self.name
            + "|"
            + self.url
            + "|"
            + self.key
            + "|"
            + self.catIDs
            + "|"
            + str(int(self.enabled))
            + "|"
            + self.search_mode
            + "|"
            + str(int(self.search_fallback))
            + "|"
            + str(int(self.enable_daily))
            + "|"
            + str(int(self.enable_backlog))
        )

    @staticmethod
    def providers_list(data):
        default_list = [x for x in (NewznabProvider._make_provider(x) for x in NewznabProvider._get_default_providers().split("!!!")) if x]
        providers_list = [x for x in (NewznabProvider._make_provider(x) for x in data.split("!!!")) if x]
        seen_values = set()
        providers_set = []

        for provider in providers_list:
            value = provider.name

            if value not in seen_values:
                providers_set.append(provider)
                seen_values.add(value)

        providers_list = providers_set
        providers_dict = {x.name: x for x in providers_list}

        for default in default_list:
            if not default:
                continue

            if default.name not in providers_dict:
                providers_dict[default.name] = default

                providers_dict[default.name].default = True
                providers_dict[default.name].name = default.name
                providers_dict[default.name].url = default.url
                providers_dict[default.name].needs_auth = default.needs_auth
                providers_dict[default.name].search_mode = default.search_mode
                providers_dict[default.name].search_fallback = default.search_fallback
                providers_dict[default.name].enable_daily = default.enable_daily
                providers_dict[default.name].enable_backlog = default.enable_backlog
                providers_dict[default.name].catIDs = (
                    ",".join([x for x in providers_dict[default.name].catIDs.split(",") if 5000 <= try_int(x) <= 5999]) or default.catIDs
                )

                if settings.QUALITY_ALLOW_HEVC and "5090" not in providers_dict[default.name].catIDs:
                    providers_dict[default.name].catIDs += ",5090"

        return [x for x in providers_list if x]

    def image_name(self):
        """
        Checks if we have an image for this provider already.
        Returns found image or the default newznab image
        """
        if os.path.isfile(os.path.join(settings.PROG_DIR, "gui", settings.GUI_NAME, "images", "providers", self.get_id() + ".png")):
            return self.get_id() + ".png"
        return "newznab.png"

    @property
    def caps(self):
        return self._caps

    @caps.setter
    def caps(self, data):
        # Override nzb.su - tvsearch without tvdbid, with q param
        if "nzb.su" in self.url:
            self.use_tv_search = True
            self.cap_tv_search = ""
            self._caps = True
            return

        elm = data.find("tv-search")
        self.use_tv_search = elm and elm.get("available") == "yes"
        if self.use_tv_search:
            self.cap_tv_search = elm.get("supportedparams", "tvdbid,season,ep")

        self._caps = any([self.cap_tv_search])

    def get_newznab_categories(self, just_caps=False):
        """
        Uses the newznab provider url and apikey to get the capabilities.
        Makes use of the default newznab caps param. e.a. http://yournewznab/api?t=caps&apikey=skdfiw7823sdkdsfjsfk
        Returns a tuple with (succes or not, array with dicts [{'id': '5070', 'name': 'Anime'},
        {'id': '5080', 'name': 'Documentary'}, {'id': '5020', 'name': 'Foreign'}...etc}], error message)
        """
        return_categories = []

        if not self._check_auth():
            return False, return_categories, "Provider requires auth and your key is not set"

        url_params = {"t": "caps"}
        if self.needs_auth and self.key:
            url_params["apikey"] = self.key

        data = self.get_url(urljoin(self.url, "api"), params=url_params, returns="text")
        if not data:
            error_string = "Error getting caps xml for [{0}]".format(self.name)
            logger.warning(error_string)
            return False, return_categories, error_string

        with BS4Parser(data, "html5lib") as html:
            try:
                self.torznab = html.find("server").get("title") == "Jackett"
            except AttributeError:
                self.torznab = False

            if not html.find("categories"):
                error_string = "Error parsing caps xml for [{0}]".format(self.name)
                logger.debug(error_string)
                return False, return_categories, error_string

            self.caps = html.find("searching")
            if just_caps:
                return True, return_categories, "Just checking caps!"

            for category in html("category"):
                if "TV" in category.get("name", "") and category.get("id", ""):
                    return_categories.append({"id": category["id"], "name": category["name"]})
                    for subcat in category("subcat"):
                        if subcat.get("name", "") and subcat.get("id", ""):
                            return_categories.append({"id": subcat["id"], "name": subcat["name"]})

            return True, return_categories, ""

    @staticmethod
    def _get_default_providers():
        # name|url|key|catIDs|enabled|search_mode|search_fallback|enable_daily|enable_backlog
        return (
            "NZB.Cat|https://nzb.cat/||5030,5040,5010|0|eponly|1|1|1!!!"
            + "NZBFinder.ws|https://nzbfinder.ws/||5030,5040,5010,5045|0|eponly|1|1|1!!!"
            + "NZBGeek|https://api.nzbgeek.info/||5030,5040|0|eponly|0|0|0!!!"
            + "Usenet-Crawler|https://www.usenet-crawler.com/||5030,5040|0|eponly|0|0|0!!!"
            + "DOGnzb|https://api.dognzb.cr/||5030,5040,5060,5070|0|eponly|0|1|1"
        )

    def _check_auth(self):
        """
        Checks that user has set their api key if it is needed
        Returns: True/False
        """
        if self.needs_auth and not self.key:
            logger.warning("Invalid api key. Check your settings")
            return False

        return True

    def _check_auth_from_data(self, data):
        """
        Checks that the returned data is valid
        Returns: _check_auth if valid otherwise False if there is an error
        """
        if data("categories") + data("item"):
            return self._check_auth()

        try:
            err_desc = data.error.attrs["description"]
            if not err_desc:
                raise AttributeError
        except (AttributeError, TypeError):
            return self._check_auth()

        logger.info(err_desc)

        return False

    @staticmethod
    def _make_provider(config):
        if not config:
            return None

        enable_backlog = 0
        enable_daily = 0
        search_fallback = 0
        search_mode = "eponly"

        try:
            values = config.split("|")

            if len(values) == 9:
                name, url, key, category_ids, enabled, search_mode, search_fallback, enable_daily, enable_backlog = values
            else:
                name = values[0]
                url = values[1]
                key = values[2]
                category_ids = values[3]
                enabled = values[4]
        except ValueError:
            logger.exception("Skipping Newznab provider string: '{0}', incorrect format".format(config))
            return None

        new_provider = NewznabProvider(
            name,
            url,
            key=key,
            catIDs=category_ids,
            search_mode=search_mode,
            search_fallback=search_fallback,
            enable_daily=enable_daily,
            enable_backlog=enable_backlog,
        )
        new_provider.enabled = enabled == "1"

        return new_provider

    def search(self, search_strings, age=0, ep_obj=None):
        """
        Searches indexer using the params in search_strings, either for latest releases, or a string/id search
        Returns: list of results in dict form
        """
        results = []
        if not self._check_auth():
            return results

        if "gingadaddy" not in self.url:  # gingadaddy has no caps.
            if not self.caps:
                self.get_newznab_categories(just_caps=True)

            if not self.caps:
                return results

        for mode in search_strings:
            search_params = {
                "t": ("search", "tvsearch")[bool(self.use_tv_search)],
                "limit": 100,
                "offset": 0,
                "cat": self.catIDs.strip(", ") or "5030,5040",
                "maxage": settings.USENET_RETENTION,
            }

            if self.needs_auth and self.key:
                search_params["apikey"] = self.key

            if mode != "RSS":
                if self.use_tv_search:
                    if "tvdbid" in str(self.cap_tv_search):
                        search_params["tvdbid"] = ep_obj.show.indexerid

                    if ep_obj.show.air_by_date or ep_obj.show.sports:
                        # date_str = str(ep_obj.airdate)
                        # search_params['season'] = date_str.partition('-')[0]
                        # search_params['ep'] = date_str.partition('-')[2].replace('-', '/')
                        search_params["q"] = str(ep_obj.airdate)
                    elif ep_obj.show.is_anime:
                        search_params["ep"] = ep_obj.absolute_number
                    else:
                        search_params["season"] = ep_obj.scene_season
                        search_params["ep"] = ep_obj.scene_episode

                if mode == "Season":
                    search_params.pop("ep", "")

            if self.torznab:
                search_params.pop("ep", "")
                search_params.pop("season", "")

            items = []
            logger.debug("Search Mode: {0}".format(mode))
            for search_string in {*search_strings[mode]}:
                if mode != "RSS":
                    logger.debug(_("Search String: {search_string}".format(search_string=search_string)))

                    if "tvdbid" not in search_params:
                        search_params["q"] = search_string

                time.sleep(cpu_presets[settings.CPU_PRESET])
                data = self.get_url(urljoin(self.url, "api"), params=search_params, returns="text")
                if not data:
                    break

                with BS4Parser(data, "html5lib") as html:
                    if not self._check_auth_from_data(html):
                        break

                    # try:
                    #     self.torznab = 'xmlns:torznab' in html.rss.attrs
                    # except AttributeError:
                    #     self.torznab = False

                    for item in html("item"):
                        try:
                            title = item.title.get_text(strip=True)
                            download_url = None
                            if item.link:
                                if validators.url(item.link.get_text(strip=True)):
                                    download_url = item.link.get_text(strip=True)
                                elif validators.url(item.link.next.strip()):
                                    download_url = item.link.next.strip()

                            if (not download_url, item.enclosure and validators.url(item.enclosure.get("url", "").strip())):
                                download_url = item.enclosure.get("url", "").strip()

                            if not (title and download_url):
                                continue

                            seeders = leechers = None
                            if "gingadaddy" in self.url:
                                size_regex = re.search(r"\d*.?\d* [KMGT]B", str(item.description))
                                item_size = size_regex.group() if size_regex else -1
                            else:
                                item_size = item.size.get_text(strip=True) if item.size else -1
                                for attr in item.find_all(["newznab:attr", "torznab:attr"]):
                                    item_size = attr["value"] if attr["name"] == "size" else item_size
                                    seeders = try_int(attr["value"]) if attr["name"] == "seeders" else seeders
                                    leechers = try_int(attr["value"]) if attr["name"] == "peers" else leechers

                            if not item_size or (self.torznab and (seeders is None or leechers is None)):
                                continue

                            size = convert_size(item_size) or -1

                            result = {"title": title, "link": download_url, "size": size, "seeders": seeders, "leechers": leechers}
                            items.append(result)
                        except Exception:
                            continue

                # Since we aren't using the search string,
                # break out of the search string loop
                if "tvdbid" in search_params:
                    break

            if self.torznab:
                results.sort(key=lambda d: try_int(d.get("seeders", 0)), reverse=True)
            results += items

        return results

    def _get_size(self, item):
        """
        Gets size info from a result item
        Returns int size or -1
        """
        return try_int(item.get("size", -1), -1)


Provider = NewznabProvider
