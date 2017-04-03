# coding=utf-8

from __future__ import print_function, unicode_literals

import os
import posixpath

from libtrakt.trakt import TraktAPI
from libtrakt.exceptions import traktException

import sickbeard
from sickbeard import helpers, logger
from sickbeard.indexers.indexer_config import INDEXER_TVDB
from sickrage.helper.encoding import ek
from sickrage.helper.exceptions import ex, MultipleShowObjectsException


class traktTrending(object):
    def __init__(self):
        """Gets a list of most popular TV series from imdb"""

        self.session = helpers.make_session()

    def fetch_trending_shows(self, trakt_list, page_url):
        """Get trending show information from Trakt"""

        trending_shows = []

        trakt_api = TraktAPI(sickbeard.SSL_VERIFY, sickbeard.TRAKT_TIMEOUT)

        try:
            not_liked_show = ""
            if sickbeard.TRAKT_ACCESS_TOKEN != '':
                library_shows = trakt_api.traktRequest("sync/collection/shows?extended=full") or []
                if sickbeard.TRAKT_BLACKLIST_NAME:
                    not_liked_show = trakt_api.traktRequest("users/" + sickbeard.TRAKT_USERNAME + "/lists/" + sickbeard.TRAKT_BLACKLIST_NAME + "/items") or []
                else:
                    logger.log("Trakt blacklist name is empty", logger.DEBUG)

            if trakt_list not in ["recommended", "newshow", "newseason"]:
                limit_show = "?limit=" + str(100 + len(not_liked_show)) + "&"
            else:
                limit_show = "?"

            shows = trakt_api.traktRequest(page_url + limit_show + "extended=full") or []

            if sickbeard.TRAKT_ACCESS_TOKEN != '':
                library_shows = trakt_api.traktRequest("sync/collection/shows?extended=full") or []

            for show in shows:
                try:
                    if 'show' not in show:
                        show['show'] = show

                    if sickbeard.TRAKT_ACCESS_TOKEN != '':
                        if show['show']['ids']['tvdb'] not in (lshow['show']['ids']['tvdb'] for lshow in library_shows):
                            if not_liked_show:
                                if show['show']['ids']['tvdb'] not in (show['show']['ids']['tvdb'] for show in not_liked_show if show['type'] == 'show'):
                                    trending_shows += [show]
                            else:
                                trending_shows += [show]
                    else:
                        if not_liked_show:
                            if show['show']['ids']['tvdb'] not in (show['show']['ids']['tvdb'] for show in not_liked_show if show['type'] == 'show'):
                                trending_shows += [show]
                        else:
                            trending_shows += [show]

                except MultipleShowObjectsException:
                    continue

            if sickbeard.TRAKT_BLACKLIST_NAME != '':
                black_list = True
            else:
                black_list = False

        except traktException as e:
            logger.log("Could not connect to Trakt service: {0}".format(ex(e)), logger.WARNING)

        for trending_show in trending_shows:
            # get indexer id
            indexer_id = trending_show['show']['ids']['tvdb']
            trending_show['indexer_id'] = indexer_id
            # set image path to show (needed to show it on the screen from the cache)
            image_name = self.get_image_name(indexer_id)
            image_path_relative = ek(posixpath.join, 'images', 'trakt_trending', image_name)
            trending_show['image_path'] = image_path_relative
            # clear indexer_id if we already have the image in the cache so we don't retrieve it again
            image_path = self.get_image_path(image_name)
            if ek(os.path.isfile, image_path):
                trending_show['indexer_id'] = ''

        return trending_shows, black_list

    @staticmethod
    def get_image_url(indexer_id):
        """ Get poster image url from TVDB """
        image_url = None

        try:
            lINDEXER_API_PARMS = sickbeard.indexerApi(INDEXER_TVDB).api_params.copy()

            lINDEXER_API_PARMS['banners'] = True

            t = sickbeard.indexerApi(INDEXER_TVDB).indexer(**lINDEXER_API_PARMS)
            indexer_show_obj = t[int(indexer_id)]
        except (sickbeard.indexer_error, IOError) as e:
            logger.log("Show id " + indexer_id + " not found on " + sickbeard.indexerApi(INDEXER_TVDB).name +
                       ", not downloading poster: " + ex(e), logger.DEBUG)
            return None

        if getattr(indexer_show_obj, 'poster', None):
            image_url = indexer_show_obj['poster'].replace('posters', '_cache/posters')

        return image_url

    @staticmethod
    def get_image_name(indexer_id):
         return str(indexer_id) + ".jpg"

    @staticmethod
    def get_image_path(image_name):
        path = ek(os.path.abspath, ek(os.path.join, sickbeard.CACHE_DIR, 'images', 'trakt_trending'))

        if not ek(os.path.exists, path):
            ek(os.makedirs, path)

        return ek(os.path.join, path, image_name)

    def cache_image(self, image_url, image_path):
        # Only cache if the file does not exist yet
        if not ek(os.path.isfile, image_path):
            helpers.download_file(image_url, image_path, session=self.session)

trakt_trending = traktTrending()
