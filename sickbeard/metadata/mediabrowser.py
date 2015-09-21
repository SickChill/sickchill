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

import generic

from sickbeard import logger, helpers

from sickrage.helper.common import dateFormat
from sickrage.helper.encoding import ek
from sickrage.helper.exceptions import ex, ShowNotFoundException

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
        return (None, None, None)

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
            xml_file_name = helpers.replaceExtension(ek(os.path.basename, ep_obj.location), self._ep_nfo_extension)
            metadata_dir_name = ek(os.path.join, ek(os.path.dirname, ep_obj.location), 'metadata')
            xml_file_path = ek(os.path.join, metadata_dir_name, xml_file_name)
        else:
            logger.log(u"Episode location doesn't exist: " + str(ep_obj.location), logger.DEBUG)
            return ''

        return xml_file_path

    def get_episode_thumb_path(self, ep_obj):
        """
        Returns a full show dir/metadata/episode.jpg path for MediaBrowser
        episode thumbs.

        ep_obj: a TVEpisode object to get the path from
        """

        if ek(os.path.isfile, ep_obj.location):
            tbn_file_name = helpers.replaceExtension(ek(os.path.basename, ep_obj.location), 'jpg')
            metadata_dir_name = ek(os.path.join, ek(os.path.dirname, ep_obj.location), 'metadata')
            tbn_file_path = ek(os.path.join, metadata_dir_name, tbn_file_name)
        else:
            return None

        return tbn_file_path

    def get_season_poster_path(self, show_obj, season):
        """
        Season thumbs for MediaBrowser go in Show Dir/Season X/folder.jpg

        If no season folder exists, None is returned
        """

        dir_list = [x for x in ek(os.listdir, show_obj.location) if
                    ek(os.path.isdir, ek(os.path.join, show_obj.location, x))]

        season_dir_regex = '^Season\s+(\d+)$'

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
            logger.log(u"Unable to find a season dir for season " + str(season), logger.DEBUG)
            return None

        logger.log(u"Using " + str(season_dir) + "/folder.jpg as season dir for season " + str(season), logger.DEBUG)

        return ek(os.path.join, show_obj.location, season_dir, 'folder.jpg')

    def get_season_banner_path(self, show_obj, season):
        """
        Season thumbs for MediaBrowser go in Show Dir/Season X/banner.jpg

        If no season folder exists, None is returned
        """

        dir_list = [x for x in ek(os.listdir, show_obj.location) if
                    ek(os.path.isdir, ek(os.path.join, show_obj.location, x))]

        season_dir_regex = '^Season\s+(\d+)$'

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
            logger.log(u"Unable to find a season dir for season " + str(season), logger.DEBUG)
            return None

        logger.log(u"Using " + str(season_dir) + "/banner.jpg as season dir for season " + str(season), logger.DEBUG)

        return ek(os.path.join, show_obj.location, season_dir, 'banner.jpg')

    def _show_data(self, show_obj):
        """
        Creates an elementTree XML structure for a MediaBrowser-style series.xml
        returns the resulting data object.

        show_obj: a TVShow instance to create the NFO for
        """

        indexer_lang = show_obj.lang
        # There's gotta be a better way of doing this but we don't wanna
        # change the language value elsewhere
        lINDEXER_API_PARMS = sickbeard.indexerApi(show_obj.indexer).api_params.copy()

        lINDEXER_API_PARMS['actors'] = True

        if indexer_lang and not indexer_lang == sickbeard.INDEXER_DEFAULT_LANGUAGE:
            lINDEXER_API_PARMS['language'] = indexer_lang

        if show_obj.dvdorder != 0:
            lINDEXER_API_PARMS['dvdorder'] = True

        t = sickbeard.indexerApi(show_obj.indexer).indexer(**lINDEXER_API_PARMS)

        tv_node = etree.Element("Series")

        try:
            myShow = t[int(show_obj.indexerid)]
        except sickbeard.indexer_shownotfound:
            logger.log(u"Unable to find show with id " + str(show_obj.indexerid) + " on " + sickbeard.indexerApi(
                show_obj.indexer).name + ", skipping it", logger.ERROR)
            raise

        except sickbeard.indexer_error:
            logger.log(
                u"" + sickbeard.indexerApi(show_obj.indexer).name + " is down, can't use its data to make the NFO",
                logger.ERROR)
            raise

        # check for title and id
        if getattr(myShow, 'seriesname', None) is None or getattr(myShow, 'id', None) is None:
            logger.log(u"Incomplete info for show with id " + str(show_obj.indexerid) + " on " + sickbeard.indexerApi(
                show_obj.indexer).name + ", skipping it", logger.ERROR)
            return False

        indexerid = etree.SubElement(tv_node, "id")
        if getattr(myShow, 'id', None) is not None:
            indexerid.text = str(myShow['id'])


        SeriesName = etree.SubElement(tv_node, "SeriesName")
        if getattr(myShow, 'seriesname', None) is not None:
            SeriesName.text = myShow['seriesname']

        Status = etree.SubElement(tv_node, "Status")
        if getattr(myShow, 'status', None) is not None:
            Status.text = myShow['status']

        Network = etree.SubElement(tv_node, "Network")
        if getattr(myShow, 'network', None) is not None:
            Network.text = myShow['network']

        Airs_Time = etree.SubElement(tv_node, "Airs_Time")
        if getattr(myShow, 'airs_time', None) is not None:
            Airs_Time.text = myShow['airs_time']

        Airs_DayOfWeek = etree.SubElement(tv_node, "Airs_DayOfWeek")
        if getattr(myShow, 'airs_dayofweek', None) is not None:
            Airs_DayOfWeek.text = myShow['airs_dayofweek']

        FirstAired = etree.SubElement(tv_node, "FirstAired")
        if getattr(myShow, 'firstaired', None) is not None:
            FirstAired.text = myShow['firstaired']

        ContentRating = etree.SubElement(tv_node, "ContentRating")
        MPAARating = etree.SubElement(tv_node, "MPAARating")
        certification = etree.SubElement(tv_node, "certification")
        if getattr(myShow, 'contentrating', None) is not None:
            ContentRating.text = myShow['contentrating']
            MPAARating.text = myShow['contentrating']
            certification.text = myShow['contentrating']

        MetadataType = etree.SubElement(tv_node, "Type")
        MetadataType.text = "Series"

        Overview = etree.SubElement(tv_node, "Overview")
        if getattr(myShow, 'overview', None) is not None:
            Overview.text = myShow['overview']

        PremiereDate = etree.SubElement(tv_node, "PremiereDate")
        if getattr(myShow, 'firstaired', None) is not None:
            PremiereDate.text = myShow['firstaired']

        Rating = etree.SubElement(tv_node, "Rating")
        if getattr(myShow, 'rating', None) is not None:
            Rating.text = myShow['rating']

        ProductionYear = etree.SubElement(tv_node, "ProductionYear")
        if getattr(myShow, 'firstaired', None) is not None:
            try:
                year_text = str(datetime.datetime.strptime(myShow['firstaired'], dateFormat).year)
                if year_text:
                    ProductionYear.text = year_text
            except:
                pass

        RunningTime = etree.SubElement(tv_node, "RunningTime")
        Runtime = etree.SubElement(tv_node, "Runtime")
        if getattr(myShow, 'runtime', None) is not None:
            RunningTime.text = myShow['runtime']
            Runtime.text = myShow['runtime']

        IMDB_ID = etree.SubElement(tv_node, "IMDB_ID")
        IMDB = etree.SubElement(tv_node, "IMDB")
        IMDbId = etree.SubElement(tv_node, "IMDbId")
        if getattr(myShow, 'imdb_id', None) is not None:
            IMDB_ID.text = myShow['imdb_id']
            IMDB.text = myShow['imdb_id']
            IMDbId.text = myShow['imdb_id']

        Zap2ItId = etree.SubElement(tv_node, "Zap2ItId")
        if getattr(myShow, 'zap2it_id', None) is not None:
            Zap2ItId.text = myShow['zap2it_id']

        Genres = etree.SubElement(tv_node, "Genres")
        for genre in myShow['genre'].split('|'):
            if genre:
                cur_genre = etree.SubElement(Genres, "Genre")
                cur_genre.text = genre

        Genre = etree.SubElement(tv_node, "Genre")
        if getattr(myShow, 'genre', None) is not None:
            Genre.text = "|".join([x for x in myShow["genre"].split('|') if x])

        Studios = etree.SubElement(tv_node, "Studios")
        Studio = etree.SubElement(Studios, "Studio")
        if getattr(myShow, 'network', None) is not None:
            Studio.text = myShow['network']

        Persons = etree.SubElement(tv_node, "Persons")
        if getattr(myShow, 'actors', None) is not None:
            for actor in myShow['_actors']:
                cur_actor = etree.SubElement(Persons, "Person")

                cur_actor_name = etree.SubElement(cur_actor, "Name")
                if getattr(actor, 'name', None):
                    cur_actor_name.text = actor['name'].strip()

                cur_actor_type = etree.SubElement(cur_actor, "Type")
                cur_actor_type.text = "Actor"

                cur_actor_role = etree.SubElement(cur_actor, "Role")
                if getattr(actor, 'role', None):
                    cur_actor_role.text = actor['role']

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

        persons_dict = {}
        persons_dict['Director'] = []
        persons_dict['GuestStar'] = []
        persons_dict['Writer'] = []

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

        rootNode = etree.Element("Item")

        # write an MediaBrowser XML containing info for all matching episodes
        for curEpToWrite in eps_to_write:

            try:
                myEp = myShow[curEpToWrite.season][curEpToWrite.episode]
            except (sickbeard.indexer_episodenotfound, sickbeard.indexer_seasonnotfound):
                logger.log(u"Unable to find episode " + str(curEpToWrite.season) + "x" + str(
                    curEpToWrite.episode) + " on " + sickbeard.indexerApi(
                    ep_obj.show.indexer).name + ".. has it been removed? Should I delete from db?")
                return None

            if curEpToWrite == ep_obj:
                # root (or single) episode

                # default to today's date for specials if firstaired is not set
                if getattr(myEp, 'firstaired', None) is None and ep_obj.season == 0:
                    myEp['firstaired'] = str(datetime.date.fromordinal(1))

                if getattr(myEp, 'episodename', None) is None or getattr(myEp, 'firstaired', None) is None:
                    return None

                episode = rootNode

                EpisodeName = etree.SubElement(episode, "EpisodeName")
                if curEpToWrite.name != None:
                    EpisodeName.text = curEpToWrite.name
                else:
                    EpisodeName.text = ""

                EpisodeNumber = etree.SubElement(episode, "EpisodeNumber")
                EpisodeNumber.text = str(ep_obj.episode)

                if ep_obj.relatedEps:
                    EpisodeNumberEnd = etree.SubElement(episode, "EpisodeNumberEnd")
                    EpisodeNumberEnd.text = str(curEpToWrite.episode)

                SeasonNumber = etree.SubElement(episode, "SeasonNumber")
                SeasonNumber.text = str(curEpToWrite.season)

                if not ep_obj.relatedEps:
                    absolute_number = etree.SubElement(episode, "absolute_number")
                    if getattr(myEp, 'absolute_number', None) is not None:
                        absolute_number.text = myEp['absolute_number']

                FirstAired = etree.SubElement(episode, "FirstAired")
                if curEpToWrite.airdate != datetime.date.fromordinal(1):
                    FirstAired.text = str(curEpToWrite.airdate)
                else:
                    FirstAired.text = ""

                MetadataType = etree.SubElement(episode, "Type")
                MetadataType.text = "Episode"

                Overview = etree.SubElement(episode, "Overview")
                if curEpToWrite.description != None:
                    Overview.text = curEpToWrite.description
                else:
                    Overview.text = ""

                if not ep_obj.relatedEps:
                    Rating = etree.SubElement(episode, "Rating")
                    if getattr(myEp, 'rating', None) is not None:
                        Rating.text = myEp['rating']

                    IMDB_ID = etree.SubElement(episode, "IMDB_ID")
                    IMDB = etree.SubElement(episode, "IMDB")
                    IMDbId = etree.SubElement(episode, "IMDbId")
                    if getattr(myShow, 'imdb_id', None) is not None:
                        IMDB_ID.text = myShow['imdb_id']
                        IMDB.text = myShow['imdb_id']
                        IMDbId.text = myShow['imdb_id']

                indexerid = etree.SubElement(episode, "id")
                indexerid.text = str(curEpToWrite.indexerid)

                Persons = etree.SubElement(episode, "Persons")

                Language = etree.SubElement(episode, "Language")
                try:
                    Language.text = myEp['language']
                except:
                    Language.text = sickbeard.INDEXER_DEFAULT_LANGUAGE  # tvrage api doesn't provide language so we must assume a value here

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
            if getattr(myEp, 'director', None) is not None:
                persons_dict['Director'] += [x.strip() for x in myEp['director'].split('|') if x]
            if getattr(myEp, 'gueststars', None) is not None:
                persons_dict['GuestStar'] += [x.strip() for x in myEp['gueststars'].split('|') if x]
            if getattr(myEp, 'writer', None) is not None:
                persons_dict['Writer'] += [x.strip() for x in myEp['writer'].split('|') if x]

        # fill in Persons section with collected directors, guest starts and writers
        for person_type, names in persons_dict.iteritems():
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
