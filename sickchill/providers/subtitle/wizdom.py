import bisect
import io
import logging
import os
import zipfile

from babelfish import Language
from guessit import guessit
from requests import Session
from subliminal.cache import region, SHOW_EXPIRATION_TIME
from subliminal.exceptions import ProviderError
from subliminal.matches import guess_matches
from subliminal.providers import Provider
from subliminal.subtitle import fix_line_ending, Subtitle
from subliminal.utils import sanitize
from subliminal.video import Episode, Movie

from sickchill import settings

logger = logging.getLogger(__name__)


class WizdomSubtitle(Subtitle):
    """Wizdom Subtitle."""

    provider_name = "wizdom"

    def __init__(self, language, hearing_impaired, page_link, series, season, episode, title, imdb_id, subtitle_id, releases):
        super().__init__(language, hearing_impaired, page_link)
        self.series = series
        self.season = season
        self.episode = episode
        self.title = title
        self.imdb_id = imdb_id
        self.subtitle_id = subtitle_id
        self.downloaded = 0
        self.releases = releases

    @property
    def id(self):
        return str(self.subtitle_id)

    def get_matches(self, video):
        matches = set()

        # episode
        if isinstance(video, Episode):
            # series
            if video.series and sanitize(self.series) == sanitize(video.series):
                matches.add("series")
            # season
            if video.season and self.season == video.season:
                matches.add("season")
            # episode
            if video.episode and self.episode == video.episode:
                matches.add("episode")
            # imdb_id
            if video.series_imdb_id and self.imdb_id == video.series_imdb_id:
                matches.add("series_imdb_id")
            # guess
            for release in self.releases:
                matches |= guess_matches(video, guessit(release, {"type": "episode"}))
        # movie
        elif isinstance(video, Movie):
            # guess
            for release in self.releases:
                matches |= guess_matches(video, guessit(release, {"type": "movie"}))

        # title
        if video.title and sanitize(self.title) == sanitize(video.title):
            matches.add("title")

        return matches


class WizdomProvider(Provider):
    """Wizdom Provider."""

    languages = {Language.fromalpha2(l) for l in ["he"]}
    server_url = "wizdom.xyz"

    def __init__(self):
        self.session = None

    def initialize(self):
        self.session = Session()

    def terminate(self):
        self.session.close()

    @region.cache_on_arguments(expiration_time=SHOW_EXPIRATION_TIME)
    def _search_imdb_id(self, title, year, is_movie):
        """Search the IMDB ID for the given `title` and `year`.

        :param str title: title to search for.
        :param int year: year to search for (or 0 if not relevant).
        :param bool is_movie: If True, IMDB ID will be searched for in TMDB instead of Wizdom.
        :return: the IMDB ID for the given title and year (or None if not found).
        :rtype: str

        """
        # make the search
        logger.info("Searching IMDB ID for %r%r", title, "" if not year else " ({})".format(year))
        category = "movie" if is_movie else "tv"
        title = title.replace("'", "")
        # get TMDB ID first
        r = self.session.get(
            "http://api.tmdb.org/3/search/{}?api_key={}&query={}{}&language=en".format(
                category, settings.TMDB_API_KEY, title, "" if not year else "&year={}".format(year)
            )
        )
        r.raise_for_status()
        tmdb_results = r.json().get("results")
        if tmdb_results:
            tmdb_id = tmdb_results[0].get("id")
            if tmdb_id:
                # get actual IMDB ID from TMDB
                r = self.session.get(
                    "http://api.tmdb.org/3/{}/{}{}?api_key={}&language=en".format(category, tmdb_id, "" if is_movie else "/external_ids", settings.TMDB_API_KEY)
                )
                r.raise_for_status()
                return str(r.json().get("imdb_id", "")) or None
        return None

    def query(self, title, season=None, episode=None, year=None, filename=None, imdb_id=None):
        # search for the IMDB ID if needed.
        is_movie = not (season and episode)
        imdb_id = imdb_id or self._search_imdb_id(title, year, is_movie)
        if not imdb_id:
            return {}

        # search
        logger.debug("Using IMDB ID %r", imdb_id)
        url = "http://json.{}/{}.json".format(self.server_url, imdb_id)
        page_link = "http://{}/#/{}/{}".format(self.server_url, "movies" if is_movie else "series", imdb_id)

        # get the list of subtitles
        logger.debug("Getting the list of subtitles")
        r = self.session.get(url)
        r.raise_for_status()
        try:
            results = r.json()
        except ValueError:
            return {}

        # filter irrelevant results
        if not is_movie:
            results = results.get("subs", {}).get(str(season), {}).get(str(episode), [])
        else:
            results = results.get("subs", [])

        # loop over results
        subtitles = {}
        for result in results:
            language = Language.fromalpha2("he")
            hearing_impaired = False
            subtitle_id = result["id"]
            release = result["version"]

            # add the release and increment downloaded count if we already have the subtitle
            if subtitle_id in subtitles:
                logger.debug("Found additional release %r for subtitle %d", release, subtitle_id)
                bisect.insort_left(subtitles[subtitle_id].releases, release)  # deterministic order
                subtitles[subtitle_id].downloaded += 1
                continue

            # otherwise create it
            subtitle = WizdomSubtitle(language, hearing_impaired, page_link, title, season, episode, title, imdb_id, subtitle_id, [release])
            logger.debug("Found subtitle %r", subtitle)
            subtitles[subtitle_id] = subtitle

        return list(subtitles.values())

    def list_subtitles(self, video: Episode, languages):
        season = episode = None
        title = video.title
        year = video.year
        filename = video.name
        imdb_id = video.imdb_id

        if isinstance(video, Episode):
            title = video.series
            season = video.season
            episode = video.episode
            imdb_id = video.series_imdb_id

        return [s for s in self.query(title, season, episode, year, filename, imdb_id) if s.language in languages]

    def download_subtitle(self, subtitle: WizdomSubtitle):
        # download
        url = "http://zip.{}/{}.zip".format(self.server_url, subtitle.subtitle_id)
        r = self.session.get(url, headers={"Referer": subtitle.page_link}, timeout=10)
        r.raise_for_status()

        # open the zip
        with zipfile.ZipFile(io.BytesIO(r.content)) as zf:
            # remove some filenames from the namelist
            namelist = [n for n in zf.namelist() if os.path.splitext(n)[1] in [".srt", ".sub"]]
            if len(namelist) > 1:
                raise ProviderError("More than one file to unzip")

            subtitle.content = fix_line_ending(zf.read(namelist[0]))
