# coding=utf-8

from __future__ import print_function, unicode_literals

import re
import os
import posixpath
from bs4 import BeautifulSoup
from datetime import date

import sickbeard
from sickbeard import helpers
from sickrage.helper.encoding import ek


class imdbPopular(object):
    def __init__(self):
        """Gets a list of most popular TV series from imdb"""

        # Use akas.imdb.com, just like the imdb lib.
        self.url = 'http://akas.imdb.com/search/title'

        self.params = {
            'at': 0,
            'sort': 'moviemeter',
            'title_type': 'tv_series',
            'year': '{0},{1}'.format(date.today().year - 1, date.today().year + 1)
        }

        self.session = helpers.make_session()

    def fetch_popular_shows(self):
        """Get popular show information from IMDB"""

        popular_shows = []

        data = helpers.getURL(self.url, session=self.session, params=self.params, headers={'Referer': 'http://akas.imdb.com/'}, returns='text')
        if not data:
            return None

        soup = BeautifulSoup(data, 'html5lib')
        results = soup.find("table", {"class": "results"})
        rows = results("tr")

        for row in rows:
            show = {}
            image_td = row.find("td", {"class": "image"})

            if image_td:
                image = image_td.find("img")
                show['image_url_large'] = self.change_size(image['src'], 3)
                show['image_path'] = ek(posixpath.join, 'images', 'imdb_popular', ek(os.path.basename, show['image_url_large']))

                self.cache_image(show['image_url_large'])

            td = row.find("td", {"class": "title"})

            if td:
                show['name'] = td.find("a").contents[0]
                show['imdb_url'] = "http://akas.imdb.com" + td.find("a")["href"]
                show['imdb_tt'] = show['imdb_url'][-10:][0:9]
                show['year'] = td.find("span", {"class": "year_type"}).contents[0].split(" ")[0][1:]

                rating_all = td.find("div", {"class": "user_rating"})
                if rating_all:
                    rating_string = rating_all.find("div", {"class": "rating rating-list"})
                    if rating_string:
                        rating_string = rating_string['title']

                        match = re.search(r".* (.*)\/10.*\((.*)\).*", rating_string)
                        if match:
                            matches = match.groups()
                            show['rating'] = matches[0]
                            show['votes'] = matches[1]
                        else:
                            show['rating'] = None
                            show['votes'] = None
                else:
                    show['rating'] = None
                    show['votes'] = None

                outline = td.find("span", {"class": "outline"})
                if outline:
                    show['outline'] = outline.contents[0]
                else:
                    show['outline'] = ''

                popular_shows.append(show)

        return popular_shows

    @staticmethod
    def change_size(image_url, factor=3):
        match = re.search(r"^(.*)V1._(.{2})(.*?)_(.{2})(.*?),(.*?),(.*?),(.*?)_.jpg$", image_url)

        if match:
            matches = match.groups()
            ek(os.path.basename, image_url)
            matches = list(matches)
            matches[2] = int(matches[2]) * factor
            matches[4] = int(matches[4]) * factor
            matches[5] = int(matches[5]) * factor
            matches[6] = int(matches[6]) * factor
            matches[7] = int(matches[7]) * factor

            return "{0}V1._{1}{2}_{3}{4},{5},{6},{7}_.jpg".format(matches[0], matches[1], matches[2], matches[3], matches[4],
                                                      matches[5], matches[6], matches[7])
        else:
            return image_url

    def cache_image(self, image_url):
        """
        Store cache of image in cache dir
        :param image_url: Source URL
        """
        path = ek(os.path.abspath, ek(os.path.join, sickbeard.CACHE_DIR, 'images', 'imdb_popular'))

        if not ek(os.path.exists, path):
            ek(os.makedirs, path)

        full_path = ek(os.path.join, path, ek(os.path.basename, image_url))

        if not ek(os.path.isfile, full_path):
            helpers.download_file(image_url, full_path, session=self.session)

imdb_popular = imdbPopular()
