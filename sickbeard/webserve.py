# coding=utf-8
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage. If not, see <http://www.gnu.org/licenses/>.
# pylint: disable=abstract-method,too-many-lines, R

import ast
import datetime
import gettext
import os
import rarfile
import re
import time
import traceback
import urllib

try:
    import json
except ImportError:
    import simplejson as json

from requests.compat import urljoin
import markdown2

from mako.template import Template as MakoTemplate
from mako.lookup import TemplateLookup
from mako.exceptions import RichTraceback
from mako.runtime import UNDEFINED

from tornado.routes import route
from tornado.web import RequestHandler, HTTPError, authenticated
from tornado.gen import coroutine
from tornado.ioloop import IOLoop
from tornado.process import cpu_count
from tornado.concurrent import run_on_executor

from concurrent.futures import ThreadPoolExecutor

from dateutil import tz
import adba
from libtrakt import TraktAPI
from libtrakt.exceptions import traktException

import sickbeard
from sickbeard import config, sab, clients, notifiers, processTV, ui, logger, \
    helpers, classes, db, search_queue, naming, subtitles as subtitle_module, \
    network_timezones
from sickbeard.providers import newznab, rsstorrent
from sickbeard.common import Quality, Overview, statusStrings, cpu_presets, \
    SNATCHED, UNAIRED, IGNORED, WANTED, FAILED, SKIPPED

from sickbeard.blackandwhitelist import BlackAndWhiteList, short_group_names
from sickbeard.browser import foldersAtPath
from sickbeard.scene_numbering import get_scene_numbering, set_scene_numbering, get_scene_numbering_for_show, \
    get_xem_numbering_for_show, get_scene_absolute_numbering_for_show, get_xem_absolute_numbering_for_show, \
    get_scene_absolute_numbering

from sickbeard.webapi import function_mapper
from sickbeard.imdbPopular import imdb_popular
from sickbeard.helpers import get_showname_from_indexer
from sickbeard.versionChecker import CheckVersion

from sickrage.helper import setup_github, episode_num, try_int, sanitize_filename
from sickrage.helper.encoding import ek, ss
from sickrage.helper.exceptions import CantRefreshShowException, CantUpdateShowException, ex
from sickrage.helper.exceptions import MultipleShowObjectsException, NoNFOException, ShowDirectoryNotFoundException
from sickrage.media.ShowBanner import ShowBanner
from sickrage.media.ShowFanArt import ShowFanArt
from sickrage.media.ShowNetworkLogo import ShowNetworkLogo
from sickrage.media.ShowPoster import ShowPoster
from sickrage.providers.GenericProvider import GenericProvider
from sickrage.show.ComingEpisodes import ComingEpisodes
from sickrage.show.History import History as HistoryTool
from sickrage.show.Show import Show
from sickrage.system.Restart import Restart
from sickrage.system.Shutdown import Shutdown

mako_lookup = {}

def get_lookup():
    mako_lookup['mako'] = mako_lookup.get('mako') or TemplateLookup(
        directories=[ek(os.path.join, sickbeard.PROG_DIR, "gui/" + sickbeard.GUI_NAME + "/views/")],
        module_directory=ek(os.path.join, sickbeard.CACHE_DIR, 'mako'),
        strict_undefined=sickbeard.BRANCH and sickbeard.BRANCH != 'master',
        #  format_exceptions=True,
        filesystem_checks=True
    )
    return mako_lookup.get('mako')


class PageTemplate(MakoTemplate):
    def __init__(self, rh, filename):
        super(PageTemplate, self).__init__(filename)
        self.arguments = {}

        lookup = get_lookup()
        self.template = lookup.get_template(filename)

        self.arguments['srRoot'] = sickbeard.WEB_ROOT
        self.arguments['sbHttpPort'] = sickbeard.WEB_PORT
        self.arguments['sbHttpsPort'] = sickbeard.WEB_PORT
        self.arguments['sbHttpsEnabled'] = sickbeard.ENABLE_HTTPS
        self.arguments['sbHandleReverseProxy'] = sickbeard.HANDLE_REVERSE_PROXY
        self.arguments['sbThemeName'] = sickbeard.THEME_NAME
        self.arguments['sbDefaultPage'] = sickbeard.DEFAULT_PAGE
        self.arguments['srLogin'] = rh.get_current_user()
        self.arguments['sbStartTime'] = rh.startTime

        if rh.request.headers['Host'][0] == '[':
            self.arguments['sbHost'] = re.match(r"^\[.*\]", rh.request.headers['Host'], re.X | re.M | re.S).group(0)
        else:
            self.arguments['sbHost'] = re.match(r"^[^:]+", rh.request.headers['Host'], re.X | re.M | re.S).group(0)

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
        self.arguments['submenu'] = []
        self.arguments['controller'] = "FixME"
        self.arguments['action'] = "FixME"
        self.arguments['show'] = UNDEFINED

    def render(self, *args, **kwargs):
        for key in self.arguments:
            if key not in kwargs:
                kwargs[key] = self.arguments[key]

        kwargs['makoStartTime'] = time.time()
        try:
            return self.template.render_unicode(*args, **kwargs)
        except Exception:
            kwargs['title'] = '500'
            kwargs['header'] = _('Mako Error')
            kwargs['backtrace'] = RichTraceback()
            return get_lookup().get_template('500.mako').render_unicode(*args, **kwargs)


class BaseHandler(RequestHandler):
    startTime = 0.

    def __init__(self, *args, **kwargs):
        self.startTime = time.time()

        super(BaseHandler, self).__init__(*args, **kwargs)

    # def set_default_headers(self):
    #     self.set_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')

    def write_error(self, status_code, **kwargs):
        # handle 404 http errors
        if status_code == 404:
            url = self.request.uri
            if sickbeard.WEB_ROOT and self.request.uri.startswith(sickbeard.WEB_ROOT):
                url = url[len(sickbeard.WEB_ROOT) + 1:]

            if url[:3] != 'api':
                t = PageTemplate(rh=self, filename="404.mako")
                return self.finish(t.render(title='404', header=_('Oops')))
            else:
                self.finish(_('Wrong API key used'))

        elif self.settings.get("debug") and "exc_info" in kwargs:
            exc_info = kwargs["exc_info"]
            trace_info = ''.join(["{0}<br>".format(line) for line in traceback.format_exception(*exc_info)])
            request_info = ''.join(["<strong>{0}</strong>: {1}<br>".format(k, self.request.__dict__[k]) for k in
                                    self.request.__dict__.keys()])
            error = exc_info[1]

            self.set_header('Content-Type', 'text/html')
            self.finish("""<html>
                                 <title>{0}</title>
                                 <body>
                                    <h2>Error</h2>
                                    <p>{1}</p>
                                    <h2>Traceback</h2>
                                    <p>{2}</p>
                                    <h2>Request Info</h2>
                                    <p>{3}</p>
                                    <button onclick="window.location='{4}/errorlogs/';">View Log(Errors)</button>
                                 </body>
                               </html>""".format(error, error, trace_info, request_info, sickbeard.WEB_ROOT))

    def redirect(self, url, permanent=False, status=None):
        """Sends a redirect to the given (optionally relative) URL.

        ----->>>>> NOTE: Removed self.finish <<<<<-----

        If the ``status`` argument is specified, that value is used as the
        HTTP status code; otherwise either 301 (permanent) or 302
        (temporary) is chosen based on the ``permanent`` argument.
        The default is 302 (temporary).
        """
        from tornado.escape import utf8
        if not url.startswith(sickbeard.WEB_ROOT):
            url = sickbeard.WEB_ROOT + url

        if self._headers_written:
            raise Exception("Cannot redirect after headers have been written")
        if not status:
            status = 301 if permanent else 302
        else:
            assert isinstance(status, int) and 300 <= status <= 399
        self.set_status(status)
        self.set_header("Location", urljoin(utf8(self.request.uri), utf8(url)))

    def get_current_user(self):
        if not isinstance(self, UI) and sickbeard.WEB_USERNAME and sickbeard.WEB_PASSWORD:
            return self.get_secure_cookie('sickrage_user')
        else:
            return True


class WebHandler(BaseHandler):
    def __init__(self, *args, **kwargs):
        super(WebHandler, self).__init__(*args, **kwargs)
        self.io_loop = IOLoop.current()

    executor = ThreadPoolExecutor(cpu_count())

    @authenticated
    @coroutine
    def get(self, _route, *args, **kwargs):
        try:
            # route -> method obj
            _route = _route.strip('/').replace('.', '_') or 'index'
            method = getattr(self, _route)

            results = yield self.async_call(method)

            self.finish(results)

        except AttributeError:
            logger.log(u'Failed doing webui request "{0}": {1}'.format(route, traceback.format_exc()), logger.DEBUG)
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
        except Exception:
            logger.log(u'Failed doing webui callback: {0}'.format((traceback.format_exc())), logger.ERROR)
            raise

    # post uses get method
    post = get


class LoginHandler(BaseHandler):
    def get(self, *args, **kwargs):

        if self.get_current_user():
            self.redirect('/' + sickbeard.DEFAULT_PAGE + '/')
        else:
            t = PageTemplate(rh=self, filename="login.mako")
            self.finish(t.render(title=_("Login"), header=_("Login"), topmenu="login"))

    def post(self, *args, **kwargs):

        api_key = None

        username = sickbeard.WEB_USERNAME
        password = sickbeard.WEB_PASSWORD

        if self.get_argument('username', '') == username and self.get_argument('password', '') == password:
            api_key = sickbeard.API_KEY

        if sickbeard.NOTIFY_ON_LOGIN and not helpers.is_ip_private(self.request.remote_ip):
            notifiers.notify_login(self.request.remote_ip)

        if api_key:
            remember_me = try_int(self.get_argument('remember_me', default=0), 0)
            self.set_secure_cookie('sickrage_user', api_key, expires_days=30 if remember_me > 0 else None)
            logger.log(u'User logged into the SickRage web interface', logger.INFO)
        else:
            logger.log(u'User attempted a failed login to the SickRage web interface from IP: ' + self.request.remote_ip, logger.WARNING)

        self.redirect('/' + sickbeard.DEFAULT_PAGE + '/')


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

            if self.get_argument('u', '') == username and self.get_argument('p', '') == password:
                api_key = sickbeard.API_KEY

            self.finish({'success': bool(api_key), 'api_key': api_key})
        except Exception:
            logger.log(u'Failed doing key request: {0}'.format((traceback.format_exc())), logger.ERROR)
            self.finish({'success': False, 'error': 'Failed returning results'})


@route('(.*)(/?)')
class WebRoot(WebHandler):
    def __init__(self, *args, **kwargs):
        super(WebRoot, self).__init__(*args, **kwargs)

    def index(self):
        return self.redirect('/' + sickbeard.DEFAULT_PAGE + '/')

    def robots_txt(self):
        """ Keep web crawlers out """
        self.set_header('Content-Type', 'text/plain')
        return "User-agent: *\nDisallow: /"

    def apibuilder(self):
        def titler(x):
            return (helpers.remove_article(x), x)[not x or sickbeard.SORT_ARTICLE]

        main_db_con = db.DBConnection(row_type='dict')
        shows = sorted(sickbeard.showList, lambda x, y: cmp(titler(x.name), titler(y.name)))
        episodes = {}

        results = main_db_con.select(
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
            apikey = _('API Key not generated')

        t = PageTemplate(rh=self, filename='apiBuilder.mako')
        return t.render(title=_('API Builder'), header=_('API Builder'), shows=shows, episodes=episodes, apikey=apikey,
                        commands=function_mapper)

    def showPoster(self, show=None, which=None):

        media_format = ('normal', 'thumb')[which in ('banner_thumb', 'poster_thumb', 'small')]

        if which[0:6] == 'banner':
            media = ShowBanner(show, media_format)
        elif which[0:6] == 'fanart':
            media = ShowFanArt(show, media_format)
        elif which[0:6] == 'poster':
            media = ShowPoster(show, media_format)
        elif which[0:7] == 'network':
            media = ShowNetworkLogo(show, media_format)
        else:
            media = None

        if media:
            self.set_header('Content-Type', media.get_media_type())

            return media.get_media()

        return None

    def setHomeLayout(self, layout):

        if layout not in ('poster', 'small', 'banner', 'simple', 'coverflow'):
            layout = 'poster'

        sickbeard.HOME_LAYOUT = layout
        # Don't redirect to default page so user can see new layout
        return self.redirect("/home/")

    @staticmethod
    def setPosterSortBy(sort):

        if sort not in ('name', 'date', 'network', 'progress'):
            sort = 'name'

        sickbeard.POSTER_SORTBY = sort
        sickbeard.save_config()

    @staticmethod
    def setPosterSortDir(direction):

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
        if sort not in ('date', 'network', 'show') or sickbeard.COMING_EPS_LAYOUT == 'calendar':
            sort = 'date'

        sickbeard.COMING_EPS_SORT = sort

        return self.redirect("/schedule/")

    def schedule(self, layout=None):
        next_week = datetime.date.today() + datetime.timedelta(days=7)
        next_week1 = datetime.datetime.combine(next_week, datetime.time(tzinfo=network_timezones.sb_timezone))
        results = ComingEpisodes.get_coming_episodes(ComingEpisodes.categories, sickbeard.COMING_EPS_SORT, False)
        today = datetime.datetime.now().replace(tzinfo=network_timezones.sb_timezone)

        # Allow local overriding of layout parameter
        if layout and layout in ('poster', 'banner', 'list', 'calendar'):
            layout = layout
        else:
            layout = sickbeard.COMING_EPS_LAYOUT

        t = PageTemplate(rh=self, filename='schedule.mako')
        return t.render(next_week=next_week1, today=today, results=results, layout=layout,
                        title=_('Schedule'), header=_('Schedule'), topmenu='schedule',
                        controller="schedule", action="index")


class CalendarHandler(BaseHandler):
    def get(self):
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

        logger.log(u"Receiving iCal request from {0}".format(self.request.remote_ip))

        # Create a iCal string
        ical = 'BEGIN:VCALENDAR\r\n'
        ical += 'VERSION:2.0\r\n'
        ical += 'X-WR-CALNAME:SickRage\r\n'
        ical += 'X-WR-CALDESC:SickRage\r\n'
        ical += 'PRODID://Sick-Beard Upcoming Episodes//\r\n'

        future_weeks = try_int(self.get_argument('future', 52), 52)
        past_weeks = try_int(self.get_argument('past', 52), 52)

        # Limit dates
        past_date = (datetime.date.today() + datetime.timedelta(weeks=-past_weeks)).toordinal()
        future_date = (datetime.date.today() + datetime.timedelta(weeks=future_weeks)).toordinal()

        # Get all the shows that are not paused and are currently on air (from kjoconnor Fork)
        main_db_con = db.DBConnection()
        calendar_shows = main_db_con.select(
            "SELECT show_name, indexer_id, network, airs, runtime FROM tv_shows WHERE ( status = 'Continuing' OR status = 'Returning Series' ) AND paused != '1'")
        for show in calendar_shows:
            # Get all episodes of this show airing between today and next month
            episode_list = main_db_con.select(
                "SELECT indexerid, name, season, episode, description, airdate FROM tv_episodes WHERE airdate >= ? AND airdate < ? AND showid = ?",
                (past_date, future_date, int(show["indexer_id"])))

            utc = tz.gettz('GMT')

            for episode in episode_list:

                air_date_time = network_timezones.parse_date_time(episode['airdate'], show["airs"],
                                                                  show['network']).astimezone(utc)
                air_date_time_end = air_date_time + datetime.timedelta(
                    minutes=try_int(show["runtime"], 60))

                # Create event for episode
                ical += 'BEGIN:VEVENT\r\n'
                ical += 'DTSTART:' + air_date_time.strftime("%Y%m%d") + 'T' + air_date_time.strftime(
                    "%H%M%S") + 'Z\r\n'
                ical += 'DTEND:' + air_date_time_end.strftime(
                    "%Y%m%d") + 'T' + air_date_time_end.strftime(
                        "%H%M%S") + 'Z\r\n'
                if sickbeard.CALENDAR_ICONS:
                    ical += 'X-GOOGLE-CALENDAR-CONTENT-ICON:https://lh3.googleusercontent.com/-Vp_3ZosvTgg/VjiFu5BzQqI/AAAAAAAA_TY/3ZL_1bC0Pgw/s16-Ic42/SickRage.png\r\n'
                    ical += 'X-GOOGLE-CALENDAR-CONTENT-DISPLAY:CHIP\r\n'
                ical += u'SUMMARY: {0} - {1}x{2} - {3}\r\n'.format(
                    show['show_name'], episode['season'], episode['episode'], episode['name']
                )
                ical += 'UID:SickRage-' + str(datetime.date.today().isoformat()) + '-' + \
                    show['show_name'].replace(" ", "-") + '-E' + str(episode['episode']) + \
                    'S' + str(episode['season']) + '\r\n'
                if episode['description']:
                    ical += u'DESCRIPTION: {0} on {1} \\n\\n {2}\r\n'.format(
                        (show['airs'] or '(Unknown airs)'),
                        (show['network'] or 'Unknown network'),
                        episode['description'].splitlines()[0])
                else:
                    ical += 'DESCRIPTION:' + (show['airs'] or '(Unknown airs)') + ' on ' + (
                        show['network'] or 'Unknown network') + '\r\n'

                ical += 'END:VEVENT\r\n'

        # Ending the iCal
        ical += 'END:VCALENDAR'

        return ical


@route('/ui(/?.*)')
class UI(WebRoot):
    def __init__(self, *args, **kwargs):
        super(UI, self).__init__(*args, **kwargs)

    @staticmethod
    def add_message():
        ui.notifications.message(_('Test 1'), _('This is test number 1'))
        ui.notifications.error(_('Test 2'), _('This is test number 2'))

        return "ok"

    def get_messages(self):
        self.set_header('Cache-Control', 'max-age=0,no-cache,no-store')
        self.set_header("Content-Type", "application/json")
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

    def index(self, path='', includeFiles=False):  # pylint: disable=arguments-differ

        self.set_header('Cache-Control', 'max-age=0,no-cache,no-store')
        self.set_header("Content-Type", "application/json")

        return json.dumps(foldersAtPath(path, True, bool(int(includeFiles))))

    def complete(self, term, includeFiles=0):

        self.set_header('Cache-Control', 'max-age=0,no-cache,no-store')
        self.set_header("Content-Type", "application/json")
        paths = [entry['path'] for entry in foldersAtPath(ek(os.path.dirname, term), includeFiles=bool(int(includeFiles)))
                 if 'path' in entry]

        return json.dumps(paths)


@route('/home(/?.*)')
class Home(WebRoot):
    def __init__(self, *args, **kwargs):
        super(Home, self).__init__(*args, **kwargs)

    def _genericMessage(self, subject, message):
        t = PageTemplate(rh=self, filename="genericMessage.mako")
        return t.render(message=message, subject=subject, topmenu="home", title="")

    @staticmethod
    def _getEpisode(show, season=None, episode=None, absolute=None):
        if not show:
            return None, _("Invalid show parameters")

        show_obj = Show.find(sickbeard.showList, int(show))

        if not show_obj:
            return None, _("Invalid show paramaters")

        if absolute:
            ep_obj = show_obj.getEpisode(absolute_number=absolute)
        elif season and episode:
            ep_obj = show_obj.getEpisode(season, episode)
        else:
            return None, _("Invalid paramaters")

        if not ep_obj:
            return None, _("Episode couldn't be retrieved")

        return ep_obj, ''

    def index(self, *args, **kwargs):
        t = PageTemplate(rh=self, filename="home.mako")

        selected_root = kwargs.get('root')
        if selected_root and sickbeard.ROOT_DIRS:
            backend_pieces = sickbeard.ROOT_DIRS.split('|')
            backend_dirs = backend_pieces[1:]
            try:
                assert selected_root != '-1'
                selected_root_dir = backend_dirs[int(selected_root)]
                if selected_root_dir[-1] not in ('/', '\\'):
                    selected_root_dir += os.sep
            except (IndexError, ValueError, TypeError, AssertionError):
                selected_root_dir = ''
        else:
            selected_root_dir = ''

        if sickbeard.ANIME_SPLIT_HOME:
            shows = []
            anime = []
            for show in sickbeard.showList:
                if selected_root_dir in show._location:
                    if show.is_anime:
                        anime.append(show)
                    else:
                        shows.append(show)
            showlists = [["Shows", shows], ["Anime", anime]]
        else:
            shows = []
            for show in sickbeard.showList:
                if selected_root_dir in show._location:
                    shows.append(show)
            showlists = [["Shows", shows]]

        stats = self.show_statistics()
        return t.render(title=_("Home"), header=_("Show List"), topmenu="home", showlists=showlists, show_stat=stats[
            0], max_download_count=stats[1], controller="home", action="index", selected_root=selected_root or '-1')

    @staticmethod
    def show_statistics():
        main_db_con = db.DBConnection()
        today = str(datetime.date.today().toordinal())

        status_quality = '(' + ','.join([str(x) for x in Quality.SNATCHED + Quality.SNATCHED_PROPER + Quality.SNATCHED_BEST]) + ')'
        status_download = '(' + ','.join([str(x) for x in Quality.DOWNLOADED + Quality.ARCHIVED]) + ')'

        sql_statement = 'SELECT showid, '

        sql_statement += '(SELECT COUNT(*) FROM tv_episodes WHERE showid=tv_eps.showid AND season > 0 AND episode > 0 AND airdate > 1 AND status IN ' + status_quality + ') AS ep_snatched, '
        sql_statement += '(SELECT COUNT(*) FROM tv_episodes WHERE showid=tv_eps.showid AND season > 0 AND episode > 0 AND airdate > 1 AND status IN ' + status_download + ') AS ep_downloaded, '
        sql_statement += '(SELECT COUNT(*) FROM tv_episodes WHERE showid=tv_eps.showid AND season > 0 AND episode > 0 AND airdate > 1 '
        sql_statement += ' AND ((airdate <= ' + today + ' AND (status = ' + str(SKIPPED) + ' OR status = ' + str(WANTED) + ' OR status = ' + str(FAILED) + ')) '
        sql_statement += ' OR (status IN ' + status_quality + ') OR (status IN ' + status_download + '))) AS ep_total, '

        sql_statement += ' (SELECT airdate FROM tv_episodes WHERE showid=tv_eps.showid AND airdate >= ' + today
        sql_statement += ' AND (status = ' + str(UNAIRED) + ' OR status = ' + str(WANTED) + ') ORDER BY airdate ASC LIMIT 1) AS ep_airs_next, '
        sql_statement += ' (SELECT airdate FROM tv_episodes WHERE showid=tv_eps.showid AND airdate > 1 AND status <> ' + str(UNAIRED) + ' ORDER BY airdate DESC LIMIT 1) AS ep_airs_prev, '
        sql_statement += ' (SELECT SUM(file_size) FROM tv_episodes WHERE showid=tv_eps.showid) AS show_size'
        sql_statement += ' FROM tv_episodes tv_eps GROUP BY showid'

        sql_result = main_db_con.select(sql_statement)

        show_stat = {}
        max_download_count = 1000
        for cur_result in sql_result:
            show_stat[cur_result['showid']] = cur_result
            if cur_result['ep_total'] > max_download_count:
                max_download_count = cur_result['ep_total']

        max_download_count *= 100

        return show_stat, max_download_count

    def is_alive(self, *args_, **kwargs):
        callback, jq_obj = kwargs.get('callback'), kwargs.get('_')
        if not callback and jq_obj:
            return _("Error: Unsupported Request. Send jsonp request with 'callback' variable in the query string.")

        # self.set_header('Cache-Control', 'max-age=0,no-cache,no-store')
        self.set_header('Content-Type', 'text/javascript')
        self.set_header('Access-Control-Allow-Origin', '*')
        self.set_header('Access-Control-Allow-Headers', 'x-requested-with')

        if sickbeard.started:
            return callback + '(' + json.dumps(
                {"msg": str(sickbeard.PID)}) + ');'
        else:
            return callback + '(' + json.dumps({"msg": "nope"}) + ');'

    @staticmethod
    def haveKODI():
        return sickbeard.USE_KODI and sickbeard.KODI_UPDATE_LIBRARY

    @staticmethod
    def havePLEX():
        return sickbeard.USE_PLEX_SERVER and sickbeard.PLEX_UPDATE_LIBRARY

    @staticmethod
    def haveEMBY():
        return sickbeard.USE_EMBY

    @staticmethod
    def haveTORRENT():
        if sickbeard.USE_TORRENTS and sickbeard.TORRENT_METHOD != 'blackhole' and \
                (sickbeard.ENABLE_HTTPS and sickbeard.TORRENT_HOST[:5] == 'https' or not
                 sickbeard.ENABLE_HTTPS and sickbeard.TORRENT_HOST[:5] == 'http:'):
            return True
        else:
            return False

    @staticmethod
    def testSABnzbd(host=None, username=None, password=None, apikey=None):
        # self.set_header('Cache-Control', 'max-age=0,no-cache,no-store')

        host = config.clean_url(host)

        connection, accesMsg = sab.getSabAccesMethod(host)
        if connection:
            authed, authMsg = sab.testAuthentication(host, username, password, apikey)  # @UnusedVariable
            if authed:
                return _("Success. Connected and authenticated")
            else:
                return _("Authentication failed. SABnzbd expects") + " '" + accesMsg + "' " + _("as authentication method") + ", '" + authMsg + "'"
        else:
            return _("Unable to connect to host")

    def testDSM(self, host=None, username=None, password=None):
        return self.testTorrent('download_station', host, username, password)

    @staticmethod
    def testTorrent(torrent_method=None, host=None, username=None, password=None):

        host = config.clean_url(host)

        client = clients.getClientInstance(torrent_method)

        result_, accesMsg = client(host, username, password).testAuthentication()

        return accesMsg

    @staticmethod
    def testFreeMobile(freemobile_id=None, freemobile_apikey=None):

        result, message = notifiers.freemobile_notifier.test_notify(freemobile_id, freemobile_apikey)
        if result:
            return _("SMS sent successfully")
        else:
            return _("Problem sending SMS: {message}").format(message=message)

    @staticmethod
    def testTelegram(telegram_id=None, telegram_apikey=None):

        result, message = notifiers.telegram_notifier.test_notify(telegram_id, telegram_apikey)
        if result:
            return _("Telegram notification succeeded. Check your Telegram clients to make sure it worked")
        else:
            return _("Error sending Telegram notification: {message}").format(message=message)

    @staticmethod
    def testJoin(join_id=None):

        result, message = notifiers.join_notifier.test_notify(join_id)
        if result:
            return _("join notification succeeded. Check your join clients to make sure it worked")
        else:
            return _("Error sending join notification: {message}").format(message=message)

    @staticmethod
    def testGrowl(host=None, password=None):
        # self.set_header('Cache-Control', 'max-age=0,no-cache,no-store')

        host = config.clean_host(host, default_port=23053)

        result = notifiers.growl_notifier.test_notify(host, password)

        pw_append = _(" with password") + ": " + password if password else ''
        if result:
            return _("Registered and Tested growl successfully {growl_host}").format(growl_host=urllib.unquote_plus(host)) + pw_append
        else:
            return _("Registration and Testing of growl failed {growl_host}").format(growl_host=urllib.unquote_plus(host)) + pw_append

    @staticmethod
    def testProwl(prowl_api=None, prowl_priority=0):

        result = notifiers.prowl_notifier.test_notify(prowl_api, prowl_priority)
        if result:
            return _("Test prowl notice sent successfully")
        else:
            return _("Test prowl notice failed")

    @staticmethod
    def testBoxcar2(accesstoken=None):

        result = notifiers.boxcar2_notifier.test_notify(accesstoken)
        if result:
            return _("Boxcar2 notification succeeded. Check your Boxcar2 clients to make sure it worked")
        else:
            return _("Error sending Boxcar2 notification")

    @staticmethod
    def testPushover(userKey=None, apiKey=None):

        result = notifiers.pushover_notifier.test_notify(userKey, apiKey)
        if result:
            return _("Pushover notification succeeded. Check your Pushover clients to make sure it worked")
        else:
            return _("Error sending Pushover notification")

    @staticmethod
    def putio_authorize():
        client = clients.getClientInstance('putio')
        return client().authentication_url  # pylint: disable=protected-access

    @staticmethod
    def twitterStep1():
        return notifiers.twitter_notifier._get_authorization()  # pylint: disable=protected-access

    @staticmethod
    def twitterStep2(key):

        result = notifiers.twitter_notifier._get_credentials(key)  # pylint: disable=protected-access
        logger.log(u"result: " + str(result))
        if result:
            return _("Key verification successful")
        else:
            return _("Unable to verify key")

    @staticmethod
    def testTwitter():

        result = notifiers.twitter_notifier.test_notify()
        if result:
            return _("Tweet successful, check your twitter to make sure it worked")
        else:
            return _("Error sending tweet")

    @staticmethod
    def testTwilio():
        if not notifiers.twilio_notifier.account_regex.match(sickbeard.TWILIO_ACCOUNT_SID):
            return _('Please enter a valid account sid')

        if not notifiers.twilio_notifier.auth_regex.match(sickbeard.TWILIO_AUTH_TOKEN):
            return _('Please enter a valid auth token')

        if not notifiers.twilio_notifier.phone_regex.match(sickbeard.TWILIO_PHONE_SID):
            return _('Please enter a valid phone sid')

        if not notifiers.twilio_notifier.number_regex.match(sickbeard.TWILIO_TO_NUMBER):
            return _('Please format the phone number as "+1-###-###-####"')

        result = notifiers.twilio_notifier.test_notify()
        if result:
            return _('Authorization successful and number ownership verified')
        else:
            return _('Error sending sms')

    @staticmethod
    def testSlack():
        result = notifiers.slack_notifier.test_notify()
        if result:
            return _("Slack message successful")
        else:
            return _("Slack message failed")

    @staticmethod
    def testKODI(host=None, username=None, password=None):

        host = config.clean_hosts(host)
        finalResult = ''
        for curHost in [x.strip() for x in host.split(",")]:
            curResult = notifiers.kodi_notifier.test_notify(urllib.unquote_plus(curHost), username, password)
            if len(curResult.split(":")) > 2 and 'OK' in curResult.split(":")[2]:
                finalResult += _("Test KODI notice sent successfully to {kodi_host}").format(kodi_host=urllib.unquote_plus(curHost))
            else:
                finalResult += _("Test KODI notice failed to {kodi_host}").format(kodi_host=urllib.unquote_plus(curHost))
            finalResult += "<br>\n"

        return finalResult

    def testPHT(self, host=None, username=None, password=None):
        self.set_header('Cache-Control', 'max-age=0,no-cache,no-store')

        if set('*') == set(password or '*'):
            password = sickbeard.PLEX_CLIENT_PASSWORD

        finalResult = ''
        for curHost in [x.strip() for x in host.split(',')]:
            curResult = notifiers.plex_notifier.test_notify_pht(urllib.unquote_plus(curHost), username, password)
            if len(curResult.split(':')) > 2 and 'OK' in curResult.split(':')[2]:
                finalResult += _('Successful test notice sent to Plex Home Theater ... {plex_clients}').format(plex_clients=urllib.unquote_plus(curHost))
            else:
                finalResult += _('Test failed for Plex Home Theater ... {plex_clients}').format(plex_clients=urllib.unquote_plus(curHost))
            finalResult += '<br>' + '\n'

        ui.notifications.message(_('Tested Plex Home Theater(s)') + ':', urllib.unquote_plus(host.replace(',', ', ')))

        return finalResult

    def testPMS(self, host=None, username=None, password=None, plex_server_token=None):
        self.set_header('Cache-Control', 'max-age=0,no-cache,no-store')

        if set('*') == set(password or '*'):
            password = sickbeard.PLEX_SERVER_PASSWORD

        finalResult = ''

        curResult = notifiers.plex_notifier.test_notify_pms(urllib.unquote_plus(host), username, password, plex_server_token)
        if curResult is None:
            finalResult += _('Successful test of Plex Media Server(s) ... {plex_servers}').format(plex_servers=urllib.unquote_plus(host.replace(',', ', ')))
        elif curResult is False:
            finalResult += _('Test failed, No Plex Media Server host specified')
        else:
            finalResult += _('Test failed for Plex Media Server(s) ... {plex_servers}').format(plex_servers=urllib.unquote_plus(str(curResult).replace(',', ', ')))
        finalResult += '<br>' + '\n'

        ui.notifications.message(_('Tested Plex Media Server host(s)') + ':', urllib.unquote_plus(host.replace(',', ', ')))

        return finalResult

    @staticmethod
    def testLibnotify():

        if notifiers.libnotify_notifier.test_notify():
            return _("Tried sending desktop notification via libnotify")
        return notifiers.libnotify_notifier.diagnose()

    @staticmethod
    def testEMBY(host=None, emby_apikey=None):

        host = config.clean_host(host)
        result = notifiers.emby_notifier.test_notify(urllib.unquote_plus(host), emby_apikey)
        if result:
            return _("Test notice sent successfully to {emby_host}").format(emby_host=urllib.unquote_plus(host))
        else:
            return _("Test notice failed to {emby_host}").format(emby_host=urllib.unquote_plus(host))

    @staticmethod
    def testNMJ(host=None, database=None, mount=None):

        host = config.clean_host(host)
        result = notifiers.nmj_notifier.test_notify(urllib.unquote_plus(host), database, mount)
        if result:
            return _("Successfully started the scan update")
        else:
            return _("Test failed to start the scan update")

    @staticmethod
    def settingsNMJ(host=None):

        host = config.clean_host(host)
        result = notifiers.nmj_notifier.notify_settings(urllib.unquote_plus(host))
        if result:
            return '{{"message": _("Got settings from {host}"), "database": "{database}", "mount": "{mount}"}}'.format(**{
                "host": host, "database": sickbeard.NMJ_DATABASE, "mount": sickbeard.NMJ_MOUNT})
        else:
            return '{"message": _("Failed! Make sure your Popcorn is on and NMJ is running. (see Log & Errors -> Debug for detailed info)"), "database": "", "mount": ""}'

    @staticmethod
    def testNMJv2(host=None):

        host = config.clean_host(host)
        result = notifiers.nmjv2_notifier.test_notify(urllib.unquote_plus(host))
        if result:
            return _("Test notice sent successfully to {nmj2_host}").format(nmj2_host=urllib.unquote_plus(host))
        else:
            return _("Test notice failed to {nmj2_host}").format(nmj2_host=urllib.unquote_plus(host))

    @staticmethod
    def settingsNMJv2(host=None, dbloc=None, instance=None):

        host = config.clean_host(host)
        result = notifiers.nmjv2_notifier.notify_settings(urllib.unquote_plus(host), dbloc, instance)
        if result:
            return '{{"message": _("NMJ Database found at: {host}"), "database": "{database}"}}'.format(
                **{"host": host, "database": sickbeard.NMJv2_DATABASE})
        else:
            return '{{"message": _("Unable to find NMJ Database at location: {dbloc}. Is the right location selected and PCH running?"), "database": ""}}'.format(**{
                "dbloc": dbloc})

    @staticmethod
    def getTraktToken(trakt_pin=None):

        trakt_api = TraktAPI(sickbeard.SSL_VERIFY, sickbeard.TRAKT_TIMEOUT)
        response = trakt_api.traktToken(trakt_pin)
        if response:
            return _("Trakt Authorized")
        return _("Trakt Not Authorized!")

    @staticmethod
    def testTrakt(username=None, blacklist_name=None):
        return notifiers.trakt_notifier.test_notify(username, blacklist_name)

    @staticmethod
    def loadShowNotifyLists():

        main_db_con = db.DBConnection()
        rows = main_db_con.select("SELECT show_id, show_name, notify_list FROM tv_shows ORDER BY show_name ASC")

        data = {}
        size = 0
        for r in rows:
            NotifyList = {'emails': '', 'prowlAPIs': ''}
            if r['notify_list'] and len(r['notify_list']) > 0:
                # First, handle legacy format (emails only)
                if not r['notify_list'][0] == '{':
                    NotifyList['emails'] = r['notify_list']
                else:
                    NotifyList = dict(ast.literal_eval(r['notify_list']))

            data[r['show_id']] = {
                'id': r['show_id'],
                'name': r['show_name'],
                'list': NotifyList['emails'],
                'prowl_notify_list': NotifyList['prowlAPIs']
            }
            size += 1
        data['_size'] = size
        return json.dumps(data)

    @staticmethod
    def saveShowNotifyList(show=None, emails=None, prowlAPIs=None):

        entries = {'emails': '', 'prowlAPIs': ''}
        main_db_con = db.DBConnection()

        # Get current data
        for subs in main_db_con.select("SELECT notify_list FROM tv_shows WHERE show_id = ?", [show]):
            if subs['notify_list'] and len(subs['notify_list']) > 0:
                # First, handle legacy format (emails only)
                if not subs['notify_list'][0] == '{':
                    entries['emails'] = subs['notify_list']
                else:
                    entries = dict(ast.literal_eval(subs['notify_list']))

        if emails:
            entries['emails'] = emails
        if prowlAPIs:
            entries['prowlAPIs'] = prowlAPIs

        if emails or prowlAPIs:
            if not main_db_con.action("UPDATE tv_shows SET notify_list = ? WHERE show_id = ?", [str(entries), show]):
                return 'ERROR'

        return 'OK'

    @staticmethod
    def testEmail(host=None, port=None, smtp_from=None, use_tls=None, user=None, pwd=None, to=None):

        host = config.clean_host(host)
        if notifiers.email_notifier.test_notify(host, port, smtp_from, use_tls, user, pwd, to):
            return _('Test email sent successfully! Check inbox.')
        else:
            return _('ERROR: {last_error}').format(last_error=notifiers.email_notifier.last_err)

    @staticmethod
    def testNMA(nma_api=None, nma_priority=0):

        result = notifiers.nma_notifier.test_notify(nma_api, nma_priority)
        if result:
            return _("Test NMA notice sent successfully")
        else:
            return _("Test NMA notice failed")

    @staticmethod
    def testPushalot(authorizationToken=None):

        result = notifiers.pushalot_notifier.test_notify(authorizationToken)
        if result:
            return _("Pushalot notification succeeded. Check your Pushalot clients to make sure it worked")
        else:
            return _("Error sending Pushalot notification")

    @staticmethod
    def testPushbullet(api=None):

        result = notifiers.pushbullet_notifier.test_notify(api)
        if result:
            return _("Pushbullet notification succeeded. Check your device to make sure it worked")
        else:
            return _("Error sending Pushbullet notification")

    @staticmethod
    def getPushbulletDevices(api=None):
        # self.set_header('Cache-Control', 'max-age=0,no-cache,no-store')

        result = notifiers.pushbullet_notifier.get_devices(api)
        if result:
            return result
        else:
            return _("Error sending Pushbullet notification")

    @staticmethod
    def getPushbulletChannels(api=None):

        result = notifiers.pushbullet_notifier.get_channels(api)
        if result:
            return result
        else:
            return _("Error sending Pushbullet notification")

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

        t = PageTemplate(rh=self, filename="status.mako")
        return t.render(title=_('Status'), header=_('Status'), topmenu='system',
                        tvdirFree=tvdirFree, rootDir=rootDir,
                        controller="home", action="status")

    def shutdown(self, pid=None):
        if not Shutdown.stop(pid):
            return self.redirect('/' + sickbeard.DEFAULT_PAGE + '/')

        title = "Shutting down"
        message = "SickRage is shutting down..."

        return self._genericMessage(title, message)

    def restart(self, pid=None):
        if not Restart.restart(pid):
            return self.redirect('/' + sickbeard.DEFAULT_PAGE + '/')

        t = PageTemplate(rh=self, filename="restart.mako")

        return t.render(title=_("Home"), header=_("Restarting SickRage"), topmenu="system",
                        controller="home", action="restart")

    def updateCheck(self, pid=None):
        if str(pid) != str(sickbeard.PID):
            return self.redirect('/home/')

        sickbeard.versionCheckScheduler.action.check_for_new_version(force=True)
        sickbeard.versionCheckScheduler.action.check_for_new_news()

        return self.redirect('/' + sickbeard.DEFAULT_PAGE + '/')

    def update(self, pid=None, branch=None):

        if str(pid) != str(sickbeard.PID):
            return self.redirect('/home/')

        checkversion = CheckVersion()
        backup = checkversion.updater and checkversion._runbackup()  # pylint: disable=protected-access

        if backup is True:
            if branch:
                checkversion.updater.branch = branch

            if checkversion.updater.need_update() and checkversion.updater.update():
                # do a hard restart
                sickbeard.events.put(sickbeard.events.SystemEvent.RESTART)

                t = PageTemplate(rh=self, filename="restart.mako")
                return t.render(title=_("Home"), header=_("Restarting SickRage"), topmenu="home",
                                controller="home", action="restart")
            else:
                return self._genericMessage(_("Update Failed"),
                                            _("Update wasn't successful, not restarting. Check your log for more information."))
        else:
            return self.redirect('/' + sickbeard.DEFAULT_PAGE + '/')

    def branchCheckout(self, branch):
        if sickbeard.BRANCH != branch:
            sickbeard.BRANCH = branch
            ui.notifications.message(_('Checking out branch') + ': ', branch)
            return self.update(sickbeard.PID, branch)
        else:
            ui.notifications.message(_('Already on branch') + ': ', branch)
            return self.redirect('/' + sickbeard.DEFAULT_PAGE + '/')

    @staticmethod
    def getDBcompare():

        checkversion = CheckVersion()
        db_status = checkversion.getDBcompare()

        if db_status == 'upgrade':
            logger.log(u"Checkout branch has a new DB version - Upgrade", logger.DEBUG)
            return json.dumps({"status": "success", 'message': 'upgrade'})
        elif db_status == 'equal':
            logger.log(u"Checkout branch has the same DB version - Equal", logger.DEBUG)
            return json.dumps({"status": "success", 'message': 'equal'})
        elif db_status == 'downgrade':
            logger.log(u"Checkout branch has an old DB version - Downgrade", logger.DEBUG)
            return json.dumps({"status": "success", 'message': 'downgrade'})
        else:
            logger.log(u"Checkout branch couldn't compare DB version.", logger.ERROR)
            return json.dumps({"status": "error", 'message': 'General exception'})

    def displayShow(self, show=None):
        # todo: add more comprehensive show validation
        try:
            show = int(show)  # fails if show id ends in a period SickRage/SickRage#65
            show_obj = Show.find(sickbeard.showList, show)
        except (ValueError, TypeError):
            return self._genericMessage(_("Error"), _("Invalid show ID: {show}").format(show=str(show)))

        if not show_obj:
            return self._genericMessage(_("Error"), _("Show not in show list"))

        main_db_con = db.DBConnection()
        seasonResults = main_db_con.select(
            "SELECT DISTINCT season FROM tv_episodes WHERE showid = ? AND season IS NOT NULL ORDER BY season DESC",
            [show_obj.indexerid]
        )

        min_season = 0 if sickbeard.DISPLAY_SHOW_SPECIALS else 1

        sql_results = main_db_con.select(
            "SELECT * FROM tv_episodes WHERE showid = ? and season >= ? ORDER BY season DESC, episode DESC",
            [show_obj.indexerid, min_season]
        )

        t = PageTemplate(rh=self, filename="displayShow.mako")
        submenu = [{'title': _('Edit'), 'path': 'home/editShow?show={0:d}'.format(show_obj.indexerid), 'icon': 'fa fa-pencil'}]

        try:
            showLoc = (show_obj.location, True)
        except ShowDirectoryNotFoundException:
            showLoc = (show_obj._location, False)  # pylint: disable=protected-access

        show_message = ''

        if sickbeard.showQueueScheduler.action.isBeingAdded(show_obj):
            show_message = _('This show is in the process of being downloaded - the info below is incomplete.')

        elif sickbeard.showQueueScheduler.action.isBeingUpdated(show_obj):
            show_message = _('The information on this page is in the process of being updated.')

        elif sickbeard.showQueueScheduler.action.isBeingRefreshed(show_obj):
            show_message = _('The episodes below are currently being refreshed from disk')

        elif sickbeard.showQueueScheduler.action.isBeingSubtitled(show_obj):
            show_message = _('Currently downloading subtitles for this show')

        elif sickbeard.showQueueScheduler.action.isInRefreshQueue(show_obj):
            show_message = _('This show is queued to be refreshed.')

        elif sickbeard.showQueueScheduler.action.isInUpdateQueue(show_obj):
            show_message = _('This show is queued and awaiting an update.')

        elif sickbeard.showQueueScheduler.action.isInSubtitleQueue(show_obj):
            show_message = _('This show is queued and awaiting subtitles download.')

        if not sickbeard.showQueueScheduler.action.isBeingAdded(show_obj):
            if not sickbeard.showQueueScheduler.action.isBeingUpdated(show_obj):
                if show_obj.paused:
                    submenu.append({'title': _('Resume'), 'path': 'home/togglePause?show={0:d}'.format(show_obj.indexerid), 'icon': 'fa fa-play'})
                else:
                    submenu.append({'title': _('Pause'), 'path': 'home/togglePause?show={0:d}'.format(show_obj.indexerid), 'icon': 'fa fa-pause'})

                submenu.append({'title': _('Remove'), 'path': 'home/deleteShow?show={0:d}'.format(show_obj.indexerid), 'class': 'removeshow', 'confirm': True, 'icon': 'fa fa-trash'})
                submenu.append({'title': _('Re-scan files'), 'path': 'home/refreshShow?show={0:d}'.format(show_obj.indexerid), 'icon': 'fa fa-refresh'})
                submenu.append({'title': _('Force Full Update'), 'path': 'home/updateShow?show={0:d}&amp;force=1'.format(show_obj.indexerid), 'icon': 'fa fa-exchange'})
                submenu.append({'title': _('Update show in KODI'), 'path': 'home/updateKODI?show={0:d}'.format(show_obj.indexerid), 'requires': self.haveKODI(), 'icon': 'menu-icon-kodi'})
                submenu.append({'title': _('Update show in Emby'), 'path': 'home/updateEMBY?show={0:d}'.format(show_obj.indexerid), 'requires': self.haveEMBY(), 'icon': 'menu-icon-emby'})
                if seasonResults and int(seasonResults[-1]["season"]) == 0:
                    if sickbeard.DISPLAY_SHOW_SPECIALS:
                        submenu.append({'title': _('Hide specials'), 'path': 'home/toggleDisplayShowSpecials/?show={0:d}'.format(show_obj.indexerid), 'confirm': True, 'icon': 'fa fa-times'})
                    else:
                        submenu.append({'title': _('Show specials'), 'path': 'home/toggleDisplayShowSpecials/?show={0:d}'.format(show_obj.indexerid), 'confirm': True, 'icon': 'fa fa-check'})

                submenu.append({'title': _('Preview Rename'), 'path': 'home/testRename?show={0:d}'.format(show_obj.indexerid), 'icon': 'fa fa-tag'})

                if sickbeard.USE_SUBTITLES and show_obj.subtitles and not sickbeard.showQueueScheduler.action.isBeingSubtitled(show_obj):
                    submenu.append({'title': _('Download Subtitles'), 'path': 'home/subtitleShow?show={0:d}'.format(show_obj.indexerid), 'icon': 'fa fa-language'})

        epCounts = {
            Overview.SKIPPED: 0,
            Overview.WANTED: 0,
            Overview.QUAL: 0,
            Overview.GOOD: 0,
            Overview.UNAIRED: 0,
            Overview.SNATCHED: 0,
            Overview.SNATCHED_PROPER: 0,
            Overview.SNATCHED_BEST: 0
        }
        epCats = {}

        for curResult in sql_results:
            curEpCat = show_obj.getOverview(curResult["status"])
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
            sortedShowLists = [
                ["Shows", sorted(shows, lambda x, y: cmp(titler(x.name).lower(), titler(y.name).lower()))],
                ["Anime", sorted(anime, lambda x, y: cmp(titler(x.name).lower(), titler(y.name).lower()))]
            ]
        else:
            sortedShowLists = [
                ["Shows", sorted(sickbeard.showList, lambda x, y: cmp(titler(x.name).lower(), titler(y.name).lower()))]
            ]

        bwl = None
        if show_obj.is_anime:
            bwl = show_obj.release_groups

        show_obj.exceptions = sickbeard.scene_exceptions.get_scene_exceptions(show_obj.indexerid)

        indexerid = int(show_obj.indexerid)
        indexer = int(show_obj.indexer)

        # Delete any previous occurrances
        for index, recentShow in enumerate(sickbeard.SHOWS_RECENT):
            if recentShow['indexerid'] == indexerid:
                del sickbeard.SHOWS_RECENT[index]

        # Only track 5 most recent shows
        del sickbeard.SHOWS_RECENT[4:]

        # Insert most recent show
        sickbeard.SHOWS_RECENT.insert(0, {
            'indexerid': indexerid,
            'name': show_obj.name,
        })

        return t.render(
            submenu=submenu, showLoc=showLoc, show_message=show_message,
            show=show_obj, sql_results=sql_results, seasonResults=seasonResults,
            sortedShowLists=sortedShowLists, bwl=bwl, epCounts=epCounts,
            epCats=epCats, all_scene_exceptions=show_obj.exceptions,
            scene_numbering=get_scene_numbering_for_show(indexerid, indexer),
            xem_numbering=get_xem_numbering_for_show(indexerid, indexer),
            scene_absolute_numbering=get_scene_absolute_numbering_for_show(indexerid, indexer),
            xem_absolute_numbering=get_xem_absolute_numbering_for_show(indexerid, indexer),
            title=show_obj.name,
            controller="home",
            action="displayShow"
        )

    @staticmethod
    def plotDetails(show, season, episode):
        main_db_con = db.DBConnection()
        result = main_db_con.selectOne(
            "SELECT description FROM tv_episodes WHERE showid = ? AND season = ? AND episode = ?",
            (int(show), int(season), int(episode)))
        return result['description'] if result else 'Episode not found.'

    @staticmethod
    def sceneExceptions(show):
        exceptionsList = sickbeard.scene_exceptions.get_all_scene_exceptions(show)
        if not exceptionsList:
            return _("No scene exceptions")

        out = []
        for season, names in iter(sorted(exceptionsList.iteritems())):
            if season == -1:
                season = "*"
            out.append("S" + str(season) + ": " + ", ".join(names))
        return "<br>".join(out)

    def editShow(self, show=None, location=None, anyQualities=None, bestQualities=None,
                 exceptions_list=None, flatten_folders=None, paused=None, directCall=False,
                 air_by_date=None, sports=None, dvdorder=None, indexerLang=None,
                 subtitles=None, subtitles_sr_metadata=None, rls_ignore_words=None, rls_require_words=None,
                 anime=None, blacklist=None, whitelist=None, scene=None,
                 defaultEpStatus=None, quality_preset=None):

        anidb_failed = False
        if not show:
            errString = _("Invalid show ID") + ": {show}".format(show=str(show))
            if directCall:
                return [errString]
            else:
                return self._genericMessage(_("Error"), errString)

        show_obj = Show.find(sickbeard.showList, int(show))

        if not show_obj:
            errString = _("Unable to find the specified show") + ": {show}".format(show=str(show))
            if directCall:
                return [errString]
            else:
                return self._genericMessage(_("Error"), errString)

        show_obj.exceptions = sickbeard.scene_exceptions.get_scene_exceptions(show_obj.indexerid)

        if try_int(quality_preset, None):
            bestQualities = []

        if not (location or anyQualities or bestQualities or flatten_folders):
            t = PageTemplate(rh=self, filename="editShow.mako")

            if show_obj.is_anime:
                whitelist = show_obj.release_groups.whitelist
                blacklist = show_obj.release_groups.blacklist

                groups = []
                if helpers.set_up_anidb_connection() and not anidb_failed:
                    try:
                        anime = adba.Anime(sickbeard.ADBA_CONNECTION, name=show_obj.name)
                        groups = anime.get_groups()
                    except Exception as e:
                        anidb_failed = True
                        ui.notifications.error(_('Unable to retreive Fansub Groups from AniDB.'))
                        logger.log(u'Unable to retreive Fansub Groups from AniDB. Error is {0}'.format(e), logger.DEBUG)

            with show_obj.lock:
                show = show_obj
                scene_exceptions = sickbeard.scene_exceptions.get_scene_exceptions(show_obj.indexerid)

            if show_obj.is_anime:
                return t.render(show=show, scene_exceptions=scene_exceptions, groups=groups, whitelist=whitelist,
                                blacklist=blacklist, title=_('Edit Show'), header=_('Edit Show'), controller="home", action="editShow")
            else:
                return t.render(show=show, scene_exceptions=scene_exceptions, title=_('Edit Show'), header=_('Edit Show'),
                                controller="home", action="editShow")

        flatten_folders = not config.checkbox_to_value(flatten_folders)  # UI inverts this value
        dvdorder = config.checkbox_to_value(dvdorder)
        paused = config.checkbox_to_value(paused)
        air_by_date = config.checkbox_to_value(air_by_date)
        scene = config.checkbox_to_value(scene)
        sports = config.checkbox_to_value(sports)
        anime = config.checkbox_to_value(anime)
        subtitles = config.checkbox_to_value(subtitles)
        subtitles_sr_metadata = config.checkbox_to_value(subtitles_sr_metadata)

        if indexerLang and indexerLang in sickbeard.indexerApi(show_obj.indexer).indexer().config['valid_languages']:
            indexer_lang = indexerLang
        else:
            indexer_lang = show_obj.lang

        # if we changed the language then kick off an update
        if indexer_lang == show_obj.lang:
            do_update = False
        else:
            do_update = True

        if scene == show_obj.scene and anime == show_obj.anime:
            do_update_scene_numbering = False
        else:
            do_update_scene_numbering = True

        if not anyQualities:
            anyQualities = []

        if not bestQualities:
            bestQualities = []

        if not exceptions_list:
            exceptions_list = []

        if not isinstance(anyQualities, list):
            anyQualities = [anyQualities]

        if not isinstance(bestQualities, list):
            bestQualities = [bestQualities]

        if not isinstance(exceptions_list, list):
            exceptions_list = [exceptions_list]

        # If directCall from mass_edit_update no scene exceptions handling or blackandwhite list handling
        if directCall:
            do_update_exceptions = False
        else:
            if set(exceptions_list) == set(show_obj.exceptions):
                do_update_exceptions = False
            else:
                do_update_exceptions = True

            with show_obj.lock:
                if anime:
                    if not show_obj.release_groups:
                        show_obj.release_groups = BlackAndWhiteList(show_obj.indexerid)

                    if whitelist:
                        shortwhitelist = short_group_names(whitelist)
                        show_obj.release_groups.set_white_keywords(shortwhitelist)
                    else:
                        show_obj.release_groups.set_white_keywords([])

                    if blacklist:
                        shortblacklist = short_group_names(blacklist)
                        show_obj.release_groups.set_black_keywords(shortblacklist)
                    else:
                        show_obj.release_groups.set_black_keywords([])

        errors = []
        with show_obj.lock:
            newQuality = Quality.combineQualities([int(q) for q in anyQualities], [int(q) for q in bestQualities])
            show_obj.quality = newQuality

            # reversed for now
            if bool(show_obj.flatten_folders) != bool(flatten_folders):
                show_obj.flatten_folders = flatten_folders
                try:
                    sickbeard.showQueueScheduler.action.refreshShow(show_obj)
                except CantRefreshShowException as e:
                    errors.append(_("Unable to refresh this show: {error}").format(error=e))

            show_obj.paused = paused
            show_obj.scene = scene
            show_obj.anime = anime
            show_obj.sports = sports
            show_obj.subtitles = subtitles
            show_obj.subtitles_sr_metadata = subtitles_sr_metadata
            show_obj.air_by_date = air_by_date
            show_obj.default_ep_status = int(defaultEpStatus)

            if not directCall:
                show_obj.lang = indexer_lang
                show_obj.dvdorder = dvdorder
                show_obj.rls_ignore_words = rls_ignore_words.strip()
                show_obj.rls_require_words = rls_require_words.strip()

            if not isinstance(location, unicode):
                location = ek(unicode, location, 'utf-8')

            # if we change location clear the db of episodes, change it, write to db, and rescan
            if ek(os.path.normpath, show_obj._location) != ek(os.path.normpath, location):  # pylint: disable=protected-access
                logger.log(ek(os.path.normpath, show_obj._location) + " != " + ek(os.path.normpath, location), logger.DEBUG)  # pylint: disable=protected-access
                if not ek(os.path.isdir, location) and not sickbeard.CREATE_MISSING_SHOW_DIRS:
                    errors.append(_("New location <tt>{location}</tt> does not exist").format(location=location))

                # don't bother if we're going to update anyway
                elif not do_update:
                    # change it
                    try:
                        show_obj.location = location
                        try:
                            sickbeard.showQueueScheduler.action.refreshShow(show_obj)
                        except CantRefreshShowException as e:
                            errors.append(_("Unable to refresh this show: {error}").format(error=e))
                            # grab updated info from TVDB
                            # show_obj.loadEpisodesFromIndexer()
                            # rescan the episodes in the new folder
                    except NoNFOException:
                        errors.append(
                            "The folder at <tt>{0}</tt> doesn't contain a tvshow.nfo - copy your files to that folder before you change the directory in SickRage.".format(location))

            # save it to the DB
            show_obj.saveToDB()

        # force the update
        if do_update:
            try:
                sickbeard.showQueueScheduler.action.updateShow(show_obj, True)
                time.sleep(cpu_presets[sickbeard.CPU_PRESET])
            except CantUpdateShowException as e:
                errors.append(_("Unable to update show: {error}").format(error=e))

        if do_update_exceptions:
            try:
                sickbeard.scene_exceptions.update_scene_exceptions(show_obj.indexerid, exceptions_list)  # @UndefinedVdexerid)
                time.sleep(cpu_presets[sickbeard.CPU_PRESET])
            except CantUpdateShowException as e:
                errors.append(_("Unable to force an update on scene exceptions of the show."))

        if do_update_scene_numbering:
            try:
                sickbeard.scene_numbering.xem_refresh(show_obj.indexerid, show_obj.indexer)
                time.sleep(cpu_presets[sickbeard.CPU_PRESET])
            except CantUpdateShowException as e:
                errors.append(_("Unable to force an update on scene numbering of the show."))

        if directCall:
            return errors

        if errors:
            ui.notifications.error(_('{num_errors:d} error{plural} while saving changes:').format(num_errors=len(errors), plural="" if len(errors) == 1 else "s"),
                                   '<ul>' + '\n'.join(['<li>{0}</li>'.format(error) for error in errors]) + "</ul>")

        return self.redirect("/home/displayShow?show=" + show)

    def togglePause(self, show=None):
        error, show = Show.pause(show)

        if error:
            return self._genericMessage(_('Error'), error)

        ui.notifications.message(_('{show_name} has been {paused_resumed}').format(show_name=show.name, paused_resumed=(_('resumed'), _('paused'))[show.paused]))

        return self.redirect("/home/displayShow?show={0:d}".format(show.indexerid))

    def deleteShow(self, show=None, full=0):
        if show:
            error, show = Show.delete(show, full)

            if error:
                return self._genericMessage(_('Error'), error)

            ui.notifications.message(
                _('{show_name} has been {deleted_trashed} {was_deleted}').format(
                    show_name=show.name,
                    deleted_trashed=(_('deleted'), _('trashed'))[bool(sickbeard.TRASH_REMOVE_SHOW)],
                    was_deleted=(_('(media untouched)'), _('(with all related media)'))[bool(full)]
                )
            )

            time.sleep(cpu_presets[sickbeard.CPU_PRESET])

        # Remove show from 'RECENT SHOWS' in 'Shows' menu
        sickbeard.SHOWS_RECENT = [x for x in sickbeard.SHOWS_RECENT if x['indexerid'] != show.indexerid]

        # Don't redirect to the default page, so the user can confirm that the show was deleted
        return self.redirect('/home/')

    def refreshShow(self, show=None):
        error, show = Show.refresh(show)

        # This is a show validation error
        if error and not show:
            return self._genericMessage(_('Error'), error)

        # This is a refresh error
        if error:
            ui.notifications.error(_('Unable to refresh this show.'), error)

        time.sleep(cpu_presets[sickbeard.CPU_PRESET])

        return self.redirect("/home/displayShow?show=" + str(show.indexerid))

    def updateShow(self, show=None, force=0):

        if not show:
            return self._genericMessage(_("Error"), _("Invalid show ID"))

        show_obj = Show.find(sickbeard.showList, int(show))

        if not show_obj:
            return self._genericMessage(_("Error"), _("Unable to find the specified show"))

        # force the update
        try:
            sickbeard.showQueueScheduler.action.updateShow(show_obj, bool(force))
        except CantUpdateShowException as e:
            ui.notifications.error(_("Unable to update this show."), ex(e))

        # just give it some time
        time.sleep(cpu_presets[sickbeard.CPU_PRESET])

        return self.redirect("/home/displayShow?show=" + str(show_obj.indexerid))

    def subtitleShow(self, show=None, force=0):

        if not show:
            return self._genericMessage(_("Error"), _("Invalid show ID"))

        show_obj = Show.find(sickbeard.showList, int(show))

        if not show_obj:
            return self._genericMessage(_("Error"), _("Unable to find the specified show"))

        # search and download subtitles
        sickbeard.showQueueScheduler.action.download_subtitles(show_obj, bool(force))

        time.sleep(cpu_presets[sickbeard.CPU_PRESET])

        return self.redirect("/home/displayShow?show=" + str(show_obj.indexerid))

    def updateKODI(self, show=None):
        showName = None
        show_obj = None

        if show:
            show_obj = Show.find(sickbeard.showList, int(show))
            if show_obj:
                showName = urllib.quote_plus(show_obj.name.encode('utf-8'))

        if sickbeard.KODI_UPDATE_ONLYFIRST:
            host = sickbeard.KODI_HOST.split(",")[0].strip()
        else:
            host = sickbeard.KODI_HOST

        if notifiers.kodi_notifier.update_library(showName=showName):
            ui.notifications.message(_("Library update command sent to KODI host(s)): {kodi_hosts}").format(kodi_hosts=host))
        else:
            ui.notifications.error(_("Unable to contact one or more KODI host(s)): {kodi_hosts}").format(kodi_hosts=host))

        if show_obj:
            return self.redirect('/home/displayShow?show=' + str(show_obj.indexerid))
        else:
            return self.redirect('/home/')

    def updatePLEX(self):
        if None is notifiers.plex_notifier.update_library():
            ui.notifications.message(_("Library update command sent to Plex Media Server host: {plex_server}").format
                                     (plex_server=sickbeard.PLEX_SERVER_HOST))
        else:
            ui.notifications.error(_("Unable to contact Plex Media Server host: {plex_server}").format
                                   (plex_server=sickbeard.PLEX_SERVER_HOST))
        return self.redirect('/home/')

    def updateEMBY(self, show=None):
        show_obj = None

        if show:
            show_obj = Show.find(sickbeard.showList, int(show))

        if notifiers.emby_notifier.update_library(show_obj):
            ui.notifications.message(
                _("Library update command sent to Emby host: {emby_host}").format(emby_host=sickbeard.EMBY_HOST))
        else:
            ui.notifications.error(_("Unable to contact Emby host: {emby_host}").format(emby_host=sickbeard.EMBY_HOST))

        if show_obj:
            return self.redirect('/home/displayShow?show=' + str(show_obj.indexerid))
        else:
            return self.redirect('/home/')

    def setStatus(self, show=None, eps=None, status=None, direct=False):

        if not all([show, eps, status]):
            errMsg = _("You must specify a show and at least one episode")
            if direct:
                ui.notifications.error(_('Error'), errMsg)
                return json.dumps({'result': 'error'})
            else:
                return self._genericMessage(_("Error"), errMsg)

        # Use .has_key() since it is overridden for statusStrings in common.py
        if status not in statusStrings:
            errMsg = _("Invalid status")
            if direct:
                ui.notifications.error(_('Error'), errMsg)
                return json.dumps({'result': 'error'})
            else:
                return self._genericMessage(_("Error"), errMsg)

        show_obj = Show.find(sickbeard.showList, int(show))

        if not show_obj:
            errMsg = _("Show not in show list")
            if direct:
                ui.notifications.error(_('Error'), errMsg)
                return json.dumps({'result': 'error'})
            else:
                return self._genericMessage(_("Error"), errMsg)

        segments = {}
        trakt_data = []
        if eps:

            sql_l = []
            for cur_ep in eps.split('|'):

                if not cur_ep:
                    logger.log(u"cur_ep was empty when trying to setStatus", logger.DEBUG)

                logger.log(u"Attempting to set status on episode " + cur_ep + " to " + status, logger.DEBUG)

                epInfo = cur_ep.split('x')

                if not all(epInfo):
                    logger.log(u"Something went wrong when trying to setStatus, epInfo[0]: {0}, epInfo[1]: {1}".format(epInfo[0], epInfo[1]), logger.DEBUG)
                    continue

                ep_obj = show_obj.getEpisode(epInfo[0], epInfo[1])

                if not ep_obj:
                    return self._genericMessage(_("Error"), _("Episode couldn't be retrieved"))

                if int(status) in [WANTED, FAILED]:
                    # figure out what episodes are wanted so we can backlog them
                    if ep_obj.season in segments:
                        segments[ep_obj.season].append(ep_obj)
                    else:
                        segments[ep_obj.season] = [ep_obj]

                with ep_obj.lock:
                    # don't let them mess up UNAIRED episodes
                    if ep_obj.status == UNAIRED:
                        logger.log(u"Refusing to change status of " + cur_ep + " because it is UNAIRED", logger.WARNING)
                        continue

                    if int(status) in Quality.DOWNLOADED and ep_obj.status not in Quality.SNATCHED + \
                            Quality.SNATCHED_PROPER + Quality.SNATCHED_BEST + Quality.DOWNLOADED + [IGNORED] and not ek(os.path.isfile, ep_obj.location):
                        logger.log(u"Refusing to change status of " + cur_ep + " to DOWNLOADED because it's not SNATCHED/DOWNLOADED", logger.WARNING)
                        continue

                    if int(status) == FAILED and ep_obj.status not in Quality.SNATCHED + Quality.SNATCHED_PROPER + \
                            Quality.SNATCHED_BEST + Quality.DOWNLOADED + Quality.ARCHIVED:
                        logger.log(u"Refusing to change status of " + cur_ep + " to FAILED because it's not SNATCHED/DOWNLOADED", logger.WARNING)
                        continue

                    if ep_obj.status in Quality.DOWNLOADED + Quality.ARCHIVED and int(status) == WANTED:
                        logger.log(u"Removing release_name for episode as you want to set a downloaded episode back to wanted, so obviously you want it replaced")
                        ep_obj.release_name = ""

                    ep_obj.status = int(status)

                    # mass add to database
                    sql_l.append(ep_obj.get_sql())

                    trakt_data.append((ep_obj.season, ep_obj.episode))

            data = notifiers.trakt_notifier.trakt_episode_data_generate(trakt_data)

            if sickbeard.USE_TRAKT and sickbeard.TRAKT_SYNC_WATCHLIST:
                if int(status) in [WANTED, FAILED]:
                    logger.log(u"Add episodes, showid: indexerid " + str(show_obj.indexerid) + ", Title " + str(show_obj.name) + " to Watchlist", logger.DEBUG)
                    upd = "add"
                elif int(status) in [IGNORED, SKIPPED] + Quality.DOWNLOADED + Quality.ARCHIVED:
                    logger.log(u"Remove episodes, showid: indexerid " + str(show_obj.indexerid) + ", Title " + str(show_obj.name) + " from Watchlist", logger.DEBUG)
                    upd = "remove"

                if data:
                    notifiers.trakt_notifier.update_watchlist(show_obj, data_episode=data, update=upd)

            if sql_l:
                main_db_con = db.DBConnection()
                main_db_con.mass_action(sql_l)

        if int(status) == WANTED and not show_obj.paused:
            msg = _("Backlog was automatically started for the following seasons of <b>{show_name}</b>").format(show_name=show_obj.name)
            msg += ':<br><ul>'

            for season, segment in segments.iteritems():
                cur_backlog_queue_item = search_queue.BacklogQueueItem(show_obj, segment)
                sickbeard.searchQueueScheduler.action.add_item(cur_backlog_queue_item)

                msg += "<li>" + _("Season") + " " + str(season) + "</li>"
                logger.log(u"Sending backlog for " + show_obj.name + " season " + str(
                    season) + " because some eps were set to wanted")

            msg += "</ul>"

            if segments:
                ui.notifications.message(_("Backlog started"), msg)
        elif int(status) == WANTED and show_obj.paused:
            logger.log(u"Some episodes were set to wanted, but " + show_obj.name + " is paused. Not adding to Backlog until show is unpaused")

        if int(status) == FAILED:
            msg = _("Retrying Search was automatically started for the following season of <b>{show_name}</b>").format(show_name=show_obj.name)
            msg += ':<br><ul>'

            for season, segment in segments.iteritems():
                cur_failed_queue_item = search_queue.FailedQueueItem(show_obj, segment)
                sickbeard.searchQueueScheduler.action.add_item(cur_failed_queue_item)

                msg += "<li>" + _("Season") + " " + str(season) + "</li>"
                logger.log(u"Retrying Search for " + show_obj.name + " season " + str(
                    season) + " because some eps were set to failed")

            msg += "</ul>"

            if segments:
                ui.notifications.message(_("Retry Search started"), msg)

        if direct:
            return json.dumps({'result': 'success'})
        else:
            return self.redirect("/home/displayShow?show=" + show)

    def testRename(self, show=None):

        if not show:
            return self._genericMessage(_("Error"), _("You must specify a show"))

        show_obj = Show.find(sickbeard.showList, int(show))

        if not show_obj:
            return self._genericMessage(_("Error"), _("Show not in show list"))

        try:
            show_obj.location  # @UnusedVariable
        except ShowDirectoryNotFoundException:
            return self._genericMessage(_("Error"), _("Can't rename episodes when the show dir is missing."))

        ep_obj_rename_list = []

        ep_obj_list = show_obj.getAllEpisodes(has_location=True)
        ep_obj_list = [x for x in ep_obj_list if x.location]
        ep_obj_rename_list = []
        for ep_obj in ep_obj_list:
            has_already = False
            for check in ep_obj.relatedEps + [ep_obj]:
                if check in ep_obj_rename_list:
                    has_already = True
                    break
            if not has_already:
                ep_obj_rename_list.append(ep_obj)

        if ep_obj_rename_list:
            ep_obj_rename_list.reverse()

        t = PageTemplate(rh=self, filename="testRename.mako")
        submenu = [{'title': _('Edit'), 'path': 'home/editShow?show={0:d}'.format(show_obj.indexerid), 'icon': 'ui-icon ui-icon-pencil'}]

        return t.render(submenu=submenu, ep_obj_list=ep_obj_rename_list,
                        show=show_obj, title=_('Preview Rename'),
                        header=_('Preview Rename'),
                        controller="home", action="previewRename")

    def doRename(self, show=None, eps=None):
        if not (show and eps):
            return self._genericMessage(_("Error"), _("You must specify a show and at least one episode"))

        show_obj = Show.find(sickbeard.showList, int(show))
        if not show_obj:
            return self._genericMessage(_("Error"), _("Show not in show list"))

        try:
            show_obj.location  # @UnusedVariable
        except ShowDirectoryNotFoundException:
            return self._genericMessage(_("Error"), _("Can't rename episodes when the show dir is missing."))

        if not eps:
            return self.redirect("/home/displayShow?show=" + show)

        main_db_con = db.DBConnection()
        for cur_ep in eps.split('|'):

            epInfo = cur_ep.split('x')

            # this is probably the worst possible way to deal with double eps but I've kinda painted myself into a corner here with this stupid database
            ep_result = main_db_con.select(
                "SELECT location FROM tv_episodes WHERE showid = ? AND season = ? AND episode = ? AND 5=5",
                [show, epInfo[0], epInfo[1]])
            if not ep_result:
                logger.log(u"Unable to find an episode for " + cur_ep + ", skipping", logger.WARNING)
                continue
            related_eps_result = main_db_con.select(
                "SELECT season, episode FROM tv_episodes WHERE location = ? AND episode != ?",
                [ep_result[0]["location"], epInfo[1]]
            )

            root_ep_obj = show_obj.getEpisode(epInfo[0], epInfo[1])
            root_ep_obj.relatedEps = []

            for cur_related_ep in related_eps_result:
                related_ep_obj = show_obj.getEpisode(cur_related_ep["season"], cur_related_ep["episode"])
                if related_ep_obj not in root_ep_obj.relatedEps:
                    root_ep_obj.relatedEps.append(related_ep_obj)

            root_ep_obj.rename()

        return self.redirect("/home/displayShow?show=" + show)

    def searchEpisode(self, show=None, season=None, episode=None, downCurQuality=0):

        # retrieve the episode object and fail if we can't get one
        ep_obj, error_msg = self._getEpisode(show, season, episode)
        if error_msg or not ep_obj:
            return json.dumps({'result': 'failure', 'errorMessage': error_msg})

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

    # ## Returns the current ep_queue_item status for the current viewed show.
    # Possible status: Downloaded, Snatched, etc...
    # Returns {'show': 279530, 'episodes' : ['episode' : 6, 'season' : 1, 'searchstatus' : 'queued', 'status' : 'running', 'quality': '4013']
    def getManualSearchStatus(self, show=None):
        def getEpisodes(searchThread, searchstatus):
            results = []
            show_obj = Show.find(sickbeard.showList, int(searchThread.show.indexerid))

            if not show_obj:
                logger.log(u'No Show Object found for show with indexerID: ' + str(searchThread.show.indexerid), logger.WARNING)
                return results

            if isinstance(searchThread, sickbeard.search_queue.ManualSearchQueueItem):
                results.append({
                    'show': searchThread.show.indexerid,
                    'episode': searchThread.segment.episode,
                    'episodeindexid': searchThread.segment.indexerid,
                    'season': searchThread.segment.season,
                    'searchstatus': searchstatus,
                    'status': statusStrings[searchThread.segment.status],
                    'quality': self.getQualityClass(searchThread.segment),
                    'overview': Overview.overviewStrings[show_obj.getOverview(searchThread.segment.status)]
                })
            else:
                for ep_obj in searchThread.segment:
                    results.append({
                        'show': ep_obj.show.indexerid,
                        'episode': ep_obj.episode,
                        'episodeindexid': ep_obj.indexerid,
                        'season': ep_obj.season,
                        'searchstatus': searchstatus,
                        'status': statusStrings[ep_obj.status],
                        'quality': self.getQualityClass(ep_obj),
                        'overview': Overview.overviewStrings[show_obj.getOverview(ep_obj.status)]
                    })

            return results

        episodes = []

        # Queued Searches
        searchstatus = 'queued'
        for searchThread in sickbeard.searchQueueScheduler.action.get_all_ep_from_queue(show):
            episodes += getEpisodes(searchThread, searchstatus)

        # Running Searches
        searchstatus = 'searching'
        if sickbeard.searchQueueScheduler.action.is_manualsearch_in_progress():
            searchThread = sickbeard.searchQueueScheduler.action.currentItem

            if searchThread.success:
                searchstatus = 'finished'

            episodes += getEpisodes(searchThread, searchstatus)

        # Finished Searches
        searchstatus = 'finished'
        for searchThread in sickbeard.search_queue.MANUAL_SEARCH_HISTORY:
            if not show:
                if not str(searchThread.show.indexerid) == show:
                    continue

            if isinstance(searchThread, sickbeard.search_queue.ManualSearchQueueItem):
                if not [x for x in episodes if x['episodeindexid'] == searchThread.segment.indexerid]:
                    episodes += getEpisodes(searchThread, searchstatus)
            else:
                # ## These are only Failed Downloads/Retry SearchThreadItems.. lets loop through the segement/episodes
                if not [i for i, j in zip(searchThread.segment, episodes) if i.indexerid == j['episodeindexid']]:
                    episodes += getEpisodes(searchThread, searchstatus)

        return json.dumps({'episodes': episodes})

    @staticmethod
    def getQualityClass(ep_obj):
        # return the correct json value

        # Find the quality class for the episode
        ep_status_, ep_quality = Quality.splitCompositeStatus(ep_obj.status)
        if ep_quality in Quality.cssClassStrings:
            quality_class = Quality.cssClassStrings[ep_quality]
        else:
            quality_class = Quality.cssClassStrings[Quality.UNKNOWN]

        return quality_class

    def searchEpisodeSubtitles(self, show=None, season=None, episode=None):
        # retrieve the episode object and fail if we can't get one
        ep_obj, error_msg = self._getEpisode(show, season, episode)
        if error_msg or not ep_obj:
            return json.dumps({'result': 'failure', 'errorMessage': error_msg})

        try:
            new_subtitles = ep_obj.download_subtitles()  # pylint: disable=no-member
        except Exception:
            return json.dumps({'result': 'failure'})

        if new_subtitles:
            new_languages = [subtitle_module.name_from_code(code) for code in new_subtitles]
            status = _('New subtitles downloaded: {new_subtitle_languages}').format(
                new_subtitle_languages=', '.join(new_languages))
        else:
            status = _('No subtitles downloaded')

        ui.notifications.message(ep_obj.show.name, status)  # pylint: disable=no-member
        return json.dumps({'result': status, 'subtitles': ','.join(ep_obj.subtitles)})  # pylint: disable=no-member

    def retrySearchSubtitles(self, show, season, episode, lang):
        # retrieve the episode object and fail if we can't get one
        ep_obj, error_msg = self._getEpisode(show, season, episode)
        if error_msg or not ep_obj:
            return json.dumps({'result': 'failure', 'errorMessage': error_msg})

        try:
            new_subtitles = ep_obj.download_subtitles(force_lang=lang)
        except Exception as ex:
            return json.dumps({'result': 'failure', 'errorMessage': ex.message})

        if new_subtitles:
            new_languages = [subtitle_module.name_from_code(code) for code in new_subtitles]
            status = _('New subtitles downloaded: {new_subtitle_languages}').format(
                new_subtitle_languages=', '.join(new_languages))
        else:
            status = _('No subtitles downloaded')

        ui.notifications.message(ep_obj.show.name, status)
        return json.dumps({'result': status, 'subtitles': ','.join(ep_obj.subtitles)})


    def setSceneNumbering(self, show, indexer, forSeason=None, forEpisode=None, forAbsolute=None, sceneSeason=None,
                          sceneEpisode=None, sceneAbsolute=None):

        # sanitize:
        if forSeason in ('null', ''):
            forSeason = None
        if forEpisode in ('null', ''):
            forEpisode = None
        if forAbsolute in ('null', ''):
            forAbsolute = None
        if sceneSeason in ('null', ''):
            sceneSeason = None
        if sceneEpisode in ('null', ''):
            sceneEpisode = None
        if sceneAbsolute in ('null', ''):
            sceneAbsolute = None

        show_obj = Show.find(sickbeard.showList, int(show))

        if show_obj.is_anime:
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
        if show_obj.is_anime:
            ep_obj, error_msg = self._getEpisode(show, absolute=forAbsolute)
        else:
            ep_obj, error_msg = self._getEpisode(show, forSeason, forEpisode)

        if error_msg or not ep_obj:
            result['success'] = False
            result['errorMessage'] = error_msg
        elif show_obj.is_anime:
            logger.log(u"setAbsoluteSceneNumbering for {0} from {1} to {2}".format(show, forAbsolute, sceneAbsolute), logger.DEBUG)

            show = int(show)
            indexer = int(indexer)
            forAbsolute = int(forAbsolute)
            if sceneAbsolute is not None:
                sceneAbsolute = int(sceneAbsolute)

            set_scene_numbering(show, indexer, absolute_number=forAbsolute, sceneAbsolute=sceneAbsolute)
        else:
            logger.log(u"setEpisodeSceneNumbering for {0} from {1}x{2} to {3}x{4}".format(show, forSeason, forEpisode, sceneSeason, sceneEpisode), logger.DEBUG)

            show = int(show)
            indexer = int(indexer)
            forSeason = int(forSeason)
            forEpisode = int(forEpisode)
            if sceneSeason is not None:
                sceneSeason = int(sceneSeason)
            if sceneEpisode is not None:
                sceneEpisode = int(sceneEpisode)

            set_scene_numbering(show, indexer, season=forSeason, episode=forEpisode, sceneSeason=sceneSeason,
                                sceneEpisode=sceneEpisode)

        if show_obj.is_anime:
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

    def retryEpisode(self, show, season, episode, downCurQuality=0):
        # retrieve the episode object and fail if we can't get one
        ep_obj, error_msg = self._getEpisode(show, season, episode)
        if error_msg or not ep_obj:
            return json.dumps({'result': 'failure', 'errorMessage': error_msg})

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

    @staticmethod
    def fetch_releasegroups(show_name):
        logger.log(u'ReleaseGroups: {0}'.format(show_name), logger.INFO)
        if helpers.set_up_anidb_connection():
            try:
                anime = adba.Anime(sickbeard.ADBA_CONNECTION, name=show_name)
                groups = anime.get_groups()
                logger.log(u'ReleaseGroups: {0}'.format(groups), logger.INFO)
                return json.dumps({'result': 'success', 'groups': groups})
            except AttributeError as error:
                logger.log(u'Unable to get ReleaseGroups: {0}'.format(error), logger.DEBUG)

        return json.dumps({'result': 'failure'})


@route('/IRC(/?.*)')
class HomeIRC(Home):
    def __init__(self, *args, **kwargs):
        super(HomeIRC, self).__init__(*args, **kwargs)

    def index(self, *args_, **kwargs_):

        t = PageTemplate(rh=self, filename="IRC.mako")
        return t.render(topmenu="system", header=_("IRC"), title=_("IRC"), controller="IRC", action="index")


@route('/news(/?.*)')
class HomeNews(Home):
    def __init__(self, *args, **kwargs):
        super(HomeNews, self).__init__(*args, **kwargs)

    def index(self, *args_, **kwargs_):
        try:
            news = sickbeard.versionCheckScheduler.action.check_for_new_news()
        except Exception:
            logger.log(u'Could not load news from repo, giving a link!', logger.DEBUG)
            news = _('Could not load news from the repo. [Click here for news.md])({news_url})').format(news_url=sickbeard.NEWS_URL)

        sickbeard.NEWS_LAST_READ = sickbeard.NEWS_LATEST
        sickbeard.NEWS_UNREAD = 0
        sickbeard.save_config()

        t = PageTemplate(rh=self, filename="markdown.mako")
        data = markdown2.markdown(news if news else _("The was a problem connecting to github, please refresh and try again"), extras=['header-ids'])

        return t.render(title=_("News"), header=_("News"), topmenu="system", data=data, controller="news", action="index")


@route('/changes(/?.*)')
class HomeChangeLog(Home):
    def __init__(self, *args, **kwargs):
        super(HomeChangeLog, self).__init__(*args, **kwargs)

    def index(self, *args_, **kwargs_):
        try:
            changes = helpers.getURL('http://sickrage.github.io/sickrage-news/CHANGES.md', session=helpers.make_session(), returns='text')
        except Exception:
            logger.log(u'Could not load changes from repo, giving a link!', logger.DEBUG)
            changes = _('Could not load changes from the repo. [Click here for CHANGES.md]({changes_url})').format(changes_url='http://sickrage.github.io/sickrage-news/CHANGES.md')

        t = PageTemplate(rh=self, filename="markdown.mako")
        data = markdown2.markdown(changes if changes else _("The was a problem connecting to github, please refresh and try again"), extras=['header-ids'])

        return t.render(title=_("Changelog"), header=_("Changelog"), topmenu="system", data=data, controller="changes", action="index")


@route('/home/postprocess(/?.*)')
class HomePostProcess(Home):
    def __init__(self, *args, **kwargs):
        super(HomePostProcess, self).__init__(*args, **kwargs)

    def index(self, *args_, **kwargs_):
        t = PageTemplate(rh=self, filename="home_postprocess.mako")
        return t.render(title=_('Post Processing'), header=_('Post Processing'), topmenu='home', controller="home", action="postProcess")

    def processEpisode(self, proc_dir=None, nzbName=None, quiet=None, process_method=None, force=None,
                       is_priority=None, delete_on="0", failed="0", proc_type="auto", force_next=False, *args_, **kwargs):

        mode = kwargs.get('type', proc_type)
        process_path = ss(kwargs.get('dir', proc_dir))
        if not process_path:
            return self.redirect("/home/postprocess/")

        release_name = ss(nzbName) if nzbName else nzbName

        result = sickbeard.postProcessorTaskScheduler.action.add_item(
            process_path, release_name, method=process_method, force=force,
            is_priority=is_priority, delete=delete_on, failed=failed, mode=mode,
            force_next=force_next
        )

        if config.checkbox_to_value(quiet):
            return result

        result = result.replace("\n", "<br>\n")
        return self._genericMessage("Postprocessing results", result)


@route('/addShows(/?.*)')
class HomeAddShows(Home):
    def __init__(self, *args, **kwargs):
        super(HomeAddShows, self).__init__(*args, **kwargs)

    def index(self, *args_, **kwargs_):
        t = PageTemplate(rh=self, filename="addShows.mako")
        return t.render(title=_('Add Shows'), header=_('Add Shows'), topmenu='home', controller="addShows", action="index")

    @staticmethod
    def getIndexerLanguages():
        result = sickbeard.indexerApi().config['valid_languages']

        return json.dumps({'results': result})

    @staticmethod
    def sanitizeFileName(name):
        return sanitize_filename(name)

    @staticmethod
    def searchIndexersForShowName(search_term, lang=None, indexer=None):
        if not lang or lang == 'null':
            lang = sickbeard.INDEXER_DEFAULT_LANGUAGE

        search_term = search_term.encode('utf-8')

        searchTerms = [search_term]

        # If search term ends with what looks like a year, enclose it in ()
        matches = re.match(r'^(.+ |)([12][0-9]{3})$', search_term)
        if matches:
            searchTerms.append("{0}({1})".format(matches.group(1), matches.group(2)))

        for searchTerm in searchTerms:
            # If search term begins with an article, let's also search for it without
            matches = re.match(r'^(?:a|an|the) (.+)$', searchTerm, re.I)
            if matches:
                searchTerms.append(matches.group(1))

        results = {}
        final_results = []

        # Query Indexers for each search term and build the list of results
        for indexer in sickbeard.indexerApi().indexers if not int(indexer) else [int(indexer)]:
            lINDEXER_API_PARMS = sickbeard.indexerApi(indexer).api_params.copy()
            lINDEXER_API_PARMS['language'] = lang or sickbeard.INDEXER_DEFAULT_LANGUAGE
            lINDEXER_API_PARMS['custom_ui'] = classes.AllShowsListUI
            t = sickbeard.indexerApi(indexer).indexer(**lINDEXER_API_PARMS)

            logger.log(u"Searching for Show with searchterm(s): {0} on Indexer: {1}".format(
                searchTerms, sickbeard.indexerApi(indexer).name), logger.DEBUG)
            for searchTerm in searchTerms:
                try:
                    indexerResults = t[searchTerm]
                except Exception:
                    # logger.log(traceback.format_exc(), logger.ERROR)
                    continue

                # add search results
                results.setdefault(indexer, []).extend(indexerResults)

        for i, shows in results.iteritems():
            final_results.extend({(sickbeard.indexerApi(i).name, i, sickbeard.indexerApi(i).config["show_url"], int(show['id']),
                                   show['seriesname'], show['firstaired']) for show in shows})

        lang_id = sickbeard.indexerApi().config['langabbv_to_id'][lang]
        return json.dumps({'results': final_results, 'langid': lang_id})

    def massAddTable(self, rootDir=None):
        t = PageTemplate(rh=self, filename="home_massAddTable.mako")

        if not rootDir:
            return _("No folders selected.")
        elif not isinstance(rootDir, list):
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

        main_db_con = db.DBConnection()
        for root_dir in root_dirs:
            try:
                file_list = ek(os.listdir, root_dir)
            except Exception:
                continue

            for cur_file in file_list:

                try:
                    cur_path = ek(os.path.normpath, ek(os.path.join, root_dir, cur_file))
                    if not ek(os.path.isdir, cur_path):
                        continue
                except Exception:
                    continue

                cur_dir = {
                    'dir': cur_path,
                    'display_dir': '<b>' + ek(os.path.dirname, cur_path) + os.sep + '</b>' + ek(
                        os.path.basename,
                        cur_path),
                }

                # see if the folder is in KODI already
                dirResults = main_db_con.select("SELECT indexer_id FROM tv_shows WHERE location = ? LIMIT 1", [cur_path])

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
                            (show_name_, idxr, i) = helpers.searchIndexerForShowID(show_name, indexer, indexer_id)

                            # set indexer and indexer_id from found info
                            if not indexer and idxr:
                                indexer = idxr

                            if not indexer_id and i:
                                indexer_id = i

                cur_dir['existing_info'] = (indexer_id, show_name, indexer)

                if indexer_id and Show.find(sickbeard.showList, indexer_id):
                    cur_dir['added_already'] = True
        return t.render(dirList=dir_list)

    def newShow(self, show_to_add=None, other_shows=None, search_string=None):
        """
        Display the new show page which collects a tvdb id, folder, and extra options and
        posts them to addNewShow
        """
        t = PageTemplate(rh=self, filename="addShows_newShow.mako")

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
            default_show_name = re.sub(r' \(\d{4}\)', '',
                                       ek(os.path.basename, ek(os.path.normpath, show_dir)).replace('.', ' '))
        else:
            default_show_name = show_name

        # carry a list of other dirs if given
        if not other_shows:
            other_shows = []
        elif not isinstance(other_shows, list):
            other_shows = [other_shows]

        provided_indexer_id = int(indexer_id or 0)
        provided_indexer_name = show_name

        provided_indexer = int(indexer or sickbeard.INDEXER_DEFAULT)

        return t.render(
            enable_anime_options=True, use_provided_info=use_provided_info,
            default_show_name=default_show_name, other_shows=other_shows,
            provided_show_dir=show_dir, provided_indexer_id=provided_indexer_id,
            provided_indexer_name=provided_indexer_name, provided_indexer=provided_indexer,
            indexers=sickbeard.indexerApi().indexers, whitelist=[], blacklist=[], groups=[],
            title=_('New Show'), header=_('New Show'), topmenu='home',
            controller="addShows", action="newShow"
        )

    def trendingShows(self, traktList=None):
        """
        Display the new show page which collects a tvdb id, folder, and extra options and
        posts them to addNewShow
        """
        if not traktList:
            traktList = ""

        traktList = traktList.lower()

        if traktList == "trending":
            page_title = _("Trending Shows")
        elif traktList == "popular":
            page_title = _("Popular Shows")
        elif traktList == "anticipated":
            page_title = _("Most Anticipated Shows")
        elif traktList == "collected":
            page_title = "Most Collected Shows"
        elif traktList == "watched":
            page_title = "Most Watched Shows"
        elif traktList == "played":
            page_title = "Most Played Shows"
        elif traktList == "recommended":
            page_title = "Recommended Shows"
        elif traktList == "newshow":
            page_title = _("New Shows")
        elif traktList == "newseason":
            page_title = _("Season Premieres")
        else:
            page_title = _("Most Anticipated Shows")

        t = PageTemplate(rh=self, filename="addShows_trendingShows.mako")
        return t.render(title=page_title, header=page_title, enable_anime_options=False,
                        traktList=traktList, controller="addShows", action="trendingShows")

    def getTrendingShows(self, traktList=None):
        """
        Display the new show page which collects a tvdb id, folder, and extra options and
        posts them to addNewShow
        """
        t = PageTemplate(rh=self, filename="trendingShows.mako")
        if not traktList:
            traktList = ""

        traktList = traktList.lower()

        if traktList == "trending":
            page_url = "shows/trending"
        elif traktList == "popular":
            page_url = "shows/popular"
        elif traktList == "anticipated":
            page_url = "shows/anticipated"
        elif traktList == "collected":
            page_url = "shows/collected"
        elif traktList == "watched":
            page_url = "shows/watched"
        elif traktList == "played":
            page_url = "shows/played"
        elif traktList == "recommended":
            page_url = "recommendations/shows"
        elif traktList == "newshow":
            page_url = 'calendars/all/shows/new/{0}/30'.format(datetime.date.today().strftime("%Y-%m-%d"))
        elif traktList == "newseason":
            page_url = 'calendars/all/shows/premieres/{0}/30'.format(datetime.date.today().strftime("%Y-%m-%d"))
        else:
            page_url = "shows/anticipated"

        trending_shows = []

        trakt_api = TraktAPI(sickbeard.SSL_VERIFY, sickbeard.TRAKT_TIMEOUT)

        try:
            not_liked_show = ""
            if sickbeard.TRAKT_ACCESS_TOKEN != '':
                library_shows = trakt_api.traktRequest("sync/collection/shows?extended=full") or []
                if sickbeard.TRAKT_BLACKLIST_NAME:
                    not_liked_show = trakt_api.traktRequest("users/" + sickbeard.TRAKT_USERNAME + "/lists/" + sickbeard.TRAKT_BLACKLIST_NAME + "/items") or []
                else:
                    logger.log(u"Trakt blacklist name is empty", logger.DEBUG)

            if traktList not in ["recommended", "newshow", "newseason"]:
                limit_show = "?limit=" + str(100 + len(not_liked_show)) + "&"
            else:
                limit_show = "?"

            shows = trakt_api.traktRequest(page_url + limit_show + "extended=full,images") or []

            if sickbeard.TRAKT_ACCESS_TOKEN != '':
                library_shows = trakt_api.traktRequest("sync/collection/shows?extended=full") or []

            for show in shows:
                try:
                    if 'show' not in show:
                        show['show'] = show

                    if not Show.find(sickbeard.showList, [int(show['show']['ids']['tvdb'])]):
                        if sickbeard.TRAKT_ACCESS_TOKEN != '':
                            if show['show']['ids']['tvdb'] not in (lshow['show']['ids']['tvdb'] for lshow in library_shows):
                                if not_liked_show:
                                    if show['show']['ids']['tvdb'] not in (show['show']['ids']['tvdb'] for show in not_liked_show if show['type'] == 'show'):
                                        trending_shows += [show]
                                else:
                                    trending_shows += [show]
                        else:
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
            logger.log(u"Could not connect to Trakt service: {0}".format(ex(e)), logger.WARNING)

        return t.render(blacklist=blacklist, trending_shows=trending_shows)

    def popularShows(self):
        """
        Fetches data from IMDB to show a list of popular shows.
        """
        t = PageTemplate(rh=self, filename="addShows_popularShows.mako")
        e = None

        try:
            popular_shows = imdb_popular.fetch_popular_shows()
        except Exception as e:
            # print traceback.format_exc()
            popular_shows = None

        return t.render(title=_("Popular Shows"), header=_("Popular Shows"),
                        popular_shows=popular_shows, imdb_exception=e,
                        topmenu="home",
                        controller="addShows", action="popularShows")

    def addShowToBlacklist(self, indexer_id):
        # URL parameters
        data = {'shows': [{'ids': {'tvdb': indexer_id}}]}

        trakt_api = TraktAPI(sickbeard.SSL_VERIFY, sickbeard.TRAKT_TIMEOUT)

        trakt_api.traktRequest("users/" + sickbeard.TRAKT_USERNAME + "/lists/" + sickbeard.TRAKT_BLACKLIST_NAME + "/items", data, method='POST')

        return self.redirect('/addShows/trendingShows/')

    def existingShows(self):
        """
        Prints out the page to add existing shows from a root dir
        """
        t = PageTemplate(rh=self, filename="addShows_addExistingShow.mako")
        return t.render(enable_anime_options=False, title=_('Existing Show'),
                        header=_('Existing Show'), topmenu="home",
                        controller="addShows", action="addExistingShow")

    def addShowByID(  # pylint: disable=unused-argument
            self, indexer_id, show_name, indexer="TVDB", which_series=None,
            indexer_lang=None, root_dir=None, default_status=None,
            quality_preset=None, any_qualities=None, best_qualities=None,
            flatten_folders=None, subtitles=None, full_show_path=None,
            other_shows=None, skip_show=None, provided_indexer=None,
            anime=None, scene=None, blacklist=None, whitelist=None,
            default_status_after=None, default_flatten_folders=None,
            configure_show_options=None):

        if indexer != "TVDB":
            tvdb_id = helpers.getTVDBFromID(indexer_id, indexer.upper())
            if not tvdb_id:
                logger.log(u"Unable to to find tvdb ID to add {0}".format(show_name))
                ui.notifications.error(
                    "Unable to add {0}".format(show_name),
                    "Could not add {0}.  We were unable to locate the tvdb id at this time.".format(show_name)
                )
                return

            indexer_id = try_int(tvdb_id, None)

        if Show.find(sickbeard.showList, int(indexer_id)):
            return

        # Sanitize the paramater anyQualities and bestQualities. As these would normally be passed as lists
        any_qualities = any_qualities.split(',') if any_qualities else []
        best_qualities = best_qualities.split(',') if best_qualities else []

        # If configure_show_options is enabled let's use the provided settings
        configure_show_options = config.checkbox_to_value(configure_show_options)

        if configure_show_options:
            # prepare the inputs for passing along
            scene = config.checkbox_to_value(scene)
            anime = config.checkbox_to_value(anime)
            flatten_folders = config.checkbox_to_value(flatten_folders)
            subtitles = config.checkbox_to_value(subtitles)

            if whitelist:
                whitelist = short_group_names(whitelist)
            if blacklist:
                blacklist = short_group_names(blacklist)

            if not any_qualities:
                any_qualities = []

            if not best_qualities or try_int(quality_preset, None):
                best_qualities = []

            if not isinstance(any_qualities, list):
                any_qualities = [any_qualities]

            if not isinstance(best_qualities, list):
                best_qualities = [best_qualities]

            quality = Quality.combineQualities([int(q) for q in any_qualities], [int(q) for q in best_qualities])

            location = root_dir

        else:
            default_status = sickbeard.STATUS_DEFAULT
            quality = sickbeard.QUALITY_DEFAULT
            flatten_folders = sickbeard.FLATTEN_FOLDERS_DEFAULT
            subtitles = sickbeard.SUBTITLES_DEFAULT
            anime = sickbeard.ANIME_DEFAULT
            scene = sickbeard.SCENE_DEFAULT
            default_status_after = sickbeard.STATUS_DEFAULT_AFTER

            if sickbeard.ROOT_DIRS:
                root_dirs = sickbeard.ROOT_DIRS.split('|')
                location = root_dirs[int(root_dirs[0]) + 1]
            else:
                location = None

        if not location:
            logger.log(u"There was an error creating the show, no root directory setting found")
            return _("No root directories setup, please go back and add one.")

        show_name = get_showname_from_indexer(1, indexer_id)
        show_dir = None

        # add the show
        sickbeard.showQueueScheduler.action.addShow(1, int(indexer_id), show_dir, int(default_status), quality, flatten_folders,
                                                    indexer_lang, subtitles, anime, scene, None, blacklist, whitelist,
                                                    int(default_status_after), root_dir=location)

        ui.notifications.message(_('Show added'), _('Adding the specified show {show_name}').format(show_name=show_name))

        # done adding show
        return self.redirect('/home/')

    def addNewShow(self, whichSeries=None, indexerLang=None, rootDir=None, defaultStatus=None,
                   quality_preset=None, anyQualities=None, bestQualities=None, flatten_folders=None, subtitles=None,
                   subtitles_sr_metadata=None, fullShowPath=None, other_shows=None, skipShow=None, providedIndexer=None,
                   anime=None, scene=None, blacklist=None, whitelist=None, defaultStatusAfter=None):
        """
        Receive tvdb id, dir, and other options and create a show from them. If extra show dirs are
        provided then it forwards back to newShow, if not it goes to /home.
        """

        if not indexerLang:
            indexerLang = sickbeard.INDEXER_DEFAULT_LANGUAGE

        # grab our list of other dirs if given
        if not other_shows:
            other_shows = []
        elif not isinstance(other_shows, list):
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
            return _("Missing params, no Indexer ID or folder: {show_to_add} and {root_dir}/{show_path}").format(
                show_to_add=whichSeries, root_dir=rootDir, show_path=fullShowPath)

        # figure out what show we're adding and where
        series_pieces = whichSeries.split('|')
        if (whichSeries and rootDir) or (whichSeries and fullShowPath and len(series_pieces) > 1):
            if len(series_pieces) < 6:
                logger.log(u"Unable to add show due to show selection. Not anough arguments: {0}".format((repr(series_pieces))),
                           logger.ERROR)
                ui.notifications.error(_("Unknown error. Unable to add show due to problem with show selection."))
                return self.redirect('/addShows/existingShows/')

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
            show_name = ek(os.path.basename, ek(os.path.normpath, fullShowPath))

        # use the whole path if it's given, or else append the show name to the root dir to get the full show path
        if fullShowPath:
            show_dir = ek(os.path.normpath, fullShowPath)
        else:
            show_dir = ek(os.path.join, rootDir, sanitize_filename(show_name))

        # blanket policy - if the dir exists you should have used "add existing show" numbnuts
        if ek(os.path.isdir, show_dir) and not fullShowPath:
            ui.notifications.error(_("Unable to add show"), _("Folder {show_dir} exists already").format(show_dir=show_dir))
            return self.redirect('/addShows/existingShows/')

        # don't create show dir if config says not to
        if sickbeard.ADD_SHOWS_WO_DIR:
            logger.log(u"Skipping initial creation of " + show_dir + " due to config.ini setting")
        else:
            dir_exists = helpers.makeDir(show_dir)
            if not dir_exists:
                logger.log(u"Unable to create the folder " + show_dir + ", can't add the show", logger.ERROR)
                ui.notifications.error(_("Unable to add show"),
                                       _("Unable to create the folder {show_dir}, can't add the show").format(show_dir=show_dir))
                # Don't redirect to default page because user wants to see the new show
                return self.redirect("/home/")
            else:
                helpers.chmodAsParent(show_dir)

        # prepare the inputs for passing along
        scene = config.checkbox_to_value(scene)
        anime = config.checkbox_to_value(anime)
        flatten_folders = config.checkbox_to_value(flatten_folders)
        subtitles = config.checkbox_to_value(subtitles)
        subtitles_sr_metadata = config.checkbox_to_value(subtitles_sr_metadata)

        if whitelist:
            whitelist = short_group_names(whitelist)
        if blacklist:
            blacklist = short_group_names(blacklist)

        if not anyQualities:
            anyQualities = []
        if not bestQualities or try_int(quality_preset, None):
            bestQualities = []
        if not isinstance(anyQualities, list):
            anyQualities = [anyQualities]
        if not isinstance(bestQualities, list):
            bestQualities = [bestQualities]
        newQuality = Quality.combineQualities([int(q) for q in anyQualities], [int(q) for q in bestQualities])

        # add the show
        sickbeard.showQueueScheduler.action.addShow(indexer, indexer_id, show_dir, int(defaultStatus), newQuality,
                                                    flatten_folders, indexerLang, subtitles, subtitles_sr_metadata,
                                                    anime, scene, None, blacklist, whitelist, int(defaultStatusAfter))
        ui.notifications.message(_('Show added'), _('Adding the specified show into {show_dir}').format(show_dir=show_dir))

        return finishAddShow()

    @staticmethod
    def split_extra_show(extra_show):
        if not extra_show:
            return None, None, None, None
        split_vals = extra_show.split('|')
        if len(split_vals) < 4:
            indexer = split_vals[0]
            show_dir = split_vals[1]
            return indexer, show_dir, None, None
        indexer = split_vals[0]
        show_dir = split_vals[1]
        indexer_id = split_vals[2]
        show_name = '|'.join(split_vals[3:])

        return indexer, show_dir, indexer_id, show_name

    def addExistingShows(self, shows_to_add, promptForSettings, **kwargs):
        """
        Receives a dir list and add them. Adds the ones with given TVDB IDs first, then forwards
        along to the newShow page.
        """

        # grab a list of other shows to add, if provided
        if not shows_to_add:
            shows_to_add = []
        elif not isinstance(shows_to_add, list):
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
            if '|' not in cur_dir:
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
                sickbeard.showQueueScheduler.action.addShow(
                    indexer, indexer_id, show_dir,
                    default_status=sickbeard.STATUS_DEFAULT,
                    quality=sickbeard.QUALITY_DEFAULT,
                    flatten_folders=sickbeard.FLATTEN_FOLDERS_DEFAULT,
                    subtitles=sickbeard.SUBTITLES_DEFAULT,
                    anime=sickbeard.ANIME_DEFAULT,
                    scene=sickbeard.SCENE_DEFAULT,
                    default_status_after=sickbeard.STATUS_DEFAULT_AFTER
                )
                num_added += 1

        if num_added:
            ui.notifications.message(_("Shows Added"),
                                     _("Automatically added {num_shows} from their existing metadata files").format(num_shows=str(num_added)))

        # if we're done then go home
        if not dirs_only:
            return self.redirect('/home/')

        # for the remaining shows we need to prompt for each one, so forward this on to the newShow page
        return self.newShow(dirs_only[0], dirs_only[1:])


@route('/manage(/?.*)')
class Manage(Home, WebRoot):
    def __init__(self, *args, **kwargs):
        super(Manage, self).__init__(*args, **kwargs)

    def index(self, *args_, **kwargs_):
        t = PageTemplate(rh=self, filename="manage.mako")
        return t.render(title=_('Mass Update'), header=_('Mass Update'), topmenu='manage', controller="manage", action="index")

    @staticmethod
    def showEpisodeStatuses(indexer_id, whichStatus):
        status_list = [int(whichStatus)]
        if status_list[0] == SNATCHED:
            status_list = Quality.SNATCHED + Quality.SNATCHED_PROPER + Quality.SNATCHED_BEST

        main_db_con = db.DBConnection()
        cur_show_results = main_db_con.select(
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

        t = PageTemplate(rh=self, filename="manage_episodeStatuses.mako")

        # if we have no status then this is as far as we need to go
        if not status_list:
            return t.render(
                title=_("Episode Overview"), header=_("Episode Overview"),
                topmenu="manage", show_names=None, whichStatus=whichStatus,
                ep_counts=None, sorted_show_ids=None,
                controller="manage", action="episodeStatuses")

        main_db_con = db.DBConnection()
        status_results = main_db_con.select(
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

        return t.render(
            title=_("Episode Overview"), header=_("Episode Overview"),
            topmenu='manage', whichStatus=whichStatus,
            show_names=show_names, ep_counts=ep_counts, sorted_show_ids=sorted_show_ids,
            controller="manage", action="episodeStatuses")

    def changeEpisodeStatuses(self, oldStatus, newStatus, *args_, **kwargs):
        status_list = [int(oldStatus)]
        if status_list[0] == SNATCHED:
            status_list = Quality.SNATCHED + Quality.SNATCHED_PROPER + Quality.SNATCHED_BEST

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

        main_db_con = db.DBConnection()
        for cur_indexer_id in to_change:

            # get a list of all the eps we want to change if they just said "all"
            if 'all' in to_change[cur_indexer_id]:
                all_eps_results = main_db_con.select(
                    "SELECT season, episode FROM tv_episodes WHERE status IN (" + ','.join(
                        ['?'] * len(status_list)) + ") AND season != 0 AND showid = ?",
                    status_list + [cur_indexer_id])
                all_eps = [str(x["season"]) + 'x' + str(x["episode"]) for x in all_eps_results]
                to_change[cur_indexer_id] = all_eps

            self.setStatus(cur_indexer_id, '|'.join(to_change[cur_indexer_id]), newStatus, direct=True)

        return self.redirect('/manage/episodeStatuses/')

    @staticmethod
    def showSubtitleMissed(indexer_id, whichSubs):
        main_db_con = db.DBConnection()
        cur_show_results = main_db_con.select(
            "SELECT season, episode, name, subtitles FROM tv_episodes WHERE showid = ? AND season != 0 AND (status LIKE '%4' OR status LIKE '%6') and location != ''",
            [int(indexer_id)])

        result = {}
        for cur_result in cur_show_results:
            if whichSubs == 'all':
                if not frozenset(subtitle_module.wanted_languages()).difference(cur_result["subtitles"].split(',')):
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
        t = PageTemplate(rh=self, filename="manage_subtitleMissed.mako")

        if not whichSubs:
            return t.render(whichSubs=whichSubs, title=_('Episode Overview'),
                            header=_('Episode Overview'), topmenu='manage',
                            show_names=None, ep_counts=None, sorted_show_ids=None,
                            controller="manage", action="subtitleMissed")

        main_db_con = db.DBConnection()
        status_results = main_db_con.select(
            "SELECT show_name, tv_shows.indexer_id as indexer_id, tv_episodes.subtitles subtitles " +
            "FROM tv_episodes, tv_shows " +
            "WHERE tv_shows.subtitles = 1 AND (tv_episodes.status LIKE '%4' OR tv_episodes.status LIKE '%6') AND tv_episodes.season != 0 " +
            "AND tv_episodes.location != '' AND tv_episodes.showid = tv_shows.indexer_id ORDER BY show_name")

        ep_counts = {}
        show_names = {}
        sorted_show_ids = []
        for cur_status_result in status_results:
            if whichSubs == 'all':
                if not frozenset(subtitle_module.wanted_languages()).difference(cur_status_result["subtitles"].split(',')):
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
                        title=_('Missing Subtitles'), header=_('Missing Subtitles'), topmenu='manage',
                        controller="manage", action="subtitleMissed")

    def downloadSubtitleMissed(self, *args_, **kwargs):
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
                main_db_con = db.DBConnection()
                all_eps_results = main_db_con.select(
                    "SELECT season, episode FROM tv_episodes WHERE (status LIKE '%4' OR status LIKE '%6') AND season != 0 AND showid = ? AND location != ''",
                    [cur_indexer_id])
                to_download[cur_indexer_id] = [str(x["season"]) + 'x' + str(x["episode"]) for x in all_eps_results]

            for epResult in to_download[cur_indexer_id]:
                season, episode = epResult.split('x')

                show = Show.find(sickbeard.showList, int(cur_indexer_id))
                show.getEpisode(season, episode).download_subtitles()

        return self.redirect('/manage/subtitleMissed/')

    def backlogShow(self, indexer_id):
        show_obj = Show.find(sickbeard.showList, int(indexer_id))

        if show_obj:
            sickbeard.backlogSearchScheduler.action.searchBacklog([show_obj])

        return self.redirect("/manage/backlogOverview/")

    def backlogOverview(self):
        t = PageTemplate(rh=self, filename="manage_backlogOverview.mako")

        showCounts = {}
        showCats = {}
        showSQLResults = {}

        main_db_con = db.DBConnection()
        for curShow in sickbeard.showList:

            epCounts = {
                Overview.SKIPPED: 0,
                Overview.WANTED: 0,
                Overview.QUAL: 0,
                Overview.GOOD: 0,
                Overview.UNAIRED: 0,
                Overview.SNATCHED: 0,
                Overview.SNATCHED_PROPER: 0,
                Overview.SNATCHED_BEST: 0
            }
            epCats = {}

            sql_results = main_db_con.select(
                "SELECT status, season, episode, name, airdate FROM tv_episodes WHERE tv_episodes.season IS NOT NULL "
                "AND tv_episodes.showid IN (SELECT tv_shows.indexer_id FROM tv_shows WHERE tv_shows.indexer_id = ? "
                "AND paused = 0) ORDER BY tv_episodes.season DESC, tv_episodes.episode DESC",
                [curShow.indexerid])

            for curResult in sql_results:
                curEpCat = curShow.getOverview(curResult["status"])
                if curEpCat:
                    epCats[u'{ep}'.format(ep=episode_num(curResult['season'], curResult['episode']))] = curEpCat
                    epCounts[curEpCat] += 1

            showCounts[curShow.indexerid] = epCounts
            showCats[curShow.indexerid] = epCats
            showSQLResults[curShow.indexerid] = sql_results

        return t.render(
            showCounts=showCounts, showCats=showCats,
            showSQLResults=showSQLResults, controller='manage',
            action='backlogOverview', title=_('Backlog Overview'),
            header=_('Backlog Overview'), topmenu='manage')

    def massEdit(self, toEdit=None):
        t = PageTemplate(rh=self, filename="manage_massEdit.mako")

        if not toEdit:
            return self.redirect("/manage/")

        showIDs = toEdit.split("|")
        showList = []
        showNames = []
        for curID in showIDs:
            curID = int(curID)
            show_obj = Show.find(sickbeard.showList, curID)
            if show_obj:
                showList.append(show_obj)
                showNames.append(show_obj.name)

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

            cur_root_dir = ek(os.path.dirname, curShow._location)  # pylint: disable=protected-access
            if cur_root_dir not in root_dir_list:
                root_dir_list.append(cur_root_dir)

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

        return t.render(showList=toEdit, showNames=showNames, default_ep_status_value=default_ep_status_value,
                        paused_value=paused_value, anime_value=anime_value, flatten_folders_value=flatten_folders_value,
                        quality_value=quality_value, subtitles_value=subtitles_value, scene_value=scene_value, sports_value=sports_value,
                        air_by_date_value=air_by_date_value, root_dir_list=root_dir_list, title=_('Mass Edit'), header=_('Mass Edit'), topmenu='manage')

    def massEditSubmit(self, paused=None, default_ep_status=None,
                       anime=None, sports=None, scene=None, flatten_folders=None, quality_preset=None,
                       subtitles=None, air_by_date=None, anyQualities=None, bestQualities=None, toEdit=None, *args_,
                       **kwargs):
        dir_map = {}
        for cur_arg in filter(lambda x: x.startswith('orig_root_dir_'), kwargs):
            dir_map[kwargs[cur_arg]] = ek(unicode, kwargs[cur_arg.replace('orig_root_dir_', 'new_root_dir_')], 'utf-8')

        showIDs = toEdit.split("|")
        errors = []
        for curShow in showIDs:
            curErrors = []
            show_obj = Show.find(sickbeard.showList, int(curShow))
            if not show_obj:
                continue

            cur_root_dir = ek(os.path.dirname, show_obj._location)  # pylint: disable=protected-access
            cur_show_dir = ek(os.path.basename, show_obj._location)  # pylint: disable=protected-access
            if cur_root_dir in dir_map and cur_root_dir != dir_map[cur_root_dir]:
                new_show_dir = ek(os.path.join, dir_map[cur_root_dir], cur_show_dir)
                logger.log(
                    u"For show " + show_obj.name + " changing dir from " + show_obj._location + " to " + new_show_dir)  # pylint: disable=protected-access
            else:
                new_show_dir = show_obj._location  # pylint: disable=protected-access

            if paused == 'keep':
                new_paused = show_obj.paused
            else:
                new_paused = True if paused == 'enable' else False
            new_paused = 'on' if new_paused else 'off'

            if default_ep_status == 'keep':
                new_default_ep_status = show_obj.default_ep_status
            else:
                new_default_ep_status = default_ep_status

            if anime == 'keep':
                new_anime = show_obj.anime
            else:
                new_anime = True if anime == 'enable' else False
            new_anime = 'on' if new_anime else 'off'

            if sports == 'keep':
                new_sports = show_obj.sports
            else:
                new_sports = True if sports == 'enable' else False
            new_sports = 'on' if new_sports else 'off'

            if scene == 'keep':
                new_scene = show_obj.is_scene
            else:
                new_scene = True if scene == 'enable' else False
            new_scene = 'on' if new_scene else 'off'

            if air_by_date == 'keep':
                new_air_by_date = show_obj.air_by_date
            else:
                new_air_by_date = True if air_by_date == 'enable' else False
            new_air_by_date = 'on' if new_air_by_date else 'off'

            if flatten_folders == 'keep':
                new_flatten_folders = show_obj.flatten_folders
            else:
                new_flatten_folders = True if flatten_folders == 'enable' else False
            new_flatten_folders = 'on' if new_flatten_folders else 'off'

            if subtitles == 'keep':
                new_subtitles = show_obj.subtitles
            else:
                new_subtitles = True if subtitles == 'enable' else False

            new_subtitles = 'on' if new_subtitles else 'off'

            if quality_preset == 'keep':
                anyQualities, bestQualities = Quality.splitQuality(show_obj.quality)
            elif try_int(quality_preset, None):
                bestQualities = []

            exceptions_list = []

            curErrors += self.editShow(curShow, new_show_dir, anyQualities,
                                       bestQualities, exceptions_list,
                                       defaultEpStatus=new_default_ep_status,
                                       flatten_folders=new_flatten_folders,
                                       paused=new_paused, sports=new_sports,
                                       subtitles=new_subtitles, anime=new_anime,
                                       scene=new_scene, air_by_date=new_air_by_date,
                                       directCall=True)

            if curErrors:
                logger.log(u"Errors: " + str(curErrors), logger.ERROR)
                errors.append('<b>{0}:</b>\n<ul>'.format(show_obj.name) + ' '.join(
                    ['<li>{0}</li>'.format(error) for error in curErrors]) + "</ul>")

        if len(errors) > 0:
            ui.notifications.error(_('{num_errors:d} error{plural} while saving changes:').format(num_errors=len(errors), plural="" if len(errors) == 1 else "s"),
                                   " ".join(errors))

        return self.redirect("/manage/")

    def massUpdate(self, toUpdate=None, toRefresh=None, toRename=None, toDelete=None, toRemove=None, toMetadata=None,
                   toSubtitle=None):

        toUpdate = toUpdate.split('|') if toUpdate else []
        toRefresh = toRefresh.split('|') if toRefresh else []
        toRename = toRename.split('|') if toRename else []
        toSubtitle = toSubtitle.split('|') if toSubtitle else []
        toDelete = toDelete.split('|') if toDelete else []
        toRemove = toRemove.split('|') if toRemove else []
        toMetadata = toMetadata.split('|') if toMetadata else []

        errors = []
        refreshes = []
        updates = []
        renames = []
        subtitles = []

        for curShowID in set(toUpdate + toRefresh + toRename + toSubtitle + toDelete + toRemove + toMetadata):

            if curShowID == '':
                continue

            show_obj = Show.find(sickbeard.showList, int(curShowID))
            if not show_obj:
                continue

            if curShowID in toDelete:
                sickbeard.showQueueScheduler.action.removeShow(show_obj, True)
                # don't do anything else if it's being deleted
                continue

            if curShowID in toRemove:
                sickbeard.showQueueScheduler.action.removeShow(show_obj)
                # don't do anything else if it's being remove
                continue

            if curShowID in toUpdate:
                try:
                    sickbeard.showQueueScheduler.action.updateShow(show_obj, True)
                    updates.append(show_obj.name)
                except CantUpdateShowException as e:
                    errors.append(_("Unable to update show: {excption_format}").format(excption_format=e))

            # don't bother refreshing shows that were updated anyway
            if curShowID in toRefresh and curShowID not in toUpdate:
                try:
                    sickbeard.showQueueScheduler.action.refreshShow(show_obj)
                    refreshes.append(show_obj.name)
                except CantRefreshShowException as e:
                    errors.append(_("Unable to refresh show {show_name}: {excption_format}").format(show_name=show_obj.name, excption_format=e))

            if curShowID in toRename:
                sickbeard.showQueueScheduler.action.renameShowEpisodes(show_obj)
                renames.append(show_obj.name)

            if curShowID in toSubtitle:
                sickbeard.showQueueScheduler.action.download_subtitles(show_obj)
                subtitles.append(show_obj.name)

        if errors:
            ui.notifications.error(_("Errors encountered"),
                                   '<br >\n'.join(errors))

        messageDetail = ""

        if updates:
            messageDetail += "<br><b>" + _("Updates") + "</b><br><ul><li>"
            messageDetail += "</li><li>".join(updates)
            messageDetail += "</li></ul>"

        if refreshes:
            messageDetail += "<br><b>" + _("Refreshes") + "</b><br><ul><li>"
            messageDetail += "</li><li>".join(refreshes)
            messageDetail += "</li></ul>"

        if renames:
            messageDetail += "<br><b>" + _("Renames") + "</b><br><ul><li>"
            messageDetail += "</li><li>".join(renames)
            messageDetail += "</li></ul>"

        if subtitles:
            messageDetail += "<br><b>" + _("Subtitles") + "</b><br><ul><li>"
            messageDetail += "</li><li>".join(subtitles)
            messageDetail += "</li></ul>"

        if updates + refreshes + renames + subtitles:
            ui.notifications.message(_("The following actions were queued") + ":",
                                     messageDetail)

        return self.redirect("/manage/")

    def manageTorrents(self):
        t = PageTemplate(rh=self, filename="manage_torrents.mako")
        info_download_station = ''

        if re.search('localhost', sickbeard.TORRENT_HOST):
            webui_url = re.sub('localhost', sickbeard.LOCALHOST_IP or helpers.get_lan_ip(), sickbeard.TORRENT_HOST)
        else:
            webui_url = sickbeard.TORRENT_HOST

        if sickbeard.TORRENT_METHOD == 'utorrent':
            webui_url = '/'.join(s.strip('/') for s in (webui_url, 'gui/'))
        if sickbeard.TORRENT_METHOD == 'download_station':
            if helpers.check_url(urljoin(webui_url, 'download/')):
                webui_url += 'download/'
            else:
                info_download_station = '<p>' + _('For best results please set the Download Station alias as') + ' <code>download</code>. '
                info_download_station += _('You can check this setting in the Synology DSM') + ' ' + '<b>' + _('Control Panel') + '</b> > <b>' + _('Application Portal') + '</b>.'
                info_download_station += _('Make sure you allow DSM to be embedded with iFrames too in') + ' ' + '<b>'
                info_download_station += _('Control Panel') + '</b> > <b>' + _('DSM Settings') + '</b> > <b>' + _('Security') + '</b>.'
                info_download_station += '</p><br>'

        if not sickbeard.TORRENT_PASSWORD == "" and not sickbeard.TORRENT_USERNAME == "":
            webui_url = re.sub('://', '://' + str(sickbeard.TORRENT_USERNAME) + ':' + str(sickbeard.TORRENT_PASSWORD) + '@', webui_url)

        return t.render(
            webui_url=webui_url, info_download_station=info_download_station,
            title=_('Manage Torrents'), header=_('Manage Torrents'), topmenu='manage')

    def failedDownloads(self, limit=100, toRemove=None):
        failed_db_con = db.DBConnection('failed.db')

        if limit == "0":
            sql_results = failed_db_con.select("SELECT * FROM failed")
        else:
            sql_results = failed_db_con.select("SELECT * FROM failed LIMIT ?", [limit])

        toRemove = toRemove.split("|") if toRemove else []

        for release in toRemove:
            failed_db_con.action("DELETE FROM failed WHERE failed.release = ?", [release])

        if toRemove:
            return self.redirect('/manage/failedDownloads/')

        t = PageTemplate(rh=self, filename="manage_failedDownloads.mako")

        return t.render(limit=limit, failedResults=sql_results,
                        title=_('Failed Downloads'), header=_('Failed Downloads'),
                        topmenu='manage', controller="manage",
                        action="failedDownloads")


@route('/manage/manageSearches(/?.*)')
class ManageSearches(Manage):
    def __init__(self, *args, **kwargs):
        super(ManageSearches, self).__init__(*args, **kwargs)

    def index(self, *args_, **kwargs_):
        t = PageTemplate(rh=self, filename="manage_manageSearches.mako")
        # t.backlogPI = sickbeard.backlogSearchScheduler.action.getProgressIndicator()

        return t.render(backlogPaused=sickbeard.searchQueueScheduler.action.is_backlog_paused(),
                        backlogRunning=sickbeard.searchQueueScheduler.action.is_backlog_in_progress(), dailySearchStatus=sickbeard.dailySearchScheduler.action.amActive,
                        findPropersStatus=sickbeard.properFinderScheduler.action.amActive, queueLength=sickbeard.searchQueueScheduler.action.queue_length(),
                        subtitlesFinderStatus=sickbeard.subtitlesFinderScheduler.action.amActive,
                        title=_('Manage Searches'), header=_('Manage Searches'), topmenu='manage',
                        controller="manage", action="manageSearches")

    def forceBacklog(self):
        # force it to run the next time it looks
        result = sickbeard.backlogSearchScheduler.forceRun()
        if result:
            logger.log(u"Backlog search forced")
            ui.notifications.message(_('Backlog search started'))

        return self.redirect("/manage/manageSearches/")

    def forceSearch(self):

        # force it to run the next time it looks
        result = sickbeard.dailySearchScheduler.forceRun()
        if result:
            logger.log(u"Daily search forced")
            ui.notifications.message(_('Daily search started'))

        return self.redirect("/manage/manageSearches/")

    def forceFindPropers(self):
        # force it to run the next time it looks
        result = sickbeard.properFinderScheduler.forceRun()
        if result:
            logger.log(u"Find propers search forced")
            ui.notifications.message(_('Find propers search started'))

        return self.redirect("/manage/manageSearches/")

    def forceSubtitlesFinder(self):
        # force it to run the next time it looks
        result = sickbeard.subtitlesFinderScheduler.forceRun()
        if result:
            logger.log(u"Subtitle search forced")
            ui.notifications.message(_('Subtitle search started'))

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

    def index(self, limit=None):  # pylint: disable=arguments-differ
        sickbeard.HISTORY_LIMIT = limit = try_int(limit or sickbeard.HISTORY_LIMIT or 100, 100)
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
                index = [
                    i for i, item in enumerate(compact)
                    if item['show_id'] == row['show_id'] and
                    item['season'] == row['season'] and
                    item['episode'] == row['episode'] and
                    item['quality'] == row['quality']
                ][0]
                history = compact[index]
                history['actions'].append(action)
                history['actions'].sort(key=lambda x: x['time'], reverse=True)

        t = PageTemplate(rh=self, filename="history.mako")
        submenu = [
            {'title': _('Clear History'), 'path': 'history/clearHistory', 'icon': 'fa fa-trash', 'class': 'clearhistory', 'confirm': True},
            {'title': _('Trim History'), 'path': 'history/trimHistory', 'icon': 'fa fa-scissors', 'class': 'trimhistory', 'confirm': True},
        ]

        return t.render(historyResults=data, compactResults=compact, limit=limit,
                        submenu=submenu, title=_('History'), header=_('History'),
                        topmenu="history", controller="history", action="index")

    def clearHistory(self):
        self.history.clear()

        ui.notifications.message(_('History cleared'))

        return self.redirect("/history/")

    def trimHistory(self):
        self.history.trim()

        ui.notifications.message(_('Removed history entries older than 30 days'))

        return self.redirect("/history/")


@route('/config(/?.*)')
class Config(WebRoot):
    def __init__(self, *args, **kwargs):
        super(Config, self).__init__(*args, **kwargs)

    @staticmethod
    def ConfigMenu():
        menu = [
            {'title': _('General'), 'path': 'config/general/', 'icon': 'fa fa-cog'},
            {'title': _('Backup/Restore'), 'path': 'config/backuprestore/', 'icon': 'fa fa-floppy-o'},
            {'title': _('Search Settings'), 'path': 'config/search/', 'icon': 'fa fa-search'},
            {'title': _('Search Providers'), 'path': 'config/providers/', 'icon': 'fa fa-plug'},
            {'title': _('Subtitles Settings'), 'path': 'config/subtitles/', 'icon': 'fa fa-language'},
            {'title': _('Post Processing'), 'path': 'config/postProcessing/', 'icon': 'fa fa-refresh'},
            {'title': _('Notifications'), 'path': 'config/notifications/', 'icon': 'fa fa-bell-o'},
            {'title': _('Anime'), 'path': 'config/anime/', 'icon': 'fa fa-eye'},
        ]

        return menu

    def index(self):
        t = PageTemplate(rh=self, filename="config.mako")

        try:
            import pwd
            sr_user = pwd.getpwuid(os.getuid()).pw_name
        except ImportError:
            try:
                import getpass
                sr_user = getpass.getuser()
            except StandardError:
                sr_user = 'Unknown'

        try:
            import locale
            sr_locale = locale.getdefaultlocale()
        except StandardError:
            sr_locale = 'Unknown', 'Unknown'

        try:
            import ssl
            ssl_version = ssl.OPENSSL_VERSION
        except StandardError:
            ssl_version = 'Unknown'

        sr_version = ''
        if sickbeard.VERSION_NOTIFY:
            updater = CheckVersion().updater
            if updater:
                updater.need_update()
                sr_version = updater.get_cur_version()

        return t.render(
            submenu=self.ConfigMenu(), title=_('SickRage Configuration'),
            header=_('SickRage Configuration'), topmenu="config",
            sr_user=sr_user, sr_locale=sr_locale, ssl_version=ssl_version,
            sr_version=sr_version
        )


@route('/config/general(/?.*)')
class ConfigGeneral(Config):
    def __init__(self, *args, **kwargs):
        super(ConfigGeneral, self).__init__(*args, **kwargs)

    def index(self):
        t = PageTemplate(rh=self, filename="config_general.mako")

        return t.render(title=_('Config - General'), header=_('General Configuration'),
                        topmenu='config', submenu=self.ConfigMenu(),
                        controller="config", action="index")

    @staticmethod
    def generateApiKey():
        return helpers.generateApiKey()

    @staticmethod
    def saveRootDirs(rootDirString=None):
        sickbeard.ROOT_DIRS = rootDirString

    @staticmethod
    def saveAddShowDefaults(defaultStatus, anyQualities, bestQualities, defaultFlattenFolders, subtitles=False,
                            anime=False, scene=False, defaultStatusAfter=WANTED):

        if anyQualities:
            anyQualities = anyQualities.split(',')
        else:
            anyQualities = []

        if bestQualities:
            bestQualities = bestQualities.split(',')
        else:
            bestQualities = []

        newQuality = Quality.combineQualities([int(quality) for quality in anyQualities], [int(quality) for quality in bestQualities])

        sickbeard.STATUS_DEFAULT = int(defaultStatus)
        sickbeard.STATUS_DEFAULT_AFTER = int(defaultStatusAfter)
        sickbeard.QUALITY_DEFAULT = int(newQuality)

        sickbeard.FLATTEN_FOLDERS_DEFAULT = config.checkbox_to_value(defaultFlattenFolders)
        sickbeard.SUBTITLES_DEFAULT = config.checkbox_to_value(subtitles)

        sickbeard.ANIME_DEFAULT = config.checkbox_to_value(anime)

        sickbeard.SCENE_DEFAULT = config.checkbox_to_value(scene)
        sickbeard.save_config()

        ui.notifications.message(_('Saved Defaults'), _('Your "add show" defaults have been set to your current selections.'))

    def saveGeneral(  # pylint: disable=unused-argument
            self, log_dir=None, log_nr=5, log_size=1, web_port=None, notify_on_login=None, web_log=None, encryption_version=None, web_ipv6=None,
            trash_remove_show=None, trash_rotate_logs=None, update_frequency=None, skip_removed_files=None,
            indexerDefaultLang='en', ep_default_deleted_status=None, launch_browser=None, showupdate_hour=3, web_username=None,
            api_key=None, indexer_default=None, timezone_display=None, cpu_preset='NORMAL',
            web_password=None, version_notify=None, enable_https=None, https_cert=None, https_key=None,
            handle_reverse_proxy=None, sort_article=None, auto_update=None, notify_on_update=None,
            proxy_setting=None, anon_redirect=None, git_path=None, git_remote=None,
            calendar_unprotected=None, calendar_icons=None, debug=None, ssl_verify=None, no_restart=None, coming_eps_missed_range=None,
            fuzzy_dating=None, trim_zero=None, date_preset=None, date_preset_na=None, time_preset=None,
            indexer_timeout=None, download_url=None, rootDir=None, theme_name=None, default_page=None, fanart_background=None, fanart_background_opacity=None,
            git_reset=None, git_username=None, git_password=None, display_all_seasons=None, gui_language=None):

        results = []

        if gui_language != sickbeard.GUI_LANG:
            if gui_language:
                # Selected language
                gettext.translation('messages', sickbeard.LOCALE_DIR, languages=[gui_language], codeset='UTF-8').install(unicode=1)
            else:
                # System default language
                gettext.install('messages', sickbeard.LOCALE_DIR, unicode=1, codeset='UTF-8')

            sickbeard.GUI_LANG = gui_language

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
        sickbeard.LOG_SIZE = float(log_size)

        sickbeard.TRASH_REMOVE_SHOW = config.checkbox_to_value(trash_remove_show)
        sickbeard.TRASH_ROTATE_LOGS = config.checkbox_to_value(trash_rotate_logs)
        config.change_UPDATE_FREQUENCY(update_frequency)
        sickbeard.LAUNCH_BROWSER = config.checkbox_to_value(launch_browser)
        sickbeard.SORT_ARTICLE = config.checkbox_to_value(sort_article)
        sickbeard.CPU_PRESET = cpu_preset
        sickbeard.ANON_REDIRECT = anon_redirect
        sickbeard.PROXY_SETTING = proxy_setting

        git_credentials_changed = sickbeard.GIT_USERNAME, sickbeard.GIT_PASSWORD != git_username, git_password
        sickbeard.GIT_USERNAME = git_username
        sickbeard.GIT_PASSWORD = git_password

        if git_credentials_changed:
            # Re-Initializes sickbeard.gh, so a restart isn't necessary
            setup_github()

        # sickbeard.GIT_RESET = config.checkbox_to_value(git_reset)
        # Force GIT_RESET
        sickbeard.GIT_RESET = 1
        sickbeard.GIT_PATH = git_path
        sickbeard.GIT_REMOTE = git_remote
        sickbeard.CALENDAR_UNPROTECTED = config.checkbox_to_value(calendar_unprotected)
        sickbeard.CALENDAR_ICONS = config.checkbox_to_value(calendar_icons)
        sickbeard.NO_RESTART = config.checkbox_to_value(no_restart)
        sickbeard.DEBUG = config.checkbox_to_value(debug)
        logger.set_level()

        sickbeard.SSL_VERIFY = config.checkbox_to_value(ssl_verify)
        # sickbeard.LOG_DIR is set in config.change_LOG_DIR()
        sickbeard.COMING_EPS_MISSED_RANGE = try_int(coming_eps_missed_range, 7)
        sickbeard.DISPLAY_ALL_SEASONS = config.checkbox_to_value(display_all_seasons)
        sickbeard.NOTIFY_ON_LOGIN = config.checkbox_to_value(notify_on_login)
        sickbeard.WEB_PORT = try_int(web_port)
        sickbeard.WEB_IPV6 = config.checkbox_to_value(web_ipv6)
        # sickbeard.WEB_LOG is set in config.change_LOG_DIR()
        if config.checkbox_to_value(encryption_version) == 1:
            sickbeard.ENCRYPTION_VERSION = 2
        else:
            sickbeard.ENCRYPTION_VERSION = 0
        sickbeard.WEB_USERNAME = web_username
        sickbeard.WEB_PASSWORD = web_password

        sickbeard.FUZZY_DATING = config.checkbox_to_value(fuzzy_dating)
        sickbeard.TRIM_ZERO = config.checkbox_to_value(trim_zero)

        if date_preset:
            sickbeard.DATE_PRESET = date_preset

        if indexer_default:
            sickbeard.INDEXER_DEFAULT = try_int(indexer_default)

        if indexer_timeout:
            sickbeard.INDEXER_TIMEOUT = try_int(indexer_timeout)

        if time_preset:
            sickbeard.TIME_PRESET_W_SECONDS = time_preset
            sickbeard.TIME_PRESET = sickbeard.TIME_PRESET_W_SECONDS.replace(u":%S", u"")

        sickbeard.TIMEZONE_DISPLAY = timezone_display

        if not config.change_LOG_DIR(log_dir, web_log):
            results += [
                _("Unable to create directory {directory}, log directory not changed.").format(directory=ek(os.path.normpath, log_dir))]

        sickbeard.API_KEY = api_key

        sickbeard.ENABLE_HTTPS = config.checkbox_to_value(enable_https)

        if not config.change_HTTPS_CERT(https_cert):
            results += [
                _("Unable to create directory {directory}, https cert directory not changed.").format(directory=ek(os.path.normpath, https_cert))]

        if not config.change_HTTPS_KEY(https_key):
            results += [
                _("Unable to create directory {directory}, https key directory not changed.").format(directory=ek(os.path.normpath, https_key))]

        sickbeard.HANDLE_REVERSE_PROXY = config.checkbox_to_value(handle_reverse_proxy)

        sickbeard.THEME_NAME = theme_name
        sickbeard.FANART_BACKGROUND = config.checkbox_to_value(fanart_background)
        sickbeard.FANART_BACKGROUND_OPACITY = fanart_background_opacity

        sickbeard.DEFAULT_PAGE = default_page

        sickbeard.save_config()

        if len(results) > 0:
            for x in results:
                logger.log(x, logger.ERROR)
            ui.notifications.error(_('Error(s) Saving Configuration'),
                                   '<br>\n'.join(results))
        else:
            ui.notifications.message(_('Configuration Saved'), ek(os.path.join, sickbeard.CONFIG_FILE))

        return self.redirect("/config/general/")


@route('/config/backuprestore(/?.*)')
class ConfigBackupRestore(Config):
    def __init__(self, *args, **kwargs):
        super(ConfigBackupRestore, self).__init__(*args, **kwargs)

    def index(self, *args_, **kwargs_):
        t = PageTemplate(rh=self, filename="config_backuprestore.mako")

        return t.render(submenu=self.ConfigMenu(), title=_('Config - Backup/Restore'),
                        header=_('Backup/Restore'), topmenu='config',
                        controller="config", action="backupRestore")

    @staticmethod
    def backup(backupDir=None):

        finalResult = ''

        if backupDir:
            source = [ek(os.path.join, sickbeard.DATA_DIR, 'sickbeard.db'), sickbeard.CONFIG_FILE,
                      ek(os.path.join, sickbeard.DATA_DIR, 'failed.db'),
                      ek(os.path.join, sickbeard.DATA_DIR, 'cache.db')]
            target = ek(os.path.join, backupDir, 'sickrage-' + time.strftime('%Y%m%d%H%M%S') + '.zip')

            for (path, dirs, files) in ek(os.walk, sickbeard.CACHE_DIR, topdown=True):
                for dirname in dirs:
                    if path == sickbeard.CACHE_DIR and dirname not in ['images']:
                        dirs.remove(dirname)
                for filename in files:
                    source.append(ek(os.path.join, path, filename))

            if helpers.backupConfigZip(source, target, sickbeard.DATA_DIR):
                finalResult += "Successful backup to " + target
            else:
                finalResult += "Backup FAILED"
        else:
            finalResult += "You need to choose a folder to save your backup to!"

        finalResult += "<br>\n"

        return finalResult

    @staticmethod
    def restore(backupFile=None):

        finalResult = ''

        if backupFile:
            source = backupFile
            target_dir = ek(os.path.join, sickbeard.DATA_DIR, 'restore')

            if helpers.restoreConfigZip(source, target_dir):
                finalResult += "Successfully extracted restore files to " + target_dir
                finalResult += "<br>Restart sickrage to complete the restore."
            else:
                finalResult += "Restore FAILED"
        else:
            finalResult += "You need to select a backup file to restore!"

        finalResult += "<br>\n"

        return finalResult


@route('/config/search(/?.*)')
class ConfigSearch(Config):
    def __init__(self, *args, **kwargs):
        super(ConfigSearch, self).__init__(*args, **kwargs)

    def index(self, *args_, **kwargs_):
        t = PageTemplate(rh=self, filename="config_search.mako")

        return t.render(submenu=self.ConfigMenu(), title=_('Config - Episode Search'),
                        header=_('Search Settings'), topmenu='config',
                        controller="config", action="search")

    def saveSearch(self, use_nzbs=None, use_torrents=None, nzb_dir=None, sab_username=None, sab_password=None,
                   sab_apikey=None, sab_category=None, sab_category_anime=None, sab_category_backlog=None, sab_category_anime_backlog=None, sab_host=None, nzbget_username=None,
                   nzbget_password=None, nzbget_category=None, nzbget_category_backlog=None, nzbget_category_anime=None, nzbget_category_anime_backlog=None, nzbget_priority=None,
                   nzbget_host=None, nzbget_use_https=None, backlog_days=None, backlog_frequency=None,
                   dailysearch_frequency=None, nzb_method=None, torrent_method=None, usenet_retention=None,
                   download_propers=None, check_propers_interval=None, allow_high_priority=None, sab_forced=None,
                   randomize_providers=None, use_failed_downloads=None, delete_failed=None,
                   torrent_dir=None, torrent_username=None, torrent_password=None, torrent_host=None,
                   torrent_label=None, torrent_label_anime=None, torrent_path=None, torrent_verify_cert=None,
                   torrent_seed_time=None, torrent_paused=None, torrent_high_bandwidth=None,
                   torrent_rpcurl=None, torrent_auth_type=None, ignore_words=None, trackers_list=None, require_words=None, ignored_subs_list=None,
                   syno_dsm_host=None, syno_dsm_user=None, syno_dsm_pass=None, syno_dsm_path=None):

        results = []

        if not config.change_NZB_DIR(nzb_dir):
            results += ["Unable to create directory " + ek(os.path.normpath, nzb_dir) + ", dir not changed."]

        if not config.change_TORRENT_DIR(torrent_dir):
            results += ["Unable to create directory " + ek(os.path.normpath, torrent_dir) + ", dir not changed."]

        config.change_DAILYSEARCH_FREQUENCY(dailysearch_frequency)

        config.change_BACKLOG_FREQUENCY(backlog_frequency)
        sickbeard.BACKLOG_DAYS = try_int(backlog_days, 7)

        sickbeard.USE_NZBS = config.checkbox_to_value(use_nzbs)
        sickbeard.USE_TORRENTS = config.checkbox_to_value(use_torrents)

        sickbeard.NZB_METHOD = nzb_method
        sickbeard.TORRENT_METHOD = torrent_method
        sickbeard.USENET_RETENTION = try_int(usenet_retention, 500)

        sickbeard.IGNORE_WORDS = ignore_words if ignore_words else ""
        sickbeard.TRACKERS_LIST = trackers_list if trackers_list else ""
        sickbeard.REQUIRE_WORDS = require_words if require_words else ""
        sickbeard.IGNORED_SUBS_LIST = ignored_subs_list if ignored_subs_list else ""

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
        sickbeard.SAB_CATEGORY_BACKLOG = sab_category_backlog
        sickbeard.SAB_CATEGORY_ANIME = sab_category_anime
        sickbeard.SAB_CATEGORY_ANIME_BACKLOG = sab_category_anime_backlog
        sickbeard.SAB_HOST = config.clean_url(sab_host)
        sickbeard.SAB_FORCED = config.checkbox_to_value(sab_forced)

        sickbeard.NZBGET_USERNAME = nzbget_username
        sickbeard.NZBGET_PASSWORD = nzbget_password
        sickbeard.NZBGET_CATEGORY = nzbget_category
        sickbeard.NZBGET_CATEGORY_BACKLOG = nzbget_category_backlog
        sickbeard.NZBGET_CATEGORY_ANIME = nzbget_category_anime
        sickbeard.NZBGET_CATEGORY_ANIME_BACKLOG = nzbget_category_anime_backlog
        sickbeard.NZBGET_HOST = config.clean_host(nzbget_host)
        sickbeard.NZBGET_USE_HTTPS = config.checkbox_to_value(nzbget_use_https)
        sickbeard.NZBGET_PRIORITY = try_int(nzbget_priority, 100)

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

        sickbeard.SYNOLOGY_DSM_HOST = config.clean_url(syno_dsm_host)
        sickbeard.SYNOLOGY_DSM_USERNAME = syno_dsm_user
        sickbeard.SYNOLOGY_DSM_PASSWORD = syno_dsm_pass
        sickbeard.SYNOLOGY_DSM_PATH = syno_dsm_path.rstrip('/\\')

        # This is a PITA, but lets merge the settings if they only set DSM up in one section to save them some time
        if sickbeard.TORRENT_METHOD == 'download_station':
            if not sickbeard.SYNOLOGY_DSM_HOST:
                sickbeard.SYNOLOGY_DSM_HOST = sickbeard.TORRENT_HOST
            if not sickbeard.SYNOLOGY_DSM_USERNAME:
                sickbeard.SYNOLOGY_DSM_USERNAME = sickbeard.TORRENT_USERNAME
            if not sickbeard.SYNOLOGY_DSM_PASSWORD:
                sickbeard.SYNOLOGY_DSM_PASSWORD = sickbeard.TORRENT_PASSWORD
            if not sickbeard.SYNOLOGY_DSM_PATH:
                sickbeard.SYNOLOGY_DSM_PATH = sickbeard.TORRENT_PATH

        if sickbeard.NZB_METHOD == 'download_station':
            if not sickbeard.TORRENT_HOST:
                sickbeard.TORRENT_HOST = sickbeard.SYNOLOGY_DSM_HOST
            if not sickbeard.TORRENT_USERNAME:
                sickbeard.TORRENT_USERNAME = sickbeard.SYNOLOGY_DSM_USERNAME
            if not sickbeard.TORRENT_PASSWORD:
                sickbeard.TORRENT_PASSWORD = sickbeard.SYNOLOGY_DSM_PASSWORD
            if not sickbeard.TORRENT_PATH:
                sickbeard.TORRENT_PATH = sickbeard.SYNOLOGY_DSM_PATH

        sickbeard.save_config()

        if len(results) > 0:
            for x in results:
                logger.log(x, logger.ERROR)
            ui.notifications.error(_('Error(s) Saving Configuration'),
                                   '<br>\n'.join(results))
        else:
            ui.notifications.message(_('Configuration Saved'), ek(os.path.join, sickbeard.CONFIG_FILE))

        return self.redirect("/config/search/")


@route('/config/postProcessing(/?.*)')
class ConfigPostProcessing(Config):
    def __init__(self, *args, **kwargs):
        super(ConfigPostProcessing, self).__init__(*args, **kwargs)

    def index(self, *args_, **kwargs_):
        t = PageTemplate(rh=self, filename="config_postProcessing.mako")

        return t.render(submenu=self.ConfigMenu(), title=_('Config - Post Processing'),
                        header=_('Post Processing'), topmenu='config',
                        controller="config", action="postProcessing")

    def savePostProcessing(self, kodi_data=None, kodi_12plus_data=None,
                           mediabrowser_data=None, sony_ps3_data=None,
                           wdtv_data=None, tivo_data=None, mede8er_data=None,
                           keep_processed_dir=None, process_method=None,
                           del_rar_contents=None, process_automatically=None,
                           no_delete=None, rename_episodes=None, airdate_episodes=None,
                           file_timestamp_timezone=None,
                           unpack=None, unrar_tool=None, alt_unrar_tool=None,
                           move_associated_files=None, sync_files=None,
                           postpone_if_sync_files=None,
                           allowed_extensions=None, tv_download_dir=None,
                           create_missing_show_dirs=None, add_shows_wo_dir=None,
                           extra_scripts=None, nfo_rename=None,
                           naming_pattern=None, naming_multi_ep=None,
                           naming_custom_abd=None, naming_anime=None,
                           naming_abd_pattern=None, naming_strip_year=None,
                           naming_custom_sports=None, naming_sports_pattern=None,
                           naming_custom_anime=None, naming_anime_pattern=None,
                           naming_anime_multi_ep=None, autopostprocessor_frequency=None,
                           use_icacls=None):

        results = []

        if not config.change_TV_DOWNLOAD_DIR(tv_download_dir):
            results += ["Unable to create directory " + ek(os.path.normpath, tv_download_dir) + ", dir not changed."]

        config.change_AUTOPOSTPROCESSOR_FREQUENCY(autopostprocessor_frequency)
        config.change_PROCESS_AUTOMATICALLY(process_automatically)
        sickbeard.USE_ICACLS = config.checkbox_to_value(use_icacls)

        sickbeard.UNRAR_TOOL = unrar_tool
        sickbeard.ALT_UNRAR_TOOL = alt_unrar_tool

        if unpack:
            if self.isRarSupported() != 'not supported':
                sickbeard.UNPACK = config.checkbox_to_value(unpack)
            else:
                sickbeard.UNPACK = 0
                results.append(_("Unpacking Not Supported, disabling unpack setting"))
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
        sickbeard.FILE_TIMESTAMP_TIMEZONE = file_timestamp_timezone
        sickbeard.MOVE_ASSOCIATED_FILES = config.checkbox_to_value(move_associated_files)
        sickbeard.SYNC_FILES = sync_files
        sickbeard.POSTPONE_IF_SYNC_FILES = config.checkbox_to_value(postpone_if_sync_files)

        sickbeard.ALLOWED_EXTENSIONS = ','.join({x.strip() for x in allowed_extensions.split(',') if x.strip()})
        sickbeard.NAMING_CUSTOM_ABD = config.checkbox_to_value(naming_custom_abd)
        sickbeard.NAMING_CUSTOM_SPORTS = config.checkbox_to_value(naming_custom_sports)
        sickbeard.NAMING_CUSTOM_ANIME = config.checkbox_to_value(naming_custom_anime)
        sickbeard.NAMING_STRIP_YEAR = config.checkbox_to_value(naming_strip_year)
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
            if int(naming_anime or 0) in [1, 2]:
                results.append(_("You tried saving an invalid anime naming config, not saving your naming settings"))
            else:
                results.append(_("You tried saving an invalid naming config, not saving your naming settings"))

        if self.isNamingValid(naming_anime_pattern, naming_anime_multi_ep, anime_type=naming_anime) != "invalid":
            sickbeard.NAMING_ANIME_PATTERN = naming_anime_pattern
            sickbeard.NAMING_ANIME_MULTI_EP = int(naming_anime_multi_ep)
            sickbeard.NAMING_ANIME = int(naming_anime)
            sickbeard.NAMING_FORCE_FOLDERS = naming.check_force_season_folders()
        else:
            if int(naming_anime or 0) in [1, 2]:
                results.append(_("You tried saving an invalid anime naming config, not saving your naming settings"))
            else:
                results.append(_("You tried saving an invalid naming config, not saving your naming settings"))

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
                logger.log(x, logger.WARNING)
            ui.notifications.error(_('Error(s) Saving Configuration'),
                                   '<br>\n'.join(results))
        else:
            ui.notifications.message(_('Configuration Saved'), ek(os.path.join, sickbeard.CONFIG_FILE))

        return self.redirect("/config/postProcessing/")

    @staticmethod
    def testNaming(pattern=None, multi=None, abd=False, sports=False, anime_type=None):

        if multi is not None:
            multi = int(multi)

        if anime_type is not None:
            anime_type = int(anime_type)

        result = naming.test_name(pattern, multi, abd, sports, anime_type)

        result = ek(os.path.join, result['dir'], result['name'])

        return result

    @staticmethod
    def isNamingValid(pattern=None, multi=None, abd=False, sports=False, anime_type=None):
        if not pattern:
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

    @staticmethod
    def isRarSupported():
        """
        Test Packing Support:
            - Simulating in memory rar extraction on test.rar file
        """
        check = rarfile._check_unrar_tool()
        if not check:
            logger.log(u'Looks like unrar is not installed, check failed', logger.WARNING)
        return ('not supported', 'supported')[check]


@route('/config/providers(/?.*)')
class ConfigProviders(Config):
    def __init__(self, *args, **kwargs):
        super(ConfigProviders, self).__init__(*args, **kwargs)

    def index(self, *args_, **kwargs_):
        t = PageTemplate(rh=self, filename="config_providers.mako")

        return t.render(submenu=self.ConfigMenu(), title=_('Config - Providers'),
                        header=_('Search Providers'), topmenu='config',
                        controller="config", action="providers")

    @staticmethod
    def canAddNewznabProvider(name):

        if not name:
            return json.dumps({'error': 'No Provider Name specified'})

        providerDict = dict(zip([x.get_id() for x in sickbeard.newznabProviderList], sickbeard.newznabProviderList))

        tempProvider = newznab.NewznabProvider(name, '')

        if tempProvider.get_id() in providerDict:
            return json.dumps({'error': 'Provider Name already exists as ' + providerDict[tempProvider.get_id()].name})
        else:
            return json.dumps({'success': tempProvider.get_id()})

    @staticmethod
    def getNewznabCategories(name, url, key):
        """
        Retrieves a list of possible categories with category id's
        Using the default url/api?cat
        http://yournewznaburl.com/api?t=caps&apikey=yourapikey
        """
        error = ""
        success = False

        if not name:
            error += "\n" + _("No Provider Name specified")
        if not url:
            error += "\n" + _("No Provider Url specified")
        if not key:
            error += "\n" + _("No Provider Api key specified")

        if error:
            return json.dumps({'success': False, 'error': error})

        # Get list with Newznabproviders
        # providerDict = dict(zip([x.get_id() for x in sickbeard.newznabProviderList], sickbeard.newznabProviderList))

        # Get newznabprovider obj with provided name
        tempProvider = newznab.NewznabProvider(name, url, key)

        success, tv_categories, error = tempProvider.get_newznab_categories()

        return json.dumps({'success': success, 'tv_categories': tv_categories, 'error': error})

    @staticmethod
    def deleteNewznabProvider(nnid):

        providerDict = dict(zip([x.get_id() for x in sickbeard.newznabProviderList], sickbeard.newznabProviderList))

        if nnid not in providerDict or providerDict[nnid].default:
            return '0'

        # delete it from the list
        sickbeard.newznabProviderList.remove(providerDict[nnid])

        if nnid in sickbeard.PROVIDER_ORDER:
            sickbeard.PROVIDER_ORDER.remove(nnid)

        return '1'

    @staticmethod
    def canAddTorrentRssProvider(name, url, cookies, titleTAG):

        if not name:
            return json.dumps({'error': 'Invalid name specified'})

        providerDict = dict(
            zip([x.get_id() for x in sickbeard.torrentRssProviderList], sickbeard.torrentRssProviderList))

        tempProvider = rsstorrent.TorrentRssProvider(name, url, cookies, titleTAG)

        if tempProvider.get_id() in providerDict:
            return json.dumps({'error': 'Exists as ' + providerDict[tempProvider.get_id()].name})
        else:
            (succ, errMsg) = tempProvider.validateRSS()
            if succ:
                return json.dumps({'success': tempProvider.get_id()})
            else:
                return json.dumps({'error': errMsg})

    @staticmethod
    def deleteTorrentRssProvider(provider_id):

        providerDict = dict(
            zip([x.get_id() for x in sickbeard.torrentRssProviderList], sickbeard.torrentRssProviderList))

        if provider_id not in providerDict:
            return '0'

        # delete it from the list
        sickbeard.torrentRssProviderList.remove(providerDict[provider_id])

        if provider_id in sickbeard.PROVIDER_ORDER:
            sickbeard.PROVIDER_ORDER.remove(provider_id)

        return '1'

    def saveProviders(self, newznab_string='', torrentrss_string='', provider_order=None, **kwargs):
        results = []

        provider_str_list = provider_order.split()
        provider_list = []

        newznabProviderDict = dict(
            zip([x.get_id() for x in sickbeard.newznabProviderList], sickbeard.newznabProviderList))

        finishedNames = []

        # add all the newznab info we got into our list
        if newznab_string:
            for curNewznabProviderStr in newznab_string.split('!!!'):

                if not curNewznabProviderStr:
                    continue

                cur_name, cur_url, cur_key, cur_cat = curNewznabProviderStr.split('|')
                cur_url = config.clean_url(cur_url)

                newProvider = newznab.NewznabProvider(cur_name, cur_url, key=cur_key)

                cur_id = newProvider.get_id()

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
                    except Exception:
                        pass

                    try:
                        newznabProviderDict[cur_id].search_fallback = config.checkbox_to_value(
                            kwargs[cur_id + '_search_fallback'])
                    except Exception:
                        newznabProviderDict[cur_id].search_fallback = 0

                    try:
                        newznabProviderDict[cur_id].enable_daily = config.checkbox_to_value(
                            kwargs[cur_id + '_enable_daily'])
                    except Exception:
                        newznabProviderDict[cur_id].enable_daily = 0

                    try:
                        newznabProviderDict[cur_id].enable_backlog = config.checkbox_to_value(
                            kwargs[cur_id + '_enable_backlog'])
                    except Exception:
                        newznabProviderDict[cur_id].enable_backlog = 0
                else:
                    sickbeard.newznabProviderList.append(newProvider)

                finishedNames.append(cur_id)

        # delete anything that is missing
        for curProvider in sickbeard.newznabProviderList:
            if curProvider.get_id() not in finishedNames:
                sickbeard.newznabProviderList.remove(curProvider)

        torrentRssProviderDict = dict(
            zip([x.get_id() for x in sickbeard.torrentRssProviderList], sickbeard.torrentRssProviderList))
        finishedNames = []

        if torrentrss_string:
            for curTorrentRssProviderStr in torrentrss_string.split('!!!'):

                if not curTorrentRssProviderStr:
                    continue

                curName, curURL, curCookies, curTitleTAG = curTorrentRssProviderStr.split('|')
                curURL = config.clean_url(curURL)

                newProvider = rsstorrent.TorrentRssProvider(curName, curURL, curCookies, curTitleTAG)

                curID = newProvider.get_id()

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
            if curProvider.get_id() not in finishedNames:
                sickbeard.torrentRssProviderList.remove(curProvider)

        disabled_list = []
        # do the enable/disable
        for curProviderStr in provider_str_list:
            curProvider, curEnabled = curProviderStr.split(':')
            curEnabled = try_int(curEnabled)

            curProvObj = [x for x in sickbeard.providers.sortedProviderList() if
                          x.get_id() == curProvider and hasattr(x, 'enabled')]
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
        for curTorrentProvider in [prov for prov in sickbeard.providers.sortedProviderList() if
                                   prov.provider_type == GenericProvider.TORRENT]:

            if hasattr(curTorrentProvider, 'custom_url'):
                try:
                    curTorrentProvider.custom_url = str(kwargs[curTorrentProvider.get_id() + '_custom_url']).strip()
                except Exception:
                    curTorrentProvider.custom_url = None

            if hasattr(curTorrentProvider, 'minseed'):
                try:
                    curTorrentProvider.minseed = int(str(kwargs[curTorrentProvider.get_id() + '_minseed']).strip())
                except Exception:
                    curTorrentProvider.minseed = 0

            if hasattr(curTorrentProvider, 'minleech'):
                try:
                    curTorrentProvider.minleech = int(str(kwargs[curTorrentProvider.get_id() + '_minleech']).strip())
                except Exception:
                    curTorrentProvider.minleech = 0

            if hasattr(curTorrentProvider, 'ratio'):
                try:
                    ratio = float(str(kwargs[curTorrentProvider.get_id() + '_ratio']).strip())
                    curTorrentProvider.ratio = (ratio, -1)[ratio < 0]
                except Exception:
                    curTorrentProvider.ratio = None

            if hasattr(curTorrentProvider, 'digest'):
                try:
                    curTorrentProvider.digest = str(kwargs[curTorrentProvider.get_id() + '_digest']).strip()
                except Exception:
                    curTorrentProvider.digest = None

            if hasattr(curTorrentProvider, 'hash'):
                try:
                    curTorrentProvider.hash = str(kwargs[curTorrentProvider.get_id() + '_hash']).strip()
                except Exception:
                    curTorrentProvider.hash = None

            if hasattr(curTorrentProvider, 'api_key'):
                try:
                    curTorrentProvider.api_key = str(kwargs[curTorrentProvider.get_id() + '_api_key']).strip()
                except Exception:
                    curTorrentProvider.api_key = None

            if hasattr(curTorrentProvider, 'username'):
                try:
                    curTorrentProvider.username = str(kwargs[curTorrentProvider.get_id() + '_username']).strip()
                except Exception:
                    curTorrentProvider.username = None

            if hasattr(curTorrentProvider, 'password'):
                try:
                    curTorrentProvider.password = str(kwargs[curTorrentProvider.get_id() + '_password']).strip()
                except Exception:
                    curTorrentProvider.password = None

            if hasattr(curTorrentProvider, 'passkey'):
                try:
                    curTorrentProvider.passkey = str(kwargs[curTorrentProvider.get_id() + '_passkey']).strip()
                except Exception:
                    curTorrentProvider.passkey = None

            if hasattr(curTorrentProvider, 'pin'):
                try:
                    curTorrentProvider.pin = str(kwargs[curTorrentProvider.get_id() + '_pin']).strip()
                except Exception:
                    curTorrentProvider.pin = None

            if hasattr(curTorrentProvider, 'confirmed'):
                try:
                    curTorrentProvider.confirmed = config.checkbox_to_value(
                        kwargs[curTorrentProvider.get_id() + '_confirmed'])
                except Exception:
                    curTorrentProvider.confirmed = 0

            if hasattr(curTorrentProvider, 'ranked'):
                try:
                    curTorrentProvider.ranked = config.checkbox_to_value(
                        kwargs[curTorrentProvider.get_id() + '_ranked'])
                except Exception:
                    curTorrentProvider.ranked = 0

            if hasattr(curTorrentProvider, 'engrelease'):
                try:
                    curTorrentProvider.engrelease = config.checkbox_to_value(
                        kwargs[curTorrentProvider.get_id() + '_engrelease'])
                except Exception:
                    curTorrentProvider.engrelease = 0

            if hasattr(curTorrentProvider, 'onlyspasearch'):
                try:
                    curTorrentProvider.onlyspasearch = config.checkbox_to_value(
                        kwargs[curTorrentProvider.get_id() + '_onlyspasearch'])
                except Exception:
                    curTorrentProvider.onlyspasearch = 0

            if hasattr(curTorrentProvider, 'sorting'):
                try:
                    curTorrentProvider.sorting = str(kwargs[curTorrentProvider.get_id() + '_sorting']).strip()
                except Exception:
                    curTorrentProvider.sorting = 'seeders'

            if hasattr(curTorrentProvider, 'freeleech'):
                try:
                    curTorrentProvider.freeleech = config.checkbox_to_value(
                        kwargs[curTorrentProvider.get_id() + '_freeleech'])
                except Exception:
                    curTorrentProvider.freeleech = 0

            if hasattr(curTorrentProvider, 'search_mode'):
                try:
                    curTorrentProvider.search_mode = str(kwargs[curTorrentProvider.get_id() + '_search_mode']).strip()
                except Exception:
                    curTorrentProvider.search_mode = 'eponly'

            if hasattr(curTorrentProvider, 'search_fallback'):
                try:
                    curTorrentProvider.search_fallback = config.checkbox_to_value(
                        kwargs[curTorrentProvider.get_id() + '_search_fallback'])
                except Exception:
                    curTorrentProvider.search_fallback = 0  # these exceptions are catching unselected checkboxes

            if hasattr(curTorrentProvider, 'enable_daily'):
                try:
                    curTorrentProvider.enable_daily = config.checkbox_to_value(
                        kwargs[curTorrentProvider.get_id() + '_enable_daily'])
                except Exception:
                    curTorrentProvider.enable_daily = 0  # these exceptions are actually catching unselected checkboxes

            if hasattr(curTorrentProvider, 'enable_backlog'):
                try:
                    curTorrentProvider.enable_backlog = config.checkbox_to_value(
                        kwargs[curTorrentProvider.get_id() + '_enable_backlog'])
                except Exception:
                    curTorrentProvider.enable_backlog = 0  # these exceptions are actually catching unselected checkboxes

            if hasattr(curTorrentProvider, 'cat'):
                try:
                    curTorrentProvider.cat = int(str(kwargs[curTorrentProvider.get_id() + '_cat']).strip())
                except Exception:
                    curTorrentProvider.cat = 0

            if hasattr(curTorrentProvider, 'subtitle'):
                try:
                    curTorrentProvider.subtitle = config.checkbox_to_value(
                        kwargs[curTorrentProvider.get_id() + '_subtitle'])
                except Exception:
                    curTorrentProvider.subtitle = 0

            if curTorrentProvider.enable_cookies:
                try:
                    curTorrentProvider.cookies = str(kwargs['{id}_cookies'.format(id=curTorrentProvider.get_id())]).strip()
                except Exception:
                    pass  # I don't want to configure a default value here, as it can also be configured intially as a custom rss torrent provider

        for curNzbProvider in [prov for prov in sickbeard.providers.sortedProviderList() if
                               prov.provider_type == GenericProvider.NZB]:

            if hasattr(curNzbProvider, 'api_key'):
                try:
                    curNzbProvider.api_key = str(kwargs[curNzbProvider.get_id() + '_api_key']).strip()
                except Exception:
                    curNzbProvider.api_key = None

            if hasattr(curNzbProvider, 'username'):
                try:
                    curNzbProvider.username = str(kwargs[curNzbProvider.get_id() + '_username']).strip()
                except Exception:
                    curNzbProvider.username = None

            if hasattr(curNzbProvider, 'search_mode'):
                try:
                    curNzbProvider.search_mode = str(kwargs[curNzbProvider.get_id() + '_search_mode']).strip()
                except Exception:
                    curNzbProvider.search_mode = 'eponly'

            if hasattr(curNzbProvider, 'search_fallback'):
                try:
                    curNzbProvider.search_fallback = config.checkbox_to_value(
                        kwargs[curNzbProvider.get_id() + '_search_fallback'])
                except Exception:
                    curNzbProvider.search_fallback = 0  # these exceptions are actually catching unselected checkboxes

            if hasattr(curNzbProvider, 'enable_daily'):
                try:
                    curNzbProvider.enable_daily = config.checkbox_to_value(
                        kwargs[curNzbProvider.get_id() + '_enable_daily'])
                except Exception:
                    curNzbProvider.enable_daily = 0  # these exceptions are actually catching unselected checkboxes

            if hasattr(curNzbProvider, 'enable_backlog'):
                try:
                    curNzbProvider.enable_backlog = config.checkbox_to_value(
                        kwargs[curNzbProvider.get_id() + '_enable_backlog'])
                except Exception:
                    curNzbProvider.enable_backlog = 0  # these exceptions are actually catching unselected checkboxes

        sickbeard.NEWZNAB_DATA = '!!!'.join([x.configStr() for x in sickbeard.newznabProviderList])
        sickbeard.PROVIDER_ORDER = provider_list

        sickbeard.save_config()

        if len(results) > 0:
            for x in results:
                logger.log(x, logger.ERROR)
            ui.notifications.error(_('Error(s) Saving Configuration'),
                                   '<br>\n'.join(results))
        else:
            ui.notifications.message(_('Configuration Saved'), ek(os.path.join, sickbeard.CONFIG_FILE))

        return self.redirect("/config/providers/")


@route('/config/notifications(/?.*)')
class ConfigNotifications(Config):
    def __init__(self, *args, **kwargs):
        super(ConfigNotifications, self).__init__(*args, **kwargs)

    def index(self, *args_, **kwargs_):
        t = PageTemplate(rh=self, filename="config_notifications.mako")

        return t.render(submenu=self.ConfigMenu(), title=_('Config - Notifications'),
                        header=_('Notifications'), topmenu='config',
                        controller="config", action="notifications")

    def saveNotifications(  # pylint: disable=unused-argument
            self, use_kodi=None, kodi_always_on=None, kodi_notify_onsnatch=None,
            kodi_notify_ondownload=None,
            kodi_notify_onsubtitledownload=None, kodi_update_onlyfirst=None,
            kodi_update_library=None, kodi_update_full=None, kodi_host=None, kodi_username=None,
            kodi_password=None,
            use_plex_server=None, plex_notify_onsnatch=None, plex_notify_ondownload=None,
            plex_notify_onsubtitledownload=None, plex_update_library=None,
            plex_server_host=None, plex_server_token=None, plex_client_host=None, plex_server_username=None, plex_server_password=None,
            use_plex_client=None, plex_client_username=None, plex_client_password=None,
            plex_server_https=None, use_emby=None, emby_host=None, emby_apikey=None,
            use_growl=None, growl_notify_onsnatch=None, growl_notify_ondownload=None,
            growl_notify_onsubtitledownload=None, growl_host=None, growl_password=None,
            use_freemobile=None, freemobile_notify_onsnatch=None, freemobile_notify_ondownload=None,
            freemobile_notify_onsubtitledownload=None, freemobile_id=None, freemobile_apikey=None,
            use_telegram=None, telegram_notify_onsnatch=None, telegram_notify_ondownload=None,
            telegram_notify_onsubtitledownload=None, telegram_id=None, telegram_apikey=None,
            use_join=None, join_notify_onsnatch=None, join_notify_ondownload=None,
            join_notify_onsubtitledownload=None, join_id=None,
            use_prowl=None, prowl_notify_onsnatch=None, prowl_notify_ondownload=None,
            prowl_notify_onsubtitledownload=None, prowl_api=None, prowl_priority=0,
            prowl_show_list=None, prowl_show=None, prowl_message_title=None,
            use_twitter=None, twitter_notify_onsnatch=None, twitter_notify_ondownload=None,
            twitter_notify_onsubtitledownload=None, twitter_usedm=None, twitter_dmto=None,
            use_twilio=None, twilio_notify_onsnatch=None, twilio_notify_ondownload=None, twilio_notify_onsubtitledownload=None,
            twilio_phone_sid=None, twilio_account_sid=None, twilio_auth_token=None, twilio_to_number=None,
            use_boxcar2=None, boxcar2_notify_onsnatch=None, boxcar2_notify_ondownload=None,
            boxcar2_notify_onsubtitledownload=None, boxcar2_accesstoken=None,
            use_pushover=None, pushover_notify_onsnatch=None, pushover_notify_ondownload=None,
            pushover_notify_onsubtitledownload=None, pushover_userkey=None, pushover_apikey=None, pushover_device=None, pushover_sound=None, pushover_priority=0,
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
            pushbullet_device_list=None, pushbullet_channel_list=None, pushbullet_channel=None,
            use_email=None, email_notify_onsnatch=None, email_notify_ondownload=None,
            email_notify_onsubtitledownload=None, email_host=None, email_port=25, email_from=None,
            email_tls=None, email_user=None, email_password=None, email_list=None, email_subject=None, email_show_list=None,
            email_show=None, use_slack=False, slack_notify_snatch=None, slack_notify_download=None, slack_webhook=None):

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

        sickbeard.USE_PLEX_SERVER = config.checkbox_to_value(use_plex_server)
        sickbeard.PLEX_NOTIFY_ONSNATCH = config.checkbox_to_value(plex_notify_onsnatch)
        sickbeard.PLEX_NOTIFY_ONDOWNLOAD = config.checkbox_to_value(plex_notify_ondownload)
        sickbeard.PLEX_NOTIFY_ONSUBTITLEDOWNLOAD = config.checkbox_to_value(plex_notify_onsubtitledownload)
        sickbeard.PLEX_UPDATE_LIBRARY = config.checkbox_to_value(plex_update_library)
        sickbeard.PLEX_CLIENT_HOST = config.clean_hosts(plex_client_host)
        sickbeard.PLEX_SERVER_HOST = config.clean_hosts(plex_server_host)
        sickbeard.PLEX_SERVER_TOKEN = config.clean_host(plex_server_token)
        sickbeard.PLEX_SERVER_USERNAME = plex_server_username
        if plex_server_password != '*' * len(sickbeard.PLEX_SERVER_PASSWORD):
            sickbeard.PLEX_SERVER_PASSWORD = plex_server_password

        sickbeard.USE_PLEX_CLIENT = config.checkbox_to_value(use_plex_client)
        sickbeard.PLEX_CLIENT_USERNAME = plex_client_username
        if plex_client_password != '*' * len(sickbeard.PLEX_CLIENT_PASSWORD):
            sickbeard.PLEX_CLIENT_PASSWORD = plex_client_password
        sickbeard.PLEX_SERVER_HTTPS = config.checkbox_to_value(plex_server_https)

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

        sickbeard.USE_TELEGRAM = config.checkbox_to_value(use_telegram)
        sickbeard.TELEGRAM_NOTIFY_ONSNATCH = config.checkbox_to_value(telegram_notify_onsnatch)
        sickbeard.TELEGRAM_NOTIFY_ONDOWNLOAD = config.checkbox_to_value(telegram_notify_ondownload)
        sickbeard.TELEGRAM_NOTIFY_ONSUBTITLEDOWNLOAD = config.checkbox_to_value(telegram_notify_onsubtitledownload)
        sickbeard.TELEGRAM_ID = telegram_id
        sickbeard.TELEGRAM_APIKEY = telegram_apikey

        sickbeard.USE_JOIN = config.checkbox_to_value(use_join)
        sickbeard.JOIN_NOTIFY_ONSNATCH = config.checkbox_to_value(join_notify_onsnatch)
        sickbeard.JOIN_NOTIFY_ONDOWNLOAD = config.checkbox_to_value(join_notify_ondownload)
        sickbeard.JOIN_NOTIFY_ONSUBTITLEDOWNLOAD = config.checkbox_to_value(join_notify_onsubtitledownload)
        sickbeard.JOIN_ID = join_id

        sickbeard.USE_PROWL = config.checkbox_to_value(use_prowl)
        sickbeard.PROWL_NOTIFY_ONSNATCH = config.checkbox_to_value(prowl_notify_onsnatch)
        sickbeard.PROWL_NOTIFY_ONDOWNLOAD = config.checkbox_to_value(prowl_notify_ondownload)
        sickbeard.PROWL_NOTIFY_ONSUBTITLEDOWNLOAD = config.checkbox_to_value(prowl_notify_onsubtitledownload)
        sickbeard.PROWL_API = prowl_api
        sickbeard.PROWL_PRIORITY = prowl_priority
        sickbeard.PROWL_MESSAGE_TITLE = prowl_message_title

        sickbeard.USE_TWITTER = config.checkbox_to_value(use_twitter)
        sickbeard.TWITTER_NOTIFY_ONSNATCH = config.checkbox_to_value(twitter_notify_onsnatch)
        sickbeard.TWITTER_NOTIFY_ONDOWNLOAD = config.checkbox_to_value(twitter_notify_ondownload)
        sickbeard.TWITTER_NOTIFY_ONSUBTITLEDOWNLOAD = config.checkbox_to_value(twitter_notify_onsubtitledownload)
        sickbeard.TWITTER_USEDM = config.checkbox_to_value(twitter_usedm)
        sickbeard.TWITTER_DMTO = twitter_dmto

        sickbeard.USE_TWILIO = config.checkbox_to_value(use_twilio)
        sickbeard.TWILIO_NOTIFY_ONSNATCH = config.checkbox_to_value(twilio_notify_onsnatch)
        sickbeard.TWILIO_NOTIFY_ONDOWNLOAD = config.checkbox_to_value(twilio_notify_ondownload)
        sickbeard.TWILIO_NOTIFY_ONSUBTITLEDOWNLOAD = config.checkbox_to_value(twilio_notify_onsubtitledownload)
        sickbeard.TWILIO_PHONE_SID = twilio_phone_sid
        sickbeard.TWILIO_ACCOUNT_SID = twilio_account_sid
        sickbeard.TWILIO_AUTH_TOKEN = twilio_auth_token
        sickbeard.TWILIO_TO_NUMBER = twilio_to_number

        sickbeard.USE_SLACK = config.checkbox_to_value(use_slack)
        sickbeard.SLACK_NOTIFY_SNATCH = config.checkbox_to_value(slack_notify_snatch)
        sickbeard.SLACK_NOTIFY_DOWNLOAD = config.checkbox_to_value(slack_notify_download)
        sickbeard.SLACK_WEBHOOK = slack_webhook

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
        sickbeard.PUSHOVER_PRIORITY = pushover_priority

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
        sickbeard.EMAIL_PORT = try_int(email_port, 25)
        sickbeard.EMAIL_FROM = email_from
        sickbeard.EMAIL_TLS = config.checkbox_to_value(email_tls)
        sickbeard.EMAIL_USER = email_user
        sickbeard.EMAIL_PASSWORD = email_password
        sickbeard.EMAIL_LIST = email_list
        sickbeard.EMAIL_SUBJECT = email_subject

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
        sickbeard.PUSHBULLET_CHANNEL = pushbullet_channel_list or ""

        sickbeard.save_config()

        if len(results) > 0:
            for x in results:
                logger.log(x, logger.ERROR)
            ui.notifications.error(_('Error(s) Saving Configuration'),
                                   '<br>\n'.join(results))
        else:
            ui.notifications.message(_('Configuration Saved'), ek(os.path.join, sickbeard.CONFIG_FILE))

        return self.redirect("/config/notifications/")


@route('/config/subtitles(/?.*)')
class ConfigSubtitles(Config):
    def __init__(self, *args, **kwargs):
        super(ConfigSubtitles, self).__init__(*args, **kwargs)

    def index(self, *args_, **kwargs_):
        t = PageTemplate(rh=self, filename="config_subtitles.mako")

        return t.render(submenu=self.ConfigMenu(), title=_('Config - Subtitles'),
                        header=_('Subtitles'), topmenu='config',
                        controller="config", action="subtitles")

    def saveSubtitles(  # pylint: disable=unused-argument
            self, use_subtitles=None, subtitles_plugins=None, subtitles_languages=None, subtitles_dir=None, subtitles_perfect_match=None,
            service_order=None, subtitles_history=None, subtitles_finder_frequency=None,
            subtitles_multi=None, embedded_subtitles_all=None, subtitles_extra_scripts=None, subtitles_hearing_impaired=None,
            addic7ed_user=None, addic7ed_pass=None, itasa_user=None, itasa_pass=None, legendastv_user=None, legendastv_pass=None,
            opensubtitles_user=None, opensubtitles_pass=None, subtitles_download_in_pp=None, subtitles_keep_only_wanted=None):

        config.change_SUBTITLES_FINDER_FREQUENCY(subtitles_finder_frequency)
        config.change_USE_SUBTITLES(use_subtitles)

        sickbeard.SUBTITLES_LANGUAGES = [code.strip() for code in subtitles_languages.split(',') if code.strip() in subtitle_module.subtitle_code_filter()] if subtitles_languages else []
        sickbeard.SUBTITLES_DIR = subtitles_dir
        sickbeard.SUBTITLES_PERFECT_MATCH = config.checkbox_to_value(subtitles_perfect_match)
        sickbeard.SUBTITLES_HISTORY = config.checkbox_to_value(subtitles_history)
        sickbeard.EMBEDDED_SUBTITLES_ALL = config.checkbox_to_value(embedded_subtitles_all)
        sickbeard.SUBTITLES_HEARING_IMPAIRED = config.checkbox_to_value(subtitles_hearing_impaired)
        sickbeard.SUBTITLES_MULTI = config.checkbox_to_value(subtitles_multi)
        sickbeard.SUBTITLES_DOWNLOAD_IN_PP = config.checkbox_to_value(subtitles_download_in_pp)
        sickbeard.SUBTITLES_KEEP_ONLY_WANTED = config.checkbox_to_value(subtitles_keep_only_wanted)
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

        sickbeard.ADDIC7ED_USER = addic7ed_user or ''
        sickbeard.ADDIC7ED_PASS = addic7ed_pass or ''
        sickbeard.ITASA_USER = itasa_user or ''
        sickbeard.ITASA_PASS = itasa_pass or ''
        sickbeard.LEGENDASTV_USER = legendastv_user or ''
        sickbeard.LEGENDASTV_PASS = legendastv_pass or ''
        sickbeard.OPENSUBTITLES_USER = opensubtitles_user or ''
        sickbeard.OPENSUBTITLES_PASS = opensubtitles_pass or ''

        sickbeard.save_config()
        # Reset provider pool so next time we use the newest settings
        subtitle_module.SubtitleProviderPool().reset()

        ui.notifications.message(_('Configuration Saved'), ek(os.path.join, sickbeard.CONFIG_FILE))

        return self.redirect("/config/subtitles/")


@route('/config/anime(/?.*)')
class ConfigAnime(Config):
    def __init__(self, *args, **kwargs):
        super(ConfigAnime, self).__init__(*args, **kwargs)

    def index(self, *args_, **kwargs_):

        t = PageTemplate(rh=self, filename="config_anime.mako")

        return t.render(submenu=self.ConfigMenu(), title=_('Config - Anime'),
                        header=_('Anime'), topmenu='config',
                        controller="config", action="anime")

    def saveAnime(self, use_anidb=None, anidb_username=None, anidb_password=None, anidb_use_mylist=None,
                  split_home=None):

        sickbeard.USE_ANIDB = config.checkbox_to_value(use_anidb)
        sickbeard.ANIDB_USERNAME = anidb_username
        sickbeard.ANIDB_PASSWORD = anidb_password
        sickbeard.ANIDB_USE_MYLIST = config.checkbox_to_value(anidb_use_mylist)
        sickbeard.ANIME_SPLIT_HOME = config.checkbox_to_value(split_home)

        sickbeard.save_config()
        ui.notifications.message(_('Configuration Saved'), ek(os.path.join, sickbeard.CONFIG_FILE))

        return self.redirect("/config/anime/")


@route('/errorlogs(/?.*)')
class ErrorLogs(WebRoot):
    def __init__(self, *args, **kwargs):
        super(ErrorLogs, self).__init__(*args, **kwargs)

    def ErrorLogsMenu(self, level):
        menu = [
            {
                'title': _('Clear Errors'),
                'path': 'errorlogs/clearerrors/',
                'requires': self.haveErrors() and level == logger.ERROR,
                'icon': 'ui-icon ui-icon-trash'
            },
            {
                'title': _('Clear Warnings'),
                'path': 'errorlogs/clearerrors/?level=' + str(logger.WARNING),
                'requires': self.haveWarnings() and level == logger.WARNING,
                'icon': 'ui-icon ui-icon-trash'
            },
            {
                'title': _('Submit Errors'),
                'path': 'errorlogs/submit_errors/',
                'requires': self.haveErrors() and level == logger.ERROR,
                'class': 'submiterrors',
                'confirm': True,
                'icon': 'ui-icon ui-icon-arrowreturnthick-1-n'
            },
        ]

        return menu

    def index(self, level=logger.ERROR):  # pylint: disable=arguments-differ
        level = try_int(level, logger.ERROR)

        t = PageTemplate(rh=self, filename="errorlogs.mako")
        return t.render(header=_("Logs &amp; Errors"), title=_("Logs &amp; Errors"),
                        topmenu="system", submenu=self.ErrorLogsMenu(level),
                        logLevel=level, controller="errorlogs", action="index")

    @staticmethod
    def haveErrors():
        return len(classes.ErrorViewer.errors) > 0

    @staticmethod
    def haveWarnings():
        return len(classes.WarningViewer.errors) > 0

    def clearerrors(self, level=logger.ERROR):
        if int(level) == logger.WARNING:
            classes.WarningViewer.clear()
        else:
            classes.ErrorViewer.clear()

        return self.redirect("/errorlogs/viewlog/")

    def viewlog(self, min_level=logger.INFO, log_filter="<NONE>", log_search='', max_lines=500):
        data = sickbeard.logger.log_data(min_level, log_filter, log_search, max_lines)

        t = PageTemplate(rh=self, filename="viewlogs.mako")
        return t.render(
            header=_("Log File"), title=_("Logs"), topmenu="system",
            log_data=u"".join(data), min_level=min_level,
            log_filter=log_filter, log_search=log_search,
            controller="errorlogs", action="viewlogs")

    def submit_errors(self):
        submitter_result, issue_id = logger.submit_errors()
        logger.log(submitter_result, (logger.INFO, logger.WARNING)[not issue_id])
        submitter_notification = ui.notifications.error if not issue_id else ui.notifications.message
        submitter_notification(submitter_result)

        return self.redirect("/errorlogs/")
