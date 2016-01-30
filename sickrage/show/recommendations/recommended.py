import os
import posixpath
import requests
import sickbeard
from sickbeard import helpers
from sickrage.helper.encoding import ek

class RecommendedShow(object):
    '''
    show_id: the id of the show as provided by the list provider. For ex. for imdb, this will be the tt1233456 id, for anidb the aid.
    rating: rating of the show in %. For ex. 88 as for 88%
    votes: nummer of votes
    title: title of the show as displayed in the recommended show page
    image_href: the href when clicked on the show image (poster)
    image_src: the url to the "cached" image (poster)
    indexer_id: a mapped indexer_id for indexer
    indexer: the indexer used to map the show to
    show_in_list: Checks if the show is already in the added list of shows
    '''
    def __init__(self, show_id, title, indexer, indexer_id, cache_subfolder='recommended', 
                 rating=None, votes=None, image_href=None, image_src=None, source_url=None):
        self.cache_subfolder = cache_subfolder
        self.session = requests.Session()
        self.show_id = show_id
        self.rating = rating
        self.votes = votes
        self.title = title
        self.image_href = image_href
        self.image_src = image_src
        self.indexer_id = indexer_id
        self.indexer = indexer
        self.show_in_list = None
        
        # Check if the show is currently already in the db
        self.show_in_list = self.indexer_id in [ show.indexerid for show in sickbeard.showList if show.indexerid ]
        
    def cache_image(self, image_url):
        """
        Store cache of image in cache dir
        :param image_url: Source URL
        """
        if not self.cache_subfolder:
            return
        
        self.image_src = ek(posixpath.join, 'images', self.cache_subfolder, ek(os.path.basename, image_url))
        
        path = ek(os.path.abspath, ek(os.path.join, sickbeard.CACHE_DIR, 'images', self.cache_subfolder))

        if not ek(os.path.exists, path):
            ek(os.makedirs, path)

        full_path = ek(posixpath.join, path, ek(os.path.basename, image_url))

        if not ek(os.path.isfile, full_path):
            helpers.download_file(image_url, full_path, session=self.session)