import asyncio
import errno
import os
import threading
from pathlib import Path
from socket import AF_INET, AF_INET6, error as socket_error, SOMAXCONN
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
    def __init__(self):
        super().__init__()
        self.daemon = True
        self.alive = True
        self.name = "WEBSERVER"

        if settings.WEB_HOST and settings.WEB_HOST != "0.0.0.0":
            web_host = settings.WEB_HOST
        else:
            web_host = ("0.0.0.0", "")[settings.WEB_IPV6]

        self.data_root = settings.PROG_DIR / "gui" / settings.GUI_NAME
        self.web_root = "/" + settings.WEB_ROOT.strip("/")
        self.hosts = web_host
        self.log_dir = (None, settings.LOG_DIR)[settings.WEB_LOG]

        self.port = settings.WEB_PORT

        # api root
        if not settings.API_KEY:
            settings.API_KEY = generateApiKey()

        self.api_root = f"{settings.WEB_ROOT}/api/{settings.API_KEY}"

        self.https_key = None
        self.https_cert = None

        if settings.ENABLE_HTTPS:
            self.https_cert = Path(settings.HTTPS_CERT)
            if not self.https_cert.exists():
                self.https_cert = settings.DATA_DIR / settings.HTTPS_CERT

            if settings.HTTPS_KEY:
                self.https_key = os.path.realpath(settings.HTTPS_KEY)
                if not os.path.exists(self.https_key) and not os.path.isabs(self.https_key):
                    self.https_key = os.path.realpath(os.path.join(settings.DATA_DIR, settings.HTTPS_KEY))

            # If either the HTTPS certificate or key do not exist, make some self-signed ones.
            if not (self.https_cert and os.path.exists(self.https_cert) and self.https_key and os.path.exists(self.https_key)):
                if not create_https_certificates(self.https_cert, self.https_key):
                    logger.info("Unable to create CERT/KEY files, disabling HTTPS")
                    settings.ENABLE_HTTPS = False

            if not (os.path.exists(self.https_cert) and os.path.exists(self.https_key)):
                logger.warning("Disabled HTTPS because of missing CERT and KEY files")
                settings.ENABLE_HTTPS = False

        asyncio.set_event_loop_policy(AnyThreadEventLoopPolicy())

        # Load the app
        self.app: Application = Application(
            [],
            debug=False,  # enables autoreload, compiled_template_cache, static_hash_cache, serve_traceback - This fixes the 404 page and fixes autoreload for
            #  devs. We could now update without restart possibly if we check DB version hasnt changed!
            autoreload=False,
            gzip=settings.WEB_USE_GZIP,
            cookie_secret=settings.WEB_COOKIE_SECRET,
            login_url=f"{self.web_root}/login/",
            static_path=self.data_root,
            static_url_prefix=f"{self.web_root}/",
            static_handler_class=SickChillStaticFileHandler
            # default_handler_class=Custom404Handler
        )

        # Static File Handlers
        self.app.add_handlers(
            ".*$",
            [
                url(
                    rf"{self.web_root}/(favicon\.ico)",
                    SickChillStaticFileHandler,
                    {"path": os.path.join(self.data_root, "images/ico")},
                    name="favicon",
                ),
                url(
                    rf"{self.web_root}/images/(.*)",
                    SickChillStaticFileHandler,
                    {"path": os.path.join(self.data_root, "images")},
                    name="images",
                ),
                url(
                    rf"{self.web_root}/cache/images/(.*)",
                    SickChillStaticFileHandler,
                    {"path": os.path.join(settings.CACHE_DIR, "images")},
                    name="image_cache",
                ),
                url(rf"{self.web_root}/css/(.*)", SickChillStaticFileHandler, {"path": os.path.join(self.data_root, "css")}, name="css"),
                url(rf"{self.web_root}/js/(.*)", SickChillStaticFileHandler, {"path": os.path.join(self.data_root, "js")}, name="js"),
                url(
                    rf"{self.web_root}/fonts/(.*)",
                    SickChillStaticFileHandler,
                    {"path": os.path.join(self.data_root, "fonts")},
                    name="fonts",
                )
                # TODO: WTF is this?
                # url(rf'{self.web_root}/videos/(.*)', SickChillStaticFileHandler,
                #     {"path": self.video_root}, name='videos')
            ],
        )

        # Main Handlers
        self.app.add_handlers(
            ".*$",
            [
                url(rf"{self.api_root}(/?.*)", ApiHandler, name="api"),
                url(rf"{self.web_root}/getkey(/?.*)", KeyHandler, name="get_api_key"),
                url(rf"{self.web_root}/api/builder", RedirectHandler, {"url": self.web_root + "/apibuilder/"}, name="apibuilder"),
                url(rf"{self.web_root}/login(/?)", LoginHandler, name="login"),
                url(rf"{self.web_root}/logout(/?)", LogoutHandler, name="logout"),
                url(rf"{self.web_root}/calendar/?", CalendarHandler, name="calendar"),
                url(rf"{self.web_root}/movies/(?P<route>details)/(?P<slug>.*)/", MoviesHandler, name="movies-details"),
                url(rf"{self.web_root}/movies/(?P<route>remove)/(?P<pk>.*)/", MoviesHandler, name="movies-remove"),
                url(rf"{self.web_root}/movies/(?P<route>add)/", MoviesHandler, name="movies-add"),
                url(rf"{self.web_root}/movies/(?P<route>search)/", MoviesHandler, name="movies-search"),
                url(rf"{self.web_root}/movies/(?P<route>list)/", MoviesHandler, name="movies-list"),
                url(rf"{self.web_root}/movies/(.*)", MoviesHandler, name="movies"),
                # routes added by @route decorator
                # Plus naked index with missing web_root prefix
            ]
            + Route.get_routes(self.web_root),
        )

    def run(self):
        raise SystemExit(2)
        if settings.ENABLE_HTTPS:
            protocol = "https"
            ssl_options = {"certfile": self.https_cert, "keyfile": self.https_key}
        else:
            protocol = "http"
            ssl_options = None

        try:
            if "," in self.hosts:
                hosts = self.hosts.split(",")
            else:
                hosts = [self.hosts]

            for host in hosts:
                logger.info(f"Starting SickChill on {protocol}://{host}:{self.port}/")
                family = (AF_INET, AF_INET6)[":" in host]
                self.app.listen(
                    self.port,
                    host,
                    family=family,
                    ssl_options=ssl_options,
                    xheaders=settings.HANDLE_REVERSE_PROXY,
                    protocol=protocol,
                    reuse_port=True,
                    backlog=min(SOMAXCONN, 512),
                )
        except socket_error as ex:
            err_msg = ""
            if ex.errno == errno.EADDRINUSE:  # Address/port combination already in use
                if not (settings.NO_LAUNCH_BROWSER or self.daemon):
                    sickchill.start.launchBrowser("https" if settings.ENABLE_HTTPS else "http", self.port, settings.WEB_ROOT)
                    logger.info("Launching browser and exiting")
                err_msg = "already in use!"

            logger.info(f"Could not start webserver on port {self.port}: {err_msg or ex}")
            raise SystemExit(1)
        except Exception as ex:
            logger.info(f"Could not start webserver on port {self.port}: {ex}")

            raise SystemExit(1)

        try:
            IOLoop.current().start()
            IOLoop.current().close(True)
        except (IOError, ValueError):
            # Ignore errors like "ValueError: I/O operation on closed kqueue fd". These might be thrown during a reload.
            pass

    def shutdown(self):
        self.alive = False
        IOLoop.current().stop()
