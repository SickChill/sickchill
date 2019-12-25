# coding=utf-8

# Author: Nic Wolfe <nic@wolfeden.ca>
# URL: https://sickchill.github.io
#
# This file is part of SickChill.
#
# SickChill is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SickChill is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickChill. If not, see <http://www.gnu.org/licenses/>.

from __future__ import print_function, unicode_literals

import datetime
import os
import re

import six

import sickbeard
from sickbeard import helpers, logger
from sickbeard.metadata import generic
from sickchill.helper.common import dateFormat, replace_extension
from sickchill.helper.encoding import ek
from sickchill.helper.exceptions import ex, ShowNotFoundException

try:
    import xml.etree.cElementTree as etree
except ImportError:
    import xml.etree.ElementTree as etree


class MediaBrowserMetadata(generic.GenericMetadata):
    """
    Metadata generation class for Media Browser 2.x/3.x - Standard Mode.

    The following file structure is used:

    show_root/series.xml                       (show metadata)
    show_root/folder.jpg                       (poster)
    show_root/backdrop.jpg                     (fanart)
    show_root/Season ##/folder.jpg             (season thumb)
    show_root/Season ##/filename.ext           (*)
    show_root/Season ##/metadata/filename.xml  (episode metadata)
    show_root/Season ##/metadata/filename.jpg  (episode thumb)
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

        self.name = 'MediaBrowser'

        self._ep_nfo_extension = 'xml'
        self._show_metadata_filename = 'series.xml'

        self.fanart_name = "backdrop.jpg"
        self.poster_name = "folder.jpg"

        # web-ui metadata template
        self.eg_show_metadata = "series.xml"
        self.eg_episode_metadata = "Season##\\metadata\\<i>filename</i>.xml"
        self.eg_fanart = "backdrop.jpg"
        self.eg_poster = "folder.jpg"
        self.eg_banner = "banner.jpg"
        self.eg_episode_thumbnails = "Season##\\metadata\\<i>filename</i>.jpg"
        self.eg_season_posters = "Season##\\folder.jpg"
        self.eg_season_banners = "Season##\\banner.jpg"
        self.eg_season_all_poster = "<i>not supported</i>"
        self.eg_season_all_banner = "<i>not supported</i>"

    # Override with empty methods for unsupported features
    def retrieveShowMetadata(self, folder):
        # while show metadata is generated, it is not supported for our lookup
        return None, None, None

    def create_season_all_poster(self, show_obj):
        pass

    def create_season_all_banner(self, show_obj):
        pass

    def get_episode_file_path(self, ep_obj):
        """
        Returns a full show dir/metadata/episode.xml path for MediaBrowser
        episode metadata files

        ep_obj: a TVEpisode object to get the path for
        """

        if ek(os.path.isfile, ep_obj.location):
            xml_file_name = replace_extension(ek(os.path.basename, ep_obj.location), self._ep_nfo_extension)
            metadata_dir_name = ek(os.path.join, ek(os.path.dirname, ep_obj.location), 'metadata')
            xml_file_path = ek(os.path.join, metadata_dir_name, xml_file_name)
        else:
            logger.log("Episode location doesn't exist: " + str(ep_obj.location), logger.DEBUG)
            return ''

        return xml_file_path

    @staticmethod
    def get_episode_thumb_path(ep_obj):
        """
        Returns a full show dir/metadata/episode.jpg path for MediaBrowser
        episode thumbs.

        ep_obj: a TVEpisode object to get the path from
        """

        if ek(os.path.isfile, ep_obj.location):
            tbn_file_name = replace_extension(ek(os.path.basename, ep_obj.location), 'jpg')
            metadata_dir_name = ek(os.path.join, ek(os.path.dirname, ep_obj.location), 'metadata')
            tbn_file_path = ek(os.path.join, metadata_dir_name, tbn_file_name)
        else:
            return None

        return tbn_file_path

    @staticmethod
    def get_season_poster_path(show_obj, season):
        """
        Season thumbs for MediaBrowser go in Show Dir/Season X/folder.jpg

        If no season folder exists, None is returned
        """

        dir_list = [x for x in ek(os.listdir, show_obj.location) if
                    ek(os.path.isdir, ek(os.path.join, show_obj.location, x))]

        season_dir_regex = r'^Season\s+(\d+)$'

        season_dir = None

        for cur_dir in dir_list:
            # MediaBrowser 1.x only supports 'Specials'
            # MediaBrowser 2.x looks to only support 'Season 0'
            # MediaBrowser 3.x looks to mimic KODI/Plex support
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
            logger.log("Unable to find a season dir for season " + str(season), logger.DEBUG)
            return None

        logger.log("Using " + str(season_dir) + "/folder.jpg as season dir for season " + str(season), logger.DEBUG)

        return ek(os.path.join, show_obj.location, season_dir, 'folder.jpg')

    @staticmethod
    def get_season_banner_path(show_obj, season):
        """
        Season thumbs for MediaBrowser go in Show Dir/Season X/banner.jpg

        If no season folder exists, None is returned
        """

        dir_list = [x for x in ek(os.listdir, show_obj.location) if
                    ek(os.path.isdir, ek(os.path.join, show_obj.location, x))]

        season_dir_regex = r'^Season\s+(\d+)$'

        season_dir = None

        for cur_dir in dir_list:
            # MediaBrowser 1.x only supports 'Specials'
            # MediaBrowser 2.x looks to only support 'Season 0'
            # MediaBrowser 3.x looks to mimic KODI/Plex support
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
            logger.log("Unable to find a season dir for season " + str(season), logger.DEBUG)
            return None

        logger.log("Using " + str(season_dir) + "/banner.jpg as season dir for season " + str(season), logger.DEBUG)

        return ek(os.path.join, show_obj.location, season_dir, 'banner.jpg')

    def _show_data(self, show_obj):
        """
        Creates an elementTree XML structure for a MediaBrowser-style series.xml
        returns the resulting data object.

        show_obj: a TVShow instance to create the NFO for
        """

        tv_node = etree.Element("Series")

        try:
            myShow = sickbeard.show_indexer[show_obj.indexer].series(show_obj.indexerid, language=show_obj.lang)
        except sickbeard.indexer_shownotfound:
            logger.log("Unable to find show with id {} on {}, skipping it".format(show_obj.indexerid, show_obj.indexer_name), logger.ERROR)
            raise

        except sickbeard.indexer_error:
            logger.log("{} is down, can't use its data to make the NFO".format(show_obj.indexer_name), logger.ERROR)
            raise

        # check for title and id
        if not (getattr(myShow, 'seriesname', None) and getattr(myShow, 'id', None)):
            logger.log("Incomplete info for show with id {} on {}, skipping it".format(show_obj.indexerid, show_obj.indexer_name))
            return False

        data = getattr(myShow, 'id', None)
        if data:
            indexerid = etree.SubElement(tv_node, "id")
            indexerid.text = data

        data = getattr(myShow, 'seriesname', None)
        if data:
            SeriesName = etree.SubElement(tv_node, "SeriesName")
            SeriesName.text = data

        data = getattr(myShow, 'status', None)
        if data:
            Status = etree.SubElement(tv_node, "Status")
            Status.text = data

        data = getattr(myShow, 'network', None)
        if data:
            Network = etree.SubElement(tv_node, "Network")
            Network.text = data

        data = getattr(myShow, 'airs_time', None)
        if data:
            Airs_Time = etree.SubElement(tv_node, "Airs_Time")
            Airs_Time.text = data

        data = getattr(myShow, 'airs_dayofweek', None)
        if data:
            Airs_DayOfWeek = etree.SubElement(tv_node, "Airs_DayOfWeek")
            Airs_DayOfWeek.text = data

        data = getattr(myShow, 'firstAired', None)
        if data:
            FirstAired = etree.SubElement(tv_node, "FirstAired")
            FirstAired.text = data

        data = getattr(myShow, 'contentrating', None)
        if data:
            ContentRating = etree.SubElement(tv_node, "ContentRating")
            ContentRating.text = data

            MPAARating = etree.SubElement(tv_node, "MPAARating")
            MPAARating.text = data

            certification = etree.SubElement(tv_node, "certification")
            certification.text = data

        MetadataType = etree.SubElement(tv_node, "Type")
        MetadataType.text = "Series"

        data = getattr(myShow, 'overview', None)
        if data:
            Overview = etree.SubElement(tv_node, "Overview")
            Overview.text = data

        data = getattr(myShow, 'firstaired', None)
        if data:
            PremiereDate = etree.SubElement(tv_node, "PremiereDate")
            PremiereDate.text = data

        data = getattr(myShow, 'rating', None)
        if data:
            Rating = etree.SubElement(tv_node, "Rating")
            Rating.text = data

        data = getattr(myShow, 'firstaired', None)
        if data:
            try:
                year_text = str(datetime.datetime.strptime(myShow['firstaired'], dateFormat).year)
                if year_text:
                    ProductionYear = etree.SubElement(tv_node, "ProductionYear")
                    ProductionYear.text = year_text
            except Exception:
                pass

        data = getattr(myShow, 'runtime', None)
        if data:
            RunningTime = etree.SubElement(tv_node, "RunningTime")
            RunningTime.text = data

            Runtime = etree.SubElement(tv_node, "Runtime")
            Runtime.text = data

        data = getattr(myShow, 'imdb_id', None)
        if data:
            imdb_id = etree.SubElement(tv_node, "IMDB_ID")
            imdb_id.text = data

            imdb_id = etree.SubElement(tv_node, "IMDB")
            imdb_id.text = data

            imdb_id = etree.SubElement(tv_node, "IMDbId")
            imdb_id.text = data

        data = getattr(myShow, 'zap2it_id', None)
        if data:
            Zap2ItId = etree.SubElement(tv_node, "Zap2ItId")
            Zap2ItId.text = data

        if getattr(myShow, 'genre', None) and isinstance(myShow["genre"], six.string_types):
            Genres = etree.SubElement(tv_node, "Genres")
            for genre in myShow['genre'].split('|'):
                if genre.strip():
                    cur_genre = etree.SubElement(Genres, "Genre")
                    cur_genre.text = genre.strip()

            Genre = etree.SubElement(tv_node, "Genre")
            Genre.text = "|".join([x.strip() for x in myShow["genre"].split('|') if x.strip()])

        data = getattr(myShow, 'network', None)
        if data:
            Studios = etree.SubElement(tv_node, "Studios")
            Studio = etree.SubElement(Studios, "Studio")
            Studio.text = data

        data = getattr(myShow, '_actors', None)
        if data:
            Persons = etree.SubElement(tv_node, "Persons")
            for actor in myShow['_actors']:
                if not ('name' in actor and actor['name'].strip()):
                    continue

                cur_actor = etree.SubElement(Persons, "Person")

                cur_actor_name = etree.SubElement(cur_actor, "Name")
                cur_actor_name.text = actor['name'].strip()

                cur_actor_type = etree.SubElement(cur_actor, "Type")
                cur_actor_type.text = "Actor"

                if 'role' in actor and actor['role'].strip():
                    cur_actor_role = etree.SubElement(cur_actor, "Role")
                    cur_actor_role.text = actor['role'].strip()

        helpers.indentXML(tv_node)

        data = etree.ElementTree(tv_node)

        return data

    def _ep_data(self, ep_obj):
        """
        Creates an elementTree XML structure for a MediaBrowser style episode.xml
        and returns the resulting data object.

        show_obj: a TVShow instance to create the NFO for
        """

        eps_to_write = [ep_obj] + ep_obj.relatedEps

        persons_dict = {
            'Director': [],
            'GuestStar': [],
            'Writer': []
        }

        indexer_lang = ep_obj.show.lang

        try:
            lINDEXER_API_PARMS = sickbeard.indexerApi(ep_obj.show.indexer).api_params.copy()

            lINDEXER_API_PARMS['actors'] = True

            lINDEXER_API_PARMS['language'] = indexer_lang or sickbeard.INDEXER_DEFAULT_LANGUAGE

            if ep_obj.show.dvdorder:
                lINDEXER_API_PARMS['dvdorder'] = True

            t = sickbeard.indexerApi(ep_obj.show.indexer).indexer(**lINDEXER_API_PARMS)

            myShow = t[ep_obj.show.indexerid]
        except sickbeard.indexer_shownotfound as e:
            raise ShowNotFoundException(e.message)
        except sickbeard.indexer_error as e:
            logger.log("Unable to connect to " + sickbeard.indexerApi(
                ep_obj.show.indexer).name + " while creating meta files - skipping - " + ex(e), logger.ERROR)
            return False

        rootNode = etree.Element("Item")

        # write an MediaBrowser XML containing info for all matching episodes
        for curEpToWrite in eps_to_write:

            try:
                myEp = myShow[curEpToWrite.season][curEpToWrite.episode]
            except (sickbeard.indexer_episodenotfound, sickbeard.indexer_seasonnotfound):
                logger.log("Metadata writer is unable to find episode {0:d}x{1:d} of {2} on {3}..."
                           "has it been removed? Should I delete from db?".format(
                    curEpToWrite.season, curEpToWrite.episode, curEpToWrite.show.name,
                    sickbeard.indexerApi(ep_obj.show.indexer).name))
                return None

            if curEpToWrite == ep_obj:
                # root (or single) episode

                # default to today's date for specials if firstaired is not set
                if ep_obj.season == 0 and not getattr(myEp, 'firstaired', None):
                    myEp['firstaired'] = str(datetime.date.fromordinal(1))

                if not (getattr(myEp, 'episodename', None) and getattr(myEp, 'firstaired', None)):
                    return None

                episode = rootNode

                if curEpToWrite.name:
                    EpisodeName = etree.SubElement(episode, "EpisodeName")
                    EpisodeName.text = curEpToWrite.name

                EpisodeNumber = etree.SubElement(episode, "EpisodeNumber")
                EpisodeNumber.text = str(ep_obj.episode)

                if ep_obj.relatedEps:
                    EpisodeNumberEnd = etree.SubElement(episode, "EpisodeNumberEnd")
                    EpisodeNumberEnd.text = str(curEpToWrite.episode)

                SeasonNumber = etree.SubElement(episode, "SeasonNumber")
                SeasonNumber.text = str(curEpToWrite.season)

                if not ep_obj.relatedEps and getattr(myEp, 'absolute_number', None):
                    absolute_number = etree.SubElement(episode, "absolute_number")
                    absolute_number.text = str(myEp['absolute_number'])

                if curEpToWrite.airdate != datetime.date.fromordinal(1):
                    FirstAired = etree.SubElement(episode, "FirstAired")
                    FirstAired.text = str(curEpToWrite.airdate)

                MetadataType = etree.SubElement(episode, "Type")
                MetadataType.text = "Episode"

                if curEpToWrite.description:
                    Overview = etree.SubElement(episode, "Overview")
                    Overview.text = curEpToWrite.description

                if not ep_obj.relatedEps:
                    data = getattr(myEp, 'rating', None)
                    if data:
                        Rating = etree.SubElement(episode, "Rating")
                        Rating.text = data

                    data = getattr(myShow, 'imdb_id', None)
                    if data:
                        IMDB_ID = etree.SubElement(episode, "IMDB_ID")
                        IMDB_ID.text = data

                        IMDB = etree.SubElement(episode, "IMDB")
                        IMDB.text = data

                        IMDbId = etree.SubElement(episode, "IMDbId")
                        IMDbId.text = data

                indexerid = etree.SubElement(episode, "id")
                indexerid.text = str(curEpToWrite.indexerid)

                Persons = etree.SubElement(episode, "Persons")

                data = getattr(myShow, '_actors', None)
                if data:
                    for actor in data:
                        if not ('name' in actor and actor['name'].strip()):
                            continue

                        cur_actor = etree.SubElement(Persons, "Person")

                        cur_actor_name = etree.SubElement(cur_actor, "Name")
                        cur_actor_name.text = actor['name'].strip()

                        cur_actor_type = etree.SubElement(cur_actor, "Type")
                        cur_actor_type.text = "Actor"

                        if 'role' in actor and actor['role'].strip():
                            cur_actor_role = etree.SubElement(cur_actor, "Role")
                            cur_actor_role.text = actor['role'].strip()

                Language = etree.SubElement(episode, "Language")
                Language.text = getattr(myEp, 'language', sickbeard.INDEXER_DEFAULT_LANGUAGE)

                thumb = etree.SubElement(episode, "filename")
                # TODO: See what this is needed for.. if its still needed
                # just write this to the NFO regardless of whether it actually exists or not
                # note: renaming files after nfo generation will break this, tough luck
                thumb_text = self.get_episode_thumb_path(ep_obj)
                if thumb_text:
                    thumb.text = thumb_text

            else:
                # append data from (if any) related episodes
                EpisodeNumberEnd.text = str(curEpToWrite.episode)

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

            # collect all directors, guest stars and writers
            data = getattr(myEp, 'director', None)
            if data:
                persons_dict['Director'] += [x.strip() for x in data.split('|') if x.strip()]
            data = getattr(myEp, 'gueststars', None)
            if data:
                persons_dict['GuestStar'] += [x.strip() for x in data.split('|') if x.strip()]
            data = getattr(myEp, 'writer', None)
            if data:
                persons_dict['Writer'] += [x.strip() for x in data.split('|') if x.strip()]

        # fill in Persons section with collected directors, guest starts and writers
        for person_type, names in six.iteritems(persons_dict):
            # remove doubles
            names = list(set(names))
            for cur_name in names:
                Person = etree.SubElement(Persons, "Person")
                cur_person_name = etree.SubElement(Person, "Name")
                cur_person_name.text = cur_name
                cur_person_type = etree.SubElement(Person, "Type")
                cur_person_type.text = person_type

        helpers.indentXML(rootNode)
        data = etree.ElementTree(rootNode)

        return data


# present a standard "interface" from the module
metadata_class = MediaBrowserMetadata
