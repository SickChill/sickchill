from sickchill import logger, settings
from sickchill.helper.common import try_int
from sickchill.oldbeard import tvcache
from sickchill.providers.nzb.NZBProvider import NZBProvider


class Provider(NZBProvider):
    def __init__(self):
        super().__init__("OMGWTFNZBs")

        self.username = None
        self.api_key = None

        self.cache = OmgwtfnzbsCache(self)

        self.url = "https://omgwtfnzbs.me/"
        self.urls = {"rss": "https://rss.omgwtfnzbs.me/rss-download.php", "api": "https://api.omgwtfnzbs.me/json/"}

        self.proper_strings = [".PROPER.", ".REPACK."]

    def _check_auth(self):

        if not self.username or not self.api_key:
            logger.warning("Invalid api key. Check your settings")
            return False

        return True

    def _check_auth_from_data(self, parsed_data, is_XML=True):

        if not parsed_data:
            return self._check_auth()

        if is_XML:
            # provider doesn't return xml on error
            return True

        if "notice" in parsed_data:
            description_text = parsed_data.get("notice")
            if "information is incorrect" in description_text:
                logger.warning("Invalid api key. Check your settings")
            elif "0 results matched your terms" not in description_text:
                logger.debug("Unknown error: {0}".format(description_text))
            return False

        return True

    def _get_title_and_url(self, item):
        return item["release"], item["getnzb"]

    def _get_size(self, item):
        return try_int(item["sizebytes"], -1)

    def search(self, search_strings, age=0, ep_obj=None):
        results = []
        if not self._check_auth():
            return results

        search_params = {
            "user": self.username,
            "api": self.api_key,
            "eng": 1,
            "catid": "19,20,30",  # SD,HD,UHD
            "retention": settings.USENET_RETENTION,
        }

        for mode in search_strings:
            items = []
            logger.debug(_("Search Mode: {mode}").format(mode=mode))
            for search_string in {*search_strings[mode]}:
                search_params["search"] = search_string
                if mode != "RSS":
                    logger.debug(_("Search String: {search_string}").format(search_string=search_string))

                data = self.get_url(self.urls["api"], params=search_params, returns="json")
                if not data:
                    logger.debug(_("No data returned from provider"))
                    continue

                if not self._check_auth_from_data(data, is_XML=False):
                    continue

                for item in data:
                    if not self._get_title_and_url(item):
                        continue

                    logger.debug(_("Found result: ") + f'{item.get("release")}')
                    items.append(item)

            results += items

        return results


class OmgwtfnzbsCache(tvcache.TVCache):
    def _get_title_and_url(self, item):
        title = item.get("title")
        if title:
            title = title.replace(" ", ".")

        url = item.get("link")
        if url:
            url = url.replace("&amp;", "&")

        return title, url

    def _get_rss_data(self):
        search_params = {
            "user": self.provider.username,
            "api": self.provider.api_key,
            "eng": 1,
            "catid": "19,20,30",  # SD,HD,UHD
        }
        return self.get_rss_feed(self.provider.urls["rss"], params=search_params)
