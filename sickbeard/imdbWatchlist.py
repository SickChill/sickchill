# coding=utf-8
import re
import os
import requests
from bs4 import BeautifulSoup
from datetime import date

import sickbeard
from sickbeard import helpers
from sickrage.helper.encoding import ek


class imdbWatchlist(object):
    def __init__(self):
        """Gets a list of most TV series from imdb"""

        # Use akas.imdb.com, just like the imdb lib.
        self.url = 'http://akas.imdb.com/search/title'

        self.params = {}
        self.params['popular'] = {
            'at': 0,
            'sort': 'moviemeter',
            'title_type': 'tv_series',
            'year': '%s,%s' % (date.today().year - 1, date.today().year + 1)
        }
        
        self.params['watchlist'] = {   
            'at': 0,
            'title_type': 'tv_series',
            'sort' : 'year,desc'
        }

        self.session = requests.Session()

    def fetch_shows_from_watchlist(self, list_id=None):
        """Get popular show information from IMDB"""

        shows = []
        
        if list_id not in 'popular':
            params = self.params['watchlist']
            params['lists'] = list_id
        else:
            params = self.params['popular']

        data = helpers.getURL(self.url, session=self.session, params=params, headers={'Referer': 'http://akas.imdb.com/'})
        if not data:
            return None

        soup = BeautifulSoup(data, 'html5lib')
        results = soup.find("table", {"class": "results"})
        rows = results.find_all("tr")

        for row in rows:
            show = {}
            image_td = row.find("td", {"class": "image"})

            if image_td:
                image = image_td.find("img")
                show['image_url_large'] = self.change_size(image['src'], 3)
                show['image_path'] = ek(os.path.join, 'images', 'imdb', ek(os.path.basename, show['image_url_large']))

                self.cache_image(show['image_url_large'])

            td = row.find("td", {"class": "title"})

            if td:
                show['name'] = td.find("a").contents[0]
                show['imdb_url'] = "http://www.imdb.com" + td.find("a")["href"]
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
                    show['outline'] = u''

                shows.append(show)

        return shows

    @staticmethod
    def change_size(image_url, factor=3):
        match = re.search("^(.*)V1._(.{2})(.*?)_(.{2})(.*?),(.*?),(.*?),(.*?)_.jpg$", image_url)

        if match:
            matches = match.groups()
            ek(os.path.basename, image_url)
            matches = list(matches)
            matches[2] = int(matches[2]) * factor
            matches[4] = int(matches[4]) * factor
            matches[5] = int(matches[5]) * factor
            matches[6] = int(matches[6]) * factor
            matches[7] = int(matches[7]) * factor

            return "%sV1._%s%s_%s%s,%s,%s,%s_.jpg" % (matches[0], matches[1], matches[2], matches[3], matches[4],
                                                      matches[5], matches[6], matches[7])
        else:
            return image_url
    
    def get_lists_from_user(self, user_id):
        url = "http://www.imdb.com/user/%s/watchlist"
        
        data = helpers.getURL(url % user_id, session=self.session, params={"ref_" : "wt_nv_wl_all_0"}, headers={'Referer': 'http://akas.imdb.com/'})
        
        list_ids = []
        
        # Retrieve the Main Watchlist list id's
        # user_id should be parsed as: ur59344686
        re_main_watchlist = re.compile("(ls[0-9]+)&author_id=%s" % (user_id))
        main_watchlist_id = re_main_watchlist.findall(data)
            
        # Retrieve the any secondary list id's
        re_secondary_list_ids = re.compile(".*<strong><a.href=./list/(ls[0-9]+)\?[^>]+>([^<]+).*")
        secondary_list_ids = re_secondary_list_ids.findall(data)
        
        # A user should always have a primary whatchlist
        if not main_watchlist_id:
            return False
        
        list_ids.append({ "Watchlist" : main_watchlist_id[0]})
        
        # Let's search of addintional watchlists
        for list_id, list_desc in secondary_list_ids:
            list_ids.append({ list_desc : list_id })
            
        return list_ids
        
    def cache_image(self, image_url):
        """
        Store cache of image in cache dir
        :param image_url: Source URL
        """
        path = ek(os.path.abspath, ek(os.path.join, sickbeard.CACHE_DIR, 'images', 'imdb'))

        if not ek(os.path.exists, path):
            ek(os.makedirs, path)

        full_path = ek(os.path.join, path, ek(os.path.basename, image_url))

        if not ek(os.path.isfile, full_path):
            helpers.download_file(image_url, full_path, session=self.session)

imdb_watchlist = imdbWatchlist()
