import asyncio
import errno
import os
import threading
from socket import error as socket_error
from typing import Any, Dict

from tornado.ioloop import IOLoop
from tornado.platform.asyncio import AnyThreadEventLoopPolicy
from tornado.web import Application, RedirectHandler, StaticFileHandler, url

import sickchill.start
from sickchill import logger, settings
from sickchill.oldbeard.helpers import create_https_certificates, generateApiKey
from sickchill.views import CalendarHandler, LoginHandler, LogoutHandler, MoviesHandler
from sickchill.views.api import ApiHandler, KeyHandler

from .routes import Route

# class Custom404Handler(RequestHandler):
#     startTime = 0.
#
#     def prepare(self):
#         return self.redirect(self.reverse_url('home', ''))
#
#         self.set_status(404)
#         t = PageTemplate(rh=self, filename="404.mako")
#         return self.finish(t.render(title='404', header=_('Oops')))


class SickChillStaticFileHandler(StaticFileHandler):
    @classmethod
    def make_static_url(cls, settings: Dict[str, Any], path: str, include_version: bool = True) -> str:
        url = settings.get("static_url_prefix", "/static/") + path
        if not include_version:
            return url

        custom_settings = settings.copy()
        if "cache/" in path:
            custom_settings["static_path"] = os.path.dirname(sickchill.settings.CACHE_DIR)

        version_hash = cls.get_version(custom_settings, path)
        if not version_hash:
            return url

        return "%s?v=%s" % (url, version_hash)


class SRWebServer(threading.Thread):
    def __init__(self, options=None):
        super().__init__()
        self.daemon = True
        self.alive = True
        self.name = "WEBSERVER"

        self.options = options

        if settings.WEB_HOST and settings.WEB_HOST != "0.0.0.0":
            web_host = settings.WEB_HOST
        else:
            web_host = ("0.0.0.0", "")[settings.WEB_IPV6]

        self.options.update(
            {
                "data_root": os.path.join(settings.PROG_DIR, "gui", settings.GUI_NAME),
                "web_root": settings.WEB_ROOT,
                "host": web_host,
                "enable_https": settings.ENABLE_HTTPS,
                "handle_reverse_proxy": settings.HANDLE_REVERSE_PROXY,
                "log_dir": (None, settings.LOG_DIR)[settings.WEB_LOG],
                # 'username': oldbeard.WEB_USERNAME or '',
                # 'password': oldbeard.WEB_PASSWORD or '',
            }
        )

        self.options.setdefault("port", settings.WEB_PORT or 8081)

        self.server = None

        # video root
        if settings.ROOT_DIRS:
            root_dirs = settings.ROOT_DIRS.split("|")
            self.video_root = root_dirs[int(root_dirs[0]) + 1]
        else:
            self.video_root = None

        # web root
        if self.options["web_root"]:
            settings.WEB_ROOT = self.options["web_root"] = "/" + self.options["web_root"].strip("/")

        # api root
        if not settings.API_KEY:
            settings.API_KEY = generateApiKey()
        self.options["api_root"] = f"{settings.WEB_ROOT}/api/{settings.API_KEY}"

        # tornado setup
        self.enable_https = self.options["enable_https"]

        self.https_cert = None
        if settings.HTTPS_CERT:
            self.https_cert = os.path.realpath(settings.HTTPS_CERT)
            if not os.path.exists(self.https_cert) and not os.path.isabs(self.https_cert):
                self.https_cert = os.path.realpath(os.path.join(settings.DATA_DIR, settings.HTTPS_CERT))

        self.https_key = None
        if settings.HTTPS_KEY:
            self.https_key = os.path.realpath(settings.HTTPS_KEY)
            if not os.path.exists(self.https_key) and not os.path.isabs(self.https_key):
                self.https_key = os.path.realpath(os.path.join(settings.DATA_DIR, settings.HTTPS_KEY))

        if self.enable_https:
            # If either the HTTPS certificate or key do not exist, make some self-signed ones.
            if not (self.https_cert and os.path.exists(self.https_cert) and self.https_key and os.path.exists(self.https_key)):
                if not create_https_certificates(self.https_cert, self.https_key):
                    logger.info("Unable to create CERT/KEY files, disabling HTTPS")
                    settings.ENABLE_HTTPS = self.enable_https = False

            if not (os.path.exists(self.https_cert) and os.path.exists(self.https_key)):
                logger.warning("Disabled HTTPS because of missing CERT and KEY files")
                settings.ENABLE_HTTPS = self.enable_https = False

        asyncio.set_event_loop_policy(AnyThreadEventLoopPolicy())

        # Load the app
        self.app = Application(
            [],
            debug=False,  # enables autoreload, compiled_template_cache, static_hash_cache, serve_traceback - This fixes the 404 page and fixes autoreload for
            #  devs. We could now update without restart possibly if we check DB version hasnt changed!
            autoreload=False,
            gzip=settings.WEB_USE_GZIP,
            cookie_secret=settings.WEB_COOKIE_SECRET,
            login_url=f'{self.options["web_root"]}/login/',
            static_path=self.options["data_root"],
            static_url_prefix=f'{self.options["web_root"]}/',
            static_handler_class=SickChillStaticFileHandler
            # default_handler_class=Custom404Handler
        )

        # Static File Handlers
        self.app.add_handlers(
            ".*$",
            [
                url(
                    rf'{self.options["web_root"]}/(favicon\.ico)',
                    SickChillStaticFileHandler,
                    {"path": os.path.join(self.options["data_root"], "images/ico")},
                    name="favicon",
                ),
                url(
                    rf'{self.options["web_root"]}/images/(.*)',
                    SickChillStaticFileHandler,
                    {"path": os.path.join(self.options["data_root"], "images")},
                    name="images",
                ),
                url(
                    rf'{self.options["web_root"]}/cache/images/(.*)',
                    SickChillStaticFileHandler,
                    {"path": os.path.join(settings.CACHE_DIR, "images")},
                    name="image_cache",
                ),
                url(rf'{self.options["web_root"]}/css/(.*)', SickChillStaticFileHandler, {"path": os.path.join(self.options["data_root"], "css")}, name="css"),
                url(rf'{self.options["web_root"]}/js/(.*)', SickChillStaticFileHandler, {"path": os.path.join(self.options["data_root"], "js")}, name="js"),
                url(
                    rf'{self.options["web_root"]}/fonts/(.*)',
                    SickChillStaticFileHandler,
                    {"path": os.path.join(self.options["data_root"], "fonts")},
                    name="fonts",
                )
                # TODO: WTF is this?
                # url(rf'{self.options["web_root"]}/videos/(.*)', SickChillStaticFileHandler,
                #     {"path": self.video_root}, name='videos')
            ],
        )

        # Main Handlers
        self.app.add_handlers(
            ".*$",
            [
                url(rf'{self.options["api_root"]}(/?.*)', ApiHandler, name="api"),
                url(rf'{self.options["web_root"]}/getkey(/?.*)', KeyHandler, name="get_api_key"),
                url(rf'{self.options["web_root"]}/api/builder', RedirectHandler, {"url": self.options["web_root"] + "/apibuilder/"}, name="apibuilder"),
                url(rf'{self.options["web_root"]}/login(/?)', LoginHandler, name="login"),
                url(rf'{self.options["web_root"]}/logout(/?)', LogoutHandler, name="logout"),
                url(rf'{self.options["web_root"]}/calendar/?', CalendarHandler, name="calendar"),
                url(rf'{self.options["web_root"]}/movies/(?P<route>details)/(?P<slug>.*)/', MoviesHandler, name="movies-details"),
                url(rf'{self.options["web_root"]}/movies/(?P<route>remove)/(?P<pk>.*)/', MoviesHandler, name="movies-remove"),
                url(rf'{self.options["web_root"]}/movies/(?P<route>add)/', MoviesHandler, name="movies-add"),
                url(rf'{self.options["web_root"]}/movies/(?P<route>search)/', MoviesHandler, name="movies-search"),
                url(rf'{self.options["web_root"]}/movies/(?P<route>list)/', MoviesHandler, name="movies-list"),
                url(rf'{self.options["web_root"]}/movies/(.*)', MoviesHandler, name="movies"),
                # routes added by @route decorator
                # Plus naked index with missing web_root prefix
            ]
            + Route.get_routes(self.options["web_root"]),
        )

    def run(self):
        if self.enable_https:
            protocol = "https"
            ssl_options = {"certfile": self.https_cert, "keyfile": self.https_key}
        else:
            protocol = "http"
            ssl_options = None

        logger.info(f"Starting SickChill on {protocol}://{self.options['host']}:{self.options['port']}/")

        try:
            self.server = self.app.listen(
                self.options["port"], self.options["host"], ssl_options=ssl_options, xheaders=settings.HANDLE_REVERSE_PROXY, protocol=protocol
            )
        except socket_error as ex:
            err_msg = ""
            if ex.errno == errno.EADDRINUSE:  # Address/port combination already in use
                if settings.LAUNCH_BROWSER and not self.daemon:
                    sickchill.start.launchBrowser("https" if settings.ENABLE_HTTPS else "http", self.options["port"], settings.WEB_ROOT)
                    logger.info("Launching browser and exiting")
                err_msg = "already in use!"

            logger.info(f"Could not start webserver on port {self.options['port']}: {err_msg or ex}")
            # noinspection PyProtectedMember
            os._exit(1)
        except Exception as ex:
            logger.info(f"Could not start webserver on port {self.options['port']}: {ex}")

            # noinspection PyProtectedMember
            os._exit(1)

        try:
            IOLoop.current().start()
            IOLoop.current().close(True)
        except (IOError, ValueError):
            # Ignore errors like "ValueError: I/O operation on closed kqueue fd". These might be thrown during a reload.
            pass

    def shutdown(self):
        self.alive = False
        IOLoop.current().stop()
