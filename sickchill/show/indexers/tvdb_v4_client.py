"""
Minimal TheTVDB v4 REST client for SickChill.

Replaces tvdbsimple (legacy api.thetvdb.com). Talks to api4.thetvdb.com/v4 only.
Purpose-built for sickchill.show.indexers.tvdb — not a full SDK.
"""

from __future__ import annotations

import re
import threading
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
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
            token = self._token

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }
        if if_modified_since:
            headers["If-Modified-Since"] = if_modified_since
        return headers

    @staticmethod
    def _retry_delay_seconds(response: requests.Response, attempt: int) -> float:
        """Honor Retry-After when present (delta-seconds or HTTP-date); else exponential backoff."""
        retry_after = response.headers.get("Retry-After")
        if retry_after:
            # RFC 7231: delta-seconds
            try:
                return max(0.0, float(retry_after))
            except (TypeError, ValueError):
                pass
            # RFC 7231: HTTP-date
            try:
                when = parsedate_to_datetime(retry_after)
                if when.tzinfo is None:
                    # Naive HTTP-date is GMT per RFC
                    when = when.replace(tzinfo=timezone.utc)
                delay = (when - datetime.now(timezone.utc)).total_seconds()
                return max(0.0, delay)
            except (TypeError, ValueError, IndexError, OverflowError, OSError):
                pass
        # attempt 0 → 1s, 1 → 2s, 2 → 4s (cap 10s)
        return min(10.0, float(2**attempt))

    def _request_envelope(
        self,
        method: str,
        path: str,
        params: dict | None = None,
        if_modified_since: str | None = None,
        _auth_retried: bool = False,
        _transient_attempt: int = 0,
        max_transient_retries: int = 3,
    ) -> tuple[Any, dict]:
        """
        Perform one HTTP request and return (data, links) for that response only.

        No shared pagination state — safe when concurrent requests interleave.
        """
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

        if response.status_code == 401 and not _auth_retried:
            with self._lock:
                self._token = None
            return self._request_envelope(
                method,
                path,
                params=params,
                if_modified_since=if_modified_since,
                _auth_retried=True,
                _transient_attempt=_transient_attempt,
                max_transient_retries=max_transient_retries,
            )

        if response.status_code == 304:
            raise TVDBv4NotModified()

        if response.status_code == 404:
            return None, {}

        # Retry rate limits and server errors a bounded number of times
        if response.status_code == 429 or 500 <= response.status_code < 600:
            if _transient_attempt < max_transient_retries:
                delay = self._retry_delay_seconds(response, _transient_attempt)
                logger.debug(f"TVDB v4 {response.status_code} for {path}; retry {_transient_attempt + 1}/{max_transient_retries} after {delay:.1f}s")
                if delay > 0:
                    time.sleep(delay)
                return self._request_envelope(
                    method,
                    path,
                    params=params,
                    if_modified_since=if_modified_since,
                    _auth_retried=_auth_retried,
                    _transient_attempt=_transient_attempt + 1,
                    max_transient_retries=max_transient_retries,
                )
            raise TVDBv4Error(
                f"request to {path} failed after retries (HTTP {response.status_code})",
                response=response,
            )

        data = response.json() if response.content else {}
        if response.status_code != 200 or data.get("status") != "success":
            raise TVDBv4Error(
                data.get("message") or f"request to {path} failed (HTTP {response.status_code})",
                response=response,
            )

        result = data.get("data")
        links = data.get("links") if isinstance(data.get("links"), dict) else {}
        last_modified = response.headers.get("Last-Modified")
        # Embed links on dict payloads (episode lists, etc.) so callers see them on the same object
        if isinstance(result, dict):
            result = dict(result)
            if last_modified:
                result["_http_last_modified"] = last_modified
            if links and "links" not in result:
                result["links"] = links
        return result, links

    def _request(
        self,
        method: str,
        path: str,
        params: dict | None = None,
        if_modified_since: str | None = None,
        **kwargs,
    ) -> Any:
        result, _links = self._request_envelope(method, path, params=params, if_modified_since=if_modified_since, **kwargs)
        return result

    def _get(self, path: str, params: dict | None = None, if_modified_since: str | None = None) -> Any:
        return self._request("GET", path, params=params, if_modified_since=if_modified_since)

    def _get_envelope(self, path: str, params: dict | None = None, if_modified_since: str | None = None) -> tuple[Any, dict]:
        return self._request_envelope("GET", path, params=params, if_modified_since=if_modified_since)

    def search(self, query: str, search_type: str = "series", language: str | None = None) -> list:
        """
        GET /search — series/movies/people/companies.

        ``language`` is accepted for call-site clarity (addShows metadata language) but is
        intentionally **not** sent as the API ``language`` query parameter. That param
        restricts results to a matching *primary* language and would hide foreign-primary
        shows (e.g. Japanese anime when the UI language is English). Callers apply
        ``SearchResult.translations`` / ``overviews`` for display names instead.
        """
        params: dict[str, Any] = {"query": query, "type": search_type}
        # language deliberately omitted from params — see docstring
        _ = language
        result = self._get("/search", params=params)
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

        # Some deployments accept remote_id only with an accompanying query=
        result = self._get("/search", params={"remote_id": remote_id, "query": remote_id})
        return result or []

    def series(self, series_id, if_modified_since: str | None = None) -> dict | None:
        return self._get(f"/series/{series_id}", if_modified_since=if_modified_since)

    def series_extended(self, series_id, short: bool = False, if_modified_since: str | None = None) -> dict | None:
        params = {"short": "true"} if short else None
        return self._get(f"/series/{series_id}/extended", params=params, if_modified_since=if_modified_since)

    def series_translation(self, series_id, language: str) -> dict | None:
        """GET /series/{id}/translations/{lang} — name/overview in that language when available."""
        if not language:
            return None
        return self._get(f"/series/{series_id}/translations/{language}")

    def series_episodes(
        self,
        series_id,
        season_type: str = "default",
        page: int = 0,
        language: str | None = None,
        if_modified_since: str | None = None,
    ) -> dict | None:
        """
        GET /series/{id}/episodes/{season-type}[/{lang}]

        When ``language`` is a TVDB code (e.g. eng, jpn, ita), use the translated
        endpoint so episode name/overview are in that language rather than the
        series primary/original language.
        """
        season_type = season_type or "default"
        if language:
            path = f"/series/{series_id}/episodes/{season_type}/{language}"
        else:
            path = f"/series/{series_id}/episodes/{season_type}"
        return self._get(path, params={"page": page}, if_modified_since=if_modified_since)

    def all_episodes(self, series_id, season_type: str = "default", max_pages: int = 50, language: str | None = None) -> list:
        """Page through full episode list (v4 typically ~500 per page), capped by max_pages.

        ``language`` should be a TVDB 3-letter code (eng, jpn, …) when translated
        titles are required; omit for primary/original language names.
        """
        episodes: list = []
        page = 0
        while page < max_pages:
            result = self.series_episodes(series_id, season_type, page, language=language)
            if not result:
                break
            # Translated and default payloads both expose episodes on the data object
            batch = result.get("episodes") or []
            episodes.extend(batch)
            links = result.get("links") or {}
            if not links.get("next") or not batch:
                break
            page += 1
        return episodes

    @staticmethod
    def _extract_update_records(result) -> list:
        if result is None:
            return []
        if isinstance(result, list):
            return result
        if isinstance(result, dict):
            for key in ("updates", "series", "episodes"):
                if isinstance(result.get(key), list):
                    return result[key]
        return []

    @staticmethod
    def _next_page_value(links: dict | None, current_page: int):
        """Return next page index/token from links.next, or None if finished."""
        if not links:
            return None
        nxt = links.get("next")
        if nxt in (None, "", False):
            return None
        if isinstance(nxt, int):
            return nxt
        if isinstance(nxt, str):
            if nxt.isdigit():
                return int(nxt)
            # URL with page= query
            match = re.search(r"[?&]page=(\d+)", nxt)
            if match:
                return int(match.group(1))
            # Non-numeric next token — advance by one from current
            return current_page + 1
        return current_page + 1

    def updates_since(self, since: int, entity_type: str | None = "series", page: int = 0) -> tuple[list, dict]:
        """
        GET /updates?since={unix}[&type=series][&page=n]

        Returns (update_records, links) from this response only — no shared client pagination state.
        """
        params: dict[str, Any] = {"since": int(since)}
        if entity_type:
            params["type"] = entity_type
        if page:
            params["page"] = page

        result, links = self._get_envelope("/updates", params=params)
        records = self._extract_update_records(result)
        # Prefer envelope links; dict payloads may also carry embedded links
        if not links and isinstance(result, dict) and isinstance(result.get("links"), dict):
            links = result["links"]
        return records, dict(links or {})

    def all_updates_since(self, since: int, entity_type: str | None = "series", max_pages: int = 50) -> list:
        """Collect updates across pages while links.next is present (capped by max_pages)."""
        collected: list = []
        page = 0
        pages_fetched = 0
        while pages_fetched < max_pages:
            batch, links = self.updates_since(since, entity_type=entity_type, page=page)
            pages_fetched += 1
            if not batch:
                break
            collected.extend(batch)
            next_page = self._next_page_value(links, page)
            if next_page is None:
                break
            page = next_page
        return collected
