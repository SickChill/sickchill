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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

import os
import re
import datetime
import traceback
import subliminal
import subprocess
import pkg_resources
import sickbeard
from subliminal.api import provider_manager
from babelfish import Language, language_converters
from sickbeard import logger
from sickbeard import history
from sickbeard import db
from sickbeard import processTV
from sickrage.helper.common import media_extensions, dateTimeFormat
from sickrage.helper.encoding import ek
from sickrage.helper.exceptions import ex

DISTRIBUTION = pkg_resources.Distribution(location=os.path.dirname(os.path.dirname(__file__)),
                                          project_name='fake_entry_points', version='1.0.0')

ENTRY_POINTS = {
    'subliminal.providers': [
        'addic7ed = subliminal.providers.addic7ed:Addic7edProvider',
        'legendastv = subliminal.providers.legendastv:LegendasTvProvider',
        'napiprojekt = subliminal.providers.napiprojekt:NapiProjektProvider',
        'opensubtitles = subliminal.providers.opensubtitles:OpenSubtitlesProvider',
        'podnapisi = subliminal.providers.podnapisi:PodnapisiProvider',
        'thesubdb = subliminal.providers.thesubdb:TheSubDBProvider',
        'tvsubtitles = subliminal.providers.tvsubtitles:TVsubtitlesProvider'
    ],
    'babelfish.language_converters': [
        'addic7ed = subliminal.converters.addic7ed:Addic7edConverter',
        'legendastv = subliminal.converters.legendastv:LegendasTvConverter',
        'thesubdb = subliminal.converters.thesubdb:TheSubDBConverter',
        'tvsubtitles = subliminal.converters.tvsubtitles:TVsubtitlesConverter'
    ]
}

# pylint: disable=W0212
# Access to a protected member of a client class
DISTRIBUTION._ep_map = pkg_resources.EntryPoint.parse_map(ENTRY_POINTS, DISTRIBUTION)
pkg_resources.working_set.add(DISTRIBUTION)

provider_manager.ENTRY_POINT_CACHE.pop('subliminal.providers')

subliminal.region.configure('dogpile.cache.memory')

PROVIDER_URLS = {
    'addic7ed': 'http://www.addic7ed.com',
    'legendastv': 'http://www.legendas.tv',
    'napiprojekt': 'http://www.napiprojekt.pl',
    'opensubtitles': 'http://www.opensubtitles.org',
    'podnapisi': 'http://www.podnapisi.net',
    'thesubdb': 'http://www.thesubdb.com',
    'tvsubtitles': 'http://www.tvsubtitles.net'
}


def sortedServiceList():
    new_list = []
    lmgtfy = 'http://lmgtfy.com/?q=%s'

    current_index = 0
    for current_service in sickbeard.SUBTITLES_SERVICES_LIST:
        if current_service in subliminal.provider_manager.names():
            new_list.append({'name': current_service,
                             'url': PROVIDER_URLS[current_service] if current_service in PROVIDER_URLS else
                                    lmgtfy % current_service,
                             'image': current_service + '.png',
                             'enabled': sickbeard.SUBTITLES_SERVICES_ENABLED[current_index] == 1
                            })
        current_index += 1

    for current_service in subliminal.provider_manager.names():
        if current_service not in [x['name'] for x in new_list]:
            new_list.append({'name': current_service,
                             'url': PROVIDER_URLS[current_service] if current_service in PROVIDER_URLS else
                                    lmgtfy % current_service,
                             'image': current_service + '.png',
                             'enabled': False,
                            })

    return new_list


def getEnabledServiceList():
    return [x['name'] for x in sortedServiceList() if x['enabled']]


# Hack around this for now.
def fromietf(language):
    return Language.fromopensubtitles(language)


def isValidLanguage(language):
    try:
        fromietf(language)
    except Exception:
        return False
    return True


def download_subtitles(subtitles_info):
    existing_subtitles = subtitles_info['subtitles']

    # Check if we really need subtitles
    languages = get_needed_languages(existing_subtitles)
    if not languages:
        logger.log(u'No subtitles needed for %s S%02dE%02d'
                   % (subtitles_info['show.name'], subtitles_info['season'],
                      subtitles_info['episode']), logger.DEBUG)
        return (existing_subtitles, None)

    subtitles_path = get_subtitles_path(subtitles_info['location']).encode(sickbeard.SYS_ENCODING)
    video_path = subtitles_info['location'].encode(sickbeard.SYS_ENCODING)

    video = get_video(video_path, subtitles_path=subtitles_path)
    if not video:
        logger.log(u'Exception caught in subliminal.scan_video for %s S%02dE%02d'
                   % (subtitles_info['show.name'], subtitles_info['season'],
                      subtitles_info['episode']), logger.DEBUG)
        return (existing_subtitles, None)

    providers = getEnabledServiceList()
    provider_configs = {'addic7ed': {'username': sickbeard.ADDIC7ED_USER,
                                     'password': sickbeard.ADDIC7ED_PASS},
                        'legendastv': {'username': sickbeard.LEGENDASTV_USER,
                                       'password': sickbeard.LEGENDASTV_PASS},
                        'opensubtitles': {'username': sickbeard.OPENSUBTITLES_USER,
                                          'password': sickbeard.OPENSUBTITLES_PASS}}

    pool = subliminal.api.ProviderPool(providers=providers, provider_configs=provider_configs)

    try:
        subtitles_list = pool.list_subtitles(video, languages)
        if not subtitles_list:
            logger.log(u'No subtitles found for %s S%02dE%02d on any provider'
                       % (subtitles_info['show.name'], subtitles_info['season'],
                          subtitles_info['episode']), logger.DEBUG)
            return (existing_subtitles, None)

        found_subtitles = pool.download_best_subtitles(subtitles_list, video, languages=languages,
                                                       hearing_impaired=sickbeard.SUBTITLES_HEARING_IMPAIRED,
                                                       only_one=not sickbeard.SUBTITLES_MULTI)

        subliminal.save_subtitles(video, found_subtitles, directory=subtitles_path,
                                  single=not sickbeard.SUBTITLES_MULTI)

    except Exception:
        logger.log(u"Error occurred when downloading subtitles for: %s" % video_path)
        logger.log(traceback.format_exc(), logger.ERROR)
        return (existing_subtitles, None)

    for subtitle in found_subtitles:
        subtitle_path = subliminal.subtitle.get_subtitle_path(video.name,
                                                              None if not sickbeard.SUBTITLES_MULTI else
                                                              subtitle.language)
        if subtitles_path is not None:
            subtitle_path = os.path.join(subtitles_path, os.path.split(subtitle_path)[1])
        sickbeard.helpers.chmodAsParent(subtitle_path)
        sickbeard.helpers.fixSetGroupID(subtitle_path)

    if (not sickbeard.EMBEDDED_SUBTITLES_ALL and sickbeard.SUBTITLES_EXTRA_SCRIPTS and
            video_path.rsplit(".", 1)[1] in media_extensions):
        run_subs_extra_scripts(subtitles_info, found_subtitles, video, single=not sickbeard.SUBTITLES_MULTI)

    current_subtitles = [subtitle.language.opensubtitles for subtitle in found_subtitles]
    new_subtitles = frozenset(current_subtitles).difference(existing_subtitles)
    current_subtitles += existing_subtitles

    if sickbeard.SUBTITLES_HISTORY:
        for subtitle in found_subtitles:
            logger.log(u'history.logSubtitle %s, %s' % (subtitle.provider_name,
                                                        subtitle.language.opensubtitles), logger.DEBUG)
            history.logSubtitle(subtitles_info['show.indexerid'], subtitles_info['season'],
                                subtitles_info['episode'], subtitles_info['status'], subtitle)

    return (current_subtitles, new_subtitles)


def get_needed_languages(subtitles):
    languages = set()
    for language in frozenset(wantedLanguages()).difference(subtitles):
        languages.add(fromietf(language))

    return languages


# TODO: Filter here for non-languages in sickbeard.SUBTITLES_LANGUAGES
def wantedLanguages(sql_like=None):
    wanted = [x for x in sorted(sickbeard.SUBTITLES_LANGUAGES) if x in subtitle_code_filter()]
    if sql_like:
        return '%' + ','.join(wanted) + '%'

    return wanted


def refresh_subtitles(episode_info, existing_subtitles):
    current_subtitles = get_subtitles(get_video(episode_info['location']))
    if existing_subtitles == current_subtitles:
        logger.log(u'No changed subtitles for %s S%02dE%02d'
                   % (episode_info['show.name'], episode_info['season'],
                      episode_info['episode']), logger.DEBUG)
        return (existing_subtitles, None)
    else:
        return (current_subtitles, True)


def get_video(video_path, subtitles_path=None):
    if not subtitles_path:
        subtitles_path = get_subtitles_path(video_path).encode(sickbeard.SYS_ENCODING)

    try:
        if not sickbeard.EMBEDDED_SUBTITLES_ALL and video_path.endswith('.mkv'):
            video = subliminal.scan_video(video_path, subtitles=True, embedded_subtitles=True,
                                          subtitles_dir=subtitles_path)
        else:
            video = subliminal.scan_video(video_path, subtitles=True, embedded_subtitles=False,
                                          subtitles_dir=subtitles_path)
    except Exception:
        return None

    return video


def get_subtitles_path(video_path):
    if os.path.isabs(sickbeard.SUBTITLES_DIR):
        new_subtitles_path = sickbeard.SUBTITLES_DIR
    elif sickbeard.SUBTITLES_DIR:
        new_subtitles_path = ek(os.path.join, ek(os.path.dirname, video_path), sickbeard.SUBTITLES_DIR)
        dir_exists = sickbeard.helpers.makeDir(new_subtitles_path)
        if not dir_exists:
            logger.log(u'Unable to create subtitles folder ' + new_subtitles_path, logger.ERROR)
        else:
            sickbeard.helpers.chmodAsParent(new_subtitles_path)
    else:
        new_subtitles_path = ek(os.path.join, ek(os.path.dirname, video_path))

    return new_subtitles_path


def get_subtitles(video):
    """Return a sorted list of detected subtitles for the given video file"""

    result_list = []

    if not video.subtitle_languages:
        return result_list

    if not sickbeard.SUBTITLES_MULTI:
        if len(wantedLanguages()) == 1 and Language('und') in video.subtitle_languages:
            video.subtitle_languages.remove(Language('und'))
            video.subtitle_languages.add(fromietf(wantedLanguages()[0]))

    for language in video.subtitle_languages:
        if hasattr(language, 'opensubtitles') and language.opensubtitles:
            result_list.append(language.opensubtitles)

    return sorted(result_list)


# TODO: Return only languages our providers allow
def subtitleLanguageFilter():
    return [Language.fromopensubtitles(language) for language
            in language_converters['opensubtitles'].codes if len(language) == 3]


def subtitle_code_filter():
    return [Language.fromopensubtitles(language).opensubtitles for language
            in language_converters['opensubtitles'].codes if len(language) == 3]


class SubtitlesFinder(object):
    """
    The SubtitlesFinder will be executed every hour but will not necessarly search
    and download subtitles. Only if the defined rule is true
    """
    def __init__(self):
        self.amActive = False

    def subtitles_download_in_pp():
        logger.log(u'Checking for needed subtitles in Post-Process folder', logger.INFO)

        providers = getEnabledServiceList()
        provider_configs = {'addic7ed': {'username': sickbeard.ADDIC7ED_USER,
                                         'password': sickbeard.ADDIC7ED_PASS},
                            'legendastv': {'username': sickbeard.LEGENDASTV_USER,
                                           'password': sickbeard.LEGENDASTV_PASS},
                            'opensubtitles': {'username': sickbeard.OPENSUBTITLES_USER,
                                              'password': sickbeard.OPENSUBTITLES_PASS}}

        pool = subliminal.api.ProviderPool(providers=providers, provider_configs=provider_configs)

        # Search for all wanted languages
        languages = set()
        for language in set(wantedLanguages()):
            languages.add(fromietf(language))
        if not languages:
            return

        run_post_process = False
        # Check if PP folder is set
        if sickbeard.TV_DOWNLOAD_DIR and os.path.isdir(sickbeard.TV_DOWNLOAD_DIR):
            for root, _, files in os.walk(sickbeard.TV_DOWNLOAD_DIR, topdown=False):
                for video_filename in sorted(files):
                    if video_filename.rsplit(".", 1)[1] in media_extensions:
                        try:
                            video = subliminal.scan_video(os.path.join(root, video_filename),
                                                          subtitles=False, embedded_subtitles=False)
                            subtitles_list = pool.list_subtitles(video, languages)

                            if not subtitles_list:
                                logger.log(u'No subtitles found for %s'
                                           % os.path.join(root, video_filename), logger.DEBUG)
                                continue

                            hearing_impaired = sickbeard.SUBTITLES_HEARING_IMPAIRED
                            found_subtitles = pool.download_best_subtitles(subtitles_list, video, languages=languages,
                                                                           hearing_impaired=hearing_impaired,
                                                                           only_one=not sickbeard.SUBTITLES_MULTI)

                            for subtitle in found_subtitles:
                                logger.log(u"Found subtitle for %s in %s provider with language %s"
                                           % (os.path.join(root, video_filename), subtitle.provider_name,
                                              subtitle.language.opensubtitles), logger.DEBUG)
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

                                run_post_process = True
                        except Exception as error:
                            logger.log(u"Error occurred when downloading subtitles for: %s. Error: %r"
                                       % (os.path.join(root, video_filename), ex(error)))
            if run_post_process:
                logger.log(u"Starting post-process with default settings now that we found subtitles")
                processTV.processDir(sickbeard.TV_DOWNLOAD_DIR)

    def run(self):

        if not sickbeard.USE_SUBTITLES:
            return

        if len(sickbeard.subtitles.getEnabledServiceList()) < 1:
            logger.log(u'Not enough services selected. At least 1 service is required to '
                       'search subtitles in the background', logger.WARNING)
            return

        self.amActive = True

        if sickbeard.SUBTITLES_DOWNLOAD_IN_PP:
            self.subtitles_download_in_pp()

        logger.log(u'Checking for subtitles', logger.INFO)

        # get episodes on which we want subtitles
        # criteria is:
        #  - show subtitles = 1
        #  - episode subtitles != config wanted languages or 'und' (depends on config multi)
        #  - search count < 2 and diff(airdate, now) > 1 week : now -> 1d
        #  - search count < 7 and diff(airdate, now) <= 1 week : now -> 4h -> 8h -> 16h -> 1d -> 1d -> 1d

        today = datetime.date.today().toordinal()
        database = db.DBConnection()

        sql_results = database.select(
            'SELECT s.show_name, e.showid, e.season, e.episode, e.status, e.subtitles, ' +
            'e.subtitles_searchcount AS searchcount, e.subtitles_lastsearch AS lastsearch, e.location, '
            '(? - e.airdate) AS airdate_daydiff ' +
            'FROM tv_episodes AS e INNER JOIN tv_shows AS s ON (e.showid = s.indexer_id) ' +
            'WHERE s.subtitles = 1 AND e.subtitles NOT LIKE (?) ' +
            'AND (e.subtitles_searchcount <= 2 OR (e.subtitles_searchcount <= 7 AND airdate_daydiff <= 7)) ' +
            'AND e.location != ""', [today, wantedLanguages(True)])

        if len(sql_results) == 0:
            logger.log(u'No subtitles to download', logger.INFO)
            self.amActive = False
            return

        rules = self._get_rules()
        now = datetime.datetime.now()
        for ep_to_sub in sql_results:

            if not ek(os.path.isfile, ep_to_sub['location']):
                logger.log(u'Episode file does not exist, cannot download subtitles for episode %dx%d of show %s'
                           % (ep_to_sub['season'], ep_to_sub['episode'], ep_to_sub['show_name']), logger.DEBUG)
                continue

            # http://bugs.python.org/issue7980#msg221094
            # I dont think this needs done here, but keeping to be safe (Recent shows rule)
            datetime.datetime.strptime('20110101', '%Y%m%d')
            if ((ep_to_sub['airdate_daydiff'] > 7 and ep_to_sub['searchcount'] < 2 and
                 now - datetime.datetime.strptime(ep_to_sub['lastsearch'], dateTimeFormat) >
                 datetime.timedelta(hours=rules['old'][ep_to_sub['searchcount']])) or
                    (ep_to_sub['airdate_daydiff'] <= 7 and ep_to_sub['searchcount'] < 7 and
                     now - datetime.datetime.strptime(ep_to_sub['lastsearch'], dateTimeFormat) >
                     datetime.timedelta(hours=rules['new'][ep_to_sub['searchcount']]))):

                logger.log(u'Downloading subtitles for episode %dx%d of show %s'
                           % (ep_to_sub['season'], ep_to_sub['episode'], ep_to_sub['show_name']), logger.DEBUG)

                show_object = sickbeard.helpers.findCertainShow(sickbeard.showList, int(ep_to_sub['showid']))
                if not show_object:
                    logger.log(u'Show not found', logger.DEBUG)
                    self.amActive = False
                    return

                episode_object = show_object.getEpisode(int(ep_to_sub["season"]), int(ep_to_sub["episode"]))
                if isinstance(episode_object, str):
                    logger.log(u'Episode not found', logger.DEBUG)
                    self.amActive = False
                    return

                existing_subtitles = episode_object.subtitles

                try:
                    episode_object.download_subtitles()
                except Exception as error:
                    logger.log(u'Unable to find subtitles', logger.DEBUG)
                    logger.log(str(error), logger.DEBUG)
                    self.amActive = False
                    return

                new_subtitles = frozenset(episode_object.subtitles).difference(existing_subtitles)
                if new_subtitles:
                    logger.log(u'Downloaded subtitles for S%02dE%02d in %s'
                               % (ep_to_sub["season"], ep_to_sub["episode"], ', '.join(new_subtitles)))

        self.amActive = False

    @staticmethod
    def _get_rules():
        """
        Define the hours to wait between 2 subtitles search depending on:
        - the episode: new or old
        - the number of searches done so far (searchcount), represented by the index of the list
        """
        return {'old': [0, 24], 'new': [0, 4, 8, 4, 16, 24, 24]}


def run_subs_extra_scripts(episode_object, found_subtitles, video, single=False):

    for script_name in sickbeard.SUBTITLES_EXTRA_SCRIPTS:
        script_cmd = [piece for piece in re.split("( |\\\".*?\\\"|'.*?')", script_name) if piece.strip()]
        script_cmd[0] = ek(os.path.abspath, script_cmd[0])
        logger.log(u"Absolute path to script: " + script_cmd[0], logger.DEBUG)

        for subtitle in found_subtitles:
            subtitle_path = subliminal.subtitle.get_subtitle_path(video.name, None if single else subtitle.language)

            inner_cmd = script_cmd + [video.name, subtitle_path, subtitle.language.opensubtitles,
                                      episode_object['show.name'], str(episode_object['season']),
                                      str(episode_object['episode']), episode_object['name'],
                                      str(episode_object['show.indexerid'])]

            # use subprocess to run the command and capture output
            logger.log(u"Executing command: %s" % inner_cmd)
            try:
                process = subprocess.Popen(inner_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                           stderr=subprocess.STDOUT, cwd=sickbeard.PROG_DIR)
                out, _ = process.communicate()  # @UnusedVariable
                logger.log(u"Script result: %s" % out, logger.DEBUG)

            except Exception as error:
                logger.log(u"Unable to run subs_extra_script: " + ex(error))
