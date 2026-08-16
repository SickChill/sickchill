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


def _pick_translation_map_value(mapping, language: str | None) -> str:
    """Pick a non-empty string from a TVDB TranslationSimple map for language candidates."""
    if not isinstance(mapping, dict) or not language:
        return ""
    for code in _tvdb_language_candidates(language):
        val = mapping.get(code)
        if val is not None and str(val).strip():
            return str(val).strip()
    return ""


def _search_result_display_name(item: dict, language: str | None) -> str:
    """
    Preferred series title for addShows search list.

    V4 /search returns the original/primary title in ``name`` (e.g. ダンジョン飯) and
    language titles in ``translations`` (TranslationSimple: eng, jpn, ita, …). Prefer
    the metadata language selected on the addShows page.
    """
    if not isinstance(item, dict):
        return ""
    primary = (item.get("name") or item.get("seriesName") or item.get("title") or "").strip()
    if not language:
        return primary

    translated = _pick_translation_map_value(item.get("translations"), language)
    if translated:
        return translated

    # Primary language already matches the requested metadata language
    primary_lang = (item.get("primary_language") or "").strip().lower()
    if primary_lang and primary_lang in set(_tvdb_language_candidates(language)):
        return primary

    name_translated = item.get("name_translated")
    if isinstance(name_translated, dict):
        from_map = _pick_translation_map_value(name_translated, language)
        if from_map:
            return from_map
    elif isinstance(name_translated, str) and name_translated.strip():
        return name_translated.strip()

    return primary


def _search_result_overview(item: dict, language: str | None) -> str:
    """Preferred overview for search hits using overviews TranslationSimple when present."""
    if not isinstance(item, dict):
        return ""
    translated = _pick_translation_map_value(item.get("overviews"), language)
    if translated:
        return translated
    return (item.get("overview") or "").strip()


def _raw_search_score(item: dict) -> float:
    """
    Extract a numeric score from a V4 search hit.

    Search payloads may include popularity ``score``, Algolia-style ``_score``,
    or omit both (rely on result order). Returns 0.0 when nothing usable is present.
    """
    if not isinstance(item, dict):
        return 0.0
    for key in ("score", "_score", "relevance", "weight"):
        val = item.get(key)
        if val is None or val == "":
            continue
        try:
            return float(val)
        except (TypeError, ValueError):
            continue
    return 0.0


def _normalize_search_scores(mapped: list) -> list:
    """
    Turn raw scores into 0–100 integers for UI sort/display.

    - If any raw score > 0: scale each as percent of the max in this result set.
    - If all raw scores are 0: use reverse list position (API already ranks best first).
    """
    if not mapped:
        return mapped
    raw_scores = []
    for item in mapped:
        try:
            raw_scores.append(float(item.get("score") or 0))
        except (TypeError, ValueError):
            raw_scores.append(0.0)
    max_raw = max(raw_scores) if raw_scores else 0.0
    n = len(mapped)
    for i, item in enumerate(mapped):
        if max_raw > 0:
            pct = round(100.0 * raw_scores[i] / max_raw)
        else:
            # Preserve API ranking: first hit ≈ 100, later hits lower
            pct = round(100.0 * (n - i) / n) if n else 0
        item["score"] = max(0, min(100, pct))
    return mapped


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
        # True only when both required entity feeds (series + episodes) succeed (even if empty).
        # False on any TVDBv4Error so ShowUpdater does not advance lastUpdate for a partial feed.
        self.feed_ok = False
        # Do not set self.series here — it would shadow the series() method
        # (tvdbsimple only assigns the attribute after series() is called).

    def series(self):
        """Collect series IDs from V4 series + episode update streams since from_time."""
        records: list = []
        failed_types: list[str] = []
        for entity_type in ("series", "episodes"):
            try:
                records.extend(self._client.all_updates_since(self._from_time, entity_type=entity_type))
            except TVDBv4Error as error:
                failed_types.append(entity_type)
                logger.debug(f"TVDB v4 updates failed ({entity_type}): {error}")

        # Both entity types must succeed; partial success is treated as feed failure
        self.feed_ok = not failed_types
        if failed_types:
            # Distinguish feed failure (partial or total) from a successful empty change list
            self.series = []
            logger.warning(f"TVDB v4 update feed failed for entity type(s) {', '.join(failed_types)} since {self._from_time}")
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
                # key: (show_id, season_type, lang)
                show_id, season_type = key[0], key[1]
                lang = key[2] if len(key) > 2 else None
                for ikey in list(self._episode_index_cache):
                    # ikey: (show_id, season_type, lang, season, episode)
                    if ikey[0] != show_id or ikey[1] != season_type:
                        continue
                    if lang is not None and len(ikey) > 2 and ikey[2] != lang:
                        continue
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

    def _all_episodes_for_language(self, show_id, season_type: str, language: str | None) -> list:
        """
        Fetch episode list preferring translated titles for show metadata language.

        Tries TVDB language candidates (en→eng, …). Falls back to the untranslated
        endpoint if every translated request fails.
        """
        candidates = _tvdb_language_candidates(language)
        errors: list[str] = []
        for code in candidates:
            try:
                eps = self.client.all_episodes(show_id, season_type, language=code)
                logger.debug(f"TVDB v4 episodes for {show_id} using language={code!r} ({len(eps)} ep(s))")
                return eps
            except TVDBv4Error as error:
                errors.append(f"{code}:{error}")
                logger.debug(f"TVDB v4 translated episodes failed for {show_id}/{code}: {error}")

        # No language requested, or all translated paths failed — primary/original names
        if candidates:
            logger.debug(f"TVDB v4 falling back to untranslated episodes for {show_id} (tried {', '.join(candidates)}; errors: {'; '.join(errors) or 'none'})")
        return self.client.all_episodes(show_id, season_type, language=None)

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

    @staticmethod
    def resolve_season_type(show) -> str:
        """V4 path segment for episode lists: seasons_order, else legacy dvdorder."""
        if hasattr(show, "resolved_seasons_order"):
            return show.resolved_seasons_order
        raw = getattr(show, "seasons_order", None)
        if isinstance(raw, str) and raw.strip():
            return raw.strip().lower()
        return "dvd" if getattr(show, "dvdorder", False) else "default"

    # Cache payload format version (bump when label/dedupe rules change so stale rows refetch)
    _SEASON_TYPES_CACHE_VERSION = 3

    # V4 path slugs that both mean aired order on the site; store/API path uses "default"
    _SEASON_TYPE_AIRED_SLUGS = frozenset({"default", "official"})

    def seasons_order_label(self, series_id, slug: str | None = None) -> str:
        """
        TVDB display name for a stored seasons_order slug (editShow / displayShow).

        Labels are series-specific: e.g. slug ``alternate`` may show as BBC iPlayer
        on one show and a different platform name on another — never hard-map alternate.
        """
        slug = (slug or "default").strip().lower() or "default"
        if slug == "official":
            slug = "default"
        for item in self.series_season_types(series_id) or []:
            if item.get("slug") == slug:
                return item.get("name") or self._season_type_display_name(slug)
        return self._season_type_display_name(slug)

    def series_season_types(self, series_id, use_cache: bool = True) -> list[dict]:
        """
        Available season order types for a series (editShow picker).

        Returns list of {slug, name}:
          - slug: V4 path / DB value (default, dvd, absolute, alternate, …)
          - name: TVDB display string for *this* series (Aired Order, Absolute Order,
            or a platform title such as BBC iPlayer / Netflix when that is the named order)
        Uses cache.db for 1 day when use_cache=True.
        """
        import json
        import time as _time

        from sickchill.oldbeard import db as sc_db

        series_id = int(series_id)
        cache_ttl = 24 * 60 * 60
        cache_db = sc_db.DBConnection("cache.db")
        try:
            cache_db.action("CREATE TABLE IF NOT EXISTS tvdb_season_types (indexer_id INTEGER PRIMARY KEY, payload TEXT, last_refreshed INTEGER)")
        except Exception:
            pass

        if use_cache:
            try:
                rows = cache_db.select(
                    "SELECT payload, last_refreshed FROM tvdb_season_types WHERE indexer_id = ?",
                    [series_id],
                )
                if rows:
                    last = int(rows[0]["last_refreshed"] or 0)
                    if _time.time() - last < cache_ttl:
                        envelope = json.loads(rows[0]["payload"] or "{}")
                        if isinstance(envelope, dict) and envelope.get("v") == self._SEASON_TYPES_CACHE_VERSION:
                            data = envelope.get("types") or []
                            if isinstance(data, list) and data:
                                return data
            except Exception as error:
                logger.debug(f"TVDB season types cache read failed for {series_id}: {error}")

        types = self._fetch_series_season_types(series_id)
        try:
            payload = json.dumps({"v": self._SEASON_TYPES_CACHE_VERSION, "types": types})
            cache_db.action(
                "INSERT OR REPLACE INTO tvdb_season_types (indexer_id, payload, last_refreshed) VALUES (?, ?, ?)",
                [series_id, payload, int(_time.time())],
            )
        except Exception as error:
            logger.debug(f"TVDB season types cache write failed for {series_id}: {error}")
        return types

    @staticmethod
    def _season_type_display_name(slug: str, api_name: str | None = None) -> str:
        """UI label: prefer TVDB name/alternateName as returned; generic fallback by slug only."""
        label = (api_name or "").strip()
        if label:
            return label
        slug_l = (slug or "").strip().lower()
        # Only when API omitted a name — never invent platform titles (those vary per series)
        fallback = {
            "default": "Aired Order",
            "official": "Aired Order",
            "dvd": "DVD Order",
            "absolute": "Absolute Order",
            "alternate": "Alternate Order",
            "regional": "Regional Order",
        }
        return fallback.get(slug_l, slug_l or "Aired Order")

    def _fetch_series_season_types(self, series_id: int) -> list[dict]:
        """
        Build unique {slug, name} list from series.extended seasonTypes.

        - slug: V4 path segment stored in tv_shows.seasons_order (default, dvd, absolute,
          alternate, regional, or any other type string TVDB returns for the series)
        - name: TVDB display for this series — prefer alternateName then name
          (platform-named orders use alternateName, e.g. one show's alternate → "BBC iPlayer",
          another's alternate → a different service; other slugs may be platform-specific too)

        Only collapse official + default → default (both are aired). Do not merge distinct
        path slugs: each TVDB type is a separate selectable order.
        """
        # slug -> display name from TVDB for this series only
        by_slug: dict[str, str] = {}

        try:
            raw = self.client.series_extended(series_id) or {}
        except TVDBv4Error as error:
            logger.debug(f"TVDB series_extended for season types failed ({series_id}): {error}")
            raw = {}

        def _add(slug, api_name=None):
            if not slug:
                return
            slug = str(slug).strip().lower()
            if not slug:
                return
            # Collapse official → default (both aired); keep best display name
            if slug in self._SEASON_TYPE_AIRED_SLUGS:
                slug = "default"
            label = self._season_type_display_name(slug, api_name)
            if slug not in by_slug:
                by_slug[slug] = label
            else:
                # Prefer a more specific TVDB label over generic fallback / slug
                existing = by_slug[slug]
                if api_name and (existing.lower() in (slug, "aired order", "alternate order") or len(str(api_name)) > len(existing)):
                    by_slug[slug] = str(api_name).strip()

        # Primary: seasonTypes on series.extended (one row per distinct type slug)
        for item in raw.get("seasonTypes") or []:
            if not isinstance(item, dict):
                continue
            slug = item.get("type")
            if not slug or not isinstance(slug, str):
                continue
            # Prefer alternateName (often the platform/show-specific title), else name
            label_src = item.get("alternateName") or item.get("name")
            _add(slug, label_src)

        # Secondary: seasons may reference types not listed on seasonTypes
        for season in raw.get("seasons") or []:
            if not isinstance(season, dict):
                continue
            st = season.get("type") or season.get("seasonType") or {}
            if isinstance(st, dict):
                slug = st.get("type")
                if slug and isinstance(slug, str):
                    _add(slug, st.get("alternateName") or st.get("name"))

        if "default" not in by_slug:
            _add("default", "Aired Order")

        # Well-known types first; any other TVDB type slugs (platform-specific, etc.) after
        priority = {"default": 0, "dvd": 1, "absolute": 2, "alternate": 3, "regional": 4}
        ordered = sorted(by_slug.items(), key=lambda kv: (priority.get(kv[0], 50), kv[1].lower(), kv[0]))
        return [{"slug": slug, "name": name} for slug, name in ordered]

    @ExceptionDecorator()
    def episodes(self, show, season=None):
        import time as _time

        self._prune_episode_cache()
        season_type = self.resolve_season_type(show)
        # Metadata language from the show (addShows / edit show); drives translated episode titles
        raw_lang = getattr(show, "lang", None)
        show_lang = raw_lang.strip().lower() if isinstance(raw_lang, str) else ""
        cache_key = (int(show.indexerid), season_type, show_lang)
        cached = self._episode_list_cache.get(cache_key)
        now = _time.monotonic()
        if cached is None or (now - cached[0]) > self._episode_cache_ttl:
            all_eps = self._all_episodes_for_language(show.indexerid, season_type, show_lang or None)
            mapped = [_episode_dict(e) for e in all_eps if isinstance(e, dict)]
            # Drop any prior index rows for this show+type+lang before re-index
            for ikey in list(self._episode_index_cache):
                if ikey[0] == int(show.indexerid) and ikey[1] == season_type and (len(ikey) < 3 or ikey[2] == show_lang):
                    del self._episode_index_cache[ikey]
            self._episode_list_cache[cache_key] = (now, mapped)
            for ep in mapped:
                s, e = ep.get("airedSeason"), ep.get("airedEpisodeNumber")
                if s is None or e is None:
                    continue
                self._episode_index_cache[(int(show.indexerid), season_type, show_lang, int(s), int(e))] = ep
            # Bound after insert so a newly cached show cannot leave the map oversized
            self._prune_episode_cache()
            logger.debug(f"TVDB v4 cached {len(mapped)} episode(s) for show {show.indexerid} ({season_type}, lang={show_lang or 'primary'})")
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

        season_type = self.resolve_season_type(show)
        raw_lang = getattr(show, "lang", None)
        show_lang = raw_lang.strip().lower() if isinstance(raw_lang, str) else ""
        index_key = (int(show.indexerid), season_type, show_lang, int(season), int(episode))
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
            return self._map_search_results(raw_results, language=language)

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
                            "score": 100,  # exact id match (0–100 display scale)
                            "source": "tvdb",
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
                # Pass language only for client-side translation selection on results —
                # not as /search?language= filter (that restricts primary language and
                # would hide anime like Delicious in Dungeon when metadata lang is eng).
                raw_results = self.client.search(attempt, language=language)
                if raw_results:
                    break
            except TVDBv4Error as error:
                # 404 / empty is normal for no match
                logger.debug(f"theTVDB v4 name search failed for '{attempt}': {error}")
            except Exception:
                logger.debug(traceback.format_exc())

        result = self._map_search_results(raw_results, language=language)

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
                                        "score": 0.0,
                                        "source": "tvmaze",
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
    def _map_search_results(raw_results, language: str | None = None) -> list:
        """Map V4 SearchResult payloads; seriesName/overview prefer metadata language."""
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
                    "seriesName": _search_result_display_name(item, language),
                    "firstAired": item.get("first_air_time") or item.get("firstAired") or item.get("year") or "",
                    "overview": _search_result_overview(item, language),
                    "network": item.get("network") or "",
                    "image_url": item.get("image_url") or item.get("thumbnail") or item.get("poster") or "",
                    # Raw popularity/relevance; normalized to 0–100 int after mapping
                    "score": _raw_search_score(item),
                    "status": item.get("status") or "",
                    "year": item.get("year") or "",
                    "source": item.get("source") or "tvdb",
                }
            )
        return _normalize_search_scores(mapped)

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
