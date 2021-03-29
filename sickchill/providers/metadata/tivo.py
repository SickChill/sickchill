import datetime
import os

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

    def create_show_metadata(self, show_obj):
        pass

    def update_show_indexer_metadata(self, show_obj):
        pass

    def get_show_file_path(self, show_obj):
        pass

    def create_fanart(self, show_obj):
        pass

    def create_poster(self, show_obj):
        pass

    def create_banner(self, show_obj):
        pass

    def create_episode_thumb(self, ep_obj):
        pass

    @staticmethod
    def get_episode_thumb_path(ep_obj):
        pass

    def create_season_posters(self, ep_obj):
        pass

    def create_season_banners(self, ep_obj):
        pass

    def create_season_all_poster(self, show_obj):
        pass

    def create_season_all_banner(self, show_obj):
        pass

    # Override generic class
    def get_episode_file_path(self, ep_obj):
        """
        Returns a full show dir/.meta/episode.txt path for Tivo
        episode metadata files.

        Note, that pyTivo requires the metadata filename to include the original extention.

        ie If the episode name is foo.avi, the metadata name is foo.avi.txt

        ep_obj: a TVEpisode object to get the path for
        """
        if os.path.isfile(ep_obj.location):
            metadata_filename = os.path.basename(ep_obj.location) + "." + self._ep_nfo_extension
            metadata_dir_name = os.path.join(os.path.dirname(ep_obj.location), ".meta")
            metadata_file_path = os.path.join(metadata_dir_name, metadata_filename)
        else:
            logger.debug("Episode location doesn't exist: " + str(ep_obj.location))
            return ""
        return metadata_file_path

    def _ep_data(self, ep_obj):
        """
        Creates a key value structure for a Tivo episode metadata file and
        returns the resulting data object.

        ep_obj: a TVEpisode instance to create the metadata file for.

        The key values for the tivo metadata file are from:

        http://pytivo.sourceforge.net/wiki/index.php/Metadata
        """

        data = ""

        eps_to_write = [ep_obj] + ep_obj.relatedEps

        myShow = ep_obj.idxr.series_from_episode(ep_obj)
        if not myShow:
            logger.debug("Unable to connect to {} while creating meta files for {}, skipping".format(ep_obj.indexer_name, ep_obj.name))
            return False

        for curEpToWrite in eps_to_write:
            myEp = curEpToWrite.idxr.episode(curEpToWrite)
            if not myEp:
                logger.info(
                    "Metadata writer is unable to find episode {0:d}x{1:d} of {2} on {3}...has it been removed? Should I delete from db?".format(
                        curEpToWrite.season, curEpToWrite.episode, curEpToWrite.show.name, ep_obj.indexer_name
                    )
                )
                return False

            if ep_obj.airdate != datetime.date.min and not myEp.get("firstAired"):
                myEp["firstAired"] = str(ep_obj.airdate)

            if not (myEp.get("episodeName") and myEp.get("firstAired")):
                return None

            if myShow.seriesName:
                data += "title : " + myShow.seriesName + "\n"
                data += "seriesTitle : " + myShow.seriesName + "\n"

            # noinspection PyProtectedMember
            data += "episodeTitle : " + curEpToWrite._format_pattern("%Sx%0E %EN") + "\n"

            # This should be entered for episodic shows and omitted for movies. The standard tivo format is to enter
            # the season number followed by the episode number for that season. For example, enter 201 for season 2
            # episode 01.

            # This only shows up if you go into the Details from the Program screen.

            # This seems to disappear once the video is transferred to TiVo.

            # NOTE: May not be correct format, missing season, but based on description from wiki leaving as is.
            data += "episodeNumber : " + str(curEpToWrite.episode) + "\n"

            # Must be entered as true or false. If true, the year from originalAirDate will be shown in parentheses
            # after the episode's title and before the description on the Program screen.

            # FIXME: Hardcode isEpisode to true for now, not sure how to handle movies
            data += "isEpisode : true\n"

            # Write the synopsis of the video here
            # Micrsoft Word's smartquotes can die in a fire.
            sanitizedDescription = curEpToWrite.description
            # Replace double curly quotes
            sanitizedDescription = sanitizedDescription.replace("\u201c", '"').replace("\u201d", '"')
            # Replace single curly quotes
            sanitizedDescription = sanitizedDescription.replace("\u2018", "'").replace("\u2019", "'").replace("\u02BC", "'")

            data += "description : " + sanitizedDescription + "\n"

            # Usually starts with "SH" and followed by 6-8 digits.
            # Tivo uses zap2it for thier data, so the series id is the zap2itId.
            if getattr(myShow, "zap2itId", None):
                data += "seriesId : " + myShow.zap2itId + "\n"

            # This is the call sign of the channel the episode was recorded from.
            if getattr(myShow, "network", None):
                data += "callsign : " + myShow.network + "\n"

            # This must be entered as yyyy-mm-ddThh:mm:ssZ (the t is capitalized and never changes, the Z is also
            # capitalized and never changes). This is the original air date of the episode.
            # NOTE: Hard coded the time to T00:00:00Z as we really don't know when during the day the first run happened.
            if curEpToWrite.airdate != datetime.date.min:
                data += "originalAirDate : " + str(curEpToWrite.airdate) + "T00:00:00Z\n"

            # This shows up at the beginning of the description on the Program screen and on the Details screen.
            for actor in ep_obj.idxr.actors(myShow):
                if "name" in actor and actor["name"].strip():
                    data += "vActor : " + actor["name"].strip() + "\n"

            # This is shown on both the Program screen and the Details screen.
            if myEp.get("siteRating"):
                try:
                    rating = float(myEp["siteRating"])
                except ValueError:
                    rating = 0.0
                # convert 10 to 4 star rating. 4 * rating / 10
                # only whole numbers or half numbers work. multiply by 2, round, divide by 2.0
                rating = round(8 * rating / 10) / 2.0
                data += "starRating : " + str(rating) + "\n"

            # This is shown on both the Program screen and the Details screen.
            # It uses the standard TV rating system of: TV-Y7, TV-Y, TV-G, TV-PG, TV-14, TV-MA and TV-NR.
            if getattr(myShow, "rating", None):
                data += "tvRating : " + str(str(myShow.rating)) + "\n"

            # This field can be repeated as many times as necessary or omitted completely.
            if ep_obj.show.genre:
                for genre in ep_obj.show.genre:
                    if genre:
                        data += "vProgramGenre : " + str(genre) + "\n"

                        # NOTE: The following are metadata keywords are not used
                        # displayMajorNumber
                        # showingBits
                        # displayMinorNumber
                        # colorCode
                        # vSeriesGenre
                        # vGuestStar, vDirector, vExecProducer, vProducer, vWriter, vHost, vChoreographer
                        # partCount
                        # partIndex

        return data

    def write_ep_file(self, ep_obj):
        """
        Generates and writes ep_obj's metadata under the given path with the
        given filename root. Uses the episode's name with the extension in
        _ep_nfo_extension.

        ep_obj: TVEpisode object for which to create the metadata

        filename_path: The file name to use for this metadata. Note that the extension
                will be automatically added based on _ep_nfo_extension. This should
                include an absolute path.
        """
        data = self._ep_data(ep_obj)

        if not data:
            return False

        nfo_file_path = self.get_episode_file_path(ep_obj)
        nfo_file_dir = os.path.dirname(nfo_file_path)

        try:
            if not os.path.isdir(nfo_file_dir):
                logger.debug("Metadata dir didn't exist, creating it at " + nfo_file_dir)
                os.makedirs(nfo_file_dir)
                helpers.chmodAsParent(nfo_file_dir)

            logger.debug("Writing episode nfo file to " + nfo_file_path)

            data.write(nfo_file_path)
            helpers.chmodAsParent(nfo_file_path)

        except EnvironmentError as e:
            logger.error("Unable to write file to " + nfo_file_path + " - are you sure the folder is writable? " + str(e))
            return False

        return True


# present a standard "interface" from the module
metadata_class = TIVOMetadata
