import base64
import datetime
import json
import os
import time
import traceback
from concurrent.futures import ThreadPoolExecutor
from mimetypes import guess_type
from operator import attrgetter
from secrets import compare_digest
from urllib.parse import urljoin

from mako.exceptions import RichTraceback
from tornado.concurrent import run_on_executor
from tornado.escape import utf8, xhtml_escape
from tornado.gen import coroutine
from tornado.web import authenticated, HTTPError, RequestHandler

import sickchill.start
from sickchill import logger, settings
from sickchill.init_helpers import locale_dir
from sickchill.show.ComingEpisodes import ComingEpisodes
from sickchill.views.routes import Route

from ..oldbeard import db, helpers, network_timezones, ui
from .api.webapi import function_mapper
from .common import PageTemplate

try:
    import jwt
    from jwt.algorithms import RSAAlgorithm as jwt_algorithms_RSAAlgorithm

    has_cryptography = True
except Exception:
    has_cryptography = False


class BaseHandler(RequestHandler):
    def data_received(self, chunk):
        pass

    def initialize(self):
        super().initialize()
        self.startTime = time.time()

    # def set_default_headers(self):
    #     self.set_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')

    def write_error(self, status_code, **kwargs):
        # handle 404 http errors
        if status_code == 404:
            url = self.request.uri
            if settings.WEB_ROOT and self.request.uri.startswith(settings.WEB_ROOT):
                url = url[len(settings.WEB_ROOT) + 1 :]

            if url[:3] != "api":
                t = PageTemplate(rh=self, filename="404.mako")
                return t.render(title="404", header=_("Oops: 404 Not Found"))
            else:
                return self.finish(_("Wrong API key used"))

        elif self.settings.get("debug") and "exc_info" in kwargs:
            exc_info = kwargs["exc_info"]
            trace_info = "".join(["{0}<br>".format(line) for line in traceback.format_exception(*exc_info)])
            request_info = "".join(["<strong>{0}</strong>: {1}<br>".format(k, self.request.__dict__[k]) for k in self.request.__dict__])
            error = exc_info[1]

            self.set_header("Content-Type", "text/html")
            return self.finish(
                """<html>
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
                               </html>""".format(
                    error, error, trace_info, request_info, settings.WEB_ROOT
                )
            )

    def redirect(self, url, permanent=False, status=None):
        """Sends a redirect to the given (optionally relative) URL.

        ----->>>>> NOTE: Removed self.finish <<<<<-----

        If the ``status`` argument is specified, that value is used as the
        HTTP status code; otherwise either 301 (permanent) or 302
        (temporary) is chosen based on the ``permanent`` argument.
        The default is 302 (temporary).
        """
        if not url.startswith(settings.WEB_ROOT):
            url = settings.WEB_ROOT + url

        if self._headers_written:
            raise Exception("Cannot redirect after headers have been written")
        if not status:
            status = 301 if permanent else 302
        else:
            assert isinstance(status, int)
            assert 300 <= status <= 399
        self.set_status(status)
        self.set_header("Location", urljoin(utf8(self.request.uri), utf8(url)))

    def get_current_user(self):
        if isinstance(self, UI):
            return True

        if settings.WEB_USERNAME and settings.WEB_PASSWORD:
            # Authenticate using jwt for CF Access
            # NOTE: Setting a username and password is STILL required to protect poorly configured tunnels or firewalls
            if settings.CF_AUTH_DOMAIN and settings.CF_POLICY_AUD and has_cryptography:
                CERTS_URL = "{}/cdn-cgi/access/certs".format(settings.CF_AUTH_DOMAIN)
                if "CF_Authorization" in self.request.cookies:
                    jwk_set = helpers.getURL(CERTS_URL, returns="json")
                    for key_dict in jwk_set["keys"]:
                        public_key = jwt_algorithms_RSAAlgorithm.from_jwk(json.dumps(key_dict))
                        if jwt.decode(self.request.cookies["CF_Authorization"], key=public_key, audience=settings.CF_POLICY_AUD):
                            return True

            # Logged into UI?
            if self.get_secure_cookie("sickchill_user"):
                return True

            # Basic Auth at a minimum
            auth_header = self.request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Basic "):
                auth_decoded = base64.decodebytes(auth_header[6:].encode()).decode()
                username, password = auth_decoded.split(":", 2)
                if compare_digest(username, settings.WEB_USERNAME) and compare_digest(password, settings.WEB_PASSWORD):
                    return True
                return False

        else:
            # Local network
            # strip <scope id> / <zone id> (%value/if_name) from remote_ip IPv6 scoped literal IP Addresses (RFC 4007) until phihag/ipaddress is updated tracking cpython 3.9.
            return helpers.is_ip_local(self.request.remote_ip.rsplit("%")[0])

    def get_user_locale(self):
        return settings.GUI_LANG or None


class WebHandler(BaseHandler):
    def initialize(self):
        super().initialize()
        self.executor = ThreadPoolExecutor(thread_name_prefix="WEBSERVER-" + self.__class__.__name__.upper())

    @authenticated
    @coroutine
    def get(self, route, *args, **kwargs):
        try:
            # logger.debug(f"Call for {route} with args [{self.request.arguments}]")
            # route -> method obj
            route = route.strip("/").replace(".", "_").replace("-", "_") or "index"
            method = getattr(self, route)

            results = yield self.async_call(method)

            self.finish(results)

        except AttributeError:
            logger.debug('Failed doing webui request "{0}": {1}'.format(route, traceback.format_exc()))
            raise HTTPError(404)

    @run_on_executor
    def async_call(self, function):
        try:
            # TODO: Make all routes use get_argument so we can take advantage of tornado's argument sanitization, separate post and get, and get rid of this
            # nonsense loop so we can just yield the method directly
            # raise Exception('Raising from async_call')
            kwargs = self.request.arguments
            for arg, value in kwargs.items():
                if len(value) == 1:
                    kwargs[arg] = xhtml_escape(value[0])
                elif isinstance(value, str):
                    kwargs[arg] = xhtml_escape(value)
                elif isinstance(value, list):
                    kwargs[arg] = [xhtml_escape(v) for v in value]
                else:
                    raise Exception
            return function(**kwargs)
        except TypeError:
            return function()
        except Exception as error:
            return WebRoot(application=self.application, request=self.request).print_traceback(error=error, **self.request.arguments)

    # post uses get method
    post = get


@Route("(.*)(/?)", name="index")
class WebRoot(WebHandler):
    def print_traceback(self, error, *args, **kwargs):
        logger.info(f"A mako error occurred: {error}")
        t = PageTemplate(rh=self, filename="500.mako")
        kwargs["backtrace"] = RichTraceback(error=error)
        return t.render(*args, **kwargs)

    def index(self):
        return self.redirect("/" + settings.DEFAULT_PAGE + "/")

    def robots_txt(self):
        """Keep web crawlers out"""
        self.set_header("Content-Type", "text/plain")
        return "User-agent: *\nDisallow: /"

    def apibuilder(self):
        main_db_con = db.DBConnection(row_type="dict")
        shows = sorted(settings.showList, key=lambda mbr: attrgetter("sort_name")(mbr))
        episodes = {}

        results = main_db_con.select("SELECT episode, season, showid " "FROM tv_episodes " "ORDER BY season ASC, episode ASC")

        for result in results:
            if result["showid"] not in episodes:
                episodes[result["showid"]] = {}

            if result["season"] not in episodes[result["showid"]]:
                episodes[result["showid"]][result["season"]] = []

            episodes[result["showid"]][result["season"]].append(result["episode"])

        if len(settings.API_KEY) == 32:
            apikey = settings.API_KEY
        else:
            apikey = _("API Key not generated")

        t = PageTemplate(rh=self, filename="apiBuilder.mako")
        return t.render(title=_("API Builder"), header=_("API Builder"), shows=shows, episodes=episodes, apikey=apikey, commands=function_mapper)

    def setHomeLayout(self):
        layout = self.get_query_argument("layout")
        if layout not in ("poster", "small", "banner", "simple", "coverflow"):
            layout = "poster"

        settings.HOME_LAYOUT = layout
        # Don't redirect to default page so user can see new layout
        return self.redirect("/home/")

    def setPosterSortBy(self):
        sort = self.get_query_argument("sort")
        if sort not in ("name", "date", "network", "progress"):
            sort = "name"

        settings.POSTER_SORTBY = sort
        sickchill.start.save_config()

    def setPosterSortDir(self):
        direction = self.get_query_argument("direction")

        settings.POSTER_SORTDIR = int(direction)
        sickchill.start.save_config()

    def setHistoryLayout(self):
        layout = self.get_query_argument("layout")
        if layout not in ("compact", "detailed"):
            layout = "detailed"

        settings.HISTORY_LAYOUT = layout

        return self.redirect("/history/")

    def toggleDisplayShowSpecials(self):
        show = self.get_query_argument("show")
        settings.DISPLAY_SHOW_SPECIALS = not settings.DISPLAY_SHOW_SPECIALS

        return self.redirect("/home/displayShow?show=" + show)

    def setScheduleLayout(self):
        layout = self.get_query_argument("layout")
        if layout not in ("poster", "banner", "list", "calendar"):
            layout = "banner"

        if layout == "calendar":
            settings.COMING_EPS_SORT = "date"

        settings.COMING_EPS_LAYOUT = layout

        return self.redirect("/schedule/")

    def toggleScheduleDisplayPaused(self):

        settings.COMING_EPS_DISPLAY_PAUSED = not settings.COMING_EPS_DISPLAY_PAUSED

        return self.redirect("/schedule/")

    def toggleScheduleDisplaySnatched(self):

        settings.COMING_EPS_DISPLAY_SNATCHED = not settings.COMING_EPS_DISPLAY_SNATCHED

        return self.redirect("/schedule/")

    def setScheduleSort(self):
        sort = self.get_query_argument("sort")
        if sort not in ("date", "network", "show") or settings.COMING_EPS_LAYOUT == "calendar":
            sort = "date"

        settings.COMING_EPS_SORT = sort

        return self.redirect("/schedule/")

    def schedule(self):
        layout = self.get_query_argument("layout", settings.COMING_EPS_LAYOUT)
        next_week = datetime.date.today() + datetime.timedelta(days=7)
        next_week1 = datetime.datetime.combine(next_week, datetime.time(tzinfo=network_timezones.sb_timezone))
        results = ComingEpisodes.get_coming_episodes(ComingEpisodes.categories, settings.COMING_EPS_SORT, False)
        today = datetime.datetime.now().replace(tzinfo=network_timezones.sb_timezone)

        # Allow local overriding of layout parameter
        if layout not in ("poster", "banner", "list", "calendar"):
            layout = settings.COMING_EPS_LAYOUT

        t = PageTemplate(rh=self, filename="schedule.mako")
        return t.render(
            next_week=next_week1,
            today=today,
            results=results,
            layout=layout,
            title=_("Schedule"),
            header=_("Schedule"),
            topmenu="schedule",
            controller="schedule",
            action="index",
        )


@Route("/ui(/?.*)", name="ui")
class UI(WebRoot):
    def locale_json(self):

        lang = self.get_query_argument("lang")
        """ Get /locale/{lang_code}/LC_MESSAGES/messages.json """
        locale_file = os.path.normpath(f"{locale_dir()}/{lang}/LC_MESSAGES/messages.json")

        if os.path.isfile(locale_file):
            self.set_header("Content-Type", "application/json")
            with open(locale_file) as content:
                return content.read()
        else:
            self.set_status(204)  # "No Content"
            return None

    @staticmethod
    def add_message():
        ui.notifications.message(_("Test 1"), _("This is test number 1"))
        ui.notifications.error(_("Test 2"), _("This is test number 2"))

        return "ok"

    def get_messages(self):
        self.set_header("Cache-Control", "max-age=0,no-cache,no-store")
        self.set_header("Content-Type", "application/json")
        notifications = ui.notifications.get_notifications(self.request.remote_ip)
        messages = {}
        for index, cur_notification in enumerate(notifications, 1):
            messages["notification-" + str(index)] = {
                "hash": hash(cur_notification),
                "title": cur_notification.title,
                "message": cur_notification.message,
                "type": cur_notification.type,
            }

        return json.dumps(messages)

    def set_site_message(self):
        message = self.get_body_argument("message", None)
        tag = self.get_body_argument("tag", None)
        level = self.get_body_argument("level")
        self.set_header("Cache-Control", "max-age=0,no-cache,no-store")
        if message:
            helpers.add_site_message(message, tag=tag, level=level)
        else:
            if settings.BRANCH and self.get_current_user() and settings.BRANCH not in ("master", "pip") and not settings.DEVELOPER:
                message = _("You're using the {branch} branch. Please use 'master' unless specifically asked".format(branch=settings.BRANCH))
                helpers.add_site_message(message, tag="not_using_master_branch", level="danger")

        return settings.SITE_MESSAGES

    def get_site_messages(self):
        self.set_header("Cache-Control", "max-age=0,no-cache,no-store")
        return settings.SITE_MESSAGES

    def dismiss_site_message(self):
        index = self.get_query_argument("index")
        self.set_header("Cache-Control", "max-age=0,no-cache,no-store")
        helpers.remove_site_message(key=index)
        return settings.SITE_MESSAGES

    def sickchill_background(self):
        if settings.SICKCHILL_BACKGROUND_PATH and os.path.isfile(settings.SICKCHILL_BACKGROUND_PATH):
            self.set_header("Content-Type", guess_type(settings.SICKCHILL_BACKGROUND_PATH)[0])
            with open(settings.SICKCHILL_BACKGROUND_PATH, "rb") as content:
                return content.read()
        return None

    def custom_css(self):
        if settings.CUSTOM_CSS_PATH and os.path.isfile(settings.CUSTOM_CSS_PATH):
            self.set_header("Content-Type", "text/css")
            with open(settings.CUSTOM_CSS_PATH, "r") as content:
                return content.read()
        return None
