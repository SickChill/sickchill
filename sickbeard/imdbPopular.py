import requests
from bs4 import BeautifulSoup
import re
from datetime import date

url = "http://www.imdb.com/search/title?at=0&sort=moviemeter&title_type=tv_series&year=%s,%s" % \
      (date.today().year - 1, date.today().year + 1)

def fetch_popular_shows():
    popular_shows = []

    r = requests.get(url)
    if r.status_code == 200:
        soup = BeautifulSoup(r.text)
        results = soup.find("table", {"class": "results"})
        rows = results.find_all("tr");

        for row in rows:
            show = {}
            image_td = row.find("td", {"class": "image"})

            if image_td:
                image = image_td.find("img")
                show['image_url'] =  image['src']
                show['image_url_large'] = show['image_url'].replace(
                    "V1._SX54_CR0,0,54,74_.jpg","V1._SX108_CR0,0,108,148_.jpg")

            td = row.find("td", {"class": "title"})
            if td:

                show['name'] = td.find("a").contents[0]
                show['imdb_url'] = "http://www.imdb.com" + td.find("a")["href"]
                show['year'] = td.find("span", {"class": "year_type"}).contents[0].split(" ")[0][1:]

                rating_all = td.find("div", {"class": "user_rating"})
                if rating_all:
                    rating_string = rating_all.find("div", {"class": "rating rating-list"})
                    if rating_string:
                        rating_string = rating_string['title']

                        matches = re.search(".* (.*)\/10.*\((.*)\).*", rating_string).groups()
                        show['rating'] = matches[0]
                        show['votes'] = matches[1]

                else:
                    show['rating'] = None
                    show['votes'] = None

                show['outline'] = td.find("span", {"class": "outline"}).contents[0]
                popular_shows.append(show)

        return popular_shows
    else:
        return None
