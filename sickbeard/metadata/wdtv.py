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

import datetime
import os
import re

import sickbeard

from sickbeard.metadata import generic

from sickbeard import logger, helpers
from sickrage.helper.common import dateFormat
from sickrage.helper.encoding import ek
from sickrage.helper.exceptions import ex, ShowNotFoundException

try:
    import xml.etree.cElementTree as etree
except ImportError:
    import xml.etree.ElementTree as etree


class WDTVMetadata(generic.GenericMetadata):
    """
    Metadata generation class for WDTV

    The following file structure is used:

    show_root/folder.jpg                    (poster)
    show_root/Season ##/folder.jpg          (season thumb)
    show_root/Season ##/filename.ext        (*)
    show_root/Season ##/filename.metathumb  (episode thumb)
    show_root/Season ##/filename.xml        (episode metadata)
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

        generic.GenericMetadata.__init__(self,
                                         show_metadata,
                                         episode_metadata,
                                         fanart,
                                         poster,
                                         banner,
                                         episode_thumbnails,
                                         season_posters,
                                         season_banners,
                                         season_all_poster,
                                         season_all_banner)

        self.name = 'WDTV'

        self._ep_nfo_extension = 'xml'

        self.poster_name = "folder.jpg"

        # web-ui metadata template
        self.eg_show_metadata = "<i>not supported</i>"
        self.eg_episode_metadata = "Season##\\<i>filename</i>.xml"
        self.eg_fanart = "<i>not supported</i>"
        self.eg_poster = "folder.jpg"
        self.eg_banner = "<i>not supported</i>"
        self.eg_episode_thumbnails = "Season##\\<i>filename</i>.metathumb"
        self.eg_season_posters = "Season##\\folder.jpg"
        self.eg_season_banners = "<i>not supported</i>"
        self.eg_season_all_poster = "<i>not supported</i>"
        self.eg_season_all_banner = "<i>not supported</i>"

    # Override with empty methods for unsupported features
    def retrieveShowMetadata(self, folder):
        # no show metadata generated, we abort this lookup function
        return None, None, None

    def create_show_metadata(self, show_obj):
        pass

    def update_show_indexer_metadata(self, show_obj):
        pass

    def get_show_file_path(self, show_obj):
        pass

    def create_fanart(self, show_obj):
        pass

    def create_banner(self, show_obj):
        pass

    def create_season_banners(self, show_obj):
        pass

    def create_season_all_poster(self, show_obj):
        pass

    def create_season_all_banner(self, show_obj):
        pass

    @staticmethod
    def get_episode_thumb_path(ep_obj):
        """
        Returns the path where the episode thumbnail should be stored. Defaults to
        the same path as the episode file but with a .metathumb extension.

        ep_obj: a TVEpisode instance for which to create the thumbnail
        """
        if ek(os.path.isfile, ep_obj.location):
            tbn_filename = helpers.replaceExtension(ep_obj.location, 'metathumb')
        else:
            return None

        return tbn_filename

    @staticmethod
    def get_season_poster_path(show_obj, season):
        """
        Season thumbs for WDTV go in Show Dir/Season X/folder.jpg

        If no season folder exists, None is returned
        """

        dir_list = [x for x in ek(os.listdir, show_obj.location) if
                    ek(os.path.isdir, ek(os.path.join, show_obj.location, x))]

        season_dir_regex = r'^Season\s+(\d+)$'

        season_dir = None

        for cur_dir in dir_list:
            if season == 0 and cur_dir == "Specials":
                season_dir = cur_dir
                break

            match = re.match(season_dir_regex, cur_dir, re.I)
            if not match:
                continue

            cur_season = int(match.group(1))

            if cur_season == season:
                season_dir = cur_dir
                break

        if not season_dir:
            logger.log(u"Unable to find a season dir for season " + str(season), logger.DEBUG)
            return None

        logger.log(u"Using " + str(season_dir) + "/folder.jpg as season dir for season " + str(season), logger.DEBUG)

        return ek(os.path.join, show_obj.location, season_dir, 'folder.jpg')

    def _ep_data(self, ep_obj):
        """
        Creates an elementTree XML structure for a WDTV style episode.xml
        and returns the resulting data object.

        ep_obj: a TVShow instance to create the NFO for
        """

        eps_to_write = [ep_obj] + ep_obj.relatedEps

        indexer_lang = ep_obj.show.lang

        try:
            lINDEXER_API_PARMS = sickbeard.indexerApi(ep_obj.show.indexer).api_params.copy()

            lINDEXER_API_PARMS['actors'] = True

            if indexer_lang and not indexer_lang == sickbeard.INDEXER_DEFAULT_LANGUAGE:
                lINDEXER_API_PARMS['language'] = indexer_lang

            if ep_obj.show.dvdorder != 0:
                lINDEXER_API_PARMS['dvdorder'] = True

            t = sickbeard.indexerApi(ep_obj.show.indexer).indexer(**lINDEXER_API_PARMS)
            myShow = t[ep_obj.show.indexerid]
        except sickbeard.indexer_shownotfound, e:
            raise ShowNotFoundException(e.message)
        except sickbeard.indexer_error, e:
            logger.log(u"Unable to connect to " + sickbeard.indexerApi(
                ep_obj.show.indexer).name + " while creating meta files - skipping - " + ex(e), logger.ERROR)
            return False

        rootNode = etree.Element("details")

        # write an WDTV XML containing info for all matching episodes
        for curEpToWrite in eps_to_write:

            try:
                myEp = myShow[curEpToWrite.season][curEpToWrite.episode]
            except (sickbeard.indexer_episodenotfound, sickbeard.indexer_seasonnotfound):
                logger.log(u"Unable to find episode %dx%d on %s... has it been removed? Should I delete from db?" %
                           (curEpToWrite.season, curEpToWrite.episode, sickbeard.indexerApi(ep_obj.show.indexer).name))
                return None

            if ep_obj.season == 0 and not getattr(myEp, 'firstaired', None):
                myEp["firstaired"] = str(datetime.date.fromordinal(1))

            if not (getattr(myEp, 'episodename', None) and getattr(myEp, 'firstaired', None)):
                return None

            if len(eps_to_write) > 1:
                episode = etree.SubElement(rootNode, "details")
            else:
                episode = rootNode

            # TODO: get right EpisodeID
            episodeID = etree.SubElement(episode, "id")
            episodeID.text = str(curEpToWrite.indexerid)

            title = etree.SubElement(episode, "title")
            title.text = ep_obj.prettyName()

            if getattr(myShow, 'seriesname', None):
                seriesName = etree.SubElement(episode, "series_name")
                seriesName.text = myShow["seriesname"]

            if curEpToWrite.name:
                episodeName = etree.SubElement(episode, "episode_name")
                episodeName.text = curEpToWrite.name

            seasonNumber = etree.SubElement(episode, "season_number")
            seasonNumber.text = str(curEpToWrite.season)

            episodeNum = etree.SubElement(episode, "episode_number")
            episodeNum.text = str(curEpToWrite.episode)

            firstAired = etree.SubElement(episode, "firstaired")

            if curEpToWrite.airdate != datetime.date.fromordinal(1):
                firstAired.text = str(curEpToWrite.airdate)

            if getattr(myShow, 'firstaired', None):
                try:
                    year_text = str(datetime.datetime.strptime(myShow["firstaired"], dateFormat).year)
                    if year_text:
                        year = etree.SubElement(episode, "year")
                        year.text = year_text
                except Exception:
                    pass

            if curEpToWrite.season != 0 and getattr(myShow, 'runtime', None):
                runtime = etree.SubElement(episode, "runtime")
                runtime.text = myShow["runtime"]

            if getattr(myShow, 'genre', None):
                genre = etree.SubElement(episode, "genre")
                genre.text = " / ".join([x.strip() for x in myShow["genre"].split('|') if x.strip()])

            if getattr(myEp, 'director', None):
                director = etree.SubElement(episode, "director")
                director.text = myEp['director']

            if getattr(myShow, '_actors', None):
                for actor in myShow['_actors']:
                    if not ('name' in actor and actor['name'].strip()):
                        continue

                    cur_actor = etree.SubElement(episode, "actor")

                    cur_actor_name = etree.SubElement(cur_actor, "name")
                    cur_actor_name.text = actor['name']

                    if 'role' in actor and actor['role'].strip():
                        cur_actor_role = etree.SubElement(cur_actor, "role")
                        cur_actor_role.text = actor['role'].strip()

            if curEpToWrite.description:
                overview = etree.SubElement(episode, "overview")
                overview.text = curEpToWrite.description

            # Make it purdy
            helpers.indentXML(rootNode)
            data = etree.ElementTree(rootNode)

        return data


# present a standard "interface" from the module
metadata_class = WDTVMetadata
