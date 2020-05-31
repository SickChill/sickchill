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

from __future__ import absolute_import, print_function, unicode_literals

# Stdlib Imports
import datetime
import re

# Third Party Imports
import six
from babelfish import Country

# First Party Imports
import sickchill
from sickbeard import helpers, logger
from sickbeard.metadata import generic
from sickchill.helper.common import dateFormat

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
        tv_node = etree.Element("tvshow")

        myShow = sickchill.indexer.series(show_obj)
        if not myShow:
            logger.log("Unable to find show with id {} on {}, skipping it".format(
                show_obj.indexerid, show_obj.idxr.name))
            return False

        # check for title and id
        if not (getattr(myShow, 'seriesName', None) and getattr(myShow, 'id', None)):
            logger.log("Incomplete info for show with id {} on {}, skipping it".format(
                show_obj.indexerid, show_obj.idxr.name))
            return False

        title = etree.SubElement(tv_node, "title")
        title.text = myShow.seriesName

        if getattr(myShow, 'rating', None):
            mpaa = etree.SubElement(tv_node, "mpaa")
            mpaa.text = str(myShow.rating)

        if getattr(myShow, 'siteRating', None):
            rating = etree.SubElement(tv_node, "rating")
            rating.text = str(myShow.siteRating)

        if getattr(myShow, 'firstAired', None):
            try:
                year_text = str(datetime.datetime.strptime(myShow.firstAired, dateFormat).year)
                if year_text:
                    year = etree.SubElement(tv_node, "year")
                    year.text = year_text
            except Exception:
                pass

        if getattr(myShow, 'overview', None):
            plot = etree.SubElement(tv_node, "plot")
            plot.text = myShow.overview

        if getattr(myShow, 'id', None):
            episodeguide = etree.SubElement(tv_node, "episodeguide")
            episodeguideurl = etree.SubElement(episodeguide, "url")
            episodeguideurl.attrib = {'post': 'yes', 'cache': 'auth.json'}
            episodeguideurl.text = show_obj.idxr.episode_guide_url(show_obj)

            indexerid = etree.SubElement(tv_node, "id")
            indexerid.text = str(myShow.id)

            indexerid = etree.SubElement(tv_node, "tvdbid")
            indexerid.text = str(myShow.id)

        if getattr(myShow, 'genre', None) and isinstance(myShow.genre, list):
            for genre in myShow.genre:
                cur_genre = etree.SubElement(tv_node, "genre")
                cur_genre.text = genre

        if show_obj.imdb_info.get('country_codes'):
            for country in self._split_info(show_obj.imdb_info['country_codes']):
                try:
                    cur_country_name = Country(country.upper()).name.title()
                except Exception:
                    continue

                cur_country = etree.SubElement(tv_node, "country")
                cur_country.text = cur_country_name

        if getattr(myShow, 'firstAired', None):
            premiered = etree.SubElement(tv_node, "premiered")
            premiered.text = myShow.firstAired

        if getattr(myShow, 'network', None):
            studio = etree.SubElement(tv_node, "studio")
            studio.text = myShow.network.strip()

        data = show_obj.idxr.actors(myShow)
        if data:
            for actor in data:
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
                    cur_actor_thumb.text = show_obj.idxr.complete_image_url(actor['image'])

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

        myShow = ep_obj.idxr.series_from_episode(ep_obj)
        if not myShow:
            logger.log("Unable to find {} on {} while creating meta files, skipping".format(
                ep_obj.show.indexerid, ep_obj.idxr.name), logger.INFO)
            return

        if len(eps_to_write) > 1:
            rootNode = etree.Element("kodimultiepisode")
        else:
            rootNode = etree.Element("episodedetails")

        # write an NFO containing info for all matching episodes
        for curEpToWrite in eps_to_write:

            myEp = curEpToWrite.idxr.episode(curEpToWrite)
            if not myEp:
                logger.log("Metadata writer is unable to find episode {0:d}x{1:d} of {2} on {3}..."
                           "has it been removed? Should I delete from db?".format(
                    curEpToWrite.season, curEpToWrite.episode, curEpToWrite.show.name, ep_obj.idxr.name))

                return None

            if ep_obj.airdate != datetime.date.min and not myEp.get('firstAired'):
                myEp["firstAired"] = str(ep_obj.airdate)

            if not myEp.get('episodeName'):
                logger.log("Not generating nfo because the ep has no title", logger.DEBUG)
                return None

            if not myEp.get('firstAired'):
                logger.log("Not generating nfo because the ep has no airdate", logger.DEBUG)
                return None

            logger.log("Creating metadata for episode " + str(ep_obj.season) + "x" + str(ep_obj.episode), logger.DEBUG)

            if len(eps_to_write) > 1:
                episode = etree.SubElement(rootNode, "episodedetails")
            else:
                episode = rootNode

            if myEp.get('episodeName'):
                title = etree.SubElement(episode, "title")
                title.text = myEp['episodeName']

            if getattr(myShow, 'seriesName', None):
                showtitle = etree.SubElement(episode, "showtitle")
                showtitle.text = myShow.seriesName

            season = etree.SubElement(episode, "season")
            season.text = str(curEpToWrite.season)

            episodenum = etree.SubElement(episode, "episode")
            episodenum.text = str(curEpToWrite.episode)

            if myEp.get('id'):
                uniqueid = etree.SubElement(episode, "uniqueid")
                uniqueid.text = str(myEp['id'])

            if curEpToWrite.airdate != datetime.date.min:
                aired = etree.SubElement(episode, "aired")
                aired.text = str(curEpToWrite.airdate)

            if myEp.get('overview'):
                plot = etree.SubElement(episode, "plot")
                plot.text = myEp['overview']

            if curEpToWrite.season and getattr(myShow, 'runtime', None):
                runtime = etree.SubElement(episode, "runtime")
                runtime.text = myShow.runtime

            if myEp.get('airedSeason'):
                displayseason = etree.SubElement(episode, "displayseason")
                displayseason.text = str(myEp['airedSeason'])

            if myEp.get('airedEpisodeNumber'):
                displayepisode = etree.SubElement(episode, "displayepisode")
                displayepisode.text = str(myEp['airedEpisodeNumber'])

            if myEp.get('filename'):
                thumb = etree.SubElement(episode, "thumb")
                thumb.text = ep_obj.idxr.complete_image_url(myEp['filename'])

            if myEp.get('rating') is not None:
                rating = etree.SubElement(episode, "rating")
                rating.text = str(myEp['rating'])

            if myEp.get('writers') and isinstance(myEp['writers'], list):
                for writer in myEp['writers']:
                    cur_writer = etree.SubElement(episode, "credits")
                    cur_writer.text = writer

            if myEp.get('directors') and isinstance(myEp['directors'], list):
                for director in myEp['directors']:
                    cur_director = etree.SubElement(episode, "director")
                    cur_director.text = director

            if myEp.get('guestStars') and isinstance(myEp['guestStars'], list):
                for actor in myEp['guestStars']:
                    cur_actor = etree.SubElement(episode, "actor")
                    cur_actor_name = etree.SubElement(cur_actor, "name")
                    cur_actor_name.text = actor

            for actor in ep_obj.idxr.actors(myShow):
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
                    cur_actor_thumb.text = ep_obj.idxr.complete_image_url(actor['image'])

        # Make it purdy
        helpers.indentXML(rootNode)

        return etree.ElementTree(rootNode)


# present a standard "interface" from the module
metadata_class = KODI_12PlusMetadata
