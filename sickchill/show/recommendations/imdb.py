import os
import re

from imdbpie import Imdb, ImdbFacade
from imdbpie.exceptions import ImdbAPIError

from sickchill import logger, settings
from sickchill.oldbeard import helpers


class imdbPopular(object):
    def __init__(self):
        """Gets a list of most popular TV series from IMDb via imdb-pie"""
        self.session = helpers.make_session()
        self.client = Imdb()  # Low-level client
        self.imdb = ImdbFacade(client=self.client)  # Higher-level facade (recommended)

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
            print(f"Failed to get title {imdb_id}: {e}")
            return None

    def imdb_url(self, result):
        """Return full IMDb URL"""
        imdb_id = result.get("id") or result.get("tconst") or getattr(result, "imdb_id", None)
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


imdb_popular = imdbPopular()
