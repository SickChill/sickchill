from mimetypes import guess_type
from pathlib import Path, PosixPath

import imagesize

import sickchill
from sickchill import logger, settings
from sickchill.helper.exceptions import ShowDirectoryNotFoundException
from sickchill.providers.metadata.generic import GenericMetadata
from sickchill.providers.metadata.helpers import getShowImage

from . import helpers


class ImageCache(object):
    BANNER = 1
    POSTER = 2
    BANNER_THUMB = 3
    POSTER_THUMB = 4
    FANART = 5

    image_str = {BANNER: "banner", BANNER_THUMB: "banner thumbnail", POSTER: "poster", POSTER_THUMB: "poster thumbnail", FANART: "fanart"}

    @staticmethod
    def _cache_dir() -> Path:
        """
        Builds up the full path to the image cache directory
        """
        return (settings.CACHE_DIR / "images").absolute()

    def _thumbnails_dir(self) -> Path:
        """
        Builds up the full path to the thumbnails image cache directory
        """
        return self._cache_dir() / "thumbnails"

    def poster_path(self, indexer_id) -> Path:
        """
        Builds up the path to a poster cache for a given Indexer ID

        :param indexer_id: ID of the show to use in the file name
        :return: a full path to the cached poster file for the given Indexer ID
        """
        return self._cache_dir() / f"{indexer_id}.poster.jpg"

    def banner_path(self, indexer_id) -> Path:
        """
        Builds up the path to a banner cache for a given Indexer ID

        :param indexer_id: ID of the show to use in the file name
        :return: a full path to the cached banner file for the given Indexer ID
        """
        return self._cache_dir() / f"{indexer_id}.banner.jpg"

    def fanart_path(self, indexer_id) -> Path:
        """
        Builds up the path to a fanart cache for a given Indexer ID

        :param indexer_id: ID of the show to use in the file name
        :return: a full path to the cached fanart file for the given Indexer ID
        """
        return self._cache_dir() / f"{indexer_id}.fanart.jpg"

    def poster_thumb_path(self, indexer_id) -> Path:
        """
        Builds up the path to a poster thumb cache for a given Indexer ID

        :param indexer_id: ID of the show to use in the file name
        :return: a full path to the cached poster thumb file for the given Indexer ID
        """
        return self._thumbnails_dir() / f"{indexer_id}.poster.jpg"

    def banner_thumb_path(self, indexer_id) -> Path:
        """
        Builds up the path to a banner thumb cache for a given Indexer ID

        :param indexer_id: ID of the show to use in the file name
        :return: a full path to the cached banner thumb file for the given Indexer ID
        """
        return self._thumbnails_dir() / f"{indexer_id}.banner.jpg"

    def has_poster(self, indexer_id) -> bool:
        """
        Returns true if a cached poster exists for the given Indexer ID
        """
        filename = self.poster_path(indexer_id)
        logger.debug(_(f"Checking if file {filename} exists"))
        return filename.exists()

    def has_banner(self, indexer_id) -> bool:
        """
        Returns true if a cached banner exists for the given Indexer ID
        """
        filename = self.banner_path(indexer_id)
        logger.debug(_(f"Checking if file {filename} exists"))
        return filename.exists()

    def has_fanart(self, indexer_id) -> bool:
        """
        Returns true if a cached fanart exists for the given Indexer ID
        """
        filename = self.fanart_path(indexer_id)
        logger.debug(_(f"Checking if file {filename} exists"))
        return filename.exists()

    def has_poster_thumb(self, indexer_id) -> bool:
        """
        Returns true if a cached poster thumbnail exists for the given Indexer ID
        """
        filename = self.poster_thumb_path(indexer_id)
        logger.debug(_(f"Checking if file {filename} exists"))
        return filename.exists()

    def has_banner_thumb(self, indexer_id) -> bool:
        """
        Returns true if a cached banner exists for the given Indexer ID
        """
        filename = self.banner_thumb_path(indexer_id)
        logger.debug(_(f"Checking if file {filename} exists"))
        return filename.exists()

    def image_url(self, indexer_id, which):
        path = getattr(self, which + "_path")(indexer_id)
        if path.exists():
            return (PosixPath("cache") / path.relative_to(settings.CACHE_DIR)).as_posix()
        if which == "fanart" and settings.SICKCHILL_BACKGROUND:
            return "ui/sickchill_background"

        return ("images/poster.png", "images/banner.png")["banner" in which]

    def which_type(self, path):
        """
        Analyzes the image provided and attempts to determine whether it is a poster or banner.

        :param path: full path to the image
        :return: BANNER, POSTER if it concluded one or the other, or None if the image was neither (or didn't exist)
        """

        if not path.exists():
            logger.warning(_(f"Couldn't check the type of {path} cause it doesn't exist"))
            return None

        width, height = imagesize.get(path)

        if not (width and height):
            logger.debug(_(f"Unable to get metadata from {path}, not using your existing image"))
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
            logger.warning(_(f"Image has size ratio of {img_ratio}, unknown type"))
            return None

    @staticmethod
    def image_data(path):
        """
        :return: The content of the desired media file
        """

        if path.exists():
            with open(path, "rb") as content:
                return content.read()

        return None

    @staticmethod
    def content_type(path):
        """
        :return: The mime type of the current media
        """

        if path.exists():
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
            logger.exception(_(f"Invalid cache image type: {img_type}"))
            return False

        # make sure the cache folder exists before we try copying to it
        if not self._cache_dir().is_dir():
            logger.info(_(f"Image cache dir didn't exist, creating it at {self._cache_dir()}"))
            self._cache_dir().mkdir(parents=True, exist_ok=True)

        if not self._thumbnails_dir().is_dir():
            logger.info(_(f"Thumbnails cache dir didn't exist, creating it at {self._thumbnails_dir()}"))
            self._thumbnails_dir().mkdir(parents=True, exist_ok=True)

        logger.info(_(f"Copying from {image_path} to {dest_path}"))
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
            logger.exception(_(f"Invalid cache image type: {img_type}"))
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

        logger.debug(_(f"Checking if we need any cache images for show {show_obj.indexerid}"))

        # check if the images are already cached or not
        need_images = {
            self.POSTER: not self.has_poster(show_obj.indexerid),
            self.BANNER: not self.has_banner(show_obj.indexerid),
            self.POSTER_THUMB: not self.has_poster_thumb(show_obj.indexerid),
            self.BANNER_THUMB: not self.has_banner_thumb(show_obj.indexerid),
            self.FANART: not self.has_fanart(show_obj.indexerid),
        }

        if not any(need_images.values()):
            logger.debug(_("No new cache images needed, not retrieving new ones"))
            return

        # check the show dir for poster or banner images and use them
        if need_images[self.POSTER] or need_images[self.BANNER] or need_images[self.FANART]:
            try:
                for cur_provider in settings.metadata_provider_dict.values():
                    logger.debug(_(f"[{show_obj.indexerid}] Checking if we can use images from {cur_provider.name} metadata"))

                    for method in (cur_provider.get_poster_path, cur_provider.get_banner_path, cur_provider.get_fanart_path):
                        current_path = method(show_obj)
                        if current_path.exists():
                            cur_filename = current_path.absolute()
                            cur_file_type = self.which_type(cur_filename)

                            if cur_file_type not in self.image_str:
                                logger.warning(_(f"Unable to retrieve image type, not using the image from {cur_filename}"))
                                continue

                            file_type_str = self.image_str[cur_file_type]
                            file_type_needed = need_images[cur_file_type]

                            logger.debug(
                                _(f"[{show_obj.indexerid}] Checking if {cur_filename} ({file_type_str}) needs cached: {file_type_needed}")
                            )

                            if cur_file_type in need_images and need_images[cur_file_type]:
                                logger.debug(
                                    _(f"[{show_obj.indexerid}] Found a {file_type_str} in the show dir that doesn't exist in the cache, caching it")
                                )
                                need_images[cur_file_type] = self._cache_image_from_file(cur_filename, cur_file_type, show_obj.indexerid)

            except ShowDirectoryNotFoundException:
                logger.debug(_(f"[{show_obj.indexerid}] Unable to search for images in show dir because it doesn't exist"))

        # download from indexer for missing ones
        for cur_image_type in need_images:
            logger.debug(_(f"[{show_obj.indexerid}] Seeing if we still need a {self.image_str[cur_image_type]}: {need_images[cur_image_type]}"))
            if cur_image_type in need_images and need_images[cur_image_type]:
                self._cache_image_from_indexer(show_obj, cur_image_type)

        logger.info(_("Done cache check"))
