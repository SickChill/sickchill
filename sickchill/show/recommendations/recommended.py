"""
Recommend shows based on lists from indexers
"""
import os
import posixpath

from sickchill import settings
from sickchill.oldbeard import helpers


class RecommendedShow(object):
    """
    Base class for show recommendations
    """

    def __init__(self, show_id, title, indexer, indexer_id, cache_subfolder="recommended", rating=None, votes=None, image_href=None, image_src=None):
        """
        Create a show recommendation

        :param show_id: as provided by the list provider
        :param title: of the show as displayed in the recommended show page
        :param indexer: used to map the show to
        :param indexer_id: a mapped indexer_id for indexer
        :param cache_subfolder: to store images
        :param rating: of the show in percent
        :param votes: number of votes
        :param image_href: the href when clicked on the show image (poster)
        :param image_src: the url to the "cached" image (poster)
        """
        self.show_id = show_id
        self.title = title
        self.indexer = indexer
        self.indexer_id = indexer_id
        self.cache_subfolder = cache_subfolder
        self.rating = rating
        self.votes = votes
        self.image_href = image_href
        self.image_src = image_src

        # Check if the show is currently already in the db
        self.show_in_list = self.indexer_id in {show.indexerid for show in settings.showList if show.indexerid}
        self.session = helpers.make_indexer_session()

    def cache_image(self, image_url):
        """
        Store cache of image in cache dir

        :param image_url: Source URL
        """
        if not self.cache_subfolder:
            return

        self.image_src = posixpath.join("images", self.cache_subfolder, os.path.basename(image_url))

        path = os.path.abspath(os.path.join(settings.CACHE_DIR, "images", self.cache_subfolder))

        if not os.path.exists(path):
            os.makedirs(path)

        full_path = os.path.join(path, os.path.basename(image_url))

        if not os.path.isfile(full_path):
            helpers.download_file(image_url, full_path, session=self.session)
