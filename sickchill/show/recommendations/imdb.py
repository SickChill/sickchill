import os
import re

import imdb
from imdb.parser.http.piculet import Path, Rule

from sickchill import settings
from sickchill.oldbeard import helpers


class imdbPopular(object):
    def __init__(self):
        """Gets a list of most popular TV series from imdb"""
        self.session = helpers.make_session()

        self.imdb = imdb.IMDb()
        try:
            self.imdb.topBottomProxy.tvmeter100_parser.rules[0].extractor.rules.append(
                Rule(key="cover url", extractor=Path('./td[@class="posterColumn"]/a/img/@src'))
            )
        except Exception:
            pass

    def fetch_popular_shows(self):
        """Get popular show information from IMDB"""
        return self.imdb.get_popular100_tv()

    def imdb_url(self, result):
        return self.imdb.get_imdbURL(result)

    @staticmethod
    def change_size(image_url, factor=3):
        match = re.search(r"^(.*)V1_(.{2})(.*?)_(.{2})(.*?),(.*?),(.*?),(.\d?)_(.*?)_.jpg$", image_url)

        if match:
            matches = match.groups()
            os.path.basename(image_url)
            matches = list(matches)
            matches[2] = int(matches[2]) * factor
            matches[4] = int(matches[4]) * factor
            matches[5] = int(matches[5]) * factor
            matches[6] = int(matches[6]) * factor
            matches[7] = int(matches[7]) * factor

            return "{0}V1._{1}{2}_{3}{4},{5},{6},{7}_.jpg".format(
                matches[0], matches[1], matches[2], matches[3], matches[4], matches[5], matches[6], matches[7]
            )
        else:
            return image_url

    def cache_image(self, image_url):
        """
        Store cache of image in cache dir
        :param image_url: Source URL
        """
        path = os.path.abspath(os.path.join(settings.CACHE_DIR, "images", "imdb_popular"))

        if not os.path.exists(path):
            os.makedirs(path)

        full_path = os.path.join(path, os.path.basename(image_url))

        if not os.path.isfile(full_path):
            helpers.download_file(image_url, full_path, session=self.session)


imdb_popular = imdbPopular()
