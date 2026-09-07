"""Built-in Jackett Torznab provider (torrent search; does not require USE_NZBS)."""

from __future__ import annotations

import ipaddress
import time
from urllib.parse import urljoin, urlsplit, urlunsplit

from sickchill import logger, settings
from sickchill.helper.common import try_int
from sickchill.oldbeard import tvcache
from sickchill.oldbeard.bs4_parser import BS4Parser
from sickchill.oldbeard.common import cpu_presets
from sickchill.providers.torrent.TorrentProvider import TorrentProvider


class Provider(TorrentProvider, tvcache.RSSTorrentMixin):
    """Jackett aggregator via Torznab API — enabled under torrent search only.

    Named Jackett-SC (id ``jackett_sc``) so it does not collide with Custom Newznab
    entries named ``Jackett`` from older setup guides.
    """

    def __init__(self):
        super().__init__("Jackett-SC")

        self.public = False
        self.supports_backlog = True

        self.custom_url = "http://127.0.0.1:9117"
        self.api_key = "9dxv8e0lv3z9os1lzqt97klpucon60z8"
        self.indexer = "all"
        self.categories = "5000,5030,5040,5045,5050,5060,5070"
        self.minseed = 1
        self.minleech = 0

        self.search_mode = "episode"
        self.search_fallback = False
        self.enable_daily = True
        self.enable_backlog = True

        self._caps = False
        self.use_tv_search = None
        self.cap_tv_search = None

        self.url = self.custom_url
        self.cache = tvcache.TVCache(self, min_time=30)

    def image_name(self):
        import os

        icon = "jackett.png"
        path = os.path.join(settings.PROG_DIR, "gui", settings.GUI_NAME, "images", "providers", icon)
        if os.path.isfile(path):
            return icon
        return "newznab.png"

    @staticmethod
    def _normalize_jackett_base(url: str) -> str:
        """Strip query/fragment and trailing slash so path suffix checks stay valid."""
        parts = urlsplit((url or "").strip())
        path = (parts.path or "").rstrip("/")
        return urlunsplit((parts.scheme, parts.netloc, path, "", ""))

    @classmethod
    def _url_allows_apikey_transport(cls, url: str) -> bool:
        """Allow apikey query params over HTTPS, or HTTP only for loopback endpoints."""
        parts = urlsplit((url or "").strip())
        scheme = (parts.scheme or "").lower()
        if scheme == "https":
            return True
        if scheme != "http":
            return False

        host = (parts.hostname or "").lower().rstrip(".")
        if not host:
            return False
        if host in ("localhost", "127.0.0.1", "::1") or host.endswith(".localhost"):
            return True

        try:
            return bool(ipaddress.ip_address(host).is_loopback)
        except ValueError:
            # Any non-loopback hostname (LAN, docker, public) requires HTTPS
            return False

    @property
    def torznab_url(self) -> str:
        """Build Jackett Torznab API URL.

        Official form (Jackett README)::

            http://host:9117/api/v2.0/indexers/<indexer>/results/torznab/api

        Accepts a bare Jackett base URL, a Torznab feed path (with or without trailing
        ``/api``), or an indexer id of ``all`` / a single configured indexer.
        """
        raw = self._normalize_jackett_base(self.custom_url or "http://127.0.0.1:9117")
        lowered = raw.lower()

        # Already a Torznab API endpoint
        if lowered.endswith(("/torznab/api", "/results/torznab/api")):
            return raw

        # Torznab feed root without /api — append it (Jackett query syntax)
        if "/results/torznab" in lowered or lowered.endswith("/torznab"):
            return raw + "/api"

        indexer = (self.indexer or "all").strip().strip("/") or "all"
        return urljoin(raw + "/", f"api/v2.0/indexers/{indexer}/results/torznab/api")

    def _check_auth(self) -> bool:
        if not (self.api_key or "").strip():
            logger.warning(_("Jackett API key is not set. Check your provider settings."))
            return False
        if self.invalid_url(self.custom_url or ""):
            logger.warning(_("Invalid Jackett URL. Check your provider settings."))
            return False
        # apikey is sent as a query param — require HTTPS except for loopback HTTP
        if not self._url_allows_apikey_transport(self.torznab_url):
            logger.warning(
                _(
                    "Jackett URL must use HTTPS when the API key is sent in the query string. "
                    "HTTP is only allowed for loopback addresses (localhost / 127.0.0.1 / ::1)."
                )
            )
            return False
        return True

    @staticmethod
    def _is_tv_category(cat_id, name: str) -> bool:
        """Torznab TV cats are 5000-5999; also match TV/Television names."""
        name_u = (name or "").upper()
        if "TV" in name_u or "TELEVISION" in name_u:
            return True
        try:
            return 5000 <= int(cat_id) <= 5999
        except (TypeError, ValueError):
            return False

    def get_jackett_categories(self, just_caps: bool = False):
        """Fetch Torznab caps (TV categories) from Jackett."""
        return_categories = []
        if not self._check_auth():
            return False, return_categories, "Jackett requires a URL and API key"

        params = {"t": "caps", "apikey": self.api_key}
        # Do not follow redirects — apikey is in the query string
        data = self.get_url(self.torznab_url, params=params, returns="text", allow_redirects=False)
        if not data:
            error_string = f"Error getting caps xml for [{self.name}]"
            logger.warning(error_string)
            return False, return_categories, error_string

        with BS4Parser(data, language="xml") as html:
            if not html.find("categories"):
                error_string = f"Error parsing caps xml for [{self.name}]"
                logger.debug(error_string)
                return False, return_categories, error_string

            self.caps = html.find("searching")
            if just_caps:
                return True, return_categories, "Just checking caps!"

            seen_ids = set()
            for category in html("category"):
                cat_id = category.get("id", "")
                cat_name = category.get("name", "")
                if not cat_id or not self._is_tv_category(cat_id, cat_name):
                    continue
                if cat_id not in seen_ids:
                    return_categories.append({"id": cat_id, "name": cat_name or cat_id})
                    seen_ids.add(cat_id)
                for subcat in category("subcat"):
                    sub_id = subcat.get("id", "")
                    sub_name = subcat.get("name", "")
                    if not sub_id or sub_id in seen_ids:
                        continue
                    # Subcats under a TV parent are TV even if the name omits "TV"
                    return_categories.append({"id": sub_id, "name": sub_name or sub_id})
                    seen_ids.add(sub_id)

            if not return_categories:
                return False, return_categories, f"No TV categories found in caps for [{self.name}]"

            return True, return_categories, ""

    @property
    def caps(self):
        return self._caps

    @caps.setter
    def caps(self, data):
        elm = data.find("tv-search") if data else None
        self.use_tv_search = bool(elm and elm.get("available") == "yes")
        if self.use_tv_search:
            self.cap_tv_search = elm.get("supportedParams", "tvdbid,season,ep")
        self._caps = True  # Jackett always searchable via q even without tvsearch caps

    def check_auth_from_data(self, data) -> bool:
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

    def search(self, search_strings):
        results = []
        if not self._check_auth():
            return results

        if not self.caps:
            self.get_jackett_categories(just_caps=True)

        for mode in search_strings:
            search_params = {
                "t": ("search", "tvsearch")[bool(self.use_tv_search)],
                "limit": 100,
                "offset": 0,
                "cat": (self.categories or "5030,5040").strip(", "),
                "apikey": self.api_key,
            }
            # Do not send USENET_RETENTION as maxage for Jackett torrents

            # Aggregate "all" mixes indexers poorly with tvdbid/season/ep (Jackett README).
            use_structured_tv = bool(self.use_tv_search and self.show and (self.indexer or "all").strip().lower() != "all")
            # Air-date / sports structured search sets q=airdate; do not overwrite with search_string.
            preserve_airdate_q = False

            if mode != "RSS" and use_structured_tv:
                if self.cap_tv_search and "tvdbid" in str(self.cap_tv_search):
                    search_params["tvdbid"] = self.show.indexerid

                if self.show.air_by_date or self.show.sports:
                    if self.current_episode_object:
                        search_params["q"] = str(self.current_episode_object.airdate)
                        preserve_airdate_q = True
                elif self.show.is_anime:
                    if self.current_episode_object:
                        search_params["ep"] = self.current_episode_object.absolute_number
                elif self.current_episode_object:
                    # Jackett: t=tvsearch&q=Title&season=1&ep=2
                    search_params["season"] = self.current_episode_object.scene_season
                    search_params["ep"] = self.current_episode_object.scene_episode

                if mode == "Season":
                    search_params.pop("ep", None)

            items = []
            logger.debug(_("Search Mode: {mode}").format(mode=mode))
            for search_string in {*search_strings[mode]}:
                if mode != "RSS":
                    logger.debug(_("Search String: {search_string}").format(search_string=search_string))
                    # Jackett tvsearch still uses q= for the show title alongside season/ep
                    if not preserve_airdate_q:
                        search_params["q"] = search_string

                time.sleep(cpu_presets[settings.CPU_PRESET])
                data = self.get_url(self.torznab_url, params=search_params, returns="text", allow_redirects=False)
                if not data:
                    logger.debug(_("No data was returned from the provider"))
                    break

                with BS4Parser(data, language="xml") as html:
                    if not self.check_auth_from_data(html):
                        break

                    for item in html("item"):
                        try:
                            result = self.parse_feed_item(item, self.torznab_url)
                            if not result:
                                continue
                            seeders = try_int(result.get("seeders"), 0)
                            leechers = try_int(result.get("leechers"), 0)
                            if seeders < self.minseed or leechers < self.minleech:
                                if mode != "RSS":
                                    logger.debug(
                                        "Discarding torrent because it doesn't meet the minimum seeders or leechers: "
                                        f"{result.get('title')} (S:{seeders} L:{leechers})"
                                    )
                                continue
                            items.append(result)
                        except Exception:  # noqa: S112
                            continue

                if "tvdbid" in search_params:
                    break

            items.sort(key=lambda d: try_int(d.get("seeders", 0)), reverse=True)
            results += items

        return results

    def _get_size(self, item):
        return try_int(item.get("size", -1), -1)


def warn_jackett_newznab_overlap() -> None:
    """Warn-only: Custom Newznab entries that collide with or look like Jackett/Torznab."""
    jackett = next((p for p in (settings.providerList or []) if p.get_id() == "jackett_sc"), None)
    builtin_ids = {p.get_id() for p in (settings.providerList or [])}

    for provider in settings.newznab_provider_list or []:
        provider_id = provider.get_id()
        url = (getattr(provider, "url", None) or "").lower()
        name_l = (provider.name or "").lower()

        # Same id as a built-in (e.g. custom named Jackett-SC) hides that built-in in priorities
        if provider_id in builtin_ids:
            logger.warning(
                _(
                    "Custom Newznab provider '{name}' conflicts with built-in id '{provider_id}'. "
                    "Rename or delete it under Configure Custom Newznab Providers, then enable the "
                    "built-in Jackett-SC torrent provider (Torrent Search — NZB search is not required)."
                ).format(name=provider.name, provider_id=provider_id)
            )
            continue

        if not jackett or not jackett.enabled:
            continue

        if name_l == "jackett" or "torznab" in url or "jackett" in url or "/indexers/" in url:
            logger.warning(
                _(
                    "Custom Newznab provider '{name}' looks like Jackett/Torznab. "
                    "Prefer the built-in Jackett-SC torrent provider (Search Providers) and disable this "
                    "Newznab entry to avoid duplicate searches. NZB search is not required for Jackett-SC."
                ).format(name=provider.name)
            )
