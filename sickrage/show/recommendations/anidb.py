# coding=utf-8
from __future__ import unicode_literals

from anidbhttp import anidbquery
from anidbhttp.query import QUERY_HOT
from recommended import RecommendedShow

from sickbeard import helpers
from sickrage.helper.common import try_int


class AnidbPopular(object):
    def __init__(self):
        self.cache_subfolder = __name__.split('.')[-1] if '.' in __name__ else __name__
        self.session = helpers.make_session()

    def fetch_latest_hot_shows(self):
        """Get popular show information from IMDB"""

        shows = []
        result = []

        shows = anidbquery.query(QUERY_HOT)
        for show in shows:
            try:
                recommended_show = RecommendedShow(show.id, show.titles['x-jat'][0], 1, show.tvdbid, cache_subfolder=self.cache_subfolder,
                     rating=str(show.ratings['temporary']['rating']), votes=str(try_int(show.ratings['temporary']['count'], 0)), image_href=show.url)

                # Check cache or get and save image
                recommended_show.cache_image("https://img7.anidb.net/pics/anime/{0}".format(show.image_path))

                result.append(recommended_show)
            except Exception:
                pass

        return result

anidb_popular = AnidbPopular()
