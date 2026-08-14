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

# SickChill uses 2-letter codes (INDEXER_DEFAULT_LANGUAGE / show.lang); TVDB v4 translation
# routes expect ISO 639-2/3 style codes (eng, zho, …). Try both when fetching.
_TVDB_LANG_CANDIDATES = {
    "en": ("eng", "en"),
    "zh": ("zho", "chi", "zh", "zh-cn", "zh-tw", "zh-hans", "zh-hant"),
    "cs": ("ces", "cze", "cs"),
    "da": ("dan", "da"),
    "de": ("deu", "ger", "de"),
    "el": ("ell", "gre", "el"),
    "es": ("spa", "es"),
    "fi": ("fin", "fi"),
    "fr": ("fra", "fre", "fr"),
    "he": ("heb", "he"),
    "hr": ("hrv", "hr"),
    "hu": ("hun", "hu"),
    "it": ("ita", "it"),
    "ja": ("jpn", "ja"),
    "ko": ("kor", "ko"),
    "nl": ("nld", "dut", "nl"),
    "no": ("nor", "nob", "no"),
    "pl": ("pol", "pl"),
    "pt": ("por", "pt"),
    "ru": ("rus", "ru"),
    "sl": ("slv", "sl"),
    "sv": ("swe", "sv"),
    "tr": ("tur", "tr"),
}


def _tvdb_language_candidates(language: str | None) -> list[str]:
    """Ordered TVDB language codes to try for a SickChill language setting."""
    if not language:
        return []
    raw = str(language).strip().lower().replace("_", "-")
    if not raw:
        return []
    base = raw.split("-", 1)[0]
    candidates: list[str] = []
    for code in _TVDB_LANG_CANDIDATES.get(base, ()):
        if code not in candidates:
            candidates.append(code)
    for code in (raw, base):
        if code and code not in candidates:
            candidates.append(code)
    return candidates


def _apply_series_translation(raw: dict, translation: dict | None) -> dict:
    """Overlay translated name/overview onto a series payload copy when present."""
    if not isinstance(translation, dict):
        return raw
    name = (translation.get("name") or translation.get("seriesName") or "").strip()
    overview = translation.get("overview")
    if overview is not None:
        overview = str(overview).strip()
    if not name and not overview:
        return raw
    updated = dict(raw)
    if name:
        updated["name"] = name
    if overview:
        updated["overview"] = overview
    return updated


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
        self.zap2itId = ""
        for remote in self._raw.get("remoteIds") or []:
            if not isinstance(remote, dict):
                continue
            rid = remote.get("id") or ""
            source = (remote.get("sourceName") or remote.get("typeName") or "").lower()
            if remote.get("type") == REMOTE_ID_TYPE_IMDB or source == "imdb":
                if not self.imdbId:
                    self.imdbId = rid
            elif ("zap2it" in source or source in ("tms", "tribune")) and not self.zap2itId:
                self.zap2itId = rid

        # Optional fields used by metadata writers (kodi/tivo/mede8er/mediabrowser)
        self.siteRating = self._raw.get("score")
        if self.siteRating is None:
            self.siteRating = self._raw.get("siteRating")
        self.rating = None
        self.contentRating = None
        for cr in self._raw.get("contentRatings") or []:
            if not isinstance(cr, dict):
                continue
            name = cr.get("name") or cr.get("contentRating") or ""
            if not name:
                continue
            # Prefer US/GB when present; otherwise first available
            country = (cr.get("country") or "").upper()
            if self.contentRating is None or country in ("USA", "US", "GBR", "GB"):
                self.contentRating = name
                self.rating = name
                if country in ("USA", "US"):
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
        # True if at least one entity-type feed call succeeded (even if empty).
        # False if every feed request failed — distinct from a successful empty feed.
        self.feed_ok = False
        # Do not set self.series here — it would shadow the series() method
        # (tvdbsimple only assigns the attribute after series() is called).

    def series(self):
        """Collect series IDs from V4 series + episode update streams since from_time."""
        records: list = []
        any_success = False
        for entity_type in ("series", "episodes"):
            try:
                records.extend(self._client.all_updates_since(self._from_time, entity_type=entity_type))
                any_success = True
            except TVDBv4Error as error:
                logger.debug(f"TVDB v4 updates failed ({entity_type}): {error}")

        self.feed_ok = any_success
        if not any_success:
            # Distinguish total feed failure from a successful empty change list
            self.series = []
            logger.warning(f"TVDB v4 update feed failed for all entity types since {self._from_time}")
            return self.series

        ids = set()
        result = []
        for item in records:
            if not isinstance(item, dict):
                continue
            # Defensive: V4 update shapes vary (recordType, entityType, seriesId, id)
            record_type = item.get("recordType") or item.get("entityType") or item.get("method") or "series"
            record_type_l = record_type.lower() if isinstance(record_type, str) else "series"
            if record_type_l in ("series", "show", ""):
                series_id = item.get("seriesId") or item.get("series_id") or item.get("recordId") or item.get("id")
            else:
                # Episode (or other) updates: require parent series id when present
                series_id = item.get("seriesId") or item.get("series_id")
                if not series_id:
                    continue

            try:
                series_id = int(series_id)
            except (TypeError, ValueError):
                continue

            if self._to_time:
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
        logger.debug(f"TVDB v4 updates since {self._from_time}: {len(result)} series id(s) changed")
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
        # In-memory episode list cache for a load cycle: (showid, season_type) -> (monotonic_ts, list[dict])
        self._episode_list_cache: dict[tuple, tuple[float, list]] = {}
        # (showid, season_type, season, episode) -> dict
        self._episode_index_cache: dict[tuple, dict] = {}
        self._episode_cache_ttl = 300.0  # seconds; reuse within a load, refresh afterward
        self._episode_cache_max_shows = 32  # bound process lifetime growth

    @property
    def api_key(self):
        """Project API key from settings only (sole default defined in settings.TVDB_V4_APIKEY)."""
        return (getattr(settings, "TVDB_V4_APIKEY", None) or "").strip()

    @property
    def client(self) -> TVDBv4Client:
        key = self.api_key
        pin = getattr(settings, "TVDB_V4_PIN", None) or ""
        timeout = getattr(settings, "INDEXER_TIMEOUT", None) or 20
        if self._client is None or self._client.apikey != key or (self._client.pin or "") != (pin or "") or self._client.timeout != timeout:
            self._client = TVDBv4Client(key, pin=pin, timeout=timeout)
        return self._client

    def updates(self, fromTime=0, toTime="", language=""):
        """V4-backed replacement for tvdbsimple.Updates used by ShowUpdater."""
        return _UpdatesResult(self.client, fromTime, toTime, language)

    def clear_episode_cache(self, show_id=None):
        """Drop in-memory episode caches (optionally for one show)."""
        if show_id is None:
            self._episode_list_cache.clear()
            self._episode_index_cache.clear()
            return
        show_id = int(show_id)
        for key in list(self._episode_list_cache):
            if key[0] == show_id:
                del self._episode_list_cache[key]
        for key in list(self._episode_index_cache):
            if key[0] == show_id:
                del self._episode_index_cache[key]

    def _prune_episode_cache(self):
        """Drop expired entries and bound unique show count."""
        import time as _time

        now = _time.monotonic()
        ttl = self._episode_cache_ttl
        for key, (ts, _data) in list(self._episode_list_cache.items()):
            if now - ts > ttl:
                del self._episode_list_cache[key]
                show_id, season_type = key
                for ikey in list(self._episode_index_cache):
                    if ikey[0] == show_id and ikey[1] == season_type:
                        del self._episode_index_cache[ikey]

        # Bound by unique show ids (oldest first)
        show_ids = []
        seen = set()
        for key, (ts, _data) in sorted(self._episode_list_cache.items(), key=lambda item: item[1][0]):
            sid = key[0]
            if sid not in seen:
                seen.add(sid)
                show_ids.append(sid)
        while len(show_ids) > self._episode_cache_max_shows:
            drop_id = show_ids.pop(0)
            self.clear_episode_cache(drop_id)

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

        # Always resolve the requested language (including English). V4 series.extended
        # returns the primary/original title (often Chinese for donghua); English is on
        # /translations/eng — skipping eng left titles stuck on 吞噬星空 for en shows.
        raw = self._with_series_translation(raw, indexerid, language)

        return _SeriesResult(raw, language)

    def _with_series_translation(self, raw: dict, indexerid, language: str | None) -> dict:
        """Fetch and apply the best matching series translation for language."""
        for code in _tvdb_language_candidates(language):
            try:
                translation = self.client.series_translation(indexerid, code)
            except TVDBv4Error as error:
                logger.debug(f"TVDB v4 translation fetch failed for {indexerid}/{code}: {error}")
                continue
            if not isinstance(translation, dict):
                continue
            # Endpoint may return a single object or a list of translation records
            if isinstance(translation.get("translations"), list):
                # Prefer exact language match inside a bulk payload
                chosen = None
                for item in translation["translations"]:
                    if not isinstance(item, dict):
                        continue
                    item_lang = (item.get("language") or item.get("languageCode") or "").lower()
                    if item_lang == code or item_lang.startswith(code[:2]):
                        chosen = item
                        break
                translation = chosen or next((i for i in translation["translations"] if isinstance(i, dict)), None)
            applied = _apply_series_translation(raw, translation)
            if applied is not raw:
                logger.debug(f"TVDB v4 applied translation {code!r} for series {indexerid}: {(raw.get('name') or '')!r} -> {(applied.get('name') or '')!r}")
                return applied
        return raw

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
        import time as _time

        self._prune_episode_cache()
        season_type = "dvd" if getattr(show, "dvdorder", False) else "default"
        cache_key = (int(show.indexerid), season_type)
        cached = self._episode_list_cache.get(cache_key)
        now = _time.monotonic()
        if cached is None or (now - cached[0]) > self._episode_cache_ttl:
            all_eps = self.client.all_episodes(show.indexerid, season_type)
            mapped = [_episode_dict(e) for e in all_eps if isinstance(e, dict)]
            # Drop any prior index rows for this show+type before re-index
            for ikey in list(self._episode_index_cache):
                if ikey[0] == int(show.indexerid) and ikey[1] == season_type:
                    del self._episode_index_cache[ikey]
            self._episode_list_cache[cache_key] = (now, mapped)
            for ep in mapped:
                s, e = ep.get("airedSeason"), ep.get("airedEpisodeNumber")
                if s is None or e is None:
                    continue
                self._episode_index_cache[(int(show.indexerid), season_type, int(s), int(e))] = ep
            # Bound after insert so a newly cached show cannot leave the map oversized
            self._prune_episode_cache()
            logger.debug(f"TVDB v4 cached {len(mapped)} episode(s) for show {show.indexerid} ({season_type})")
            result = mapped
        else:
            result = cached[1]
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

        season_type = "dvd" if getattr(show, "dvdorder", False) else "default"
        index_key = (int(show.indexerid), season_type, int(season), int(episode))
        cached = self._episode_index_cache.get(index_key)
        if cached is not None:
            return cached

        # Populate cache via bulk list (one HTTP for the show), then index lookup
        self.episodes(show)
        cached = self._episode_index_cache.get(index_key)
        if cached is not None:
            return cached
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

        # IMDb id — only with explicit tt prefix (bare 7–8 digit numbers are TVDB ids below)
        stripped = name.strip()
        if re.match(r"^tt\d{7,8}$", stripped, flags=re.IGNORECASE):
            try:
                imdb = "tt" + stripped[2:]
                raw_results = self.client.search_by_remote_id(imdb)
            except TVDBv4Error:
                logger.debug(traceback.format_exc())
                raw_results = []
            return self._map_search_results(raw_results)

        # Bare TVDB series id (5–8 digits; includes values that look like IMDb numbers without tt)
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

    def __call_images_api(self, show, artwork_type, multiple=False, thumb=False):
        """
        Return artwork URL(s). On failure return [] when multiple=True else "" —
        do not use ExceptionDecorator(default_return="") which becomes [] via `or []`.
        """
        empty = [] if multiple else ""
        try:
            series = self.series(show)
            if not series:
                return empty

            images = [a for a in (series.artworks or []) if isinstance(a, dict) and a.get("type") == artwork_type]
            images.sort(key=lambda a: a.get("score") or 0, reverse=True)
            if not images:
                return empty

            urls = []
            for img in images:
                if thumb:
                    location = img.get("thumbnail") or img.get("image") or ""
                else:
                    location = img.get("image") or img.get("thumbnail") or ""
                url = self.complete_image_url(location)
                if url:
                    urls.append(url)
            if not urls:
                return empty
            return urls if multiple else urls[0]
        except Exception as error:
            logger.debug(f"Could not load artwork type {artwork_type} for show: {error}")
            logger.debug(traceback.format_exc())
            return empty

    @staticmethod
    @ExceptionDecorator()
    def actors(series):
        # Not consumed meaningfully for V4 yet; return empty list for metadata writers.
        return []

    def series_poster_url(self, show, thumb=False, multiple=False):
        return self.__call_images_api(show, ARTWORK_TYPE_POSTER, multiple=multiple, thumb=thumb)

    def series_banner_url(self, show, thumb=False, multiple=False):
        return self.__call_images_api(show, ARTWORK_TYPE_BANNER, multiple=multiple, thumb=thumb)

    def series_fanart_url(self, show, thumb=False, multiple=False):
        return self.__call_images_api(show, ARTWORK_TYPE_BACKGROUND, multiple=multiple, thumb=thumb)

    def season_poster_url(self, show, season, thumb=False, multiple=False):
        # Show-level art only for now (no per-season filtering required).
        # Prefer season-type artwork when present on the series payload; else series poster.
        result = self.__call_images_api(show, ARTWORK_TYPE_SEASON_POSTER, multiple=multiple, thumb=thumb)
        if result:
            return result
        return self.__call_images_api(show, ARTWORK_TYPE_POSTER, multiple=multiple, thumb=thumb)

    def season_banner_url(self, show, season, thumb=False, multiple=False):
        # Show-level art only for now (no per-season id resolution).
        result = self.__call_images_api(show, ARTWORK_TYPE_SEASON_BANNER, multiple=multiple, thumb=thumb)
        if result:
            return result
        return self.__call_images_api(show, ARTWORK_TYPE_BANNER, multiple=multiple, thumb=thumb)

    def episode_image_url(self, episode):
        """Return episode image URL, or "" on failure (never a list)."""
        try:
            filename = self.episode(episode).get("filename", "")
            return self.complete_image_url(filename)
        except Exception as error:
            logger.debug(f"Could not load episode image: {error}")
            logger.debug(traceback.format_exc())
            return ""

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
