# coding=utf-8
# Author: Nic Wolfe <nic@wolfeden.ca>
# URL: https://sickchill.github.io
#
# This file is part of SickChill.
#
# SickChill is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SickChill is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickChill. If not, see <http://www.gnu.org/licenses/>.
# pylint: disable=abstract-method,too-many-lines, R

from __future__ import absolute_import, print_function, unicode_literals

import datetime
import os
import time
import traceback
from concurrent.futures import ThreadPoolExecutor
from mimetypes import guess_type
from operator import attrgetter

import six
from mako.lookup import Template
from requests.compat import urljoin
from tornado.concurrent import run_on_executor
from tornado.escape import utf8, xhtml_escape
from tornado.gen import coroutine
from tornado.ioloop import IOLoop
from tornado.process import cpu_count
from tornado.web import authenticated, HTTPError, RequestHandler

import sickbeard
from sickbeard import db, helpers, logger, network_timezones, ui
from sickbeard.common import ek
from sickchill.media.ShowBanner import ShowBanner
from sickchill.media.ShowFanArt import ShowFanArt
from sickchill.media.ShowNetworkLogo import ShowNetworkLogo
from sickchill.media.ShowPoster import ShowPoster
from sickchill.show.ComingEpisodes import ComingEpisodes
from sickchill.views.routes import Route

from .api.webapi import function_mapper
from .common import PageTemplate

try:
    import json
except ImportError:
    # noinspection PyPackageRequirements,PyUnresolvedReferences
    import simplejson as json


class BaseHandler(RequestHandler):
    startTime = 0.

    def data_received(self, chunk):
        pass

    def __init__(self, *args, **kwargs):
        self.startTime = time.time()

        super(BaseHandler, self).__init__(*args, **kwargs)
        # self.include_host = True

    # def set_default_headers(self):
    #     self.set_header(b'Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')

    def write_error(self, status_code, **kwargs):
        # handle 404 http errors
        if status_code == 404:
            url = self.request.uri
            if sickbeard.WEB_ROOT and self.request.uri.startswith(sickbeard.WEB_ROOT):
                url = url[len(sickbeard.WEB_ROOT) + 1:]

            if url[:3] != 'api':
                t = PageTemplate(rh=self, filename="404.mako")
                return self.finish(t.render(title='404', header=_('Oops: 404 Not Found')))
            else:
                self.finish(_('Wrong API key used'))

        elif self.settings.get("debug") and "exc_info" in kwargs:
            exc_info = kwargs["exc_info"]
            trace_info = ''.join(["{0}<br>".format(line) for line in traceback.format_exception(*exc_info)])
            request_info = ''.join(["<strong>{0}</strong>: {1}<br>".format(k, self.request.__dict__[k]) for k in
                                    self.request.__dict__.keys()])
            error = exc_info[1]

            self.set_header(b'Content-Type', 'text/html')
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
        if not url.startswith(sickbeard.WEB_ROOT):
            url = sickbeard.WEB_ROOT + url

        if self._headers_written:
            raise Exception("Cannot redirect after headers have been written")
        if not status:
            status = 301 if permanent else 302
        else:
            assert isinstance(status, int)
            assert 300 <= status <= 399
        self.set_status(status)
        self.set_header(b"Location", urljoin(utf8(self.request.uri), utf8(url)))

    def get_current_user(self):
        if not isinstance(self, UI) and sickbeard.WEB_USERNAME and sickbeard.WEB_PASSWORD:
            return self.get_secure_cookie('sickchill_user')
        else:
            return True

    def get_user_locale(self):
        return sickbeard.GUI_LANG or None


class WebHandler(BaseHandler):
    def __init__(self, *args, **kwargs):
        super(WebHandler, self).__init__(*args, **kwargs)
        self.io_loop = IOLoop.current()

    executor = ThreadPoolExecutor(cpu_count())

    @authenticated
    @coroutine
    def get(self, route, *args, **kwargs):
        try:
            # route -> method obj
            route = route.strip('/').replace('.', '_').replace('-', '_') or 'index'
            method = getattr(self, route)

            results = yield self.async_call(method)

            self.finish(results)

        except AttributeError:
            logger.log('Failed doing webui request "{0}": {1}'.format(route, traceback.format_exc()), logger.DEBUG)
            raise HTTPError(404)

    @run_on_executor
    def async_call(self, function):
        try:
            kwargs = self.request.arguments
            for arg, value in six.iteritems(kwargs):
                if len(value) == 1:
                    kwargs[arg] = xhtml_escape(value[0])
                elif isinstance(value, six.string_types):
                    kwargs[arg] = xhtml_escape(value)
                elif isinstance(value, list):
                    kwargs[arg] = [xhtml_escape(v) for v in value]
                else:
                    raise Exception

            result = function(**kwargs)
            return result
        except OSError as e:
            return Template("Looks like we do not have enough disk space to render the page! {error}").render_unicode(data=e.message)
        except Exception:
            logger.log('Failed doing webui callback: {0}'.format((traceback.format_exc())), logger.ERROR)
            raise

    # post uses get method
    post = get


@Route('(.*)(/?)', name='index')
class WebRoot(WebHandler):
    def __init__(self, *args, **kwargs):
        super(WebRoot, self).__init__(*args, **kwargs)

    def index(self):
        return self.redirect('/' + sickbeard.DEFAULT_PAGE + '/')

    def robots_txt(self):
        """ Keep web crawlers out """
        self.set_header(b'Content-Type', 'text/plain')
        return "User-agent: *\nDisallow: /"

    def apibuilder(self):
        main_db_con = db.DBConnection(row_type='dict')
        shows = sorted(sickbeard.showList, key=lambda mbr: attrgetter('sort_name')(mbr))
        episodes = {}

        results = main_db_con.select(
            'SELECT episode, season, showid '
            'FROM tv_episodes '
            'ORDER BY season ASC, episode ASC'
        )

        for result in results:
            if result[b'showid'] not in episodes:
                episodes[result[b'showid']] = {}

            if result[b'season'] not in episodes[result[b'showid']]:
                episodes[result[b'showid']][result[b'season']] = []

            episodes[result[b'showid']][result[b'season']].append(result[b'episode'])

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
            abspath = media.get_static_media_path()
            stat_result = os.stat(abspath)
            modified = datetime.datetime.fromtimestamp(int(stat_result.st_mtime))

            self.set_header(b'Last-Modified', modified)
            self.set_header(b'Content-Type', media.get_media_type())
            self.set_header(b'Accept-Ranges', 'bytes')
            self.set_header(b'Cache-Control', 'public, max-age=86400')

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

    def toggleScheduleDisplaySnatched(self):

        sickbeard.COMING_EPS_DISPLAY_SNATCHED = not sickbeard.COMING_EPS_DISPLAY_SNATCHED

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


@Route('/ui(/?.*)', name='ui')
class UI(WebRoot):
    def __init__(self, *args, **kwargs):
        super(UI, self).__init__(*args, **kwargs)

    def locale_json(self):
        """ Get /locale/{lang_code}/LC_MESSAGES/messages.json """
        locale_file = ek(os.path.normpath, '{locale_dir}/{lang}/LC_MESSAGES/messages.json'.format(
            locale_dir=sickbeard.LOCALE_DIR, lang=sickbeard.GUI_LANG))

        if os.path.isfile(locale_file):
            self.set_header(b'Content-Type', 'application/json')
            with open(locale_file, 'r') as content:
                return content.read()
        else:
            self.set_status(204)  # "No Content"
            return None

    @staticmethod
    def add_message():
        ui.notifications.message(_('Test 1'), _('This is test number 1'))
        ui.notifications.error(_('Test 2'), _('This is test number 2'))

        return "ok"

    def get_messages(self):
        self.set_header(b'Cache-Control', 'max-age=0,no-cache,no-store')
        self.set_header(b'Content-Type', 'application/json')
        notifications = ui.notifications.get_notifications(self.request.remote_ip)
        messages = {}
        for index, cur_notification in enumerate(notifications, 1):
            messages['notification-' + str(index)] = {
                'hash': hash(cur_notification),
                'title': cur_notification.title,
                'message': cur_notification.message,
                'type': cur_notification.type
            }

        return json.dumps(messages)

    def set_site_message(self, message, tag, level):
        self.set_header(b'Cache-Control', 'max-age=0,no-cache,no-store')
        if message:
            helpers.add_site_message(message, tag=tag, level=level)
        else:
            if sickbeard.BRANCH and sickbeard.BRANCH != 'master' and not sickbeard.DEVELOPER and self.get_current_user():
                message = _('You\'re using the {branch} branch. '
                            'Please use \'master\' unless specifically asked').format(branch=sickbeard.BRANCH)
                helpers.add_site_message(message, tag='not_using_master_branch', level='danger')

        return sickbeard.SITE_MESSAGES

    def get_site_messages(self):
        self.set_header(b'Cache-Control', 'max-age=0,no-cache,no-store')
        return sickbeard.SITE_MESSAGES

    def dismiss_site_message(self, index):
        self.set_header(b'Cache-Control', 'max-age=0,no-cache,no-store')
        helpers.remove_site_message(key=index)
        return sickbeard.SITE_MESSAGES

    def sickchill_background(self):
        if sickbeard.SICKCHILL_BACKGROUND_PATH and ek(os.path.isfile, sickbeard.SICKCHILL_BACKGROUND_PATH):
            self.set_header(b'Content-Type', guess_type(sickbeard.SICKCHILL_BACKGROUND_PATH)[0])
            with open(sickbeard.SICKCHILL_BACKGROUND_PATH, 'rb') as content:
                return content.read()
        return None

    def custom_css(self):
        if sickbeard.CUSTOM_CSS_PATH and ek(os.path.isfile, sickbeard.CUSTOM_CSS_PATH):
            self.set_header(b'Content-Type', 'text/css')
            with open(sickbeard.CUSTOM_CSS_PATH, 'r') as content:
                return content.read()
        return None
