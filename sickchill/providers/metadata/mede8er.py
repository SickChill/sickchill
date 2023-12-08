import datetime
import os
from xml.etree import ElementTree

import sickchill
from sickchill.helper.common import dateFormat, replace_extension
from sickchill.oldbeard import helpers

from ... import logger
from . import mediabrowser


class Mede8erMetadata(mediabrowser.MediaBrowserMetadata):
    """
    Metadata generation class for Mede8er based on the MediaBrowser.

    The following file structure is used:

    show_root/series.xml                    (show metadata)
    show_root/folder.jpg                    (poster)
    show_root/fanart.jpg                    (fanart)
    show_root/Season ##/folder.jpg          (season thumb)
    show_root/Season ##/filename.ext        (*)
    show_root/Season ##/filename.xml        (episode metadata)
    show_root/Season ##/filename.jpg        (episode thumb)
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
        mediabrowser.MediaBrowserMetadata.__init__(
            self,
            show_metadata,
            episode_metadata,
            fanart,
            poster,
            banner,
            episode_thumbnails,
            season_posters,
            season_banners,
            season_all_poster,
            season_all_banner,
        )

        self.name = "Mede8er"

        self.fanart_name = "fanart.jpg"

        # web-ui metadata template
        # self.eg_show_metadata = "series.xml"
        self.eg_episode_metadata = "Season##\\<i>filename</i>.xml"
        self.eg_fanart = "fanart.jpg"
        # self.eg_poster = "folder.jpg"
        # self.eg_banner = "banner.jpg"
        self.eg_episode_thumbnails = "Season##\\<i>filename</i>.jpg"
        # self.eg_season_posters = "Season##\\folder.jpg"
        # self.eg_season_banners = "Season##\\banner.jpg"
        # self.eg_season_all_poster = "<i>not supported</i>"
        # self.eg_season_all_banner = "<i>not supported</i>"

    def get_episode_file_path(self, episode_object):
        return replace_extension(episode_object.location, self._ep_nfo_extension)

    @staticmethod
    def get_episode_thumb_path(episode_object):
        return replace_extension(episode_object.location, "jpg")

    def _show_data(self, show_obj):
        """
        Creates an elementTree XML structure for a MediaBrowser-style series.xml
        returns the resulting data object.

        show_obj: a TVShow instance to create the NFO for
        """
        root_node = ElementTree.Element("details")
        tv_node = ElementTree.SubElement(root_node, "movie")
        tv_node.attrib["isExtra"] = "false"
        tv_node.attrib["isSet"] = "false"
        tv_node.attrib["isTV"] = "true"

        indexer_show = sickchill.indexer.series(show_obj)
        if not indexer_show:
            logger.info("Unable to find show with id {} on {}, skipping it".format(show_obj.indexerid, show_obj.idxr.name))
            return False

        # check for title and id
        if not (getattr(indexer_show, "seriesName", None) and getattr(indexer_show, "id", None)):
            logger.info("Incomplete info for show with id {} on {}, skipping it".format(show_obj.indexerid, show_obj.idxr.name))
            return False

        title_element = ElementTree.SubElement(tv_node, "title")
        title_element.text = indexer_show.seriesName

        if getattr(indexer_show, "genre", None):
            genres_element = ElementTree.SubElement(tv_node, "genres")
            for genre in indexer_show.genre:
                if genre and genre.strip():
                    genre_element = ElementTree.SubElement(genres_element, "Genre")
                    genre_element.text = genre.strip()

        if getattr(indexer_show, "firstAired", None):
            premiered_element = ElementTree.SubElement(tv_node, "premiered")
            premiered_element.text = indexer_show.firstAired

        if getattr(indexer_show, "firstAired", None):
            try:
                year_text = str(datetime.datetime.strptime(indexer_show.firstAired, dateFormat).year)
                if year_text:
                    year_element = ElementTree.SubElement(tv_node, "year")
                    year_element.text = year_text
            except Exception:
                pass

        if getattr(indexer_show, "overview", None):
            plot_element = ElementTree.SubElement(tv_node, "plot")
            plot_element.text = indexer_show.overview

        if getattr(indexer_show, "rating", None):
            try:
                rating = int(float(indexer_show.siteRating) * 10)
            except ValueError:
                rating = 0

            if rating:
                rating_element = ElementTree.SubElement(tv_node, "rating")
                rating_element.text = str(rating)

        if getattr(indexer_show, "status", None):
            status_element = ElementTree.SubElement(tv_node, "status")
            status_element.text = indexer_show.status

        if getattr(indexer_show, "contentRating", None):
            mpaa_element = ElementTree.SubElement(tv_node, "mpaa")
            mpaa_element.text = indexer_show.rating

        if getattr(indexer_show, "imdb_id", None):
            id_element = ElementTree.SubElement(tv_node, "id")
            id_element.attrib["moviedb"] = "imdb"
            id_element.text = indexer_show.imdbId

        if getattr(indexer_show, "id", None):
            indexerid_element = ElementTree.SubElement(tv_node, "indexerid")
            indexerid_element.text = str(indexer_show.id)

        if getattr(indexer_show, "runtime", None):
            runtime_element = ElementTree.SubElement(tv_node, "runtime")
            runtime_element.text = indexer_show.runtime

        indexer_show_actors = show_obj.idxr.actors(indexer_show)
        if indexer_show_actors:
            cast_element = ElementTree.SubElement(tv_node, "cast")
            for actor in indexer_show_actors:
                if "name" in actor and actor["name"].strip():
                    actor_element = ElementTree.SubElement(cast_element, "actor")
                    actor_element.text = actor["name"].strip()

        helpers.indentXML(root_node)

        return ElementTree.ElementTree(root_node)

    def _ep_data(self, episode_object):
        """
        Creates an elementTree XML structure for a MediaBrowser style episode.xml
        and returns the resulting data object.

        show_obj: a TVShow instance to create the NFO for
        """

        episodes_to_write = [episode_object] + episode_object.related_episodes

        indexer_show = episode_object.idxr.series_from_episode(episode_object)
        if not indexer_show:
            logger.info("Unable to connect to {} while creating meta files - skipping".format(episode_object.idxr.name))
            return False

        root_node = ElementTree.Element("details")
        movie_element = ElementTree.SubElement(root_node, "movie")

        movie_element.attrib["isExtra"] = "false"
        movie_element.attrib["isSet"] = "false"
        movie_element.attrib["isTV"] = "true"

        # write an MediaBrowser XML containing info for all matching episodes
        for current_episode in episodes_to_write:
            indexer_episode = current_episode.idxr.episode(current_episode)
            if not indexer_episode:
                logger.info(
                    "Metadata writer is unable to find episode {0:d}x{1:d} of {2} on {3}..."
                    "has it been removed? Should I delete from db?".format(
                        current_episode.season, current_episode.episode, current_episode.show.name, episode_object.idxr.name
                    )
                )
                return None

            if current_episode == episode_object:
                # root (or single) episode

                if episode_object.airdate != datetime.date.min and not indexer_episode.get("firstAired"):
                    indexer_episode["firstAired"] = str(episode_object.airdate)

                if not (indexer_episode.get("episodeName") and indexer_episode.get("firstAired")):
                    return None

                episode = movie_element

                if current_episode.name:
                    title_element = ElementTree.SubElement(episode, "title")
                    title_element.text = current_episode.name

                season_element = ElementTree.SubElement(episode, "season")
                season_element.text = str(current_episode.season)

                episode_element = ElementTree.SubElement(episode, "episode")
                episode_element.text = str(current_episode.episode)

                if getattr(indexer_show, "firstAired", None):
                    try:
                        year_text = str(datetime.datetime.strptime(indexer_show.firstAired, dateFormat).year)
                        if year_text:
                            year_element = ElementTree.SubElement(episode, "year")
                            year_element.text = year_text
                    except Exception:
                        pass

                if getattr(indexer_show, "overview", None):
                    plot_element = ElementTree.SubElement(episode, "plot")
                    plot_element.text = indexer_show.overview

                if current_episode.description:
                    episode_plot_element = ElementTree.SubElement(episode, "episodeplot")
                    episode_plot_element.text = current_episode.description

                if getattr(indexer_show, "contentRating", None):
                    mpaa_element = ElementTree.SubElement(episode, "mpaa")
                    mpaa_element.text = indexer_show.rating

                if not episode_object.related_episodes and indexer_episode.get("rating"):
                    try:
                        rating = int((float(indexer_episode.siteRating) * 10))
                    except ValueError:
                        rating = 0

                    if rating:
                        rating_element = ElementTree.SubElement(episode, "rating")
                        rating_element.text = str(rating)

                if indexer_episode.get("directors") and isinstance(indexer_episode["directors"], list):
                    for director in indexer_episode["directors"]:
                        director_element = ElementTree.SubElement(episode, "director")
                        director_element.text = director

                if indexer_episode.get("writers") and isinstance(indexer_episode["writers"], list):
                    for writer in indexer_episode["writers"]:
                        writer_element = ElementTree.SubElement(episode, "credits")
                        writer_element.text = writer

                if indexer_episode.get("guestStars") and isinstance(indexer_episode["guestStars"], list):
                    cast = ElementTree.SubElement(episode, "cast")
                    for actor in indexer_episode["guestStars"]:
                        actor_element = ElementTree.SubElement(cast, "actor")
                        actor_element.text = actor

            else:
                # append data from (if any) related episodes

                if current_episode.name:
                    if not title_element.text:
                        title_element.text = current_episode.name
                    else:
                        title_element.text = title_element.text + ", " + current_episode.name

                if current_episode.description:
                    if not episode_plot_element.text:
                        episode_plot_element.text = current_episode.description
                    else:
                        episode_plot_element.text = episode_plot_element.text + "\r" + current_episode.description

        helpers.indentXML(root_node)
        return ElementTree.ElementTree(root_node)

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

            data.write(nfo_file, encoding="utf-8", xml_declaration=True)
            nfo_file.close()
            helpers.chmodAsParent(nfo_file_path)
        except IOError as error:
            logger.error(f"Unable to write file to {nfo_file_path} - are you sure the folder is writable? {error}")
            return False

        return True

    def write_ep_file(self, episode_object):
        """
        Generates and writes episode_object's metadata under the given path with the
        given filename root. Uses the episode's name with the extension in
        _ep_nfo_extension.

        episode_object: TVEpisode object for which to create the metadata

        filename_path: The file name to use for this metadata. Note that the extension
                will be automatically added based on _ep_nfo_extension. This should
                include an absolute path.

        Note that this method expects that _ep_data will return an ElementTree
        object. If your _ep_data returns data in another format yo'll need to
        override this method.
        """

        data = self._ep_data(episode_object)

        if not data:
            return False

        nfo_file_path = self.get_episode_file_path(episode_object)
        nfo_file_dir = os.path.dirname(nfo_file_path)

        try:
            if not os.path.isdir(nfo_file_dir):
                logger.debug("Metadata dir didn't exist, creating it at " + nfo_file_dir)
                os.makedirs(nfo_file_dir)
                helpers.chmodAsParent(nfo_file_dir)

            logger.debug("Writing episode nfo file to " + nfo_file_path)

            nfo_file = open(nfo_file_path, "wb")

            data.write(nfo_file, encoding="utf-8", xml_declaration=True)
            nfo_file.close()
            helpers.chmodAsParent(nfo_file_path)
        except IOError as error:
            logger.error(f"Unable to write file to {nfo_file_path} - are you sure the folder is writable? {error}")
            return False

        return True


# present a standard "interface" from the module
metadata_class = Mede8erMetadata
