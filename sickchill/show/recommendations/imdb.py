import os
import posixpath
import re
import threading
from urllib.parse import urlparse

from sickchill import logger, settings
from sickchill.helper import helpers
from sickchill.show.indexers.imdb_api import Imdb, ImdbAPIError, ImdbFacade

# Card posters are fetched by SickChill and served from /cache/images. A browser
# pointed at the NAS often cannot load m.media-amazon.com (DSM proxy CSP, tracking
# protection, or a client network that never sees the app proxy). Localhost can.
_IMDB_POSTER_ID_RE = re.compile(r"^tt\d{7,}$", re.IGNORECASE)
_AMAZON_POSTER_HOSTS = frozenset({"m.media-amazon.com"})
_V1_JPG_RE = re.compile(r"@\._V1_[^/]*\.jpg$", re.IGNORECASE)
_POSTER_MAX_BYTES = 2 * 1024 * 1024
_poster_locks = {}
_poster_locks_guard = threading.Lock()


class imdbPopular(object):
    def __init__(self):
        """Gets a list of most popular TV series from IMDb via imdb-pie"""
        self.session = helpers.make_session()
        self.client = Imdb()
        self.imdb = ImdbFacade(client=self.client)

    def fetch_popular_shows(self):
        """Get popular show information from IMDB"""
        try:
            data = self.client.get_popular_shows()

            if isinstance(data, dict):
                # imdb-pie returns 'ranks' for this endpoint
                ranks = data.get("ranks", [])
                if ranks:
                    return ranks

                # Fallback for other possible structures
                chart = data.get("chart", {})
                return chart.get("titles") or chart.get("titleMeter", [])

            return []

        except ImdbAPIError as e:
            logger.warning(f"IMDb popular shows fetch failed:{e}")
            return []

    def get_title(self, imdb_id):
        """Optional helper: get full title details (including better image info)"""
        try:
            return self.imdb.get_title(imdb_id=imdb_id)
        except ImdbAPIError as e:
            logger.warning(f"Failed to get title {imdb_id}: {e}")
            return None

    def imdb_url(self, result):
        """Return full IMDb URL"""
        if isinstance(result, dict):
            imdb_id = result.get("id") or result.get("tconst")
        else:
            imdb_id = getattr(result, "imdb_id", None)
            if callable(imdb_id):
                imdb_id = imdb_id()
        if imdb_id:
            return f"https://www.imdb.com/title/{imdb_id}/"
        return None

    @staticmethod
    def change_size(image_url, factor=3):
        """More robust poster URL resizer"""
        if not image_url or not isinstance(image_url, str):
            return image_url

        # Improved regex (handles V1_/V2_ + .jpg/.webp)
        pattern = re.compile(r"^(.*?)V(\d+)_(.{2})(.*?)_(.{2})(.*?),(\d+),(\d+),(\d+)_(.+?)(\.\w+)$", re.IGNORECASE)
        match = pattern.search(image_url)
        if not match:
            return image_url

        try:
            matches = list(match.groups())
            # Scale requested size plus crop coordinates/dimensions.
            for i in (3, 5, 6, 7, 8):
                if matches[i].isdigit():
                    matches[i] = str(int(matches[i]) * factor)

            return (
                f"{matches[0]}V{matches[1]}_{matches[2]}{matches[3]}_{matches[4]}{matches[5]},{matches[6]},{matches[7]},{matches[8]}_{matches[9]}{matches[10]}"
            )
        except (IndexError, ValueError):
            return image_url

    def cache_image(self, image_url):
        """Store cache of image in cache dir"""
        if not image_url:
            return

        path = os.path.abspath(os.path.join(settings.CACHE_DIR, "images", "imdb_popular"))
        os.makedirs(path, exist_ok=True)

        full_path = os.path.join(path, os.path.basename(image_url))

        if not os.path.isfile(full_path):
            helpers.download_file(image_url, full_path, session=self.session)

    def cache_poster(self, imdb_id, image_url):
        """Save one allowlisted Amazon poster as cache/images/imdb_popular/<ttid>.jpg."""
        destination = poster_cache_path(imdb_id)
        if not destination:
            return False
        if poster_is_cached(imdb_id):
            return True
        sized = sized_poster_url(image_url)
        if not allowed_poster_url(sized):
            logger.warning("Refusing IMDb poster URL that is not an Amazon image")
            return False

        lock = _poster_lock(imdb_id)
        with lock:
            if poster_is_cached(imdb_id):
                return True
            os.makedirs(os.path.dirname(destination), exist_ok=True)
            temporary = f"{destination}.{os.getpid()}.part"
            response = None
            try:
                hooks, cookies, verify, proxies = helpers.request_defaults({})
                response = self.session.get(
                    sized,
                    headers={"Accept": "image/jpeg,image/*;q=0.8", "Referer": "https://www.imdb.com/"},
                    timeout=20,
                    allow_redirects=False,
                    stream=True,
                    hooks=hooks,
                    cookies=cookies,
                    verify=verify,
                    proxies=proxies,
                )
                if response.status_code != 200:
                    logger.debug(f"IMDb poster cache got HTTP {response.status_code} for {imdb_id}")
                    return False
                content_type = (response.headers.get("Content-Type") or "").split(";", 1)[0].strip().lower()
                if content_type != "image/jpeg":
                    logger.debug(f"IMDb poster cache got {content_type or 'no content type'} for {imdb_id}")
                    return False
                written = 0
                with open(temporary, "wb") as handle:
                    for chunk in response.iter_content(64 * 1024):
                        if not chunk:
                            continue
                        written += len(chunk)
                        if written > _POSTER_MAX_BYTES:
                            logger.debug(f"IMDb poster for {imdb_id} exceeded {_POSTER_MAX_BYTES} bytes")
                            return False
                        handle.write(chunk)
                if written <= 0:
                    return False
                os.replace(temporary, destination)
                helpers.chmodAsParent(destination)
                return True
            except Exception as error:
                logger.debug(f"IMDb poster cache failed for {imdb_id}: {error}")
                return False
            finally:
                if response is not None:
                    response.close()
                if os.path.exists(temporary):
                    try:
                        os.unlink(temporary)
                    except OSError:
                        pass


def poster_cache_name(imdb_id):
    if not imdb_id or not _IMDB_POSTER_ID_RE.fullmatch(str(imdb_id)):
        return None
    return f"{str(imdb_id).lower()}.jpg"


def poster_cache_relative(imdb_id):
    """URL path under cache/, using forward slashes."""
    name = poster_cache_name(imdb_id)
    if not name:
        return None
    return posixpath.join("images", "imdb_popular", name)


def poster_cache_path(imdb_id):
    name = poster_cache_name(imdb_id)
    if not name or not settings.CACHE_DIR:
        return None
    return os.path.join(settings.CACHE_DIR, "images", "imdb_popular", name)


def poster_is_cached(imdb_id):
    path = poster_cache_path(imdb_id)
    return bool(path and os.path.isfile(path) and os.path.getsize(path) > 0)


def sized_poster_url(image_url):
    """Ask Amazon for a card-sized JPEG. A bare @._V1_.jpg is the full poster."""
    if not image_url or not isinstance(image_url, str):
        return image_url
    if _V1_JPG_RE.search(image_url):
        return _V1_JPG_RE.sub("@._V1_QL75_UX280_.jpg", image_url)
    return imdbPopular.change_size(image_url)


def allowed_poster_url(url):
    if not url or not isinstance(url, str):
        return False
    parsed = urlparse(url.strip())
    if parsed.scheme != "https" or parsed.username is not None or parsed.password is not None:
        return False
    host = (parsed.hostname or "").lower().rstrip(".")
    if host not in _AMAZON_POSTER_HOSTS:
        return False
    path = parsed.path or ""
    return path.startswith("/images/") and ".." not in path.split("/")


def _poster_lock(imdb_id):
    key = str(imdb_id).lower()
    with _poster_locks_guard:
        lock = _poster_locks.get(key)
        if lock is None:
            lock = threading.Lock()
            _poster_locks[key] = lock
        return lock


imdb_popular = imdbPopular()
