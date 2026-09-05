"""Trakt.tv API v2 client.

Modernized to align with the current Trakt authentication documentation:
https://docs.trakt.tv/docs/authentication-oauth
https://docs.trakt.tv/reference/auth

Key behaviours:
  * OAuth 2.0 Device Code Flow (recommended for headless / media-center apps).
  * Legacy PIN / Authorization Code Flow (``urn:ietf:wg:oauth:2.0:oob``) is still supported
    so existing installs continue to work while users migrate.
  * Refresh tokens are single-use: every successful refresh response is persisted immediately
    via ``sickchill.oldbeard.config.save_config`` so a process restart cannot lose a token.
  * OAuth error bodies (``invalid_grant`` / ``session not found``) are parsed and surfaced
    as :class:`traktTokenExpiredException` instead of a generic 401 warning.
  * Transient failures (502/503/504/520-522, ``ConnectionError``, ``Timeout``) use bounded
    exponential backoff and never recurse without a depth counter.
"""

from __future__ import annotations

import time
from typing import Any, Mapping, MutableMapping, Optional

import certifi
import requests
from requests.exceptions import ConnectionError as RequestsConnectionError
from requests.exceptions import RequestException, Timeout
from requests.structures import CaseInsensitiveDict

from sickchill import logger, settings
from sickchill.oldbeard.trakt_api.exceptions import (
    traktAuthException,
    traktDeviceCodeExpiredException,
    traktDeviceCodePendingException,
    traktException,
    traktRateLimitException,
    traktServerBusy,
    traktTokenExpiredException,
)

# Trakt's own guidance: retry transient failures a small, bounded number of times.
_MAX_RETRIES = 3
_RETRY_BACKOFF_SECONDS = 2.0
_RETRYABLE_STATUS = frozenset({500, 502, 503, 504, 520, 521, 522, 524})

# OAuth 2.0 out-of-band redirect used by the legacy PIN flow.
_OOB_REDIRECT_URI = "urn:ietf:wg:oauth:2.0:oob"

_USER_AGENT = "SickChill/1.0 (+https://sickchill.github.io)"


def _persist_tokens() -> None:
    """Persist Trakt tokens to disk immediately.

    Refresh tokens are single-use; if the process restarts between an in-memory update
    and the next scheduled config save, the token is permanently lost. Call this every
    time we receive a new access/refresh token pair.
    """
    try:
        # Local import to avoid a circular import at module load time.
        from sickchill.oldbeard import config as _config

        _config.save_config()
    except Exception as save_error:  # pragma: no cover - defensive
        logger.debug(f"Trakt: failed to persist tokens to disk: {save_error}")


class TraktAPI:
    def __init__(self, ssl_verify: bool = True, timeout: Optional[int] = 30):
        self.verify = certifi.where() if ssl_verify else False
        self.timeout = timeout if timeout else 30
        self.auth_url = settings.TRAKT_OAUTH_URL
        self.api_url = settings.TRAKT_API_URL
        self.headers: CaseInsensitiveDict = CaseInsensitiveDict(
            {
                "Content-Type": "application/json",
                "trakt-api-version": "2",
                "trakt-api-key": settings.TRAKT_API_KEY,
                "User-Agent": _USER_AGENT,
            }
        )

    # ------------------------------------------------------------------
    # OAuth: Authorization Code / PIN flow
    # ------------------------------------------------------------------
    def traktToken(self, trakt_pin: Optional[str] = None, refresh: bool = False, count: int = 0) -> bool:
        """Exchange a PIN or refresh token for an access token.

        Retained for backwards compatibility with the existing UI. New installs should
        prefer :meth:`device_code_start` / :meth:`device_code_poll`.
        """
        if count > _MAX_RETRIES:
            logger.warning(_("Trakt token exchange failed after multiple attempts."))
            settings.TRAKT_ACCESS_TOKEN = ""
            _persist_tokens()
            return False
        if count > 0:
            time.sleep(_RETRY_BACKOFF_SECONDS)

        data: MutableMapping[str, Any] = {
            "client_id": settings.TRAKT_API_KEY,
            "client_secret": settings.TRAKT_API_SECRET,
            "redirect_uri": _OOB_REDIRECT_URI,
        }

        if refresh:
            if not settings.TRAKT_REFRESH_TOKEN:
                logger.info(_("Trakt: no refresh token stored; user must re-authorize."))
                return False
            data["grant_type"] = "refresh_token"
            data["refresh_token"] = settings.TRAKT_REFRESH_TOKEN
        else:
            data["grant_type"] = "authorization_code"
            if trakt_pin:
                data["code"] = trakt_pin
            else:
                logger.warning(_("Trakt: PIN is required to authorize."))
                return False

        headers = CaseInsensitiveDict({"Content-Type": "application/json", "User-Agent": _USER_AGENT})

        try:
            resp = self.traktRequest("oauth/token", data=data, headers=headers, url=self.auth_url, method="POST", count=count)
        except traktTokenExpiredException:
            # Refresh token is dead - clear stored state and force the user to reauthorize.
            logger.warning(_("Trakt refresh token is no longer valid. Please reauthorize SickChill in the Trakt settings."))
            settings.TRAKT_ACCESS_TOKEN = ""
            settings.TRAKT_REFRESH_TOKEN = ""
            _persist_tokens()
            return False
        except traktAuthException as auth_error:
            logger.warning(f"Trakt auth error during token exchange: {auth_error}")
            return False

        if isinstance(resp, Mapping) and "access_token" in resp:
            settings.TRAKT_ACCESS_TOKEN = resp["access_token"]
            if resp.get("refresh_token"):
                settings.TRAKT_REFRESH_TOKEN = resp["refresh_token"]
            _persist_tokens()
            return True
        return False

    # ------------------------------------------------------------------
    # OAuth: Device Code flow (recommended for headless installs)
    # ------------------------------------------------------------------
    def device_code_start(self) -> Mapping[str, Any]:
        """Start the OAuth device code flow.

        Returns the raw response from ``/oauth/device/code`` which includes ``device_code``,
        ``user_code``, ``verification_url``, ``expires_in`` and ``interval``.
        Callers should display ``user_code`` + ``verification_url`` to the user and then
        poll with :meth:`device_code_poll` at ``interval`` seconds.
        """
        data = {"client_id": settings.TRAKT_API_KEY}
        headers = CaseInsensitiveDict({"Content-Type": "application/json", "User-Agent": _USER_AGENT})
        resp = self.traktRequest(
            "oauth/device/code",
            data=data,
            headers=headers,
            url=self.auth_url,
            method="POST",
        )
        if not isinstance(resp, Mapping) or "device_code" not in resp:
            raise traktException(_("Unexpected response from Trakt device code endpoint."))
        return resp

    def device_code_poll(self, device_code: str) -> bool:
        """Poll ``/oauth/device/token`` once for a pending device code authorization.

        Returns ``True`` when the user has approved and tokens are stored. Raises
        :class:`traktDeviceCodePendingException` while the user has not yet approved,
        :class:`traktDeviceCodeExpiredException` when the code has expired, or another
        :class:`traktException` subclass on failure.
        """
        data = {
            "code": device_code,
            "client_id": settings.TRAKT_API_KEY,
            "client_secret": settings.TRAKT_API_SECRET,
        }
        headers = CaseInsensitiveDict({"Content-Type": "application/json", "User-Agent": _USER_AGENT})

        url = self.auth_url + "oauth/device/token"
        try:
            response = requests.post(
                url,
                json=data,
                headers=headers,
                timeout=self.timeout,
                verify=self.verify,
            )
        except (RequestsConnectionError, Timeout) as network_error:
            raise traktServerBusy(str(network_error)) from network_error
        except RequestException as request_error:
            raise traktException(str(request_error)) from request_error

        # Per Trakt docs the polling endpoint uses HTTP status codes to communicate state:
        #   200 - approved (token in body)
        #   400 - pending
        #   404 - not found (invalid device_code)
        #   409 - already used
        #   410 - expired
        #   418 - denied
        #   429 - slow down
        status = response.status_code
        if status == 200:
            body = _safe_json(response)
            if not isinstance(body, Mapping) or "access_token" not in body:
                raise traktException(_("Trakt device token response missing access_token."))
            settings.TRAKT_ACCESS_TOKEN = body["access_token"]
            if body.get("refresh_token"):
                settings.TRAKT_REFRESH_TOKEN = body["refresh_token"]
            _persist_tokens()
            return True
        if status == 400:
            raise traktDeviceCodePendingException("pending")
        if status == 404:
            raise traktException(_("Trakt device code not found."))
        if status == 409:
            raise traktException(_("Trakt device code already used."))
        if status == 410:
            raise traktDeviceCodeExpiredException(_("Trakt device code expired."))
        if status == 418:
            raise traktAuthException(_("Trakt authorization denied by user."))
        if status == 429:
            raise traktRateLimitException(_("Trakt asked us to slow down polling."))
        raise traktException(_("Unexpected Trakt device token status {code}").format(code=status))

    # ------------------------------------------------------------------
    # Account probes
    # ------------------------------------------------------------------
    def validateAccount(self) -> bool:
        resp = self.traktRequest("users/settings")
        return isinstance(resp, Mapping) and "account" in resp

    # ------------------------------------------------------------------
    # Core request pipeline
    # ------------------------------------------------------------------
    def traktRequest(
        self,
        path: str,
        data: Optional[Mapping[str, Any]] = None,
        headers: Optional[Mapping[str, str]] = None,
        url: Optional[str] = None,
        method: str = "GET",
        count: int = 0,
    ) -> Any:
        """Issue a request against the Trakt API.

        ``count`` tracks recursive retries and is always incremented before recursing so we
        cannot loop forever on repeated 401/502 responses.
        """
        if url is None:
            url = self.api_url

        count += 1
        if count > _MAX_RETRIES:
            logger.warning(_("Trakt request {path} exceeded retry limit.").format(path=path))
            return {}

        request_headers: MutableMapping[str, str] = CaseInsensitiveDict(headers if headers is not None else self.headers)

        # Only attach a Bearer token for endpoints that actually need one - OAuth endpoints
        # authenticate via client_id/client_secret in the body.
        is_oauth_endpoint = path.startswith("oauth/")
        if settings.TRAKT_ACCESS_TOKEN and not is_oauth_endpoint:
            request_headers["Authorization"] = "Bearer " + settings.TRAKT_ACCESS_TOKEN
        elif not settings.TRAKT_ACCESS_TOKEN and not is_oauth_endpoint and count > 1:
            logger.warning(_("You must get a Trakt TOKEN. Check your Trakt settings"))
            return {}

        method_upper = method.upper()
        request_kwargs: dict = {
            "headers": dict(request_headers),
            "timeout": self.timeout,
            "verify": self.verify,
        }
        # Never send a body on GET/DELETE (some proxies and Trakt itself reject that).
        if data is not None and method_upper not in {"GET", "HEAD"}:
            request_kwargs["json"] = data

        try:
            resp = requests.request(method_upper, url + path, **request_kwargs)
        except Timeout as timeout_error:
            logger.warning(_("Timeout connecting to Trakt. Try to increase timeout value in Trakt settings"))
            if count < _MAX_RETRIES:
                time.sleep(_RETRY_BACKOFF_SECONDS * count)
                return self.traktRequest(path, data=data, headers=headers, url=url, method=method, count=count)
            raise traktServerBusy(str(timeout_error)) from timeout_error
        except RequestsConnectionError as conn_error:
            logger.debug(_("Could not connect to Trakt. Error: {error}").format(error=conn_error))
            if count < _MAX_RETRIES:
                time.sleep(_RETRY_BACKOFF_SECONDS * count)
                return self.traktRequest(path, data=data, headers=headers, url=url, method=method, count=count)
            return {}
        except RequestException as request_error:
            logger.debug(_("Could not connect to Trakt. Error: {error}").format(error=request_error))
            return {}

        code = resp.status_code

        # 2xx path - happy case
        if 200 <= code < 300:
            body = _safe_json(resp)
            if isinstance(body, Mapping) and body.get("status") == "failure":
                message = body.get("message") or body.get("error") or "Unknown Error"
                raise traktException(str(message))
            return body if body is not None else {}

        # Rate limited - honour Retry-After header if present, otherwise back off.
        if code == 429:
            retry_after = _parse_retry_after(resp.headers.get("Retry-After"))
            logger.debug(_("Trakt rate limit hit; sleeping {sec}s").format(sec=retry_after))
            if count < _MAX_RETRIES:
                time.sleep(retry_after)
                return self.traktRequest(path, data=data, headers=headers, url=url, method=method, count=count)
            raise traktRateLimitException(_("Trakt rate limit exceeded"))

        # Auth failures - inspect the OAuth error body if we can.
        if code == 401:
            oauth_error = _extract_oauth_error(resp)
            if oauth_error in {"invalid_grant"}:
                # Refresh token dead per Trakt's authentication migration guidance.
                raise traktTokenExpiredException(
                    _("Trakt refresh token invalid - please reauthorize SickChill in the Trakt settings.")
                )
            # For non-OAuth endpoints, attempt exactly one silent refresh.
            if not is_oauth_endpoint and settings.TRAKT_REFRESH_TOKEN and count == 1:
                logger.debug(_("Trakt 401 on {path}; attempting refresh").format(path=path))
                if self.traktToken(refresh=True, count=0):
                    return self.traktRequest(path, data=data, headers=headers, url=url, method=method, count=count)
            logger.warning(_("Unauthorized. Please check your Trakt settings"))
            if is_oauth_endpoint:
                raise traktAuthException(oauth_error or "unauthorized")
            return {}

        if code == 400 and is_oauth_endpoint:
            oauth_error = _extract_oauth_error(resp)
            if oauth_error == "invalid_grant":
                raise traktTokenExpiredException(
                    _("Trakt refresh token invalid - please reauthorize SickChill in the Trakt settings.")
                )
            raise traktAuthException(oauth_error or "bad_request")

        if code == 404:
            logger.debug(_("Trakt error (404) the resource does not exist: {url}{path}").format(url=url, path=path))
            return {}

        if code in _RETRYABLE_STATUS:
            logger.debug(_("Trakt transient {code} on {path}; retry {n}/{m}").format(code=code, path=path, n=count, m=_MAX_RETRIES))
            if count < _MAX_RETRIES:
                time.sleep(_RETRY_BACKOFF_SECONDS * count)
                return self.traktRequest(path, data=data, headers=headers, url=url, method=method, count=count)
            raise traktServerBusy(_("Trakt is unavailable (HTTP {code})").format(code=code))

        # Fallthrough - unexpected client error. Surface the JSON body if any.
        body_snippet = _extract_error_message(resp)
        logger.warning(_("Trakt error {code} on {path}: {body}").format(code=code, path=path, body=body_snippet))
        return {}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _safe_json(response: requests.Response) -> Any:
    """Return the JSON body if possible, otherwise ``None``."""
    if not response.content:
        return None
    try:
        return response.json()
    except ValueError:
        return None


def _extract_oauth_error(response: requests.Response) -> Optional[str]:
    body = _safe_json(response)
    if isinstance(body, Mapping):
        err = body.get("error")
        if isinstance(err, str):
            return err
    return None


def _extract_error_message(response: requests.Response) -> str:
    body = _safe_json(response)
    if isinstance(body, Mapping):
        parts = []
        for key in ("error", "error_description", "message"):
            value = body.get(key)
            if value:
                parts.append(f"{key}={value}")
        if parts:
            return "; ".join(parts)
    text = (response.text or "").strip()
    return text[:200] if text else "<no body>"


def _parse_retry_after(value: Optional[str]) -> float:
    if not value:
        return _RETRY_BACKOFF_SECONDS
    try:
        return max(float(value), 1.0)
    except (TypeError, ValueError):
        return _RETRY_BACKOFF_SECONDS
