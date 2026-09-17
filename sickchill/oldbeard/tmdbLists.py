"""TMDB discovery lists for Add Shows (Phase 5a)."""

from __future__ import annotations

import time

from sickchill import logger, settings
from sickchill.oldbeard import helpers

TMDB_API_BASE = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w185"

# list_key -> API path
TMDB_LIST_PATHS = {
    "trending": "/trending/tv/week",
    "popular": "/tv/popular",
    "top_rated": "/tv/top_rated",
    "on_the_air": "/tv/on_the_air",
}

_CACHE_TTL = 20 * 60  # seconds (~15–30 min)
_list_cache: dict[str, tuple[float, list]] = {}


class TMDBListsError(Exception):
    """Raised when a TMDB list request fails."""


class TMDBMissingKeyError(TMDBListsError):
    """Raised when no TMDB API key is configured."""


def _api_key() -> str:
    return (getattr(settings, "TMDB_API_KEY", None) or "").strip()


def _session():
    session = helpers.make_session()
    session.headers.update({"User-Agent": "SickChill"})
    return session


def fetch_list(list_key: str) -> list[dict]:
    """
    Fetch one TMDB TV list. Returns normalized cards:
    {title, tmdb_id, rating, votes, poster_url, overview, year, source}
    """
    list_key = (list_key or "").strip().lower()
    path = TMDB_LIST_PATHS.get(list_key)
    if not path:
        raise TMDBListsError(f"Unknown TMDB list key: {list_key}")

    key = _api_key()
    if not key:
        raise TMDBMissingKeyError("TMDB API key is not configured")

    now = time.time()
    cached = _list_cache.get(list_key)
    if cached and now < cached[0]:
        return cached[1]

    url = f"{TMDB_API_BASE}{path}"
    params = {"api_key": key, "language": "en-US"}
    data = helpers.getURL(url, params=params, session=_session(), returns="json")
    if not isinstance(data, dict):
        raise TMDBListsError(f"TMDB list {list_key} returned no data")

    results = data.get("results")
    if not isinstance(results, list):
        raise TMDBListsError(f"TMDB list {list_key} missing results")

    cards = []
    for item in results:
        if not isinstance(item, dict):
            continue
        tmdb_id = item.get("id")
        title = (item.get("name") or item.get("original_name") or "").strip()
        if not tmdb_id or not title:
            continue
        poster_path = item.get("poster_path") or ""
        first_air = (item.get("first_air_date") or "")[:4]
        year = int(first_air) if first_air.isdigit() else None
        cards.append(
            {
                "title": title,
                "tmdb_id": int(tmdb_id),
                "tvdb_id": None,
                "rating": float(item.get("vote_average") or 0),
                "votes": int(item.get("vote_count") or 0),
                "poster_url": f"{TMDB_IMAGE_BASE}{poster_path}" if poster_path else "",
                "overview": (item.get("overview") or "").strip(),
                "year": year,
                "source": "tmdb",
                "detail_url": f"https://www.themoviedb.org/tv/{int(tmdb_id)}",
            }
        )

    _list_cache[list_key] = (now + _CACHE_TTL, cards)
    logger.debug(f"TMDB list {list_key}: {len(cards)} show(s)")
    return cards


def resolve_tvdb_id(tmdb_id: int) -> int | None:
    """Lazy GET /tv/{tmdb_id}/external_ids → tvdb_id or None."""
    key = _api_key()
    if not key:
        raise TMDBMissingKeyError("TMDB API key is not configured")

    tmdb_id = int(tmdb_id)
    url = f"{TMDB_API_BASE}/tv/{tmdb_id}/external_ids"
    data = helpers.getURL(url, params={"api_key": key}, session=_session(), returns="json")
    if not isinstance(data, dict):
        return None
    tvdb = data.get("tvdb_id")
    try:
        tvdb_id = int(tvdb) if tvdb else None
    except (TypeError, ValueError):
        return None
    return tvdb_id if tvdb_id and tvdb_id > 0 else None


def clear_cache(list_key: str | None = None) -> None:
    if list_key is None:
        _list_cache.clear()
    else:
        _list_cache.pop(list_key, None)
