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
    def get_episode_thumb_path(ep_obj):
        """
        Returns the path where the episode thumbnail should be stored. Defaults to
        the same path as the episode file but with a .metathumb extension.

        ep_obj: a TVEpisode instance for which to create the thumbnail
        """
        if os.path.isfile(ep_obj.location):
            tbn_filename = replace_extension(ep_obj.location, "metathumb")
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
            logger.debug("Unable to find a season dir for season " + str(season))
            return None

        logger.debug("Using " + str(season_dir) + "/folder.jpg as season dir for season " + str(season))

        return os.path.join(show_obj.location, season_dir, "folder.jpg")

    def _ep_data(self, ep_obj):
        """
        Creates an elementTree XML structure for a WDTV style episode.xml
        and returns the resulting data object.

        ep_obj: a TVShow instance to create the NFO for
        """

        eps_to_write = [ep_obj] + ep_obj.relatedEps

        myShow = ep_obj.idxr.series_from_episode(ep_obj)

        rootNode = ElementTree.Element("details")

        # write an WDTV XML containing info for all matching episodes
        for curEpToWrite in eps_to_write:
            myEp = curEpToWrite.idxr.episode(curEpToWrite)
            if not myEp:
                logger.info(
                    "Metadata writer is unable to find episode {0:d}x{1:d} of {2} on {3}..."
                    "has it been removed? Should I delete from db?".format(curEpToWrite.season, curEpToWrite.episode, curEpToWrite.show.name, ep_obj.idxr.name)
                )
                return None

            if ep_obj.airdate != datetime.date.min and not myEp.get("firstAired"):
                myEp["firstAired"] = str(ep_obj.airdate)

            if not (myEp.get("episodeName") and myEp.get("firstAired")):
                return None

            if len(eps_to_write) > 1:
                episode = ElementTree.SubElement(rootNode, "details")
            else:
                episode = rootNode

            if myEp.get("id"):
                episodeID = ElementTree.SubElement(episode, "id")
                episodeID.text = str(myEp["id"])

            title = ElementTree.SubElement(episode, "title")
            title.text = ep_obj.pretty_name

            if getattr(myShow, "seriesName", None):
                seriesName = ElementTree.SubElement(episode, "series_name")
                seriesName.text = myShow.seriesName

            if curEpToWrite.name:
                episodeName = ElementTree.SubElement(episode, "episode_name")
                episodeName.text = curEpToWrite.name

            seasonNumber = ElementTree.SubElement(episode, "season_number")
            seasonNumber.text = str(curEpToWrite.season)

            episodeNum = ElementTree.SubElement(episode, "episode_number")
            episodeNum.text = str(curEpToWrite.episode)

            firstAired = ElementTree.SubElement(episode, "firstAired")

            if curEpToWrite.airdate != datetime.date.min:
                firstAired.text = str(curEpToWrite.airdate)

            if getattr(myShow, "firstAired", None):
                try:
                    year_text = str(datetime.datetime.strptime(myShow.firstAired, dateFormat).year)
                    if year_text:
                        year = ElementTree.SubElement(episode, "year")
                        year.text = year_text
                except Exception:
                    pass

            if curEpToWrite.season != 0 and getattr(myShow, "runtime", None):
                runtime = ElementTree.SubElement(episode, "runtime")
                runtime.text = myShow.runtime

            if getattr(myShow, "genre", None):
                genre = ElementTree.SubElement(episode, "genre")
                genre.text = " / ".join(myShow.genre)

            if myEp.get("directors") and isinstance(myEp["directors"], list):
                for director in myEp["directors"]:
                    director_element = ElementTree.SubElement(episode, "director")
                    director_element.text = director

            data = ep_obj.idxr.actors(myShow)
            for actor in data:
                if not ("name" in actor and actor["name"].strip()):
                    continue

                cur_actor = ElementTree.SubElement(episode, "actor")

                cur_actor_name = ElementTree.SubElement(cur_actor, "name")
                cur_actor_name.text = actor["name"]

                if "role" in actor and actor["role"].strip():
                    cur_actor_role = ElementTree.SubElement(cur_actor, "role")
                    cur_actor_role.text = actor["role"].strip()

            if curEpToWrite.description:
                overview = ElementTree.SubElement(episode, "overview")
                overview.text = curEpToWrite.description

            # Make it purdy
            helpers.indentXML(rootNode)
            data = ElementTree.ElementTree(rootNode)

        return data


# present a standard "interface" from the module
metadata_class = WDTVMetadata
