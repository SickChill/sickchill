import os.path
from mimetypes import guess_type

import imagesize

import sickchill
from sickchill import logger, settings
from sickchill.helper.exceptions import ShowDirectoryNotFoundException
from sickchill.providers.metadata.generic import GenericMetadata
from sickchill.providers.metadata.helpers import getShowImage

from . import helpers


class ImageCache(object):
    def __init__(self):
        pass

    def __del__(self):
        pass

    @staticmethod
    def _cache_dir():
        """
        Builds up the full path to the image cache directory
        """
        return os.path.abspath(os.path.join(settings.CACHE_DIR, "images"))

    def _thumbnails_dir(self):
        """
        Builds up the full path to the thumbnails image cache directory
        """
        return os.path.abspath(os.path.join(self._cache_dir(), "thumbnails"))

    def poster_path(self, indexer_id):
        """
        Builds up the path to a poster cache for a given Indexer ID

        :param indexer_id: ID of the show to use in the file name
        :return: a full path to the cached poster file for the given Indexer ID
        """
        poster_filename = str(indexer_id) + ".poster.jpg"
        return os.path.join(self._cache_dir(), poster_filename)

    def banner_path(self, indexer_id):
        """
        Builds up the path to a banner cache for a given Indexer ID

        :param indexer_id: ID of the show to use in the file name
        :return: a full path to the cached banner file for the given Indexer ID
        """
        banner_filename = str(indexer_id) + ".banner.jpg"
        return os.path.join(self._cache_dir(), banner_filename)

    def fanart_path(self, indexer_id):
        """
        Builds up the path to a fanart cache for a given Indexer ID

        :param indexer_id: ID of the show to use in the file name
        :return: a full path to the cached fanart file for the given Indexer ID
        """
        fanart_filename = str(indexer_id) + ".fanart.jpg"
        return os.path.join(self._cache_dir(), fanart_filename)

    def poster_thumb_path(self, indexer_id):
        """
        Builds up the path to a poster thumb cache for a given Indexer ID

        :param indexer_id: ID of the show to use in the file name
        :return: a full path to the cached poster thumb file for the given Indexer ID
        """
        posterthumb_filename = str(indexer_id) + ".poster.jpg"
        return os.path.join(self._thumbnails_dir(), posterthumb_filename)

    def banner_thumb_path(self, indexer_id):
        """
        Builds up the path to a banner thumb cache for a given Indexer ID

        :param indexer_id: ID of the show to use in the file name
        :return: a full path to the cached banner thumb file for the given Indexer ID
        """
        bannerthumb_filename = str(indexer_id) + ".banner.jpg"
        return os.path.join(self._thumbnails_dir(), bannerthumb_filename)

    def has_poster(self, indexer_id):
        """
        Returns true if a cached poster exists for the given Indexer ID
        """
        poster_path = self.poster_path(indexer_id)
        logger.debug(f"Checking if file poster_path exists")
        return os.path.isfile(poster_path)

    def has_banner(self, indexer_id):
        """
        Returns true if a cached banner exists for the given Indexer ID
        """
        banner_path = self.banner_path(indexer_id)
        logger.debug(f"Checking if file banner_path exists")
        return os.path.isfile(banner_path)

    def has_fanart(self, indexer_id):
        """
        Returns true if a cached fanart exists for the given Indexer ID
        """
        fanart_path = self.fanart_path(indexer_id)
        logger.debug(f"Checking if file fanart_path exists")
        return os.path.isfile(fanart_path)

    def has_poster_thumb(self, indexer_id):
        """
        Returns true if a cached poster thumbnail exists for the given Indexer ID
        """
        poster_thumb_path = self.poster_thumb_path(indexer_id)
        logger.debug(f"Checking if file poster_thumb_path exists")
        return os.path.isfile(poster_thumb_path)

    def has_banner_thumb(self, indexer_id):
        """
        Returns true if a cached banner exists for the given Indexer ID
        """
        banner_thumb_path = self.banner_thumb_path(indexer_id)
        logger.debug(f"Checking if file banner_thumb_path exists")
        return os.path.isfile(banner_thumb_path)

    def image_url(self, indexer_id, which):
        path = self.__getattribute__(which + "_path")(indexer_id)
        if os.path.isfile(path):
            return "cache" + path.split(settings.CACHE_DIR)[1].replace("\\", "/")
        if which == "fanart" and settings.SICKCHILL_BACKGROUND:
            return "ui/sickchill_background"

        return ("images/poster.png", "images/banner.png")["banner" in which]

    BANNER = 1
    POSTER = 2
    BANNER_THUMB = 3
    POSTER_THUMB = 4
    FANART = 5

    image_str = {BANNER: "banner", BANNER_THUMB: "banner thumbnail", POSTER: "poster", POSTER_THUMB: "poster thumbnail", FANART: "fanart"}

    def which_type(self, path):
        """
        Analyzes the image provided and attempts to determine whether it is a poster or banner.

        :param path: full path to the image
        :return: BANNER, POSTER if it concluded one or the other, or None if the image was neither (or didn't exist)
        """

        if not os.path.isfile(path):
            logger.warning(f"Couldn't check the type of {path} cause it doesn't exist")
            return None

        width, height = imagesize.get(path)

        if not (width and height):
            logger.debug(f"Unable to get metadata from {path}, not using your existing image")
            return None

        img_ratio = float(width) / float(height)

        # most posters are around 0.68 width/height ratio (eg. 680/1000)
        if 0.55 < img_ratio < 0.8:
            return self.POSTER

        # most banners are around 5.4 width/height ratio (eg. 758/140)
        elif 5 < img_ratio < 6:
            return self.BANNER

        # most fanart are around 1.77777 width/height ratio (eg. 1280/720 and 1920/1080)
        elif 1.7 < img_ratio < 1.8:
            return self.FANART
        else:
            logger.warning(f"Image has size ratio of {img_ratio}, unknown type")
            return None

    @staticmethod
    def image_data(path):
        """
        :return: The content of the desired media file
        """

        if os.path.isfile(path):
            with open(path, "rb") as content:
                return content.read()

        return None

    @staticmethod
    def content_type(path):
        """
        :return: The mime type of the current media
        """

        if os.path.isfile(path):
            return guess_type(path)[0]

        return ""

    def _cache_image_from_file(self, image_path, img_type, indexer_id):
        """
        Takes the image provided and copies it to the cache folder

        :param image_path: path to the image we're caching
        :param img_type: BANNER or POSTER or FANART
        :param indexer_id: id of the show this image belongs to
        :return: bool representing success
        """

        # generate the path based on the type & indexer_id
        if img_type == self.POSTER:
            dest_path = self.poster_path(indexer_id)
        elif img_type == self.BANNER:
            dest_path = self.banner_path(indexer_id)
        elif img_type == self.FANART:
            dest_path = self.fanart_path(indexer_id)
        else:
            logger.exception(f"Invalid cache image type: {img_type}")
            return False

        # make sure the cache folder exists before we try copying to it
        if not os.path.isdir(self._cache_dir()):
            logger.info(f"Image cache dir didn't exist, creating it at {self._cache_dir()}")
            os.makedirs(self._cache_dir())

        if not os.path.isdir(self._thumbnails_dir()):
            logger.info(f"Thumbnails cache dir didn't exist, creating it at {self._thumbnails_dir()}")
            os.makedirs(self._thumbnails_dir())

        logger.info(f"Copying from {image_path} to {dest_path}")
        helpers.copyFile(image_path, dest_path)

        return True

    def _cache_image_from_indexer(self, show_obj, img_type):
        """
        Retrieves an image of the type specified from indexer and saves it to the cache folder

        :param show_obj: TVShow object that we want to cache an image for
        :param img_type: BANNER or POSTER or FANART
        :return: bool representing success
        """

        metadata_generator = GenericMetadata()

        # generate the path based on the type & indexer_id
        if img_type == self.POSTER:
            img_url = sickchill.indexer.series_poster_url(show_obj)
            if not img_url:
                img_url = metadata_generator._retrieve_show_image_urls_from_fanart(show_obj, "poster")
            if not img_url:
                img_url = metadata_generator._retrieve_show_image_urls_from_tmdb(show_obj, "poster")
            dest_path = self.poster_path(show_obj.indexerid)
        elif img_type == self.BANNER:
            img_url = sickchill.indexer.series_banner_url(show_obj)
            if not img_url:
                img_url = metadata_generator._retrieve_show_image_urls_from_fanart(show_obj, "banner")
            dest_path = self.banner_path(show_obj.indexerid)
        elif img_type == self.POSTER_THUMB:
            img_url = sickchill.indexer.series_poster_url(show_obj, thumb=True)
            if not img_url:
                img_url = metadata_generator._retrieve_show_image_urls_from_fanart(show_obj, "poster", thumb=True)
            if not img_url:
                img_url = metadata_generator._retrieve_show_image_urls_from_tmdb(show_obj, "poster")
            dest_path = self.poster_thumb_path(show_obj.indexerid)
        elif img_type == self.BANNER_THUMB:
            img_url = sickchill.indexer.series_banner_url(show_obj, thumb=True)
            if not img_url:
                img_url = metadata_generator._retrieve_show_image_urls_from_fanart(show_obj, "banner", thumb=True)
            dest_path = self.banner_thumb_path(show_obj.indexerid)
        elif img_type == self.FANART:
            img_url = sickchill.indexer.series_fanart_url(show_obj)
            if not img_url:
                img_url = metadata_generator._retrieve_show_image_urls_from_fanart(show_obj, "fanart")
            if not img_url:
                img_url = metadata_generator._retrieve_show_image_urls_from_tmdb(show_obj, "fanart")
            dest_path = self.fanart_path(show_obj.indexerid)
        else:
            logger.exception(f"Invalid cache image type: {img_type}")
            return False

        # retrieve the image from indexer using the generic metadata class
        # TODO: refactor
        img_data = getShowImage(img_url)
        result = metadata_generator._write_image(img_data, dest_path)

        return result

    def fill_cache(self, show_obj):
        """
        Caches all images for the given show. Copies them from the show dir if possible, or
        downloads them from indexer if they aren't in the show dir.

        :param show_obj: TVShow object to cache images for
        """

        logger.debug(f"Checking if we need any cache images for show {show_obj.indexerid}")

        # check if the images are already cached or not
        need_images = {
            self.POSTER: not self.has_poster(show_obj.indexerid),
            self.BANNER: not self.has_banner(show_obj.indexerid),
            self.POSTER_THUMB: not self.has_poster_thumb(show_obj.indexerid),
            self.BANNER_THUMB: not self.has_banner_thumb(show_obj.indexerid),
            self.FANART: not self.has_fanart(show_obj.indexerid),
        }

        if not any(need_images.values()):
            logger.debug("No new cache images needed, not retrieving new ones")
            return

        # check the show dir for poster or banner images and use them
        if need_images[self.POSTER] or need_images[self.BANNER] or need_images[self.FANART]:
            try:
                for cur_provider in settings.metadata_provider_dict.values():
                    logger.debug("[{}] Checking if we can use images from {} metadata".format(show_obj.indexerid, cur_provider.name))

                    for method in (cur_provider.get_poster_path, cur_provider.get_banner_path, cur_provider.get_fanart_path):
                        current_path = method(show_obj)
                        if os.path.isfile(current_path):
                            cur_filename = os.path.abspath(current_path)
                            cur_file_type = self.which_type(cur_filename)

                            if cur_file_type is None:
                                logger.warning(f"Unable to retrieve image type, not using the image from {cur_filename}")
                                continue

                            logger.debug(
                                "[{}] Checking if {} ({}) needs cached: {}".format(
                                    show_obj.indexerid, cur_filename, self.image_str[cur_file_type], need_images[cur_file_type]
                                )
                            )

                            if cur_file_type in need_images and need_images[cur_file_type]:
                                logger.debug(
                                    "[{}] Found a {} in the show dir that doesn't exist in the cache, caching it".format(
                                        show_obj.indexerid, self.image_str[cur_file_type]
                                    )
                                )
                                self._cache_image_from_file(cur_filename, cur_file_type, show_obj.indexerid)
                                need_images[cur_file_type] = False

            except ShowDirectoryNotFoundException:
                logger.debug("[{}] Unable to search for images in show dir because it doesn't exist".format(show_obj.indexerid))

        # download from indexer for missing ones
        for cur_image_type in need_images:
            logger.debug("[{}] Seeing if we still need a {}: {}".format(show_obj.indexerid, self.image_str[cur_image_type], need_images[cur_image_type]))
            if cur_image_type in need_images and need_images[cur_image_type]:
                self._cache_image_from_indexer(show_obj, cur_image_type)

        logger.info("Done cache check")
