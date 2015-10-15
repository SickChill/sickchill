# Author: Nyaran <nyayukko@gmail.com>, based on Antoine Bertin <diaoulael@gmail.com> work
# URL: http://code.google.com/p/sickbeard/
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

import datetime
import sickbeard
import traceback
import pkg_resources
import subliminal
import subprocess
from sickbeard.common import *
from sickbeard import logger
from sickbeard import history
from sickbeard import db
from sickrage.helper.common import dateTimeFormat
from sickrage.helper.encoding import ek
from sickrage.helper.exceptions import ex
from subliminal.api import provider_manager
from enzyme import MKV, MalformedMKVError
from babelfish import Error as BabelfishError, Language, language_converters

distribution = pkg_resources.Distribution(location=os.path.dirname(os.path.dirname(__file__)), 
                                          project_name='fake_entry_points', version='1.0.0')

entry_points = {
    'subliminal.providers': [
        'addic7ed = subliminal.providers.addic7ed:Addic7edProvider',
        'napiprojekt = subliminal.providers.napiprojekt:NapiProjektProvider',
        'opensubtitles = subliminal.providers.opensubtitles:OpenSubtitlesProvider',
        'podnapisi = subliminal.providers.podnapisi:PodnapisiProvider',
        'thesubdb = subliminal.providers.thesubdb:TheSubDBProvider',
        'tvsubtitles = subliminal.providers.tvsubtitles:TVsubtitlesProvider'
    ],
    'babelfish.language_converters': [
        'addic7ed = subliminal.converters.addic7ed:Addic7edConverter',
        'tvsubtitles = subliminal.converters.tvsubtitles:TVsubtitlesConverter'
    ]
}
distribution._ep_map = pkg_resources.EntryPoint.parse_map(entry_points, distribution)
pkg_resources.working_set.add(distribution)

provider_manager.ENTRY_POINT_CACHE.pop('subliminal.providers')

subliminal.region.configure('dogpile.cache.memory')

provider_urls = {
    'addic7ed': 'http://www.addic7ed.com',
    'napiprojekt': 'http://www.napiprojekt.pl',
    'opensubtitles': 'http://www.opensubtitles.org',
    'podnapisi': 'http://www.podnapisi.net',
    'thesubdb': 'http://www.thesubdb.com',
    'tvsubtitles': 'http://www.tvsubtitles.net'
}

SINGLE = 'und'

def sortedServiceList():
    newList = []
    lmgtfy = 'http://lmgtfy.com/?q=%s'

    curIndex = 0
    for curService in sickbeard.SUBTITLES_SERVICES_LIST:
        if curService in subliminal.provider_manager.names():
            newList.append({'name': curService,
                            'url': provider_urls[curService] if curService in provider_urls else lmgtfy % curService,
                            'image': curService + '.png',
                            'enabled': sickbeard.SUBTITLES_SERVICES_ENABLED[curIndex] == 1
                           })
        curIndex += 1

    for curService in subliminal.provider_manager.names():
        if curService not in [x['name'] for x in newList]:
            newList.append({'name': curService,
                            'url': provider_urls[curService] if curService in provider_urls else lmgtfy % curService,
                            'image': curService + '.png',
                            'enabled': False,
                           })

    return newList

def getEnabledServiceList():
    return [x['name'] for x in sortedServiceList() if x['enabled']]

#Hack around this for now.
def fromietf(language):
    return Language.fromopensubtitles(language)

def isValidLanguage(language):
    try:
        langObj = fromietf(language)
    except:
        return False
    return True

def getLanguageName(language):
    return fromietf(language).name

def downloadSubtitles(subtitles_info):
    existing_subtitles = subtitles_info['subtitles']
    # First of all, check if we need subtitles
    languages = getNeededLanguages(existing_subtitles)
    if not languages:
        logger.log(u'%s: No missing subtitles for S%02dE%02d' % (subtitles_info['show.indexerid'], subtitles_info['season'], subtitles_info['episode']), logger.DEBUG)
        return (existing_subtitles, None)

    subtitles_path = getSubtitlesPath(subtitles_info['location']).encode(sickbeard.SYS_ENCODING)
    video_path = subtitles_info['location'].encode(sickbeard.SYS_ENCODING)
    providers = getEnabledServiceList()

    try:
        video = subliminal.scan_video(video_path, subtitles=False, embedded_subtitles=False)
    except Exception:
        logger.log(u'%s: Exception caught in subliminal.scan_video for S%02dE%02d' %
        (subtitles_info['show.indexerid'], subtitles_info['season'], subtitles_info['episode']), logger.DEBUG)
        return (existing_subtitles, None)

    try:
        # TODO: Add gui option for hearing_impaired parameter ?
        found_subtitles = subliminal.download_best_subtitles([video], languages=languages, hearing_impaired=False, only_one=not sickbeard.SUBTITLES_MULTI, providers=providers)
        if not found_subtitles:
            logger.log(u'%s: No subtitles found for S%02dE%02d on any provider' % (subtitles_info['show.indexerid'], subtitles_info['season'], subtitles_info['episode']), logger.DEBUG)
            return (existing_subtitles, None)

        subliminal.save_subtitles(video, found_subtitles[video], directory=subtitles_path, single=not sickbeard.SUBTITLES_MULTI)

        for video, subtitles in found_subtitles.iteritems():
            for subtitle in subtitles:
                new_video_path = subtitles_path + "/" + video.name.rsplit("/", 1)[-1]
                new_subtitles_path = subliminal.subtitle.get_subtitle_path(new_video_path, subtitle.language if sickbeard.SUBTITLES_MULTI else None)
                sickbeard.helpers.chmodAsParent(new_subtitles_path)
                sickbeard.helpers.fixSetGroupID(new_subtitles_path)

        if not sickbeard.EMBEDDED_SUBTITLES_ALL and sickbeard.SUBTITLES_EXTRA_SCRIPTS and video_path.endswith(('.mkv','.mp4')):
            run_subs_extra_scripts(subtitles_info, found_subtitles)

        current_subtitles = subtitlesLanguages(video_path)[0]
        new_subtitles = frozenset(current_subtitles).difference(existing_subtitles)

    except Exception as e:
                logger.log("Error occurred when downloading subtitles for: %s" % video_path)
                logger.log(traceback.format_exc(), logger.ERROR)
                return (existing_subtitles, None)

    if sickbeard.SUBTITLES_HISTORY:
        for video, subtitles in found_subtitles.iteritems():
            for subtitle in subtitles:
                logger.log(u'history.logSubtitle %s, %s' % (subtitle.provider_name, subtitle.language.opensubtitles), logger.DEBUG)
                history.logSubtitle(subtitles_info['show.indexerid'], subtitles_info['season'], subtitles_info['episode'], subtitles_info['status'], subtitle)

    return (current_subtitles, new_subtitles)

def getNeededLanguages(current_subtitles):
    languages = set()
    for language in frozenset(wantedLanguages()).difference(current_subtitles):
        languages.add(fromietf(language))

    return languages

# TODO: Filter here for non-languages in sickbeard.SUBTITLES_LANGUAGES
def wantedLanguages(sqlLike = False):
    wantedLanguages = [x for x in sorted(sickbeard.SUBTITLES_LANGUAGES) if x in subtitleCodeFilter()]
    if sqlLike:
        return '%' + ','.join(wantedLanguages) + '%'

    return wantedLanguages

def getSubtitlesPath(video_path):
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

def subtitlesLanguages(video_path):
    """Return a list detected subtitles for the given video file"""
    resultList = []
    save_subtitles = None

    if not sickbeard.EMBEDDED_SUBTITLES_ALL and video_path.endswith('.mkv'):
        embedded_subtitle_languages = getEmbeddedLanguages(video_path.encode(sickbeard.SYS_ENCODING))

    # Search subtitles with the absolute path
    if os.path.isabs(sickbeard.SUBTITLES_DIR):
        video_path = ek(os.path.join, sickbeard.SUBTITLES_DIR, ek(os.path.basename, video_path))
    # Search subtitles with the relative path
    elif sickbeard.SUBTITLES_DIR:
        check_subtitles_path = ek(os.path.join, ek(os.path.dirname, video_path), sickbeard.SUBTITLES_DIR)
        if not os.path.exists(check_subtitles_path):
            getSubtitlesPath(video_path)
        video_path = ek(os.path.join, ek(os.path.dirname, video_path), sickbeard.SUBTITLES_DIR, ek(os.path.basename, video_path))
    else:
        video_path = ek(os.path.join, ek(os.path.dirname, video_path), ek(os.path.basename, video_path))

    if not sickbeard.EMBEDDED_SUBTITLES_ALL and video_path.endswith('.mkv'):
        external_subtitle_languages = scan_subtitle_languages(video_path)
        subtitle_languages = external_subtitle_languages.union(embedded_subtitle_languages)
        if not sickbeard.SUBTITLES_MULTI:
            currentWantedLanguages = wantedLanguages()
            if len(currentWantedLanguages) is 1 and Language('und') in external_subtitle_languages:
                if embedded_subtitle_languages not in currentWantedLanguages and Language('und') in embedded_subtitle_languages:
                    # TODO: Replace with a checkbox
                    subtitle_languages.add(fromietf(currentWantedLanguages[0]))
                    save_subtitles = True
                elif embedded_subtitle_languages not in currentWantedLanguages and Language('und') not in embedded_subtitle_languages:
                    subtitle_languages.remove(Language('und'))
                    subtitle_languages.add(fromietf(currentWantedLanguages[0]))
                    save_subtitles = True
    else:
        subtitle_languages = scan_subtitle_languages(video_path)
        if not sickbeard.SUBTITLES_MULTI:
            if len(wantedLanguages()) is 1 and Language('und') in subtitle_languages:
                subtitle_languages.remove(Language('und'))
                subtitle_languages.add(fromietf(wantedLanguages()[0]))
                save_subtitles = True

    for language in subtitle_languages:
        if hasattr(language, 'opensubtitles') and language.opensubtitles:
            resultList.append(language.opensubtitles)
        elif hasattr(language, 'alpha3b') and language.alpha3b:
            resultList.append(language.alpha3b)
        elif hasattr(language, 'alpha3t') and language.alpha3t:
            resultList.append(language.alpha3t)
        elif hasattr(language, 'alpha2') and language.alpha2:
            resultList.append(language.alpha2)

    defaultLang = wantedLanguages()

    if ('pob' in defaultLang or 'pb' in defaultLang) and ('pt' not in defaultLang and 'por' not in defaultLang):
            resultList = [x if not x in ['por', 'pt'] else u'pob' for x in resultList]

    return (sorted(resultList), save_subtitles)

def getEmbeddedLanguages(video_path):
    embedded_subtitle_languages = set()
    try:
        with open(video_path, 'rb') as f:
            mkv = MKV(f)
            if mkv.subtitle_tracks:
                for st in mkv.subtitle_tracks:
                    if st.language:
                        try:
                            embedded_subtitle_languages.add(Language.fromalpha3b(st.language))
                        except BabelfishError:
                            logger.log('Embedded subtitle track is not a valid language', logger.DEBUG)
                            embedded_subtitle_languages.add(Language('und'))
                    elif st.name:
                        try:
                            embedded_subtitle_languages.add(Language.fromname(st.name))
                        except BabelfishError:
                            logger.log('Embedded subtitle track is not a valid language', logger.DEBUG)
                            embedded_subtitle_languages.add(Language('und'))
                    else:
                        embedded_subtitle_languages.add(Language('und'))
            else:
                logger.log('MKV has no subtitle track', logger.DEBUG)
    except MalformedMKVError:
        logger.log('MKV seems to be malformed, ignoring embedded subtitles', logger.WARNING)

    return embedded_subtitle_languages

def scan_subtitle_languages(path):
    language_extensions = tuple('.' + c for c in language_converters['opensubtitles'].codes)
    dirpath, filename = os.path.split(path)
    subtitles = set()
    for p in os.listdir(dirpath):
        if not isinstance(p, bytes) and p.startswith(os.path.splitext(filename)[0]) and p.endswith(subliminal.video.SUBTITLE_EXTENSIONS):
            if os.path.splitext(p)[0].endswith(language_extensions) and len(os.path.splitext(p)[0].rsplit('.', 1)[1]) is 2:
                subtitles.add(Language.fromopensubtitles(os.path.splitext(p)[0][-2:]))
            elif os.path.splitext(p)[0].endswith(language_extensions) and len(os.path.splitext(p)[0].rsplit('.', 1)[1]) is 3:
                subtitles.add(Language.fromopensubtitles(os.path.splitext(p)[0][-3:]))
            else:
                subtitles.add(Language('und'))

    return subtitles

# TODO: Return only languages our providers allow
def subtitleLanguageFilter():
    return [Language.fromopensubtitles(language) for language in language_converters['opensubtitles'].codes if len(language) == 3]

def subtitleCodeFilter():
    return [Language.fromopensubtitles(language).opensubtitles for language in language_converters['opensubtitles'].codes if len(language) == 3]

class SubtitlesFinder():
    """
    The SubtitlesFinder will be executed every hour but will not necessarly search
    and download subtitles. Only if the defined rule is true
    """
    def __init__(self):
        self.amActive = False

    def run(self, force=False):

        self.amActive = True
        if not sickbeard.USE_SUBTITLES:
            return

        if len(sickbeard.subtitles.getEnabledServiceList()) < 1:
            logger.log(u'Not enough services selected. At least 1 service is required to search subtitles in the background', logger.WARNING)
            return

        logger.log(u'Checking for subtitles', logger.INFO)

        # get episodes on which we want subtitles
        # criteria is:
        #  - show subtitles = 1
        #  - episode subtitles != config wanted languages or SINGLE (depends on config multi)
        #  - search count < 2 and diff(airdate, now) > 1 week : now -> 1d
        #  - search count < 7 and diff(airdate, now) <= 1 week : now -> 4h -> 8h -> 16h -> 1d -> 1d -> 1d

        today = datetime.date.today().toordinal()

        # you have 5 minutes to understand that one. Good luck
        myDB = db.DBConnection()

        sqlResults = myDB.select('SELECT s.show_name, e.showid, e.season, e.episode, e.status, e.subtitles, ' +
        'e.subtitles_searchcount AS searchcount, e.subtitles_lastsearch AS lastsearch, e.location, (? - e.airdate) AS airdate_daydiff ' +
        'FROM tv_episodes AS e INNER JOIN tv_shows AS s ON (e.showid = s.indexer_id) ' +
        'WHERE s.subtitles = 1 AND e.subtitles NOT LIKE (?) ' +
        'AND (e.subtitles_searchcount <= 2 OR (e.subtitles_searchcount <= 7 AND airdate_daydiff <= 7)) ' +
        'AND e.location != ""', [today, wantedLanguages(True)])

        if len(sqlResults) == 0:
            logger.log('No subtitles to download', logger.INFO)
            return

        rules = self._getRules()
        now = datetime.datetime.now()
        for epToSub in sqlResults:

            if not ek(os.path.isfile, epToSub['location']):
                logger.log('Episode file does not exist, cannot download subtitles for episode %dx%d of show %s' % (epToSub['season'], epToSub['episode'], epToSub['show_name']), logger.DEBUG)
                continue

            # Old shows rule
            throwaway = datetime.datetime.strptime('20110101', '%Y%m%d')
            if ((epToSub['airdate_daydiff'] > 7 and epToSub['searchcount'] < 2 and now - datetime.datetime.strptime(epToSub['lastsearch'], dateTimeFormat) > datetime.timedelta(hours=rules['old'][epToSub['searchcount']])) or
                # Recent shows rule
                (epToSub['airdate_daydiff'] <= 7 and epToSub['searchcount'] < 7 and now - datetime.datetime.strptime(epToSub['lastsearch'], dateTimeFormat) > datetime.timedelta(hours=rules['new'][epToSub['searchcount']]))):
                logger.log('Downloading subtitles for episode %dx%d of show %s' % (epToSub['season'], epToSub['episode'], epToSub['show_name']), logger.DEBUG)

                showObj = sickbeard.helpers.findCertainShow(sickbeard.showList, int(epToSub['showid']))
                if not showObj:
                    logger.log(u'Show not found', logger.DEBUG)
                    return

                epObj = showObj.getEpisode(int(epToSub["season"]), int(epToSub["episode"]))
                if isinstance(epObj, str):
                    logger.log(u'Episode not found', logger.DEBUG)
                    return

                existing_subtitles = epObj.subtitles

                try:
                    epObj.downloadSubtitles()
                except Exception as e:
                    logger.log(u'Unable to find subtitles', logger.DEBUG)
                    logger.log(str(e), logger.DEBUG)
                    return

                newSubtitles = frozenset(epObj.subtitles).difference(existing_subtitles)
                if newSubtitles:
                    logger.log(u'Downloaded subtitles for S%02dE%02d in %s' % (epToSub["season"], epToSub["episode"], ', '.join(newSubtitles)))

        self.amActive = False

    def _getRules(self):
        """
        Define the hours to wait between 2 subtitles search depending on:
        - the episode: new or old
        - the number of searches done so far (searchcount), represented by the index of the list
        """
        return {'old': [0, 24], 'new': [0, 4, 8, 4, 16, 24, 24]}


def run_subs_extra_scripts(epObj, foundSubs):

    for curScriptName in sickbeard.SUBTITLES_EXTRA_SCRIPTS:
        script_cmd = [piece for piece in re.split("( |\\\".*?\\\"|'.*?')", curScriptName) if piece.strip()]
        script_cmd[0] = ek(os.path.abspath, script_cmd[0])
        logger.log(u"Absolute path to script: " + script_cmd[0], logger.DEBUG)

        for video, subs in foundSubs.iteritems():
            subpaths = []
            for sub in subs:
                subpath = subliminal.subtitle.get_subtitle_path(video.name, sub.language)
                if os.path.isabs(sickbeard.SUBTITLES_DIR):
                    subpath = ek(os.path.join, sickbeard.SUBTITLES_DIR, ek(os.path.basename, subpath))
                elif sickbeard.SUBTITLES_DIR:
                    subpath = ek(os.path.join, ek(os.path.dirname, subpath), sickbeard.SUBTITLES_DIR, ek(os.path.basename, subpath))

                inner_cmd = script_cmd + [video.name, subpath, sub.language.opensubtitles, epObj['show.name'],
                                         str(epObj['season']), str(epObj['episode']), epObj['name'], str(epObj['show.indexerid'])]

                # use subprocess to run the command and capture output
                logger.log(u"Executing command: %s" % inner_cmd)
                try:
                    p = subprocess.Popen(inner_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, cwd=sickbeard.PROG_DIR)
                    out, err = p.communicate()  # @UnusedVariable
                    logger.log(u"Script result: %s" % out, logger.DEBUG)

                except Exception as e:
                    logger.log(u"Unable to run subs_extra_script: " + ex(e))
