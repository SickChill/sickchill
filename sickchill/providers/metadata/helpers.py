import re
import time
from urllib.parse import urljoin, urlparse

import requests

from sickchill import logger, settings
from sickchill.oldbeard import helpers

meta_session = helpers.make_session()

# Public artwork CDNs used by the image selector / edit-show replace flow.
# Keep in sync with sickchill.views.imageSelector.url_wrap allowlist.
ALLOWED_SHOW_IMAGE_HOSTS = frozenset(
    {
        "artworks.thetvdb.com",
        "assets.fanart.tv",
        "image.tmdb.org",
    }
)

_ALLOWED_SHOW_IMAGE_URL_RE = re.compile(
    r"^https?://(artworks\.thetvdb\.com|assets\.fanart\.tv|image\.tmdb\.org)/.*",
    re.IGNORECASE,
)

_MAX_IMAGE_REDIRECTS = 5
_IMAGE_CHUNK_SIZE = 64 * 1024


def is_allowed_show_image_url(url: str | None) -> bool:
    """Return True if url is http(s) to an approved public artwork host (SSRF guard)."""
    if not url or not isinstance(url, str):
        return False
    candidate = url.strip()
    if not candidate or not _ALLOWED_SHOW_IMAGE_URL_RE.match(candidate):
        return False
    parsed = urlparse(candidate)
    if parsed.scheme not in ("http", "https"):
        return False
    if parsed.username is not None or parsed.password is not None:
        return False
    host = (parsed.hostname or "").lower()
    return host in ALLOWED_SHOW_IMAGE_HOSTS


def getShowImage(url, imgNum=None, timeout=30):
    if not url:
        return None

    # if they provided a fanart number try to use it instead
    if imgNum is not None:
        temp_url = url.split("-")[0] + "-" + str(imgNum) + ".jpg"
    else:
        temp_url = url

    if not is_allowed_show_image_url(temp_url):
        logger.warning(f"Blocked show image fetch from non-allowlisted URL: {temp_url}")
        return None

    logger.debug("Fetching image from " + temp_url)

    try:
        image_data = _fetch_allowed_image_content(temp_url, timeout=timeout)
    except requests.exceptions.RequestException:
        image_data = None

    if not image_data:
        logger.warning("There was an error trying to retrieve the image, aborting")
        return

    return image_data


def _read_response_until_deadline(response, deadline: float, url: str):
    """Consume a streamed response in bounded chunks, aborting when the shared deadline expires."""
    chunks = []
    try:
        for chunk in response.iter_content(_IMAGE_CHUNK_SIZE):
            if deadline - time.monotonic() <= 0:
                logger.warning(f"Timed out while reading show image from {url}")
                return None
            if chunk:
                chunks.append(chunk)
    finally:
        try:
            response.close()
        except Exception:
            pass
    return b"".join(chunks) or None


def _fetch_allowed_image_content(url: str, timeout: float = 30):
    """GET image bytes, re-validating every redirect target against the allowlist.

    ``timeout`` is a budget for the whole redirect chain and body download, not per hop.
    Responses are streamed in bounded chunks so a slow body cannot overrun the deadline.
    """
    deadline = time.monotonic() + float(timeout)
    current = url
    for _ in range(_MAX_IMAGE_REDIRECTS + 1):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            logger.warning(f"Timed out while fetching show image from {url}")
            return None

        if not is_allowed_show_image_url(current):
            logger.warning(f"Blocked show image redirect to non-allowlisted URL: {current}")
            return None

        # Pass only remaining budget — do not inflate past the cumulative deadline.
        response = helpers.getURL(
            current,
            session=meta_session,
            returns="response",
            allow_redirects=False,
            allow_proxy=settings.PROXY_INDEXERS,
            timeout=remaining,
            stream=True,
        )
        if not response:
            return None

        if getattr(response, "is_redirect", False) or response.status_code in {301, 302, 303, 307, 308}:
            location = response.headers.get("Location") or ""
            response_url = response.url or current
            try:
                response.close()
            except Exception:
                pass
            if not location:
                logger.warning(f"Show image redirect missing Location from {current}")
                return None
            current = urljoin(response_url, location)
            continue

        try:
            response.raise_for_status()
        except requests.exceptions.RequestException:
            try:
                response.close()
            except Exception:
                pass
            return None

        return _read_response_until_deadline(response, deadline, url)

    logger.warning(f"Too many redirects while fetching show image from {url}")
    return None
