# Author: Nic Wolfe <nic@wolfeden.ca>
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
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

import traceback
import os
import time
import urllib
import re
import datetime
import codecs

import sickbeard
from sickbeard import config, sab
from sickbeard import clients
from sickbeard import notifiers, processTV
from sickbeard import ui
from sickbeard import logger, helpers, classes, db
from sickbeard import search_queue
from sickbeard import naming
from sickbeard import subtitles
from sickbeard import network_timezones
from sickbeard.providers import newznab, rsstorrent
from sickbeard.common import Quality, Overview, statusStrings, qualityPresetStrings, cpu_presets
from sickbeard.common import SNATCHED, UNAIRED, IGNORED, WANTED, FAILED, SKIPPED
from sickbeard.common import SD, HD720p, HD1080p
from sickbeard.blackandwhitelist import BlackAndWhiteList, short_group_names
from sickbeard.browser import foldersAtPath
from sickbeard.scene_numbering import get_scene_numbering, set_scene_numbering, get_scene_numbering_for_show, \
    get_xem_numbering_for_show, get_scene_absolute_numbering_for_show, get_xem_absolute_numbering_for_show, \
    get_scene_absolute_numbering
from sickbeard.webapi import function_mapper

from imdbPopular import imdb_popular

from dateutil import tz
from unrar2 import RarFile
import adba
from libtrakt import TraktAPI
from libtrakt.exceptions import traktException
from sickrage.helper.encoding import ek, ss
from sickrage.helper.exceptions import CantRefreshShowException, CantUpdateShowException, ex
from sickrage.helper.exceptions import MultipleShowObjectsException, NoNFOException, ShowDirectoryNotFoundException
from sickrage.media.ShowBanner import ShowBanner
from sickrage.media.ShowFanArt import ShowFanArt
from sickrage.media.ShowNetworkLogo import ShowNetworkLogo
from sickrage.media.ShowPoster import ShowPoster
from sickrage.show.ComingEpisodes import ComingEpisodes
from sickrage.show.History import History as HistoryTool
from sickrage.show.Show import Show
from sickrage.system.Restart import Restart
from sickrage.system.Shutdown import Shutdown
from versionChecker import CheckVersion

import requests
import markdown2

try:
    import json
except ImportError:
    import simplejson as json

from mako.template import Template as MakoTemplate
from mako.lookup import TemplateLookup

from tornado.routes import route
from tornado.web import RequestHandler, HTTPError, authenticated
from tornado.gen import coroutine
from tornado.ioloop import IOLoop
from tornado.concurrent import run_on_executor
from concurrent.futures import ThreadPoolExecutor

class PageTemplate(MakoTemplate):

    def __init__(self, rh, file, *args, **kwargs):
        self.arguments = {}

        self.mako_path = os.path.join(sickbeard.PROG_DIR, "gui/" + sickbeard.GUI_NAME + "/views/")
        self.mako_cache = os.path.join(sickbeard.CACHE_DIR, 'mako')
        self.mako_lookup = TemplateLookup(directories=[self.mako_path], module_directory=self.mako_cache, format_exceptions=True)

        kwargs['filename'] = os.path.join(self.mako_path, file)
        kwargs['module_directory'] = self.mako_cache
        kwargs['lookup'] = self.mako_lookup
        kwargs['format_exceptions'] = True

        super(PageTemplate, self).__init__(*args, **kwargs)

        self.arguments['srRoot'] = sickbeard.WEB_ROOT
        self.arguments['sbHttpPort'] = sickbeard.WEB_PORT
        self.arguments['sbHttpsPort'] = sickbeard.WEB_PORT
        self.arguments['sbHttpsEnabled'] = sickbeard.ENABLE_HTTPS
        self.arguments['sbHandleReverseProxy'] = sickbeard.HANDLE_REVERSE_PROXY
        self.arguments['sbThemeName'] = sickbeard.THEME_NAME
        self.arguments['sbDefaultPage'] = sickbeard.DEFAULT_PAGE
        self.arguments['sbLogin'] = rh.get_current_user()
        self.arguments['sbStartTime'] = rh.startTime

        if rh.request.headers['Host'][0] == '[':
            self.arguments['sbHost'] = re.match("^\[.*\]", rh.request.headers['Host'], re.X | re.M | re.S).group(0)
        else:
            self.arguments['sbHost'] = re.match("^[^:]+", rh.request.headers['Host'], re.X | re.M | re.S).group(0)

        if "X-Forwarded-Host" in rh.request.headers:
            self.arguments['sbHost'] = rh.request.headers['X-Forwarded-Host']
        if "X-Forwarded-Port" in rh.request.headers:
            sbHttpPort = rh.request.headers['X-Forwarded-Port']
            self.arguments['sbHttpsPort'] = sbHttpPort
        if "X-Forwarded-Proto" in rh.request.headers:
            self.arguments['sbHttpsEnabled'] = True if rh.request.headers['X-Forwarded-Proto'] == 'https' else False

        self.arguments['numErrors'] = len(classes.ErrorViewer.errors)
        self.arguments['numWarnings'] = len(classes.WarningViewer.errors)
        self.arguments['sbPID'] = str(sickbeard.PID)

        self.arguments['title'] = "FixME"
        self.arguments['header'] = "FixME"
        self.arguments['topmenu'] = "FixME"

    def render(self, *args, **kwargs):
        for key in self.arguments:
            if key not in kwargs:
                kwargs[key] = self.arguments[key]

        kwargs['makoStartTime'] = time.time()

        return super(PageTemplate, self).render(*args, **kwargs)


class BaseHandler(RequestHandler):
    startTime = 0.

    def __init__(self, *args, **kwargs):
        self.startTime = time.time()

        super(BaseHandler, self).__init__(*args, **kwargs)

    #def set_default_headers(self):
        #self.set_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')

    def write_error(self, status_code, **kwargs):
        # handle 404 http errors
        if status_code == 404:
            url = self.request.uri
            if sickbeard.WEB_ROOT and self.request.uri.startswith(sickbeard.WEB_ROOT):
                url = url[len(sickbeard.WEB_ROOT) + 1:]

            if url[:3] != 'api':
                return self.redirect('/')
            else:
                self.finish('Wrong API key used')

        elif self.settings.get("debug") and "exc_info" in kwargs:
            exc_info = kwargs["exc_info"]
            trace_info = ''.join(["%s<br/>" % line for line in traceback.format_exception(*exc_info)])
            request_info = ''.join(["<strong>%s</strong>: %s<br/>" % (k, self.request.__dict__[k] ) for k in
                                    self.request.__dict__.keys()])
            error = exc_info[1]

            self.set_header('Content-Type', 'text/html')
            self.finish("""<html>
                                 <title>%s</title>
                                 <body>
                                    <h2>Error</h2>
                                    <p>%s</p>
                                    <h2>Traceback</h2>
                                    <p>%s</p>
                                    <h2>Request Info</h2>
                                    <p>%s</p>
                                    <button onclick="window.location='%s/errorlogs/';">View Log(Errors)</button>
                                 </body>
                               </html>""" % (error, error, trace_info, request_info, sickbeard.WEB_ROOT))

    def redirect(self, url, permanent=False, status=None):
        """Sends a redirect to the given (optionally relative) URL.

        ----->>>>> NOTE: Removed self.finish <<<<<-----

        If the ``status`` argument is specified, that value is used as the
        HTTP status code; otherwise either 301 (permanent) or 302
        (temporary) is chosen based on the ``permanent`` argument.
        The default is 302 (temporary).
        """
        import urlparse
        from tornado.escape import utf8
        if not url.startswith(sickbeard.WEB_ROOT):
            url = sickbeard.WEB_ROOT + url

        if self._headers_written:
            raise Exception("Cannot redirect after headers have been written")
        if status is None:
            status = 301 if permanent else 302
        else:
            assert isinstance(status, int) and 300 <= status <= 399
        self.set_status(status)
        self.set_header("Location", urlparse.urljoin(utf8(self.request.uri),
                                                     utf8(url)))

    def get_current_user(self, *args, **kwargs):
        if not isinstance(self, UI) and sickbeard.WEB_USERNAME and sickbeard.WEB_PASSWORD:
            return self.get_secure_cookie('sickrage_user')
        else:
            return True


class WebHandler(BaseHandler):
    def __init__(self, *args, **kwargs):
        super(WebHandler, self).__init__(*args, **kwargs)
        self.io_loop = IOLoop.current()

    executor = ThreadPoolExecutor(50)

    @authenticated
    @coroutine
    def get(self, route, *args, **kwargs):
        try:
            # route -> method obj
            route = route.strip('/').replace('.', '_') or 'index'
            method = getattr(self, route)

            results = yield self.async_call(method)
            self.finish(results)

        except:
            logger.log('Failed doing webui request "%s": %s' % (route, traceback.format_exc()), logger.DEBUG)
            raise HTTPError(404)

    @run_on_executor
    def async_call(self, function):
        try:
            kwargs = self.request.arguments
            for arg, value in kwargs.iteritems():
                if len(value) == 1:
                    kwargs[arg] = value[0]

            result = function(**kwargs)
            return result
        except:
            logger.log('Failed doing webui callback: %s' % (traceback.format_exc()), logger.ERROR)
            raise

    # post uses get method
    post = get


class LoginHandler(BaseHandler):
    def get(self, *args, **kwargs):

        if self.get_current_user():
            self.redirect('/' + sickbeard.DEFAULT_PAGE +'/')
        else:
            t = PageTemplate(rh=self, file="login.mako")
            self.finish(t.render(title="Login", header="Login", topmenu="login"))

    def post(self, *args, **kwargs):

        api_key = None

        username = sickbeard.WEB_USERNAME
        password = sickbeard.WEB_PASSWORD

        if (self.get_argument('username') == username or not username) \
                and (self.get_argument('password') == password or not password):
            api_key = sickbeard.API_KEY

        if api_key:
            remember_me = int(self.get_argument('remember_me', default=0) or 0)
            self.set_secure_cookie('sickrage_user', api_key, expires_days=30 if remember_me > 0 else None)
            logger.log('User logged into the SickRage web interface', logger.INFO)
        else:
            logger.log('User attempted a failed login to the SickRage web interface from IP: ' + self.request.remote_ip, logger.WARNING)

        self.redirect('/' + sickbeard.DEFAULT_PAGE +'/')


class LogoutHandler(BaseHandler):
    def get(self, *args, **kwargs):
        self.clear_cookie("sickrage_user")
        self.redirect('/login/')

class KeyHandler(RequestHandler):
    def __init__(self, *args, **kwargs):
        super(KeyHandler, self).__init__(*args, **kwargs)

    def get(self, *args, **kwargs):
        api_key = None

        try:
            username = sickbeard.WEB_USERNAME
            password = sickbeard.WEB_PASSWORD

            if (self.get_argument('u', None) == username or not username) and \
                    (self.get_argument('p', None) == password or not password):
                api_key = sickbeard.API_KEY

            self.finish({'success': api_key is not None, 'api_key': api_key})
        except:
            logger.log('Failed doing key request: %s' % (traceback.format_exc()), logger.ERROR)
            self.finish({'success': False, 'error': 'Failed returning results'})


@route('(.*)(/?)')
class WebRoot(WebHandler):
    def __init__(self, *args, **kwargs):
        super(WebRoot, self).__init__(*args, **kwargs)

    def index(self):
        return self.redirect('/' + sickbeard.DEFAULT_PAGE +'/')

    def robots_txt(self):
        """ Keep web crawlers out """
        self.set_header('Content-Type', 'text/plain')
        return "User-agent: *\nDisallow: /"

    def apibuilder(self):
        def titler(x):
            return (helpers.remove_article(x), x)[not x or sickbeard.SORT_ARTICLE]

        myDB = db.DBConnection(row_type='dict')
        shows = sorted(sickbeard.showList, lambda x, y: cmp(titler(x.name), titler(y.name)))
        episodes = {}

        results = myDB.select(
            'SELECT episode, season, showid '
            'FROM tv_episodes '
            'ORDER BY season ASC, episode ASC'
        )

        for result in results:
            if result['showid'] not in episodes:
                episodes[result['showid']] = {}

            if result['season'] not in episodes[result['showid']]:
                episodes[result['showid']][result['season']] = []

            episodes[result['showid']][result['season']].append(result['episode'])

        if len(sickbeard.API_KEY) == 32:
            apikey = sickbeard.API_KEY
        else:
            apikey = 'API Key not generated'

        t = PageTemplate(rh=self, file='apiBuilder.mako')
        return t.render(title='API Builder', header='API Builder', shows=shows, episodes=episodes, apikey=apikey,
                        commands=function_mapper)

    def showPoster(self, show=None, which=None):
        media = None
        media_format = ('normal', 'thumb')[which in ('banner_thumb', 'poster_thumb', 'small')]

        if which[0:6] == 'banner':
            media = ShowBanner(show, media_format)
        elif which[0:6] == 'fanart':
            media = ShowFanArt(show, media_format)
        elif which[0:6] == 'poster':
            media = ShowPoster(show, media_format)
        elif which[0:7] == 'network':
            media = ShowNetworkLogo(show, media_format)

        if media is not None:
            self.set_header('Content-Type', media.get_media_type())

            return media.get_media()

        return None

    def setHomeLayout(self, layout):

        if layout not in ('poster', 'small', 'banner', 'simple', 'coverflow'):
            layout = 'poster'

        sickbeard.HOME_LAYOUT = layout
        #Dont redirect to default page so user can see new layout
        return self.redirect("/home/")

    def setPosterSortBy(self, sort):

        if sort not in ('name', 'date', 'network', 'progress'):
            sort = 'name'

        sickbeard.POSTER_SORTBY = sort
        sickbeard.save_config()

    def setPosterSortDir(self, direction):

        sickbeard.POSTER_SORTDIR = int(direction)
        sickbeard.save_config()

    def setHistoryLayout(self, layout):

        if layout not in ('compact', 'detailed'):
            layout = 'detailed'

        sickbeard.HISTORY_LAYOUT = layout

        return self.redirect("/history/")

    def toggleDisplayShowSpecials(self, show):

        sickbeard.DISPLAY_SHOW_SPECIALS = not sickbeard.DISPLAY_SHOW_SPECIALS

        return self.redirect("/home/displayShow?show=" + show)

    def setScheduleLayout(self, layout):
        if layout not in ('poster', 'banner', 'list', 'calendar'):
            layout = 'banner'

        if layout == 'calendar':
            sickbeard.COMING_EPS_SORT = 'date'

        sickbeard.COMING_EPS_LAYOUT = layout

        return self.redirect("/schedule/")

    def toggleScheduleDisplayPaused(self):

        sickbeard.COMING_EPS_DISPLAY_PAUSED = not sickbeard.COMING_EPS_DISPLAY_PAUSED

        return self.redirect("/schedule/")

    def setScheduleSort(self, sort):
        if sort not in ('date', 'network', 'show'):
            sort = 'date'

        if sickbeard.COMING_EPS_LAYOUT == 'calendar':
            sort \
                = 'date'

        sickbeard.COMING_EPS_SORT = sort

        return self.redirect("/schedule/")

    def schedule(self, layout=None):
        next_week = datetime.date.today() + datetime.timedelta(days=7)
        next_week1 = datetime.datetime.combine(next_week, datetime.time(tzinfo=network_timezones.sb_timezone))
        results = ComingEpisodes.get_coming_episodes(ComingEpisodes.categories, sickbeard.COMING_EPS_SORT, False)
        today = datetime.datetime.now().replace(tzinfo=network_timezones.sb_timezone)

        submenu = [
            {
                'title': 'Sort by:',
                'path': {
                    'Date': 'setScheduleSort/?sort=date',
                    'Show': 'setScheduleSort/?sort=show',
                    'Network': 'setScheduleSort/?sort=network',
                }
            },
            {
                'title': 'Layout:',
                'path': {
                    'Banner': 'setScheduleLayout/?layout=banner',
                    'Poster': 'setScheduleLayout/?layout=poster',
                    'List': 'setScheduleLayout/?layout=list',
                    'Calendar': 'setScheduleLayout/?layout=calendar',
                }
            },
            {
                'title': 'View Paused:',
                'path': {
                    'Hide': 'toggleScheduleDisplayPaused'
                } if sickbeard.COMING_EPS_DISPLAY_PAUSED else {
                    'Show': 'toggleScheduleDisplayPaused'
                }
            },
        ]

        # Allow local overriding of layout parameter
        if layout and layout in ('poster', 'banner', 'list', 'calendar'):
            layout = layout
        else:
            layout = sickbeard.COMING_EPS_LAYOUT

        t = PageTemplate(rh=self, file='schedule.mako')
        return t.render(submenu=submenu, next_week=next_week1, today=today, results=results, layout=layout,
                        title='Schedule', header='Schedule', topmenu='schedule')


class CalendarHandler(BaseHandler):
    def get(self, *args, **kwargs):
        if sickbeard.CALENDAR_UNPROTECTED:
            self.write(self.calendar())
        else:
            self.calendar_auth()

    @authenticated
    def calendar_auth(self):
        self.write(self.calendar())

    # Raw iCalendar implementation by Pedro Jose Pereira Vieito (@pvieito).
    #
    # iCalendar (iCal) - Standard RFC 5545 <http://tools.ietf.org/html/rfc5546>
    # Works with iCloud, Google Calendar and Outlook.
    def calendar(self):
        """ Provides a subscribeable URL for iCal subscriptions
        """

        logger.log(u"Receiving iCal request from %s" % self.request.remote_ip)

        # Create a iCal string
        ical = 'BEGIN:VCALENDAR\r\n'
        ical += 'VERSION:2.0\r\n'
        ical += 'X-WR-CALNAME:SickRage\r\n'
        ical += 'X-WR-CALDESC:SickRage\r\n'
        ical += 'PRODID://Sick-Beard Upcoming Episodes//\r\n'

        # Limit dates
        past_date = (datetime.date.today() + datetime.timedelta(weeks=-52)).toordinal()
        future_date = (datetime.date.today() + datetime.timedelta(weeks=52)).toordinal()

        # Get all the shows that are not paused and are currently on air (from kjoconnor Fork)
        myDB = db.DBConnection()
        calendar_shows = myDB.select(
            "SELECT show_name, indexer_id, network, airs, runtime FROM tv_shows WHERE ( status = 'Continuing' OR status = 'Returning Series' ) AND paused != '1'")
        for show in calendar_shows:
            # Get all episodes of this show airing between today and next month
            episode_list = myDB.select(
                "SELECT indexerid, name, season, episode, description, airdate FROM tv_episodes WHERE airdate >= ? AND airdate < ? AND showid = ?",
                (past_date, future_date, int(show["indexer_id"])))

            utc = tz.gettz('GMT')

            for episode in episode_list:

                air_date_time = network_timezones.parse_date_time(episode['airdate'], show["airs"],
                                                                  show['network']).astimezone(utc)
                air_date_time_end = air_date_time + datetime.timedelta(
                    minutes=helpers.tryInt(show["runtime"], 60))

                # Create event for episode
                ical = ical + 'BEGIN:VEVENT\r\n'
                ical = ical + 'DTSTART:' + air_date_time.strftime("%Y%m%d") + 'T' + air_date_time.strftime(
                    "%H%M%S") + 'Z\r\n'
                ical = ical + 'DTEND:' + air_date_time_end.strftime(
                    "%Y%m%d") + 'T' + air_date_time_end.strftime(
                    "%H%M%S") + 'Z\r\n'
                ical = ical + u'SUMMARY: {0} - {1}x{2} - {3}\r\n'.format(
                       show['show_name'],
                       episode['season'],
                       episode['episode'],
                       episode['name'])
                ical = ical + 'UID:Sick-Beard-' + str(datetime.date.today().isoformat()) + '-' + show[
                    'show_name'].replace(" ", "-") + '-E' + str(episode['episode']) + 'S' + str(
                    episode['season']) + '\r\n'
                if episode['description']:
                    ical = ical + u'DESCRIPTION: {0} on {1} \\n\\n {2}\r\n'.format(
                        (show['airs'] or '(Unknown airs)'),
                        (show['network'] or 'Unknown network'),
                        episode['description'].splitlines()[0])
                else:
                    ical = ical + 'DESCRIPTION:' + (show['airs'] or '(Unknown airs)') + ' on ' + (
                        show['network'] or 'Unknown network') + '\r\n'

                ical = ical + 'END:VEVENT\r\n'

        # Ending the iCal
        ical += 'END:VCALENDAR'

        return ical

@route('/ui(/?.*)')
class UI(WebRoot):
    def __init__(self, *args, **kwargs):
        super(UI, self).__init__(*args, **kwargs)

    def add_message(self):
        ui.notifications.message('Test 1', 'This is test number 1')
        ui.notifications.error('Test 2', 'This is test number 2')

        return "ok"

    def get_messages(self):
        messages = {}
        cur_notification_num = 1
        for cur_notification in ui.notifications.get_notifications(self.request.remote_ip):
            messages['notification-' + str(cur_notification_num)] = {'title': cur_notification.title,
                                                                     'message': cur_notification.message,
                                                                     'type': cur_notification.type}
            cur_notification_num += 1

        return json.dumps(messages)


@route('/browser(/?.*)')
class WebFileBrowser(WebRoot):
    def __init__(self, *args, **kwargs):
        super(WebFileBrowser, self).__init__(*args, **kwargs)

    def index(self, path='', includeFiles=False, *args, **kwargs):
        self.set_header("Content-Type", "application/json")
        return json.dumps(foldersAtPath(path, True, bool(int(includeFiles))))

    def complete(self, term, includeFiles=0, *args, **kwargs):
        self.set_header("Content-Type", "application/json")
        paths = [entry['path'] for entry in foldersAtPath(os.path.dirname(term), includeFiles=bool(int(includeFiles)))
                 if 'path' in entry]

        return json.dumps(paths)


@route('/home(/?.*)')
class Home(WebRoot):
    def __init__(self, *args, **kwargs):
        super(Home, self).__init__(*args, **kwargs)

    def _genericMessage(self, subject, message):
        t = PageTemplate(rh=self, file="genericMessage.mako")
        return t.render(message=message, subject=subject, topmenu="home", title="")

    def _getEpisode(self, show, season=None, episode=None, absolute=None):
        if show is None:
            return "Invalid show parameters"

        showObj = sickbeard.helpers.findCertainShow(sickbeard.showList, int(show))

        if showObj is None:
            return "Invalid show paramaters"

        if absolute:
            epObj = showObj.getEpisode(absolute_number=int(absolute))
        elif season and episode:
            epObj = showObj.getEpisode(int(season), int(episode))
        else:
            return "Invalid paramaters"

        if epObj is None:
            return "Episode couldn't be retrieved"

        return epObj

    def index(self):
        t = PageTemplate(rh=self, file="home.mako")
        if sickbeard.ANIME_SPLIT_HOME:
            shows = []
            anime = []
            for show in sickbeard.showList:
                if show.is_anime:
                    anime.append(show)
                else:
                    shows.append(show)
            showlists = [["Shows", shows],["Anime", anime]]
        else:
            showlists = [["Shows", sickbeard.showList]]

        return t.render(title="Home", header="Show List", topmenu="home", showlists=showlists)

    def is_alive(self, *args, **kwargs):
        if 'callback' in kwargs and '_' in kwargs:
            callback, _ = kwargs['callback'], kwargs['_']
        else:
            return "Error: Unsupported Request. Send jsonp request with 'callback' variable in the query string."

        # self.set_header('Cache-Control', 'max-age=0,no-cache,no-store')
        self.set_header('Content-Type', 'text/javascript')
        self.set_header('Access-Control-Allow-Origin', '*')
        self.set_header('Access-Control-Allow-Headers', 'x-requested-with')

        if sickbeard.started:
            return callback + '(' + json.dumps(
                {"msg": str(sickbeard.PID)}) + ');'
        else:
            return callback + '(' + json.dumps({"msg": "nope"}) + ');'

    def haveKODI(self):
        return sickbeard.USE_KODI and sickbeard.KODI_UPDATE_LIBRARY

    def havePLEX(self):
        return sickbeard.USE_PLEX and sickbeard.PLEX_UPDATE_LIBRARY

    def haveEMBY(self):
        return sickbeard.USE_EMBY

    def haveTORRENT(self):
        if sickbeard.USE_TORRENTS and sickbeard.TORRENT_METHOD != 'blackhole' \
                and (sickbeard.ENABLE_HTTPS and sickbeard.TORRENT_HOST[:5] == 'https'
                     or not sickbeard.ENABLE_HTTPS and sickbeard.TORRENT_HOST[:5] == 'http:'):
            return True
        else:
            return False

    def testSABnzbd(self, host=None, username=None, password=None, apikey=None):
        # self.set_header('Cache-Control', 'max-age=0,no-cache,no-store')

        host = config.clean_url(host)

        connection, accesMsg = sab.getSabAccesMethod(host, username, password, apikey)
        if connection:
            authed, authMsg = sab.testAuthentication(host, username, password, apikey)  # @UnusedVariable
            if authed:
                return "Success. Connected and authenticated"
            else:
                return "Authentication failed. SABnzbd expects '" + accesMsg + "' as authentication method"
        else:
            return "Unable to connect to host"


    def testTorrent(self, torrent_method=None, host=None, username=None, password=None):
        # self.set_header('Cache-Control', 'max-age=0,no-cache,no-store')

        host = config.clean_url(host)

        client = clients.getClientIstance(torrent_method)

        connection, accesMsg = client(host, username, password).testAuthentication()

        return accesMsg

    def testFreeMobile(self, freemobile_id=None, freemobile_apikey=None):

        result, message = notifiers.freemobile_notifier.test_notify(freemobile_id, freemobile_apikey)
        if result:
            return "SMS sent successfully"
        else:
            return "Problem sending SMS: " + message

    def testGrowl(self, host=None, password=None):
        # self.set_header('Cache-Control', 'max-age=0,no-cache,no-store')

        host = config.clean_host(host, default_port=23053)

        result = notifiers.growl_notifier.test_notify(host, password)
        if password is None or password == '':
            pw_append = ''
        else:
            pw_append = " with password: " + password

        if result:
            return "Registered and Tested growl successfully " + urllib.unquote_plus(host) + pw_append
        else:
            return "Registration and Testing of growl failed " + urllib.unquote_plus(host) + pw_append


    def testProwl(self, prowl_api=None, prowl_priority=0):
        # self.set_header('Cache-Control', 'max-age=0,no-cache,no-store')

        result = notifiers.prowl_notifier.test_notify(prowl_api, prowl_priority)
        if result:
            return "Test prowl notice sent successfully"
        else:
            return "Test prowl notice failed"


    def testBoxcar(self, username=None):
        # self.set_header('Cache-Control', 'max-age=0,no-cache,no-store')

        result = notifiers.boxcar_notifier.test_notify(username)
        if result:
            return "Boxcar notification succeeded. Check your Boxcar clients to make sure it worked"
        else:
            return "Error sending Boxcar notification"


    def testBoxcar2(self, accesstoken=None):
        # self.set_header('Cache-Control', 'max-age=0,no-cache,no-store')

        result = notifiers.boxcar2_notifier.test_notify(accesstoken)
        if result:
            return "Boxcar2 notification succeeded. Check your Boxcar2 clients to make sure it worked"
        else:
            return "Error sending Boxcar2 notification"


    def testPushover(self, userKey=None, apiKey=None):
        # self.set_header('Cache-Control', 'max-age=0,no-cache,no-store')

        result = notifiers.pushover_notifier.test_notify(userKey, apiKey)
        if result:
            return "Pushover notification succeeded. Check your Pushover clients to make sure it worked"
        else:
            return "Error sending Pushover notification"


    def twitterStep1(self):
        # self.set_header('Cache-Control', 'max-age=0,no-cache,no-store')

        return notifiers.twitter_notifier._get_authorization()


    def twitterStep2(self, key):
        # self.set_header('Cache-Control', 'max-age=0,no-cache,no-store')

        result = notifiers.twitter_notifier._get_credentials(key)
        logger.log(u"result: " + str(result))
        if result:
            return "Key verification successful"
        else:
            return "Unable to verify key"


    def testTwitter(self):
        # self.set_header('Cache-Control', 'max-age=0,no-cache,no-store')

        result = notifiers.twitter_notifier.test_notify()
        if result:
            return "Tweet successful, check your twitter to make sure it worked"
        else:
            return "Error sending tweet"


    def testKODI(self, host=None, username=None, password=None):
        # self.set_header('Cache-Control', 'max-age=0,no-cache,no-store')

        host = config.clean_hosts(host)
        finalResult = ''
        for curHost in [x.strip() for x in host.split(",")]:
            curResult = notifiers.kodi_notifier.test_notify(urllib.unquote_plus(curHost), username, password)
            if len(curResult.split(":")) > 2 and 'OK' in curResult.split(":")[2]:
                finalResult += "Test KODI notice sent successfully to " + urllib.unquote_plus(curHost)
            else:
                finalResult += "Test KODI notice failed to " + urllib.unquote_plus(curHost)
            finalResult += "<br />\n"

        return finalResult


    def testPMC(self, host=None, username=None, password=None):
        self.set_header('Cache-Control', 'max-age=0,no-cache,no-store')

        if None is not password and set('*') == set(password):
            password = sickbeard.PLEX_CLIENT_PASSWORD

        finalResult = ''
        for curHost in [x.strip() for x in host.split(',')]:
            curResult = notifiers.plex_notifier.test_notify_pmc(urllib.unquote_plus(curHost), username, password)
            if len(curResult.split(':')) > 2 and 'OK' in curResult.split(':')[2]:
                finalResult += 'Successful test notice sent to Plex client ... ' + urllib.unquote_plus(curHost)
            else:
                finalResult += 'Test failed for Plex client ... ' + urllib.unquote_plus(curHost)
            finalResult += '<br />' + '\n'

        ui.notifications.message('Tested Plex client(s): ', urllib.unquote_plus(host.replace(',', ', ')))

        return finalResult

    def testPMS(self, host=None, username=None, password=None, plex_server_token=None):
        self.set_header('Cache-Control', 'max-age=0,no-cache,no-store')

        if None is not password and set('*') == set(password):
            password = sickbeard.PLEX_PASSWORD

        finalResult = ''

        curResult = notifiers.plex_notifier.test_notify_pms(urllib.unquote_plus(host), username, password, plex_server_token)
        if None is curResult:
            finalResult += 'Successful test of Plex server(s) ... ' + urllib.unquote_plus(host.replace(',', ', '))
        else:
            finalResult += 'Test failed for Plex server(s) ... ' + urllib.unquote_plus(curResult.replace(',', ', '))
        finalResult += '<br />' + '\n'

        ui.notifications.message('Tested Plex Media Server host(s): ', urllib.unquote_plus(host.replace(',', ', ')))

        return finalResult

    def testLibnotify(self):
        # self.set_header('Cache-Control', 'max-age=0,no-cache,no-store')

        if notifiers.libnotify_notifier.test_notify():
            return "Tried sending desktop notification via libnotify"
        else:
            return notifiers.libnotify.diagnose()


    def testEMBY(self, host=None, emby_apikey=None):
        # self.set_header('Cache-Control', 'max-age=0,no-cache,no-store')

        host = config.clean_host(host)
        result = notifiers.emby_notifier.test_notify(urllib.unquote_plus(host), emby_apikey)
        if result:
            return "Test notice sent successfully to " + urllib.unquote_plus(host)
        else:
            return "Test notice failed to " + urllib.unquote_plus(host)


    def testNMJ(self, host=None, database=None, mount=None):
        # self.set_header('Cache-Control', 'max-age=0,no-cache,no-store')

        host = config.clean_host(host)
        result = notifiers.nmj_notifier.test_notify(urllib.unquote_plus(host), database, mount)
        if result:
            return "Successfully started the scan update"
        else:
            return "Test failed to start the scan update"


    def settingsNMJ(self, host=None):
        # self.set_header('Cache-Control', 'max-age=0,no-cache,no-store')

        host = config.clean_host(host)
        result = notifiers.nmj_notifier.notify_settings(urllib.unquote_plus(host))
        if result:
            return '{"message": "Got settings from %(host)s", "database": "%(database)s", "mount": "%(mount)s"}' % {
                "host": host, "database": sickbeard.NMJ_DATABASE, "mount": sickbeard.NMJ_MOUNT}
        else:
            return '{"message": "Failed! Make sure your Popcorn is on and NMJ is running. (see Log & Errors -> Debug for detailed info)", "database": "", "mount": ""}'


    def testNMJv2(self, host=None):
        # self.set_header('Cache-Control', 'max-age=0,no-cache,no-store')

        host = config.clean_host(host)
        result = notifiers.nmjv2_notifier.test_notify(urllib.unquote_plus(host))
        if result:
            return "Test notice sent successfully to " + urllib.unquote_plus(host)
        else:
            return "Test notice failed to " + urllib.unquote_plus(host)


    def settingsNMJv2(self, host=None, dbloc=None, instance=None):
        # self.set_header('Cache-Control', 'max-age=0,no-cache,no-store')

        host = config.clean_host(host)
        result = notifiers.nmjv2_notifier.notify_settings(urllib.unquote_plus(host), dbloc, instance)
        if result:
            return '{"message": "NMJ Database found at: %(host)s", "database": "%(database)s"}' % {"host": host,
                                                                                                   "database": sickbeard.NMJv2_DATABASE}
        else:
            return '{"message": "Unable to find NMJ Database at location: %(dbloc)s. Is the right location selected and PCH running?", "database": ""}' % {
                "dbloc": dbloc}

    def getTraktToken(self, trakt_pin=None):

        trakt_api = TraktAPI(sickbeard.SSL_VERIFY, sickbeard.TRAKT_TIMEOUT)
        response = trakt_api.traktToken(trakt_pin)
        if response:
            return "Trakt Authorized"
        return "Trakt Not Authorized!"

    def testTrakt(self, username=None, blacklist_name=None):
        return notifiers.trakt_notifier.test_notify(username, blacklist_name)


    def loadShowNotifyLists(self):
        # self.set_header('Cache-Control', 'max-age=0,no-cache,no-store')

        myDB = db.DBConnection()
        rows = myDB.select("SELECT show_id, show_name, notify_list FROM tv_shows ORDER BY show_name ASC")

        data = {}
        size = 0
        for r in rows:
            data[r['show_id']] = {'id': r['show_id'], 'name': r['show_name'], 'list': r['notify_list']}
            size += 1
        data['_size'] = size
        return json.dumps(data)


    def saveShowNotifyList(self, show=None, emails=None):
        # self.set_header('Cache-Control', 'max-age=0,no-cache,no-store')

        myDB = db.DBConnection()
        if myDB.action("UPDATE tv_shows SET notify_list = ? WHERE show_id = ?", [emails, show]):
            return 'OK'
        else:
            return 'ERROR'


    def testEmail(self, host=None, port=None, smtp_from=None, use_tls=None, user=None, pwd=None, to=None):
        # self.set_header('Cache-Control', 'max-age=0,no-cache,no-store')

        host = config.clean_host(host)
        if notifiers.email_notifier.test_notify(host, port, smtp_from, use_tls, user, pwd, to):
            return 'Test email sent successfully! Check inbox.'
        else:
            return 'ERROR: %s' % notifiers.email_notifier.last_err


    def testNMA(self, nma_api=None, nma_priority=0):
        # self.set_header('Cache-Control', 'max-age=0,no-cache,no-store')

        result = notifiers.nma_notifier.test_notify(nma_api, nma_priority)
        if result:
            return "Test NMA notice sent successfully"
        else:
            return "Test NMA notice failed"


    def testPushalot(self, authorizationToken=None):
        # self.set_header('Cache-Control', 'max-age=0,no-cache,no-store')

        result = notifiers.pushalot_notifier.test_notify(authorizationToken)
        if result:
            return "Pushalot notification succeeded. Check your Pushalot clients to make sure it worked"
        else:
            return "Error sending Pushalot notification"


    def testPushbullet(self, api=None):
        # self.set_header('Cache-Control', 'max-age=0,no-cache,no-store')

        result = notifiers.pushbullet_notifier.test_notify(api)
        if result:
            return "Pushbullet notification succeeded. Check your device to make sure it worked"
        else:
            return "Error sending Pushbullet notification"


    def getPushbulletDevices(self, api=None):
        # self.set_header('Cache-Control', 'max-age=0,no-cache,no-store')

        result = notifiers.pushbullet_notifier.get_devices(api)
        if result:
            return result
        else:
            return "Error sending Pushbullet notification"

    def status(self):
        tvdirFree = helpers.getDiskSpaceUsage(sickbeard.TV_DOWNLOAD_DIR)
        rootDir = {}
        if sickbeard.ROOT_DIRS:
            backend_pieces = sickbeard.ROOT_DIRS.split('|')
            backend_dirs = backend_pieces[1:]
        else:
            backend_dirs = []

        if len(backend_dirs):
            for subject in backend_dirs:
                rootDir[subject] = helpers.getDiskSpaceUsage(subject)

        t = PageTemplate(rh=self, file="status.mako")
        return t.render(title='Status', header='Status', topmenu='system', tvdirFree=tvdirFree, rootDir=rootDir)

    def shutdown(self, pid=None):
        if not Shutdown.stop(pid):
            return self.redirect('/' + sickbeard.DEFAULT_PAGE + '/')

        title = "Shutting down"
        message = "SickRage is shutting down..."

        return self._genericMessage(title, message)

    def restart(self, pid=None):
        if not Restart.restart(pid):
            return self.redirect('/' + sickbeard.DEFAULT_PAGE + '/')

        t = PageTemplate(rh=self, file="restart.mako")

        return t.render(title="Home", header="Restarting SickRage", topmenu="system")

    def updateCheck(self, pid=None):
        if str(pid) != str(sickbeard.PID):
            return self.redirect('/home/')

        sickbeard.versionCheckScheduler.action.check_for_new_version(force=True)
        sickbeard.versionCheckScheduler.action.check_for_new_news(force=True)

        return self.redirect('/' + sickbeard.DEFAULT_PAGE + '/')

    def update(self, pid=None):

        if str(pid) != str(sickbeard.PID):
            return self.redirect('/home/')

        checkversion = CheckVersion()
        backup = checkversion._runbackup()

        if backup == True:

            if sickbeard.versionCheckScheduler.action.update():
                # do a hard restart
                sickbeard.events.put(sickbeard.events.SystemEvent.RESTART)

                t = PageTemplate(rh=self, file="restart.mako")
                return t.render(title="Home", header="Restarting SickRage", topmenu="home")
            else:
                return self._genericMessage("Update Failed",
                                            "Update wasn't successful, not restarting. Check your log for more information.")
        else:
            return self.redirect('/' + sickbeard.DEFAULT_PAGE +'/')

    def branchCheckout(self, branch):
        if sickbeard.BRANCH != branch:
            sickbeard.BRANCH = branch
            ui.notifications.message('Checking out branch: ', branch)
            return self.update(sickbeard.PID)
        else:
            ui.notifications.message('Already on branch: ', branch)
            return self.redirect('/' + sickbeard.DEFAULT_PAGE +'/')

    def getDBcompare(self):

        checkversion = CheckVersion()
        db_status = checkversion.getDBcompare()

        if db_status == 'upgrade':
            logger.log(u"Checkout branch has a new DB version - Upgrade", logger.DEBUG)
            return json.dumps({ "status": "success", 'message': 'upgrade' })
        elif db_status == 'equal':
            logger.log(u"Checkout branch has the same DB version - Equal", logger.DEBUG)
            return json.dumps({ "status": "success", 'message': 'equal' })
        elif db_status == 'downgrade':
            logger.log(u"Checkout branch has an old DB version - Downgrade", logger.DEBUG)
            return json.dumps({ "status": "success", 'message': 'downgrade' })
        else:
            logger.log(u"Checkout branch couldn't compare DB version.", logger.ERROR)
            return json.dumps({ "status": "error", 'message': 'General exception' })

    def displayShow(self, show=None):

        if show is None:
            return self._genericMessage("Error", "Invalid show ID")
        else:
            showObj = sickbeard.helpers.findCertainShow(sickbeard.showList, int(show))

            if showObj is None:
                return self._genericMessage("Error", "Show not in show list")

        myDB = db.DBConnection()
        seasonResults = myDB.select(
            "SELECT DISTINCT season FROM tv_episodes WHERE showid = ? ORDER BY season DESC",
            [showObj.indexerid]
        )

        sqlResults = myDB.select(
            "SELECT * FROM tv_episodes WHERE showid = ? ORDER BY season DESC, episode DESC",
            [showObj.indexerid]
        )

        t = PageTemplate(rh=self, file="displayShow.mako")
        submenu = [{'title': 'Edit', 'path': 'home/editShow?show=%d' % showObj.indexerid, 'icon': 'ui-icon ui-icon-pencil'}]

        try:
            showLoc = (showObj.location, True)
        except ShowDirectoryNotFoundException:
            showLoc = (showObj._location, False)

        show_message = ''

        if sickbeard.showQueueScheduler.action.isBeingAdded(showObj):
            show_message = 'This show is in the process of being downloaded - the info below is incomplete.'

        elif sickbeard.showQueueScheduler.action.isBeingUpdated(showObj):
            show_message = 'The information on this page is in the process of being updated.'

        elif sickbeard.showQueueScheduler.action.isBeingRefreshed(showObj):
            show_message = 'The episodes below are currently being refreshed from disk'

        elif sickbeard.showQueueScheduler.action.isBeingSubtitled(showObj):
            show_message = 'Currently downloading subtitles for this show'

        elif sickbeard.showQueueScheduler.action.isInRefreshQueue(showObj):
            show_message = 'This show is queued to be refreshed.'

        elif sickbeard.showQueueScheduler.action.isInUpdateQueue(showObj):
            show_message = 'This show is queued and awaiting an update.'

        elif sickbeard.showQueueScheduler.action.isInSubtitleQueue(showObj):
            show_message = 'This show is queued and awaiting subtitles download.'

        if not sickbeard.showQueueScheduler.action.isBeingAdded(showObj):
            if not sickbeard.showQueueScheduler.action.isBeingUpdated(showObj):
                if showObj.paused:
                    submenu.append({'title': 'Resume', 'path': 'home/togglePause?show=%d' % showObj.indexerid, 'icon': 'ui-icon ui-icon-play'})
                else:
                    submenu.append({'title': 'Pause', 'path': 'home/togglePause?show=%d' % showObj.indexerid, 'icon': 'ui-icon ui-icon-pause'})

                submenu.append({'title': 'Remove', 'path': 'home/deleteShow?show=%d' % showObj.indexerid, 'class':'removeshow', 'confirm': True, 'icon': 'ui-icon ui-icon-trash'})
                submenu.append({'title': 'Re-scan files', 'path': 'home/refreshShow?show=%d' % showObj.indexerid, 'icon': 'ui-icon ui-icon-refresh'})
                submenu.append({'title': 'Force Full Update', 'path': 'home/updateShow?show=%d&amp;force=1' % showObj.indexerid, 'icon': 'ui-icon ui-icon-transfer-e-w'})
                submenu.append({'title': 'Update show in KODI','path': 'home/updateKODI?show=%d' % showObj.indexerid, 'requires': self.haveKODI(), 'icon': 'submenu-icon-kodi'})
                submenu.append({'title': 'Update show in Emby', 'path': 'home/updateEMBY?show=%d' % showObj.indexerid, 'requires': self.haveEMBY(), 'icon': 'ui-icon ui-icon-refresh'})
                submenu.append({'title': 'Preview Rename', 'path': 'home/testRename?show=%d' % showObj.indexerid, 'icon': 'ui-icon ui-icon-tag'})

                if sickbeard.USE_SUBTITLES and not sickbeard.showQueueScheduler.action.isBeingSubtitled(
                        showObj) and showObj.subtitles:
                    submenu.append({'title': 'Download Subtitles', 'path': 'home/subtitleShow?show=%d' % showObj.indexerid, 'icon': 'ui-icon ui-icon-comment'})

        epCounts = {}
        epCats = {}
        epCounts[Overview.SKIPPED] = 0
        epCounts[Overview.WANTED] = 0
        epCounts[Overview.QUAL] = 0
        epCounts[Overview.GOOD] = 0
        epCounts[Overview.UNAIRED] = 0
        epCounts[Overview.SNATCHED] = 0

        for curResult in sqlResults:
            curEpCat = showObj.getOverview(int(curResult["status"] or -1))
            if curEpCat:
                epCats[str(curResult["season"]) + "x" + str(curResult["episode"])] = curEpCat
                epCounts[curEpCat] += 1

        def titler(x):
            return (helpers.remove_article(x), x)[not x or sickbeard.SORT_ARTICLE]

        if sickbeard.ANIME_SPLIT_HOME:
            shows = []
            anime = []
            for show in sickbeard.showList:
                if show.is_anime:
                    anime.append(show)
                else:
                    shows.append(show)
            sortedShowLists = [["Shows", sorted(shows, lambda x, y: cmp(titler(x.name), titler(y.name)))],
                                 ["Anime", sorted(anime, lambda x, y: cmp(titler(x.name), titler(y.name)))]]
        else:
            sortedShowLists = [
                ["Shows", sorted(sickbeard.showList, lambda x, y: cmp(titler(x.name), titler(y.name)))]]

        bwl = None
        if showObj.is_anime:
            bwl = showObj.release_groups

        showObj.exceptions = sickbeard.scene_exceptions.get_scene_exceptions(showObj.indexerid)

        indexerid = int(showObj.indexerid)
        indexer = int(showObj.indexer)

        # Delete any previous occurrances
        for index, recentShow in enumerate(sickbeard.SHOWS_RECENT):
            if recentShow['indexerid'] == indexerid:
                del sickbeard.SHOWS_RECENT[index]

        # Only track 5 most recent shows
        del sickbeard.SHOWS_RECENT[4:]

        # Insert most recent show
        sickbeard.SHOWS_RECENT.insert(0, {
            'indexerid': indexerid,
            'name': showObj.name,
        })

        return t.render(submenu=submenu, showLoc=showLoc, show_message=show_message,
                show=showObj, sqlResults=sqlResults, seasonResults=seasonResults,
                sortedShowLists=sortedShowLists, bwl=bwl, epCounts=epCounts,
                epCats=epCats, all_scene_exceptions=showObj.exceptions,
                scene_numbering=get_scene_numbering_for_show(indexerid, indexer),
                xem_numbering=get_xem_numbering_for_show(indexerid, indexer),
                scene_absolute_numbering=get_scene_absolute_numbering_for_show(indexerid, indexer),
                xem_absolute_numbering=get_xem_absolute_numbering_for_show(indexerid, indexer),
                title=showObj.name
        )


    def plotDetails(self, show, season, episode):
        myDB = db.DBConnection()
        result = myDB.selectOne(
            "SELECT description FROM tv_episodes WHERE showid = ? AND season = ? AND episode = ?",
            (int(show), int(season), int(episode)))
        return result['description'] if result else 'Episode not found.'


    def sceneExceptions(self, show):
        exceptionsList = sickbeard.scene_exceptions.get_all_scene_exceptions(show)
        if not exceptionsList:
            return "No scene exceptions"

        out = []
        for season, names in iter(sorted(exceptionsList.iteritems())):
            if season == -1:
                season = "*"
            out.append("S" + str(season) + ": " + ", ".join(names))
        return "<br/>".join(out)


    def editShow(self, show=None, location=None, anyQualities=[], bestQualities=[], exceptions_list=[],
                 flatten_folders=None, paused=None, directCall=False, air_by_date=None, sports=None, dvdorder=None,
                 indexerLang=None, subtitles=None, archive_firstmatch=None, rls_ignore_words=None,
                 rls_require_words=None, anime=None, blacklist=None, whitelist=None,
                 scene=None, defaultEpStatus=None):

        anidb_failed = False
        if show is None:
            errString = "Invalid show ID: " + str(show)
            if directCall:
                return [errString]
            else:
                return self._genericMessage("Error", errString)

        showObj = sickbeard.helpers.findCertainShow(sickbeard.showList, int(show))

        if not showObj:
            errString = "Unable to find the specified show: " + str(show)
            if directCall:
                return [errString]
            else:
                return self._genericMessage("Error", errString)

        showObj.exceptions = sickbeard.scene_exceptions.get_scene_exceptions(showObj.indexerid)

        if not location and not anyQualities and not bestQualities and not flatten_folders:
            t = PageTemplate(rh=self, file="editShow.mako")

            if showObj.is_anime:
                whitelist = showObj.release_groups.whitelist
                blacklist = showObj.release_groups.blacklist

                groups = []
                if helpers.set_up_anidb_connection() and not anidb_failed:
                    try:
                        anime = adba.Anime(sickbeard.ADBA_CONNECTION, name=showObj.name)
                        groups = anime.get_groups()
                    except Exception as e:
                        anidb_failed = True
                        ui.notifications.error('Unable to retreive Fansub Groups from AniDB.')
                        logger.log('Unable to retreive Fansub Groups from AniDB. Error is {0}'.format(str(e)),logger.DEBUG)

            with showObj.lock:
                show = showObj
                scene_exceptions = sickbeard.scene_exceptions.get_scene_exceptions(showObj.indexerid)

            if showObj.is_anime:
                return t.render(show=show, scene_exceptions=scene_exceptions, groups=groups, whitelist=whitelist,
                                blacklist=blacklist, title='Edit Shows', header='Edit Shows')
            else:
                return t.render(show=show, scene_exceptions=scene_exceptions, title='Edit Shows', header='Edit Shows')

        flatten_folders = config.checkbox_to_value(flatten_folders)
        dvdorder = config.checkbox_to_value(dvdorder)
        archive_firstmatch = config.checkbox_to_value(archive_firstmatch)
        paused = config.checkbox_to_value(paused)
        air_by_date = config.checkbox_to_value(air_by_date)
        scene = config.checkbox_to_value(scene)
        sports = config.checkbox_to_value(sports)
        anime = config.checkbox_to_value(anime)
        subtitles = config.checkbox_to_value(subtitles)

        if indexerLang and indexerLang in sickbeard.indexerApi(showObj.indexer).indexer().config['valid_languages']:
            indexer_lang = indexerLang
        else:
            indexer_lang = showObj.lang

        # if we changed the language then kick off an update
        if indexer_lang == showObj.lang:
            do_update = False
        else:
            do_update = True

        if scene == showObj.scene and anime == showObj.anime:
            do_update_scene_numbering = False
        else:
            do_update_scene_numbering = True

        if type(anyQualities) != list:
            anyQualities = [anyQualities]

        if type(bestQualities) != list:
            bestQualities = [bestQualities]

        if type(exceptions_list) != list:
            exceptions_list = [exceptions_list]

        # If directCall from mass_edit_update no scene exceptions handling or blackandwhite list handling
        if directCall:
            do_update_exceptions = False
        else:
            if set(exceptions_list) == set(showObj.exceptions):
                do_update_exceptions = False
            else:
                do_update_exceptions = True

            with showObj.lock:
                if anime:
                    if not showObj.release_groups:
                        showObj.release_groups = BlackAndWhiteList(showObj.indexerid)

                    if whitelist:
                        shortwhitelist = short_group_names(whitelist)
                        showObj.release_groups.set_white_keywords(shortwhitelist)
                    else:
                        showObj.release_groups.set_white_keywords([])

                    if blacklist:
                        shortblacklist = short_group_names(blacklist)
                        showObj.release_groups.set_black_keywords(shortblacklist)
                    else:
                        showObj.release_groups.set_black_keywords([])

        errors = []
        with showObj.lock:
            newQuality = Quality.combineQualities(map(int, anyQualities), map(int, bestQualities))
            showObj.quality = newQuality
            showObj.archive_firstmatch = archive_firstmatch

            # reversed for now
            if bool(showObj.flatten_folders) != bool(flatten_folders):
                showObj.flatten_folders = flatten_folders
                try:
                    sickbeard.showQueueScheduler.action.refreshShow(showObj)
                except CantRefreshShowException, e:
                    errors.append("Unable to refresh this show: " + ex(e))

            showObj.paused = paused
            showObj.scene = scene
            showObj.anime = anime
            showObj.sports = sports
            showObj.subtitles = subtitles
            showObj.air_by_date = air_by_date
            showObj.default_ep_status = int(defaultEpStatus)

            if not directCall:
                showObj.lang = indexer_lang
                showObj.dvdorder = dvdorder
                showObj.rls_ignore_words = rls_ignore_words.strip()
                showObj.rls_require_words = rls_require_words.strip()

            # if we change location clear the db of episodes, change it, write to db, and rescan
            if os.path.normpath(showObj._location) != os.path.normpath(location):
                logger.log(os.path.normpath(showObj._location) + " != " + os.path.normpath(location), logger.DEBUG)
                if not ek(os.path.isdir, location) and not sickbeard.CREATE_MISSING_SHOW_DIRS:
                    errors.append("New location <tt>%s</tt> does not exist" % location)

                # don't bother if we're going to update anyway
                elif not do_update:
                    # change it
                    try:
                        showObj.location = location
                        try:
                            sickbeard.showQueueScheduler.action.refreshShow(showObj)
                        except CantRefreshShowException, e:
                            errors.append("Unable to refresh this show:" + ex(e))
                            # grab updated info from TVDB
                            # showObj.loadEpisodesFromIndexer()
                            # rescan the episodes in the new folder
                    except NoNFOException:
                        errors.append(
                            "The folder at <tt>%s</tt> doesn't contain a tvshow.nfo - copy your files to that folder before you change the directory in SickRage." % location)

            # save it to the DB
            showObj.saveToDB()

        # force the update
        if do_update:
            try:
                sickbeard.showQueueScheduler.action.updateShow(showObj, True)
                time.sleep(cpu_presets[sickbeard.CPU_PRESET])
            except CantUpdateShowException as e:
                errors.append("Unable to update show: {0}".format(str(e)))

        if do_update_exceptions:
            try:
                sickbeard.scene_exceptions.update_scene_exceptions(showObj.indexerid, exceptions_list)  # @UndefinedVdexerid)
                time.sleep(cpu_presets[sickbeard.CPU_PRESET])
            except CantUpdateShowException, e:
                errors.append("Unable to force an update on scene exceptions of the show.")

        if do_update_scene_numbering:
            try:
                sickbeard.scene_numbering.xem_refresh(showObj.indexerid, showObj.indexer)
                time.sleep(cpu_presets[sickbeard.CPU_PRESET])
            except CantUpdateShowException, e:
                errors.append("Unable to force an update on scene numbering of the show.")

        if directCall:
            return errors

        if len(errors) > 0:
            ui.notifications.error('%d error%s while saving changes:' % (len(errors), "" if len(errors) == 1 else "s"),
                                   '<ul>' + '\n'.join(['<li>%s</li>' % error for error in errors]) + "</ul>")

        return self.redirect("/home/displayShow?show=" + show)

    def togglePause(self, show=None):
        error, show = Show.pause(show)

        if error is not None:
            return self._genericMessage('Error', error)

        ui.notifications.message('%s has been %s' % (show.name, ('resumed', 'paused')[show.paused]))

        return self.redirect("/home/displayShow?show=%i" % show.indexerid)

    def deleteShow(self, show=None, full=0):
        error, show = Show.delete(show, full)

        if error is not None:
            return self._genericMessage('Error', error)

        ui.notifications.message(
            '%s has been %s %s' %
            (
                show.name,
                ('deleted', 'trashed')[bool(sickbeard.TRASH_REMOVE_SHOW)],
                ('(media untouched)', '(with all related media)')[bool(full)]
            )
        )

        time.sleep(cpu_presets[sickbeard.CPU_PRESET])

        # Don't redirect to the default page, so the user can confirm that the show was deleted
        return self.redirect('/home/')

    def refreshShow(self, show=None):
        error, show = Show.refresh(show)

        # This is a show validation error
        if error is not None and show is None:
            return self._genericMessage('Error', error)

        # This is a refresh error
        if error is not None:
            ui.notifications.error('Unable to refresh this show.', ex(error))

        time.sleep(cpu_presets[sickbeard.CPU_PRESET])

        return self.redirect("/home/displayShow?show=" + str(show.indexerid))

    def updateShow(self, show=None, force=0):

        if show is None:
            return self._genericMessage("Error", "Invalid show ID")

        showObj = sickbeard.helpers.findCertainShow(sickbeard.showList, int(show))

        if showObj is None:
            return self._genericMessage("Error", "Unable to find the specified show")

        # force the update
        try:
            sickbeard.showQueueScheduler.action.updateShow(showObj, bool(force))
        except CantUpdateShowException, e:
            ui.notifications.error("Unable to update this show.", ex(e))

        # just give it some time
        time.sleep(cpu_presets[sickbeard.CPU_PRESET])

        return self.redirect("/home/displayShow?show=" + str(showObj.indexerid))

    def subtitleShow(self, show=None, force=0):

        if show is None:
            return self._genericMessage("Error", "Invalid show ID")

        showObj = sickbeard.helpers.findCertainShow(sickbeard.showList, int(show))

        if showObj is None:
            return self._genericMessage("Error", "Unable to find the specified show")

        # search and download subtitles
        sickbeard.showQueueScheduler.action.downloadSubtitles(showObj, bool(force))

        time.sleep(cpu_presets[sickbeard.CPU_PRESET])

        return self.redirect("/home/displayShow?show=" + str(showObj.indexerid))


    def updateKODI(self, show=None):
        showName=None
        showObj=None

        if show:
            showObj = sickbeard.helpers.findCertainShow(sickbeard.showList, int(show))
            if showObj:
                showName=urllib.quote_plus(showObj.name.encode('utf-8'))

        # only send update to first host in the list -- workaround for kodi sql backend users
        if sickbeard.KODI_UPDATE_ONLYFIRST:
            # only send update to first host in the list -- workaround for kodi sql backend users
            host = sickbeard.KODI_HOST.split(",")[0].strip()
        else:
            host = sickbeard.KODI_HOST

        if notifiers.kodi_notifier.update_library(showName=showName):
            ui.notifications.message("Library update command sent to KODI host(s): " + host)
        else:
            ui.notifications.error("Unable to contact one or more KODI host(s): " + host)

        if showObj:
            return self.redirect('/home/displayShow?show=' + str(showObj.indexerid))
        else:
            return self.redirect('/home/')

    def updatePLEX(self):
        if None is notifiers.plex_notifier.update_library():
            ui.notifications.message(
                "Library update command sent to Plex Media Server host: " + sickbeard.PLEX_SERVER_HOST)
        else:
            ui.notifications.error("Unable to contact Plex Media Server host: " + sickbeard.PLEX_SERVER_HOST)
        return self.redirect('/home/')

    def updateEMBY(self, show=None):
        showName=None
        showObj=None

        if show:
            showObj = sickbeard.helpers.findCertainShow(sickbeard.showList, int(show))

        if notifiers.emby_notifier.update_library(showObj):
            ui.notifications.message(
                "Library update command sent to Emby host: " + sickbeard.EMBY_HOST)
        else:
            ui.notifications.error("Unable to contact Emby host: " + sickbeard.EMBY_HOST)

        if showObj:
            return self.redirect('/home/displayShow?show=' + str(showObj.indexerid))
        else:
            return self.redirect('/home/')

    def setStatus(self, show=None, eps=None, status=None, direct=False):

        if not all([show, eps, status]):
            errMsg = "You must specify a show and at least one episode"
            if direct:
                ui.notifications.error('Error', errMsg)
                return json.dumps({'result': 'error'})
            else:
                return self._genericMessage("Error", errMsg)

        if not statusStrings.has_key(int(status)):
            errMsg = "Invalid status"
            if direct:
                ui.notifications.error('Error', errMsg)
                return json.dumps({'result': 'error'})
            else:
                return self._genericMessage("Error", errMsg)

        showObj = sickbeard.helpers.findCertainShow(sickbeard.showList, int(show))

        if not showObj:
            errMsg = "Error", "Show not in show list"
            if direct:
                ui.notifications.error('Error', errMsg)
                return json.dumps({'result': 'error'})
            else:
                return self._genericMessage("Error", errMsg)

        segments = {}
        trakt_data = []
        if eps:

            sql_l = []
            for curEp in eps.split('|'):

                if not curEp:
                    logger.log(u"curEp was empty when trying to setStatus", logger.DEBUG)

                logger.log(u"Attempting to set status on episode " + curEp + " to " + status, logger.DEBUG)

                epInfo = curEp.split('x')

                if not all(epInfo):
                    logger.log(u"Something went wrong when trying to setStatus, epInfo[0]: %s, epInfo[1]: %s" % (epInfo[0], epInfo[1]), logger.DEBUG)
                    continue

                epObj = showObj.getEpisode(int(epInfo[0]), int(epInfo[1]))

                if not epObj:
                    return self._genericMessage("Error", "Episode couldn't be retrieved")

                if int(status) in [WANTED, FAILED]:
                    # figure out what episodes are wanted so we can backlog them
                    if epObj.season in segments:
                        segments[epObj.season].append(epObj)
                    else:
                        segments[epObj.season] = [epObj]

                with epObj.lock:
                    # don't let them mess up UNAIRED episodes
                    if epObj.status == UNAIRED:
                        logger.log(u"Refusing to change status of " + curEp + " because it is UNAIRED", logger.ERROR)
                        continue

                    if int(status) in Quality.DOWNLOADED and epObj.status not in Quality.SNATCHED + Quality.SNATCHED_PROPER + Quality.DOWNLOADED + [
                        IGNORED] and not ek(os.path.isfile, epObj.location):
                        logger.log(
                            u"Refusing to change status of " + curEp + " to DOWNLOADED because it's not SNATCHED/DOWNLOADED",
                            logger.ERROR)
                        continue

                    if int(status) == FAILED and epObj.status not in Quality.SNATCHED + Quality.SNATCHED_PROPER + Quality.DOWNLOADED + Quality.ARCHIVED:
                        logger.log(
                            u"Refusing to change status of " + curEp + " to FAILED because it's not SNATCHED/DOWNLOADED",
                            logger.ERROR)
                        continue

                    if epObj.status in Quality.DOWNLOADED + Quality.ARCHIVED and int(status) == WANTED:
                        logger.log(u"Removing release_name for episode as you want to set a downloaded episode back to wanted, so obviously you want it replaced")
                        epObj.release_name = ""

                    epObj.status = int(status)

                    # mass add to database
                    sql_l.append(epObj.get_sql())

                    trakt_data.append((epObj.season, epObj.episode))

            data = notifiers.trakt_notifier.trakt_episode_data_generate(trakt_data)

            if sickbeard.USE_TRAKT and sickbeard.TRAKT_SYNC_WATCHLIST:
                if int(status) in [WANTED, FAILED]:
                    logger.log(u"Add episodes, showid: indexerid " + str(showObj.indexerid) + ", Title " + str(showObj.name) + " to Watchlist", logger.DEBUG)
                    upd = "add"
                elif int(status) in [IGNORED, SKIPPED] + Quality.DOWNLOADED + Quality.ARCHIVED:
                    logger.log(u"Remove episodes, showid: indexerid " + str(showObj.indexerid) + ", Title " + str(showObj.name) + " from Watchlist", logger.DEBUG)
                    upd = "remove"

                if data:
                    notifiers.trakt_notifier.update_watchlist(showObj, data_episode=data, update=upd)

            if len(sql_l) > 0:
                myDB = db.DBConnection()
                myDB.mass_action(sql_l)

        if int(status) == WANTED and not showObj.paused:
            msg = "Backlog was automatically started for the following seasons of <b>" + showObj.name + "</b>:<br />"
            msg += '<ul>'

            for season, segment in segments.iteritems():
                cur_backlog_queue_item = search_queue.BacklogQueueItem(showObj, segment)
                sickbeard.searchQueueScheduler.action.add_item(cur_backlog_queue_item)

                msg += "<li>Season " + str(season) + "</li>"
                logger.log(u"Sending backlog for " + showObj.name + " season " + str(
                    season) + " because some eps were set to wanted")

            msg += "</ul>"

            if segments:
                ui.notifications.message("Backlog started", msg)
        elif int(status) == WANTED and showObj.paused:
            logger.log(u"Some episodes were set to wanted, but " + showObj.name + " is paused. Not adding to Backlog until show is unpaused")

        if int(status) == FAILED:
            msg = "Retrying Search was automatically started for the following season of <b>" + showObj.name + "</b>:<br />"
            msg += '<ul>'

            for season, segment in segments.iteritems():
                cur_failed_queue_item = search_queue.FailedQueueItem(showObj, segment)
                sickbeard.searchQueueScheduler.action.add_item(cur_failed_queue_item)

                msg += "<li>Season " + str(season) + "</li>"
                logger.log(u"Retrying Search for " + showObj.name + " season " + str(
                    season) + " because some eps were set to failed")

            msg += "</ul>"

            if segments:
                ui.notifications.message("Retry Search started", msg)

        if direct:
            return json.dumps({'result': 'success'})
        else:
            return self.redirect("/home/displayShow?show=" + show)


    def testRename(self, show=None):

        if show is None:
            return self._genericMessage("Error", "You must specify a show")

        showObj = sickbeard.helpers.findCertainShow(sickbeard.showList, int(show))

        if showObj is None:
            return self._genericMessage("Error", "Show not in show list")

        try:
            show_loc = showObj.location  # @UnusedVariable
        except ShowDirectoryNotFoundException:
            return self._genericMessage("Error", "Can't rename episodes when the show dir is missing.")

        ep_obj_rename_list = []

        ep_obj_list = showObj.getAllEpisodes(has_location=True)

        for cur_ep_obj in ep_obj_list:
            # Only want to rename if we have a location
            if cur_ep_obj.location:
                if cur_ep_obj.relatedEps:
                    # do we have one of multi-episodes in the rename list already
                    have_already = False
                    for cur_related_ep in cur_ep_obj.relatedEps + [cur_ep_obj]:
                        if cur_related_ep in ep_obj_rename_list:
                            have_already = True
                            break
                        if not have_already:
                            ep_obj_rename_list.append(cur_ep_obj)
                else:
                    ep_obj_rename_list.append(cur_ep_obj)

        if ep_obj_rename_list:
            # present season DESC episode DESC on screen
            ep_obj_rename_list.reverse()

        t = PageTemplate(rh=self, file="testRename.mako")
        submenu = [{'title': 'Edit', 'path': 'home/editShow?show=%d' % showObj.indexerid, 'icon': 'ui-icon ui-icon-pencil'}]

        return t.render(submenu=submenu, ep_obj_list=ep_obj_rename_list, show=showObj, title='Preview Rename', header='Preview Rename')


    def doRename(self, show=None, eps=None):

        if show is None or eps is None:
            errMsg = "You must specify a show and at least one episode"
            return self._genericMessage("Error", errMsg)

        show_obj = sickbeard.helpers.findCertainShow(sickbeard.showList, int(show))

        if show_obj is None:
            errMsg = "Error", "Show not in show list"
            return self._genericMessage("Error", errMsg)

        try:
            show_loc = show_obj.location  # @UnusedVariable
        except ShowDirectoryNotFoundException:
            return self._genericMessage("Error", "Can't rename episodes when the show dir is missing.")

        if eps is None:
            return self.redirect("/home/displayShow?show=" + show)

        myDB = db.DBConnection()
        for curEp in eps.split('|'):

            epInfo = curEp.split('x')

            # this is probably the worst possible way to deal with double eps but I've kinda painted myself into a corner here with this stupid database
            ep_result = myDB.select(
                "SELECT * FROM tv_episodes WHERE showid = ? AND season = ? AND episode = ? AND 5=5",
                [show, epInfo[0], epInfo[1]])
            if not ep_result:
                logger.log(u"Unable to find an episode for " + curEp + ", skipping", logger.WARNING)
                continue
            related_eps_result = myDB.select("SELECT * FROM tv_episodes WHERE location = ? AND episode != ?",
                                             [ep_result[0]["location"], epInfo[1]])

            root_ep_obj = show_obj.getEpisode(int(epInfo[0]), int(epInfo[1]))
            root_ep_obj.relatedEps = []

            for cur_related_ep in related_eps_result:
                related_ep_obj = show_obj.getEpisode(int(cur_related_ep["season"]), int(cur_related_ep["episode"]))
                if related_ep_obj not in root_ep_obj.relatedEps:
                    root_ep_obj.relatedEps.append(related_ep_obj)

            root_ep_obj.rename()

        return self.redirect("/home/displayShow?show=" + show)

    def searchEpisode(self, show=None, season=None, episode=None, downCurQuality=0):

        # retrieve the episode object and fail if we can't get one
        ep_obj = self._getEpisode(show, season, episode)
        if isinstance(ep_obj, str):
            return json.dumps({'result': 'failure'})

        # make a queue item for it and put it on the queue
        ep_queue_item = search_queue.ManualSearchQueueItem(ep_obj.show, ep_obj, bool(int(downCurQuality)))

        sickbeard.searchQueueScheduler.action.add_item(ep_queue_item)

        if not ep_queue_item.started and ep_queue_item.success is None:
            return json.dumps(
                {'result': 'success'})  # I Actually want to call it queued, because the search hasnt been started yet!
        if ep_queue_item.started and ep_queue_item.success is None:
            return json.dumps({'result': 'success'})
        else:
            return json.dumps({'result': 'failure'})

    ### Returns the current ep_queue_item status for the current viewed show.
    # Possible status: Downloaded, Snatched, etc...
    # Returns {'show': 279530, 'episodes' : ['episode' : 6, 'season' : 1, 'searchstatus' : 'queued', 'status' : 'running', 'quality': '4013']
    def getManualSearchStatus(self, show=None):
        def getEpisodes(searchThread, searchstatus):
            results = []
            showObj = sickbeard.helpers.findCertainShow(sickbeard.showList, int(searchThread.show.indexerid))

            if not showObj:
                logger.log('No Show Object found for show with indexerID: ' + str(searchThread.show.indexerid), logger.ERROR)
                return results

            if isinstance(searchThread, sickbeard.search_queue.ManualSearchQueueItem):
                results.append({'show': searchThread.show.indexerid,
                                'episode': searchThread.segment.episode,
                                'episodeindexid': searchThread.segment.indexerid,
                                'season': searchThread.segment.season,
                                'searchstatus': searchstatus,
                                'status': statusStrings[searchThread.segment.status],
                                'quality': self.getQualityClass(searchThread.segment),
                                'overview': Overview.overviewStrings[showObj.getOverview(int(searchThread.segment.status or -1))]})
            else:
                for epObj in searchThread.segment:
                    results.append({'show': epObj.show.indexerid,
                                    'episode': epObj.episode,
                                    'episodeindexid': epObj.indexerid,
                                    'season': epObj.season,
                                    'searchstatus': searchstatus,
                                    'status': statusStrings[epObj.status],
                                    'quality': self.getQualityClass(epObj),
                                    'overview': Overview.overviewStrings[showObj.getOverview(int(epObj.status or -1))]})

            return results

        episodes = []

        # Queued Searches
        searchstatus = 'queued'
        for searchThread in sickbeard.searchQueueScheduler.action.get_all_ep_from_queue(show):
            episodes += getEpisodes(searchThread, searchstatus)

        # Running Searches
        searchstatus = 'searching'
        if (sickbeard.searchQueueScheduler.action.is_manualsearch_in_progress()):
            searchThread = sickbeard.searchQueueScheduler.action.currentItem

            if searchThread.success:
                searchstatus = 'finished'

            episodes += getEpisodes(searchThread, searchstatus)

        # Finished Searches
        searchstatus = 'finished'
        for searchThread in sickbeard.search_queue.MANUAL_SEARCH_HISTORY:
            if show is not None:
                if not str(searchThread.show.indexerid) == show:
                    continue

            if isinstance(searchThread, sickbeard.search_queue.ManualSearchQueueItem):
                if not [x for x in episodes if x['episodeindexid'] == searchThread.segment.indexerid]:
                    episodes += getEpisodes(searchThread, searchstatus)
            else:
                ### These are only Failed Downloads/Retry SearchThreadItems.. lets loop through the segement/episodes
                if not [i for i, j in zip(searchThread.segment, episodes) if i.indexerid == j['episodeindexid']]:
                    episodes += getEpisodes(searchThread, searchstatus)

        return json.dumps({'episodes': episodes})

    def getQualityClass(self, ep_obj):
        # return the correct json value

        # Find the quality class for the episode
        ep_status, ep_quality = Quality.splitCompositeStatus(ep_obj.status)
        if ep_quality in Quality.cssClassStrings:
            quality_class = Quality.cssClassStrings[ep_quality]
        else:
            quality_class = Quality.cssClassStrings[Quality.UNKNOWN]

        return quality_class

    def searchEpisodeSubtitles(self, show=None, season=None, episode=None):
        # retrieve the episode object and fail if we can't get one
        ep_obj = self._getEpisode(show, season, episode)
        if isinstance(ep_obj, str):
            return json.dumps({'result': 'failure'})

        # try do download subtitles for that episode
        previous_subtitles = ep_obj.subtitles
        try:
            ep_obj.downloadSubtitles()
        except:
            return json.dumps({'result': 'failure'})

        # return the correct json value
        newSubtitles = frozenset(ep_obj.subtitles).difference(previous_subtitles)
        if newSubtitles:
            newLangs = [subtitles.fromietf(newSub) for newSub in newSubtitles]
            status = 'New subtitles downloaded: %s' % ', '.join([newLang.name for newLang in newLangs])
        else:
            status = 'No subtitles downloaded'
        ui.notifications.message(ep_obj.show.name, status)
        return json.dumps({'result': status, 'subtitles': ','.join(ep_obj.subtitles)})

    def setSceneNumbering(self, show, indexer, forSeason=None, forEpisode=None, forAbsolute=None, sceneSeason=None,
                          sceneEpisode=None, sceneAbsolute=None):

        # sanitize:
        if forSeason in ['null', '']: forSeason = None
        if forEpisode in ['null', '']: forEpisode = None
        if forAbsolute in ['null', '']: forAbsolute = None
        if sceneSeason in ['null', '']: sceneSeason = None
        if sceneEpisode in ['null', '']: sceneEpisode = None
        if sceneAbsolute in ['null', '']: sceneAbsolute = None

        showObj = sickbeard.helpers.findCertainShow(sickbeard.showList, int(show))

        if showObj.is_anime:
            result = {
                'success': True,
                'forAbsolute': forAbsolute,
            }
        else:
            result = {
                'success': True,
                'forSeason': forSeason,
                'forEpisode': forEpisode,
            }

        # retrieve the episode object and fail if we can't get one
        if showObj.is_anime:
            ep_obj = self._getEpisode(show, absolute=forAbsolute)
        else:
            ep_obj = self._getEpisode(show, forSeason, forEpisode)

        if isinstance(ep_obj, str):
            result['success'] = False
            result['errorMessage'] = ep_obj
        elif showObj.is_anime:
            logger.log(u"setAbsoluteSceneNumbering for %s from %s to %s" %
                       (show, forAbsolute, sceneAbsolute), logger.DEBUG)

            show = int(show)
            indexer = int(indexer)
            forAbsolute = int(forAbsolute)
            if sceneAbsolute is not None: sceneAbsolute = int(sceneAbsolute)

            set_scene_numbering(show, indexer, absolute_number=forAbsolute, sceneAbsolute=sceneAbsolute)
        else:
            logger.log(u"setEpisodeSceneNumbering for %s from %sx%s to %sx%s" %
                       (show, forSeason, forEpisode, sceneSeason, sceneEpisode), logger.DEBUG)

            show = int(show)
            indexer = int(indexer)
            forSeason = int(forSeason)
            forEpisode = int(forEpisode)
            if sceneSeason is not None: sceneSeason = int(sceneSeason)
            if sceneEpisode is not None: sceneEpisode = int(sceneEpisode)

            set_scene_numbering(show, indexer, season=forSeason, episode=forEpisode, sceneSeason=sceneSeason,
                                sceneEpisode=sceneEpisode)

        if showObj.is_anime:
            sn = get_scene_absolute_numbering(show, indexer, forAbsolute)
            if sn:
                result['sceneAbsolute'] = sn
            else:
                result['sceneAbsolute'] = None
        else:
            sn = get_scene_numbering(show, indexer, forSeason, forEpisode)
            if sn:
                (result['sceneSeason'], result['sceneEpisode']) = sn
            else:
                (result['sceneSeason'], result['sceneEpisode']) = (None, None)

        return json.dumps(result)


    def retryEpisode(self, show, season, episode, downCurQuality):

        # retrieve the episode object and fail if we can't get one
        ep_obj = self._getEpisode(show, season, episode)
        if isinstance(ep_obj, str):
            return json.dumps({'result': 'failure'})

        # make a queue item for it and put it on the queue
        ep_queue_item = search_queue.FailedQueueItem(ep_obj.show, [ep_obj], bool(int(downCurQuality)))
        sickbeard.searchQueueScheduler.action.add_item(ep_queue_item)

        if not ep_queue_item.started and ep_queue_item.success is None:
            return json.dumps(
                {'result': 'success'})  # I Actually want to call it queued, because the search hasnt been started yet!
        if ep_queue_item.started and ep_queue_item.success is None:
            return json.dumps({'result': 'success'})
        else:
            return json.dumps({'result': 'failure'})

    def fetch_releasegroups(self, show_name):
        logger.log(u'ReleaseGroups: %s' % show_name, logger.INFO)
        if helpers.set_up_anidb_connection():
            anime = adba.Anime(sickbeard.ADBA_CONNECTION, name=show_name)
            groups = anime.get_groups()
            logger.log(u'ReleaseGroups: %s' % groups, logger.INFO)
            return json.dumps({'result': 'success', 'groups': groups})

        return json.dumps({'result': 'failure'})

@route('/IRC(/?.*)')
class HomeIRC(Home):
    def __init__(self, *args, **kwargs):
        super(HomeIRC, self).__init__(*args, **kwargs)

    def index(self):

        t = PageTemplate(rh=self, file="IRC.mako")
        return t.render(topmenu="system", header="IRC", title="IRC")

@route('/news(/?.*)')
class HomeNews(Home):
    def __init__(self, *args, **kwargs):
        super(HomeNews, self).__init__(*args, **kwargs)

    def index(self):
        try:
            news = sickbeard.versionCheckScheduler.action.check_for_new_news(force=True)
        except Exception:
            logger.log(u'Could not load news from repo, giving a link!', logger.DEBUG)
            news = 'Could not load news from the repo. [Click here for news.md]('+sickbeard.NEWS_URL+')'

        sickbeard.NEWS_LAST_READ = sickbeard.NEWS_LATEST
        sickbeard.NEWS_UNREAD = 0
        sickbeard.save_config()

        t = PageTemplate(rh=self, file="markdown.mako")
        data = markdown2.markdown(news if news else "The was a problem connecting to github, please refresh and try again", extras=['header-ids'])

        return t.render(title="News", header="News", topmenu="system", data=data)


@route('/changes(/?.*)')
class HomeChangeLog(Home):
    def __init__(self, *args, **kwargs):
        super(HomeChangeLog, self).__init__(*args, **kwargs)

    def index(self):
        try:
            changes = helpers.getURL('http://sickragetv.github.io/sickrage-news/CHANGES.md', session=requests.Session())
        except Exception:
            logger.log(u'Could not load changes from repo, giving a link!', logger.DEBUG)
            changes = 'Could not load changes from the repo. [Click here for CHANGES.md](http://sickragetv.github.io/sickrage-news/CHANGES.md)'

        t = PageTemplate(rh=self, file="markdown.mako")
        data = markdown2.markdown(changes if changes else "The was a problem connecting to github, please refresh and try again", extras=['header-ids'])

        return t.render(title="Changelog", header="Changelog", topmenu="system", data=data)


@route('/home/postprocess(/?.*)')
class HomePostProcess(Home):
    def __init__(self, *args, **kwargs):
        super(HomePostProcess, self).__init__(*args, **kwargs)

    def index(self):
        t = PageTemplate(rh=self, file="home_postprocess.mako")
        return t.render(title='Post Processing', header='Post Processing', topmenu='home')

    def processEpisode(self, dir=None, nzbName=None, jobName=None, quiet=None, process_method=None, force=None,
                       is_priority=None, delete_on="0", failed="0", type="auto", *args, **kwargs):

        if failed == "0":
            failed = False
        else:
            failed = True

        if force in ["on", "1"]:
            force = True
        else:
            force = False

        if is_priority in ["on", "1"]:
            is_priority = True
        else:
            is_priority = False

        if delete_on in ["on", "1"]:
            delete_on = True
        else:
            delete_on = False

        if not dir:
            return self.redirect("/home/postprocess/")
        else:
            result = processTV.processDir(dir, nzbName, process_method=process_method, force=force,
                                          is_priority=is_priority, delete_on=delete_on, failed=failed, type=type)
            if quiet is not None and int(quiet) == 1:
                return result

            result = result.replace("\n", "<br />\n")
            return self._genericMessage("Postprocessing results", result)


@route('/home/addShows(/?.*)')
class HomeAddShows(Home):
    def __init__(self, *args, **kwargs):
        super(HomeAddShows, self).__init__(*args, **kwargs)

    def index(self):
        t = PageTemplate(rh=self, file="home_addShows.mako")
        return t.render(title='Add Shows', header='Add Shows', topmenu='home')

    def getIndexerLanguages(self):
        result = sickbeard.indexerApi().config['valid_languages']

        return json.dumps({'results': result})


    def sanitizeFileName(self, name):
        return helpers.sanitizeFileName(name)


    def searchIndexersForShowName(self, search_term, lang=None, indexer=None):
        if not lang or lang == 'null':
            lang = sickbeard.INDEXER_DEFAULT_LANGUAGE

        search_term = search_term.encode('utf-8')

        results = {}
        final_results = []

        # Query Indexers for each search term and build the list of results
        for indexer in sickbeard.indexerApi().indexers if not int(indexer) else [int(indexer)]:
            lINDEXER_API_PARMS = sickbeard.indexerApi(indexer).api_params.copy()
            lINDEXER_API_PARMS['language'] = lang
            lINDEXER_API_PARMS['custom_ui'] = classes.AllShowsListUI
            t = sickbeard.indexerApi(indexer).indexer(**lINDEXER_API_PARMS)

            logger.log("Searching for Show with searchterm: %s on Indexer: %s" % (
                search_term, sickbeard.indexerApi(indexer).name), logger.DEBUG)
            try:
                # add search results
                results.setdefault(indexer, []).extend(t[search_term])
            except Exception, e:
                continue

        map(final_results.extend,
            ([[sickbeard.indexerApi(id).name, id, sickbeard.indexerApi(id).config["show_url"], int(show['id']),
               show['seriesname'], show['firstaired']] for show in shows] for id, shows in results.iteritems()))

        lang_id = sickbeard.indexerApi().config['langabbv_to_id'][lang]
        return json.dumps({'results': final_results, 'langid': lang_id})


    def massAddTable(self, rootDir=None):
        t = PageTemplate(rh=self, file="home_massAddTable.mako")

        if not rootDir:
            return "No folders selected."
        elif type(rootDir) != list:
            root_dirs = [rootDir]
        else:
            root_dirs = rootDir

        root_dirs = [urllib.unquote_plus(x) for x in root_dirs]

        if sickbeard.ROOT_DIRS:
            default_index = int(sickbeard.ROOT_DIRS.split('|')[0])
        else:
            default_index = 0

        if len(root_dirs) > default_index:
            tmp = root_dirs[default_index]
            if tmp in root_dirs:
                root_dirs.remove(tmp)
                root_dirs = [tmp] + root_dirs

        dir_list = []

        myDB = db.DBConnection()
        for root_dir in root_dirs:
            try:
                file_list = ek(os.listdir, root_dir)
            except:
                continue

            for cur_file in file_list:

                try:
                    cur_path = ek(os.path.normpath, ek(os.path.join, root_dir, cur_file))
                    if not ek(os.path.isdir, cur_path):
                        continue
                except:
                    continue

                cur_dir = {
                    'dir': cur_path,
                    'display_dir': '<b>' + ek(os.path.dirname, cur_path) + os.sep + '</b>' + ek(
                        os.path.basename,
                        cur_path),
                }

                # see if the folder is in KODI already
                dirResults = myDB.select("SELECT * FROM tv_shows WHERE location = ?", [cur_path])

                if dirResults:
                    cur_dir['added_already'] = True
                else:
                    cur_dir['added_already'] = False

                dir_list.append(cur_dir)

                indexer_id = show_name = indexer = None
                for cur_provider in sickbeard.metadata_provider_dict.values():
                    if not (indexer_id and show_name):
                        (indexer_id, show_name, indexer) = cur_provider.retrieveShowMetadata(cur_path)

                        # default to TVDB if indexer was not detected
                        if show_name and not (indexer or indexer_id):
                            (sn, idx, id) = helpers.searchIndexerForShowID(show_name, indexer, indexer_id)

                            # set indexer and indexer_id from found info
                            if not indexer and idx:
                                indexer = idx

                            if not indexer_id and id:
                                indexer_id = id

                cur_dir['existing_info'] = (indexer_id, show_name, indexer)

                if indexer_id and helpers.findCertainShow(sickbeard.showList, indexer_id):
                    cur_dir['added_already'] = True


        return t.render(dirList=dir_list)


    def newShow(self, show_to_add=None, other_shows=None, search_string=None):
        """
        Display the new show page which collects a tvdb id, folder, and extra options and
        posts them to addNewShow
        """
        t = PageTemplate(rh=self, file="home_newShow.mako")

        indexer, show_dir, indexer_id, show_name = self.split_extra_show(show_to_add)

        if indexer_id and indexer and show_name:
            use_provided_info = True
        else:
            use_provided_info = False

        # use the given show_dir for the indexer search if available
        if not show_dir:
            if search_string:
                default_show_name = search_string
            else:
                default_show_name = ''

        elif not show_name:
            default_show_name = re.sub(' \(\d{4}\)', '',
                                         ek(os.path.basename, ek(os.path.normpath, show_dir)).replace('.', ' '))
        else:
            default_show_name = show_name

        # carry a list of other dirs if given
        if not other_shows:
            other_shows = []
        elif type(other_shows) != list:
            other_shows = [other_shows]

        provided_indexer_id = int(indexer_id or 0)
        provided_indexer_name = show_name

        provided_indexer = int(indexer or sickbeard.INDEXER_DEFAULT)

        return t.render(enable_anime_options=True,
                use_provided_info=use_provided_info, default_show_name=default_show_name, other_shows=other_shows,
                provided_show_dir=show_dir, provided_indexer_id=provided_indexer_id, provided_indexer_name=provided_indexer_name,
                provided_indexer=provided_indexer, indexers=sickbeard.indexerApi().indexers, whitelist=[], blacklist=[], groups=[],
                title='New Show', header='New Show', topmenu='home'
        )

    def recommendedShows(self):
        """
        Display the new show page which collects a tvdb id, folder, and extra options and
        posts them to addNewShow
        """
        t = PageTemplate(rh=self, file="home_recommendedShows.mako")
        return t.render(title="Recommended Shows", header="Recommended Shows", enable_anime_options=False)

    def getRecommendedShows(self):
        t = PageTemplate(rh=self, file="trendingShows.mako")

        trending_shows = []

        trakt_api = TraktAPI(sickbeard.SSL_VERIFY, sickbeard.TRAKT_TIMEOUT)

        try:
            not_liked_show = ""
            if sickbeard.TRAKT_BLACKLIST_NAME is not None and sickbeard.TRAKT_BLACKLIST_NAME:
                not_liked_show = trakt_api.traktRequest("users/" + sickbeard.TRAKT_USERNAME + "/lists/" + sickbeard.TRAKT_BLACKLIST_NAME + "/items") or []
            else:
                logger.log(u"trending blacklist name is empty", logger.DEBUG)

            shows = trakt_api.traktRequest("recommendations/shows?extended=full,images") or []

            library_shows = trakt_api.traktRequest("sync/collection/shows?extended=full") or []

            for show_detail in shows:
                show = {}
                show['show']=show_detail
                try:
                    if not helpers.findCertainShow(sickbeard.showList, [int(show['show']['ids']['tvdb'])]):
                        if show['show']['ids']['tvdb'] not in (lshow['show']['ids']['tvdb'] for lshow in library_shows):
                            if not_liked_show:
                                if show['show']['ids']['tvdb'] not in (show['show']['ids']['tvdb'] for show in not_liked_show if show['type'] == 'show'):
                                    trending_shows += [show]
                            else:
                                trending_shows += [show]

                except MultipleShowObjectsException:
                    continue

            if sickbeard.TRAKT_BLACKLIST_NAME != '':
                blacklist = True
            else:
                blacklist = False

        except traktException as e:
            logger.log(u"Could not connect to Trakt service: %s" % ex(e), logger.WARNING)

        return t.render(title="Trending Shows", header="Trending Shows", trending_shows=trending_shows, blacklist=blacklist)

    def trendingShows(self):
        """
        Display the new show page which collects a tvdb id, folder, and extra options and
        posts them to addNewShow
        """
        t = PageTemplate(rh=self, file="home_trendingShows.mako")
        return t.render(title="Trending Shows", header="Trending Shows", enable_anime_options=False)

    def getTrendingShows(self):
        """
        Display the new show page which collects a tvdb id, folder, and extra options and
        posts them to addNewShow
        """
        t = PageTemplate(rh=self, file="trendingShows.mako")

        trending_shows = []

        trakt_api = TraktAPI(sickbeard.SSL_VERIFY, sickbeard.TRAKT_TIMEOUT)

        try:
            not_liked_show = ""
            if sickbeard.TRAKT_BLACKLIST_NAME is not None and sickbeard.TRAKT_BLACKLIST_NAME:
                not_liked_show = trakt_api.traktRequest("users/" + sickbeard.TRAKT_USERNAME + "/lists/" + sickbeard.TRAKT_BLACKLIST_NAME + "/items") or []
            else:
                logger.log(u"trending blacklist name is empty", logger.DEBUG)

            limit_show = 50 + len(not_liked_show)

            shows = trakt_api.traktRequest("shows/trending?limit=" + str(limit_show) + "&extended=full,images") or []

            library_shows = trakt_api.traktRequest("sync/collection/shows?extended=full") or []
            for show in shows:
                try:
                    if not helpers.findCertainShow(sickbeard.showList, [int(show['show']['ids']['tvdb'])]):
                        if show['show']['ids']['tvdb'] not in (lshow['show']['ids']['tvdb'] for lshow in library_shows):
                            if not_liked_show:
                                if show['show']['ids']['tvdb'] not in (show['show']['ids']['tvdb'] for show in not_liked_show if show['type'] == 'show'):
                                    trending_shows += [show]
                            else:
                                trending_shows += [show]

                except MultipleShowObjectsException:
                    continue

            if sickbeard.TRAKT_BLACKLIST_NAME != '':
                blacklist = True
            else:
                blacklist = False

        except traktException as e:
            logger.log(u"Could not connect to Trakt service: %s" % ex(e), logger.WARNING)

        return t.render(blacklist=blacklist, trending_shows=trending_shows)


    def popularShows(self):
        """
        Fetches data from IMDB to show a list of popular shows.
        """
        t = PageTemplate(rh=self, file="home_popularShows.mako")
        e = None

        try:
            popular_shows = imdb_popular.fetch_popular_shows()
        except Exception as e:
            popular_shows = None

        return t.render(title="Popular Shows", header="Popular Shows", popular_shows=popular_shows, imdb_exception=e, topmenu="home")


    def addShowToBlacklist(self, indexer_id):

        # URL parameters
        data = {
            'shows': [
                {
                    'ids': {
                           'tvdb': indexer_id
                           }
                }
            ]
        }

        trakt_api = TraktAPI(sickbeard.SSL_VERIFY, sickbeard.TRAKT_TIMEOUT)

        result=trakt_api.traktRequest("users/" + sickbeard.TRAKT_USERNAME + "/lists/" + sickbeard.TRAKT_BLACKLIST_NAME + "/items", data, method='POST')

        return self.redirect('/home/addShows/trendingShows/')

    def existingShows(self):
        """
        Prints out the page to add existing shows from a root dir
        """
        t = PageTemplate(rh=self, file="home_addExistingShow.mako")
        return t.render(enable_anime_options=False, title='Existing Show', header='Existing Show', topmenu="home")

    def addTraktShow(self, indexer_id, showName):
        if helpers.findCertainShow(sickbeard.showList, int(indexer_id)):
            return

        if sickbeard.ROOT_DIRS:
            root_dirs = sickbeard.ROOT_DIRS.split('|')
            location = root_dirs[int(root_dirs[0]) + 1]
        else:
            location = None

        if location:
            show_dir = ek(os.path.join, location, helpers.sanitizeFileName(showName))
            dir_exists = helpers.makeDir(show_dir)
            if not dir_exists:
                logger.log(u"Unable to create the folder " + show_dir + ", can't add the show", logger.ERROR)
                return
            else:
                helpers.chmodAsParent(show_dir)

            sickbeard.showQueueScheduler.action.addShow(1, int(indexer_id), show_dir,
                                                        default_status=sickbeard.STATUS_DEFAULT,
                                                        quality=sickbeard.QUALITY_DEFAULT,
                                                        flatten_folders=sickbeard.FLATTEN_FOLDERS_DEFAULT,
                                                        subtitles=sickbeard.SUBTITLES_DEFAULT,
                                                        anime=sickbeard.ANIME_DEFAULT,
                                                        scene=sickbeard.SCENE_DEFAULT,
                                                        default_status_after=sickbeard.STATUS_DEFAULT_AFTER,
                                                        archive=sickbeard.ARCHIVE_DEFAULT)

            ui.notifications.message('Show added', 'Adding the specified show into ' + show_dir)
        else:
            logger.log(u"There was an error creating the show, no root directory setting found", logger.ERROR)
            return "No root directories setup, please go back and add one."

        # done adding show
        return self.redirect('/home/')

    def addNewShow(self, whichSeries=None, indexerLang=None, rootDir=None, defaultStatus=None,
                   anyQualities=None, bestQualities=None, flatten_folders=None, subtitles=None,
                   fullShowPath=None, other_shows=None, skipShow=None, providedIndexer=None, anime=None,
                   scene=None, blacklist=None, whitelist=None, defaultStatusAfter=None, archive=None):
        """
        Receive tvdb id, dir, and other options and create a show from them. If extra show dirs are
        provided then it forwards back to newShow, if not it goes to /home.
        """

        if indexerLang is None:
            indexerLang = sickbeard.INDEXER_DEFAULT_LANGUAGE

        # grab our list of other dirs if given
        if not other_shows:
            other_shows = []
        elif type(other_shows) != list:
            other_shows = [other_shows]

        def finishAddShow():
            # if there are no extra shows then go home
            if not other_shows:
                return self.redirect('/home/')

            # peel off the next one
            next_show_dir = other_shows[0]
            rest_of_show_dirs = other_shows[1:]

            # go to add the next show
            return self.newShow(next_show_dir, rest_of_show_dirs)

        # if we're skipping then behave accordingly
        if skipShow:
            return finishAddShow()

        # sanity check on our inputs
        if (not rootDir and not fullShowPath) or not whichSeries:
            return "Missing params, no Indexer ID or folder:" + repr(whichSeries) + " and " + repr(
                rootDir) + "/" + repr(fullShowPath)

        # figure out what show we're adding and where
        series_pieces = whichSeries.split('|')
        if (whichSeries and rootDir) or (whichSeries and fullShowPath and len(series_pieces) > 1):
            if len(series_pieces) < 6:
                logger.log("Unable to add show due to show selection. Not anough arguments: %s" % (repr(series_pieces)),
                           logger.ERROR)
                ui.notifications.error("Unknown error. Unable to add show due to problem with show selection.")
                return self.redirect('/home/addShows/existingShows/')

            indexer = int(series_pieces[1])
            indexer_id = int(series_pieces[3])
            # Show name was sent in UTF-8 in the form
            show_name = series_pieces[4].decode('utf-8')
        else:
            # if no indexer was provided use the default indexer set in General settings
            if not providedIndexer:
                providedIndexer = sickbeard.INDEXER_DEFAULT

            indexer = int(providedIndexer)
            indexer_id = int(whichSeries)
            show_name = os.path.basename(os.path.normpath(fullShowPath))

        # use the whole path if it's given, or else append the show name to the root dir to get the full show path
        if fullShowPath:
            show_dir = ek(os.path.normpath, fullShowPath)
        else:
            show_dir = ek(os.path.join, rootDir, helpers.sanitizeFileName(show_name))

        # blanket policy - if the dir exists you should have used "add existing show" numbnuts
        if ek(os.path.isdir, show_dir) and not fullShowPath:
            ui.notifications.error("Unable to add show", "Folder " + show_dir + " exists already")
            return self.redirect('/home/addShows/existingShows/')

        # don't create show dir if config says not to
        if sickbeard.ADD_SHOWS_WO_DIR:
            logger.log(u"Skipping initial creation of " + show_dir + " due to config.ini setting")
        else:
            dir_exists = helpers.makeDir(show_dir)
            if not dir_exists:
                logger.log(u"Unable to create the folder " + show_dir + ", can't add the show", logger.ERROR)
                ui.notifications.error("Unable to add show",
                                       "Unable to create the folder " + show_dir + ", can't add the show")
                #Dont redirect to default page because user wants to see the new show
                return self.redirect("/home/")
            else:
                helpers.chmodAsParent(show_dir)

        # prepare the inputs for passing along
        scene = config.checkbox_to_value(scene)
        anime = config.checkbox_to_value(anime)
        flatten_folders = config.checkbox_to_value(flatten_folders)
        subtitles = config.checkbox_to_value(subtitles)
        archive = config.checkbox_to_value(archive)

        if whitelist:
            whitelist = short_group_names(whitelist)
        if blacklist:
            blacklist = short_group_names(blacklist)

        if not anyQualities:
            anyQualities = []
        if not bestQualities:
            bestQualities = []
        if type(anyQualities) != list:
            anyQualities = [anyQualities]
        if type(bestQualities) != list:
            bestQualities = [bestQualities]
        newQuality = Quality.combineQualities(map(int, anyQualities), map(int, bestQualities))

        # add the show
        sickbeard.showQueueScheduler.action.addShow(indexer, indexer_id, show_dir, int(defaultStatus), newQuality,
                                                    flatten_folders, indexerLang, subtitles, anime,
                                                    scene, None, blacklist, whitelist, int(defaultStatusAfter), archive)
        ui.notifications.message('Show added', 'Adding the specified show into ' + show_dir)

        return finishAddShow()

    def split_extra_show(self, extra_show):
        if not extra_show:
            return (None, None, None, None)
        split_vals = extra_show.split('|')
        if len(split_vals) < 4:
            indexer = split_vals[0]
            show_dir = split_vals[1]
            return (indexer, show_dir, None, None)
        indexer = split_vals[0]
        show_dir = split_vals[1]
        indexer_id = split_vals[2]
        show_name = '|'.join(split_vals[3:])

        return (indexer, show_dir, indexer_id, show_name)


    def addExistingShows(self, shows_to_add=None, promptForSettings=None):
        """
        Receives a dir list and add them. Adds the ones with given TVDB IDs first, then forwards
        along to the newShow page.
        """

        # grab a list of other shows to add, if provided
        if not shows_to_add:
            shows_to_add = []
        elif type(shows_to_add) != list:
            shows_to_add = [shows_to_add]

        shows_to_add = [urllib.unquote_plus(x) for x in shows_to_add]

        promptForSettings = config.checkbox_to_value(promptForSettings)

        indexer_id_given = []
        dirs_only = []
        # separate all the ones with Indexer IDs
        for cur_dir in shows_to_add:
            if '|' in cur_dir:
                split_vals = cur_dir.split('|')
                if len(split_vals) < 3:
                    dirs_only.append(cur_dir)
            if not '|' in cur_dir:
                dirs_only.append(cur_dir)
            else:
                indexer, show_dir, indexer_id, show_name = self.split_extra_show(cur_dir)

                if not show_dir or not indexer_id or not show_name:
                    continue

                indexer_id_given.append((int(indexer), show_dir, int(indexer_id), show_name))


        # if they want me to prompt for settings then I will just carry on to the newShow page
        if promptForSettings and shows_to_add:
            return self.newShow(shows_to_add[0], shows_to_add[1:])

        # if they don't want me to prompt for settings then I can just add all the nfo shows now
        num_added = 0
        for cur_show in indexer_id_given:
            indexer, show_dir, indexer_id, show_name = cur_show

            if indexer is not None and indexer_id is not None:
                # add the show
                sickbeard.showQueueScheduler.action.addShow(indexer, indexer_id, show_dir,
                                                            default_status=sickbeard.STATUS_DEFAULT,
                                                            quality=sickbeard.QUALITY_DEFAULT,
                                                            flatten_folders=sickbeard.FLATTEN_FOLDERS_DEFAULT,
                                                            subtitles=sickbeard.SUBTITLES_DEFAULT,
                                                            anime=sickbeard.ANIME_DEFAULT,
                                                            scene=sickbeard.SCENE_DEFAULT,
                                                            default_status_after=sickbeard.STATUS_DEFAULT_AFTER,
                                                            archive=sickbeard.ARCHIVE_DEFAULT)
                num_added += 1

        if num_added:
            ui.notifications.message("Shows Added",
                                     "Automatically added " + str(num_added) + " from their existing metadata files")

        # if we're done then go home
        if not dirs_only:
            return self.redirect('/home/')

        # for the remaining shows we need to prompt for each one, so forward this on to the newShow page
        return self.newShow(dirs_only[0], dirs_only[1:])


@route('/manage(/?.*)')
class Manage(Home, WebRoot):
    def __init__(self, *args, **kwargs):
        super(Manage, self).__init__(*args, **kwargs)


    def index(self):
        t = PageTemplate(rh=self, file="manage.mako")
        return t.render(title='Mass Update', header='Mass Update', topmenu='manage')


    def showEpisodeStatuses(self, indexer_id, whichStatus):
        status_list = [int(whichStatus)]
        if status_list[0] == SNATCHED:
            status_list = Quality.SNATCHED + Quality.SNATCHED_PROPER

        myDB = db.DBConnection()
        cur_show_results = myDB.select(
            "SELECT season, episode, name FROM tv_episodes WHERE showid = ? AND season != 0 AND status IN (" + ','.join(
                ['?'] * len(status_list)) + ")", [int(indexer_id)] + status_list)

        result = {}
        for cur_result in cur_show_results:
            cur_season = int(cur_result["season"])
            cur_episode = int(cur_result["episode"])

            if cur_season not in result:
                result[cur_season] = {}

            result[cur_season][cur_episode] = cur_result["name"]

        return json.dumps(result)


    def episodeStatuses(self, whichStatus=None):
        if whichStatus:
            status_list = [int(whichStatus)]
            if status_list[0] == SNATCHED:
                status_list = Quality.SNATCHED + Quality.SNATCHED_PROPER + Quality.SNATCHED_BEST
        else:
            status_list = []

        t = PageTemplate(rh=self, file="manage_episodeStatuses.mako")

        # if we have no status then this is as far as we need to go
        if not status_list:
            return t.render(title="Episode Overview",  header="Episode Overview",
                    topmenu="manage", whichStatus=whichStatus)

        myDB = db.DBConnection()
        status_results = myDB.select(
            "SELECT show_name, tv_shows.indexer_id AS indexer_id FROM tv_episodes, tv_shows WHERE tv_episodes.status IN (" + ','.join(
                ['?'] * len(
                    status_list)) + ") AND season != 0 AND tv_episodes.showid = tv_shows.indexer_id ORDER BY show_name",
            status_list)

        ep_counts = {}
        show_names = {}
        sorted_show_ids = []
        for cur_status_result in status_results:
            cur_indexer_id = int(cur_status_result["indexer_id"])
            if cur_indexer_id not in ep_counts:
                ep_counts[cur_indexer_id] = 1
            else:
                ep_counts[cur_indexer_id] += 1

            show_names[cur_indexer_id] = cur_status_result["show_name"]
            if cur_indexer_id not in sorted_show_ids:
                sorted_show_ids.append(cur_indexer_id)

        return t.render(title="Episode Overview",  header="Episode Overview",
                        topmenu='manage', whichStatus=whichStatus,
                        show_names=show_names, ep_counts=ep_counts, sorted_show_ids=sorted_show_ids)


    def changeEpisodeStatuses(self, oldStatus, newStatus, *args, **kwargs):

        status_list = [int(oldStatus)]
        if status_list[0] == SNATCHED:
            status_list = Quality.SNATCHED + Quality.SNATCHED_PROPER

        to_change = {}

        # make a list of all shows and their associated args
        for arg in kwargs:
            indexer_id, what = arg.split('-')

            # we don't care about unchecked checkboxes
            if kwargs[arg] != 'on':
                continue

            if indexer_id not in to_change:
                to_change[indexer_id] = []

            to_change[indexer_id].append(what)

        myDB = db.DBConnection()
        for cur_indexer_id in to_change:

            # get a list of all the eps we want to change if they just said "all"
            if 'all' in to_change[cur_indexer_id]:
                all_eps_results = myDB.select(
                    "SELECT season, episode FROM tv_episodes WHERE status IN (" + ','.join(
                        ['?'] * len(status_list)) + ") AND season != 0 AND showid = ?",
                    status_list + [cur_indexer_id])
                all_eps = [str(x["season"]) + 'x' + str(x["episode"]) for x in all_eps_results]
                to_change[cur_indexer_id] = all_eps

            self.setStatus(cur_indexer_id, '|'.join(to_change[cur_indexer_id]), newStatus, direct=True)

        return self.redirect('/manage/episodeStatuses/')


    def showSubtitleMissed(self, indexer_id, whichSubs):
        myDB = db.DBConnection()
        cur_show_results = myDB.select(
            "SELECT season, episode, name, subtitles FROM tv_episodes WHERE showid = ? AND season != 0 AND status LIKE '%4'",
            [int(indexer_id)])

        result = {}
        for cur_result in cur_show_results:
            if whichSubs == 'all':
                if not frozenset(subtitles.wantedLanguages()).difference(cur_result["subtitles"].split(',')):
                    continue
            elif whichSubs in cur_result["subtitles"]:
                continue

            cur_season = int(cur_result["season"])
            cur_episode = int(cur_result["episode"])

            if cur_season not in result:
                result[cur_season] = {}

            if cur_episode not in result[cur_season]:
                result[cur_season][cur_episode] = {}

            result[cur_season][cur_episode]["name"] = cur_result["name"]

            result[cur_season][cur_episode]["subtitles"] = cur_result["subtitles"]

        return json.dumps(result)


    def subtitleMissed(self, whichSubs=None):

        t = PageTemplate(rh=self, file="manage_subtitleMissed.mako")

        if not whichSubs:
            return t.render(whichSubs=whichSubs, title='Episode Overview', header='Episode Overview', topmenu='manage')

        myDB = db.DBConnection()
        status_results = myDB.select(
            "SELECT show_name, tv_shows.indexer_id as indexer_id, tv_episodes.subtitles subtitles " +
            "FROM tv_episodes, tv_shows " +
            "WHERE tv_shows.subtitles = 1 AND tv_episodes.status LIKE '%4' AND tv_episodes.season != 0 " +
            "AND tv_episodes.showid = tv_shows.indexer_id ORDER BY show_name")

        ep_counts = {}
        show_names = {}
        sorted_show_ids = []
        for cur_status_result in status_results:
            if whichSubs == 'all':
                if not frozenset(subtitles.wantedLanguages()).difference(cur_status_result["subtitles"].split(',')):
                    continue
            elif whichSubs in cur_status_result["subtitles"]:
                continue

            cur_indexer_id = int(cur_status_result["indexer_id"])
            if cur_indexer_id not in ep_counts:
                ep_counts[cur_indexer_id] = 1
            else:
                ep_counts[cur_indexer_id] += 1

            show_names[cur_indexer_id] = cur_status_result["show_name"]
            if cur_indexer_id not in sorted_show_ids:
                sorted_show_ids.append(cur_indexer_id)

        return t.render(whichSubs=whichSubs, show_names=show_names, ep_counts=ep_counts, sorted_show_ids=sorted_show_ids,
                        title='Missing Subtitles', header='Missing Subtitles', topmenu='manage')


    def downloadSubtitleMissed(self, *args, **kwargs):

        to_download = {}

        # make a list of all shows and their associated args
        for arg in kwargs:
            indexer_id, what = arg.split('-')

            # we don't care about unchecked checkboxes
            if kwargs[arg] != 'on':
                continue

            if indexer_id not in to_download:
                to_download[indexer_id] = []

            to_download[indexer_id].append(what)

        for cur_indexer_id in to_download:
            # get a list of all the eps we want to download subtitles if they just said "all"
            if 'all' in to_download[cur_indexer_id]:
                myDB = db.DBConnection()
                all_eps_results = myDB.select(
                    "SELECT season, episode FROM tv_episodes WHERE status LIKE '%4' AND season != 0 AND showid = ?",
                    [cur_indexer_id])
                to_download[cur_indexer_id] = [str(x["season"]) + 'x' + str(x["episode"]) for x in all_eps_results]

            for epResult in to_download[cur_indexer_id]:
                season, episode = epResult.split('x')

                show = sickbeard.helpers.findCertainShow(sickbeard.showList, int(cur_indexer_id))
                subtitles = show.getEpisode(int(season), int(episode)).downloadSubtitles()

        return self.redirect('/manage/subtitleMissed/')


    def backlogShow(self, indexer_id):

        show_obj = helpers.findCertainShow(sickbeard.showList, int(indexer_id))

        if show_obj:
            sickbeard.backlogSearchScheduler.action.searchBacklog([show_obj])

        return self.redirect("/manage/backlogOverview/")


    def backlogOverview(self):

        t = PageTemplate(rh=self, file="manage_backlogOverview.mako")

        showCounts = {}
        showCats = {}
        showSQLResults = {}

        myDB = db.DBConnection()
        for curShow in sickbeard.showList:

            epCounts = {}
            epCats = {}
            epCounts[Overview.SKIPPED] = 0
            epCounts[Overview.WANTED] = 0
            epCounts[Overview.QUAL] = 0
            epCounts[Overview.GOOD] = 0
            epCounts[Overview.UNAIRED] = 0
            epCounts[Overview.SNATCHED] = 0

            sqlResults = myDB.select(
                "SELECT * FROM tv_episodes WHERE tv_episodes.showid in (SELECT tv_shows.indexer_id FROM tv_shows WHERE tv_shows.indexer_id = ? AND paused = 0) ORDER BY tv_episodes.season DESC, tv_episodes.episode DESC",
                [curShow.indexerid])

            for curResult in sqlResults:
                curEpCat = curShow.getOverview(int(curResult["status"] or -1))
                if curEpCat:
                    epCats[str(curResult["season"]) + "x" + str(curResult["episode"])] = curEpCat
                    epCounts[curEpCat] += 1

            showCounts[curShow.indexerid] = epCounts
            showCats[curShow.indexerid] = epCats
            showSQLResults[curShow.indexerid] = sqlResults

        return t.render(showCounts=showCounts, showCats=showCats, showSQLResults=showSQLResults,
                        title='Backlog Overview', header='Backlog Overview', topmenu='manage')


    def massEdit(self, toEdit=None):

        t = PageTemplate(rh=self, file="manage_massEdit.mako")

        if not toEdit:
            return self.redirect("/manage/")

        showIDs = toEdit.split("|")
        showList = []
        for curID in showIDs:
            curID = int(curID)
            showObj = helpers.findCertainShow(sickbeard.showList, curID)
            if showObj:
                showList.append(showObj)

        archive_firstmatch_all_same = True
        last_archive_firstmatch = None

        flatten_folders_all_same = True
        last_flatten_folders = None

        paused_all_same = True
        last_paused = None

        default_ep_status_all_same = True
        last_default_ep_status = None

        anime_all_same = True
        last_anime = None

        sports_all_same = True
        last_sports = None

        quality_all_same = True
        last_quality = None

        subtitles_all_same = True
        last_subtitles = None

        scene_all_same = True
        last_scene = None

        air_by_date_all_same = True
        last_air_by_date = None

        root_dir_list = []

        for curShow in showList:

            cur_root_dir = ek(os.path.dirname, curShow._location)
            if cur_root_dir not in root_dir_list:
                root_dir_list.append(cur_root_dir)

            if archive_firstmatch_all_same:
                # if we had a value already and this value is different then they're not all the same
                if last_archive_firstmatch not in (None, curShow.archive_firstmatch):
                    archive_firstmatch_all_same = False
                else:
                    last_archive_firstmatch = curShow.archive_firstmatch

            # if we know they're not all the same then no point even bothering
            if paused_all_same:
                # if we had a value already and this value is different then they're not all the same
                if last_paused not in (None, curShow.paused):
                    paused_all_same = False
                else:
                    last_paused = curShow.paused

            if default_ep_status_all_same:
                if last_default_ep_status not in (None, curShow.default_ep_status):
                    default_ep_status_all_same = False
                else:
                    last_default_ep_status = curShow.default_ep_status

            if anime_all_same:
                # if we had a value already and this value is different then they're not all the same
                if last_anime not in (None, curShow.is_anime):
                    anime_all_same = False
                else:
                    last_anime = curShow.anime

            if flatten_folders_all_same:
                if last_flatten_folders not in (None, curShow.flatten_folders):
                    flatten_folders_all_same = False
                else:
                    last_flatten_folders = curShow.flatten_folders

            if quality_all_same:
                if last_quality not in (None, curShow.quality):
                    quality_all_same = False
                else:
                    last_quality = curShow.quality

            if subtitles_all_same:
                if last_subtitles not in (None, curShow.subtitles):
                    subtitles_all_same = False
                else:
                    last_subtitles = curShow.subtitles

            if scene_all_same:
                if last_scene not in (None, curShow.scene):
                    scene_all_same = False
                else:
                    last_scene = curShow.scene

            if sports_all_same:
                if last_sports not in (None, curShow.sports):
                    sports_all_same = False
                else:
                    last_sports = curShow.sports

            if air_by_date_all_same:
                if last_air_by_date not in (None, curShow.air_by_date):
                    air_by_date_all_same = False
                else:
                    last_air_by_date = curShow.air_by_date

        archive_firstmatch_value = last_archive_firstmatch if archive_firstmatch_all_same else None
        default_ep_status_value = last_default_ep_status if default_ep_status_all_same else None
        paused_value = last_paused if paused_all_same else None
        anime_value = last_anime if anime_all_same else None
        flatten_folders_value = last_flatten_folders if flatten_folders_all_same else None
        quality_value = last_quality if quality_all_same else None
        subtitles_value = last_subtitles if subtitles_all_same else None
        scene_value = last_scene if scene_all_same else None
        sports_value = last_sports if sports_all_same else None
        air_by_date_value = last_air_by_date if air_by_date_all_same else None
        root_dir_list = root_dir_list

        return t.render(showList=toEdit, archive_firstmatch_value=archive_firstmatch_value, default_ep_status_value=default_ep_status_value,
                        paused_value=paused_value, anime_value=anime_value, flatten_folders_value=flatten_folders_value,
                        quality_value=quality_value, subtitles_value=subtitles_value, scene_value=scene_value, sports_value=sports_value,
                        air_by_date_value=air_by_date_value, root_dir_list=root_dir_list, title='Mass Edit', header='Mass Edit', topmenu='manage')


    def massEditSubmit(self, archive_firstmatch=None, paused=None, default_ep_status=None,
                       anime=None, sports=None, scene=None, flatten_folders=None, quality_preset=False,
                       subtitles=None, air_by_date=None, anyQualities=[], bestQualities=[], toEdit=None, *args,
                       **kwargs):

        dir_map = {}
        for cur_arg in kwargs:
            if not cur_arg.startswith('orig_root_dir_'):
                continue
            which_index = cur_arg.replace('orig_root_dir_', '')
            end_dir = kwargs['new_root_dir_' + which_index]
            dir_map[kwargs[cur_arg]] = end_dir

        showIDs = toEdit.split("|")
        errors = []
        for curShow in showIDs:
            curErrors = []
            showObj = helpers.findCertainShow(sickbeard.showList, int(curShow))
            if not showObj:
                continue

            cur_root_dir = ek(os.path.dirname, showObj._location)
            cur_show_dir = ek(os.path.basename, showObj._location)
            if cur_root_dir in dir_map and cur_root_dir != dir_map[cur_root_dir]:
                new_show_dir = ek(os.path.join, dir_map[cur_root_dir], cur_show_dir)
                logger.log(
                    u"For show " + showObj.name + " changing dir from " + showObj._location + " to " + new_show_dir)
            else:
                new_show_dir = showObj._location

            if archive_firstmatch == 'keep':
                new_archive_firstmatch = showObj.archive_firstmatch
            else:
                new_archive_firstmatch = True if archive_firstmatch == 'enable' else False
            new_archive_firstmatch = 'on' if new_archive_firstmatch else 'off'

            if paused == 'keep':
                new_paused = showObj.paused
            else:
                new_paused = True if paused == 'enable' else False
            new_paused = 'on' if new_paused else 'off'

            if default_ep_status == 'keep':
                new_default_ep_status = showObj.default_ep_status
            else:
                new_default_ep_status = default_ep_status

            if anime == 'keep':
                new_anime = showObj.anime
            else:
                new_anime = True if anime == 'enable' else False
            new_anime = 'on' if new_anime else 'off'

            if sports == 'keep':
                new_sports = showObj.sports
            else:
                new_sports = True if sports == 'enable' else False
            new_sports = 'on' if new_sports else 'off'

            if scene == 'keep':
                new_scene = showObj.is_scene
            else:
                new_scene = True if scene == 'enable' else False
            new_scene = 'on' if new_scene else 'off'

            if air_by_date == 'keep':
                new_air_by_date = showObj.air_by_date
            else:
                new_air_by_date = True if air_by_date == 'enable' else False
            new_air_by_date = 'on' if new_air_by_date else 'off'

            if flatten_folders == 'keep':
                new_flatten_folders = showObj.flatten_folders
            else:
                new_flatten_folders = True if flatten_folders == 'enable' else False
            new_flatten_folders = 'on' if new_flatten_folders else 'off'

            if subtitles == 'keep':
                new_subtitles = showObj.subtitles
            else:
                new_subtitles = True if subtitles == 'enable' else False

            new_subtitles = 'on' if new_subtitles else 'off'

            if quality_preset == 'keep':
                anyQualities, bestQualities = Quality.splitQuality(showObj.quality)

            exceptions_list = []

            curErrors += self.editShow(curShow, new_show_dir, anyQualities,
                                       bestQualities, exceptions_list,
                                       defaultEpStatus=new_default_ep_status,
                                       archive_firstmatch=new_archive_firstmatch,
                                       flatten_folders=new_flatten_folders,
                                       paused=new_paused, sports=new_sports,
                                       subtitles=new_subtitles, anime=new_anime,
                                       scene=new_scene, air_by_date=new_air_by_date,
                                       directCall=True)

            if curErrors:
                logger.log(u"Errors: " + str(curErrors), logger.ERROR)
                errors.append('<b>%s:</b>\n<ul>' % showObj.name + ' '.join(
                    ['<li>%s</li>' % error for error in curErrors]) + "</ul>")

        if len(errors) > 0:
            ui.notifications.error('%d error%s while saving changes:' % (len(errors), "" if len(errors) == 1 else "s"),
                                   " ".join(errors))

        return self.redirect("/manage/")


    def massUpdate(self, toUpdate=None, toRefresh=None, toRename=None, toDelete=None, toRemove=None, toMetadata=None,
                   toSubtitle=None):

        if toUpdate is not None:
            toUpdate = toUpdate.split('|')
        else:
            toUpdate = []

        if toRefresh is not None:
            toRefresh = toRefresh.split('|')
        else:
            toRefresh = []

        if toRename is not None:
            toRename = toRename.split('|')
        else:
            toRename = []

        if toSubtitle is not None:
            toSubtitle = toSubtitle.split('|')
        else:
            toSubtitle = []

        if toDelete is not None:
            toDelete = toDelete.split('|')
        else:
            toDelete = []

        if toRemove is not None:
            toRemove = toRemove.split('|')
        else:
            toRemove = []

        if toMetadata is not None:
            toMetadata = toMetadata.split('|')
        else:
            toMetadata = []

        errors = []
        refreshes = []
        updates = []
        renames = []
        subtitles = []

        for curShowID in set(toUpdate + toRefresh + toRename + toSubtitle + toDelete + toRemove + toMetadata):

            if curShowID == '':
                continue

            showObj = sickbeard.helpers.findCertainShow(sickbeard.showList, int(curShowID))

            if showObj is None:
                continue

            if curShowID in toDelete:
                sickbeard.showQueueScheduler.action.removeShow(showObj, True)
                # don't do anything else if it's being deleted
                continue

            if curShowID in toRemove:
                sickbeard.showQueueScheduler.action.removeShow(showObj)
                # don't do anything else if it's being remove
                continue

            if curShowID in toUpdate:
                try:
                    sickbeard.showQueueScheduler.action.updateShow(showObj, True)
                    updates.append(showObj.name)
                except CantUpdateShowException, e:
                    errors.append("Unable to update show: {0}".format(str(e)))

            # don't bother refreshing shows that were updated anyway
            if curShowID in toRefresh and curShowID not in toUpdate:
                try:
                    sickbeard.showQueueScheduler.action.refreshShow(showObj)
                    refreshes.append(showObj.name)
                except CantRefreshShowException, e:
                    errors.append("Unable to refresh show " + showObj.name + ": " + ex(e))

            if curShowID in toRename:
                sickbeard.showQueueScheduler.action.renameShowEpisodes(showObj)
                renames.append(showObj.name)

            if curShowID in toSubtitle:
                sickbeard.showQueueScheduler.action.downloadSubtitles(showObj)
                subtitles.append(showObj.name)

        if errors:
            ui.notifications.error("Errors encountered",
                                   '<br >\n'.join(errors))

        messageDetail = ""

        if updates:
            messageDetail += "<br /><b>Updates</b><br /><ul><li>"
            messageDetail += "</li><li>".join(updates)
            messageDetail += "</li></ul>"

        if refreshes:
            messageDetail += "<br /><b>Refreshes</b><br /><ul><li>"
            messageDetail += "</li><li>".join(refreshes)
            messageDetail += "</li></ul>"

        if renames:
            messageDetail += "<br /><b>Renames</b><br /><ul><li>"
            messageDetail += "</li><li>".join(renames)
            messageDetail += "</li></ul>"

        if subtitles:
            messageDetail += "<br /><b>Subtitles</b><br /><ul><li>"
            messageDetail += "</li><li>".join(subtitles)
            messageDetail += "</li></ul>"

        if updates + refreshes + renames + subtitles:
            ui.notifications.message("The following actions were queued:",
                                     messageDetail)

        return self.redirect("/manage/")


    def manageTorrents(self):

        t = PageTemplate(rh=self, file="manage_torrents.mako")
        info_download_station = ''

        if re.search('localhost', sickbeard.TORRENT_HOST):

            if sickbeard.LOCALHOST_IP == '':
                webui_url = re.sub('localhost', helpers.get_lan_ip(), sickbeard.TORRENT_HOST)
            else:
                webui_url = re.sub('localhost', sickbeard.LOCALHOST_IP, sickbeard.TORRENT_HOST)
        else:
            webui_url = sickbeard.TORRENT_HOST

        if sickbeard.TORRENT_METHOD == 'utorrent':
            webui_url = '/'.join(s.strip('/') for s in (webui_url, 'gui/'))
        if sickbeard.TORRENT_METHOD == 'download_station':
            if helpers.check_url(webui_url + 'download/'):
                webui_url = webui_url + 'download/'
            else:
                info_download_station = '<p>To have a better experience please set the Download Station alias as <code>download</code>, you can check this setting in the Synology DSM <b>Control Panel</b> > <b>Application Portal</b>. Make sure you allow DSM to be embedded with iFrames too in <b>Control Panel</b> > <b>DSM Settings</b> > <b>Security</b>.</p><br/><p>There is more information about this available <a href="https://github.com/midgetspy/Sick-Beard/pull/338">here</a>.</p><br/>'

        if not sickbeard.TORRENT_PASSWORD == "" and not sickbeard.TORRENT_USERNAME == "":
            webui_url = re.sub('://', '://' + str(sickbeard.TORRENT_USERNAME) + ':' + str(sickbeard.TORRENT_PASSWORD) + '@' ,webui_url)

        return t.render(webui_url=webui_url, info_download_station=info_download_station,
                        title='Manage Torrents', header='Manage Torrents', topmenu='manage')


    def failedDownloads(self, limit=100, toRemove=None):

        myDB = db.DBConnection('failed.db')

        if limit == "0":
            sqlResults = myDB.select("SELECT * FROM failed")
        else:
            sqlResults = myDB.select("SELECT * FROM failed LIMIT ?", [limit])

        toRemove = toRemove.split("|") if toRemove is not None else []

        for release in toRemove:
            myDB.action("DELETE FROM failed WHERE failed.release = ?", [release])

        if toRemove:
            return self.redirect('/manage/failedDownloads/')

        t = PageTemplate(rh=self, file="manage_failedDownloads.mako")

        return t.render(limit=limit, failedResults=sqlResults, title='Failed Downloads', header='Failed Downloads', topmenu='manage')


@route('/manage/manageSearches(/?.*)')
class ManageSearches(Manage):
    def __init__(self, *args, **kwargs):
        super(ManageSearches, self).__init__(*args, **kwargs)

    def index(self):
        t = PageTemplate(rh=self, file="manage_manageSearches.mako")
        # t.backlogPI = sickbeard.backlogSearchScheduler.action.getProgressIndicator()

        return t.render(backlogPaused=sickbeard.searchQueueScheduler.action.is_backlog_paused(),
                        backlogRunning=sickbeard.searchQueueScheduler.action.is_backlog_in_progress(), dailySearchStatus=sickbeard.dailySearchScheduler.action.amActive,
                        findPropersStatus=sickbeard.properFinderScheduler.action.amActive, queueLength=sickbeard.searchQueueScheduler.action.queue_length(),
                        title='Manage Searches', header='Manage Searches', topmenu='manage')

    def forceBacklog(self):
        # force it to run the next time it looks
        result = sickbeard.backlogSearchScheduler.forceRun()
        if result:
            logger.log(u"Backlog search forced")
            ui.notifications.message('Backlog search started')

        return self.redirect("/manage/manageSearches/")

    def forceSearch(self):

        # force it to run the next time it looks
        result = sickbeard.dailySearchScheduler.forceRun()
        if result:
            logger.log(u"Daily search forced")
            ui.notifications.message('Daily search started')

        return self.redirect("/manage/manageSearches/")


    def forceFindPropers(self):

        # force it to run the next time it looks
        result = sickbeard.properFinderScheduler.forceRun()
        if result:
            logger.log(u"Find propers search forced")
            ui.notifications.message('Find propers search started')

        return self.redirect("/manage/manageSearches/")


    def pauseBacklog(self, paused=None):
        if paused == "1":
            sickbeard.searchQueueScheduler.action.pause_backlog()
        else:
            sickbeard.searchQueueScheduler.action.unpause_backlog()

        return self.redirect("/manage/manageSearches/")


@route('/history(/?.*)')
class History(WebRoot):
    def __init__(self, *args, **kwargs):
        super(History, self).__init__(*args, **kwargs)

        self.history = HistoryTool()

    def index(self, limit=None):

        if limit is None:
            if sickbeard.HISTORY_LIMIT:
                limit = int(sickbeard.HISTORY_LIMIT)
            else:
                limit = 100
        else:
            limit = int(limit)

        sickbeard.HISTORY_LIMIT = limit

        sickbeard.save_config()

        compact = []
        data = self.history.get(limit)

        for row in data:
            action = {
                'action': row['action'],
                'provider': row['provider'],
                'resource': row['resource'],
                'time': row['date']
            }

            if not any((history['show_id'] == row['show_id'] and
                        history['season'] == row['season'] and
                        history['episode'] == row['episode'] and
                        history['quality'] == row['quality']) for history in compact):
                history = {
                    'actions': [action],
                    'episode': row['episode'],
                    'quality': row['quality'],
                    'resource': row['resource'],
                    'season': row['season'],
                    'show_id': row['show_id'],
                    'show_name': row['show_name']
                }

                compact.append(history)
            else:
                index = [i for i, item in enumerate(compact)
                         if item['show_id'] == row['show_id'] and
                         item['season'] == row['season'] and
                         item['episode'] == row['episode'] and
                         item['quality'] == row['quality']][0]
                history = compact[index]
                history['actions'].append(action)
                history['actions'].sort(key=lambda x: x['time'], reverse=True)

        t = PageTemplate(rh=self, file="history.mako")
        submenu = [
            {'title': 'Clear History', 'path': 'history/clearHistory', 'icon': 'ui-icon ui-icon-trash', 'class': 'clearhistory', 'confirm':True},
            {'title': 'Trim History', 'path': 'history/trimHistory', 'icon': 'ui-icon ui-icon-trash', 'class': 'trimhistory', 'confirm':True},
        ]

        return t.render(historyResults=data, compactResults=compact, limit=limit, submenu=submenu, title='History', header='History', topmenu="history")

    def clearHistory(self):
        self.history.clear()

        ui.notifications.message('History cleared')

        return self.redirect("/history/")

    def trimHistory(self):
        self.history.trim()

        ui.notifications.message('Removed history entries older than 30 days')

        return self.redirect("/history/")


@route('/config(/?.*)')
class Config(WebRoot):
    def __init__(self, *args, **kwargs):
        super(Config, self).__init__(*args, **kwargs)

    def ConfigMenu(self):
        menu = [
            {'title': 'General', 'path': 'config/general/', 'icon': 'ui-icon ui-icon-gear'},
            {'title': 'Backup/Restore', 'path': 'config/backuprestore/', 'icon': 'ui-icon ui-icon-gear'},
            {'title': 'Search Settings', 'path': 'config/search/', 'icon': 'ui-icon ui-icon-search'},
            {'title': 'Search Providers', 'path': 'config/providers/', 'icon': 'ui-icon ui-icon-search'},
            {'title': 'Subtitles Settings', 'path': 'config/subtitles/', 'icon': 'ui-icon ui-icon-comment'},
            {'title': 'Post Processing', 'path': 'config/postProcessing/', 'icon': 'ui-icon ui-icon-folder-open'},
            {'title': 'Notifications', 'path': 'config/notifications/', 'icon': 'ui-icon ui-icon-note'},
            {'title': 'Anime', 'path': 'config/anime/', 'icon': 'submenu-icon-anime'},
        ]

        return menu

    def index(self):
        t = PageTemplate(rh=self, file="config.mako")

        return t.render(submenu=self.ConfigMenu(), title='Configuration', header='Configuration', topmenu="config")


@route('/config/general(/?.*)')
class ConfigGeneral(Config):
    def __init__(self, *args, **kwargs):
        super(ConfigGeneral, self).__init__(*args, **kwargs)

    def index(self):
        t = PageTemplate(rh=self, file="config_general.mako")

        return t.render(title='Config - General', header='General Configuration', topmenu='config', submenu=self.ConfigMenu())

    def generateApiKey(self):
        return helpers.generateApiKey()

    def saveRootDirs(self, rootDirString=None):
        sickbeard.ROOT_DIRS = rootDirString

    def saveAddShowDefaults(self, defaultStatus, anyQualities, bestQualities, defaultFlattenFolders, subtitles=False,
                            anime=False, scene=False, defaultStatusAfter=WANTED, archive=False):

        if anyQualities:
            anyQualities = anyQualities.split(',')
        else:
            anyQualities = []

        if bestQualities:
            bestQualities = bestQualities.split(',')
        else:
            bestQualities = []

        newQuality = Quality.combineQualities(map(int, anyQualities), map(int, bestQualities))

        sickbeard.STATUS_DEFAULT = int(defaultStatus)
        sickbeard.STATUS_DEFAULT_AFTER = int(defaultStatusAfter)
        sickbeard.QUALITY_DEFAULT = int(newQuality)

        sickbeard.FLATTEN_FOLDERS_DEFAULT = config.checkbox_to_value(defaultFlattenFolders)
        sickbeard.SUBTITLES_DEFAULT = config.checkbox_to_value(subtitles)

        sickbeard.ANIME_DEFAULT = config.checkbox_to_value(anime)
        sickbeard.SCENE_DEFAULT = config.checkbox_to_value(scene)
        sickbeard.ARCHIVE_DEFAULT = config.checkbox_to_value(archive)

        sickbeard.save_config()

    def saveGeneral(self, log_dir=None, log_nr = 5, log_size = 1048576, web_port=None, web_log=None, encryption_version=None, web_ipv6=None,
                    trash_remove_show=None, trash_rotate_logs=None, update_frequency=None, skip_removed_files=None,
                    indexerDefaultLang='en', ep_default_deleted_status=None, launch_browser=None, showupdate_hour=3, web_username=None,
                    api_key=None, indexer_default=None, timezone_display=None, cpu_preset='NORMAL',
                    web_password=None, version_notify=None, enable_https=None, https_cert=None, https_key=None,
                    handle_reverse_proxy=None, sort_article=None, auto_update=None, notify_on_update=None,
                    proxy_setting=None, proxy_indexers=None, anon_redirect=None, git_path=None, git_remote=None,
                    calendar_unprotected=None, debug=None, ssl_verify=None, no_restart=None, coming_eps_missed_range=None,
                    filter_row=None, fuzzy_dating=None, trim_zero=None, date_preset=None, date_preset_na=None, time_preset=None,
                    indexer_timeout=None, download_url=None, rootDir=None, theme_name=None, default_page=None,
                    git_reset=None, git_username=None, git_password=None, git_autoissues=None, display_all_seasons=None):

        results = []

        # Misc
        sickbeard.DOWNLOAD_URL = download_url
        sickbeard.INDEXER_DEFAULT_LANGUAGE = indexerDefaultLang
        sickbeard.EP_DEFAULT_DELETED_STATUS = ep_default_deleted_status
        sickbeard.SKIP_REMOVED_FILES = config.checkbox_to_value(skip_removed_files)
        sickbeard.LAUNCH_BROWSER = config.checkbox_to_value(launch_browser)
        config.change_SHOWUPDATE_HOUR(showupdate_hour)
        config.change_VERSION_NOTIFY(config.checkbox_to_value(version_notify))
        sickbeard.AUTO_UPDATE = config.checkbox_to_value(auto_update)
        sickbeard.NOTIFY_ON_UPDATE = config.checkbox_to_value(notify_on_update)
        # sickbeard.LOG_DIR is set in config.change_LOG_DIR()
        sickbeard.LOG_NR = log_nr
        sickbeard.LOG_SIZE = log_size

        sickbeard.TRASH_REMOVE_SHOW = config.checkbox_to_value(trash_remove_show)
        sickbeard.TRASH_ROTATE_LOGS = config.checkbox_to_value(trash_rotate_logs)
        config.change_UPDATE_FREQUENCY(update_frequency)
        sickbeard.LAUNCH_BROWSER = config.checkbox_to_value(launch_browser)
        sickbeard.SORT_ARTICLE = config.checkbox_to_value(sort_article)
        sickbeard.CPU_PRESET = cpu_preset
        sickbeard.ANON_REDIRECT = anon_redirect
        sickbeard.PROXY_SETTING = proxy_setting
        sickbeard.PROXY_INDEXERS = config.checkbox_to_value(proxy_indexers)
        sickbeard.GIT_USERNAME = git_username
        sickbeard.GIT_PASSWORD = git_password
        #sickbeard.GIT_RESET = config.checkbox_to_value(git_reset)
        #Force GIT_RESET
        sickbeard.GIT_RESET = 1
        sickbeard.GIT_AUTOISSUES = config.checkbox_to_value(git_autoissues)
        sickbeard.GIT_PATH = git_path
        sickbeard.GIT_REMOTE = git_remote
        sickbeard.CALENDAR_UNPROTECTED = config.checkbox_to_value(calendar_unprotected)
        sickbeard.NO_RESTART = config.checkbox_to_value(no_restart)
        sickbeard.DEBUG = config.checkbox_to_value(debug)
        sickbeard.SSL_VERIFY = config.checkbox_to_value(ssl_verify)
        # sickbeard.LOG_DIR is set in config.change_LOG_DIR()
        sickbeard.COMING_EPS_MISSED_RANGE = config.to_int(coming_eps_missed_range,default=7)
        sickbeard.DISPLAY_ALL_SEASONS = config.checkbox_to_value(display_all_seasons)

        sickbeard.WEB_PORT = config.to_int(web_port)
        sickbeard.WEB_IPV6 = config.checkbox_to_value(web_ipv6)
        # sickbeard.WEB_LOG is set in config.change_LOG_DIR()
        if config.checkbox_to_value(encryption_version) == 1:
            sickbeard.ENCRYPTION_VERSION = 2
        else:
            sickbeard.ENCRYPTION_VERSION = 0
        sickbeard.WEB_USERNAME = web_username
        sickbeard.WEB_PASSWORD = web_password

        sickbeard.FILTER_ROW = config.checkbox_to_value(filter_row)
        sickbeard.FUZZY_DATING = config.checkbox_to_value(fuzzy_dating)
        sickbeard.TRIM_ZERO = config.checkbox_to_value(trim_zero)

        if date_preset:
            sickbeard.DATE_PRESET = date_preset
            discarded_na_data = date_preset_na

        if indexer_default:
            sickbeard.INDEXER_DEFAULT = config.to_int(indexer_default)

        if indexer_timeout:
            sickbeard.INDEXER_TIMEOUT = config.to_int(indexer_timeout)

        if time_preset:
            sickbeard.TIME_PRESET_W_SECONDS = time_preset
            sickbeard.TIME_PRESET = sickbeard.TIME_PRESET_W_SECONDS.replace(u":%S", u"")

        sickbeard.TIMEZONE_DISPLAY = timezone_display

        if not config.change_LOG_DIR(log_dir, web_log):
            results += ["Unable to create directory " + os.path.normpath(log_dir) + ", log directory not changed."]

        sickbeard.API_KEY = api_key

        sickbeard.ENABLE_HTTPS = config.checkbox_to_value(enable_https)

        if not config.change_HTTPS_CERT(https_cert):
            results += [
                "Unable to create directory " + os.path.normpath(https_cert) + ", https cert directory not changed."]

        if not config.change_HTTPS_KEY(https_key):
            results += [
                "Unable to create directory " + os.path.normpath(https_key) + ", https key directory not changed."]

        sickbeard.HANDLE_REVERSE_PROXY = config.checkbox_to_value(handle_reverse_proxy)

        sickbeard.THEME_NAME = theme_name

        sickbeard.DEFAULT_PAGE = default_page

        sickbeard.save_config()

        if len(results) > 0:
            for x in results:
                logger.log(x, logger.ERROR)
            ui.notifications.error('Error(s) Saving Configuration',
                                   '<br />\n'.join(results))
        else:
            ui.notifications.message('Configuration Saved', ek(os.path.join, sickbeard.CONFIG_FILE))

        return self.redirect("/config/general/")


@route('/config/backuprestore(/?.*)')
class ConfigBackupRestore(Config):
    def __init__(self, *args, **kwargs):
        super(ConfigBackupRestore, self).__init__(*args, **kwargs)

    def index(self):
        t = PageTemplate(rh=self, file="config_backuprestore.mako")

        return t.render(submenu=self.ConfigMenu(), title='Config - Backup/Restore', header='Backup/Restore', topmenu='config')

    def backup(self, backupDir=None):

        finalResult = ''

        if backupDir:
            source = [os.path.join(sickbeard.DATA_DIR, 'sickbeard.db'), sickbeard.CONFIG_FILE]
            source.append(os.path.join(sickbeard.DATA_DIR, 'failed.db'))
            source.append(os.path.join(sickbeard.DATA_DIR, 'cache.db'))
            target = os.path.join(backupDir, 'sickrage-' + time.strftime('%Y%m%d%H%M%S') + '.zip')

            for (path, dirs, files) in os.walk(sickbeard.CACHE_DIR, topdown=True):
                for dirname in dirs:
                    if path == sickbeard.CACHE_DIR and dirname not in ['images']:
                        dirs.remove(dirname)
                for filename in files:
                    source.append(os.path.join(path, filename))

            if helpers.backupConfigZip(source, target, sickbeard.DATA_DIR):
                finalResult += "Successful backup to " + target
            else:
                finalResult += "Backup FAILED"
        else:
            finalResult += "You need to choose a folder to save your backup to!"

        finalResult += "<br />\n"

        return finalResult


    def restore(self, backupFile=None):

        finalResult = ''

        if backupFile:
            source = backupFile
            target_dir = os.path.join(sickbeard.DATA_DIR, 'restore')

            if helpers.restoreConfigZip(source, target_dir):
                finalResult += "Successfully extracted restore files to " + target_dir
                finalResult += "<br>Restart sickrage to complete the restore."
            else:
                finalResult += "Restore FAILED"
        else:
            finalResult += "You need to select a backup file to restore!"

        finalResult += "<br />\n"

        return finalResult


@route('/config/search(/?.*)')
class ConfigSearch(Config):
    def __init__(self, *args, **kwargs):
        super(ConfigSearch, self).__init__(*args, **kwargs)

    def index(self):
        t = PageTemplate(rh=self, file="config_search.mako")

        return t.render(submenu=self.ConfigMenu(), title='Config - Episode Search', header='Search Settings', topmenu='config')

    def saveSearch(self, use_nzbs=None, use_torrents=None, nzb_dir=None, sab_username=None, sab_password=None,
                   sab_apikey=None, sab_category=None, sab_category_anime=None, sab_host=None, nzbget_username=None,
                   nzbget_password=None, nzbget_category=None, nzbget_category_anime=None, nzbget_priority=None,
                   nzbget_host=None, nzbget_use_https=None, backlog_frequency=None,
                   dailysearch_frequency=None, nzb_method=None, torrent_method=None, usenet_retention=None,
                   download_propers=None, check_propers_interval=None, allow_high_priority=None, sab_forced=None,
                   randomize_providers=None, use_failed_downloads=None, delete_failed=None,
                   torrent_dir=None, torrent_username=None, torrent_password=None, torrent_host=None,
                   torrent_label=None, torrent_label_anime=None, torrent_path=None, torrent_verify_cert=None,
                   torrent_seed_time=None, torrent_paused=None, torrent_high_bandwidth=None,
                   torrent_rpcurl=None, torrent_auth_type = None, ignore_words=None, require_words=None):

        results = []

        if not config.change_NZB_DIR(nzb_dir):
            results += ["Unable to create directory " + os.path.normpath(nzb_dir) + ", dir not changed."]

        if not config.change_TORRENT_DIR(torrent_dir):
            results += ["Unable to create directory " + os.path.normpath(torrent_dir) + ", dir not changed."]

        config.change_DAILYSEARCH_FREQUENCY(dailysearch_frequency)

        config.change_BACKLOG_FREQUENCY(backlog_frequency)

        sickbeard.USE_NZBS = config.checkbox_to_value(use_nzbs)
        sickbeard.USE_TORRENTS = config.checkbox_to_value(use_torrents)

        sickbeard.NZB_METHOD = nzb_method
        sickbeard.TORRENT_METHOD = torrent_method
        sickbeard.USENET_RETENTION = config.to_int(usenet_retention, default=500)

        sickbeard.IGNORE_WORDS = ignore_words if ignore_words else ""
        sickbeard.REQUIRE_WORDS = require_words if require_words else ""

        sickbeard.RANDOMIZE_PROVIDERS = config.checkbox_to_value(randomize_providers)

        config.change_DOWNLOAD_PROPERS(download_propers)

        sickbeard.CHECK_PROPERS_INTERVAL = check_propers_interval

        sickbeard.ALLOW_HIGH_PRIORITY = config.checkbox_to_value(allow_high_priority)

        sickbeard.USE_FAILED_DOWNLOADS = config.checkbox_to_value(use_failed_downloads)
        sickbeard.DELETE_FAILED = config.checkbox_to_value(delete_failed)

        sickbeard.SAB_USERNAME = sab_username
        sickbeard.SAB_PASSWORD = sab_password
        sickbeard.SAB_APIKEY = sab_apikey.strip()
        sickbeard.SAB_CATEGORY = sab_category
        sickbeard.SAB_CATEGORY_ANIME = sab_category_anime
        sickbeard.SAB_HOST = config.clean_url(sab_host)
        sickbeard.SAB_FORCED = config.checkbox_to_value(sab_forced)

        sickbeard.NZBGET_USERNAME = nzbget_username
        sickbeard.NZBGET_PASSWORD = nzbget_password
        sickbeard.NZBGET_CATEGORY = nzbget_category
        sickbeard.NZBGET_CATEGORY_ANIME = nzbget_category_anime
        sickbeard.NZBGET_HOST = config.clean_host(nzbget_host)
        sickbeard.NZBGET_USE_HTTPS = config.checkbox_to_value(nzbget_use_https)
        sickbeard.NZBGET_PRIORITY = config.to_int(nzbget_priority, default=100)

        sickbeard.TORRENT_USERNAME = torrent_username
        sickbeard.TORRENT_PASSWORD = torrent_password
        sickbeard.TORRENT_LABEL = torrent_label
        sickbeard.TORRENT_LABEL_ANIME = torrent_label_anime
        sickbeard.TORRENT_VERIFY_CERT = config.checkbox_to_value(torrent_verify_cert)
        sickbeard.TORRENT_PATH = torrent_path.rstrip('/\\')
        sickbeard.TORRENT_SEED_TIME = torrent_seed_time
        sickbeard.TORRENT_PAUSED = config.checkbox_to_value(torrent_paused)
        sickbeard.TORRENT_HIGH_BANDWIDTH = config.checkbox_to_value(torrent_high_bandwidth)
        sickbeard.TORRENT_HOST = config.clean_url(torrent_host)
        sickbeard.TORRENT_RPCURL = torrent_rpcurl
        sickbeard.TORRENT_AUTH_TYPE = torrent_auth_type

        sickbeard.save_config()

        if len(results) > 0:
            for x in results:
                logger.log(x, logger.ERROR)
            ui.notifications.error('Error(s) Saving Configuration',
                                   '<br />\n'.join(results))
        else:
            ui.notifications.message('Configuration Saved', ek(os.path.join, sickbeard.CONFIG_FILE))

        return self.redirect("/config/search/")


@route('/config/postProcessing(/?.*)')
class ConfigPostProcessing(Config):
    def __init__(self, *args, **kwargs):
        super(ConfigPostProcessing, self).__init__(*args, **kwargs)

    def index(self):
        t = PageTemplate(rh=self, file="config_postProcessing.mako")

        return t.render(submenu=self.ConfigMenu(), title='Config - Post Processing', header='Post Processing', topmenu='config')

    def savePostProcessing(self, naming_pattern=None, naming_multi_ep=None,
                           kodi_data=None, kodi_12plus_data=None, mediabrowser_data=None, sony_ps3_data=None,
                           wdtv_data=None, tivo_data=None, mede8er_data=None,
                           keep_processed_dir=None, process_method=None, del_rar_contents=None, process_automatically=None,
                           no_delete=None, rename_episodes=None, airdate_episodes=None, unpack=None,
                           move_associated_files=None, sync_files=None, postpone_if_sync_files=None, nfo_rename=None,
                           tv_download_dir=None, naming_custom_abd=None,
                           naming_anime=None,create_missing_show_dirs=None,add_shows_wo_dir=None,
                           naming_abd_pattern=None, naming_strip_year=None, use_failed_downloads=None,
                           delete_failed=None, extra_scripts=None,
                           naming_custom_sports=None, naming_sports_pattern=None,
                           naming_custom_anime=None, naming_anime_pattern=None, naming_anime_multi_ep=None,
                           autopostprocesser_frequency=None):

        results = []

        if not config.change_TV_DOWNLOAD_DIR(tv_download_dir):
            results += ["Unable to create directory " + os.path.normpath(tv_download_dir) + ", dir not changed."]

        config.change_AUTOPOSTPROCESSER_FREQUENCY(autopostprocesser_frequency)
        config.change_PROCESS_AUTOMATICALLY(process_automatically)

        if unpack:
            if self.isRarSupported() != 'not supported':
                sickbeard.UNPACK = config.checkbox_to_value(unpack)
            else:
                sickbeard.UNPACK = 0
                results.append("Unpacking Not Supported, disabling unpack setting")
        else:
            sickbeard.UNPACK = config.checkbox_to_value(unpack)
        sickbeard.NO_DELETE = config.checkbox_to_value(no_delete)
        sickbeard.KEEP_PROCESSED_DIR = config.checkbox_to_value(keep_processed_dir)
        sickbeard.CREATE_MISSING_SHOW_DIRS = config.checkbox_to_value(create_missing_show_dirs)
        sickbeard.ADD_SHOWS_WO_DIR = config.checkbox_to_value(add_shows_wo_dir)
        sickbeard.PROCESS_METHOD = process_method
        sickbeard.DELRARCONTENTS = config.checkbox_to_value(del_rar_contents)
        sickbeard.EXTRA_SCRIPTS = [x.strip() for x in extra_scripts.split('|') if x.strip()]
        sickbeard.RENAME_EPISODES = config.checkbox_to_value(rename_episodes)
        sickbeard.AIRDATE_EPISODES = config.checkbox_to_value(airdate_episodes)
        sickbeard.MOVE_ASSOCIATED_FILES = config.checkbox_to_value(move_associated_files)
        sickbeard.SYNC_FILES = sync_files
        sickbeard.POSTPONE_IF_SYNC_FILES = config.checkbox_to_value(postpone_if_sync_files)
        sickbeard.NAMING_CUSTOM_ABD = config.checkbox_to_value(naming_custom_abd)
        sickbeard.NAMING_CUSTOM_SPORTS = config.checkbox_to_value(naming_custom_sports)
        sickbeard.NAMING_CUSTOM_ANIME = config.checkbox_to_value(naming_custom_anime)
        sickbeard.NAMING_STRIP_YEAR = config.checkbox_to_value(naming_strip_year)
        sickbeard.USE_FAILED_DOWNLOADS = config.checkbox_to_value(use_failed_downloads)
        sickbeard.DELETE_FAILED = config.checkbox_to_value(delete_failed)
        sickbeard.NFO_RENAME = config.checkbox_to_value(nfo_rename)

        sickbeard.METADATA_KODI = kodi_data
        sickbeard.METADATA_KODI_12PLUS = kodi_12plus_data
        sickbeard.METADATA_MEDIABROWSER = mediabrowser_data
        sickbeard.METADATA_PS3 = sony_ps3_data
        sickbeard.METADATA_WDTV = wdtv_data
        sickbeard.METADATA_TIVO = tivo_data
        sickbeard.METADATA_MEDE8ER = mede8er_data

        sickbeard.metadata_provider_dict['KODI'].set_config(sickbeard.METADATA_KODI)
        sickbeard.metadata_provider_dict['KODI 12+'].set_config(sickbeard.METADATA_KODI_12PLUS)
        sickbeard.metadata_provider_dict['MediaBrowser'].set_config(sickbeard.METADATA_MEDIABROWSER)
        sickbeard.metadata_provider_dict['Sony PS3'].set_config(sickbeard.METADATA_PS3)
        sickbeard.metadata_provider_dict['WDTV'].set_config(sickbeard.METADATA_WDTV)
        sickbeard.metadata_provider_dict['TIVO'].set_config(sickbeard.METADATA_TIVO)
        sickbeard.metadata_provider_dict['Mede8er'].set_config(sickbeard.METADATA_MEDE8ER)

        if self.isNamingValid(naming_pattern, naming_multi_ep, anime_type=naming_anime) != "invalid":
            sickbeard.NAMING_PATTERN = naming_pattern
            sickbeard.NAMING_MULTI_EP = int(naming_multi_ep)
            sickbeard.NAMING_ANIME = int(naming_anime)
            sickbeard.NAMING_FORCE_FOLDERS = naming.check_force_season_folders()
        else:
            if int(naming_anime) in [1, 2]:
                results.append("You tried saving an invalid anime naming config, not saving your naming settings")
            else:
                results.append("You tried saving an invalid naming config, not saving your naming settings")

        if self.isNamingValid(naming_anime_pattern, naming_anime_multi_ep, anime_type=naming_anime) != "invalid":
            sickbeard.NAMING_ANIME_PATTERN = naming_anime_pattern
            sickbeard.NAMING_ANIME_MULTI_EP = int(naming_anime_multi_ep)
            sickbeard.NAMING_ANIME = int(naming_anime)
            sickbeard.NAMING_FORCE_FOLDERS = naming.check_force_season_folders()
        else:
            if int(naming_anime) in [1, 2]:
                results.append("You tried saving an invalid anime naming config, not saving your naming settings")
            else:
                results.append("You tried saving an invalid naming config, not saving your naming settings")

        if self.isNamingValid(naming_abd_pattern, None, abd=True) != "invalid":
            sickbeard.NAMING_ABD_PATTERN = naming_abd_pattern
        else:
            results.append(
                "You tried saving an invalid air-by-date naming config, not saving your air-by-date settings")

        if self.isNamingValid(naming_sports_pattern, None, sports=True) != "invalid":
            sickbeard.NAMING_SPORTS_PATTERN = naming_sports_pattern
        else:
            results.append(
                "You tried saving an invalid sports naming config, not saving your sports settings")

        sickbeard.save_config()

        if len(results) > 0:
            for x in results:
                logger.log(x, logger.ERROR)
            ui.notifications.error('Error(s) Saving Configuration',
                                   '<br />\n'.join(results))
        else:
            ui.notifications.message('Configuration Saved', ek(os.path.join, sickbeard.CONFIG_FILE))

        return self.redirect("/config/postProcessing/")

    def testNaming(self, pattern=None, multi=None, abd=False, sports=False, anime_type=None):

        if multi is not None:
            multi = int(multi)

        if anime_type is not None:
            anime_type = int(anime_type)

        result = naming.test_name(pattern, multi, abd, sports, anime_type)

        result = ek(os.path.join, result['dir'], result['name'])

        return result


    def isNamingValid(self, pattern=None, multi=None, abd=False, sports=False, anime_type=None):
        if pattern is None:
            return "invalid"

        if multi is not None:
            multi = int(multi)

        if anime_type is not None:
            anime_type = int(anime_type)

        # air by date shows just need one check, we don't need to worry about season folders
        if abd:
            is_valid = naming.check_valid_abd_naming(pattern)
            require_season_folders = False

        # sport shows just need one check, we don't need to worry about season folders
        elif sports:
            is_valid = naming.check_valid_sports_naming(pattern)
            require_season_folders = False

        else:
            # check validity of single and multi ep cases for the whole path
            is_valid = naming.check_valid_naming(pattern, multi, anime_type)

            # check validity of single and multi ep cases for only the file name
            require_season_folders = naming.check_force_season_folders(pattern, multi, anime_type)

        if is_valid and not require_season_folders:
            return "valid"
        elif is_valid and require_season_folders:
            return "seasonfolders"
        else:
            return "invalid"


    def isRarSupported(self):
        """
        Test Packing Support:
            - Simulating in memory rar extraction on test.rar file
        """

        try:
            rar_path = os.path.join(sickbeard.PROG_DIR, 'lib', 'unrar2', 'test.rar')
            testing = RarFile(rar_path).read_files('*test.txt')
            if testing[0][1] == 'This is only a test.':
                return 'supported'
            logger.log(u'Rar Not Supported: Can not read the content of test file', logger.ERROR)
            return 'not supported'
        except Exception, e:
            logger.log(u'Rar Not Supported: ' + ex(e), logger.ERROR)
            return 'not supported'


@route('/config/providers(/?.*)')
class ConfigProviders(Config):
    def __init__(self, *args, **kwargs):
        super(ConfigProviders, self).__init__(*args, **kwargs)

    def index(self):
        t = PageTemplate(rh=self, file="config_providers.mako")

        return t.render(submenu=self.ConfigMenu(), title='Config - Providers', header='Search Providers', topmenu='config')

    def canAddNewznabProvider(self, name):

        if not name:
            return json.dumps({'error': 'No Provider Name specified'})

        providerDict = dict(zip([x.getID() for x in sickbeard.newznabProviderList], sickbeard.newznabProviderList))

        tempProvider = newznab.NewznabProvider(name, '')

        if tempProvider.getID() in providerDict:
            return json.dumps({'error': 'Provider Name already exists as ' + providerDict[tempProvider.getID()].name})
        else:
            return json.dumps({'success': tempProvider.getID()})

    def saveNewznabProvider(self, name, url, key=''):

        if not name or not url:
            return '0'

        providerDict = dict(zip([x.name for x in sickbeard.newznabProviderList], sickbeard.newznabProviderList))

        if name in providerDict:
            if not providerDict[name].default:
                providerDict[name].name = name
                providerDict[name].url = config.clean_url(url)

            providerDict[name].key = key
            # a 0 in the key spot indicates that no key is needed
            if key == '0':
                providerDict[name].needs_auth = False
            else:
                providerDict[name].needs_auth = True

            return providerDict[name].getID() + '|' + providerDict[name].configStr()

        else:
            newProvider = newznab.NewznabProvider(name, url, key=key)
            sickbeard.newznabProviderList.append(newProvider)
            return newProvider.getID() + '|' + newProvider.configStr()

    def getNewznabCategories(self, name, url, key):
        '''
        Retrieves a list of possible categories with category id's
        Using the default url/api?cat
        http://yournewznaburl.com/api?t=caps&apikey=yourapikey
        '''
        error = ""
        success = False

        if not name:
            error += "\nNo Provider Name specified"
        if not url:
            error += "\nNo Provider Url specified"
        if not key:
            error += "\nNo Provider Api key specified"

        if error <> "":
            return json.dumps({'success': False, 'error': error})

        # Get list with Newznabproviders
        # providerDict = dict(zip([x.getID() for x in sickbeard.newznabProviderList], sickbeard.newznabProviderList))

        # Get newznabprovider obj with provided name
        tempProvider = newznab.NewznabProvider(name, url, key)

        success, tv_categories, error = tempProvider.get_newznab_categories()

        return json.dumps({'success': success, 'tv_categories': tv_categories, 'error': error})

    def deleteNewznabProvider(self, nnid):

        providerDict = dict(zip([x.getID() for x in sickbeard.newznabProviderList], sickbeard.newznabProviderList))

        if nnid not in providerDict or providerDict[nnid].default:
            return '0'

        # delete it from the list
        sickbeard.newznabProviderList.remove(providerDict[nnid])

        if nnid in sickbeard.PROVIDER_ORDER:
            sickbeard.PROVIDER_ORDER.remove(nnid)

        return '1'


    def canAddTorrentRssProvider(self, name, url, cookies, titleTAG):

        if not name:
            return json.dumps({'error': 'Invalid name specified'})

        providerDict = dict(
            zip([x.getID() for x in sickbeard.torrentRssProviderList], sickbeard.torrentRssProviderList))

        tempProvider = rsstorrent.TorrentRssProvider(name, url, cookies, titleTAG)

        if tempProvider.getID() in providerDict:
            return json.dumps({'error': 'Exists as ' + providerDict[tempProvider.getID()].name})
        else:
            (succ, errMsg) = tempProvider.validateRSS()
            if succ:
                return json.dumps({'success': tempProvider.getID()})
            else:
                return json.dumps({'error': errMsg})


    def saveTorrentRssProvider(self, name, url, cookies, titleTAG):

        if not name or not url:
            return '0'

        providerDict = dict(zip([x.name for x in sickbeard.torrentRssProviderList], sickbeard.torrentRssProviderList))

        if name in providerDict:
            providerDict[name].name = name
            providerDict[name].url = config.clean_url(url)
            providerDict[name].cookies = cookies
            providerDict[name].titleTAG = titleTAG

            return providerDict[name].getID() + '|' + providerDict[name].configStr()

        else:
            newProvider = rsstorrent.TorrentRssProvider(name, url, cookies, titleTAG)
            sickbeard.torrentRssProviderList.append(newProvider)
            return newProvider.getID() + '|' + newProvider.configStr()


    def deleteTorrentRssProvider(self, id):

        providerDict = dict(
            zip([x.getID() for x in sickbeard.torrentRssProviderList], sickbeard.torrentRssProviderList))

        if id not in providerDict:
            return '0'

        # delete it from the list
        sickbeard.torrentRssProviderList.remove(providerDict[id])

        if id in sickbeard.PROVIDER_ORDER:
            sickbeard.PROVIDER_ORDER.remove(id)

        return '1'


    def saveProviders(self, newznab_string='', torrentrss_string='', provider_order=None, **kwargs):

        results = []

        provider_str_list = provider_order.split()
        provider_list = []

        newznabProviderDict = dict(
            zip([x.getID() for x in sickbeard.newznabProviderList], sickbeard.newznabProviderList))

        finishedNames = []

        # add all the newznab info we got into our list
        if newznab_string:
            for curNewznabProviderStr in newznab_string.split('!!!'):

                if not curNewznabProviderStr:
                    continue

                cur_name, cur_url, cur_key, cur_cat = curNewznabProviderStr.split('|')
                cur_url = config.clean_url(cur_url)

                newProvider = newznab.NewznabProvider(cur_name, cur_url, key=cur_key)

                cur_id = newProvider.getID()

                # if it already exists then update it
                if cur_id in newznabProviderDict:
                    newznabProviderDict[cur_id].name = cur_name
                    newznabProviderDict[cur_id].url = cur_url
                    newznabProviderDict[cur_id].key = cur_key
                    newznabProviderDict[cur_id].catIDs = cur_cat
                    # a 0 in the key spot indicates that no key is needed
                    if cur_key == '0':
                        newznabProviderDict[cur_id].needs_auth = False
                    else:
                        newznabProviderDict[cur_id].needs_auth = True

                    try:
                        newznabProviderDict[cur_id].search_mode = str(kwargs[cur_id + '_search_mode']).strip()
                    except:
                        pass

                    try:
                        newznabProviderDict[cur_id].search_fallback = config.checkbox_to_value(
                            kwargs[cur_id + '_search_fallback'])
                    except:
                        newznabProviderDict[cur_id].search_fallback = 0

                    try:
                        newznabProviderDict[cur_id].enable_daily = config.checkbox_to_value(
                            kwargs[cur_id + '_enable_daily'])
                    except:
                        newznabProviderDict[cur_id].enable_daily = 0

                    try:
                        newznabProviderDict[cur_id].enable_backlog = config.checkbox_to_value(
                            kwargs[cur_id + '_enable_backlog'])
                    except:
                        newznabProviderDict[cur_id].enable_backlog = 0
                else:
                    sickbeard.newznabProviderList.append(newProvider)

                finishedNames.append(cur_id)

        # delete anything that is missing
        for curProvider in sickbeard.newznabProviderList:
            if curProvider.getID() not in finishedNames:
                sickbeard.newznabProviderList.remove(curProvider)

        torrentRssProviderDict = dict(
            zip([x.getID() for x in sickbeard.torrentRssProviderList], sickbeard.torrentRssProviderList))
        finishedNames = []

        if torrentrss_string:
            for curTorrentRssProviderStr in torrentrss_string.split('!!!'):

                if not curTorrentRssProviderStr:
                    continue

                curName, curURL, curCookies, curTitleTAG = curTorrentRssProviderStr.split('|')
                curURL = config.clean_url(curURL)

                newProvider = rsstorrent.TorrentRssProvider(curName, curURL, curCookies, curTitleTAG)

                curID = newProvider.getID()

                # if it already exists then update it
                if curID in torrentRssProviderDict:
                    torrentRssProviderDict[curID].name = curName
                    torrentRssProviderDict[curID].url = curURL
                    torrentRssProviderDict[curID].cookies = curCookies
                    torrentRssProviderDict[curID].curTitleTAG = curTitleTAG
                else:
                    sickbeard.torrentRssProviderList.append(newProvider)

                finishedNames.append(curID)

        # delete anything that is missing
        for curProvider in sickbeard.torrentRssProviderList:
            if curProvider.getID() not in finishedNames:
                sickbeard.torrentRssProviderList.remove(curProvider)

        disabled_list = []
        # do the enable/disable
        for curProviderStr in provider_str_list:
            curProvider, curEnabled = curProviderStr.split(':')
            curEnabled = config.to_int(curEnabled)

            curProvObj = [x for x in sickbeard.providers.sortedProviderList() if
                          x.getID() == curProvider and hasattr(x, 'enabled')]
            if curProvObj:
                curProvObj[0].enabled = bool(curEnabled)

            if curEnabled:
                provider_list.append(curProvider)
            else:
                disabled_list.append(curProvider)

            if curProvider in newznabProviderDict:
                newznabProviderDict[curProvider].enabled = bool(curEnabled)
            elif curProvider in torrentRssProviderDict:
                torrentRssProviderDict[curProvider].enabled = bool(curEnabled)

        provider_list = provider_list + disabled_list

        # dynamically load provider settings
        for curTorrentProvider in [curProvider for curProvider in sickbeard.providers.sortedProviderList() if
                                   curProvider.providerType == sickbeard.GenericProvider.TORRENT]:

            if hasattr(curTorrentProvider, 'minseed'):
                try:
                    curTorrentProvider.minseed = int(str(kwargs[curTorrentProvider.getID() + '_minseed']).strip())
                except:
                    curTorrentProvider.minseed = 0

            if hasattr(curTorrentProvider, 'minleech'):
                try:
                    curTorrentProvider.minleech = int(str(kwargs[curTorrentProvider.getID() + '_minleech']).strip())
                except:
                    curTorrentProvider.minleech = 0

            if hasattr(curTorrentProvider, 'ratio'):
                try:
                    curTorrentProvider.ratio = str(kwargs[curTorrentProvider.getID() + '_ratio']).strip()
                except:
                    curTorrentProvider.ratio = None

            if hasattr(curTorrentProvider, 'digest'):
                try:
                    curTorrentProvider.digest = str(kwargs[curTorrentProvider.getID() + '_digest']).strip()
                except:
                    curTorrentProvider.digest = None

            if hasattr(curTorrentProvider, 'hash'):
                try:
                    curTorrentProvider.hash = str(kwargs[curTorrentProvider.getID() + '_hash']).strip()
                except:
                    curTorrentProvider.hash = None

            if hasattr(curTorrentProvider, 'api_key'):
                try:
                    curTorrentProvider.api_key = str(kwargs[curTorrentProvider.getID() + '_api_key']).strip()
                except:
                    curTorrentProvider.api_key = None

            if hasattr(curTorrentProvider, 'username'):
                try:
                    curTorrentProvider.username = str(kwargs[curTorrentProvider.getID() + '_username']).strip()
                except:
                    curTorrentProvider.username = None

            if hasattr(curTorrentProvider, 'password'):
                try:
                    curTorrentProvider.password = str(kwargs[curTorrentProvider.getID() + '_password']).strip()
                except:
                    curTorrentProvider.password = None

            if hasattr(curTorrentProvider, 'passkey'):
                try:
                    curTorrentProvider.passkey = str(kwargs[curTorrentProvider.getID() + '_passkey']).strip()
                except:
                    curTorrentProvider.passkey = None

            if hasattr(curTorrentProvider, 'confirmed'):
                try:
                    curTorrentProvider.confirmed = config.checkbox_to_value(
                        kwargs[curTorrentProvider.getID() + '_confirmed'])
                except:
                    curTorrentProvider.confirmed = 0

            if hasattr(curTorrentProvider, 'ranked'):
                try:
                    curTorrentProvider.ranked = config.checkbox_to_value(
                        kwargs[curTorrentProvider.getID() + '_ranked'])
                except:
                    curTorrentProvider.ranked = 0

            if hasattr(curTorrentProvider, 'sorting'):
                try:
                    curTorrentProvider.sorting = str(kwargs[curTorrentProvider.getID() + '_sorting']).strip()
                except:
                     curTorrentProvider.sorting = 'seeders'

            if hasattr(curTorrentProvider, 'proxy'):
                try:
                    curTorrentProvider.proxy.enabled = config.checkbox_to_value(
                        kwargs[curTorrentProvider.getID() + '_proxy'])
                except:
                    curTorrentProvider.proxy.enabled = 0

                if hasattr(curTorrentProvider.proxy, 'url'):
                    try:
                        curTorrentProvider.proxy.url = str(kwargs[curTorrentProvider.getID() + '_proxy_url']).strip()
                    except:
                        curTorrentProvider.proxy.url = None

            if hasattr(curTorrentProvider, 'freeleech'):
                try:
                    curTorrentProvider.freeleech = config.checkbox_to_value(
                        kwargs[curTorrentProvider.getID() + '_freeleech'])
                except:
                    curTorrentProvider.freeleech = 0

            if hasattr(curTorrentProvider, 'search_mode'):
                try:
                    curTorrentProvider.search_mode = str(kwargs[curTorrentProvider.getID() + '_search_mode']).strip()
                except:
                    curTorrentProvider.search_mode = 'eponly'

            if hasattr(curTorrentProvider, 'search_fallback'):
                try:
                    curTorrentProvider.search_fallback = config.checkbox_to_value(
                        kwargs[curTorrentProvider.getID() + '_search_fallback'])
                except:
                    curTorrentProvider.search_fallback = 0  # these exceptions are catching unselected checkboxes

            if hasattr(curTorrentProvider, 'enable_daily'):
                try:
                    curTorrentProvider.enable_daily = config.checkbox_to_value(
                        kwargs[curTorrentProvider.getID() + '_enable_daily'])
                except:
                    curTorrentProvider.enable_daily = 0  # these exceptions are actually catching unselected checkboxes

            if hasattr(curTorrentProvider, 'enable_backlog'):
                try:
                    curTorrentProvider.enable_backlog = config.checkbox_to_value(
                        kwargs[curTorrentProvider.getID() + '_enable_backlog'])
                except:
                    curTorrentProvider.enable_backlog = 0  # these exceptions are actually catching unselected checkboxes

            if hasattr(curTorrentProvider, 'cat'):
                try:
                    curTorrentProvider.cat = int(str(kwargs[curTorrentProvider.getID() + '_cat']).strip())
                except:
                    curTorrentProvider.cat = 0

            if hasattr(curTorrentProvider, 'subtitle'):
                try:
                    curTorrentProvider.subtitle = config.checkbox_to_value(
                        kwargs[curTorrentProvider.getID() + '_subtitle'])
                except:
                    curTorrentProvider.subtitle = 0

        for curNzbProvider in [curProvider for curProvider in sickbeard.providers.sortedProviderList() if
                               curProvider.providerType == sickbeard.GenericProvider.NZB]:

            if hasattr(curNzbProvider, 'api_key'):
                try:
                    curNzbProvider.api_key = str(kwargs[curNzbProvider.getID() + '_api_key']).strip()
                except:
                    curNzbProvider.api_key = None

            if hasattr(curNzbProvider, 'username'):
                try:
                    curNzbProvider.username = str(kwargs[curNzbProvider.getID() + '_username']).strip()
                except:
                    curNzbProvider.username = None

            if hasattr(curNzbProvider, 'search_mode'):
                try:
                    curNzbProvider.search_mode = str(kwargs[curNzbProvider.getID() + '_search_mode']).strip()
                except:
                    curNzbProvider.search_mode = 'eponly'

            if hasattr(curNzbProvider, 'search_fallback'):
                try:
                    curNzbProvider.search_fallback = config.checkbox_to_value(
                        kwargs[curNzbProvider.getID() + '_search_fallback'])
                except:
                    curNzbProvider.search_fallback = 0  # these exceptions are actually catching unselected checkboxes

            if hasattr(curNzbProvider, 'enable_daily'):
                try:
                    curNzbProvider.enable_daily = config.checkbox_to_value(
                        kwargs[curNzbProvider.getID() + '_enable_daily'])
                except:
                    curNzbProvider.enable_daily = 0  # these exceptions are actually catching unselected checkboxes

            if hasattr(curNzbProvider, 'enable_backlog'):
                try:
                    curNzbProvider.enable_backlog = config.checkbox_to_value(
                        kwargs[curNzbProvider.getID() + '_enable_backlog'])
                except:
                    curNzbProvider.enable_backlog = 0  # these exceptions are actually catching unselected checkboxes

        sickbeard.NEWZNAB_DATA = '!!!'.join([x.configStr() for x in sickbeard.newznabProviderList])
        sickbeard.PROVIDER_ORDER = provider_list

        sickbeard.save_config()

        if len(results) > 0:
            for x in results:
                logger.log(x, logger.ERROR)
            ui.notifications.error('Error(s) Saving Configuration',
                                   '<br />\n'.join(results))
        else:
            ui.notifications.message('Configuration Saved', ek(os.path.join, sickbeard.CONFIG_FILE))

        return self.redirect("/config/providers/")


@route('/config/notifications(/?.*)')
class ConfigNotifications(Config):
    def __init__(self, *args, **kwargs):
        super(ConfigNotifications, self).__init__(*args, **kwargs)

    def index(self):
        t = PageTemplate(rh=self, file="config_notifications.mako")

        return t.render(submenu=self.ConfigMenu(), title='Config - Notifications', header='Notifications', topmenu='config')

    def saveNotifications(self, use_kodi=None, kodi_always_on=None, kodi_notify_onsnatch=None,
                          kodi_notify_ondownload=None,
                          kodi_notify_onsubtitledownload=None, kodi_update_onlyfirst=None,
                          kodi_update_library=None, kodi_update_full=None, kodi_host=None, kodi_username=None,
                          kodi_password=None,
                          use_plex=None, plex_notify_onsnatch=None, plex_notify_ondownload=None,
                          plex_notify_onsubtitledownload=None, plex_update_library=None,
                          plex_server_host=None, plex_server_token=None, plex_host=None, plex_username=None, plex_password=None,
                          use_plex_client=None, plex_client_username=None, plex_client_password=None,
                          use_emby=None, emby_host=None, emby_apikey=None,
                          use_growl=None, growl_notify_onsnatch=None, growl_notify_ondownload=None,
                          growl_notify_onsubtitledownload=None, growl_host=None, growl_password=None,
                          use_freemobile=None, freemobile_notify_onsnatch=None, freemobile_notify_ondownload=None,
                          freemobile_notify_onsubtitledownload=None, freemobile_id=None, freemobile_apikey=None,
                          use_prowl=None, prowl_notify_onsnatch=None, prowl_notify_ondownload=None,
                          prowl_notify_onsubtitledownload=None, prowl_api=None, prowl_priority=0,
                          use_twitter=None, twitter_notify_onsnatch=None, twitter_notify_ondownload=None,
                          twitter_notify_onsubtitledownload=None, twitter_usedm=None, twitter_dmto=None,
                          use_boxcar=None, boxcar_notify_onsnatch=None, boxcar_notify_ondownload=None,
                          boxcar_notify_onsubtitledownload=None, boxcar_username=None,
                          use_boxcar2=None, boxcar2_notify_onsnatch=None, boxcar2_notify_ondownload=None,
                          boxcar2_notify_onsubtitledownload=None, boxcar2_accesstoken=None,
                          use_pushover=None, pushover_notify_onsnatch=None, pushover_notify_ondownload=None,
                          pushover_notify_onsubtitledownload=None, pushover_userkey=None, pushover_apikey=None, pushover_device=None, pushover_sound=None,
                          use_libnotify=None, libnotify_notify_onsnatch=None, libnotify_notify_ondownload=None,
                          libnotify_notify_onsubtitledownload=None,
                          use_nmj=None, nmj_host=None, nmj_database=None, nmj_mount=None, use_synoindex=None,
                          use_nmjv2=None, nmjv2_host=None, nmjv2_dbloc=None, nmjv2_database=None,
                          use_trakt=None, trakt_username=None, trakt_pin=None,
                          trakt_remove_watchlist=None, trakt_sync_watchlist=None, trakt_remove_show_from_sickrage=None, trakt_method_add=None,
                          trakt_start_paused=None, trakt_use_recommended=None, trakt_sync=None, trakt_sync_remove=None,
                          trakt_default_indexer=None, trakt_remove_serieslist=None, trakt_timeout=None, trakt_blacklist_name=None,
                          use_synologynotifier=None, synologynotifier_notify_onsnatch=None,
                          synologynotifier_notify_ondownload=None, synologynotifier_notify_onsubtitledownload=None,
                          use_pytivo=None, pytivo_notify_onsnatch=None, pytivo_notify_ondownload=None,
                          pytivo_notify_onsubtitledownload=None, pytivo_update_library=None,
                          pytivo_host=None, pytivo_share_name=None, pytivo_tivo_name=None,
                          use_nma=None, nma_notify_onsnatch=None, nma_notify_ondownload=None,
                          nma_notify_onsubtitledownload=None, nma_api=None, nma_priority=0,
                          use_pushalot=None, pushalot_notify_onsnatch=None, pushalot_notify_ondownload=None,
                          pushalot_notify_onsubtitledownload=None, pushalot_authorizationtoken=None,
                          use_pushbullet=None, pushbullet_notify_onsnatch=None, pushbullet_notify_ondownload=None,
                          pushbullet_notify_onsubtitledownload=None, pushbullet_api=None, pushbullet_device=None,
                          pushbullet_device_list=None,
                          use_email=None, email_notify_onsnatch=None, email_notify_ondownload=None,
                          email_notify_onsubtitledownload=None, email_host=None, email_port=25, email_from=None,
                          email_tls=None, email_user=None, email_password=None, email_list=None, email_show_list=None,
                          email_show=None):

        results = []

        sickbeard.USE_KODI = config.checkbox_to_value(use_kodi)
        sickbeard.KODI_ALWAYS_ON = config.checkbox_to_value(kodi_always_on)
        sickbeard.KODI_NOTIFY_ONSNATCH = config.checkbox_to_value(kodi_notify_onsnatch)
        sickbeard.KODI_NOTIFY_ONDOWNLOAD = config.checkbox_to_value(kodi_notify_ondownload)
        sickbeard.KODI_NOTIFY_ONSUBTITLEDOWNLOAD = config.checkbox_to_value(kodi_notify_onsubtitledownload)
        sickbeard.KODI_UPDATE_LIBRARY = config.checkbox_to_value(kodi_update_library)
        sickbeard.KODI_UPDATE_FULL = config.checkbox_to_value(kodi_update_full)
        sickbeard.KODI_UPDATE_ONLYFIRST = config.checkbox_to_value(kodi_update_onlyfirst)
        sickbeard.KODI_HOST = config.clean_hosts(kodi_host)
        sickbeard.KODI_USERNAME = kodi_username
        sickbeard.KODI_PASSWORD = kodi_password

        sickbeard.USE_PLEX = config.checkbox_to_value(use_plex)
        sickbeard.PLEX_NOTIFY_ONSNATCH = config.checkbox_to_value(plex_notify_onsnatch)
        sickbeard.PLEX_NOTIFY_ONDOWNLOAD = config.checkbox_to_value(plex_notify_ondownload)
        sickbeard.PLEX_NOTIFY_ONSUBTITLEDOWNLOAD = config.checkbox_to_value(plex_notify_onsubtitledownload)
        sickbeard.PLEX_UPDATE_LIBRARY = config.checkbox_to_value(plex_update_library)
        sickbeard.PLEX_HOST = config.clean_hosts(plex_host)
        sickbeard.PLEX_SERVER_HOST = config.clean_host(plex_server_host)
        sickbeard.PLEX_SERVER_TOKEN = config.clean_host(plex_server_token)
        sickbeard.PLEX_USERNAME = plex_username
        sickbeard.PLEX_PASSWORD = plex_password
        sickbeard.USE_PLEX_CLIENT = config.checkbox_to_value(use_plex)
        sickbeard.PLEX_CLIENT_USERNAME = plex_username
        sickbeard.PLEX_CLIENT_PASSWORD = plex_password

        sickbeard.USE_EMBY = config.checkbox_to_value(use_emby)
        sickbeard.EMBY_HOST = config.clean_host(emby_host)
        sickbeard.EMBY_APIKEY = emby_apikey

        sickbeard.USE_GROWL = config.checkbox_to_value(use_growl)
        sickbeard.GROWL_NOTIFY_ONSNATCH = config.checkbox_to_value(growl_notify_onsnatch)
        sickbeard.GROWL_NOTIFY_ONDOWNLOAD = config.checkbox_to_value(growl_notify_ondownload)
        sickbeard.GROWL_NOTIFY_ONSUBTITLEDOWNLOAD = config.checkbox_to_value(growl_notify_onsubtitledownload)
        sickbeard.GROWL_HOST = config.clean_host(growl_host, default_port=23053)
        sickbeard.GROWL_PASSWORD = growl_password

        sickbeard.USE_FREEMOBILE = config.checkbox_to_value(use_freemobile)
        sickbeard.FREEMOBILE_NOTIFY_ONSNATCH = config.checkbox_to_value(freemobile_notify_onsnatch)
        sickbeard.FREEMOBILE_NOTIFY_ONDOWNLOAD = config.checkbox_to_value(freemobile_notify_ondownload)
        sickbeard.FREEMOBILE_NOTIFY_ONSUBTITLEDOWNLOAD = config.checkbox_to_value(freemobile_notify_onsubtitledownload)
        sickbeard.FREEMOBILE_ID = freemobile_id
        sickbeard.FREEMOBILE_APIKEY = freemobile_apikey

        sickbeard.USE_PROWL = config.checkbox_to_value(use_prowl)
        sickbeard.PROWL_NOTIFY_ONSNATCH = config.checkbox_to_value(prowl_notify_onsnatch)
        sickbeard.PROWL_NOTIFY_ONDOWNLOAD = config.checkbox_to_value(prowl_notify_ondownload)
        sickbeard.PROWL_NOTIFY_ONSUBTITLEDOWNLOAD = config.checkbox_to_value(prowl_notify_onsubtitledownload)
        sickbeard.PROWL_API = prowl_api
        sickbeard.PROWL_PRIORITY = prowl_priority

        sickbeard.USE_TWITTER = config.checkbox_to_value(use_twitter)
        sickbeard.TWITTER_NOTIFY_ONSNATCH = config.checkbox_to_value(twitter_notify_onsnatch)
        sickbeard.TWITTER_NOTIFY_ONDOWNLOAD = config.checkbox_to_value(twitter_notify_ondownload)
        sickbeard.TWITTER_NOTIFY_ONSUBTITLEDOWNLOAD = config.checkbox_to_value(twitter_notify_onsubtitledownload)
        sickbeard.TWITTER_USEDM = config.checkbox_to_value(twitter_usedm)
        sickbeard.TWITTER_DMTO = twitter_dmto

        sickbeard.USE_BOXCAR = config.checkbox_to_value(use_boxcar)
        sickbeard.BOXCAR_NOTIFY_ONSNATCH = config.checkbox_to_value(boxcar_notify_onsnatch)
        sickbeard.BOXCAR_NOTIFY_ONDOWNLOAD = config.checkbox_to_value(boxcar_notify_ondownload)
        sickbeard.BOXCAR_NOTIFY_ONSUBTITLEDOWNLOAD = config.checkbox_to_value(boxcar_notify_onsubtitledownload)
        sickbeard.BOXCAR_USERNAME = boxcar_username

        sickbeard.USE_BOXCAR2 = config.checkbox_to_value(use_boxcar2)
        sickbeard.BOXCAR2_NOTIFY_ONSNATCH = config.checkbox_to_value(boxcar2_notify_onsnatch)
        sickbeard.BOXCAR2_NOTIFY_ONDOWNLOAD = config.checkbox_to_value(boxcar2_notify_ondownload)
        sickbeard.BOXCAR2_NOTIFY_ONSUBTITLEDOWNLOAD = config.checkbox_to_value(boxcar2_notify_onsubtitledownload)
        sickbeard.BOXCAR2_ACCESSTOKEN = boxcar2_accesstoken

        sickbeard.USE_PUSHOVER = config.checkbox_to_value(use_pushover)
        sickbeard.PUSHOVER_NOTIFY_ONSNATCH = config.checkbox_to_value(pushover_notify_onsnatch)
        sickbeard.PUSHOVER_NOTIFY_ONDOWNLOAD = config.checkbox_to_value(pushover_notify_ondownload)
        sickbeard.PUSHOVER_NOTIFY_ONSUBTITLEDOWNLOAD = config.checkbox_to_value(pushover_notify_onsubtitledownload)
        sickbeard.PUSHOVER_USERKEY = pushover_userkey
        sickbeard.PUSHOVER_APIKEY = pushover_apikey
        sickbeard.PUSHOVER_DEVICE = pushover_device
        sickbeard.PUSHOVER_SOUND = pushover_sound

        sickbeard.USE_LIBNOTIFY = config.checkbox_to_value(use_libnotify)
        sickbeard.LIBNOTIFY_NOTIFY_ONSNATCH = config.checkbox_to_value(libnotify_notify_onsnatch)
        sickbeard.LIBNOTIFY_NOTIFY_ONDOWNLOAD = config.checkbox_to_value(libnotify_notify_ondownload)
        sickbeard.LIBNOTIFY_NOTIFY_ONSUBTITLEDOWNLOAD = config.checkbox_to_value(libnotify_notify_onsubtitledownload)

        sickbeard.USE_NMJ = config.checkbox_to_value(use_nmj)
        sickbeard.NMJ_HOST = config.clean_host(nmj_host)
        sickbeard.NMJ_DATABASE = nmj_database
        sickbeard.NMJ_MOUNT = nmj_mount

        sickbeard.USE_NMJv2 = config.checkbox_to_value(use_nmjv2)
        sickbeard.NMJv2_HOST = config.clean_host(nmjv2_host)
        sickbeard.NMJv2_DATABASE = nmjv2_database
        sickbeard.NMJv2_DBLOC = nmjv2_dbloc

        sickbeard.USE_SYNOINDEX = config.checkbox_to_value(use_synoindex)

        sickbeard.USE_SYNOLOGYNOTIFIER = config.checkbox_to_value(use_synologynotifier)
        sickbeard.SYNOLOGYNOTIFIER_NOTIFY_ONSNATCH = config.checkbox_to_value(synologynotifier_notify_onsnatch)
        sickbeard.SYNOLOGYNOTIFIER_NOTIFY_ONDOWNLOAD = config.checkbox_to_value(synologynotifier_notify_ondownload)
        sickbeard.SYNOLOGYNOTIFIER_NOTIFY_ONSUBTITLEDOWNLOAD = config.checkbox_to_value(
            synologynotifier_notify_onsubtitledownload)

        config.change_USE_TRAKT(use_trakt)
        sickbeard.TRAKT_USERNAME = trakt_username
        sickbeard.TRAKT_REMOVE_WATCHLIST = config.checkbox_to_value(trakt_remove_watchlist)
        sickbeard.TRAKT_REMOVE_SERIESLIST = config.checkbox_to_value(trakt_remove_serieslist)
        sickbeard.TRAKT_REMOVE_SHOW_FROM_SICKRAGE = config.checkbox_to_value(trakt_remove_show_from_sickrage)
        sickbeard.TRAKT_SYNC_WATCHLIST = config.checkbox_to_value(trakt_sync_watchlist)
        sickbeard.TRAKT_METHOD_ADD = int(trakt_method_add)
        sickbeard.TRAKT_START_PAUSED = config.checkbox_to_value(trakt_start_paused)
        sickbeard.TRAKT_USE_RECOMMENDED = config.checkbox_to_value(trakt_use_recommended)
        sickbeard.TRAKT_SYNC = config.checkbox_to_value(trakt_sync)
        sickbeard.TRAKT_SYNC_REMOVE = config.checkbox_to_value(trakt_sync_remove)
        sickbeard.TRAKT_DEFAULT_INDEXER = int(trakt_default_indexer)
        sickbeard.TRAKT_TIMEOUT = int(trakt_timeout)
        sickbeard.TRAKT_BLACKLIST_NAME = trakt_blacklist_name

        sickbeard.USE_EMAIL = config.checkbox_to_value(use_email)
        sickbeard.EMAIL_NOTIFY_ONSNATCH = config.checkbox_to_value(email_notify_onsnatch)
        sickbeard.EMAIL_NOTIFY_ONDOWNLOAD = config.checkbox_to_value(email_notify_ondownload)
        sickbeard.EMAIL_NOTIFY_ONSUBTITLEDOWNLOAD = config.checkbox_to_value(email_notify_onsubtitledownload)
        sickbeard.EMAIL_HOST = config.clean_host(email_host)
        sickbeard.EMAIL_PORT = config.to_int(email_port, default=25)
        sickbeard.EMAIL_FROM = email_from
        sickbeard.EMAIL_TLS = config.checkbox_to_value(email_tls)
        sickbeard.EMAIL_USER = email_user
        sickbeard.EMAIL_PASSWORD = email_password
        sickbeard.EMAIL_LIST = email_list

        sickbeard.USE_PYTIVO = config.checkbox_to_value(use_pytivo)
        sickbeard.PYTIVO_NOTIFY_ONSNATCH = config.checkbox_to_value(pytivo_notify_onsnatch)
        sickbeard.PYTIVO_NOTIFY_ONDOWNLOAD = config.checkbox_to_value(pytivo_notify_ondownload)
        sickbeard.PYTIVO_NOTIFY_ONSUBTITLEDOWNLOAD = config.checkbox_to_value(pytivo_notify_onsubtitledownload)
        sickbeard.PYTIVO_UPDATE_LIBRARY = config.checkbox_to_value(pytivo_update_library)
        sickbeard.PYTIVO_HOST = config.clean_host(pytivo_host)
        sickbeard.PYTIVO_SHARE_NAME = pytivo_share_name
        sickbeard.PYTIVO_TIVO_NAME = pytivo_tivo_name

        sickbeard.USE_NMA = config.checkbox_to_value(use_nma)
        sickbeard.NMA_NOTIFY_ONSNATCH = config.checkbox_to_value(nma_notify_onsnatch)
        sickbeard.NMA_NOTIFY_ONDOWNLOAD = config.checkbox_to_value(nma_notify_ondownload)
        sickbeard.NMA_NOTIFY_ONSUBTITLEDOWNLOAD = config.checkbox_to_value(nma_notify_onsubtitledownload)
        sickbeard.NMA_API = nma_api
        sickbeard.NMA_PRIORITY = nma_priority

        sickbeard.USE_PUSHALOT = config.checkbox_to_value(use_pushalot)
        sickbeard.PUSHALOT_NOTIFY_ONSNATCH = config.checkbox_to_value(pushalot_notify_onsnatch)
        sickbeard.PUSHALOT_NOTIFY_ONDOWNLOAD = config.checkbox_to_value(pushalot_notify_ondownload)
        sickbeard.PUSHALOT_NOTIFY_ONSUBTITLEDOWNLOAD = config.checkbox_to_value(pushalot_notify_onsubtitledownload)
        sickbeard.PUSHALOT_AUTHORIZATIONTOKEN = pushalot_authorizationtoken

        sickbeard.USE_PUSHBULLET = config.checkbox_to_value(use_pushbullet)
        sickbeard.PUSHBULLET_NOTIFY_ONSNATCH = config.checkbox_to_value(pushbullet_notify_onsnatch)
        sickbeard.PUSHBULLET_NOTIFY_ONDOWNLOAD = config.checkbox_to_value(pushbullet_notify_ondownload)
        sickbeard.PUSHBULLET_NOTIFY_ONSUBTITLEDOWNLOAD = config.checkbox_to_value(pushbullet_notify_onsubtitledownload)
        sickbeard.PUSHBULLET_API = pushbullet_api
        sickbeard.PUSHBULLET_DEVICE = pushbullet_device_list

        sickbeard.save_config()

        if len(results) > 0:
            for x in results:
                logger.log(x, logger.ERROR)
            ui.notifications.error('Error(s) Saving Configuration',
                                   '<br />\n'.join(results))
        else:
            ui.notifications.message('Configuration Saved', ek(os.path.join, sickbeard.CONFIG_FILE))

        return self.redirect("/config/notifications/")


@route('/config/subtitles(/?.*)')
class ConfigSubtitles(Config):
    def __init__(self, *args, **kwargs):
        super(ConfigSubtitles, self).__init__(*args, **kwargs)

    def index(self):
        t = PageTemplate(rh=self, file="config_subtitles.mako")

        return t.render(submenu=self.ConfigMenu(), title='Config - Subtitles', header='Subtitles', topmenu='config')

    def saveSubtitles(self, use_subtitles=None, subtitles_plugins=None, subtitles_languages=None, subtitles_dir=None,
                      service_order=None, subtitles_history=None, subtitles_finder_frequency=None,
                      subtitles_multi=None, embedded_subtitles_all=None, subtitles_extra_scripts=None):

        results = []

        config.change_SUBTITLES_FINDER_FREQUENCY(subtitles_finder_frequency)
        config.change_USE_SUBTITLES(use_subtitles)

        sickbeard.SUBTITLES_LANGUAGES = [lang.strip() for lang in subtitles_languages.split(',') if subtitles.isValidLanguage(lang.strip())] if subtitles_languages else []
        sickbeard.SUBTITLES_DIR = subtitles_dir
        sickbeard.SUBTITLES_HISTORY = config.checkbox_to_value(subtitles_history)
        sickbeard.EMBEDDED_SUBTITLES_ALL = config.checkbox_to_value(embedded_subtitles_all)
        sickbeard.SUBTITLES_MULTI = config.checkbox_to_value(subtitles_multi)
        sickbeard.SUBTITLES_EXTRA_SCRIPTS = [x.strip() for x in subtitles_extra_scripts.split('|') if x.strip()]

        # Subtitles services
        services_str_list = service_order.split()
        subtitles_services_list = []
        subtitles_services_enabled = []
        for curServiceStr in services_str_list:
            curService, curEnabled = curServiceStr.split(':')
            subtitles_services_list.append(curService)
            subtitles_services_enabled.append(int(curEnabled))

        sickbeard.SUBTITLES_SERVICES_LIST = subtitles_services_list
        sickbeard.SUBTITLES_SERVICES_ENABLED = subtitles_services_enabled

        sickbeard.save_config()

        if len(results) > 0:
            for x in results:
                logger.log(x, logger.ERROR)
            ui.notifications.error('Error(s) Saving Configuration',
                                   '<br />\n'.join(results))
        else:
            ui.notifications.message('Configuration Saved', ek(os.path.join, sickbeard.CONFIG_FILE))

        return self.redirect("/config/subtitles/")


@route('/config/anime(/?.*)')
class ConfigAnime(Config):
    def __init__(self, *args, **kwargs):
        super(ConfigAnime, self).__init__(*args, **kwargs)

    def index(self):

        t = PageTemplate(rh=self, file="config_anime.mako")

        return t.render(submenu=self.ConfigMenu(), title='Config - Anime', header='Anime', topmenu='config')

    def saveAnime(self, use_anidb=None, anidb_username=None, anidb_password=None, anidb_use_mylist=None,
                  split_home=None):

        results = []

        sickbeard.USE_ANIDB = config.checkbox_to_value(use_anidb)
        sickbeard.ANIDB_USERNAME = anidb_username
        sickbeard.ANIDB_PASSWORD = anidb_password
        sickbeard.ANIDB_USE_MYLIST = config.checkbox_to_value(anidb_use_mylist)
        sickbeard.ANIME_SPLIT_HOME = config.checkbox_to_value(split_home)

        sickbeard.save_config()

        if len(results) > 0:
            for x in results:
                logger.log(x, logger.ERROR)
            ui.notifications.error('Error(s) Saving Configuration',
                                   '<br />\n'.join(results))
        else:
            ui.notifications.message('Configuration Saved', ek(os.path.join, sickbeard.CONFIG_FILE))

        return self.redirect("/config/anime/")


@route('/errorlogs(/?.*)')
class ErrorLogs(WebRoot):
    def __init__(self, *args, **kwargs):
        super(ErrorLogs, self).__init__(*args, **kwargs)

    def ErrorLogsMenu(self, level):
        menu = [
            {'title': 'Clear Errors', 'path': 'errorlogs/clearerrors/', 'requires': self.haveErrors() and level == logger.ERROR, 'icon': 'ui-icon ui-icon-trash'},
            {'title': 'Clear Warnings', 'path': 'errorlogs/clearerrors/?level='+str(logger.WARNING), 'requires': self.haveWarnings() and level == logger.WARNING, 'icon': 'ui-icon ui-icon-trash'},
            {'title': 'Submit Errors', 'path': 'errorlogs/submit_errors/', 'requires': self.haveErrors() and level == logger.ERROR, 'class':'sumbiterrors', 'confirm': True, 'icon': 'ui-icon ui-icon-arrowreturnthick-1-n'},
        ]

        return menu

    def index(self, level=logger.ERROR):
        try:
            level = int(level)
        except:
            level = logger.ERROR

        t = PageTemplate(rh=self, file="errorlogs.mako")
        return t.render(header="Logs &amp; Errors", title="Logs &amp; Errors", topmenu="system", submenu=self.ErrorLogsMenu(level), logLevel=level)

    def haveErrors(self):
        if len(classes.ErrorViewer.errors) > 0:
            return True

    def haveWarnings(self):
        if len(classes.WarningViewer.errors) > 0:
            return True

    def clearerrors(self, level=logger.ERROR):
        if int(level) == logger.WARNING:
            classes.WarningViewer.clear()
        else:
            classes.ErrorViewer.clear()

        return self.redirect("/errorlogs/viewlog/")

    def viewlog(self, minLevel=logger.INFO, logFilter="<NONE>",logSearch=None, maxLines=500):

        def Get_Data(Levelmin, data_in, lines_in, regex, Filter, Search, mlines):

            lastLine = False
            numLines = lines_in
            numToShow = min(maxLines, numLines + len(data_in))

            finalData = []

            for x in reversed(data_in):
                x = ss(x)
                match = re.match(regex, x)

                if match:
                    level = match.group(7)
                    logName = match.group(8)
                    if not sickbeard.DEBUG and (level == 'DEBUG' or level == 'DB'):
                        continue
                    if level not in logger.reverseNames:
                        lastLine = False
                        continue

                    if logSearch and logSearch.lower() in x.lower():
                        lastLine = True
                        finalData.append(x)
                        numLines += 1
                    elif not logSearch and logger.reverseNames[level] >= minLevel and (logFilter == '<NONE>' or logName.startswith(logFilter)):
                        lastLine = True
                        finalData.append(x)
                        numLines += 1
                    else:
                        lastLine = False
                        continue

                elif lastLine:
                    finalData.append("AA" + x)
                    numLines += 1



                if numLines >= numToShow:
                    return finalData

            return finalData

        t = PageTemplate(rh=self, file="viewlogs.mako")

        minLevel = int(minLevel)

        logNameFilters = {'<NONE>': u'&lt;No Filter&gt;',
                          'DAILYSEARCHER': u'Daily Searcher',
                          'BACKLOG': u'Backlog',
                          'SHOWUPDATER': u'Show Updater',
                          'CHECKVERSION': u'Check Version',
                          'SHOWQUEUE': u'Show Queue',
                          'SEARCHQUEUE': u'Search Queue',
                          'FINDPROPERS': u'Find Propers',
                          'POSTPROCESSER': u'Postprocesser',
                          'FINDSUBTITLES': u'Find Subtitles',
                          'TRAKTCHECKER': u'Trakt Checker',
                          'EVENT': u'Event',
                          'ERROR': u'Error',
                          'TORNADO': u'Tornado',
                          'Thread': u'Thread',
                          'MAIN': u'Main',
                          }

        if logFilter not in logNameFilters:
            logFilter = '<NONE>'

        regex = "^(\d\d\d\d)\-(\d\d)\-(\d\d)\s*(\d\d)\:(\d\d):(\d\d)\s*([A-Z]+)\s*(.+?)\s*\:\:\s*(.*)$"

        data = []

        if os.path.isfile(logger.logFile):
            with ek(codecs.open, *[logger.logFile, 'r', 'utf-8']) as f:
                data = Get_Data(minLevel, f.readlines(), 0, regex, logFilter, logSearch, maxLines)

        for i in range (1 , int(sickbeard.LOG_NR)):
            if os.path.isfile(logger.logFile + "." + str(i)) and (len(data) <= maxLines):
                with ek(codecs.open, *[logger.logFile + "." + str(i), 'r', 'utf-8']) as f:
                        data += Get_Data(minLevel, f.readlines(), len(data), regex, logFilter, logSearch, maxLines)

        return t.render(header="Log File", title="Logs", topmenu="system",
                logLines="".join(data), minLevel=minLevel, logNameFilters=logNameFilters,
                logFilter=logFilter, logSearch=logSearch)

    def submit_errors(self):
        submitter_result, issue_id = logger.submit_errors()
        logger.log(submitter_result, (logger.INFO, logger.WARNING)[issue_id is None])
        submitter_notification = ui.notifications.error if issue_id is None else ui.notifications.message
        submitter_notification(submitter_result)

        return self.redirect("/errorlogs/")
