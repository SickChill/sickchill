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

    def get_episode_file_path(self, episode_object):
        """
        Returns a full show dir/metadata/episode.xml path for MediaBrowser
        episode metadata files

        episode_object: a TVEpisode object to get the path for
        """

        if os.path.isfile(episode_object.location):
            xml_filename = replace_extension(os.path.basename(episode_object.location), self._ep_nfo_extension)
            metadata_dir_name = os.path.join(os.path.dirname(episode_object.location), "metadata")
            xml_file_path = os.path.join(metadata_dir_name, xml_filename)
        else:
            logger.debug(f"[{self.name} META] Episode location doesn't exist: {episode_object.location}")
            return ""

        return xml_file_path

    @staticmethod
    def get_episode_thumb_path(episode_object):
        """
        Returns a full show dir/metadata/episode.jpg path for MediaBrowser
        episode thumbs.

        episode_object: a TVEpisode object to get the path from
        """

        if os.path.isfile(episode_object.location):
            tbn_filename = replace_extension(os.path.basename(episode_object.location), "jpg")
            metadata_dir_name = os.path.join(os.path.dirname(episode_object.location), "metadata")
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
            logger.debug(f"Unable to find a season dir for season {season}")
            return None

        logger.debug(f"Using {season_dir}/folder.jpg as season dir for season {season}")

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
            logger.debug(f"Unable to find a season dir for season {season}")
            return None

        logger.debug(f"Using {season_dir}/banner.jpg as season dir for season {season}")

        return os.path.join(show_obj.location, season_dir, "banner.jpg")

    def _show_data(self, show_obj):
        """
        Creates an elementTree XML structure for a MediaBrowser-style series.xml
        returns the resulting data object.

        show_obj: a TVShow instance to create the NFO for
        """

        indexer_show = sickchill.indexer.series(show_obj)
        if not indexer_show:
            logger.exception("Unable to find show with id {} on {}, skipping it".format(show_obj.indexerid, show_obj.indexer_name))
            return False

        # check for title and id
        if not (getattr(indexer_show, "seriesName", None) and getattr(indexer_show, "id", None)):
            logger.info("Incomplete info for show with id {} on {}, skipping it".format(show_obj.indexerid, show_obj.indexer_name))
            return False

        tv_node = ElementTree.Element("Series")

        data = getattr(indexer_show, "id", None)
        if data:
            indexerid_element = ElementTree.SubElement(tv_node, "id")
            indexerid_element.text = str(data)

        data = getattr(indexer_show, "seriesName", None)
        if data:
            series_name_element = ElementTree.SubElement(tv_node, "SeriesName")
            series_name_element.text = data

        data = getattr(indexer_show, "status", None)
        if data:
            status_element = ElementTree.SubElement(tv_node, "Status")
            status_element.text = data

        data = getattr(indexer_show, "network", None)
        if data:
            network_element = ElementTree.SubElement(tv_node, "Network")
            network_element.text = data

            studios_element = ElementTree.SubElement(tv_node, "Studios")
            studio_element = ElementTree.SubElement(studios_element, "Studio")
            studio_element.text = data

        data = getattr(indexer_show, "airsTime", None)
        if data:
            airs_time_element = ElementTree.SubElement(tv_node, "Airs_Time")
            airs_time_element.text = data

        data = getattr(indexer_show, "airsDayOfWeek", None)
        if data:
            airs_day_element = ElementTree.SubElement(tv_node, "Airs_DayOfWeek")
            airs_day_element.text = data

        data = getattr(indexer_show, "firstAired", None)
        if data:
            first_aired_element = ElementTree.SubElement(tv_node, "FirstAired")
            first_aired_element.text = data
            premier_date_element = ElementTree.SubElement(tv_node, "PremiereDate")
            premier_date_element.text = data
            try:
                year_text = str(datetime.datetime.strptime(data, dateFormat).year)
                if year_text:
                    production_year_element = ElementTree.SubElement(tv_node, "ProductionYear")
                    production_year_element.text = year_text
            except Exception:
                pass

        data = getattr(indexer_show, "rating", None)
        if data:
            content_rating_element = ElementTree.SubElement(tv_node, "ContentRating")
            content_rating_element.text = data

            mpaa_rating_element = ElementTree.SubElement(tv_node, "MPAARating")
            mpaa_rating_element.text = data

            certification_element = ElementTree.SubElement(tv_node, "certification")
            certification_element.text = data

            rating_element = ElementTree.SubElement(tv_node, "Rating")
            rating_element.text = data

        type_element = ElementTree.SubElement(tv_node, "Type")
        type_element.text = "Series"

        data = getattr(indexer_show, "overview", None)
        if data:
            overview_element = ElementTree.SubElement(tv_node, "Overview")
            overview_element.text = data

        data = getattr(indexer_show, "runtime", None)
        if data:
            running_time_element = ElementTree.SubElement(tv_node, "RunningTime")
            running_time_element.text = data

            runtime_element = ElementTree.SubElement(tv_node, "Runtime")
            runtime_element.text = data

        data = getattr(indexer_show, "imdbId", None)
        if data:
            imdb_id_element = ElementTree.SubElement(tv_node, "IMDB_ID")
            imdb_id_element.text = data

            imdb_id_element = ElementTree.SubElement(tv_node, "IMDB")
            imdb_id_element.text = data

            imdb_id_element = ElementTree.SubElement(tv_node, "IMDbId")
            imdb_id_element.text = data

        data = getattr(indexer_show, "zap2itId", None)
        if data:
            zap2itid_element = ElementTree.SubElement(tv_node, "Zap2ItId")
            zap2itid_element.text = data

        if getattr(indexer_show, "genre", []) and isinstance(indexer_show.genre, list):
            genres_element = ElementTree.SubElement(tv_node, "Genres")
            for genre in indexer_show.genre:
                if genre.strip():
                    genre_element = ElementTree.SubElement(genres_element, "Genre")
                    genre_element.text = genre.strip()

            genre_element = ElementTree.SubElement(tv_node, "Genre")
            genre_element.text = "|".join(indexer_show.genre)

        helpers.indentXML(tv_node)

        return ElementTree.ElementTree(tv_node)

    def _ep_data(self, episode_object):
        """
        Creates an elementTree XML structure for a MediaBrowser style episode.xml
        and returns the resulting data object.

        show_obj: a TVShow instance to create the NFO for
        """

        episodes_to_write = [episode_object] + episode_object.related_episodes

        persons_dict = {"Director": [], "GuestStar": [], "Writer": []}

        indexer_show = episode_object.idxr.series_from_episode(episode_object)
        if not indexer_show:
            logger.info("Unable to connect to {} while creating meta files - skipping".format(episode_object.idxr.name))
            return False

        root_node = ElementTree.Element("Item")

        # write an MediaBrowser XML containing info for all matching episodes
        for current_episode in episodes_to_write:
            indexer_episode = current_episode.idxr.episode(current_episode)
            if not indexer_episode:
                continue

            if current_episode == episode_object:
                # root (or single) episode

                # default to today's date for specials if firstAired is not set
                if episode_object.airdate != datetime.date.min and indexer_episode.get("firstAired"):
                    indexer_episode["firstAired"] = str(episode_object.airdate)

                if episode_object.season == 0 and not indexer_episode.get("firstAired"):
                    if episode_object.show and episode_object.show.startyear:
                        indexer_episode["firstAired"] = str(datetime.date.min.replace(year=episode_object.show.startyear))
                    else:
                        indexer_episode["firstAired"] = str(datetime.date.today())

                if not (indexer_episode.get("episodeName") and indexer_episode.get("firstAired")):
                    return None

                episode = root_node

                if current_episode.name:
                    episode_name_element = ElementTree.SubElement(episode, "EpisodeName")
                    episode_name_element.text = current_episode.name

                episode_number_element = ElementTree.SubElement(episode, "EpisodeNumber")
                episode_number_element.text = str(episode_object.episode)

                if episode_object.related_episodes:
                    try:
                        max_episode = max(e.episode for e in episode_object.related_episodes if e)
                    except (AttributeError, TypeError):
                        max_episode = current_episode.episode

                    episode_number_end_element = ElementTree.SubElement(episode, "EpisodeNumberEnd")
                    episode_number_end_element.text = str(max_episode)

                season_number_element = ElementTree.SubElement(episode, "SeasonNumber")
                season_number_element.text = str(current_episode.season)

                if indexer_episode.get("absoluteNumber") and not episode_object.related_episodes:
                    absolute_number_element = ElementTree.SubElement(episode, "absolute_number")
                    absolute_number_element.text = str(indexer_episode["absoluteNumber"])

                if current_episode.airdate != datetime.date.min:
                    first_aired_element = ElementTree.SubElement(episode, "FirstAired")
                    first_aired_element.text = str(current_episode.airdate)

                type_element = ElementTree.SubElement(episode, "Type")
                type_element.text = "Episode"

                if current_episode.description:
                    overview_element = ElementTree.SubElement(episode, "Overview")
                    overview_element.text = current_episode.description
                elif indexer_episode.get("overview"):
                    overview_element = ElementTree.SubElement(episode, "Overview")
                    overview_element.text = indexer_episode["overview"]

                if not episode_object.related_episodes:
                    if indexer_episode.get("rating"):
                        rating_element = ElementTree.SubElement(episode, "Rating")
                        rating_element.text = indexer_episode["siteRating"]

                    if indexer_episode.get("imdbId"):
                        imdb_id_element = ElementTree.SubElement(episode, "IMDB_ID")
                        imdb_id_element.text = indexer_episode["imdbId"]

                        imdb_element = ElementTree.SubElement(episode, "IMDB")
                        imdb_element.text = indexer_episode["imdbId"]

                        imdbid_element = ElementTree.SubElement(episode, "IMDbId")
                        imdbid_element.text = indexer_episode["imdbId"]

                if indexer_episode.get("id"):
                    id_element = ElementTree.SubElement(episode, "id")
                    id_element.text = str(indexer_episode["id"])

                persons_element = ElementTree.SubElement(episode, "Persons")

                for actor in episode_object.idxr.actors(indexer_show):
                    if not ("name" in actor and actor["name"].strip()):
                        continue

                    actor_element = ElementTree.SubElement(persons_element, "Person")

                    actor_name_element = ElementTree.SubElement(actor_element, "Name")
                    actor_name_element.text = actor["name"].strip()

                    actor_type_element = ElementTree.SubElement(actor_element, "Type")
                    actor_type_element.text = "Actor"

                    if "role" in actor and actor["role"].strip():
                        actor_role_element = ElementTree.SubElement(actor_element, "Role")
                        actor_role_element.text = actor["role"].strip()

                if indexer_episode.get("language"):
                    language = indexer_episode.get("language")["overview"]
                else:
                    language = settings.INDEXER_DEFAULT_LANGUAGE

                language_element = ElementTree.SubElement(episode, "Language")
                language_element.text = language

                if indexer_episode.get("filename"):
                    thumb_element = ElementTree.SubElement(episode, "filename")
                    thumb_element.text = current_episode.idxr.complete_image_url(indexer_episode["filename"])

            else:
                # append data from (if any) related episodes
                if current_episode.name:
                    if not episode_name_element.text:
                        episode_name_element.text = current_episode.name
                    else:
                        episode_name_element.text = episode_name_element.text + ", " + current_episode.name

                if current_episode.description:
                    if not overview_element.text:
                        overview_element.text = current_episode.description
                    else:
                        overview_element.text = overview_element.text + "\r" + current_episode.description

            # collect all directors, guest stars and writers
            if indexer_episode.get("directors"):
                persons_dict["Director"] += indexer_episode["directors"]
            if indexer_episode.get("guestStars"):
                persons_dict["GuestStar"] += indexer_episode["guestStars"]
            if indexer_episode.get("writers"):
                persons_dict["Writer"] += indexer_episode["writers"]

        # fill in Persons section with collected directors, guest starts and writers
        for person_type, names in persons_dict.items():
            # remove doubles
            names = list(set(names))
            for cur_name in names:
                person_element = ElementTree.SubElement(persons_element, "Person")
                person_name_element = ElementTree.SubElement(person_element, "Name")
                person_name_element.text = cur_name
                person_type_element = ElementTree.SubElement(person_element, "Type")
                person_type_element.text = person_type

        helpers.indentXML(root_node)

        return ElementTree.ElementTree(root_node)


# present a standard "interface" from the module
metadata_class = MediaBrowserMetadata
