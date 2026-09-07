import re
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


def getShowImage(url, imgNum=None):
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
        image_data = _fetch_allowed_image_content(temp_url)
    except requests.exceptions.RequestException:
        image_data = None

    if not image_data:
        logger.warning("There was an error trying to retrieve the image, aborting")
        return

    return image_data


def _fetch_allowed_image_content(url: str):
    """GET image bytes, re-validating every redirect target against the allowlist."""
    current = url
    for _ in range(_MAX_IMAGE_REDIRECTS + 1):
        if not is_allowed_show_image_url(current):
            logger.warning(f"Blocked show image redirect to non-allowlisted URL: {current}")
            return None

        response = helpers.getURL(
            current,
            session=meta_session,
            returns="response",
            allow_redirects=False,
            allow_proxy=settings.PROXY_INDEXERS,
        )
        if not response:
            return None

        if getattr(response, "is_redirect", False) or response.status_code in {301, 302, 303, 307, 308}:
            location = response.headers.get("Location") or ""
            if not location:
                logger.warning(f"Show image redirect missing Location from {current}")
                return None
            current = urljoin(response.url or current, location)
            continue

        response.raise_for_status()
        content = getattr(response, "content", None)
        return content or None

    logger.warning(f"Too many redirects while fetching show image from {url}")
    return None
