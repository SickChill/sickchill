from __future__ import annotations

from urllib.parse import quote

import requests

from sickchill import logger

TVMAZE_SEARCH = "https://api.tvmaze.com/search/shows?q="


def search(name: str) -> list[dict]:
    """
    Search TVmaze for shows by name.

    Returns a list of show dicts that contain a valid 'externals.thetvdb' ID.
    Empty list on failure or no usable results.
    """
    if not name or not str(name).strip():
        return []

    try:
        url = TVMAZE_SEARCH + quote(str(name).strip())
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        logger.debug(f"TVmaze search failed for '{name}': {e}")
        return []

    results = []
    if not isinstance(data, list):
        return results

    for item in data:
        if not isinstance(item, dict):
            continue
        show = item.get("show") or {}
        externals = show.get("externals") or {}
        if externals.get("thetvdb"):
            results.append(show)
    return results
