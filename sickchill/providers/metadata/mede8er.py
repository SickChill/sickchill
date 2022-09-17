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

    def get_episode_file_path(self, ep_obj):
        return replace_extension(ep_obj.location, self._ep_nfo_extension)

    @staticmethod
    def get_episode_thumb_path(ep_obj):
        return replace_extension(ep_obj.location, "jpg")

    def _show_data(self, show_obj):
        """
        Creates an elementTree XML structure for a MediaBrowser-style series.xml
        returns the resulting data object.

        show_obj: a TVShow instance to create the NFO for
        """
        rootNode = ElementTree.Element("details")
        tv_node = ElementTree.SubElement(rootNode, "movie")
        tv_node.attrib["isExtra"] = "false"
        tv_node.attrib["isSet"] = "false"
        tv_node.attrib["isTV"] = "true"

        myShow = sickchill.indexer.series(show_obj)
        if not myShow:
            logger.info("Unable to find show with id {} on {}, skipping it".format(show_obj.indexerid, show_obj.idxr.name))
            return False

        # check for title and id
        if not (getattr(myShow, "seriesName", None) and getattr(myShow, "id", None)):
            logger.info("Incomplete info for show with id {} on {}, skipping it".format(show_obj.indexerid, show_obj.idxr.name))
            return False

        SeriesName = ElementTree.SubElement(tv_node, "title")
        SeriesName.text = myShow.seriesName

        if getattr(myShow, "genre", None):
            Genres = ElementTree.SubElement(tv_node, "genres")
            for genre in myShow.genre:
                if genre and genre.strip():
                    cur_genre = ElementTree.SubElement(Genres, "Genre")
                    cur_genre.text = genre.strip()

        if getattr(myShow, "firstAired", None):
            FirstAired = ElementTree.SubElement(tv_node, "premiered")
            FirstAired.text = myShow.firstAired

        if getattr(myShow, "firstAired", None):
            try:
                year_text = str(datetime.datetime.strptime(myShow.firstAired, dateFormat).year)
                if year_text:
                    year = ElementTree.SubElement(tv_node, "year")
                    year.text = year_text
            except Exception:
                pass

        if getattr(myShow, "overview", None):
            plot = ElementTree.SubElement(tv_node, "plot")
            plot.text = myShow.overview

        if getattr(myShow, "rating", None):
            try:
                rating = int(float(myShow.siteRating) * 10)
            except ValueError:
                rating = 0

            if rating:
                Rating = ElementTree.SubElement(tv_node, "rating")
                Rating.text = str(rating)

        if getattr(myShow, "status", None):
            Status = ElementTree.SubElement(tv_node, "status")
            Status.text = myShow.status

        if getattr(myShow, "contentRating", None):
            mpaa = ElementTree.SubElement(tv_node, "mpaa")
            mpaa.text = myShow.rating

        if getattr(myShow, "imdb_id", None):
            imdb_id = ElementTree.SubElement(tv_node, "id")
            imdb_id.attrib["moviedb"] = "imdb"
            imdb_id.text = myShow.imdbId

        if getattr(myShow, "id", None):
            indexerid = ElementTree.SubElement(tv_node, "indexerid")
            indexerid.text = str(myShow.id)

        if getattr(myShow, "runtime", None):
            Runtime = ElementTree.SubElement(tv_node, "runtime")
            Runtime.text = myShow.runtime

        actors = show_obj.idxr.actors(myShow)
        if actors:
            cast = ElementTree.SubElement(tv_node, "cast")
            for actor in actors:
                if "name" in actor and actor["name"].strip():
                    cur_actor = ElementTree.SubElement(cast, "actor")
                    cur_actor.text = actor["name"].strip()

        helpers.indentXML(rootNode)

        data = ElementTree.ElementTree(rootNode)

        return data

    def _ep_data(self, ep_obj):
        """
        Creates an elementTree XML structure for a MediaBrowser style episode.xml
        and returns the resulting data object.

        show_obj: a TVShow instance to create the NFO for
        """

        eps_to_write = [ep_obj] + ep_obj.relatedEps

        myShow = ep_obj.idxr.series_from_episode(ep_obj)
        if not myShow:
            logger.info("Unable to connect to {} while creating meta files - skipping".format(ep_obj.idxr.name))
            return False

        rootNode = ElementTree.Element("details")
        movie = ElementTree.SubElement(rootNode, "movie")

        movie.attrib["isExtra"] = "false"
        movie.attrib["isSet"] = "false"
        movie.attrib["isTV"] = "true"

        # write an MediaBrowser XML containing info for all matching episodes
        for curEpToWrite in eps_to_write:
            myEp = curEpToWrite.idxr.episode(curEpToWrite)
            if not myEp:
                logger.info(
                    "Metadata writer is unable to find episode {0:d}x{1:d} of {2} on {3}..."
                    "has it been removed? Should I delete from db?".format(curEpToWrite.season, curEpToWrite.episode, curEpToWrite.show.name, ep_obj.idxr.name)
                )
                return None

            if curEpToWrite == ep_obj:
                # root (or single) episode

                if ep_obj.airdate != datetime.date.min and not myEp.get("firstAired"):
                    myEp["firstAired"] = str(ep_obj.airdate)

                if not (myEp.get("episodeName") and myEp.get("firstAired")):
                    return None

                episode = movie

                if curEpToWrite.name:
                    EpisodeName = ElementTree.SubElement(episode, "title")
                    EpisodeName.text = curEpToWrite.name

                SeasonNumber = ElementTree.SubElement(episode, "season")
                SeasonNumber.text = str(curEpToWrite.season)

                EpisodeNumber = ElementTree.SubElement(episode, "episode")
                EpisodeNumber.text = str(curEpToWrite.episode)

                if getattr(myShow, "firstAired", None):
                    try:
                        year_text = str(datetime.datetime.strptime(myShow.firstAired, dateFormat).year)
                        if year_text:
                            year = ElementTree.SubElement(episode, "year")
                            year.text = year_text
                    except Exception:
                        pass

                if getattr(myShow, "overview", None):
                    plot = ElementTree.SubElement(episode, "plot")
                    plot.text = myShow.overview

                if curEpToWrite.description:
                    Overview = ElementTree.SubElement(episode, "episodeplot")
                    Overview.text = curEpToWrite.description

                if getattr(myShow, "contentRating", None):
                    mpaa = ElementTree.SubElement(episode, "mpaa")
                    mpaa.text = myShow.rating

                if not ep_obj.relatedEps and myEp.get("rating"):
                    try:
                        rating = int((float(myEp.siteRating) * 10))
                    except ValueError:
                        rating = 0

                    if rating:
                        Rating = ElementTree.SubElement(episode, "rating")
                        Rating.text = str(rating)

                if myEp.get("directors") and isinstance(myEp["directors"], list):
                    for director in myEp["directors"]:
                        cur_director = ElementTree.SubElement(episode, "director")
                        cur_director.text = director

                if myEp.get("writers") and isinstance(myEp["writers"], list):
                    for writer in myEp["writers"]:
                        cur_writer = ElementTree.SubElement(episode, "credits")
                        cur_writer.text = writer

                if myEp.get("guestStars") and isinstance(myEp["guestStars"], list):
                    cast = ElementTree.SubElement(episode, "cast")
                    for actor in myEp["guestStars"]:
                        cur_actor = ElementTree.SubElement(cast, "actor")
                        cur_actor.text = actor

            else:
                # append data from (if any) related episodes

                if curEpToWrite.name:
                    if not EpisodeName.text:
                        EpisodeName.text = curEpToWrite.name
                    else:
                        EpisodeName.text = EpisodeName.text + ", " + curEpToWrite.name

                if curEpToWrite.description:
                    if not Overview.text:
                        Overview.text = curEpToWrite.description
                    else:
                        Overview.text = Overview.text + "\r" + curEpToWrite.description

        helpers.indentXML(rootNode)
        data = ElementTree.ElementTree(rootNode)

        return data

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

        nfo_file_path = self.get_episode_file_path(ep_obj)
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
