import datetime
import re
from xml.etree import ElementTree

from babelfish import Country

import sickchill
from sickchill.helper.common import dateFormat
from sickchill.oldbeard import helpers

from ... import logger
from . import generic


class KODIMetadata(generic.GenericMetadata):
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

        self.name = "KODI"

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
        return {x.strip().title() for x in re.sub(r"[,/]+", "|", info_string).split("|") if x.strip()}

    def _show_data(self, show_obj):
        """
        Creates an elementTree XML structure for an KODI-style tvshow.nfo and
        returns the resulting data object.

        show_obj: a TVShow instance to create the NFO for
        """

        indexer_show = sickchill.indexer.series(show_obj)
        if not indexer_show:
            logger.info("Unable to find show with id {} on {}, skipping it".format(show_obj.indexerid, show_obj.idxr.name))
            return False

        # check for title and id
        if not (getattr(indexer_show, "seriesName", None) and getattr(indexer_show, "id", None)):
            logger.info("Incomplete info for show with id {} on {}, skipping it".format(show_obj.indexerid, show_obj.idxr.name))
            return False

        tvshow_element = ElementTree.Element("tvshow")

        title_element = ElementTree.SubElement(tvshow_element, "title")
        title_element.text = indexer_show.seriesName

        if getattr(indexer_show, "rating", None):
            mpaa_element = ElementTree.SubElement(tvshow_element, "mpaa")
            mpaa_element.text = str(indexer_show.rating)

        if getattr(indexer_show, "siteRating", None):
            rating_element = ElementTree.SubElement(tvshow_element, "rating")
            rating_element.text = str(indexer_show.siteRating)

        if getattr(indexer_show, "firstAired", None):
            try:
                year_text = str(datetime.datetime.strptime(indexer_show.firstAired, dateFormat).year)
                if year_text:
                    year = ElementTree.SubElement(tvshow_element, "year")
                    year.text = year_text
            except Exception:
                pass

        if getattr(indexer_show, "overview", None):
            plot_element = ElementTree.SubElement(tvshow_element, "plot")
            plot_element.text = indexer_show.overview

        if getattr(indexer_show, "id", None):
            episodeguide_element = ElementTree.SubElement(tvshow_element, "episodeguide")
            episodeguide_url_element = ElementTree.SubElement(episodeguide_element, "url")
            episodeguide_url_element.attrib = {"post": "yes", "cache": "auth.json"}
            episodeguide_url_element.text = show_obj.idxr.episode_guide_url(show_obj)

            indexerid_element = ElementTree.SubElement(tvshow_element, "id")
            indexerid_element.text = str(indexer_show.id)

            indexerid_element = ElementTree.SubElement(tvshow_element, "tvdbid")
            indexerid_element.text = str(indexer_show.id)

        if getattr(indexer_show, "genre", None) and isinstance(indexer_show.genre, list):
            for genre in indexer_show.genre:
                genre_element = ElementTree.SubElement(tvshow_element, "genre")
                genre_element.text = genre

        if show_obj.imdb_info.get("country_codes"):
            for country in self._split_info(show_obj.imdb_info["country_codes"]):
                try:
                    country_name = Country(country.upper()).name.title()
                except Exception:
                    continue

                country_element = ElementTree.SubElement(tvshow_element, "country")
                country_element.text = country_name

        if getattr(indexer_show, "firstAired", None):
            premiered_element = ElementTree.SubElement(tvshow_element, "premiered")
            premiered_element.text = indexer_show.firstAired

        if getattr(indexer_show, "network", None):
            studio_element = ElementTree.SubElement(tvshow_element, "studio")
            studio_element.text = indexer_show.network.strip()

        data = show_obj.idxr.actors(indexer_show)
        if data:
            for actor in data:
                actor_element = ElementTree.SubElement(tvshow_element, "actor")

                if "name" in actor and actor["name"].strip():
                    actor_name_element = ElementTree.SubElement(actor_element, "name")
                    actor_name_element.text = actor["name"].strip()
                else:
                    continue

                if "role" in actor and actor["role"].strip():
                    actor_role_element = ElementTree.SubElement(actor_element, "role")
                    actor_role_element.text = actor["role"].strip()

                if "image" in actor and actor["image"].strip():
                    actor_thumb_element = ElementTree.SubElement(actor_element, "thumb")
                    actor_thumb_element.text = show_obj.idxr.complete_image_url(actor["image"])

        # Make it purdy
        helpers.indentXML(tvshow_element)

        return ElementTree.ElementTree(tvshow_element)

    def _ep_data(self, episode_object):
        """
        Creates an elementTree XML structure for an KODI-style episode.nfo and
        returns the resulting data object.
            show_obj: a TVEpisode instance to create the NFO for
        """

        episodes_to_write = [episode_object] + episode_object.related_episodes

        indexer_show = episode_object.idxr.series_from_episode(episode_object)
        if not indexer_show:
            logger.info("Unable to find {} on {} while creating meta files, skipping".format(episode_object.show.indexerid, episode_object.idxr.name))
            return

        if len(episodes_to_write) > 1:
            root_node = ElementTree.Element("kodimultiepisode")
        else:
            root_node = ElementTree.Element("episodedetails")

        # write an NFO containing info for all matching episodes
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

            if not indexer_episode.get("episodeName"):
                logger.debug("Not generating nfo because the ep has no title")
                return None

            if not indexer_episode.get("firstAired"):
                logger.debug("Not generating nfo because the ep has no airdate")
                return None

            logger.debug(f"Creating metadata for episode {episode_object.episode_number}")

            if len(episodes_to_write) > 1:
                episode_element = ElementTree.SubElement(root_node, "episodedetails")
            else:
                episode_element = root_node

            if indexer_episode.get("episodeName"):
                title_element = ElementTree.SubElement(episode_element, "title")
                title_element.text = indexer_episode["episodeName"]

            if getattr(indexer_show, "seriesName", None):
                showtitle_element = ElementTree.SubElement(episode_element, "showtitle")
                showtitle_element.text = indexer_show.seriesName

            season_element = ElementTree.SubElement(episode_element, "season")
            season_element.text = str(current_episode.season)

            episode_number_element = ElementTree.SubElement(episode_element, "episode")
            episode_number_element.text = str(current_episode.episode)

            if indexer_episode.get("id"):
                uniqueid_element = ElementTree.SubElement(episode_element, "uniqueid")
                uniqueid_element.text = str(indexer_episode["id"])

            if current_episode.airdate != datetime.date.min:
                aired_element = ElementTree.SubElement(episode_element, "aired")
                aired_element.text = str(current_episode.airdate)

            if indexer_episode.get("overview"):
                plot_element = ElementTree.SubElement(episode_element, "plot")
                plot_element.text = indexer_episode["overview"]

            if current_episode.season and getattr(indexer_show, "runtime", None):
                runtime_element = ElementTree.SubElement(episode_element, "runtime")
                runtime_element.text = indexer_show.runtime

            if indexer_episode.get("airedSeason"):
                displayseason_element = ElementTree.SubElement(episode_element, "displayseason")
                displayseason_element.text = str(indexer_episode["airedSeason"])

            if indexer_episode.get("airedEpisodeNumber"):
                displayepisode_element = ElementTree.SubElement(episode_element, "displayepisode")
                displayepisode_element.text = str(indexer_episode["airedEpisodeNumber"])

            if indexer_episode.get("filename"):
                thumb_element = ElementTree.SubElement(episode_element, "thumb")
                thumb_element.text = episode_object.idxr.complete_image_url(indexer_episode["filename"])

            if indexer_episode.get("rating") is not None:
                rating_element = ElementTree.SubElement(episode_element, "rating")
                rating_element.text = str(indexer_episode["rating"])

            if indexer_episode.get("writers") and isinstance(indexer_episode["writers"], list):
                for writer in indexer_episode["writers"]:
                    writer_element = ElementTree.SubElement(episode_element, "credits")
                    writer_element.text = writer

            if indexer_episode.get("directors") and isinstance(indexer_episode["directors"], list):
                for director in indexer_episode["directors"]:
                    director_element = ElementTree.SubElement(episode_element, "director")
                    director_element.text = director

            if indexer_episode.get("guestStars") and isinstance(indexer_episode["guestStars"], list):
                for actor in indexer_episode["guestStars"]:
                    actor_element = ElementTree.SubElement(episode_element, "actor")
                    actor_name_element = ElementTree.SubElement(actor_element, "name")
                    actor_name_element.text = actor

            for actor in episode_object.idxr.actors(indexer_show):
                actor_element = ElementTree.SubElement(episode_element, "actor")

                if "name" in actor and actor["name"].strip():
                    actor_name_element = ElementTree.SubElement(actor_element, "name")
                    actor_name_element.text = actor["name"].strip()
                else:
                    continue

                if "role" in actor and actor["role"].strip():
                    actor_role_element = ElementTree.SubElement(actor_element, "role")
                    actor_role_element.text = actor["role"].strip()

                if "image" in actor and actor["image"].strip():
                    actor_thumb_element = ElementTree.SubElement(actor_element, "thumb")
                    actor_thumb_element.text = episode_object.idxr.complete_image_url(actor["image"])

        # Make it purdy
        helpers.indentXML(root_node)

        return ElementTree.ElementTree(root_node)


# present a standard "interface" from the module
metadata_class = KODIMetadata
