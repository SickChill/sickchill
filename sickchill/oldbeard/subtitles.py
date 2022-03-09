import datetime
import os
import re
import subprocess
import threading
import traceback
from collections import namedtuple
from typing import Union

import subliminal
from babelfish import Language, language_converters
from guessit import guessit

import sickchill.oldbeard.helpers
from sickchill import logger, settings
from sickchill.helper.common import dateTimeFormat, episode_num
from sickchill.show.History import History
from sickchill.show.Show import Show

from . import db
from .common import Quality
from .helpers import is_media_file

# https://github.com/Diaoul/subliminal/issues/536
# provider_manager.register('napiprojekt = subliminal.providers.napiprojekt:NapiProjektProvider')
# if 'legendastv' not in subliminal.provider_manager.names():
#     subliminal.provider_manager.register('legendastv = subliminal.providers.legendastv:LegendasTVProvider')
if "itasa" not in subliminal.provider_manager.names():
    subliminal.provider_manager.register("itasa = sickchill.providers.subtitle.itasa:ItaSAProvider")
if "wizdom" not in subliminal.provider_manager.names():
    subliminal.provider_manager.register("wizdom = sickchill.providers.subtitle.wizdom:WizdomProvider")
if "subscenter" not in subliminal.provider_manager.names():
    subliminal.provider_manager.register("subscenter = sickchill.providers.subtitle.subscenter:SubsCenterProvider")
if "subtitulamos" not in subliminal.provider_manager.names():
    subliminal.provider_manager.register("subtitulamos = sickchill.providers.subtitle.subtitulamos:SubtitulamosProvider")
if "bsplayer" not in subliminal.provider_manager.names():
    subliminal.provider_manager.register("bsplayer = sickchill.providers.subtitle.bsplayer:BSPlayerProvider")

subliminal.region.configure("dogpile.cache.memory")

PROVIDER_URLS = {
    "addic7ed": "http://www.addic7ed.com",
    "bsplayer": "http://bsplayer-subtitles.com",
    "itasa": "http://www.italiansubs.net/",
    "legendastv": "http://www.legendas.tv",
    "napiprojekt": "http://www.napiprojekt.pl",
    "opensubtitles": "http://www.opensubtitles.org",
    "podnapisi": "http://www.podnapisi.net",
    "subscenter": "http://www.subscenter.info",
    "subtitulamos": "https://www.subtitulamos.tv",
    "thesubdb": "http://www.thesubdb.com",
    "wizdom": "http://wizdom.xyz",
    "tvsubtitles": "http://www.tvsubtitles.net",
}


max_score = {}
Scores = namedtuple("Scores", ["res", "percent", "min", "min_percent"])


def log_scores(subtitle: Union[subliminal.Episode, subliminal.Movie], video: subliminal.Video, user_score: int = None) -> Scores:
    if not max_score:
        max_score[subliminal.Episode] = sum(subliminal.score.episode_scores.values())
        max_score[subliminal.Movie] = sum(subliminal.score.movie_scores.values())

    score = subliminal.score.compute_score(subtitle, video, hearing_impaired=settings.SUBTITLES_HEARING_IMPAIRED)
    return Scores(score, round(score / max_score[type(video)] * 100), user_score, round(user_score / max_score[type(video)] * 100))


class SubtitleProviderPool(object):
    _lock = threading.Lock()
    _creation = None
    _instance = None

    @staticmethod
    def __init_instance():
        with SubtitleProviderPool._lock:
            providers = enabled_service_list()
            provider_configs = {
                "addic7ed": {"username": settings.ADDIC7ED_USER, "password": settings.ADDIC7ED_PASS},
                "itasa": {"username": settings.ITASA_USER, "password": settings.ITASA_PASS},
                "legendastv": {"username": settings.LEGENDASTV_USER, "password": settings.LEGENDASTV_PASS},
                "opensubtitles": {"username": settings.OPENSUBTITLES_USER, "password": settings.OPENSUBTITLES_PASS},
                "subscenter": {"username": settings.SUBSCENTER_USER, "password": settings.SUBSCENTER_PASS},
            }

            SubtitleProviderPool._instance = subliminal.ProviderPool(providers=providers, provider_configs=provider_configs)

    def __init__(self):
        if SubtitleProviderPool._creation is None:
            SubtitleProviderPool._creation = datetime.datetime.now()
            self.__init_instance()
        else:
            delta = datetime.timedelta(minutes=15)
            if SubtitleProviderPool._creation + delta < datetime.datetime.now():
                SubtitleProviderPool._creation = datetime.datetime.now()
                self.__init_instance()

    @staticmethod
    def reset():
        SubtitleProviderPool._creation = None

    def __getattr__(self, attr):
        """Delegate access to implementation"""
        return getattr(self._instance, attr)


def sorted_service_list():
    new_list = []
    lmgtfy = "http://lmgtfy.com/?q=%s"

    current_index = 0
    for current_service in settings.SUBTITLES_SERVICES_LIST:
        if current_service in subliminal.provider_manager.names():
            new_list.append(
                {
                    "name": current_service,
                    "url": PROVIDER_URLS[current_service] if current_service in PROVIDER_URLS else lmgtfy % current_service,
                    "image": current_service + ".png",
                    "enabled": settings.SUBTITLES_SERVICES_ENABLED[current_index] == 1,
                }
            )
        current_index += 1

    for current_service in subliminal.provider_manager.names():
        if current_service not in [service["name"] for service in new_list]:
            new_list.append(
                {
                    "name": current_service,
                    "url": PROVIDER_URLS[current_service] if current_service in PROVIDER_URLS else lmgtfy % current_service,
                    "image": current_service + ".png",
                    "enabled": False,
                }
            )
    return new_list


def enabled_service_list():
    return [service["name"] for service in sorted_service_list() if service["enabled"]]


def wanted_languages(sql_like=None):
    wanted = frozenset(settings.SUBTITLES_LANGUAGES).intersection(subtitle_code_filter())
    return (wanted, "%" + ",".join(sorted(wanted)) + "%" if settings.SUBTITLES_MULTI else "%und%")[bool(sql_like)]


def get_needed_languages(subtitles):
    if not settings.SUBTITLES_MULTI:
        return set() if "und" in subtitles else {from_code(language) for language in wanted_languages()}
    return {from_code(language) for language in wanted_languages().difference(subtitles)}


def subtitle_code_filter():
    return {code for code in language_converters["opensubtitles"].codes if len(code) == 3}


def needs_subtitles(subtitles, force_lang=None):
    if not wanted_languages():
        return False

    if isinstance(subtitles, str):
        subtitles = {subtitle.strip() for subtitle in subtitles.split(",") if subtitle.strip()}

    # if force language is set, we remove it from already downloaded subtitles
    if force_lang in subtitles:
        subtitles.remove(force_lang)

    if settings.SUBTITLES_MULTI:
        return wanted_languages().difference(subtitles)

    return "und" not in subtitles


def from_code(language):
    language = language.strip()
    if language and language in language_converters["opensubtitles"].codes:
        return Language.fromopensubtitles(language)

    return Language("und")


def name_from_code(code):
    return from_code(code).name


def code_from_code(code):
    return from_code(code).opensubtitles


def download_subtitles(episode, force_lang=None):
    existing_subtitles = episode.subtitles

    if not needs_subtitles(existing_subtitles, force_lang):
        logger.debug(
            "Episode already has all needed subtitles, skipping {0} {1}".format(
                episode.show.name, episode_num(episode.season, episode.episode) or episode_num(episode.season, episode.episode, numbering="absolute")
            )
        )
        return existing_subtitles, None

    if not force_lang:
        languages = get_needed_languages(existing_subtitles)
    else:
        languages = {from_code(force_lang)}

    if not languages:
        logger.debug(
            "No subtitles needed for {0} {1}".format(
                episode.show.name, episode_num(episode.season, episode.episode) or episode_num(episode.season, episode.episode, numbering="absolute")
            )
        )
        return existing_subtitles, None

    subtitles_path = get_subtitles_path(episode.location)
    video_path = episode.location

    # Perfect match = hash score - hearing impaired score - resolution score
    # (subtitle for 720p is the same as for 1080p)
    # Perfect match = 215 - 1 - 1 = 213
    # Non-perfect match = series + year + season + episode
    # Non-perfect match = 108 + 54 + 18 + 18 = 198
    # From latest subliminal code:
    # episode_scores = {'hash': 215, 'series': 108, 'year': 54, 'season': 18, 'episode': 18, 'release_group': 9,
    #                   'source': 4, 'audio_codec': 2, 'resolution': 1, 'hearing_impaired': 1, 'video_codec': 1}
    user_score = 213 if settings.SUBTITLES_PERFECT_MATCH else 198

    video = get_video(video_path, subtitles_path=subtitles_path, episode=episode)
    if not video:
        logger.debug(
            "Exception caught in subliminal.scan_video for {0} {1}".format(
                episode.show.name, episode_num(episode.season, episode.episode) or episode_num(episode.season, episode.episode, numbering="absolute")
            )
        )
        return existing_subtitles, None

    providers = enabled_service_list()
    pool = SubtitleProviderPool()

    try:
        subtitles_list = pool.list_subtitles(video, languages)

        for provider in providers:
            if provider in pool.discarded_providers:
                logger.debug("Could not search in {0} provider. Discarding for now".format(provider))

        if not subtitles_list:
            logger.debug(
                "No subtitles found for {0} {1}".format(
                    episode.show.name, episode_num(episode.season, episode.episode) or episode_num(episode.season, episode.episode, numbering="absolute")
                )
            )
            return existing_subtitles, None

        for subtitle in subtitles_list:
            scores = log_scores(subtitle, video, user_score=user_score)
            logger.debug(
                f"[{subtitle.provider_name}] Subtitle score for {subtitle.id} is: {scores['res']}/{scores['percent']}% (min={scores['min']}/{scores['min_percent']}%)"
            )

        found_subtitles = pool.download_best_subtitles(
            subtitles_list,
            video,
            languages=languages,
            hearing_impaired=settings.SUBTITLES_HEARING_IMPAIRED,
            min_score=user_score,
            only_one=not settings.SUBTITLES_MULTI,
        )

        subliminal.save_subtitles(video, found_subtitles, directory=subtitles_path, single=not settings.SUBTITLES_MULTI, encoding="utf8")
    except IOError as error:
        if "No space left on device" in str(error):
            logger.warning("Not enough space on the drive to save subtitles")
        else:
            logger.warning(traceback.format_exc())
        return existing_subtitles, None
    except Exception:
        logger.info("Error occurred when downloading subtitles for: {0}".format(video_path))
        logger.exception(traceback.format_exc())
        return existing_subtitles, None

    for subtitle in found_subtitles:
        subtitle_path = subliminal.subtitle.get_subtitle_path(video.name, None if not settings.SUBTITLES_MULTI else subtitle.language)
        if subtitles_path is not None:
            subtitle_path = os.path.join(subtitles_path, os.path.split(subtitle_path)[1])

        sickchill.oldbeard.helpers.chmodAsParent(subtitle_path)
        sickchill.oldbeard.helpers.fixSetGroupID(subtitle_path)

        History().logSubtitle(
            episode.show.indexerid, episode.season, episode.episode, episode.status, subtitle, log_scores(subtitle, video, user_score=user_score)
        )

        if settings.SUBTITLES_EXTRA_SCRIPTS and is_media_file(video_path) and not settings.EMBEDDED_SUBTITLES_ALL:

            run_subs_extra_scripts(episode, subtitle, video, single=not settings.SUBTITLES_MULTI)

    new_subtitles = sorted({subtitle.language.opensubtitles for subtitle in found_subtitles})
    current_subtitles = sorted({subtitle for subtitle in new_subtitles + existing_subtitles}) if existing_subtitles else new_subtitles
    if not settings.SUBTITLES_MULTI and len(found_subtitles) == 1:
        new_code = found_subtitles[0].language.opensubtitles
        if new_code not in existing_subtitles:
            current_subtitles.remove(new_code)
        current_subtitles.append("und")

    return current_subtitles, new_subtitles


def refresh_subtitles(episode):
    video = get_video(episode.location)
    if not video:
        logger.debug("Exception caught in subliminal.scan_video, subtitles couldn't be refreshed")
        return episode.subtitles, None
    current_subtitles = get_subtitles(video)
    if episode.subtitles == current_subtitles:
        logger.debug(
            "No changed subtitles for {0} {1}".format(
                episode.show.name, episode_num(episode.season, episode.episode) or episode_num(episode.season, episode.episode, numbering="absolute")
            )
        )
        return episode.subtitles, None
    else:
        return current_subtitles, True


def get_video(video_path, subtitles_path=None, subtitles=True, embedded_subtitles=None, episode=None):
    if not subtitles_path:
        subtitles_path = get_subtitles_path(video_path)

    try:
        video = subliminal.scan_video(video_path)

        # external subtitles
        if subtitles:
            video.subtitle_languages |= set(subliminal.core.search_external_subtitles(video_path, directory=subtitles_path).values())

        if embedded_subtitles is None:
            embedded_subtitles = bool(not settings.EMBEDDED_SUBTITLES_ALL and video_path.endswith(".mkv"))

        # Let sickchill add more information to video file, based on the metadata.
        if episode:
            refine_video(video, episode)

        subliminal.refine(video, embedded_subtitles=embedded_subtitles)
    except Exception as error:
        logger.info(traceback.format_exc())
        logger.debug("Exception: {0}".format(error))
        return None

    return video


def get_subtitles_path(video_path):
    if os.path.isabs(settings.SUBTITLES_DIR):
        new_subtitles_path = settings.SUBTITLES_DIR
    elif settings.SUBTITLES_DIR:
        new_subtitles_path = os.path.join(os.path.dirname(video_path), settings.SUBTITLES_DIR)
        dir_exists = sickchill.oldbeard.helpers.makeDir(new_subtitles_path)
        if not dir_exists:
            logger.exception("Unable to create subtitles folder {0}".format(new_subtitles_path))
        else:
            sickchill.oldbeard.helpers.chmodAsParent(new_subtitles_path)
    else:
        new_subtitles_path = os.path.dirname(video_path)

    return new_subtitles_path


def get_subtitles(video):
    """Return a sorted list of detected subtitles for the given video file."""
    result_list = []

    if not video.subtitle_languages:
        return result_list

    for language in video.subtitle_languages:
        if hasattr(language, "opensubtitles") and language.opensubtitles:
            result_list.append(language.opensubtitles)

    return sorted(result_list)


class SubtitlesFinder(object):
    """The SubtitlesFinder will be executed every hour but will not necessarly search and download subtitles.

    Only if the defined rule is true.
    """

    def __init__(self):
        self.amActive = False

    def run(self, force=False):
        if not settings.USE_SUBTITLES:
            return

        if not enabled_service_list():
            logger.warning("Not enough services selected. At least 1 service is required to " "search subtitles in the background")
            return

        self.amActive = True

        def dhm(td):
            days = td.days
            hours = td.seconds // 60**2
            minutes = (td.seconds // 60) % 60
            ret = ("", "{0} days, ".format(days))[days > 0] + ("", "{0} hours, ".format(hours))[hours > 0] + ("", "{0} minutes".format(minutes))[minutes > 0]
            if days == 1:
                ret = ret.replace("days", "day")
            if hours == 1:
                ret = ret.replace("hours", "hour")
            if minutes == 1:
                ret = ret.replace("minutes", "minute")
            return ret.rstrip(", ")

        logger.info("Checking for missed subtitles")

        database = db.DBConnection()
        sql_results = database.select(
            "SELECT s.show_name, e.showid, e.season, e.episode, e.status, e.subtitles, e.subtitles_searchcount AS searchcount, e.subtitles_lastsearch AS lastsearch, e.location, (? - e.airdate) as age FROM tv_episodes AS e INNER JOIN tv_shows AS s ON (e.showid = s.indexer_id) "
            "WHERE s.subtitles = 1 AND e.subtitles NOT LIKE ? "
            + ("AND e.season != 0 ", "")[settings.SUBTITLES_INCLUDE_SPECIALS]
            + "AND e.location != '' AND e.status IN ({}) ORDER BY age ASC".format(",".join(["?"] * len(Quality.DOWNLOADED))),
            [datetime.datetime.now().toordinal(), wanted_languages(True)] + Quality.DOWNLOADED,
        )

        if not sql_results:
            logger.info("No subtitles to download")
            self.amActive = False
            return

        for ep_to_sub in sql_results:
            if not os.path.isfile(ep_to_sub["location"]):
                logger.debug(
                    "Episode file does not exist, cannot download subtitles for {0} {1}".format(
                        ep_to_sub["show_name"],
                        episode_num(ep_to_sub["season"], ep_to_sub["episode"]) or episode_num(ep_to_sub["season"], ep_to_sub["episode"], numbering="absolute"),
                    )
                )
                continue

            if not needs_subtitles(ep_to_sub["subtitles"]):
                logger.debug(
                    "Episode already has all needed subtitles, skipping {0} {1}".format(
                        ep_to_sub["show_name"],
                        episode_num(ep_to_sub["season"], ep_to_sub["episode"]) or episode_num(ep_to_sub["season"], ep_to_sub["episode"], numbering="absolute"),
                    )
                )
                continue

            try:
                lastsearched = datetime.datetime.strptime(ep_to_sub["lastsearch"], dateTimeFormat)
            except ValueError:
                lastsearched = datetime.datetime.min

            try:
                if not force:
                    now = datetime.datetime.now()
                    days = int(ep_to_sub["age"])
                    delay_time = datetime.timedelta(hours=8 if days < 10 else 7 * 24 if days < 30 else 30 * 24)

                    # Search every hour for the first 24 hours since aired, then every 8 hours until 10 days passes
                    # After 10 days, search every 7 days, after 30 days search once a month
                    # Will always try an episode regardless of age at least 2 times
                    if lastsearched + delay_time > now and int(ep_to_sub["searchcount"]) > 2 and days:
                        logger.debug(
                            "Subtitle search for {0} {1} delayed for {2}".format(
                                ep_to_sub["show_name"],
                                episode_num(ep_to_sub["season"], ep_to_sub["episode"])
                                or episode_num(ep_to_sub["season"], ep_to_sub["episode"], numbering="absolute"),
                                dhm(lastsearched + delay_time - now),
                            )
                        )
                        continue

                logger.info(
                    "Searching for missing subtitles of {0} {1}".format(
                        ep_to_sub["show_name"],
                        episode_num(ep_to_sub["season"], ep_to_sub["episode"]) or episode_num(ep_to_sub["season"], ep_to_sub["episode"], numbering="absolute"),
                    )
                )

                show_object = Show.find(settings.showList, int(ep_to_sub["showid"]))
                if not show_object:
                    logger.debug("Show with ID {0} not found in the database".format(ep_to_sub["showid"]))
                    continue

                episode_object = show_object.getEpisode(ep_to_sub["season"], ep_to_sub["episode"])
                if isinstance(episode_object, str):
                    logger.debug(
                        "{0} {1} not found in the database".format(
                            ep_to_sub["show_name"],
                            episode_num(ep_to_sub["season"], ep_to_sub["episode"])
                            or episode_num(ep_to_sub["season"], ep_to_sub["episode"], numbering="absolute"),
                        )
                    )
                    continue

                try:
                    new_subtitles = episode_object.download_subtitles()
                except Exception as error:
                    logger.error(
                        "Unable to find subtitles for {0} {1}. Error: {2}".format(
                            ep_to_sub["show_name"],
                            episode_num(ep_to_sub["season"], ep_to_sub["episode"])
                            or episode_num(ep_to_sub["season"], ep_to_sub["episode"], numbering="absolute"),
                            str(error),
                        )
                    )
                    continue

                if new_subtitles:
                    logger.info(
                        "Downloaded {0} subtitles for {1} {2}".format(
                            ", ".join(new_subtitles),
                            ep_to_sub["show_name"],
                            episode_num(ep_to_sub["season"], ep_to_sub["episode"])
                            or episode_num(ep_to_sub["season"], ep_to_sub["episode"], numbering="absolute"),
                        )
                    )

            except Exception as error:
                logger.error(
                    "Error while searching subtitles for {0} {1}. Error: {2}".format(
                        ep_to_sub["show_name"],
                        episode_num(ep_to_sub["season"], ep_to_sub["episode"]) or episode_num(ep_to_sub["season"], ep_to_sub["episode"], numbering="absolute"),
                        str(error),
                    )
                )
                continue

        logger.info("Finished checking for missed subtitles")
        self.amActive = False


def run_subs_extra_scripts(episode, subtitle, video, single=False):
    for script_name in settings.SUBTITLES_EXTRA_SCRIPTS:
        script_cmd = [piece for piece in re.split("( |\\\".*?\\\"|'.*?')", script_name) if piece.strip()]
        script_cmd[0] = os.path.abspath(script_cmd[0])
        logger.debug("Absolute path to script: {0}".format(script_cmd[0]))

        subtitle_path = subliminal.subtitle.get_subtitle_path(video.name, None if single else subtitle.language)

        inner_cmd = script_cmd + [
            video.name,
            subtitle_path,
            subtitle.language.opensubtitles,
            episode.show.name,
            str(episode.season),
            str(episode.episode),
            episode.name,
            str(episode.show.indexerid),
        ]

        # use subprocess to run the command and capture output
        logger.info("Executing command: {0}".format(inner_cmd))
        try:
            process = subprocess.Popen(
                inner_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=settings.DATA_DIR, universal_newlines=True
            )

            stdout, stderr = process.communicate()
            logger.debug("Script result: {0}".format(str(stdout or stderr).strip()))

        except Exception as error:
            logger.info("Unable to run subs_extra_script: {0}".format(str(error)))


def refine_video(video, episode):
    # try to enrich video object using information in original filename
    if episode.release_name:
        guess_ep = subliminal.Episode.fromguess(episode.release_name, guessit(episode.release_name))
        for name in vars(guess_ep):
            if getattr(guess_ep, name) and not getattr(video, name):
                setattr(video, name, getattr(guess_ep, name))

    # Use oldbeard metadata
    metadata_mapping = {
        "episode": "episode",
        "release_group": "release_group",
        "season": "season",
        "series": "show.name",
        "series_imdb_id": "show.imdb_id",
        "size": "file_size",
        "title": "name",
        "year": "show.startyear",
        "series_tvdb_id": "show.indexerid",
        "tvdb_id": "indexerid",
    }

    def get_attr_value(obj, name):
        value = None
        for attr in name.split("."):
            if not value:
                value = getattr(obj, attr, None)
            else:
                value = getattr(value, attr, None)

        return value

    for name in metadata_mapping:
        try:
            if not getattr(video, name) and get_attr_value(episode, metadata_mapping[name]):
                setattr(video, name, get_attr_value(episode, metadata_mapping[name]))
            elif episode.show.subtitles_sr_metadata and get_attr_value(episode, metadata_mapping[name]):
                setattr(video, name, get_attr_value(episode, metadata_mapping[name]))
        except AttributeError:
            logger.debug("Unable to set {}.{} from episode.{} attribute".format(type(video), name, metadata_mapping[name]))

    # Set quality from metadata
    status, quality = Quality.splitCompositeStatus(episode.status)
    if not video.source or episode.show.subtitles_sr_metadata:
        if quality & Quality.ANYHDTV:
            video.source = Quality.combinedQualityStrings.get(Quality.ANYHDTV)
        elif quality & Quality.ANYWEBDL:
            video.source = Quality.combinedQualityStrings.get(Quality.ANYWEBDL)
        elif quality & Quality.ANYBLURAY:
            video.source = Quality.combinedQualityStrings.get(Quality.ANYBLURAY)

    if not video.resolution or episode.show.subtitles_sr_metadata:
        if quality & (Quality.HDTV | Quality.HDWEBDL | Quality.HDBLURAY):
            video.resolution = "720p"
        elif quality & Quality.RAWHDTV:
            video.resolution = "1080i"
        elif quality & (Quality.FULLHDTV | Quality.FULLHDWEBDL | Quality.FULLHDBLURAY):
            video.resolution = "1080p"
        elif quality & (Quality.UHD_4K_TV | Quality.UHD_4K_WEBDL | Quality.UHD_4K_BLURAY):
            video.resolution = "4K"
        elif quality & (Quality.UHD_8K_TV | Quality.UHD_8K_WEBDL | Quality.UHD_8K_BLURAY):
            video.resolution = "8K"
