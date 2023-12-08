import datetime
import os
import re
from xml.etree import ElementTree

from sickchill.helper.common import dateFormat, replace_extension
from sickchill.oldbeard import helpers

from ... import logger
from . import generic


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

        self.name = "WDTV"

        self._ep_nfo_extension = "xml"

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
    def get_episode_thumb_path(episode_object):
        """
        Returns the path where the episode thumbnail should be stored. Defaults to
        the same path as the episode file but with a .metathumb extension.

        episode_object: a TVEpisode instance for which to create the thumbnail
        """
        if os.path.isfile(episode_object.location):
            tbn_filename = replace_extension(episode_object.location, "metathumb")
        else:
            return None

        return tbn_filename

    @staticmethod
    def get_season_poster_path(show_obj, season):
        """
        Season thumbs for WDTV go in Show Dir/Season X/folder.jpg

        If no season folder exists, None is returned
        """

        dir_list = [x for x in os.listdir(show_obj.location) if os.path.isdir(os.path.join(show_obj.location, x))]

        season_dir_regex = r"^Season\s+(\d+)$"

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
            logger.debug(f"Unable to find a season dir for season {season}")
            return None

        logger.debug(f"Using {season_dir}/folder.jpg as season dir for season {season}")

        return os.path.join(show_obj.location, season_dir, "folder.jpg")

    def _ep_data(self, episode_object):
        """
        Creates an elementTree XML structure for a WDTV style episode.xml
        and returns the resulting data object.

        episode_object: a TVShow instance to create the NFO for
        """

        episodes_to_write = [episode_object] + episode_object.related_episodes

        indexer_show = episode_object.idxr.series_from_episode(episode_object)

        root_node = ElementTree.Element("details")

        # write an WDTV XML containing info for all matching episodes
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

            if episode_object.airdate != datetime.date.min and not indexer_episode.get("firstAired"):
                indexer_episode["firstAired"] = str(episode_object.airdate)

            if not (indexer_episode.get("episodeName") and indexer_episode.get("firstAired")):
                return None

            if len(episodes_to_write) > 1:
                episode_element = ElementTree.SubElement(root_node, "details")
            else:
                episode_element = root_node

            if indexer_episode.get("id"):
                id_element = ElementTree.SubElement(episode_element, "id")
                id_element.text = str(indexer_episode["id"])

            title_element = ElementTree.SubElement(episode_element, "title")
            title_element.text = episode_object.pretty_name

            if getattr(indexer_show, "seriesName", None):
                series_name_element = ElementTree.SubElement(episode_element, "series_name")
                series_name_element.text = indexer_show.seriesName

            if current_episode.name:
                episode_name_element = ElementTree.SubElement(episode_element, "episode_name")
                episode_name_element.text = current_episode.name

            season_number_element = ElementTree.SubElement(episode_element, "season_number")
            season_number_element.text = str(current_episode.season)

            episode_number_element = ElementTree.SubElement(episode_element, "episode_number")
            episode_number_element.text = str(current_episode.episode)

            first_aired_element = ElementTree.SubElement(episode_element, "firstAired")

            if current_episode.airdate != datetime.date.min:
                first_aired_element.text = str(current_episode.airdate)

            if getattr(indexer_show, "firstAired", None):
                try:
                    year_text = str(datetime.datetime.strptime(indexer_show.firstAired, dateFormat).year)
                    if year_text:
                        year_element = ElementTree.SubElement(episode_element, "year")
                        year_element.text = year_text
                except Exception:
                    pass

            if current_episode.season != 0 and getattr(indexer_show, "runtime", None):
                runtime_element = ElementTree.SubElement(episode_element, "runtime")
                runtime_element.text = indexer_show.runtime

            if getattr(indexer_show, "genre", None):
                genre_element = ElementTree.SubElement(episode_element, "genre")
                genre_element.text = " / ".join(indexer_show.genre)

            if indexer_episode.get("directors") and isinstance(indexer_episode["directors"], list):
                for director in indexer_episode["directors"]:
                    director_element = ElementTree.SubElement(episode_element, "director")
                    director_element.text = director

            data = episode_object.idxr.actors(indexer_show)
            for actor in data:
                if not ("name" in actor and actor["name"].strip()):
                    continue

                actor_element = ElementTree.SubElement(episode_element, "actor")

                actor_name_element = ElementTree.SubElement(actor_element, "name")
                actor_name_element.text = actor["name"]

                if "role" in actor and actor["role"].strip():
                    actor_role_element = ElementTree.SubElement(actor_element, "role")
                    actor_role_element.text = actor["role"].strip()

            if current_episode.description:
                overview_element = ElementTree.SubElement(episode_element, "overview")
                overview_element.text = current_episode.description

            # Make it purdy
            helpers.indentXML(root_node)
            data = ElementTree.ElementTree(root_node)

        return data


# present a standard "interface" from the module
metadata_class = WDTVMetadata
