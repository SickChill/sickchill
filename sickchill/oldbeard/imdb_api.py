from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import tempfile
from datetime import date, datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import parse_qs, quote, urlencode, urljoin, urlparse

import requests
from text_unidecode import unidecode

HOST = "api.imdbws.com"
BASE_URI = f"https://{HOST}"
SEARCH_BASE_URI = "https://v2.sg.media-imdb.com"
USER_AGENT = "IMDb/8.3.1 (iPhone9,4; iOS 11.2.1)"
APP_KEY = "76a6cc20-6073-4290-8a2c-951b4580ae4a"
_TITLE_AUX_PATH = "/template/imdb-ios-writable/title-auxiliary-v31.jstl/render"
_IMDB_ID_RE = re.compile(r"[a-zA-Z]{2}[0-9]{7,}", re.IGNORECASE)
_CREDS_NAME = "imdb-credentials.json"


class ImdbAPIError(Exception):
    """HTTP or API failure talking to IMDb."""


def _hmac_sha256(key: bytes, msg: str) -> bytes:
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()


def _sigv4_headers(url: str, creds: dict) -> dict[str, str]:
    parsed = urlparse(url)
    now = datetime.now(timezone.utc)
    amz_date = now.strftime("%Y%m%dT%H%M%SZ")
    datestamp = now.strftime("%Y%m%d")
    region = "us-east-1"
    service = "imdbapi"
    payload_hash = hashlib.sha256(b"").hexdigest()

    query_items = []
    for key, values in parse_qs(parsed.query, keep_blank_values=True).items():
        for value in values:
            query_items.append((quote(key, safe="-_.~"), quote(value, safe="-_.~")))
    canonical_query = "&".join(f"{key}={value}" for key, value in sorted(query_items))

    headers_to_sign = {
        "host": parsed.netloc,
        "x-amz-date": amz_date,
    }
    if creds.get("sessionToken"):
        headers_to_sign["x-amz-security-token"] = creds["sessionToken"]
    signed_headers = ";".join(sorted(headers_to_sign))
    canonical_headers = "".join(f"{name}:{headers_to_sign[name]}\n" for name in sorted(headers_to_sign))
    canonical_request = "\n".join(["GET", parsed.path or "/", canonical_query, canonical_headers, signed_headers, payload_hash])
    credential_scope = f"{datestamp}/{region}/{service}/aws4_request"
    string_to_sign = "\n".join(["AWS4-HMAC-SHA256", amz_date, credential_scope, hashlib.sha256(canonical_request.encode("utf-8")).hexdigest()])
    k_date = _hmac_sha256(("AWS4" + creds["secretAccessKey"]).encode("utf-8"), datestamp)
    k_region = hmac.new(k_date, region.encode("utf-8"), hashlib.sha256).digest()
    k_service = hmac.new(k_region, service.encode("utf-8"), hashlib.sha256).digest()
    k_signing = hmac.new(k_service, b"aws4_request", hashlib.sha256).digest()
    signature = hmac.new(k_signing, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()
    headers = {
        "Host": parsed.netloc,
        "X-Amz-Date": amz_date,
        "Authorization": (f"AWS4-HMAC-SHA256 Credential={creds['accessKeyId']}/{credential_scope}, SignedHeaders={signed_headers}, Signature={signature}"),
        "User-Agent": USER_AGENT,
    }
    if creds.get("sessionToken"):
        headers["X-Amz-Security-Token"] = creds["sessionToken"]
    return headers


def _creds_path() -> Path:
    from sickchill import settings

    cache_dir = getattr(settings, "CACHE_DIR", None)
    if cache_dir:
        return Path(cache_dir) / _CREDS_NAME
    return Path(tempfile.gettempdir()) / f"sickchill-{_CREDS_NAME}"


def _load_cached_creds() -> dict | None:
    try:
        return json.loads(_creds_path().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _store_creds(creds: dict) -> dict:
    path = _creds_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(json.dumps(creds))
    except OSError:
        pass
    return creds


def _creds_need_refresh(creds: dict | None) -> bool:
    if not isinstance(creds, dict):
        return True
    if not creds.get("expirationTimeStamp") or not creds.get("accessKeyId") or not creds.get("secretAccessKey"):
        return True
    try:
        expires = datetime.fromisoformat(str(creds["expirationTimeStamp"]).replace("Z", "+00:00"))
    except ValueError:
        return True
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    return (expires - datetime.now(timezone.utc)).total_seconds() < 60


def _fetch_credentials() -> dict:
    try:
        response = requests.post(
            f"{BASE_URI}/authentication/credentials/temporary/ios82",
            json={"appKey": APP_KEY},
            headers={"User-Agent": USER_AGENT},
            timeout=15,
        )
        response.raise_for_status()
        resource = response.json()["resource"]
    except (requests.RequestException, ValueError, KeyError, TypeError) as error:
        raise ImdbAPIError(f"Failed to fetch IMDb credentials: {error}") from error
    if not isinstance(resource, dict) or not resource.get("accessKeyId") or not resource.get("secretAccessKey"):
        raise ImdbAPIError("IMDb credentials response missing keys")
    return resource


class Imdb:
    """HTTP client for the IMDb iOS API endpoints SickChill actually uses."""

    def __init__(self, locale: str | None = None, session: requests.Session | None = None) -> None:
        self.locale = locale or "en_US"
        self.region = self.locale.split("_")[-1].upper()
        self.session = session or requests.Session()

    def _credentials(self) -> dict:
        creds = _load_cached_creds()
        if _creds_need_refresh(creds):
            creds = _store_creds(_fetch_credentials())
        return creds

    def _get(self, url: str, query: str | None = None, params: dict | None = None):
        headers = {"Accept-Language": self.locale, "User-Agent": USER_AGENT}
        if params:
            full_url = f"{url}?{urlencode(params)}"
        else:
            full_url = url
        if urlparse(url).netloc == HOST:
            headers.update(_sigv4_headers(full_url, self._credentials()))
        try:
            response = self.session.get(url, headers=headers, params=params, timeout=20)
        except requests.RequestException as error:
            raise ImdbAPIError(f"Failed talking to IMDb: {error}") from error
        if response.status_code == 404:
            raise LookupError(f"Resource {url} not found")
        if not response.ok:
            raise ImdbAPIError(f"{response.status_code} {response.text}")
        text = response.content.decode("utf-8")
        try:
            payload = json.loads(text)
        except ValueError:
            payload = self._parse_jsonp(text, query)
        if isinstance(payload, dict) and payload.get("error"):
            return None
        return payload

    @staticmethod
    def _parse_jsonp(data: str, query: str | None = None) -> dict:
        if query is None:
            pattern = r"imdb\$.+\((.+)\)"
        else:
            pattern = r"imdb\${}\((.+)\)".format(re.escape(query))
        match = re.match(pattern, data, re.IGNORECASE)
        if not match:
            raise ImdbAPIError("Unexpected IMDb search payload")
        return json.loads(match.group(1))

    def _get_resource(self, path: str) -> dict:
        payload = self._get(url=urljoin(BASE_URI, path))
        if not isinstance(payload, dict):
            return {}
        return payload.get("resource") or payload

    @staticmethod
    def validate_imdb_id(imdb_id: str) -> None:
        if not imdb_id or not _IMDB_ID_RE.fullmatch(imdb_id):
            raise ValueError("invalid imdb id")

    def get_title(self, imdb_id: str) -> dict:
        self.validate_imdb_id(imdb_id)
        return self._get_resource(f"/title/{imdb_id}/auxiliary")

    def get_title_auxiliary(self, imdb_id: str) -> dict:
        self.validate_imdb_id(imdb_id)
        return self._get(
            url=urljoin(BASE_URI, _TITLE_AUX_PATH),
            params={
                "tconst": imdb_id,
                "today": date.today().strftime("%Y-%m-%d"),
                "region": self.region,
            },
        )

    def search_for_title(self, title: str) -> list[dict]:
        cleaned = unidecode(re.sub(r"\W+", "+", title).strip("+"))
        first = next((char for char in cleaned.lower() if char.isalnum()), None)
        if not first:
            raise ValueError("invalid query, does not contain any alphanumeric characters")
        encoded = quote(cleaned)
        url = urljoin(SEARCH_BASE_URI, f"/suggests/{first}/{encoded}.json")
        search_results = self._get(url=url, query=encoded) or {}
        results = []
        for result in search_results.get("d", ()):
            if not str(result.get("id", "")).startswith("tt"):
                continue
            results.append(
                {
                    "title": result.get("l"),
                    "year": str(result["y"]) if result.get("y") else None,
                    "imdb_id": result["id"],
                    "type": result.get("q"),
                }
            )
        return results

    def get_popular_shows(self) -> dict:
        return self._get_resource("/chart/tvmeter")


class ImdbFacade:
    """Title details used by show IMDb refresh (title, year, rating, genres, runtime)."""

    def __init__(self, client: Imdb | None = None) -> None:
        self._client = client or Imdb()

    def get_title(self, imdb_id: str):
        try:
            base_data = self._client.get_title(imdb_id=imdb_id)
            aux_data = self._client.get_title_auxiliary(imdb_id=imdb_id)
        except (LookupError, ImdbAPIError, ValueError):
            return None
        if not isinstance(base_data, dict):
            return None
        base = base_data.get("base") or {}
        ratings = base_data.get("ratings") or {}
        aux = aux_data if isinstance(aux_data, dict) else {}
        try:
            runtime = aux["runningTimes"][0]["timeMinutes"]
        except (KeyError, IndexError, TypeError):
            runtime = None
        try:
            genres = tuple(str(genre).lower() for genre in aux.get("genres") or ())
        except TypeError:
            genres = ()
        try:
            certification = aux["certificate"]["certificate"]
        except (KeyError, TypeError):
            certification = ""
        try:
            rating = float(ratings["rating"])
        except (KeyError, TypeError, ValueError):
            rating = 0.0
        try:
            rating_count = int(ratings.get("ratingCount") or 0)
        except (TypeError, ValueError):
            rating_count = 0
        return SimpleNamespace(
            imdb_id=imdb_id,
            title=base.get("title"),
            year=base.get("year"),
            runtime=runtime,
            genres=genres,
            countries="",
            certification=certification or "",
            rating=rating,
            rating_count=rating_count,
        )
