import os

import sickchill
from sickchill import settings
from sickchill.oldbeard import helpers
from sickchill.show.Show import Show


class IndexerFavorites(object):
    def __init__(self):
        self.cache_subfolder = __name__.split(".")[-1] if "." in __name__ else __name__
        self.session = helpers.make_indexer_session()

    def fetch_indexer_favorites(self):
        """Get favorited show information from Indexers"""

        indexer_favorites = sickchill.indexer.get_indexer_favorites()
        results = []
        for series in indexer_favorites:
            if Show().find(settings.showList, series.id):
                continue
            results.append(series)
            self.cache_image(series.id)

        return results

    def cache_image(self, indexerid):
        """
        Store cache of image in cache dir
        :param indexerid: Source indexer id
        """
        path = os.path.abspath(os.path.join(settings.CACHE_DIR, "images", "favorites"))

        if not os.path.exists(path):
            os.makedirs(path)

        full_path = os.path.join(path, str(indexerid))

        if not os.path.isfile(full_path):
            helpers.download_file(sickchill.indexer.series_poster_url_by_id(indexerid), full_path, session=self.session)

    @staticmethod
    def test_user_key(user, key, indexer):
        return sickchill.indexer.indexers[indexer].test_user_key(user, key)


favorites = IndexerFavorites()
