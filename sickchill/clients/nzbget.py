import datetime
import gzip
import http.client
import xmlrpc.client
import zlib
from base64 import standard_b64encode
from typing import TYPE_CHECKING

from sickchill import logger, settings
from sickchill.common import Quality
from sickchill.helper.common import try_int
from sickchill.helper.helpers import make_context
from sickchill.helper.network_timezones import sc_today
from sickchill.show.History import History

if TYPE_CHECKING:
    from sickchill.providers.result_classes import SearchResult


def get_proxy(https: bool, host: str, username: str, password: str, verify: bool) -> xmlrpc.client.ServerProxy:
    scheme = "http"
    if https:
        scheme += "s"
    return xmlrpc.client.ServerProxy(f"{scheme}://{username}:{password}@{host}/xmlrpc", context=make_context(verify))


def _remember_dead_link(result: "SearchResult"):
    """Store this URL so a later search will not snatch it. The release name stays eligible."""
    url = getattr(result, "url", None)
    if not url:
        return
    provider = getattr(getattr(result, "provider", None), "name", "") or ""
    try:
        History().log_dead_url(url, getattr(result, "name", "") or "", provider)
    except Exception:
        logger.warning(_("Could not record the dead link for {name}").format(name=getattr(result, "name", "")))


def _downloaded_body(downloaded):
    """Return (body, dead) from a provider download.

    An empty string is a transport failure and stays retryable. HTTP 404/410, an empty file,
    and a page that is not an NZB are dead. 401, 403, 429, and 5xx stay retryable.
    """
    if downloaded is None or downloaded == "":
        return None, False
    if isinstance(downloaded, str):
        data = downloaded.encode("utf-8")
        status = 200 if data else 0
    elif isinstance(downloaded, (bytes, bytearray)):
        data = bytes(downloaded)
        status = 200 if data else 0
    else:
        try:
            status = int(getattr(downloaded, "status_code", 0) or 0)
        except (TypeError, ValueError):
            status = 0
        data = getattr(downloaded, "content", b"") or b""
        if isinstance(data, str):
            data = data.encode("utf-8")
        elif isinstance(data, bytearray):
            data = bytes(data)
        elif not isinstance(data, bytes):
            data = b""

    if status == 429 or status >= 500 or status in (401, 403):
        return None, False
    if status in (404, 410):
        return None, True
    return data, not data


def _nzb_bytes(data: bytes, name: str):
    """Return ``(nzb, body)``. ``nzb`` is None when the body is not an NZB.

    ``body`` is the gunzipped, BOM-stripped document so an API error can be classified
    from the same bytes. It is None when a gzip body cannot be read.
    """
    if data.startswith(b"\x1f\x8b"):
        try:
            data = gzip.decompress(data)
        except (OSError, EOFError, zlib.error):
            logger.warning(_("NZB link for {name} was not a readable gzip file").format(name=name))
            return None, None
    if data.startswith(b"\xef\xbb\xbf"):
        data = data[3:]
    if b"<nzb" not in data.lower():
        logger.warning(_("Download for {name} is not an NZB").format(name=name))
        return None, data
    return data, data


def _retryable_api_error(result: "SearchResult", data: bytes) -> bool:
    """True when the body is an account or API error, not a missing NZB.

    Newznab answers those with HTTP 200 and an ``<error>`` document. ``check_auth_from_data``
    classifies that document, including one that has a description and no code. Error code 300
    is the missing item and stays dead. Any other code stays retryable when the checker raises.
    """
    if b"<error" not in data.lower():
        return False
    provider = getattr(result, "provider", None)
    checker = getattr(provider, "check_auth_from_data", None)
    code = ""
    try:
        from sickchill.helper.bs4_parser import BS4Parser

        with BS4Parser(data.decode("utf-8", errors="replace"), language="xml") as parsed:
            error = getattr(parsed, "error", None)
            attrs = getattr(error, "attrs", None) or {}
            code = str(attrs.get("code", "") or "")
            # A missing item is dead. Decide that before the provider checker runs.
            if code == "300":
                return False
            classified = checker(parsed) if callable(checker) else False
    except Exception:
        # A known code other than 300 is an account or API error and stays retryable.
        # A parse failure, or a description-only document whose checker raises, stays dead.
        return bool(code) and code != "300"
    return classified is False


def _nzb_payload(result: "SearchResult"):
    """NZB bytes SickChill will hand to NZBGet, and whether this URL should not be tried again."""
    if result.is_nzbdata:
        raw = result.extraInfo[0] if result.extraInfo else None
        if raw is None or raw == "":
            logger.warning(_("NZB link for {name} returned nothing").format(name=result.name))
            return None, True
        downloaded, dead = _downloaded_body(raw)
    elif result.is_nzb:
        provider = result.provider
        if not provider or not provider.login():
            logger.warning(_("Could not log in to {provider} to download {name}").format(provider=getattr(provider, "name", ""), name=result.name))
            return None, False
        rate_limited = getattr(provider, "is_rate_limited", None)
        if callable(rate_limited) and rate_limited() is True:
            logger.warning(_("Could not download {name} because {provider} is rate limited").format(provider=getattr(provider, "name", ""), name=result.name))
            return None, False
        downloaded, dead = _downloaded_body(provider.get_url(result.url, returns="response", raise_status=False))
    else:
        logger.warning(_("Cannot send {name} because it is not an NZB").format(name=result.name))
        return None, False

    if downloaded is None:
        if dead:
            logger.warning(_("NZB link for {name} is gone").format(name=result.name))
        else:
            logger.warning(_("NZB link for {name} returned nothing").format(name=result.name))
        return None, dead
    if not downloaded:
        logger.warning(_("NZB link for {name} returned nothing").format(name=result.name))
        return None, True

    data, body = _nzb_bytes(downloaded, result.name)
    if data is None:
        if body is not None and _retryable_api_error(result, body):
            logger.warning(_("NZB link for {name} returned an API error").format(name=result.name))
            return None, False
        return None, True
    return data, False


def _nzbget_content(data: bytes) -> str:
    """Base64 text. NZBGet rejects the XML-RPC <base64> type that Python uses for bytes."""
    return standard_b64encode(data).decode("ascii")


def send_nzb(result: "SearchResult", proper=False) -> bool:
    """
    Sends NZB to NZBGet client

    :param result: search result
    :param proper: True if this is a Proper download, False if not. Defaults to False
    """
    if not settings.NZBGET_HOST:
        logger.warning("No NZBget host found in configuration. Please configure it.")
        return False

    proxy = get_proxy(settings.NZBGET_USE_HTTPS, settings.NZBGET_HOST, settings.NZBGET_USERNAME, settings.NZBGET_PASSWORD, settings.SSL_VERIFY)
    try:
        if proxy.writelog("INFO", _("SickChill connected to drop off {name} any moment now.").format(name=f"{result.name}.nzb")):
            logger.debug("Successfully connected to NZBget")
        else:
            logger.warning("Successfully connected to NZBget, but unable to send a message")

    except http.client.error:
        logger.warning("Please check your NZBget host and port (if it is running). NZBget is not responding to this combination")
        return False

    except xmlrpc.client.ProtocolError as error:
        if error.errmsg == "Unauthorized":
            logger.warning("NZBget username or password is incorrect.")
        else:
            logger.exception(f"Protocol Error: {error}")
        return False

    newest_episode_age = sc_today() - max({episode.airdate for episode in result.episodes if episode.airdate})
    if newest_episode_age <= datetime.timedelta(days=7):
        add_to_top = True
        nzbget_priority = settings.NZBGET_PRIORITY

        category = settings.NZBGET_CATEGORY
        if result.show.is_anime:
            category = settings.NZBGET_CATEGORY_ANIME

    else:
        add_to_top = False
        nzbget_priority = 0

        category = settings.NZBGET_CATEGORY_BACKLOG
        if result.show.is_anime:
            category = settings.NZBGET_CATEGORY_ANIME_BACKLOG

    dupe_key = ""
    # if it aired recently make it high priority and generate DupeKey/Score
    for curEp in result.episodes:
        if not dupe_key:
            dupe_key = f"SickChill-{curEp.show.indexerid}"
        dupe_key += f"-{curEp.season:02d}{curEp.episode:02d}"

    dupe_score = result.quality or 0

    if result.show.quality and dupe_score:
        allowed_qualities, preferred_qualities = Quality.splitQuality(result.show.quality)
        if preferred_qualities:
            if result.quality == max(preferred_qualities):
                dupe_score *= 1000
            elif result.quality in preferred_qualities:
                dupe_score *= 800
        elif allowed_qualities:
            if result.quality == max(allowed_qualities):
                dupe_score *= 500
            elif result.quality in allowed_qualities:
                dupe_score *= 300

    elif dupe_score and dupe_score != Quality.UNKNOWN:
        dupe_score *= 100

    if proper:
        dupe_score += 10

    nzb_bytes, dead_link = _nzb_payload(result)
    if not nzb_bytes:
        if dead_link:
            _remember_dead_link(result)
        return False
    # Every version receives the NZB body. A URL is queued before NZBGet fetches it, so a 404
    # still looks like a successful add and the episode is left SNATCHED.
    nzb_content = _nzbget_content(nzb_bytes)

    logger.info("Sending NZB to NZBget")
    logger.debug(f"URL: {result.url}")

    try:
        # Find out if nzbget supports priority (Version 9.0+), old versions beginning with a 0.x will use the old command
        nzbget_version_str = proxy.version()
        nzbget_version = try_int(nzbget_version_str[: nzbget_version_str.find(".")])
        nzb_name = f"{result.name}.nzb"
        if nzbget_version == 0:
            nzbget_result = proxy.append(nzb_name, category, add_to_top, nzb_content)
        elif nzbget_version == 12:
            nzbget_result = proxy.append(nzb_name, category, nzbget_priority, False, nzb_content, False, dupe_key, dupe_score, "score")
        # v13+ returns a queue id. Positive means the body was accepted. 0 and negative values are errors.
        elif nzbget_version >= 13:
            nzbget_result = proxy.append(nzb_name, nzb_content, category, nzbget_priority, False, False, dupe_key, dupe_score, "score") > 0
        else:
            nzbget_result = proxy.append(nzb_name, category, nzbget_priority, False, nzb_content)

        if nzbget_result:
            logger.debug("NZB sent to NZBget successfully")
            return True
        else:
            logger.warning(_("NZBget could not add {name} to the queue").format(name=f"{result.name}.nzb"))
            return False
    except Exception:
        logger.warning(_("Connect Error to NZBget: could not add {name} to the queue").format(name=f"{result.name}.nzb"))
        return False


def test_client_connection(https: bool, host: str, username: str, password: str, verify: bool):
    proxy = get_proxy(https, host, username, password, verify)

    try:
        if proxy.writelog("INFO", "SickChill connection test succeeded."):
            logger.debug("NZBget connections succeeded")
        else:
            logger.warning("NZBget connections succeeded, but unable to send a message")

        return True
    except http.client.error:
        logger.warning("NZBGet connection test failed, check your NZBget host and port (if it is running). NZBget is not responding to this combination")
        return False
