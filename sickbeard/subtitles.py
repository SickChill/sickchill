# coding=utf-8
# Author: medariox <dariox@gmx.com>,
# based on Antoine Bertin's <diaoulael@gmail.com> work
# and originally written by Nyaran <nyayukko@gmail.com>
# URL: https://github.com/SickRage/SickRage/
#
# This file is part of SickRage.
#
# SickRage is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SickRage is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage. If not, see <http://www.gnu.org/licenses/>.

from __future__ import print_function, unicode_literals

import datetime
import os
import re
import subprocess
import threading
import traceback

import six
import subliminal
from babelfish import Language, language_converters
from guessit import guessit
from subliminal import Episode, provider_manager, ProviderPool

import sickbeard
from sickbeard import db, history, logger
from sickbeard.common import Quality
from sickbeard.helpers import is_media_file
from sickrage.helper.common import dateTimeFormat, episode_num
from sickrage.helper.exceptions import ex
from sickrage.show.Show import Show

# https://github.com/Diaoul/subliminal/issues/536
# provider_manager.register('napiprojekt = subliminal.providers.napiprojekt:NapiProjektProvider')
if 'legendastv' not in provider_manager.names():
    provider_manager.register('legendastv = subliminal.providers.legendastv:LegendasTVProvider')
if 'itasa' not in provider_manager.names():
    provider_manager.register('itasa = sickrage.providers.subtitle.itasa:ItaSAProvider')
if 'wizdom' not in provider_manager.names():
    provider_manager.register('wizdom = sickrage.providers.subtitle.wizdom:WizdomProvider')
# We disabled the original subscenter in lib/subliminal/extensions.py since it's outdated.
# Until it gets an update in subliminal, we'll use a fixed provider.
if 'subscenter' not in provider_manager.names():
    provider_manager.register('subscenter = sickrage.providers.subtitle.subscenter:SubsCenterProvider')
if 'tusubtitulo' not in provider_manager.names():
    provider_manager.register('tusubtitulo = sickrage.providers.subtitle.tusubtitulo:TuSubtituloProvider')

subliminal.region.configure('dogpile.cache.memory')

PROVIDER_URLS = {
    'addic7ed': 'http://www.addic7ed.com',
    'itasa': 'http://www.italiansubs.net/',
    'legendastv': 'http://www.legendas.tv',
    'napiprojekt': 'http://www.napiprojekt.pl',
    'opensubtitles': 'http://www.opensubtitles.org',
    'podnapisi': 'http://www.podnapisi.net',
    'subscenter': 'http://www.subscenter.info',
    'thesubdb': 'http://www.thesubdb.com',
    'tusubtitulo': 'https://www.tusubtitulo.com',
    'tvsubtitles': 'http://www.tvsubtitles.net',
    'wizdom': 'http://wizdom.xyz'
}


class SubtitleProviderPool(object):  # pylint: disable=too-few-public-methods
    _lock = threading.Lock()
    _creation = None
    _instance = None

    @staticmethod
    def __init_instance():
        with SubtitleProviderPool._lock:
            providers = enabled_service_list()
            provider_configs = {
                'addic7ed': {
                    'username': sickbeard.ADDIC7ED_USER,
                    'password': sickbeard.ADDIC7ED_PASS
                },
                'itasa': {
                    'username': sickbeard.ITASA_USER,
                    'password': sickbeard.ITASA_PASS
                },
                'legendastv': {
                    'username': sickbeard.LEGENDASTV_USER,
                    'password': sickbeard.LEGENDASTV_PASS
                },
                'opensubtitles': {
                    'username': sickbeard.OPENSUBTITLES_USER,
                    'password': sickbeard.OPENSUBTITLES_PASS
                },
                'subscenter': {
                    'username': sickbeard.SUBSCENTER_USER,
                    'password': sickbeard.SUBSCENTER_PASS
                }
            }

            SubtitleProviderPool._instance = ProviderPool(providers=providers, provider_configs=provider_configs)

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
        """ Delegate access to implementation """
        return getattr(self._instance, attr)


def sorted_service_list():
    new_list = []
    lmgtfy = 'http://lmgtfy.com/?q=%s'

    current_index = 0
    for current_service in sickbeard.SUBTITLES_SERVICES_LIST:
        if current_service in provider_manager.names():
            new_list.append({'name': current_service,
                             'url': PROVIDER_URLS[current_service] if current_service in PROVIDER_URLS else lmgtfy % current_service,
                             'image': current_service + '.png',
                             'enabled': sickbeard.SUBTITLES_SERVICES_ENABLED[current_index] == 1})
        current_index += 1

    for current_service in provider_manager.names():
        if current_service not in [service['name'] for service in new_list]:
            new_list.append({'name': current_service,
                             'url': PROVIDER_URLS[current_service] if current_service in PROVIDER_URLS else lmgtfy % current_service,
                             'image': current_service + '.png',
                             'enabled': False})
    return new_list


def enabled_service_list():
    return [service['name'] for service in sorted_service_list() if service['enabled']]


def wanted_languages(sql_like=None):
    wanted = frozenset(sickbeard.SUBTITLES_LANGUAGES).intersection(subtitle_code_filter())
    return (wanted, '%' + ','.join(sorted(wanted)) + '%' if sickbeard.SUBTITLES_MULTI else '%und%')[bool(sql_like)]


def get_needed_languages(subtitles):
    if not sickbeard.SUBTITLES_MULTI:
        return set() if 'und' in subtitles else {from_code(language) for language in wanted_languages()}
    return {from_code(language) for language in wanted_languages().difference(subtitles)}


def subtitle_code_filter():
    return {code for code in language_converters['opensubtitles'].codes if len(code) == 3}


def needs_subtitles(subtitles, force_lang=None):
    if not wanted_languages():
        return False

    if isinstance(subtitles, six.string_types):
        subtitles = {subtitle.strip() for subtitle in subtitles.split(',') if subtitle.strip()}

    # if force language is set, we remove it from already downloaded subtitles
    if force_lang in subtitles:
        subtitles.remove(force_lang)

    if sickbeard.SUBTITLES_MULTI:
        return wanted_languages().difference(subtitles)

    return 'und' not in subtitles


def from_code(language):
    language = language.strip()
    if language and language in language_converters['opensubtitles'].codes:
        return Language.fromopensubtitles(language)  # pylint: disable=no-member

    return Language('und')


def name_from_code(code):
    return from_code(code).name


def code_from_code(code):
    return from_code(code).opensubtitles


def download_subtitles(episode, force_lang=None):  # pylint: disable=too-many-locals, too-many-branches, too-many-statements
    existing_subtitles = episode.subtitles

    if not needs_subtitles(existing_subtitles, force_lang):
        logger.log('Episode already has all needed subtitles, skipping {0} {1}'.format
                   (episode.show.name, episode_num(episode.season, episode.episode) or
                    episode_num(episode.season, episode.episode, numbering='absolute')), logger.DEBUG)
        return existing_subtitles, None

    if not force_lang:
        languages = get_needed_languages(existing_subtitles)
    else:
        languages = {from_code(force_lang)}

    if not languages:
        logger.log('No subtitles needed for {0} {1}'.format
                   (episode.show.name, episode_num(episode.season, episode.episode) or
                    episode_num(episode.season, episode.episode, numbering='absolute')), logger.DEBUG)
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
    #                   'format': 4, 'audio_codec': 2, 'resolution': 1, 'hearing_impaired': 1, 'video_codec': 1}
    user_score = 213 if sickbeard.SUBTITLES_PERFECT_MATCH else 198

    video = get_video(video_path, subtitles_path=subtitles_path, episode=episode)
    if not video:
        logger.log('Exception caught in subliminal.scan_video for {0} {1}'.format
                   (episode.show.name, episode_num(episode.season, episode.episode) or
                    episode_num(episode.season, episode.episode, numbering='absolute')), logger.DEBUG)
        return existing_subtitles, None

    providers = enabled_service_list()
    pool = SubtitleProviderPool()

    try:
        subtitles_list = pool.list_subtitles(video, languages)

        for provider in providers:
            if provider in pool.discarded_providers:
                logger.log('Could not search in {0} provider. Discarding for now'.format(provider), logger.DEBUG)

        if not subtitles_list:
            logger.log('No subtitles found for {0} {1}'.format
                       (episode.show.name, episode_num(episode.season, episode.episode) or
                        episode_num(episode.season, episode.episode, numbering='absolute')), logger.DEBUG)
            return existing_subtitles, None

        for subtitle in subtitles_list:
            score = subliminal.score.compute_score(subtitle, video,
                                                   hearing_impaired=sickbeard.SUBTITLES_HEARING_IMPAIRED)
            logger.log('[{0}] Subtitle score for {1} is: {2} (min={3})'.format
                       (subtitle.provider_name, subtitle.id, score, user_score), logger.DEBUG)

        found_subtitles = pool.download_best_subtitles(subtitles_list, video, languages=languages,
                                                       hearing_impaired=sickbeard.SUBTITLES_HEARING_IMPAIRED,
                                                       min_score=user_score, only_one=not sickbeard.SUBTITLES_MULTI)

        subliminal.save_subtitles(video, found_subtitles, directory=subtitles_path,
                                  single=not sickbeard.SUBTITLES_MULTI)
    except IOError as error:
        if 'No space left on device' in ex(error):
            logger.log('Not enough space on the drive to save subtitles', logger.WARNING)
        else:
            logger.log(traceback.format_exc(), logger.WARNING)
    except Exception:
        logger.log('Error occurred when downloading subtitles for: {0}'.format(video_path))
        logger.log(traceback.format_exc(), logger.ERROR)
        return existing_subtitles, None

    for subtitle in found_subtitles:
        subtitle_path = subliminal.subtitle.get_subtitle_path(video.name,
                                                              None if not sickbeard.SUBTITLES_MULTI else
                                                              subtitle.language)
        if subtitles_path is not None:
            subtitle_path = os.path.join(subtitles_path, os.path.split(subtitle_path)[1])

        sickbeard.helpers.chmodAsParent(subtitle_path)
        sickbeard.helpers.fixSetGroupID(subtitle_path)

        if sickbeard.SUBTITLES_HISTORY:
            logger.log('history.logSubtitle {0}, {1}'.format
                       (subtitle.provider_name, subtitle.language.opensubtitles), logger.DEBUG)

            history.logSubtitle(episode.show.indexerid, episode.season, episode.episode, episode.status, subtitle)

        if sickbeard.SUBTITLES_EXTRA_SCRIPTS and is_media_file(video_path) and not sickbeard.EMBEDDED_SUBTITLES_ALL:

            run_subs_extra_scripts(episode, subtitle, video, single=not sickbeard.SUBTITLES_MULTI)

    new_subtitles = sorted({subtitle.language.opensubtitles for subtitle in found_subtitles})
    current_subtitles = sorted({subtitle for subtitle in new_subtitles + existing_subtitles}) if existing_subtitles else new_subtitles
    if not sickbeard.SUBTITLES_MULTI and len(found_subtitles) == 1:
        new_code = found_subtitles[0].language.opensubtitles
        if new_code not in existing_subtitles:
            current_subtitles.remove(new_code)
        current_subtitles.append('und')

    return current_subtitles, new_subtitles


def refresh_subtitles(episode):
    video = get_video(episode.location)
    if not video:
        logger.log("Exception caught in subliminal.scan_video, subtitles couldn't be refreshed", logger.DEBUG)
        return episode.subtitles, None
    current_subtitles = get_subtitles(video)
    if episode.subtitles == current_subtitles:
        logger.log('No changed subtitles for {0} {1}'.format
                   (episode.show.name, episode_num(episode.season, episode.episode) or
                    episode_num(episode.season, episode.episode, numbering='absolute')), logger.DEBUG)
        return episode.subtitles, None
    else:
        return current_subtitles, True


def get_video(video_path, subtitles_path=None, subtitles=True, embedded_subtitles=None, episode=None):
    if not subtitles_path:
        subtitles_path = get_subtitles_path(video_path)

    try:
        # Encode paths to UTF-8 to ensure subliminal support.
        video_path = video_path.encode('utf-8')
        subtitles_path = subtitles_path.encode('utf-8')
    except UnicodeEncodeError:
        # Fallback to system encoding. This should never happen.
        video_path = video_path.encode(sickbeard.SYS_ENCODING)
        subtitles_path = subtitles_path.encode(sickbeard.SYS_ENCODING)

    try:
        video = subliminal.scan_video(video_path)

        # external subtitles
        if subtitles:
            video.subtitle_languages |= \
                set(subliminal.core.search_external_subtitles(video_path, directory=subtitles_path).values())

        if embedded_subtitles is None:
            embedded_subtitles = bool(not sickbeard.EMBEDDED_SUBTITLES_ALL and video_path.endswith('.mkv'))

        # Let sickrage add more information to video file, based on the metadata.
        if episode:
            refine_video(video, episode)

        subliminal.refine(video, embedded_subtitles=embedded_subtitles)
    except Exception as error:
        logger.log('Exception: {0}'.format(error), logger.DEBUG)
        return None

    return video


def get_subtitles_path(video_path):
    if os.path.isabs(sickbeard.SUBTITLES_DIR):
        new_subtitles_path = sickbeard.SUBTITLES_DIR
    elif sickbeard.SUBTITLES_DIR:
        new_subtitles_path = os.path.join(os.path.dirname(video_path), sickbeard.SUBTITLES_DIR)
        dir_exists = sickbeard.helpers.makeDir(new_subtitles_path)
        if not dir_exists:
            logger.log('Unable to create subtitles folder {0}'.format(new_subtitles_path), logger.ERROR)
        else:
            sickbeard.helpers.chmodAsParent(new_subtitles_path)
    else:
        new_subtitles_path = os.path.dirname(video_path)

    try:
        # Encode path to UTF-8 to ensure subliminal support.
        new_subtitles_path = new_subtitles_path.encode('utf-8')
    except UnicodeEncodeError:
        # Fallback to system encoding. This should never happen.
        new_subtitles_path = new_subtitles_path.encode(sickbeard.SYS_ENCODING)

    return new_subtitles_path


def get_subtitles(video):
    """Return a sorted list of detected subtitles for the given video file."""
    result_list = []

    if not video.subtitle_languages:
        return result_list

    for language in video.subtitle_languages:
        if hasattr(language, 'opensubtitles') and language.opensubtitles:
            result_list.append(language.opensubtitles)

    return sorted(result_list)


class SubtitlesFinder(object):  # pylint: disable=too-few-public-methods
    """The SubtitlesFinder will be executed every hour but will not necessarly search and download subtitles.

    Only if the defined rule is true.
    """

    def __init__(self):
        self.amActive = False

    def run(self, force=False):  # pylint: disable=too-many-branches, too-many-statements, too-many-locals
        if not sickbeard.USE_SUBTITLES:
            return

        if not sickbeard.subtitles.enabled_service_list():
            logger.log('Not enough services selected. At least 1 service is required to '
                       'search subtitles in the background', logger.WARNING)
            return

        self.amActive = True

        def dhm(td):
            days = td.days
            hours = td.seconds // 60 ** 2
            minutes = (td.seconds // 60) % 60
            ret = ('', '{0} days, '.format(days))[days > 0] + \
                  ('', '{0} hours, '.format(hours))[hours > 0] + \
                  ('', '{0} minutes'.format(minutes))[minutes > 0]
            if days == 1:
                ret = ret.replace('days', 'day')
            if hours == 1:
                ret = ret.replace('hours', 'hour')
            if minutes == 1:
                ret = ret.replace('minutes', 'minute')
            return ret.rstrip(', ')

        logger.log('Checking for missed subtitles', logger.INFO)

        database = db.DBConnection()
        sql_results = database.select(
            "SELECT s.show_name, e.showid, e.season, e.episode, "
            "e.status, e.subtitles, e.subtitles_searchcount AS searchcount, "
            "e.subtitles_lastsearch AS lastsearch, e.location, (? - e.airdate) as age "
            "FROM tv_episodes AS e INNER JOIN tv_shows AS s "
            "ON (e.showid = s.indexer_id) "
            "WHERE s.subtitles = 1 AND e.subtitles NOT LIKE ? "
            + ("AND e.season != 0 ", "")[sickbeard.SUBTITLES_INCLUDE_SPECIALS]
            + "AND e.location != '' AND e.status IN ({}) ORDER BY age ASC".format(','.join(['?'] * len(Quality.DOWNLOADED))),
            [datetime.datetime.now().toordinal(), wanted_languages(True)] + Quality.DOWNLOADED
        )

        if not sql_results:
            logger.log('No subtitles to download', logger.INFO)
            self.amActive = False
            return

        for ep_to_sub in sql_results:
            try:
                # Encode path to system encoding.
                subtitle_path = ep_to_sub[b'location'].encode(sickbeard.SYS_ENCODING)
            except UnicodeEncodeError:
                # Fallback to UTF-8.
                subtitle_path = ep_to_sub[b'location'].encode('utf-8')
            if not os.path.isfile(subtitle_path):
                logger.log('Episode file does not exist, cannot download subtitles for {0} {1}'.format
                           (ep_to_sub[b'show_name'], episode_num(ep_to_sub[b'season'], ep_to_sub[b'episode']) or
                            episode_num(ep_to_sub[b'season'], ep_to_sub[b'episode'], numbering='absolute')), logger.DEBUG)
                continue

            if not needs_subtitles(ep_to_sub[b'subtitles']):
                logger.log('Episode already has all needed subtitles, skipping {0} {1}'.format
                           (ep_to_sub[b'show_name'], episode_num(ep_to_sub[b'season'], ep_to_sub[b'episode']) or
                            episode_num(ep_to_sub[b'season'], ep_to_sub[b'episode'], numbering='absolute')), logger.DEBUG)
                continue

            try:
                lastsearched = datetime.datetime.strptime(ep_to_sub[b'lastsearch'], dateTimeFormat)
            except ValueError:
                lastsearched = datetime.datetime.min

            try:
                if not force:
                    now = datetime.datetime.now()
                    days = int(ep_to_sub[b'age'])
                    delay_time = datetime.timedelta(hours=8 if days < 10 else 7 * 24 if days < 30 else 30 * 24)

                    # Search every hour for the first 24 hours since aired, then every 8 hours until 10 days passes
                    # After 10 days, search every 7 days, after 30 days search once a month
                    # Will always try an episode regardless of age at least 2 times
                    if lastsearched + delay_time > now and int(ep_to_sub[b'searchcount']) > 2 and days:
                        logger.log('Subtitle search for {0} {1} delayed for {2}'.format
                                   (ep_to_sub[b'show_name'], episode_num(ep_to_sub[b'season'], ep_to_sub[b'episode']) or
                                    episode_num(ep_to_sub[b'season'], ep_to_sub[b'episode'], numbering='absolute'),
                                    dhm(lastsearched + delay_time - now)), logger.DEBUG)
                        continue

                logger.log('Searching for missing subtitles of {0} {1}'.format
                           (ep_to_sub[b'show_name'], episode_num(ep_to_sub[b'season'], ep_to_sub[b'episode']) or
                            episode_num(ep_to_sub[b'season'], ep_to_sub[b'episode'], numbering='absolute')), logger.INFO)

                show_object = Show.find(sickbeard.showList, int(ep_to_sub[b'showid']))
                if not show_object:
                    logger.log('Show with ID {0} not found in the database'.format(ep_to_sub[b'showid']), logger.DEBUG)
                    continue

                episode_object = show_object.getEpisode(ep_to_sub[b'season'], ep_to_sub[b'episode'])
                if isinstance(episode_object, str):
                    logger.log('{0} {1} not found in the database'.format
                               (ep_to_sub[b'show_name'], episode_num(ep_to_sub[b'season'], ep_to_sub[b'episode']) or
                                episode_num(ep_to_sub[b'season'], ep_to_sub[b'episode'], numbering='absolute')), logger.DEBUG)
                    continue

                try:
                    new_subtitles = episode_object.download_subtitles()
                except Exception as error:
                    logger.log('Unable to find subtitles for {0} {1}. Error: {2}'.format
                               (ep_to_sub[b'show_name'], episode_num(ep_to_sub[b'season'], ep_to_sub[b'episode']) or
                                episode_num(ep_to_sub[b'season'], ep_to_sub[b'episode'], numbering='absolute'), ex(error)), logger.ERROR)
                    continue

                if new_subtitles:
                    logger.log('Downloaded {0} subtitles for {1} {2}'.format
                               (', '.join(new_subtitles), ep_to_sub[b'show_name'], episode_num(ep_to_sub[b'season'], ep_to_sub[b'episode']) or
                                episode_num(ep_to_sub[b'season'], ep_to_sub[b'episode'], numbering='absolute')))

            except Exception as error:
                logger.log('Error while searching subtitles for {0} {1}. Error: {2}'.format
                           (ep_to_sub[b'show_name'], episode_num(ep_to_sub[b'season'], ep_to_sub[b'episode']) or
                            episode_num(ep_to_sub[b'season'], ep_to_sub[b'episode'], numbering='absolute'), ex(error)), logger.ERROR)
                continue

        logger.log('Finished checking for missed subtitles', logger.INFO)
        self.amActive = False


def run_subs_extra_scripts(episode, subtitle, video, single=False):
    for script_name in sickbeard.SUBTITLES_EXTRA_SCRIPTS:
        script_cmd = [piece for piece in re.split("( |\\\".*?\\\"|'.*?')", script_name) if piece.strip()]
        script_cmd[0] = os.path.abspath(script_cmd[0])
        logger.log('Absolute path to script: {0}'.format(script_cmd[0]), logger.DEBUG)

        subtitle_path = subliminal.subtitle.get_subtitle_path(video.name, None if single else subtitle.language)

        inner_cmd = script_cmd + [video.name, subtitle_path, subtitle.language.opensubtitles,
                                  episode.show.name, str(episode.season), str(episode.episode),
                                  episode.name, str(episode.show.indexerid)]

        # use subprocess to run the command and capture output
        logger.log('Executing command: {0}'.format(inner_cmd))
        try:
            process = subprocess.Popen(inner_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.STDOUT, cwd=sickbeard.PROG_DIR)

            stdout, stderr_ = process.communicate()
            logger.log('Script result: {0}'.format(stdout), logger.DEBUG)

        except Exception as error:
            logger.log('Unable to run subs_extra_script: {0}'.format(ex(error)))


def refine_video(video, episode):
    # try to enrich video object using information in original filename
    if episode.release_name:
        guess_ep = Episode.fromguess(None, guessit(episode.release_name))
        for name in vars(guess_ep):
            if getattr(guess_ep, name) and not getattr(video, name):
                setattr(video, name, getattr(guess_ep, name))

    # Use sickbeard metadata
    metadata_mapping = {
        'episode': 'episode',
        'release_group': 'release_group',
        'season': 'season',
        'series': 'show.name',
        'series_imdb_id': 'show.imdbid',
        'size': 'file_size',
        'title': 'name',
        'year': 'show.startyear'
    }

    def get_attr_value(obj, name):
        value = None
        for attr in name.split('.'):
            if not value:
                value = getattr(obj, attr, None)
            else:
                value = getattr(value, attr, None)

        return value

    for name in metadata_mapping:
        if not getattr(video, name) and get_attr_value(episode, metadata_mapping[name]):
            setattr(video, name, get_attr_value(episode, metadata_mapping[name]))
        elif episode.show.subtitles_sr_metadata and get_attr_value(episode, metadata_mapping[name]):
            setattr(video, name, get_attr_value(episode, metadata_mapping[name]))

    # Set quality from metadata
    _, quality = Quality.splitCompositeStatus(episode.status)
    if not video.format or episode.show.subtitles_sr_metadata:
        if quality & Quality.ANYHDTV:
            video.format = Quality.combinedQualityStrings.get(Quality.ANYHDTV)
        elif quality & Quality.ANYWEBDL:
            video.format = Quality.combinedQualityStrings.get(Quality.ANYWEBDL)
        elif quality & Quality.ANYBLURAY:
            video.format = Quality.combinedQualityStrings.get(Quality.ANYBLURAY)

    if not video.resolution or episode.show.subtitles_sr_metadata:
        if quality & (Quality.HDTV | Quality.HDWEBDL | Quality.HDBLURAY):
            video.resolution = '720p'
        elif quality & Quality.RAWHDTV:
            video.resolution = '1080i'
        elif quality & (Quality.FULLHDTV | Quality.FULLHDWEBDL | Quality.FULLHDBLURAY):
            video.resolution = '1080p'
        elif quality & (Quality.UHD_4K_TV | Quality.UHD_4K_WEBDL | Quality.UHD_4K_BLURAY):
            video.resolution = '4K'
        elif quality & (Quality.UHD_8K_TV | Quality.UHD_8K_WEBDL | Quality.UHD_8K_BLURAY):
            video.resolution = '8K'
