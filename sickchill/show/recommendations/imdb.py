import os
import posixpath
import re
from datetime import date
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from sickchill import settings
from sickchill.oldbeard import helpers


class imdbPopular(object):
    def __init__(self):
        """Gets a list of most popular TV series from imdb"""

        self.base_url = 'https://imdb.com'
        self.url = urljoin(self.base_url, 'search/title')

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

        data = helpers.getURL(self.url, session=self.session, params=self.params, headers={'Referer': self.base_url}, returns='text')
        if not data:
            return None

        soup = BeautifulSoup(data, 'html5lib')
        results = soup.find_all("div", {"class": "lister-item"})

        for row in results:
            show = {}
            image_div = row.find("div", {"class": "lister-item-image"})
            if image_div:
                image = image_div.find("img")
                show['image_url_large'] = self.change_size(image['loadlate'], 3)
                show['imdb_tt'] = image['data-tconst']
                show['image_path'] = posixpath.join('images', 'imdb_popular', os.path.basename(show['image_url_large']))
                self.cache_image(show['image_url_large'])

            content = row.find("div", {"class": "lister-item-content"})
            if content:
                header = row.find("h3", {"class": "lister-item-header"})
                if header:
                    a_tag = header.find("a")
                    if a_tag:
                        show['name'] = a_tag.get_text(strip=True)
                        show['imdb_url'] = "http://www.imdb.com" + a_tag["href"]
                        show['year'] = header.find("span", {"class": "lister-item-year"}).contents[0].split(" ")[0][1:].strip("-")

                imdb_rating = row.find("div", {"class": "ratings-imdb-rating"})
                show['rating'] = imdb_rating['data-value'] if imdb_rating else None

                votes = row.find("span", {"name": "nv"})
                show['votes'] = votes['data-value'] if votes else None

                outline = content.find_all("p", {"class": "text-muted"})
                if outline and len(outline) >= 2:
                    show['outline'] = outline[1].contents[0].strip("\"")
                else:
                    show['outline'] = ''

                popular_shows.append(show)

        return popular_shows

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

            return "{0}V1._{1}{2}_{3}{4},{5},{6},{7}_.jpg".format(matches[0], matches[1], matches[2], matches[3], matches[4],
                                                                  matches[5], matches[6], matches[7])
        else:
            return image_url

    def cache_image(self, image_url):
        """
        Store cache of image in cache dir
        :param image_url: Source URL
        """
        path = os.path.abspath(os.path.join(settings.CACHE_DIR, 'images', 'imdb_popular'))

        if not os.path.exists(path):
            os.makedirs(path)

        full_path = os.path.join(path, os.path.basename(image_url))

        if not os.path.isfile(full_path):
            helpers.download_file(image_url, full_path, session=self.session)


imdb_popular = imdbPopular()
