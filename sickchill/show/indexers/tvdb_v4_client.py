"""
Minimal TheTVDB v4 REST client for SickChill.

Replaces tvdbsimple (legacy api.thetvdb.com). Talks to api4.thetvdb.com/v4 only.
Purpose-built for sickchill.show.indexers.tvdb — not a full SDK.
"""

from __future__ import annotations

import threading
import time
from typing import Any

import requests

from sickchill import logger

BASE_URL = "https://api4.thetvdb.com/v4"

# V4 tokens last ~1 month; refresh early so long-running processes stay safe.
TOKEN_LIFETIME_SECONDS = 12 * 3600

# Artwork type ids (https://thetvdb.github.io/v4-api/)
ARTWORK_TYPE_BANNER = 1
ARTWORK_TYPE_POSTER = 2
ARTWORK_TYPE_BACKGROUND = 3
ARTWORK_TYPE_SEASON_BANNER = 6
ARTWORK_TYPE_SEASON_POSTER = 7


class TVDBv4Error(requests.exceptions.RequestException):
    """V4 API failure; subclasses RequestException for ExceptionDecorator."""

    def __init__(self, message: str, response: requests.Response | None = None):
        super().__init__(message)
        self.response = response


class TVDBv4NotModified(TVDBv4Error):
    """HTTP 304 from If-Modified-Since."""

    def __init__(self, message: str = "Not Modified"):
        super().__init__(message)


class TVDBv4Client:
    def __init__(self, apikey: str, pin: str | None = None, timeout: int = 20):
        self.apikey = apikey or ""
        self.pin = pin or ""
        self.timeout = timeout
        self._token: str | None = None
        self._token_time = 0.0
        self._lock = threading.Lock()
        self._session = requests.Session()

    def _login(self) -> None:
        if not self.apikey:
            raise TVDBv4Error("TVDB v4 API key is not configured")

        payload: dict[str, str] = {"apikey": self.apikey}
        if self.pin:
            payload["pin"] = self.pin

        response = self._session.post(f"{BASE_URL}/login", json=payload, timeout=self.timeout)
        data = response.json() if response.content else {}
        if response.status_code != 200 or data.get("status") != "success":
            raise TVDBv4Error(data.get("message") or f"login failed (HTTP {response.status_code})", response=response)

        token = (data.get("data") or {}).get("token")
        if not token:
            raise TVDBv4Error("login succeeded but no token returned", response=response)

        self._token = token
        self._token_time = time.time()

    def _headers(self, if_modified_since: str | None = None) -> dict[str, str]:
        with self._lock:
            if not self._token or (time.time() - self._token_time) > TOKEN_LIFETIME_SECONDS:
                self._login()

        headers = {
            "Authorization": f"Bearer {self._token}",
            "Accept": "application/json",
        }
        if if_modified_since:
            headers["If-Modified-Since"] = if_modified_since
        return headers

    def _request(
        self,
        method: str,
        path: str,
        params: dict | None = None,
        if_modified_since: str | None = None,
        _retried: bool = False,
    ) -> Any:
        url = f"{BASE_URL}{path}"
        try:
            response = self._session.request(
                method,
                url,
                headers=self._headers(if_modified_since),
                params=params,
                timeout=self.timeout,
            )
        except requests.exceptions.RequestException as error:
            raise TVDBv4Error(str(error)) from error

        if response.status_code == 401 and not _retried:
            with self._lock:
                self._token = None
            return self._request(method, path, params=params, if_modified_since=if_modified_since, _retried=True)

        if response.status_code == 304:
            raise TVDBv4NotModified()

        if response.status_code == 404:
            return None

        data = response.json() if response.content else {}
        if response.status_code != 200 or data.get("status") != "success":
            raise TVDBv4Error(
                data.get("message") or f"request to {path} failed (HTTP {response.status_code})",
                response=response,
            )

        # Attach last-modified for callers that want to cache IMS (phase 2).
        result = data.get("data")
        if isinstance(result, dict):
            last_modified = response.headers.get("Last-Modified")
            if last_modified:
                result = dict(result)
                result["_http_last_modified"] = last_modified
        return result

    def _get(self, path: str, params: dict | None = None, if_modified_since: str | None = None) -> Any:
        return self._request("GET", path, params=params, if_modified_since=if_modified_since)

    def search(self, query: str, search_type: str = "series") -> list:
        result = self._get("/search", params={"query": query, "type": search_type})
        return result or []

    def search_by_remote_id(self, remote_id: str) -> list:
        """Exact match on IMDb ids and similar remote identifiers."""
        # Prefer /search/remoteid/{id} when available; fall back to query param.
        try:
            result = self._get(f"/search/remoteid/{remote_id}")
            if result is not None:
                return result if isinstance(result, list) else [result]
        except TVDBv4Error as error:
            logger.debug(f"TVDB v4 remoteid path failed for {remote_id}: {error}")

        result = self._get("/search", params={"remote_id": remote_id})
        return result or []

    def series(self, series_id, if_modified_since: str | None = None) -> dict | None:
        return self._get(f"/series/{series_id}", if_modified_since=if_modified_since)

    def series_extended(self, series_id, short: bool = False, if_modified_since: str | None = None) -> dict | None:
        params = {"short": "true"} if short else None
        return self._get(f"/series/{series_id}/extended", params=params, if_modified_since=if_modified_since)

    def series_episodes(self, series_id, season_type: str = "default", page: int = 0, if_modified_since: str | None = None) -> dict | None:
        return self._get(
            f"/series/{series_id}/episodes/{season_type}",
            params={"page": page},
            if_modified_since=if_modified_since,
        )

    def all_episodes(self, series_id, season_type: str = "default") -> list:
        """Page through full episode list (v4 typically ~500 per page)."""
        episodes: list = []
        page = 0
        while True:
            result = self.series_episodes(series_id, season_type, page)
            if not result:
                break
            batch = result.get("episodes") or []
            episodes.extend(batch)
            links = result.get("links") or {}
            if not links.get("next") or not batch:
                break
            page += 1
        return episodes

    def updates_since(self, since: int, entity_type: str | None = "series", page: int = 0) -> list:
        """
        GET /updates?since={unix}[&type=series][&page=n]

        Returns list of update records (shape varies; callers should be defensive).
        """
        params: dict[str, Any] = {"since": int(since)}
        if entity_type:
            params["type"] = entity_type
        if page:
            params["page"] = page

        result = self._get("/updates", params=params)
        if result is None:
            return []
        if isinstance(result, list):
            return result
        # Some responses nest under a key
        if isinstance(result, dict):
            for key in ("updates", "series", "episodes"):
                if isinstance(result.get(key), list):
                    return result[key]
        return []

    def all_updates_since(self, since: int, entity_type: str | None = "series", max_pages: int = 50) -> list:
        """Collect updates across pages until empty or max_pages."""
        collected: list = []
        page = 0
        while page < max_pages:
            batch = self.updates_since(since, entity_type=entity_type, page=page)
            if not batch:
                break
            collected.extend(batch)
            if len(batch) < 100:
                # Heuristic: short page usually means last page
                break
            page += 1
        return collected
