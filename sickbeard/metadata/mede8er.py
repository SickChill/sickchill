# coding=utf-8

# Author: Nic Wolfe <nic@wolfeden.ca>
# URL: http://code.google.com/p/sickbeard/
#
# This file is part of SickRage.
#
# SickRage is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SickRage is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

import io
import os
import datetime

import sickbeard
from sickbeard import logger, helpers
from sickbeard.metadata import mediabrowser

from sickrage.helper.common import dateFormat
from sickrage.helper.encoding import ek
from sickrage.helper.exceptions import ex, ShowNotFoundException

try:
    import xml.etree.cElementTree as etree
except ImportError:
    import xml.etree.ElementTree as etree


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

    def __init__(self,
                 show_metadata=False,
                 episode_metadata=False,
                 fanart=False,
                 poster=False,
                 banner=False,
                 episode_thumbnails=False,
                 season_posters=False,
                 season_banners=False,
                 season_all_poster=False,
                 season_all_banner=False):

        mediabrowser.MediaBrowserMetadata.__init__(
            self, show_metadata, episode_metadata, fanart,
            poster, banner, episode_thumbnails, season_posters,
            season_banners, season_all_poster, season_all_banner
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
        return helpers.replaceExtension(ep_obj.location, self._ep_nfo_extension)

    @staticmethod
    def get_episode_thumb_path(ep_obj):
        return helpers.replaceExtension(ep_obj.location, 'jpg')

    def _show_data(self, show_obj):
        """
        Creates an elementTree XML structure for a MediaBrowser-style series.xml
        returns the resulting data object.

        show_obj: a TVShow instance to create the NFO for
        """

        indexer_lang = show_obj.lang
        lINDEXER_API_PARMS = sickbeard.indexerApi(show_obj.indexer).api_params.copy()

        lINDEXER_API_PARMS['actors'] = True

        if indexer_lang and not indexer_lang == sickbeard.INDEXER_DEFAULT_LANGUAGE:
            lINDEXER_API_PARMS['language'] = indexer_lang

        if show_obj.dvdorder != 0:
            lINDEXER_API_PARMS['dvdorder'] = True

        t = sickbeard.indexerApi(show_obj.indexer).indexer(**lINDEXER_API_PARMS)

        rootNode = etree.Element("details")
        tv_node = etree.SubElement(rootNode, "movie")
        tv_node.attrib["isExtra"] = "false"
        tv_node.attrib["isSet"] = "false"
        tv_node.attrib["isTV"] = "true"

        try:
            myShow = t[int(show_obj.indexerid)]
        except sickbeard.indexer_shownotfound:
            logger.log(u"Unable to find show with id " + str(show_obj.indexerid) + " on tvdb, skipping it", logger.ERROR)
            raise

        except sickbeard.indexer_error:
            logger.log(u"TVDB is down, can't use its data to make the NFO", logger.ERROR)
            raise

        # check for title and id
        if not (getattr(myShow, 'seriesname', None) and getattr(myShow, 'id', None)):
            logger.log(u"Incomplete info for show with id " + str(show_obj.indexerid) + " on " + sickbeard.indexerApi(
                show_obj.indexer).name + ", skipping it")
            return False

        SeriesName = etree.SubElement(tv_node, "title")
        SeriesName.text = myShow['seriesname']

        if getattr(myShow, "genre", None):
            Genres = etree.SubElement(tv_node, "genres")
            for genre in myShow['genre'].split('|'):
                if genre and genre.strip():
                    cur_genre = etree.SubElement(Genres, "Genre")
                    cur_genre.text = genre.strip()

        if getattr(myShow, 'firstaired', None):
            FirstAired = etree.SubElement(tv_node, "premiered")
            FirstAired.text = myShow['firstaired']

        if getattr(myShow, "firstaired", None):
            try:
                year_text = str(datetime.datetime.strptime(myShow["firstaired"], dateFormat).year)
                if year_text:
                    year = etree.SubElement(tv_node, "year")
                    year.text = year_text
            except Exception:
                pass

        if getattr(myShow, 'overview', None):
            plot = etree.SubElement(tv_node, "plot")
            plot.text = myShow["overview"]

        if getattr(myShow, 'rating', None):
            try:
                rating = int(float(myShow['rating']) * 10)
            except ValueError:
                rating = 0

            if rating:
                Rating = etree.SubElement(tv_node, "rating")
                Rating.text = str(rating)

        if getattr(myShow, 'status', None):
            Status = etree.SubElement(tv_node, "status")
            Status.text = myShow['status']

        if getattr(myShow, "contentrating", None):
            mpaa = etree.SubElement(tv_node, "mpaa")
            mpaa.text = myShow["contentrating"]

        if getattr(myShow, 'imdb_id', None):
            imdb_id = etree.SubElement(tv_node, "id")
            imdb_id.attrib["moviedb"] = "imdb"
            imdb_id.text = myShow['imdb_id']

        if getattr(myShow, 'id', None):
            indexerid = etree.SubElement(tv_node, "indexerid")
            indexerid.text = myShow['id']

        if getattr(myShow, 'runtime', None):
            Runtime = etree.SubElement(tv_node, "runtime")
            Runtime.text = myShow['runtime']

        if getattr(myShow, '_actors', None):
            cast = etree.SubElement(tv_node, "cast")
            for actor in myShow['_actors']:
                if 'name' in actor and actor['name'].strip():
                    cur_actor = etree.SubElement(cast, "actor")
                    cur_actor.text = actor['name'].strip()

        helpers.indentXML(rootNode)

        data = etree.ElementTree(rootNode)

        return data

    def _ep_data(self, ep_obj):
        """
        Creates an elementTree XML structure for a MediaBrowser style episode.xml
        and returns the resulting data object.

        show_obj: a TVShow instance to create the NFO for
        """

        eps_to_write = [ep_obj] + ep_obj.relatedEps

        indexer_lang = ep_obj.show.lang

        try:
            # There's gotta be a better way of doing this but we don't wanna
            # change the language value elsewhere
            lINDEXER_API_PARMS = sickbeard.indexerApi(ep_obj.show.indexer).api_params.copy()

            if indexer_lang and not indexer_lang == sickbeard.INDEXER_DEFAULT_LANGUAGE:
                lINDEXER_API_PARMS['language'] = indexer_lang

            if ep_obj.show.dvdorder != 0:
                lINDEXER_API_PARMS['dvdorder'] = True

            t = sickbeard.indexerApi(ep_obj.show.indexer).indexer(**lINDEXER_API_PARMS)
            myShow = t[ep_obj.show.indexerid]
        except sickbeard.indexer_shownotfound, e:
            raise ShowNotFoundException(e.message)
        except sickbeard.indexer_error, e:
            logger.log(u"Unable to connect to TVDB while creating meta files - skipping - " + ex(e), logger.ERROR)
            return False

        rootNode = etree.Element("details")
        movie = etree.SubElement(rootNode, "movie")

        movie.attrib["isExtra"] = "false"
        movie.attrib["isSet"] = "false"
        movie.attrib["isTV"] = "true"

        # write an MediaBrowser XML containing info for all matching episodes
        for curEpToWrite in eps_to_write:

            try:
                myEp = myShow[curEpToWrite.season][curEpToWrite.episode]
            except (sickbeard.indexer_episodenotfound, sickbeard.indexer_seasonnotfound):
                logger.log(u"Unable to find episode %dx%d on %s... has it been removed? Should I delete from db?" %
                           (curEpToWrite.season, curEpToWrite.episode, sickbeard.indexerApi(ep_obj.show.indexer).name))
                return None

            if curEpToWrite == ep_obj:
                # root (or single) episode

                # default to today's date for specials if firstaired is not set
                if curEpToWrite.season == 0 and not getattr(myEp, 'firstaired', None):
                    myEp['firstaired'] = str(datetime.date.fromordinal(1))

                if not (getattr(myEp, 'episodename', None) and getattr(myEp, 'firstaired', None)):
                    return None

                episode = movie

                if curEpToWrite.name:
                    EpisodeName = etree.SubElement(episode, "title")
                    EpisodeName.text = curEpToWrite.name

                SeasonNumber = etree.SubElement(episode, "season")
                SeasonNumber.text = str(curEpToWrite.season)

                EpisodeNumber = etree.SubElement(episode, "episode")
                EpisodeNumber.text = str(curEpToWrite.episode)

                if getattr(myShow, "firstaired", None):
                    try:
                        year_text = str(datetime.datetime.strptime(myShow["firstaired"], dateFormat).year)
                        if year_text:
                            year = etree.SubElement(episode, "year")
                            year.text = year_text
                    except Exception:
                        pass

                if getattr(myShow, "overview", None):
                    plot = etree.SubElement(episode, "plot")
                    plot.text = myShow["overview"]

                if curEpToWrite.description:
                    Overview = etree.SubElement(episode, "episodeplot")
                    Overview.text = curEpToWrite.description

                if getattr(myShow, 'contentrating', None):
                    mpaa = etree.SubElement(episode, "mpaa")
                    mpaa.text = myShow["contentrating"]

                if not ep_obj.relatedEps and getattr(myEp, "rating", None):
                    try:
                        rating = int((float(myEp['rating']) * 10))
                    except ValueError:
                        rating = 0

                    if rating:
                        Rating = etree.SubElement(episode, "rating")
                        Rating.text = str(rating)

                if getattr(myEp, 'director', None):
                    director = etree.SubElement(episode, "director")
                    director.text = myEp['director']

                if getattr(myEp, 'writer', None):
                    writer = etree.SubElement(episode, "credits")
                    writer.text = myEp['writer']

                if getattr(myShow, '_actors', None) or getattr(myEp, 'gueststars', None):
                    cast = etree.SubElement(episode, "cast")
                    if getattr(myEp, 'gueststars', None) and isinstance(myEp['gueststars'], basestring):
                        for actor in (x.strip() for x in myEp['gueststars'].split('|') if x.strip()):
                            cur_actor = etree.SubElement(cast, "actor")
                            cur_actor.text = actor

                    if getattr(myShow, '_actors', None):
                        for actor in myShow['_actors']:
                            if 'name' in actor and actor['name'].strip():
                                cur_actor = etree.SubElement(cast, "actor")
                                cur_actor.text = actor['name'].strip()

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
        data = etree.ElementTree(rootNode)

        return data

    def write_show_file(self, show_obj):
        """
        Generates and writes show_obj's metadata under the given path to the
        filename given by get_show_file_path()

        show_obj: TVShow object for which to create the metadata

        path: An absolute or relative path where we should put the file. Note that
                the file name will be the default show_file_name.

        Note that this method expects that _show_data will return an ElementTree
        object. If your _show_data returns data in another format you'll need to
        override this method.
        """

        data = self._show_data(show_obj)

        if not data:
            return False

        nfo_file_path = self.get_show_file_path(show_obj)
        nfo_file_dir = ek(os.path.dirname, nfo_file_path)

        try:
            if not ek(os.path.isdir, nfo_file_dir):
                logger.log(u"Metadata dir didn't exist, creating it at " + nfo_file_dir, logger.DEBUG)
                ek(os.makedirs, nfo_file_dir)
                helpers.chmodAsParent(nfo_file_dir)

            logger.log(u"Writing show nfo file to " + nfo_file_path, logger.DEBUG)

            nfo_file = io.open(nfo_file_path, 'wb')

            data.write(nfo_file)
            nfo_file.close()
            helpers.chmodAsParent(nfo_file_path)
        except IOError, e:
            logger.log(u"Unable to write file to " + nfo_file_path + " - are you sure the folder is writable? " + ex(e),
                       logger.ERROR)
            return False

        return True

    def write_ep_file(self, ep_obj):
        """
        Generates and writes ep_obj's metadata under the given path with the
        given filename root. Uses the episode's name with the extension in
        _ep_nfo_extension.

        ep_obj: TVEpisode object for which to create the metadata

        file_name_path: The file name to use for this metadata. Note that the extension
                will be automatically added based on _ep_nfo_extension. This should
                include an absolute path.

        Note that this method expects that _ep_data will return an ElementTree
        object. If your _ep_data returns data in another format you'll need to
        override this method.
        """

        data = self._ep_data(ep_obj)

        if not data:
            return False

        nfo_file_path = self.get_episode_file_path(ep_obj)
        nfo_file_dir = ek(os.path.dirname, nfo_file_path)

        try:
            if not ek(os.path.isdir, nfo_file_dir):
                logger.log(u"Metadata dir didn't exist, creating it at " + nfo_file_dir, logger.DEBUG)
                ek(os.makedirs, nfo_file_dir)
                helpers.chmodAsParent(nfo_file_dir)

            logger.log(u"Writing episode nfo file to " + nfo_file_path, logger.DEBUG)

            nfo_file = io.open(nfo_file_path, 'wb')

            data.write(nfo_file)
            nfo_file.close()
            helpers.chmodAsParent(nfo_file_path)
        except IOError, e:
            logger.log(u"Unable to write file to " + nfo_file_path + " - are you sure the folder is writable? " + ex(e),
                       logger.ERROR)
            return False

        return True

# present a standard "interface" from the module
metadata_class = Mede8erMetadata
