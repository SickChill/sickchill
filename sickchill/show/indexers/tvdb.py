import re
import traceback

import requests

from sickchill import logger, settings
from sickchill.tv import TVEpisode

from .base import Indexer
from .tvdb_v4_client import (
    ARTWORK_TYPE_BACKGROUND,
    ARTWORK_TYPE_BANNER,
    ARTWORK_TYPE_POSTER,
    ARTWORK_TYPE_SEASON_BANNER,
    ARTWORK_TYPE_SEASON_POSTER,
    TVDBv4Client,
    TVDBv4Error,
)
from .wrappers import ExceptionDecorator

# v4 remoteIds type for IMDb (confirmed empirically / used by wokka1 fork).
REMOTE_ID_TYPE_IMDB = 2

WEEKDAY_NAMES = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")

# Project API key for user-supported non-commercial use (shared by install base).
# Overridable via config.ini [General] tvdb_v4_apikey.
DEFAULT_TVDB_V4_APIKEY = "b304113c-3d1f-477e-ab6d-fdea3e363d50"


class _SeriesResult:
    """
    Attribute-access adapter over a v4 /series/{id}/extended response.

    Matches what tv.py / handler.py expect from the old tvdbsimple Series object
    (attribute access, optional .info(language) no-op).
    """

    def __init__(self, raw: dict, language: str | None = None):
        self._raw = raw or {}
        self.id = self._raw.get("id")
        self.seriesName = (self._raw.get("name") or "").strip()
        self.overview = self._raw.get("overview") or ""
        self.language = language

        status = self._raw.get("status") or {}
        if isinstance(status, dict):
            self.status = status.get("name") or "Unknown"
        else:
            self.status = str(status) if status else "Unknown"

        self.firstAired = self._raw.get("firstAired") or ""
        self.runtime = self._raw.get("averageRuntime") or self._raw.get("runtime") or ""
        self.genre = [g["name"] for g in (self._raw.get("genres") or []) if isinstance(g, dict) and g.get("name")]
        self.classification = "Scripted"

        self.network = ""
        for company in self._raw.get("companies") or []:
            if not isinstance(company, dict):
                continue
            company_type = company.get("companyType") or {}
            type_name = company_type.get("companyTypeName") if isinstance(company_type, dict) else None
            if type_name == "Network":
                self.network = company.get("name") or ""
                break
        if not self.network:
            original = self._raw.get("originalNetwork") or {}
            if isinstance(original, dict):
                self.network = original.get("name") or ""

        self.imdbId = ""
        for remote in self._raw.get("remoteIds") or []:
            if not isinstance(remote, dict):
                continue
            if remote.get("type") == REMOTE_ID_TYPE_IMDB:
                self.imdbId = remote.get("id") or ""
                break
            # Some payloads use sourceName instead of numeric type
            source = (remote.get("sourceName") or remote.get("typeName") or "").lower()
            if source == "imdb":
                self.imdbId = remote.get("id") or ""
                break

        self.airsDayOfWeek = ""
        airs_days = self._raw.get("airsDays") or {}
        if isinstance(airs_days, dict):
            for day in WEEKDAY_NAMES:
                if airs_days.get(day):
                    self.airsDayOfWeek = day.capitalize()
                    break
        self.airsTime = self._raw.get("airsTime") or ""

        self.artworks = self._raw.get("artworks") or []
        self.lastUpdated = self._raw.get("lastUpdated")

    def info(self, language=None):
        """No-op kept for call-site compatibility with tvdbsimple's lazy info()."""
        if language:
            self.language = language
        return self

    def __getitem__(self, key):
        return getattr(self, key)


def _episode_dict(raw: dict) -> dict:
    """Map a v4 episode object onto keys expected by TVEpisode.load_from_indexer."""
    return {
        "id": raw.get("id"),
        "airedSeason": raw.get("seasonNumber"),
        "airedEpisodeNumber": raw.get("number"),
        "episodeName": raw.get("name") or "",
        "absoluteNumber": raw.get("absoluteNumber"),
        "overview": raw.get("overview") or "",
        "firstAired": raw.get("aired") or "",
        "filename": raw.get("image") or "",
        "lastUpdated": raw.get("lastUpdated"),
    }


class _UpdatesResult:
    """
    Compatibility shim for show_updater.ShowUpdater which expects:

        data = indexer.updates(fromTime=..., toTime=...)
        data.series()
        for d in data.series: d['id']
    """

    def __init__(self, client: TVDBv4Client, from_time: int, to_time: int | str = "", language: str = ""):
        self._client = client
        self._from_time = int(from_time or 0)
        self._to_time = int(to_time) if to_time not in ("", None) else None
        self.language = language
        # Do not set self.series here — it would shadow the series() method
        # (tvdbsimple only assigns the attribute after series() is called).

    def series(self):
        try:
            records = self._client.all_updates_since(self._from_time, entity_type="series")
        except TVDBv4Error as error:
            logger.debug(f"TVDB v4 updates failed: {error}")
            result = []
            self.series = result
            return result

        ids = set()
        result = []
        for item in records:
            if not isinstance(item, dict):
                continue
            # Defensive: V4 update shapes vary (recordType, entityType, seriesId, id)
            record_type = item.get("recordType") or item.get("entityType") or item.get("method") or "series"
            if isinstance(record_type, str) and record_type.lower() not in ("series", "show", ""):
                # Skip non-series unless it carries a series id we can use
                series_id = item.get("seriesId") or item.get("series_id")
                if not series_id:
                    continue
            else:
                series_id = item.get("seriesId") or item.get("series_id") or item.get("recordId") or item.get("id")

            try:
                series_id = int(series_id)
            except (TypeError, ValueError):
                continue

            if self._to_time:
                # Optional upper bound if present on record
                ts = item.get("timeStamp") or item.get("timestamp") or item.get("time")
                try:
                    if ts is not None and int(ts) > self._to_time:
                        continue
                except (TypeError, ValueError):
                    pass

            if series_id not in ids:
                ids.add(series_id)
                result.append({"id": series_id})

        self.series = result  # attribute used by ShowUpdater after series() returns
        return result


class TVDB(Indexer):
    def __init__(self):
        super(TVDB, self).__init__()
        self.name = "theTVDB"
        self.slug = "tvdb"
        self.show_url = "https://thetvdb.com/?tab=series&id="
        self.base_url = "https://api4.thetvdb.com/v4/series/"
        self.icon = "images/indexers/thetvdb16.png"
        self._client: TVDBv4Client | None = None

    @property
    def api_key(self):
        return getattr(settings, "TVDB_V4_APIKEY", None) or DEFAULT_TVDB_V4_APIKEY

    @property
    def client(self) -> TVDBv4Client:
        pin = getattr(settings, "TVDB_V4_PIN", None) or ""
        timeout = getattr(settings, "INDEXER_TIMEOUT", None) or 20
        if self._client is None or self._client.apikey != self.api_key or (self._client.pin or "") != (pin or "") or self._client.timeout != timeout:
            self._client = TVDBv4Client(self.api_key, pin=pin, timeout=timeout)
        return self._client

    def updates(self, fromTime=0, toTime="", language=""):
        """V4-backed replacement for tvdbsimple.Updates used by ShowUpdater."""
        return _UpdatesResult(self.client, fromTime, toTime, language)

    @ExceptionDecorator()
    def series(self, *args, **kwargs):
        # Call sites: series(show), series(id), series(id=..., language=...)
        language = kwargs.get("language")
        indexerid = kwargs.get("id")
        if indexerid is None and args:
            first = args[0]
            if hasattr(first, "indexerid"):
                indexerid = first.indexerid
                language = language or getattr(first, "lang", None)
            else:
                indexerid = first
        if indexerid is None:
            indexerid = kwargs.get("indexerid")

        raw = self.client.series_extended(indexerid)
        if not raw:
            return None
        return _SeriesResult(raw, language)

    @ExceptionDecorator()
    def get_series_by_id(self, indexerid, language=None):
        return self.series(indexerid, language=language)

    @ExceptionDecorator()
    def series_from_show(self, show):
        return self.series(show)

    def series_from_episode(self, episode):
        return self.series_from_show(episode.show)

    def get_series_by_name(self, name, indexerid=None, language=None):
        if indexerid:
            return self.get_series_by_id(indexerid, language)

        try:
            results = self.search(name, language)
            if results:
                return self.get_series_by_id(results[0]["id"], language)
        except Exception:
            logger.debug(traceback.format_exc())
        return None

    @ExceptionDecorator()
    def episodes(self, show, season=None):
        season_type = "dvd" if getattr(show, "dvdorder", False) else "default"
        all_eps = self.client.all_episodes(show.indexerid, season_type)
        result = [_episode_dict(e) for e in all_eps if isinstance(e, dict)]
        if season is not None:
            result = [e for e in result if e.get("airedSeason") == season]
        return result

    @ExceptionDecorator()
    def episode(self, item, season=None, episode=None, **kwargs):
        if isinstance(item, TVEpisode):
            show = item.show
            season = item.season
            episode = item.episode
        else:
            show = item

        for ep in self.episodes(show, season):
            if ep.get("airedEpisodeNumber") == episode:
                return ep
        raise TVDBv4Error(f"Episode S{season}E{episode} not found")

    @ExceptionDecorator(default_return=list())
    def search(self, name, language=None, exact=False, indexer_id=False):
        """
        :param name: Show name to search for
        :param language: Preferred language (applied on full series fetch; search is global)
        :param exact: Exact when adding existing, processed when adding new shows
        :param indexer_id: Unused legacy flag
        :return: list of dicts with id / seriesName / firstAired (add_shows UI)
        """
        result = []
        if isinstance(name, bytes):
            name = name.decode()

        if not name:
            return result

        # IMDb id
        if re.match(r"^t?t?\d{7,8}$", name):
            try:
                imdb = f"tt{name.strip('t')}"
                raw_results = self.client.search_by_remote_id(imdb)
            except TVDBv4Error:
                logger.debug(traceback.format_exc())
                raw_results = []
            return self._map_search_results(raw_results)

        # Bare TVDB series id (6+ digits common for modern ids; also accept classic 5–7)
        if re.match(r"^\d{5,8}$", name.strip()):
            try:
                series = self.get_series_by_id(int(name.strip()), language)
                if series and series.id:
                    return [
                        {
                            "id": series.id,
                            "seriesName": series.seriesName,
                            "firstAired": series.firstAired,
                            "overview": series.overview,
                            "network": series.network,
                        }
                    ]
            except Exception:
                logger.debug(traceback.format_exc())
            return []

        names = [name]
        if not exact:
            test = re.match(r"^(.+?)[. _-]+\(\d{4}\)?$", name)
            if test:
                names.append(test.group(1).strip())
            if re.search(r"[. _-]", name):
                names.append(re.sub(r"[. _-]", " ", name).strip())
                if test:
                    names.append(re.sub(r"[. _-]", " ", test.group(1)).strip())

        raw_results = []
        for attempt in dict.fromkeys(n for n in names if n and n.strip()):
            try:
                raw_results = self.client.search(attempt)
                if raw_results:
                    break
            except TVDBv4Error as error:
                # 404 / empty is normal for no match
                logger.debug(f"theTVDB v4 name search failed for '{attempt}': {error}")
            except Exception:
                logger.debug(traceback.format_exc())

        result = self._map_search_results(raw_results)

        # TVmaze fallback only when TVDB found nothing (same behaviour as before)
        if not result:
            try:
                from . import tvmaze

                seen_ids = set()
                for attempt in dict.fromkeys(n for n in names if n and n.strip()):
                    for show in tvmaze.search(attempt):
                        tvdb_id = (show.get("externals") or {}).get("thetvdb")
                        if not tvdb_id or tvdb_id in seen_ids:
                            continue
                        try:
                            series = self.get_series_by_id(int(tvdb_id), language)
                            if series and series.id:
                                result.append(
                                    {
                                        "id": series.id,
                                        "seriesName": series.seriesName,
                                        "firstAired": series.firstAired,
                                        "overview": series.overview,
                                        "network": series.network,
                                    }
                                )
                                seen_ids.add(tvdb_id)
                        except Exception:
                            logger.debug(traceback.format_exc())
                    if result:
                        break
            except Exception:
                logger.debug(traceback.format_exc())

        return result or []

    @staticmethod
    def _map_search_results(raw_results) -> list:
        mapped = []
        seen = set()
        for item in raw_results or []:
            if not isinstance(item, dict):
                continue
            tvdb_id = item.get("tvdb_id") or item.get("id") or ""
            if isinstance(tvdb_id, str):
                tvdb_id = tvdb_id.replace("series-", "")
            try:
                tvdb_id = int(tvdb_id)
            except (TypeError, ValueError):
                continue
            if tvdb_id in seen:
                continue
            seen.add(tvdb_id)
            mapped.append(
                {
                    "id": tvdb_id,
                    "seriesName": item.get("name") or item.get("seriesName") or "",
                    "firstAired": item.get("first_air_time") or item.get("firstAired") or item.get("year") or "",
                    "overview": item.get("overview") or "",
                    "network": item.get("network") or "",
                    "image_url": item.get("image_url") or item.get("thumbnail") or "",
                    "score": item.get("score"),
                    "status": item.get("status") or "",
                    "year": item.get("year") or "",
                }
            )
        return mapped

    @property
    def languages(self):
        return ["cs", "da", "de", "el", "en", "es", "fi", "fr", "he", "hr", "hu", "it", "ja", "ko", "nl", "no", "pl", "pt", "ru", "sl", "sv", "tr", "zh"]

    @property
    def lang_dict(self):
        # Legacy numeric language ids (UI still references these in places)
        return {
            "el": 20,
            "en": 7,
            "zh": 27,
            "it": 15,
            "cs": 28,
            "es": 16,
            "ru": 22,
            "nl": 13,
            "pt": 26,
            "no": 9,
            "tr": 21,
            "pl": 18,
            "fr": 17,
            "hr": 31,
            "de": 14,
            "da": 10,
            "fi": 11,
            "hu": 19,
            "ja": 25,
            "he": 24,
            "ko": 32,
            "sv": 8,
            "sl": 30,
        }

    @staticmethod
    def complete_image_url(location):
        """Return absolute artwork URL. V4 often already returns full https URLs."""
        if not location:
            return ""
        location = str(location).strip()
        if not location:
            return ""
        if location.startswith(("http://", "https://")):
            return location
        # Legacy relative banner path fallback
        return f"https://artworks.thetvdb.com/banners/{re.sub(r'^_cache/', '', location)}"

    @ExceptionDecorator(default_return="", catch=(requests.exceptions.RequestException, KeyError, IndexError, TypeError, Exception), image_api=True)
    def __call_images_api(self, show, artwork_type, multiple=False):
        series = self.series(show)
        if not series:
            return [] if multiple else ""

        images = [a for a in (series.artworks or []) if isinstance(a, dict) and a.get("type") == artwork_type]
        images.sort(key=lambda a: a.get("score") or 0, reverse=True)
        if not images:
            return [] if multiple else ""

        urls = [self.complete_image_url(img.get("image") or img.get("thumbnail") or "") for img in images]
        urls = [u for u in urls if u]
        if not urls:
            return [] if multiple else ""
        return urls if multiple else urls[0]

    @staticmethod
    @ExceptionDecorator()
    def actors(series):
        # Not consumed meaningfully for V4 yet; return empty list for metadata writers.
        return []

    def series_poster_url(self, show, thumb=False, multiple=False):
        return self.__call_images_api(show, ARTWORK_TYPE_POSTER, multiple=multiple)

    def series_banner_url(self, show, thumb=False, multiple=False):
        return self.__call_images_api(show, ARTWORK_TYPE_BANNER, multiple=multiple)

    def series_fanart_url(self, show, thumb=False, multiple=False):
        return self.__call_images_api(show, ARTWORK_TYPE_BACKGROUND, multiple=multiple)

    def season_poster_url(self, show, season, thumb=False, multiple=False):
        return self.__call_images_api(show, ARTWORK_TYPE_SEASON_POSTER, multiple=multiple)

    def season_banner_url(self, show, season, thumb=False, multiple=False):
        return self.__call_images_api(show, ARTWORK_TYPE_SEASON_BANNER, multiple=multiple)

    @ExceptionDecorator(default_return="", catch=(requests.exceptions.RequestException, KeyError, TypeError, TVDBv4Error))
    def episode_image_url(self, episode):
        filename = self.episode(episode).get("filename", "")
        return self.complete_image_url(filename)

    def episode_guide_url(self, show):
        return self.show_url + str(show.indexerid)

    def get_favorites(self):
        """V4 user favorites not implemented (plan: do not implement)."""
        return []

    @staticmethod
    def test_user_key(user, key):
        """V4 user favorites not implemented (plan: do not implement)."""
        logger.info("TVDB user favorites are not supported with the v4 API.")
        return False
