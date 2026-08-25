"""TVMaze upcoming series premieres (S01E01) for Add Shows (Phase 5a)."""

from __future__ import annotations

import re
import time

from sickchill import logger
from sickchill.oldbeard import helpers

_TAG_RE = re.compile(r"<[^>]+>")

SCHEDULE_URL = "https://api.tvmaze.com/schedule/full"

_CACHE_TTL = 18 * 60 * 60  # ~12–24h
_cache: tuple[float, list] | None = None


class TVMazePremieresError(Exception):
    """Raised when the TVMaze schedule request fails."""


def _session():
    session = helpers.make_session()
    session.headers.update({"User-Agent": "SickChill"})
    return session


def fetch_premieres() -> list[dict]:
    """
    Fetch schedule/full once, keep season==1 and number==1, dedupe by show.id.

    Returns normalized cards compatible with TMDB list cards:
    {title, tmdb_id, tvdb_id, rating, votes, poster_url, overview, year, source, ...}
    """
    global _cache

    now = time.time()
    if _cache and now < _cache[0]:
        return _cache[1]

    data = helpers.getURL(SCHEDULE_URL, session=_session(), returns="json", timeout=90)
    if not isinstance(data, list):
        raise TVMazePremieresError("TVMaze schedule/full returned no list")

    seen_show_ids: set[int] = set()
    cards: list[dict] = []

    for episode in data:
        if not isinstance(episode, dict):
            continue
        try:
            season = int(episode.get("season"))
            number = int(episode.get("number"))
        except (TypeError, ValueError):
            continue
        if season != 1 or number != 1:
            continue

        show = episode.get("_embedded", {}).get("show") if isinstance(episode.get("_embedded"), dict) else None
        if not isinstance(show, dict):
            # Some payloads nest show at top level
            show = episode.get("show") if isinstance(episode.get("show"), dict) else None
        if not isinstance(show, dict):
            continue

        try:
            show_id = int(show.get("id"))
        except (TypeError, ValueError):
            continue
        if show_id in seen_show_ids:
            continue
        seen_show_ids.add(show_id)

        title = (show.get("name") or "").strip()
        if not title:
            continue

        externals = show.get("externals") if isinstance(show.get("externals"), dict) else {}
        tvdb_raw = externals.get("thetvdb")
        try:
            tvdb_id = int(tvdb_raw) if tvdb_raw else None
        except (TypeError, ValueError):
            tvdb_id = None
        if tvdb_id is not None and tvdb_id <= 0:
            tvdb_id = None

        image = show.get("image") if isinstance(show.get("image"), dict) else {}
        poster_url = (image.get("medium") or image.get("original") or "").strip()

        premiered = (show.get("premiered") or "")[:4]
        year = int(premiered) if premiered.isdigit() else None

        # Prefer the S01E01 episode airdate for the tile; fall back to show.premiered
        airdate = (episode.get("airdate") or show.get("premiered") or "").strip()
        if airdate and len(airdate) > 10:
            airdate = airdate[:10]

        rating_obj = show.get("rating") if isinstance(show.get("rating"), dict) else {}
        try:
            rating = float(rating_obj.get("average") or 0)
        except (TypeError, ValueError):
            rating = 0.0

        language = (show.get("language") or "").strip()

        cards.append(
            {
                "title": title,
                "tmdb_id": None,
                "tvmaze_id": show_id,
                "tvdb_id": tvdb_id,
                "rating": rating,
                "votes": 0,
                "poster_url": poster_url,
                "overview": _TAG_RE.sub("", show.get("summary") or "").strip(),
                "year": year,
                "airdate": airdate,
                "language": language,
                "source": "tvmaze",
                "detail_url": show.get("url") or f"https://www.tvmaze.com/shows/{show_id}",
            }
        )

    _cache = (now + _CACHE_TTL, cards)
    logger.debug(f"TVMaze premieres: {len(cards)} S01E01 show(s)")
    return cards


def clear_cache() -> None:
    global _cache
    _cache = None
