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

import os
import re
import datetime
import traceback
import subliminal
import subprocess
import sickbeard
from babelfish import Language, language_converters
from subliminal import ProviderPool, provider_manager
from sickbeard import logger
from sickbeard import history
from sickbeard import db
from sickbeard import processTV
from sickbeard.common import Quality
from sickbeard.helpers import remove_non_release_groups, isMediaFile, isRarFile
from sickrage.helper.common import episode_num, dateTimeFormat, subtitle_extensions
from sickrage.helper.exceptions import ex
from sickrage.show.Show import Show

provider_manager.register('legendastv = subliminal.providers.legendastv:LegendasTvProvider')
provider_manager.register('napiprojekt = subliminal.providers.napiprojekt:NapiProjektProvider')

subliminal.region.configure('dogpile.cache.memory')

PROVIDER_URLS = {
    'addic7ed': 'http://www.addic7ed.com',
    'itasa': 'http://www.italiansubs.net/',
    'legendastv': 'http://www.legendas.tv',
    'napiprojekt': 'http://www.napiprojekt.pl',
    'opensubtitles': 'http://www.opensubtitles.org',
    'podnapisi': 'http://www.podnapisi.net',
    'subscenter': 'http://www.subscenter.org',
    'thesubdb': 'http://www.thesubdb.com',
    'tvsubtitles': 'http://www.tvsubtitles.net'
}


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


def needs_subtitles(subtitles):
    if not wanted_languages():
        return False

    if isinstance(subtitles, basestring):
        subtitles = {subtitle.strip() for subtitle in subtitles.split(',') if subtitle.strip()}

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


def download_subtitles(subtitles_info):  # pylint: disable=too-many-locals, too-many-branches, too-many-statements
    existing_subtitles = subtitles_info['subtitles']

    if not needs_subtitles(existing_subtitles):
        logger.log(u'Episode already has all needed subtitles, skipping {} {}'.format
                   (subtitles_info['show_name'], episode_num(subtitles_info['season'], subtitles_info['episode']) or
                    episode_num(subtitles_info['season'], subtitles_info['episode'], numbering='absolute')), logger.DEBUG)
        return existing_subtitles, None

    languages = get_needed_languages(existing_subtitles)
    if not languages:
        logger.log(u'No subtitles needed for {} {}'.format
                   (subtitles_info['show_name'], episode_num(subtitles_info['season'], subtitles_info['episode']) or
                    episode_num(subtitles_info['season'], subtitles_info['episode'], numbering='absolute')), logger.DEBUG)
        return existing_subtitles, None

    subtitles_path = get_subtitles_path(subtitles_info['location'])
    video_path = subtitles_info['location']

    # Perfect match = hash score - hearing impaired score - resolution score (subtitle for 720p is the same as for 1080p)
    # Perfect match = 215 - 1 - 1 = 213
    # Non-perfect match = series + year + season + episode
    # Non-perfect match = 108 + 54 + 18 + 18 = 198
    # From latest subliminal code:
    # episode_scores = {'hash': 215, 'series': 108, 'year': 54, 'season': 18, 'episode': 18, 'release_group': 9,
    #                   'format': 4, 'audio_codec': 2, 'resolution': 1, 'hearing_impaired': 1, 'video_codec': 1}
    user_score = 213 if sickbeard.SUBTITLES_PERFECT_MATCH else 198

    video = get_video(video_path, subtitles_path=subtitles_path)
    if not video:
        logger.log(u'Exception caught in subliminal.scan_video for {} {}'.format
                   (subtitles_info['show_name'], episode_num(subtitles_info['season'], subtitles_info['episode']) or
                    episode_num(subtitles_info['season'], subtitles_info['episode'], numbering='absolute')), logger.DEBUG)
        return existing_subtitles, None

    providers = enabled_service_list()
    provider_configs = {'addic7ed': {'username': sickbeard.ADDIC7ED_USER,
                                     'password': sickbeard.ADDIC7ED_PASS},
                        'itasa': {'username': sickbeard.ITASA_USER,
                                     'password': sickbeard.ITASA_PASS},
                        'legendastv': {'username': sickbeard.LEGENDASTV_USER,
                                       'password': sickbeard.LEGENDASTV_PASS},
                        'opensubtitles': {'username': sickbeard.OPENSUBTITLES_USER,
                                          'password': sickbeard.OPENSUBTITLES_PASS}}

    pool = ProviderPool(providers=providers, provider_configs=provider_configs)

    try:
        subtitles_list = pool.list_subtitles(video, languages)

        for provider in providers:
            if provider in pool.discarded_providers:
                logger.log(u'Could not search in {} provider. Discarding for now'.format(provider), logger.DEBUG)

        if not subtitles_list:
            logger.log(u'No subtitles found for {} {}'.format
                       (subtitles_info['show_name'], episode_num(subtitles_info['season'], subtitles_info['episode']) or
                        episode_num(subtitles_info['season'], subtitles_info['episode'], numbering='absolute')), logger.DEBUG)
            return existing_subtitles, None

        for subtitle in subtitles_list:
            score = subliminal.score.compute_score(subtitle, video, hearing_impaired=sickbeard.SUBTITLES_HEARING_IMPAIRED)
            logger.log(u'[{}] Subtitle score for {} is: {} (min={})'.format
                       (subtitle.provider_name, subtitle.id, score, user_score), logger.DEBUG)

        found_subtitles = pool.download_best_subtitles(subtitles_list, video, languages=languages,
                                                       hearing_impaired=sickbeard.SUBTITLES_HEARING_IMPAIRED,
                                                       min_score=user_score, only_one=not sickbeard.SUBTITLES_MULTI)

        subliminal.save_subtitles(video, found_subtitles, directory=subtitles_path,
                                  single=not sickbeard.SUBTITLES_MULTI)
    except IOError as error:
        if 'No space left on device' in ex(error):
            logger.log(u'Not enough space on the drive to save subtitles', logger.WARNING)
        else:
            logger.log(traceback.format_exc(), logger.WARNING)
    except Exception:
        logger.log(u'Error occurred when downloading subtitles for: {}'.format(video_path))
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
            logger.log(u'history.logSubtitle {}, {}'.format
                       (subtitle.provider_name, subtitle.language.opensubtitles), logger.DEBUG)

            history.logSubtitle(subtitles_info['show_indexerid'], subtitles_info['season'],
                                subtitles_info['episode'], subtitles_info['status'], subtitle)

        if sickbeard.SUBTITLES_EXTRA_SCRIPTS and isMediaFile(video_path) and not sickbeard.EMBEDDED_SUBTITLES_ALL:
            run_subs_extra_scripts(subtitles_info, subtitle, video, single=not sickbeard.SUBTITLES_MULTI)

    new_subtitles = sorted({subtitle.language.opensubtitles for subtitle in found_subtitles})
    current_subtitles = sorted({subtitle for subtitle in new_subtitles + existing_subtitles}) if existing_subtitles else new_subtitles
    if not sickbeard.SUBTITLES_MULTI and len(found_subtitles) == 1:
        new_code = found_subtitles[0].language.opensubtitles
        if new_code not in existing_subtitles:
            current_subtitles.remove(new_code)
        current_subtitles.append('und')

    return current_subtitles, new_subtitles


def refresh_subtitles(episode_info, existing_subtitles):
    video = get_video(episode_info['location'])
    if not video:
        logger.log(u"Exception caught in subliminal.scan_video, subtitles couldn't be refreshed", logger.DEBUG)
        return existing_subtitles, None
    current_subtitles = get_subtitles(video)
    if existing_subtitles == current_subtitles:
        logger.log(u'No changed subtitles for {} {}'.format
                   (episode_info['show_name'], episode_num(episode_info['season'], episode_info['episode']) or
                    episode_num(episode_info['season'], episode_info['episode'], numbering='absolute')), logger.DEBUG)
        return existing_subtitles, None
    else:
        return current_subtitles, True


def get_video(video_path, subtitles_path=None):
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
        if not sickbeard.EMBEDDED_SUBTITLES_ALL and video_path.endswith('.mkv'):
            video = subliminal.scan_video(video_path, subtitles=True, embedded_subtitles=True,
                                          subtitles_dir=subtitles_path)
        else:
            video = subliminal.scan_video(video_path, subtitles=True, embedded_subtitles=False,
                                          subtitles_dir=subtitles_path)
    except Exception as error:
        logger.log(u'Exception: {}'.format(error), logger.DEBUG)
        return None

    return video


def get_subtitles_path(video_path):
    if os.path.isabs(sickbeard.SUBTITLES_DIR):
        new_subtitles_path = sickbeard.SUBTITLES_DIR
    elif sickbeard.SUBTITLES_DIR:
        new_subtitles_path = os.path.join(os.path.dirname(video_path), sickbeard.SUBTITLES_DIR)
        dir_exists = sickbeard.helpers.makeDir(new_subtitles_path)
        if not dir_exists:
            logger.log(u'Unable to create subtitles folder {}'.format(new_subtitles_path), logger.ERROR)
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


class SubtitlesFinder(object):
    """The SubtitlesFinder will be executed every hour but will not necessarly search and download subtitles.

    Only if the defined rule is true.
    """

    def __init__(self):
        self.amActive = False

    @staticmethod
    def subtitles_download_in_pp():  # pylint: disable=too-many-locals, too-many-branches, too-many-statements
        logger.log(u'Checking for needed subtitles in Post-Process folder', logger.INFO)

        providers = enabled_service_list()
        provider_configs = {'addic7ed': {'username': sickbeard.ADDIC7ED_USER,
                                         'password': sickbeard.ADDIC7ED_PASS},
                            'itasa': {'username': sickbeard.ITASA_USER,
                                         'password': sickbeard.ITASA_PASS},
                            'legendastv': {'username': sickbeard.LEGENDASTV_USER,
                                           'password': sickbeard.LEGENDASTV_PASS},
                            'opensubtitles': {'username': sickbeard.OPENSUBTITLES_USER,
                                              'password': sickbeard.OPENSUBTITLES_PASS}}

        pool = ProviderPool(providers=providers, provider_configs=provider_configs)

        # Search for all wanted languages
        languages = {from_code(language) for language in wanted_languages()}
        if not languages:
            return

        # Dict of language exceptions to use with subliminal
        language_exceptions = {'pt-br': 'pob'}

        run_post_process = False
        # Check if PP folder is set
        if sickbeard.TV_DOWNLOAD_DIR and os.path.isdir(sickbeard.TV_DOWNLOAD_DIR):

            for root, _, files in os.walk(sickbeard.TV_DOWNLOAD_DIR, topdown=False):
                rar_files = [rar_file for rar_file in files if isRarFile(rar_file)]
                if rar_files and sickbeard.UNPACK:
                    video_files = [video_file for video_file in files if isMediaFile(video_file)]
                    if u'_UNPACK' not in root and (not video_files or root == sickbeard.TV_DOWNLOAD_DIR):
                        logger.log(u'Found rar files in post-process folder: {}'.format(rar_files), logger.DEBUG)
                        result = processTV.ProcessResult()
                        processTV.unRAR(root, rar_files, False, result)
                elif rar_files and not sickbeard.UNPACK:
                    logger.log(u'Unpack is disabled. Skipping: {}'.format(rar_files), logger.WARNING)

            for root, _, files in os.walk(sickbeard.TV_DOWNLOAD_DIR, topdown=False):
                for filename in sorted(files):
                    try:
                        # Remove non release groups from video file. Needed to match subtitles
                        new_filename = remove_non_release_groups(filename)
                        if new_filename != filename:
                            os.rename(filename, new_filename)
                            filename = new_filename
                    except Exception as error:
                        logger.log(u"Couldn't remove non release groups from video file. Error: {}".format
                                   (ex(error)), logger.DEBUG)

                    # Delete unwanted subtitles before downloading new ones
                    if sickbeard.SUBTITLES_MULTI and sickbeard.SUBTITLES_KEEP_ONLY_WANTED and filename.rpartition('.')[2] in subtitle_extensions:
                        subtitle_language = filename.rsplit('.', 2)[1].lower()
                        if len(subtitle_language) == 2 and subtitle_language in language_converters['opensubtitles'].codes:
                            subtitle_language = Language.fromcode(subtitle_language, 'alpha2').opensubtitles
                        elif subtitle_language in language_exceptions:
                            subtitle_language = language_exceptions.get(subtitle_language, subtitle_language)
                        elif subtitle_language not in language_converters['opensubtitles'].codes:
                            subtitle_language = 'unknown'
                        if subtitle_language not in sickbeard.SUBTITLES_LANGUAGES:
                            try:
                                os.remove(os.path.join(root, filename))
                                logger.log(u"Deleted '{}' because we don't want subtitle language '{}'. We only want '{}' language(s)".format
                                           (filename, subtitle_language, ','.join(sickbeard.SUBTITLES_LANGUAGES)), logger.DEBUG)
                            except Exception as error:
                                logger.log(u"Couldn't delete subtitle: {}. Error: {}".format(filename, ex(error)), logger.DEBUG)

                    if isMediaFile(filename) and processTV.subtitles_enabled(filename):
                        try:
                            video = subliminal.scan_video(os.path.join(root, filename),
                                                          subtitles=False, embedded_subtitles=False)
                            subtitles_list = pool.list_subtitles(video, languages)

                            for provider in providers:
                                if provider in pool.discarded_providers:
                                    logger.log(u'Could not search in {} provider. Discarding for now'.format(provider), logger.DEBUG)

                            if not subtitles_list:
                                logger.log(u'No subtitles found for {}'.format
                                           (os.path.join(root, filename)), logger.DEBUG)
                                continue

                            logger.log(u'Found subtitle(s) canditate(s) for {}'.format(filename), logger.INFO)
                            hearing_impaired = sickbeard.SUBTITLES_HEARING_IMPAIRED
                            user_score = 213 if sickbeard.SUBTITLES_PERFECT_MATCH else 198
                            found_subtitles = pool.download_best_subtitles(subtitles_list, video, languages=languages,
                                                                           hearing_impaired=hearing_impaired,
                                                                           min_score=user_score,
                                                                           only_one=not sickbeard.SUBTITLES_MULTI)

                            for subtitle in subtitles_list:
                                score = subliminal.score.compute_score(subtitle, video, hearing_impaired=sickbeard.SUBTITLES_HEARING_IMPAIRED)
                                logger.log(u'[{}] Subtitle score for {} is: {} (min={})'.format
                                           (subtitle.provider_name, subtitle.id, score, user_score), logger.DEBUG)

                            downloaded_languages = set()
                            for subtitle in found_subtitles:
                                logger.log(u'Found subtitle for {} in {} provider with language {}'.format
                                           (os.path.join(root, filename), subtitle.provider_name,
                                            subtitle.language.opensubtitles), logger.INFO)
                                subliminal.save_subtitles(video, found_subtitles, directory=root,
                                                          single=not sickbeard.SUBTITLES_MULTI)

                                subtitles_multi = not sickbeard.SUBTITLES_MULTI
                                subtitle_path = subliminal.subtitle.get_subtitle_path(video.name,
                                                                                      None if subtitles_multi else
                                                                                      subtitle.language)
                                if root is not None:
                                    subtitle_path = os.path.join(root, os.path.split(subtitle_path)[1])
                                sickbeard.helpers.chmodAsParent(subtitle_path)
                                sickbeard.helpers.fixSetGroupID(subtitle_path)

                                downloaded_languages.add(subtitle.language.opensubtitles)

                            # Don't run post processor unless at least one file has all of the needed subtitles
                            if not needs_subtitles(downloaded_languages):
                                run_post_process = True
                        except Exception as error:
                            logger.log(u'Error occurred when downloading subtitles for: {}. Error: {}'.format
                                       (os.path.join(root, filename), ex(error)))
            if run_post_process:
                logger.log(u'Starting post-process with default settings now that we found subtitles')
                processTV.processDir(sickbeard.TV_DOWNLOAD_DIR)

    def run(self, force=False):  # pylint: disable=too-many-branches, too-many-statements, too-many-locals
        if not sickbeard.USE_SUBTITLES:
            return

        if len(sickbeard.subtitles.enabled_service_list()) < 1:
            logger.log(u'Not enough services selected. At least 1 service is required to '
                       'search subtitles in the background', logger.WARNING)
            return

        self.amActive = True

        def dhm(td):
            days = td.days
            hours = td.seconds // 60 ** 2
            minutes = (td.seconds // 60) % 60
            ret = (u'', '{} days, '.format(days))[days > 0] + \
                (u'', '{} hours, '.format(hours))[hours > 0] + \
                (u'', '{} minutes'.format(minutes))[minutes > 0]
            if days == 1:
                ret = ret.replace('days', 'day')
            if hours == 1:
                ret = ret.replace('hours', 'hour')
            if minutes == 1:
                ret = ret.replace('minutes', 'minute')
            return ret.rstrip(', ')

        if sickbeard.SUBTITLES_DOWNLOAD_IN_PP:
            self.subtitles_download_in_pp()

        logger.log(u'Checking for missed subtitles', logger.INFO)

        database = db.DBConnection()
        sql_results = database.select(
            "SELECT s.show_name, e.showid, e.season, e.episode, "
            "e.status, e.subtitles, e.subtitles_searchcount AS searchcount, "
            "e.subtitles_lastsearch AS lastsearch, e.location, (? - e.airdate) as age "
            "FROM tv_episodes AS e INNER JOIN tv_shows AS s "
            "ON (e.showid = s.indexer_id) "
            "WHERE s.subtitles = 1 AND e.subtitles NOT LIKE ? "
            "AND e.location != '' AND e.status IN (%s) ORDER BY age ASC" %
            ','.join(['?'] * len(Quality.DOWNLOADED)),
            [datetime.datetime.now().toordinal(), wanted_languages(True)] + Quality.DOWNLOADED
        )

        if not sql_results:
            logger.log(u'No subtitles to download', logger.INFO)
            self.amActive = False
            return

        for ep_to_sub in sql_results:
            try:
                # Encode path to system encoding.
                subtitle_path = ep_to_sub['location'].encode(sickbeard.SYS_ENCODING)
            except UnicodeEncodeError:
                # Fallback to UTF-8.
                subtitle_path = ep_to_sub['location'].encode('utf-8')
            if not os.path.isfile(subtitle_path):
                logger.log(u'Episode file does not exist, cannot download subtitles for {} {}'.format
                           (ep_to_sub['show_name'], episode_num(ep_to_sub['season'], ep_to_sub['episode']) or
                            episode_num(ep_to_sub['season'], ep_to_sub['episode'], numbering='absolute')), logger.DEBUG)
                continue

            if not needs_subtitles(ep_to_sub['subtitles']):
                logger.log(u'Episode already has all needed subtitles, skipping {} {}'.format
                           (ep_to_sub['show_name'], episode_num(ep_to_sub['season'], ep_to_sub['episode']) or
                            episode_num(ep_to_sub['season'], ep_to_sub['episode'], numbering='absolute')), logger.DEBUG)
                continue

            try:
                lastsearched = datetime.datetime.strptime(ep_to_sub['lastsearch'], dateTimeFormat)
            except ValueError:
                lastsearched = datetime.datetime.min

            try:
                if not force:
                    now = datetime.datetime.now()
                    days = int(ep_to_sub['age'])
                    delay_time = datetime.timedelta(hours=8 if days < 10 else 7 * 24 if days < 30 else 30 * 24)

                    # Search every hour for the first 24 hours since aired, then every 8 hours until 10 days passes
                    # After 10 days, search every 7 days, after 30 days search once a month
                    # Will always try an episode regardless of age at least 2 times
                    if lastsearched + delay_time > now and int(ep_to_sub['searchcount']) > 2 and days:
                        logger.log(u'Subtitle search for {} {} delayed for {}'.format
                                   (ep_to_sub['show_name'], episode_num(ep_to_sub['season'], ep_to_sub['episode']) or
                                    episode_num(ep_to_sub['season'], ep_to_sub['episode'], numbering='absolute'),
                                    dhm(lastsearched + delay_time - now)), logger.DEBUG)
                        continue

                logger.log(u'Searching for missing subtitles of {} {}'.format
                           (ep_to_sub['show_name'], episode_num(ep_to_sub['season'], ep_to_sub['episode']) or
                            episode_num(ep_to_sub['season'], ep_to_sub['episode'], numbering='absolute')), logger.INFO)

                show_object = Show.find(sickbeard.showList, int(ep_to_sub['showid']))
                if not show_object:
                    logger.log(u'Show with ID {} not found in the database'.format(ep_to_sub['showid']), logger.DEBUG)
                    continue

                episode_object = show_object.getEpisode(ep_to_sub['season'], ep_to_sub['episode'])
                if isinstance(episode_object, str):
                    logger.log(u'{} {} not found in the database'.format
                               (ep_to_sub['show_name'], episode_num(ep_to_sub['season'], ep_to_sub['episode']) or
                                episode_num(ep_to_sub['season'], ep_to_sub['episode'], numbering='absolute')), logger.DEBUG)
                    continue

                try:
                    new_subtitles = episode_object.download_subtitles()
                except Exception as error:
                    logger.log(u'Unable to find subtitles for {} {}. Error: {}'.format
                               (ep_to_sub['show_name'], episode_num(ep_to_sub['season'], ep_to_sub['episode']) or
                                episode_num(ep_to_sub['season'], ep_to_sub['episode'], numbering='absolute'), ex(error)), logger.ERROR)
                    continue

                if new_subtitles:
                    logger.log(u'Downloaded {} subtitles for {} {}'.format
                               (', '.join(new_subtitles), ep_to_sub['show_name'], episode_num(ep_to_sub['season'], ep_to_sub['episode']) or
                                episode_num(ep_to_sub['season'], ep_to_sub['episode'], numbering='absolute')))

            except Exception as error:
                logger.log(u'Error while searching subtitles for {} {}. Error: {}'.format
                           (ep_to_sub['show_name'], episode_num(ep_to_sub['season'], ep_to_sub['episode']) or
                            episode_num(ep_to_sub['season'], ep_to_sub['episode'], numbering='absolute'), ex(error)), logger.ERROR)
                continue

        logger.log(u'Finished checking for missed subtitles', logger.INFO)
        self.amActive = False


def run_subs_extra_scripts(episode_object, subtitle, video, single=False):
    for script_name in sickbeard.SUBTITLES_EXTRA_SCRIPTS:
        script_cmd = [piece for piece in re.split("( |\\\".*?\\\"|'.*?')", script_name) if piece.strip()]
        script_cmd[0] = os.path.abspath(script_cmd[0])
        logger.log(u'Absolute path to script: {}'.format(script_cmd[0]), logger.DEBUG)

        subtitle_path = subliminal.subtitle.get_subtitle_path(video.name, None if single else subtitle.language)

        inner_cmd = script_cmd + [video.name, subtitle_path, subtitle.language.opensubtitles,
                                  episode_object['show_name'], str(episode_object['season']),
                                  str(episode_object['episode']), episode_object['name'],
                                  str(episode_object['show_indexerid'])]

        # use subprocess to run the command and capture output
        logger.log(u'Executing command: {}'.format(inner_cmd))
        try:
            process = subprocess.Popen(inner_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.STDOUT, cwd=sickbeard.PROG_DIR)
            out, _ = process.communicate()  # @UnusedVariable
            logger.log(u'Script result: {}'.format(out), logger.DEBUG)

        except Exception as error:
            logger.log(u'Unable to run subs_extra_script: {}'.format(ex(error)))
