import os
import posixpath

from sickchill import logger, settings
from sickchill.helper.exceptions import MultipleShowObjectsException
from sickchill.oldbeard.trakt_api import TraktAPI, traktException

from . import helpers


class traktTrending(object):
    def __init__(self):
        """Gets a list of most popular TV series from imdb"""

        self.session = helpers.make_session()

    def fetch_trending_shows(self, trakt_list, page_url):
        """Get trending show information from Trakt"""

        trending_shows = []

        trakt_api = TraktAPI(settings.SSL_VERIFY, settings.TRAKT_TIMEOUT)

        try:
            not_liked_show = ""
            if settings.TRAKT_ACCESS_TOKEN != "":
                library_shows = trakt_api.traktRequest("sync/collection/shows?extended=full") or []
                if settings.TRAKT_BLACKLIST_NAME:
                    not_liked_show = trakt_api.traktRequest("users/" + settings.TRAKT_USERNAME + "/lists/" + settings.TRAKT_BLACKLIST_NAME + "/items") or []
                else:
                    logger.debug("Trakt blacklist name is empty")

            if trakt_list not in ["recommended", "newshow", "newseason"]:
                limit_show = "?limit=" + str(100 + len(not_liked_show)) + "&"
            else:
                limit_show = "?"

            shows = trakt_api.traktRequest(page_url + limit_show + "extended=full") or []

            if settings.TRAKT_ACCESS_TOKEN != "":
                library_shows = trakt_api.traktRequest("sync/collection/shows?extended=full") or []

            for show in shows:
                try:
                    if "show" not in show:
                        show["show"] = show

                    if settings.TRAKT_ACCESS_TOKEN != "":
                        if show["show"]["ids"]["tvdb"] not in (lshow["show"]["ids"]["tvdb"] for lshow in library_shows):
                            if not_liked_show:
                                if show["show"]["ids"]["tvdb"] not in (nlshow["show"]["ids"]["tvdb"] for nlshow in not_liked_show if nlshow["type"] == "show"):
                                    trending_shows += [show]
                            else:
                                trending_shows += [show]
                    else:
                        if not_liked_show:
                            if show["show"]["ids"]["tvdb"] not in (nlshow["show"]["ids"]["tvdb"] for nlshow in not_liked_show if nlshow["type"] == "show"):
                                trending_shows += [show]
                        else:
                            trending_shows += [show]

                except MultipleShowObjectsException:
                    continue

            if settings.TRAKT_BLACKLIST_NAME != "":
                black_list = True
            else:
                black_list = False

        except traktException as e:
            logger.warning("Could not connect to Trakt service: {0}".format(str(e)))

        for trending_show in trending_shows:
            # get indexer id
            indexer_id = trending_show["show"]["ids"]["tvdb"]
            trending_show["indexer_id"] = indexer_id
            # set image path to show (needed to show it on the screen from the cache)
            image_name = self.get_image_name(indexer_id)
            image_path_relative = posixpath.join("images", "trakt_trending", image_name)
            trending_show["image_path"] = image_path_relative
            # clear indexer_id if we already have the image in the cache so we don't retrieve it again
            image_path = self.get_image_path(image_name)
            if os.path.isfile(image_path):
                trending_show["indexer_id"] = ""

        return trending_shows, black_list

    @staticmethod
    def get_image_name(indexer_id):
        return str(indexer_id) + ".jpg"

    @staticmethod
    def get_image_path(image_name):
        path = os.path.abspath(os.path.join(settings.CACHE_DIR, "images", "trakt_trending"))

        if not os.path.exists(path):
            os.makedirs(path)

        return os.path.join(path, image_name)

    def cache_image(self, image_url, image_path):
        # Only cache if the file does not exist yet
        if not os.path.isfile(image_path):
            helpers.download_file(image_url, image_path, session=self.session)


trakt_trending = traktTrending()
