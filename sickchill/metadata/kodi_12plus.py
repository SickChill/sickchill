# coding=utf-8

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
import re

import six
from babelfish import Country

import sickchill
from sickchill import helpers, logger
from sickchill.helper.common import dateFormat
from sickchill.helper.exceptions import ex, ShowNotFoundException
from sickchill.metadata import generic

try:
    import xml.etree.cElementTree as etree
except ImportError:
    import xml.etree.ElementTree as etree


class KODI_12PlusMetadata(generic.GenericMetadata):
    """
    Metadata generation class for KODI 12+.

    The following file structure is used:

    show_root/tvshow.nfo                    (show metadata)
    show_root/fanart.jpg                    (fanart)
    show_root/poster.jpg                    (poster)
    show_root/banner.jpg                    (banner)
    show_root/Season ##/filename.ext        (*)
    show_root/Season ##/filename.nfo        (episode metadata)
    show_root/Season ##/filename-thumb.jpg  (episode thumb)
    show_root/season##-poster.jpg           (season posters)
    show_root/season##-banner.jpg           (season banners)
    show_root/season-all-poster.jpg         (season all poster)
    show_root/season-all-banner.jpg         (season all banner)
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

        self.name = 'KODI 12+'

        self.poster_name = "poster.jpg"
        self.season_all_poster_name = "season-all-poster.jpg"

        # web-ui metadata template
        self.eg_show_metadata = "tvshow.nfo"
        self.eg_episode_metadata = "Season##\\<i>filename</i>.nfo"
        self.eg_fanart = "fanart.jpg"
        self.eg_poster = "poster.jpg"
        self.eg_banner = "banner.jpg"
        self.eg_episode_thumbnails = "Season##\\<i>filename</i>-thumb.jpg"
        self.eg_season_posters = "season##-poster.jpg"
        self.eg_season_banners = "season##-banner.jpg"
        self.eg_season_all_poster = "season-all-poster.jpg"
        self.eg_season_all_banner = "season-all-banner.jpg"

    @staticmethod
    def _split_info(info_string):
        return {x.strip().title() for x in re.sub(r'[,/]+', '|', info_string).split('|') if x.strip()}

    def _show_data(self, show_obj):
        """
        Creates an elementTree XML structure for an KODI-style tvshow.nfo and
        returns the resulting data object.

        show_obj: a TVShow instance to create the NFO for
        """

        show_ID = show_obj.indexerid

        indexer_lang = show_obj.lang
        lINDEXER_API_PARMS = sickchill.indexerApi(show_obj.indexer).api_params.copy()

        lINDEXER_API_PARMS['actors'] = True

        lINDEXER_API_PARMS['language'] = indexer_lang or sickchill.INDEXER_DEFAULT_LANGUAGE

        if show_obj.dvdorder:
            lINDEXER_API_PARMS['dvdorder'] = True

        t = sickchill.indexerApi(show_obj.indexer).indexer(**lINDEXER_API_PARMS)

        tv_node = etree.Element("tvshow")

        try:
            myShow = t[int(show_ID)]
        except sickchill.indexer_shownotfound:
            logger.log("Unable to find show with id " + str(show_ID) + " on " + sickchill.indexerApi(
                show_obj.indexer).name + ", skipping it", logger.ERROR)
            raise

        except sickchill.indexer_error:
            logger.log(
                "" + sickchill.indexerApi(show_obj.indexer).name + " is down, can't use its data to add this show",
                logger.ERROR)
            raise

        # check for title and id
        if not (getattr(myShow, 'seriesname', None) and getattr(myShow, 'id', None)):
            logger.log("Incomplete info for show with id " + str(show_ID) + " on " + sickchill.indexerApi(
                show_obj.indexer).name + ", skipping it")
            return False

        title = etree.SubElement(tv_node, "title")
        title.text = myShow["seriesname"]

        if getattr(myShow, 'rating', None):
            rating = etree.SubElement(tv_node, "rating")
            rating.text = myShow["rating"]

        if getattr(myShow, 'firstaired', None):
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

        if getattr(myShow, 'id', None):
            episodeguide = etree.SubElement(tv_node, "episodeguide")
            episodeguideurl = etree.SubElement(episodeguide, "url")
            episodeguideurl.text = sickchill.indexerApi(show_obj.indexer).config['base_url'] + str(myShow["id"]) + '/all/en.zip'

        if getattr(myShow, 'contentrating', None):
            mpaa = etree.SubElement(tv_node, "mpaa")
            mpaa.text = myShow["contentrating"]

        if getattr(myShow, 'id', None):
            indexerid = etree.SubElement(tv_node, "id")
            indexerid.text = str(myShow["id"])

        if getattr(myShow, 'genre', None) and isinstance(myShow["genre"], six.string_types):
            for genre in self._split_info(myShow["genre"]):
                cur_genre = etree.SubElement(tv_node, "genre")
                cur_genre.text = genre

        if 'country_codes' in show_obj.imdb_info:
            for country in self._split_info(show_obj.imdb_info['country_codes']):
                try:
                    cur_country_name = Country(country.upper()).name.title()
                except Exception:
                    continue

                cur_country = etree.SubElement(tv_node, "country")
                cur_country.text = cur_country_name

        if getattr(myShow, 'firstaired', None):
            premiered = etree.SubElement(tv_node, "premiered")
            premiered.text = myShow["firstaired"]

        if getattr(myShow, 'network', None):
            studio = etree.SubElement(tv_node, "studio")
            studio.text = myShow["network"].strip()

        if getattr(myShow, 'writer', None) and isinstance(myShow['writer'], six.string_types):
            for writer in self._split_info(myShow['writer']):
                cur_writer = etree.SubElement(tv_node, "credits")
                cur_writer.text = writer

        if getattr(myShow, 'director', None) and isinstance(myShow['director'], six.string_types):
            for director in self._split_info(myShow['director']):
                cur_director = etree.SubElement(tv_node, "director")
                cur_director.text = director

        if getattr(myShow, '_actors', None):
            for actor in myShow['_actors']:
                cur_actor = etree.SubElement(tv_node, "actor")

                if 'name' in actor and actor['name'].strip():
                    cur_actor_name = etree.SubElement(cur_actor, "name")
                    cur_actor_name.text = actor['name'].strip()
                else:
                    continue

                if 'role' in actor and actor['role'].strip():
                    cur_actor_role = etree.SubElement(cur_actor, "role")
                    cur_actor_role.text = actor['role'].strip()

                if 'image' in actor and actor['image'].strip():
                    cur_actor_thumb = etree.SubElement(cur_actor, "thumb")
                    cur_actor_thumb.text = actor['image'].strip()

        # Make it purdy
        helpers.indentXML(tv_node)

        data = etree.ElementTree(tv_node)

        return data

    def _ep_data(self, ep_obj):
        """
        Creates an elementTree XML structure for an KODI-style episode.nfo and
        returns the resulting data object.
            show_obj: a TVEpisode instance to create the NFO for
        """

        eps_to_write = [ep_obj] + ep_obj.relatedEps

        indexer_lang = ep_obj.show.lang

        lINDEXER_API_PARMS = sickchill.indexerApi(ep_obj.show.indexer).api_params.copy()

        lINDEXER_API_PARMS['actors'] = True

        lINDEXER_API_PARMS['language'] = indexer_lang or sickchill.INDEXER_DEFAULT_LANGUAGE

        if ep_obj.show.dvdorder:
            lINDEXER_API_PARMS['dvdorder'] = True

        try:
            t = sickchill.indexerApi(ep_obj.show.indexer).indexer(**lINDEXER_API_PARMS)
            myShow = t[ep_obj.show.indexerid]
        except sickchill.indexer_shownotfound as e:
            raise ShowNotFoundException(e.message)
        except sickchill.indexer_error as e:
            logger.log("Unable to connect to " + sickchill.indexerApi(
                ep_obj.show.indexer).name + " while creating meta files - skipping - " + ex(e), logger.ERROR)
            return

        if len(eps_to_write) > 1:
            rootNode = etree.Element("kodimultiepisode")
        else:
            rootNode = etree.Element("episodedetails")

        # write an NFO containing info for all matching episodes
        for curEpToWrite in eps_to_write:

            try:
                myEp = myShow[curEpToWrite.season][curEpToWrite.episode]
            except (sickchill.indexer_episodenotfound, sickchill.indexer_seasonnotfound):
                logger.log("Metadata writer is unable to find episode {0:d}x{1:d} of {2} on {3}..."
                           "has it been removed? Should I delete from db?".format(
                    curEpToWrite.season, curEpToWrite.episode, curEpToWrite.show.name,
                    sickchill.indexerApi(ep_obj.show.indexer).name))

                return None

            if not getattr(myEp, 'firstaired', None):
                myEp["firstaired"] = str(datetime.date.fromordinal(1))

            if not getattr(myEp, 'episodename', None):
                logger.log("Not generating nfo because the ep has no title", logger.DEBUG)
                return None

            logger.log("Creating metadata for episode " + str(ep_obj.season) + "x" + str(ep_obj.episode), logger.DEBUG)

            if len(eps_to_write) > 1:
                episode = etree.SubElement(rootNode, "episodedetails")
            else:
                episode = rootNode

            if getattr(myEp, 'episodename', None):
                title = etree.SubElement(episode, "title")
                title.text = myEp['episodename']

            if getattr(myShow, 'seriesname', None):
                showtitle = etree.SubElement(episode, "showtitle")
                showtitle.text = myShow['seriesname']

            season = etree.SubElement(episode, "season")
            season.text = str(curEpToWrite.season)

            episodenum = etree.SubElement(episode, "episode")
            episodenum.text = str(curEpToWrite.episode)

            uniqueid = etree.SubElement(episode, "uniqueid")
            uniqueid.text = str(curEpToWrite.indexerid)

            if curEpToWrite.airdate != datetime.date.fromordinal(1):
                aired = etree.SubElement(episode, "aired")
                aired.text = str(curEpToWrite.airdate)

            if getattr(myEp, 'overview', None):
                plot = etree.SubElement(episode, "plot")
                plot.text = myEp['overview']

            if curEpToWrite.season and getattr(myShow, 'runtime', None):
                runtime = etree.SubElement(episode, "runtime")
                runtime.text = myShow["runtime"]

            if getattr(myEp, 'airsbefore_season', None):
                displayseason = etree.SubElement(episode, "displayseason")
                displayseason.text = myEp['airsbefore_season']

            if getattr(myEp, 'airsbefore_episode', None):
                displayepisode = etree.SubElement(episode, "displayepisode")
                displayepisode.text = myEp['airsbefore_episode']

            if getattr(myEp, 'filename', None):
                thumb = etree.SubElement(episode, "thumb")
                thumb.text = myEp['filename'].strip()

            # watched = etree.SubElement(episode, "watched")
            # watched.text = 'false'

            if getattr(myEp, 'rating', None):
                rating = etree.SubElement(episode, "rating")
                rating.text = myEp['rating']

            if getattr(myEp, 'writer', None) and isinstance(myEp['writer'], six.string_types):
                for writer in self._split_info(myEp['writer']):
                    cur_writer = etree.SubElement(episode, "credits")
                    cur_writer.text = writer

            if getattr(myEp, 'director', None) and isinstance(myEp['director'], six.string_types):
                for director in self._split_info(myEp['director']):
                    cur_director = etree.SubElement(episode, "director")
                    cur_director.text = director

            if getattr(myEp, 'gueststars', None) and isinstance(myEp['gueststars'], six.string_types):
                for actor in self._split_info(myEp['gueststars']):
                    cur_actor = etree.SubElement(episode, "actor")
                    cur_actor_name = etree.SubElement(cur_actor, "name")
                    cur_actor_name.text = actor

            if getattr(myShow, '_actors', None):
                for actor in myShow['_actors']:
                    cur_actor = etree.SubElement(episode, "actor")

                    if 'name' in actor and actor['name'].strip():
                        cur_actor_name = etree.SubElement(cur_actor, "name")
                        cur_actor_name.text = actor['name'].strip()
                    else:
                        continue

                    if 'role' in actor and actor['role'].strip():
                        cur_actor_role = etree.SubElement(cur_actor, "role")
                        cur_actor_role.text = actor['role'].strip()

                    if 'image' in actor and actor['image'].strip():
                        cur_actor_thumb = etree.SubElement(cur_actor, "thumb")
                        cur_actor_thumb.text = actor['image'].strip()

        # Make it purdy
        helpers.indentXML(rootNode)

        data = etree.ElementTree(rootNode)

        return data


# present a standard "interface" from the module
metadata_class = KODI_12PlusMetadata
