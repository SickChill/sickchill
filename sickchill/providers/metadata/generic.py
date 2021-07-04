import os
import re
from typing import Union
from xml.etree import ElementTree

import fanart
import tmdbsimple
from fanart.core import Request as fanartRequest

import sickchill
from sickchill import logger, settings
from sickchill.helper.common import replace_extension, try_int
from sickchill.oldbeard import helpers

from . import helpers as metadata_helpers


class GenericMetadata(object):
    """
    Base class for all metadata providers. Default behavior is meant to mostly
    follow KODI 12+ metadata standards. Has support for:
    - show metadata file
    - episode metadata file
    - episode thumbnail
    - show fanart
    - show poster
    - show banner
    - season thumbnails (poster)
    - season thumbnails (banner)
    - season all poster
    - season all banner
    """

    def __init__(
        self,
        show_metadata=False,
        episode_metadata=False,
        fanart=False,
        poster=False,
        banner=False,
        episode_thumbnails=False,
        season_posters=False,
        season_banners=False,
        season_all_poster=False,
        season_all_banner=False,
    ):

        self.name = "Generic"

        self._ep_nfo_extension = "nfo"
        self._show_metadata_filename = "tvshow.nfo"

        self.fanart_name = "fanart.jpg"
        self.poster_name = "poster.jpg"
        self.banner_name = "banner.jpg"

        self.season_all_poster_name = "season-all-poster.jpg"
        self.season_all_banner_name = "season-all-banner.jpg"

        self.show_metadata = show_metadata
        self.episode_metadata = episode_metadata
        self.fanart = fanart
        self.poster = poster
        self.banner = banner
        self.episode_thumbnails = episode_thumbnails
        self.season_posters = season_posters
        self.season_banners = season_banners
        self.season_all_poster = season_all_poster
        self.season_all_banner = season_all_banner

    def get_config(self):
        config_list = [
            self.show_metadata,
            self.episode_metadata,
            self.fanart,
            self.poster,
            self.banner,
            self.episode_thumbnails,
            self.season_posters,
            self.season_banners,
            self.season_all_poster,
            self.season_all_banner,
        ]
        return "|".join([str(int(x)) for x in config_list])

    def get_id(self):
        return GenericMetadata.makeID(self.name)

    @staticmethod
    def makeID(name):
        name_id = re.sub(r"[+]", "plus", name)
        name_id = re.sub(r"[^\w\d_]", "_", name_id).lower()
        return name_id

    def set_config(self, config_string):
        config_list = [bool(int(x)) for x in config_string.split("|")]
        self.show_metadata = config_list[0]
        self.episode_metadata = config_list[1]
        self.fanart = config_list[2]
        self.poster = config_list[3]
        self.banner = config_list[4]
        self.episode_thumbnails = config_list[5]
        self.season_posters = config_list[6]
        self.season_banners = config_list[7]
        self.season_all_poster = config_list[8]
        self.season_all_banner = config_list[9]

    @staticmethod
    def _check_exists(location):
        if location:
            result = os.path.isfile(location)
            logger.debug("Checking if " + location + " exists: " + str(result))
            return result
        return False

    def _has_show_metadata(self, show_obj):
        return self._check_exists(self.get_show_file_path(show_obj))

    def _has_episode_metadata(self, ep_obj):
        return self._check_exists(self.get_episode_file_path(ep_obj))

    def _has_fanart(self, show_obj):
        return self._check_exists(self.get_fanart_path(show_obj))

    def _has_poster(self, show_obj):
        return self._check_exists(self.get_poster_path(show_obj))

    def _has_banner(self, show_obj):
        return self._check_exists(self.get_banner_path(show_obj))

    def _has_episode_thumb(self, ep_obj):
        return self._check_exists(self.get_episode_thumb_path(ep_obj))

    def _has_season_poster(self, show_obj, season):
        return self._check_exists(self.get_season_poster_path(show_obj, season))

    def _has_season_banner(self, show_obj, season):
        return self._check_exists(self.get_season_banner_path(show_obj, season))

    def _has_season_all_poster(self, show_obj):
        return self._check_exists(self.get_season_all_poster_path(show_obj))

    def _has_season_all_banner(self, show_obj):
        return self._check_exists(self.get_season_all_banner_path(show_obj))

    def get_show_file_path(self, show_obj):
        return os.path.join(show_obj.location, self._show_metadata_filename)

    def get_episode_file_path(self, ep_obj):
        return replace_extension(ep_obj.location, self._ep_nfo_extension)

    def get_fanart_path(self, show_obj):
        return os.path.join(show_obj.location, self.fanart_name)

    def get_poster_path(self, show_obj):
        return os.path.join(show_obj.location, self.poster_name)

    def get_banner_path(self, show_obj):
        return os.path.join(show_obj.location, self.banner_name)

    @staticmethod
    def get_episode_thumb_path(ep_obj):
        """
        Returns the path where the episode thumbnail should be stored.
        ep_obj: a TVEpisode instance for which to create the thumbnail
        """
        if os.path.isfile(ep_obj.location):

            tbn_filename = ep_obj.location.rpartition(".")

            if tbn_filename[0] == "":
                tbn_filename = ep_obj.location + "-thumb.jpg"
            else:
                tbn_filename = tbn_filename[0] + "-thumb.jpg"
        else:
            return None

        return tbn_filename

    @staticmethod
    def get_season_poster_path(show_obj, season):
        """
        Returns the full path to the file for a given season poster.

        show_obj: a TVShow instance for which to generate the path
        season: a season number to be used for the path. Note that season 0
                means specials.
        """

        # Our specials thumbnail is, well, special
        if season == 0:
            season_poster_filename = "season-specials"
        else:
            season_poster_filename = "season" + str(season).zfill(2)

        return os.path.join(show_obj.location, season_poster_filename + "-poster.jpg")

    @staticmethod
    def get_season_banner_path(show_obj, season):
        """
        Returns the full path to the file for a given season banner.

        show_obj: a TVShow instance for which to generate the path
        season: a season number to be used for the path. Note that season 0
                means specials.
        """

        # Our specials thumbnail is, well, special
        if season == 0:
            season_banner_filename = "season-specials"
        else:
            season_banner_filename = "season" + str(season).zfill(2)

        return os.path.join(show_obj.location, season_banner_filename + "-banner.jpg")

    def get_season_all_poster_path(self, show_obj):
        return os.path.join(show_obj.location, self.season_all_poster_name)

    def get_season_all_banner_path(self, show_obj):
        return os.path.join(show_obj.location, self.season_all_banner_name)

    def _show_data(self, show_obj) -> Union[ElementTree.ElementTree, None]:
        """
        This should be overridden by the implementing class. It should
        provide the content of the show metadata file.
        """
        return None

    def _ep_data(self, ep_obj) -> Union[ElementTree.ElementTree, None]:
        """
        This should be overridden by the implementing class. It should
        provide the content of the episode metadata file.
        """
        return None

    def create_show_metadata(self, show_obj):
        if self.show_metadata and show_obj and not self._has_show_metadata(show_obj):
            logger.debug("Metadata provider " + self.name + " creating show metadata for " + show_obj.name)
            return self.write_show_file(show_obj)
        return False

    def update_show_indexer_metadata(self, show_obj):
        if self.show_metadata and show_obj and self._has_show_metadata(show_obj):
            logger.debug("Metadata provider " + self.name + " updating show indexer info metadata file for " + show_obj.name)

            nfo_file_path = self.get_show_file_path(show_obj)

            try:
                with open(nfo_file_path, "rb") as xmlFileObj:
                    showXML = ElementTree.ElementTree(file=xmlFileObj)

                indexerid = showXML.find("id")

                root = showXML.getroot()
                if indexerid is not None:
                    if indexerid.text == str(show_obj.indexerid):
                        return True
                    indexerid.text = str(show_obj.indexerid)
                else:
                    ElementTree.SubElement(root, "id").text = str(show_obj.indexerid)

                # Make it purdy
                helpers.indentXML(root)

                showXML.write(nfo_file_path, encoding="UTF-8")
                helpers.chmodAsParent(nfo_file_path)

                return True
            except IOError as e:
                logger.error("Unable to write file to " + nfo_file_path + " - are you sure the folder is writable? " + str(e))

    def create_episode_metadata(self, ep_obj):
        if self.episode_metadata and ep_obj and not self._has_episode_metadata(ep_obj):
            logger.debug("Metadata provider " + self.name + " creating episode metadata for " + ep_obj.pretty_name)
            return self.write_ep_file(ep_obj)
        return False

    def update_episode_metadata(self, ep_obj):
        if self.episode_metadata and ep_obj and self._has_episode_metadata(ep_obj):
            logger.debug("Metadata provider " + self.name + " updating episode indexer info metadata file for " + ep_obj.pretty_name)
            nfo_file_path = self.get_episode_file_path(ep_obj)

            attribute_map = {
                "title": "name",
                "aired": "airdate",
                "season": "season",
                "episode": "episode",
                "showtitle": "show.name",
                "runtime": "show.runtime",
                "plot": "description",
            }
            try:
                with open(nfo_file_path, "rb") as xmlFileObj:
                    episodeXML = ElementTree.ElementTree(file=xmlFileObj)

                changed = False
                for attribute in attribute_map:
                    try:
                        if not hasattr(ep_obj, attribute_map[attribute]):
                            continue

                        node = episodeXML.find(attribute)
                        if node is None or node.text == str(getattr(ep_obj, attribute_map[attribute])):
                            continue

                        node.text = str(getattr(ep_obj, attribute_map[attribute]))
                        changed = True
                    except AttributeError:
                        pass

                if not changed:
                    return True

                root = episodeXML.getroot()

                # Make it purdy
                helpers.indentXML(root)

                episodeXML.write(nfo_file_path, encoding="UTF-8")
                helpers.chmodAsParent(nfo_file_path)

                return True
            except IOError as error:
                logger.warning("Unable to write file to {} - are you sure the folder is writable? {}".format(nfo_file_path, str(error)))
            except ElementTree.ParseError as error:
                logger.warning("Error parsing existing nfo file at {} - {}".format(nfo_file_path, str(error)))

    def create_fanart(self, show_obj):
        if self.fanart and show_obj and not self._has_fanart(show_obj):
            logger.debug("Metadata provider " + self.name + " creating fanart for " + show_obj.name)
            return self.save_fanart(show_obj)
        return False

    def create_poster(self, show_obj):
        if self.poster and show_obj and not self._has_poster(show_obj):
            logger.debug("Metadata provider " + self.name + " creating poster for " + show_obj.name)
            return self.save_poster(show_obj)
        return False

    def create_banner(self, show_obj):
        if self.banner and show_obj and not self._has_banner(show_obj):
            logger.debug("Metadata provider " + self.name + " creating banner for " + show_obj.name)
            return self.save_banner(show_obj)
        return False

    def create_episode_thumb(self, ep_obj):
        if self.episode_thumbnails and ep_obj and not self._has_episode_thumb(ep_obj):
            logger.debug("Metadata provider " + self.name + " creating episode thumbnail for " + ep_obj.pretty_name)
            return self.save_thumbnail(ep_obj)
        return False

    def create_season_posters(self, show_obj):
        if self.season_posters and show_obj:
            result = []
            for season in show_obj.episodes:
                if not self._has_season_poster(show_obj, season):
                    logger.debug("Metadata provider " + self.name + " creating season posters for " + show_obj.name)
                    result.extend([self.save_season_poster(show_obj, season)])
            return all(result)
        return False

    def create_season_banners(self, show_obj):
        if self.season_banners and show_obj:
            result = []
            logger.debug("Metadata provider " + self.name + " creating season banners for " + show_obj.name)
            for season in show_obj.episodes:
                if not self._has_season_banner(show_obj, season):
                    result.extend([self.save_season_banner(show_obj, season)])
            return all(result)
        return False

    def create_season_all_poster(self, show_obj):
        if self.season_all_poster and show_obj and not self._has_season_all_poster(show_obj):
            logger.debug("Metadata provider " + self.name + " creating season all poster for " + show_obj.name)
            return self.save_season_all_poster(show_obj)
        return False

    def create_season_all_banner(self, show_obj):
        if self.season_all_banner and show_obj and not self._has_season_all_banner(show_obj):
            logger.debug("Metadata provider " + self.name + " creating season all banner for " + show_obj.name)
            return self.save_season_all_banner(show_obj)
        return False

    def write_show_file(self, show_obj):
        """
        Generates and writes show_obj's metadata under the given path to the
        filename given by get_show_file_path()

        show_obj: TVShow object for which to create the metadata

        path: An absolute or relative path where we should put the file. Note that
                the file name will be the default show_filename.

        Note that this method expects that _show_data will return an ElementTree
        object. If your _show_data returns data in another format yo'll need to
        override this method.
        """

        data = self._show_data(show_obj)

        if not data:
            return False

        nfo_file_path = self.get_show_file_path(show_obj)
        nfo_file_dir = os.path.dirname(nfo_file_path)

        try:
            if not os.path.isdir(nfo_file_dir):
                logger.debug("Metadata dir didn't exist, creating it at " + nfo_file_dir)
                os.makedirs(nfo_file_dir)
                helpers.chmodAsParent(nfo_file_dir)

            logger.debug("Writing show nfo file to " + nfo_file_path)

            nfo_file = open(nfo_file_path, "wb")
            data.write(nfo_file, encoding="UTF-8")
            nfo_file.close()
            helpers.chmodAsParent(nfo_file_path)
        except IOError as e:
            logger.error("Unable to write file to " + nfo_file_path + " - are you sure the folder is writable? " + str(e))
            return False

        return True

    def write_ep_file(self, ep_obj):
        """
        Generates and writes ep_obj's metadata under the given path with the
        given filename root. Uses the episode's name with the extension in
        _ep_nfo_extension.

        ep_obj: TVEpisode object for which to create the metadata

        filename_path: The file name to use for this metadata. Note that the extension
                will be automatically added based on _ep_nfo_extension. This should
                include an absolute path.

        Note that this method expects that _ep_data will return an ElementTree
        object. If your _ep_data returns data in another format yo'll need to
        override this method.
        """

        data = self._ep_data(ep_obj)
        if not data:
            return False

        # def print_data(d):
        #     for child in d.getroot():
        #         print(str(child.tag), str(child.text))

        # print_data(data)

        nfo_file_path = self.get_episode_file_path(ep_obj)
        nfo_file_dir = os.path.dirname(nfo_file_path)

        try:
            if not os.path.isdir(nfo_file_dir):
                logger.debug("Metadata dir didn't exist, creating it at " + nfo_file_dir)
                os.makedirs(nfo_file_dir)
                helpers.chmodAsParent(nfo_file_dir)

            logger.debug("Writing episode nfo file to " + nfo_file_path)
            nfo_file = open(nfo_file_path, "wb")
            data.write(nfo_file, encoding="UTF-8")
            nfo_file.close()
            helpers.chmodAsParent(nfo_file_path)
        except IOError as e:
            logger.error("Unable to write file to " + nfo_file_path + " - are you sure the folder is writable? " + str(e))
            return False

        return True

    def save_thumbnail(self, ep_obj):
        """
        Retrieves a thumbnail and saves it to the correct spot. This method should not need to
        be overridden by implementing classes, changing get_episode_thumb_path and
        _get_episode_thumb_url should suffice.

        ep_obj: a TVEpisode object for which to generate a thumbnail
        """

        thumb_url = sickchill.indexer.episode_image_url(ep_obj)
        if not thumb_url:
            logger.debug("No thumb is available for this episode, not creating a thumb")
            return False

        file_path = self.get_episode_thumb_path(ep_obj)
        if not file_path:
            logger.debug("Unable to find a file path to use for this thumbnail, not generating it")
            return False

        thumb_data = metadata_helpers.getShowImage(thumb_url)
        if not thumb_data:
            logger.debug("No thumb is available for this episode, not creating a thumb")
            return False

        result = self._write_image(thumb_data, file_path)

        if not result:
            return False

        for cur_ep in [ep_obj] + ep_obj.relatedEps:
            cur_ep.hastbn = True

        return True

    def save_fanart(self, show_obj):
        """
        Downloads a fanart image and saves it to the filename specified by fanart_name
        inside the show's root folder.

        show_obj: a TVShow object for which to download fanart
        """

        # use the default fanart name
        fanart_path = self.get_fanart_path(show_obj)
        if not fanart_path:
            logger.debug("Fanart path for show {} came back blank, skipping this image".format(show_obj.name))
            return False

        fanart_url = sickchill.indexer.series_fanart_url(show_obj)
        if not fanart_url:
            fanart_url = self._retrieve_show_image_urls_from_fanart(show_obj, "fanart")
            if not fanart_url:
                logger.debug("Fanart url not found for show {}, skipping this image".format(show_obj.name))
                return False

        fanart_data = metadata_helpers.getShowImage(fanart_url)
        if not fanart_data:
            logger.debug("No fanart image was retrieved, unable to write fanart")
            return False

        return self._write_image(fanart_data, fanart_path)

    def save_poster(self, show_obj):
        """
        Downloads a poster image and saves it to the filename specified by poster_name
        inside the show's root folder.

        show_obj: a TVShow object for which to download a poster
        """

        # use the default poster name
        poster_path = self.get_poster_path(show_obj)
        if not poster_path:
            logger.debug("Banner path for show {} came back blank, skipping this image".format(show_obj.name))
            return False

        poster_url = sickchill.indexer.series_poster_url(show_obj)
        if not poster_url:
            poster_url = self._retrieve_show_image_urls_from_fanart(show_obj, "poster")
            if not poster_url:
                logger.debug("Poster url not found for show {}, skipping this image".format(show_obj.name))
                return False

        poster_data = metadata_helpers.getShowImage(poster_url)
        if not poster_data:
            logger.debug("No show poster image was retrieved, unable to write poster")
            return False

        return self._write_image(poster_data, poster_path)

    def save_banner(self, show_obj):
        """
        Downloads a banner image and saves it to the filename specified by banner_name
        inside the show's root folder.

        show_obj: a TVShow object for which to download a banner
        """

        banner_path = self.get_banner_path(show_obj)
        if not banner_path:
            logger.debug("Banner path for show {} came back blank, skipping this image".format(show_obj.name))
            return False

        banner_url = sickchill.indexer.series_banner_url(show_obj)
        if not banner_url:
            banner_url = self._retrieve_show_image_urls_from_fanart(show_obj, "banner")
            if not banner_url:
                logger.debug("Banner url not found for show {}, skipping this image".format(show_obj.name))
                return False

        banner_data = metadata_helpers.getShowImage(banner_url)
        if not banner_data:
            logger.debug("No show banner image was retrieved, unable to write banner")
            return False

        return self._write_image(banner_data, banner_path)

    def save_season_poster(self, show_obj, season):
        """
        Saves a specific season poster to disk for the given show.

        show_obj: a TVShow object for which to save the season thumbs
        """

        season_poster_url = sickchill.indexer.season_poster_url(show_obj, season)
        if not season_poster_url:
            season_poster_url = self._retrieve_show_image_urls_from_fanart(show_obj, "season_poster", season=season)
            if not season_poster_url:
                logger.debug("Season poster url not found for season {}, skipping this season".format(season))
                return False

        season_poster_file_path = self.get_season_poster_path(show_obj, season)
        if not season_poster_file_path:
            logger.debug("Path for season {} came back blank, skipping this season".format(season))
            return False

        image_data = metadata_helpers.getShowImage(season_poster_url)
        if not image_data:
            logger.debug("No season poster data available, skipping this season")
            return False

        return self._write_image(image_data, season_poster_file_path)

    def save_season_banner(self, show_obj, season):
        """
        Saves the first season banner for a season to disk for the given show.

        show_obj: a TVShow object for which to save the season thumbs
        """
        season_banner_url = sickchill.indexer.season_banner_url(show_obj, season)
        if not season_banner_url:
            season_banner_url = self._retrieve_show_image_urls_from_fanart(show_obj, "season_banner", season=season)
            if not season_banner_url:
                logger.debug("Url for season banner {} came back blank, skipping this season".format(season))
                return False

        season_banner_file_path = self.get_season_banner_path(show_obj, season)
        if not season_banner_file_path:
            logger.debug("Path for season {} came back blank, skipping this season".format(season))
            return False

        image_data = metadata_helpers.getShowImage(season_banner_url)
        if not image_data:
            logger.debug("No season banner data available, skipping this season")
            return False

        return self._write_image(image_data, season_banner_file_path)

    def save_season_all_poster(self, show_obj):
        poster_url = sickchill.indexer.series_poster_url(show_obj)
        if not poster_url:
            poster_url = self._retrieve_show_image_urls_from_fanart(show_obj, "season_poster", season=0)
            if not poster_url:
                logger.debug("Url for season all poster came back blank, skipping this season")
                return False

        season_poster_file_path = self.get_season_all_poster_path(show_obj)
        if not season_poster_file_path:
            logger.debug("Path for season all poster came back blank, skipping this season")
            return False

        image_data = metadata_helpers.getShowImage(poster_url)
        if not image_data:
            logger.debug("No season all poster data available, skipping this season")
            return False

        return self._write_image(image_data, season_poster_file_path)

    def save_season_all_banner(self, show_obj):
        banner_url = sickchill.indexer.series_banner_url(show_obj)
        if not banner_url:
            banner_url = self._retrieve_show_image_urls_from_fanart(show_obj, "season_banner", season=0)
            if not banner_url:
                logger.debug("Url for season all banner came back blank, skipping this season")
                return False

        season_banner_file_path = self.get_season_all_banner_path(show_obj)
        if not season_banner_file_path:
            logger.debug("Path for season all banner came back blank, skipping this season")
            return False

        image_data = metadata_helpers.getShowImage(banner_url)
        if not image_data:
            logger.debug("No season all banner data available, skipping this season")
            return False

        return self._write_image(image_data, season_banner_file_path)

    @staticmethod
    def _write_image(image_data, image_path, overwrite=False):
        """
        Saves the data in image_data to the location image_path. Returns True/False
        to represent success or failure.

        image_data: binary image data to write to file
        image_path: file location to save the image to
        """

        # don't bother overwriting it
        if not overwrite and os.path.isfile(image_path):
            logger.debug("Image already exists, not downloading")
            return False

        image_dir = os.path.dirname(image_path)

        if not image_data:
            logger.debug("Unable to retrieve image to save in {0}, skipping".format(image_path))
            return False

        try:
            if not os.path.isdir(image_dir):
                logger.debug("Metadata dir didn't exist, creating it at " + image_dir)
                os.makedirs(image_dir)
                helpers.chmodAsParent(image_dir)

            outFile = open(image_path, "wb")
            outFile.write(image_data)
            outFile.close()
            helpers.chmodAsParent(image_path)
        except IOError as e:
            logger.error("Unable to write image to " + image_path + " - are you sure the show folder is writable? " + str(e))
            return False

        return True

    def retrieveShowMetadata(self, folder):
        """
        Used only when mass adding Existing Shows, using previously generated Show metadata to reduce the need to query TVDB.
        """

        empty_return = (None, None, None)

        metadata_path = os.path.join(folder, self._show_metadata_filename)

        if not os.path.isdir(folder) or not os.path.isfile(metadata_path):
            logger.debug(_("Can't load the metadata file from {0}, it doesn't exist").format(metadata_path))
            return empty_return

        logger.debug(_("Loading show info from metadata file in {0}").format(metadata_path))

        def read_xml():
            with open(metadata_path, "rb") as __xml_file:
                try:
                    __show_xml = ElementTree.ElementTree(file=__xml_file)
                except (ElementTree.ParseError, IOError):
                    __show_xml = None
            return __show_xml

        def fix_xml():
            logger.info(
                _(
                    "There was an error loading {0}, trying to repair it by fixing & symbols. If it still has problems, please check the file " "manually"
                ).format(metadata_path)
            )
            with open(metadata_path) as __xml_file:
                output = __xml_file.read()

            regex = re.compile(r"&(?!amp;|lt;|gt;)")
            output = regex.sub("&amp;", output)
            with open(metadata_path, "wb") as __xml_file:
                __xml_file.write(output)

            return True

        try:
            show_xml = read_xml() or fix_xml() and read_xml()
            if not show_xml:
                logger.debug(_("Can't load the metadata file from {0}, error reading file").format(metadata_path))
                return empty_return

            if not (show_xml.findtext("title") or (show_xml.findtext("tvdbid") and show_xml.findtext("id"))):
                logger.info(
                    _("Invalid info in tvshow.nfo (missing name or id): {0} {1} {2}").format(
                        show_xml.findtext("title"), show_xml.findtext("tvdbid"), show_xml.findtext("id")
                    )
                )
                return empty_return

            name = show_xml.findtext("title")

            indexer_id_text = show_xml.findtext("tvdbid") or show_xml.findtext("id")
            if indexer_id_text:
                indexer_id = try_int(indexer_id_text, None)
                if indexer_id is None or indexer_id < 1:
                    logger.debug(_("Invalid Indexer ID ({0}), not using metadata file").format(str(indexer_id)))
                    return empty_return
            else:
                logger.debug(_("Empty <id> or <tvdbid> field in NFO, unable to find a ID, not using metadata file"))
                return empty_return

            indexer = 1
            epg_url_text = show_xml.findtext("episodeguide/url")
            if epg_url_text:
                epg_url = epg_url_text.lower()
                if str(indexer_id) in epg_url and "tvrage" in epg_url:
                    if sickchill.indexer.TVRAGE not in sickchill.indexer:
                        logger.warning(_("Invalid Indexer ID ({0}), not using metadata file because it has TVRage info").format(indexer_id))
                        return empty_return
                    return indexer_id, show_xml.findtext("title"), sickchill.indexer.TVRAGE
                if str(indexer_id) in epg_url and "tvdb" in epg_url:
                    return indexer_id, show_xml.findtext("title"), sickchill.indexer.TVDB

        except Exception as e:
            logger.warning(_("There was an error parsing your existing metadata file: '{0}' error: {1}").format(metadata_path, str(e)))
            return empty_return

        return indexer_id, name, indexer

    @staticmethod
    def _retrieve_show_image_urls_from_tmdb(show, img_type, multiple=False):
        types = {"poster": "posters", "banner": None, "fanart": "backdrops", "poster_thumb": "posters", "banner_thumb": None}

        if not types[img_type]:
            return [] if multiple else ""

        # get TMDB configuration info
        tmdbsimple.API_KEY = settings.TMDB_API_KEY
        config = tmdbsimple.Configuration()
        response = config.info()
        base_url = response["images"]["base_url"]
        sizes = response["images"]["poster_sizes"]

        def size_str_to_int(x):
            return float("inf") if x == "original" else int(x[1:])

        max_size = max(sizes, key=size_str_to_int)

        try:
            results = []
            find = tmdbsimple.Find(show.indexerid)
            found = find.info(external_source="tvdb_id")
            if found["tv_results"]:
                tmdb_show = tmdbsimple.TV(found["tv_results"][0]["id"])
                images = tmdb_show.images()
                if types[img_type] in images:
                    for result in images[types[img_type]]:
                        results.append("{0}{1}{2}".format(base_url, max_size, result["file_path"]))
                        if not multiple:
                            return results[0]
                    return results
        except Exception as error:
            logger.debug(error)

        logger.info("Could not find any " + img_type + " images on TMDB for " + show.name)

    @staticmethod
    def _retrieve_show_image_urls_from_fanart(show, img_type, thumb=False, season=None, multiple=False):
        types = {
            "poster": fanart.TYPE.TV.POSTER,
            "banner": fanart.TYPE.TV.BANNER,
            "poster_thumb": fanart.TYPE.TV.POSTER,
            "banner_thumb": fanart.TYPE.TV.BANNER,
            "fanart": fanart.TYPE.TV.BACKGROUND,
            "season_poster": fanart.TYPE.TV.SEASONPOSTER,
            "season_banner": fanart.TYPE.TV.SEASONBANNER,
        }

        try:
            if img_type in types:
                request = fanartRequest(
                    apikey=settings.FANART_API_KEY,
                    id=show.indexerid,
                    ws=fanart.WS.TV,
                    type=types[img_type],
                    sort=fanart.SORT.POPULAR,
                    limit=(fanart.LIMIT.ONE, fanart.LIMIT.ALL)[season is not None],
                )

                resp = request.response()
                results = resp[types[img_type]]
                if season:
                    results = [x for x in results if try_int(x["season"], default_value=None) == season]

                def _to_preview_url(url):
                    return re.sub("/fanart/", "/preview/", url)

                if multiple:
                    urls = [result["url"] for result in results]
                    if thumb:
                        urls = [_to_preview_url(url) for url in urls]
                    return urls
                else:
                    url = results[0]["url"]
                    if thumb:
                        url = _to_preview_url(url)
                    return url
        except Exception as error:
            logger.debug(error)

        logger.info("Could not find any " + img_type + " images on Fanart.tv for " + show.name)
