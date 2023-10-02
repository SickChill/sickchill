import datetime
import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sickchill.tv import TVEpisode, TVShow

from sickchill.oldbeard import helpers

from ... import logger
from . import generic


class TIVOMetadata(generic.GenericMetadata):
    """
    Metadata generation class for TIVO

    The following file structure is used:

    show_root/Season ##/filename.ext            (*)
    show_root/Season ##/.meta/filename.ext.txt  (episode metadata)

    This class only generates episode specific metadata files, it does NOT generate a default.txt file.
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

        self.name = "TIVO"

        self._ep_nfo_extension = "txt"

        # web-ui metadata template
        self.eg_show_metadata = "<i>not supported</i>"
        self.eg_episode_metadata = "Season##\\.meta\\<i>filename</i>.ext.txt"
        self.eg_fanart = "<i>not supported</i>"
        self.eg_poster = "<i>not supported</i>"
        self.eg_banner = "<i>not supported</i>"
        self.eg_episode_thumbnails = "<i>not supported</i>"
        self.eg_season_posters = "<i>not supported</i>"
        self.eg_season_banners = "<i>not supported</i>"
        self.eg_season_all_poster = "<i>not supported</i>"
        self.eg_season_all_banner = "<i>not supported</i>"

    # Override with empty methods for unsupported features
    def retrieveShowMetadata(self, folder):
        # no show metadata generated, we abort this lookup function
        return None, None, None

    def create_show_metadata(self, show_obj: "TVShow"):
        pass

    def update_episode_metadata(self, episode_object: "TVEpisode"):
        if self.episode_metadata and episode_object:
            logger.debug(f"[{self.name} META] Updating episode metadata for {episode_object.pretty_name}")
            return self.write_ep_file(episode_object)
        return False

    def update_show_indexer_metadata(self, show_obj: "TVShow"):
        pass

    def get_show_file_path(self, show_obj: "TVShow"):
        pass

    def create_fanart(self, show_obj: "TVShow"):
        pass

    def create_poster(self, show_obj: "TVShow"):
        pass

    def create_banner(self, show_obj: "TVShow"):
        pass

    def create_episode_thumb(self, episode_object: "TVEpisode"):
        pass

    @staticmethod
    def get_episode_thumb_path(episode_object: "TVEpisode"):
        pass

    def create_season_posters(self, episode_object: "TVEpisode"):
        pass

    def create_season_banners(self, episode_object: "TVEpisode"):
        pass

    def create_season_all_poster(self, show_obj: "TVShow"):
        pass

    def create_season_all_banner(self, show_obj: "TVShow"):
        pass

    # Override generic class
    def get_episode_file_path(self, episode_object: "TVEpisode"):
        """
        Returns a full show dir/.meta/episode.txt path for Tivo
        episode metadata files.

        Note, that pyTivo requires the metadata filename to include the original extention.

        ie If the episode name is foo.avi, the metadata name is foo.avi.txt

        episode_object: a TVEpisode object to get the path for
        """
        if os.path.isfile(episode_object.location):
            metadata_filename = os.path.basename(episode_object.location) + "." + self._ep_nfo_extension
            metadata_dir_name = os.path.join(os.path.dirname(episode_object.location), ".meta")
            metadata_file_path = os.path.join(metadata_dir_name, metadata_filename)
        else:
            logger.debug(f"[{self.name} META] Episode location doesn't exist: {episode_object.location}")
            return ""
        return metadata_file_path

    def episode_pretty_title(self, episode_object: "TVEpisode"):
        """
        Returns the name of this episode in a "pretty" human-readable format

        Returns: A string representing the episode's name and season/ep numbers
        """

        if episode_object.show.anime and not episode_object.show.scene:
            return episode_object.naming_pattern("%AB - %EN")
        elif episode_object.show.air_by_date:
            return episode_object.naming_pattern("%AD - %EN")

        return episode_object.naming_pattern("S%0SE%0E - %EN")

    def _ep_data(self, episode_object: "TVEpisode"):
        """
        Creates a key value structure for a Tivo episode metadata file and
        returns the resulting data object.

        episode_object: a TVEpisode instance to create the metadata file for.

        The key values for the tivo metadata file are from:

        https://pytivo.sourceforge.net/wiki/index.php/Metadata
        """

        data = []

        eps_to_write = [episode_object] + episode_object.related_episodes

        indexer_show = episode_object.idxr.series_from_episode(episode_object)
        if not indexer_show:
            logger.debug("Unable to connect to {} while creating meta files for {}, skipping".format(episode_object.indexer_name, episode_object.name))
            return False

        for curEpToWrite in eps_to_write:
            indexer_episode = curEpToWrite.idxr.episode(curEpToWrite)
            if not indexer_episode:
                logger.info(
                    "Metadata writer is unable to find episode {0:d}x{1:d} of {2} on {3}...has it been removed? Should I delete from db?".format(
                        curEpToWrite.season, curEpToWrite.episode, curEpToWrite.show.name, episode_object.indexer_name
                    )
                )
                return False

            if episode_object.airdate != datetime.date.min and not indexer_episode.get("firstAired"):
                indexer_episode["firstAired"] = str(episode_object.airdate)

            if not (indexer_episode.get("episodeName") and indexer_episode.get("firstAired")):
                return None

            if indexer_show.seriesName:
                data.append(f"title : {indexer_show.seriesName}")
                data.append(f"seriesTitle : {indexer_show.seriesName}")

            # noinspection PyProtectedMember
            data.append(f"episodeTitle : {self.episode_pretty_title(curEpToWrite)}")

            # This should be entered for episodic shows and omitted for movies. The standard tivo format is to enter
            # the season number followed by the episode number for that season. For example, enter 201 for season 2
            # episode 01.

            # This only shows up if you go into the Details from the Program screen.

            # This seems to disappear once the video is transferred to TiVo.

            # NOTE: May not be correct format, missing season, but based on description from wiki leaving as is.
            data.append(f"episodeNumber : {curEpToWrite.episode}")

            # Must be entered as true or false. If true, the year from originalAirDate will be shown in parentheses
            # after the episode's title and before the description on the Program screen.

            # FIXME: Hardcode isEpisode to true for now, not sure how to handle movies
            data.append("isEpisode : true")

            # Write the synopsis of the video here
            # Micrsoft Word's smartquotes can die in a fire.
            sanitizedDescription = curEpToWrite.description
            # Replace double curly quotes
            sanitizedDescription = sanitizedDescription.replace("\u201c", '"').replace("\u201d", '"')
            # Replace single curly quotes
            sanitizedDescription = sanitizedDescription.replace("\u2018", "'").replace("\u2019", "'").replace("\u02BC", "'")

            data.append(f"description : {sanitizedDescription}")

            # Usually starts with "SH" and followed by 6-8 digits.
            # Tivo uses zap2it for thier data, so the series id is the zap2itId.
            if getattr(indexer_show, "zap2itId", None):
                data.append(f"seriesId : {indexer_show.zap2itId}")

            # This is the call sign of the channel the episode was recorded from.
            if getattr(indexer_show, "network", None):
                data.append(f"callsign : {indexer_show.network}")

            # This must be entered as yyyy-mm-ddThh:mm:ssZ (the t is capitalized and never changes, the Z is also
            # capitalized and never changes). This is the original air date of the episode.
            # NOTE: Hard coded the time to T00:00:00Z as we really don't know when during the day the first run happened.
            if curEpToWrite.airdate != datetime.date.min:
                data.append(f"originalAirDate : {curEpToWrite.airdate}T00:00:00Z")

            # This shows up at the beginning of the description on the Program screen and on the Details screen.
            for actor in episode_object.idxr.actors(indexer_show):
                actor_name = actor.get("name", "").strip()
                if actor_name:
                    data.append(f"vActor : {actor_name}")

            # This is shown on both the Program screen and the Details screen.
            if indexer_episode.get("siteRating"):
                try:
                    rating = float(indexer_episode["siteRating"])
                except ValueError:
                    rating = 0.0
                # convert 10 to 4 star rating. 4 * rating / 10
                # only whole numbers or half numbers work. multiply by 2, round, divide by 2.0
                rating = round(8 * rating / 10) / 2.0
                data.append(f"starRating : {rating}")

            # This is shown on both the Program screen and the Details screen.
            # It uses the standard TV rating system of: TV-Y7, TV-Y, TV-G, TV-PG, TV-14, TV-MA and TV-NR.
            if getattr(indexer_show, "rating", None):
                data.append(f"tvRating : {indexer_show.rating}")

            # This field can be repeated as many times as necessary or omitted completely.
            if episode_object.show.genre:
                for genre in episode_object.show.genre:
                    if genre:
                        data.append(f"vProgramGenre : {genre}")

                        # NOTE: The following are metadata keywords are not used
                        # displayMajorNumber
                        # showingBits
                        # displayMinorNumber
                        # colorCode
                        # vSeriesGenre
                        # vGuestStar, vDirector, vExecProducer, vProducer, vWriter, vHost, vChoreographer
                        # partCount
                        # partIndex

        return "\n".join(data)

    def write_ep_file(self, episode_object: "TVEpisode"):
        """
        Generates and writes episode_object's metadata under the given path with the
        given filename root. Uses the episode's name with the extension in
        _ep_nfo_extension.

        episode_object: TVEpisode object for which to create the metadata

        filename_path: The file name to use for this metadata. Note that the extension
                will be automatically added based on _ep_nfo_extension. This should
                include an absolute path.
        """
        data = self._ep_data(episode_object)

        if not data:
            return False

        nfo_file_path = self.get_episode_file_path(episode_object)
        nfo_file_dir = os.path.dirname(nfo_file_path)

        try:
            if not os.path.isdir(nfo_file_dir):
                logger.debug("Metadata dir didn't exist, creating it at " + nfo_file_dir)
                os.makedirs(nfo_file_dir)
                helpers.chmodAsParent(nfo_file_dir)

            logger.debug("Writing episode nfo file to " + nfo_file_path)

            with open(nfo_file_path, "w") as nfo_file:
                nfo_file.write(data)

            helpers.chmodAsParent(nfo_file_path)

        except EnvironmentError as error:
            logger.error(f"Unable to write file to {nfo_file_path} - are you sure the folder is writable? {error}")
            return False

        return True


# present a standard "interface" from the module
metadata_class = TIVOMetadata
