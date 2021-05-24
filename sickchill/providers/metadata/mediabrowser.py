import datetime
import os
import re
from xml.etree import ElementTree

import sickchill
from sickchill import logger, settings
from sickchill.helper.common import dateFormat, replace_extension
from sickchill.oldbeard import helpers

from . import generic


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

        super().__init__(
            show_metadata, episode_metadata, fanart, poster, banner, episode_thumbnails, season_posters, season_banners, season_all_poster, season_all_banner
        )

        self.name = "MediaBrowser"

        self._ep_nfo_extension = "xml"
        self._show_metadata_filename = "series.xml"

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

        if os.path.isfile(ep_obj.location):
            xml_filename = replace_extension(os.path.basename(ep_obj.location), self._ep_nfo_extension)
            metadata_dir_name = os.path.join(os.path.dirname(ep_obj.location), "metadata")
            xml_file_path = os.path.join(metadata_dir_name, xml_filename)
        else:
            logger.debug("Episode location doesn't exist: " + str(ep_obj.location))
            return ""

        return xml_file_path

    @staticmethod
    def get_episode_thumb_path(ep_obj):
        """
        Returns a full show dir/metadata/episode.jpg path for MediaBrowser
        episode thumbs.

        ep_obj: a TVEpisode object to get the path from
        """

        if os.path.isfile(ep_obj.location):
            tbn_filename = replace_extension(os.path.basename(ep_obj.location), "jpg")
            metadata_dir_name = os.path.join(os.path.dirname(ep_obj.location), "metadata")
            tbn_file_path = os.path.join(metadata_dir_name, tbn_filename)
        else:
            return None

        return tbn_file_path

    @staticmethod
    def get_season_poster_path(show_obj, season):
        """
        Season thumbs for MediaBrowser go in Show Dir/Season X/folder.jpg

        If no season folder exists, None is returned
        """

        dir_list = [x for x in os.listdir(show_obj.location) if os.path.isdir(os.path.join(show_obj.location, x))]

        season_dir_regex = r"^Season\s+(\d+)$"

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
            logger.debug("Unable to find a season dir for season " + str(season))
            return None

        logger.debug("Using " + str(season_dir) + "/folder.jpg as season dir for season " + str(season))

        return os.path.join(show_obj.location, season_dir, "folder.jpg")

    @staticmethod
    def get_season_banner_path(show_obj, season):
        """
        Season thumbs for MediaBrowser go in Show Dir/Season X/banner.jpg

        If no season folder exists, None is returned
        """

        dir_list = [x for x in os.listdir(show_obj.location) if os.path.isdir(os.path.join(show_obj.location, x))]

        season_dir_regex = r"^Season\s+(\d+)$"

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
            logger.debug("Unable to find a season dir for season " + str(season))
            return None

        logger.debug("Using " + str(season_dir) + "/banner.jpg as season dir for season " + str(season))

        return os.path.join(show_obj.location, season_dir, "banner.jpg")

    def _show_data(self, show_obj):
        """
        Creates an elementTree XML structure for a MediaBrowser-style series.xml
        returns the resulting data object.

        show_obj: a TVShow instance to create the NFO for
        """

        tv_node = ElementTree.Element("Series")

        myShow = sickchill.indexer.series(show_obj)
        if not myShow:
            logger.exception("Unable to find show with id {} on {}, skipping it".format(show_obj.indexerid, show_obj.indexer_name))
            return False

        # check for title and id
        if not (getattr(myShow, "seriesName", None) and getattr(myShow, "id", None)):
            logger.info("Incomplete info for show with id {} on {}, skipping it".format(show_obj.indexerid, show_obj.indexer_name))
            return False

        data = getattr(myShow, "id", None)
        if data:
            indexerid = ElementTree.SubElement(tv_node, "id")
            indexerid.text = str(data)

        data = getattr(myShow, "seriesName", None)
        if data:
            SeriesName = ElementTree.SubElement(tv_node, "SeriesName")
            SeriesName.text = data

        data = getattr(myShow, "status", None)
        if data:
            Status = ElementTree.SubElement(tv_node, "Status")
            Status.text = data

        data = getattr(myShow, "network", None)
        if data:
            Network = ElementTree.SubElement(tv_node, "Network")
            Network.text = data

            Studios = ElementTree.SubElement(tv_node, "Studios")
            Studio = ElementTree.SubElement(Studios, "Studio")
            Studio.text = data

        data = getattr(myShow, "airsTime", None)
        if data:
            airsTime = ElementTree.SubElement(tv_node, "Airs_Time")
            airsTime.text = data

        data = getattr(myShow, "airsDayOfWeek", None)
        if data:
            airsDayOfWeek = ElementTree.SubElement(tv_node, "Airs_DayOfWeek")
            airsDayOfWeek.text = data

        data = getattr(myShow, "firstAired", None)
        if data:
            FirstAired = ElementTree.SubElement(tv_node, "FirstAired")
            FirstAired.text = data
            PremiereDate = ElementTree.SubElement(tv_node, "PremiereDate")
            PremiereDate.text = data
            try:
                year_text = str(datetime.datetime.strptime(data, dateFormat).year)
                if year_text:
                    ProductionYear = ElementTree.SubElement(tv_node, "ProductionYear")
                    ProductionYear.text = year_text
            except Exception:
                pass

        data = getattr(myShow, "rating", None)
        if data:
            ContentRating = ElementTree.SubElement(tv_node, "ContentRating")
            ContentRating.text = data

            MPAARating = ElementTree.SubElement(tv_node, "MPAARating")
            MPAARating.text = data

            certification = ElementTree.SubElement(tv_node, "certification")
            certification.text = data

            Rating = ElementTree.SubElement(tv_node, "Rating")
            Rating.text = data

        MetadataType = ElementTree.SubElement(tv_node, "Type")
        MetadataType.text = "Series"

        data = getattr(myShow, "overview", None)
        if data:
            Overview = ElementTree.SubElement(tv_node, "Overview")
            Overview.text = data

        data = getattr(myShow, "runtime", None)
        if data:
            RunningTime = ElementTree.SubElement(tv_node, "RunningTime")
            RunningTime.text = data

            Runtime = ElementTree.SubElement(tv_node, "Runtime")
            Runtime.text = data

        data = getattr(myShow, "imdbId", None)
        if data:
            imdb_id = ElementTree.SubElement(tv_node, "IMDB_ID")
            imdb_id.text = data

            imdb_id = ElementTree.SubElement(tv_node, "IMDB")
            imdb_id.text = data

            imdb_id = ElementTree.SubElement(tv_node, "IMDbId")
            imdb_id.text = data

        data = getattr(myShow, "zap2itId", None)
        if data:
            Zap2ItId = ElementTree.SubElement(tv_node, "Zap2ItId")
            Zap2ItId.text = data

        if getattr(myShow, "genre", []) and isinstance(myShow.genre, list):
            Genres = ElementTree.SubElement(tv_node, "Genres")
            for genre in myShow.genre:
                if genre.strip():
                    cur_genre = ElementTree.SubElement(Genres, "Genre")
                    cur_genre.text = genre.strip()

            Genre = ElementTree.SubElement(tv_node, "Genre")
            Genre.text = "|".join(myShow.genre)

        helpers.indentXML(tv_node)

        return ElementTree.ElementTree(tv_node)

    def _ep_data(self, ep_obj):
        """
        Creates an elementTree XML structure for a MediaBrowser style episode.xml
        and returns the resulting data object.

        show_obj: a TVShow instance to create the NFO for
        """

        eps_to_write = [ep_obj] + ep_obj.relatedEps

        persons_dict = {"Director": [], "GuestStar": [], "Writer": []}

        myShow = ep_obj.idxr.series_from_episode(ep_obj)
        if not myShow:
            logger.info("Unable to connect to {} while creating meta files - skipping".format(ep_obj.idxr.name))
            return False

        rootNode = ElementTree.Element("Item")

        # write an MediaBrowser XML containing info for all matching episodes
        for curEpToWrite in eps_to_write:

            myEp = curEpToWrite.idxr.episode(curEpToWrite)
            if not myEp:
                continue

            if curEpToWrite == ep_obj:
                # root (or single) episode

                # default to today's date for specials if firstAired is not set
                if ep_obj.airdate != datetime.date.min and myEp.get("firstAired"):
                    myEp["firstAired"] = str(ep_obj.airdate)

                if ep_obj.season == 0 and not myEp.get("firstAired"):
                    if ep_obj.show and ep_obj.show.startyear:
                        myEp["firstAired"] = str(datetime.date.min.replace(year=ep_obj.show.startyear))
                    else:
                        myEp["firstAired"] = str(datetime.date.today())

                if not (myEp.get("episodeName") and myEp.get("firstAired")):
                    return None

                episode = rootNode

                if curEpToWrite.name:
                    EpisodeName = ElementTree.SubElement(episode, "EpisodeName")
                    EpisodeName.text = curEpToWrite.name

                EpisodeNumber = ElementTree.SubElement(episode, "EpisodeNumber")
                EpisodeNumber.text = str(ep_obj.episode)

                if ep_obj.relatedEps:
                    try:
                        max_episode = max(e.episode for e in ep_obj.relatedEps if e)
                    except (AttributeError, TypeError):
                        max_episode = curEpToWrite.episode

                    EpisodeNumberEnd = ElementTree.SubElement(episode, "EpisodeNumberEnd")
                    EpisodeNumberEnd.text = str(max_episode)

                SeasonNumber = ElementTree.SubElement(episode, "SeasonNumber")
                SeasonNumber.text = str(curEpToWrite.season)

                if myEp.get("absoluteNumber") and not ep_obj.relatedEps:
                    absolute_number = ElementTree.SubElement(episode, "absolute_number")
                    absolute_number.text = str(myEp["absoluteNumber"])

                if curEpToWrite.airdate != datetime.date.min:
                    FirstAired = ElementTree.SubElement(episode, "FirstAired")
                    FirstAired.text = str(curEpToWrite.airdate)

                MetadataType = ElementTree.SubElement(episode, "Type")
                MetadataType.text = "Episode"

                if curEpToWrite.description:
                    Overview = ElementTree.SubElement(episode, "Overview")
                    Overview.text = curEpToWrite.description
                elif myEp.get("overview"):
                    Overview = ElementTree.SubElement(episode, "Overview")
                    Overview.text = myEp["overview"]

                if not ep_obj.relatedEps:
                    if myEp.get("rating"):
                        Rating = ElementTree.SubElement(episode, "Rating")
                        Rating.text = myEp["siteRating"]

                    if myEp.get("imdbId"):
                        IMDB_ID = ElementTree.SubElement(episode, "IMDB_ID")
                        IMDB_ID.text = myEp["imdbId"]

                        IMDB = ElementTree.SubElement(episode, "IMDB")
                        IMDB.text = myEp["imdbId"]

                        IMDbId = ElementTree.SubElement(episode, "IMDbId")
                        IMDbId.text = myEp["imdbId"]

                if myEp.get("id"):
                    indexerid = ElementTree.SubElement(episode, "id")
                    indexerid.text = str(myEp["id"])

                Persons = ElementTree.SubElement(episode, "Persons")

                for actor in ep_obj.idxr.actors(myShow):
                    if not ("name" in actor and actor["name"].strip()):
                        continue

                    cur_actor = ElementTree.SubElement(Persons, "Person")

                    cur_actor_name = ElementTree.SubElement(cur_actor, "Name")
                    cur_actor_name.text = actor["name"].strip()

                    cur_actor_type = ElementTree.SubElement(cur_actor, "Type")
                    cur_actor_type.text = "Actor"

                    if "role" in actor and actor["role"].strip():
                        cur_actor_role = ElementTree.SubElement(cur_actor, "Role")
                        cur_actor_role.text = actor["role"].strip()

                if myEp.get("language"):
                    language = myEp.get("language")["overview"]
                else:
                    language = settings.INDEXER_DEFAULT_LANGUAGE

                Language = ElementTree.SubElement(episode, "Language")
                Language.text = language

                if myEp.get("filename"):
                    thumb = ElementTree.SubElement(episode, "filename")
                    thumb.text = curEpToWrite.idxr.complete_image_url(myEp["filename"])

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

            # collect all directors, guest stars and writers
            if myEp.get("directors"):
                persons_dict["Director"] += myEp["directors"]
            if myEp.get("guestStars"):
                persons_dict["GuestStar"] += myEp["guestStars"]
            if myEp.get("writers"):
                persons_dict["Writer"] += myEp["writers"]

        # fill in Persons section with collected directors, guest starts and writers
        for person_type, names in persons_dict.items():
            # remove doubles
            names = list(set(names))
            for cur_name in names:
                Person = ElementTree.SubElement(Persons, "Person")
                cur_person_name = ElementTree.SubElement(Person, "Name")
                cur_person_name.text = cur_name
                cur_person_type = ElementTree.SubElement(Person, "Type")
                cur_person_type.text = person_type

        helpers.indentXML(rootNode)

        return ElementTree.ElementTree(rootNode)


# present a standard "interface" from the module
metadata_class = MediaBrowserMetadata
