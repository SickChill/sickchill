# coding=utf-8
from __future__ import absolute_import, print_function, unicode_literals

# Stdlib Imports
import os
import threading
from socket import errno, error as socket_error

# Third Party Imports
from tornado.ioloop import IOLoop
from tornado.web import Application, RedirectHandler, StaticFileHandler, url

# First Party Imports
import sickbeard
from sickbeard import logger
from sickbeard.helpers import create_https_certificates, generateApiKey
from sickchill.helper.encoding import ek
from sickchill.views import CalendarHandler, LoginHandler, LogoutHandler
from sickchill.views.api import ApiHandler, KeyHandler

# Local Folder Imports
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


class SRWebServer(threading.Thread):
    def __init__(self, options=None):
        threading.Thread.__init__(self)
        self.daemon = True
        self.alive = True
        self.name = "WEBSERVER"
        self.io_loop = IOLoop.current()

        self.options = options or {}
        self.options.setdefault('port', 8081)
        self.options.setdefault('host', '0.0.0.0')
        self.options.setdefault('log_dir', None)
        self.options.setdefault('username', '')
        self.options.setdefault('password', '')
        self.options.setdefault('web_root', '/')

        assert isinstance(self.options['port'], int)
        assert 'data_root' in self.options

        self.server = None

        # video root
        if sickbeard.ROOT_DIRS:
            root_dirs = sickbeard.ROOT_DIRS.split('|')
            self.video_root = root_dirs[int(root_dirs[0]) + 1]
        else:
            self.video_root = None

        # web root
        if self.options['web_root']:
            sickbeard.WEB_ROOT = self.options['web_root'] = ('/' + self.options['web_root'].lstrip('/').strip('/'))

        # api root
        if not sickbeard.API_KEY:
            sickbeard.API_KEY = generateApiKey()
        self.options['api_root'] = r'{0}/api/{1}'.format(sickbeard.WEB_ROOT, sickbeard.API_KEY)

        # tornado setup
        self.enable_https = self.options['enable_https']
        self.https_cert = self.options['https_cert']
        self.https_key = self.options['https_key']

        if self.enable_https:
            # If either the HTTPS certificate or key do not exist, make some self-signed ones.
            if not (self.https_cert and ek(os.path.exists, self.https_cert)) or not (
                    self.https_key and ek(os.path.exists, self.https_key)):
                if not create_https_certificates(self.https_cert, self.https_key):
                    logger.log("Unable to create CERT/KEY files, disabling HTTPS")
                    sickbeard.ENABLE_HTTPS = False
                    self.enable_https = False

            if not (ek(os.path.exists, self.https_cert) and ek(os.path.exists, self.https_key)):
                logger.log("Disabled HTTPS because of missing CERT and KEY files", logger.WARNING)
                sickbeard.ENABLE_HTTPS = False
                self.enable_https = False

        # Load the app
        self.app = Application(
            [],
            debug=False,  # enables autoreload, compiled_template_cache, static_hash_cache, serve_traceback - This fixes the 404 page and fixes autoreload for
            #  devs. We could now update without restart possibly if we check DB version hasnt changed!
            autoreload=False,
            gzip=sickbeard.WEB_USE_GZIP,
            cookie_secret=sickbeard.WEB_COOKIE_SECRET,
            login_url='{0}/login/'.format(self.options['web_root']),
            static_path=self.options['data_root'],
            static_url_prefix='{0}/'.format(self.options['web_root'])
            # default_handler_class=Custom404Handler
        )

        # Static File Handlers
        self.app.add_handlers(".*$", [
            url(r'{0}/favicon.ico'.format(self.options['web_root']), StaticFileHandler,
                {"path": ek(os.path.join, self.options['data_root'], 'images/ico/favicon.ico')}, name='favicon'),

            url(r'{0}/images/(.*)'.format(self.options['web_root']), StaticFileHandler,
                {"path": ek(os.path.join, self.options['data_root'], 'images')}, name='images'),

            url(r'{0}/cache/images/(.*)'.format(self.options['web_root']), StaticFileHandler,
                {"path": ek(os.path.join, sickbeard.CACHE_DIR, 'images')}, name='image_cache'),

            url(r'{0}/css/(.*)'.format(self.options['web_root']), StaticFileHandler,
                {"path": ek(os.path.join, self.options['data_root'], 'css')}, name='css'),

            url(r'{0}/js/(.*)'.format(self.options['web_root']), StaticFileHandler,
                {"path": ek(os.path.join, self.options['data_root'], 'js')}, name='js'),

            url(r'{0}/fonts/(.*)'.format(self.options['web_root']), StaticFileHandler,
                {"path": ek(os.path.join, self.options['data_root'], 'fonts')}, name='fonts')

            # TODO: WTF is this?
            # url(r'{0}/videos/(.*)'.format(self.options['web_root']), StaticFileHandler,
            #     {"path": self.video_root}, name='videos')
        ])

        # Main Handlers
        self.app.add_handlers('.*$', [
            url(r'{0}(/?.*)'.format(self.options['api_root']), ApiHandler, name='api'),
            url(r'{0}/getkey(/?.*)'.format(self.options['web_root']), KeyHandler, name='get_api_key'),

            url(r'{0}/api/builder'.format(self.options['web_root']), RedirectHandler, {"url": self.options['web_root'] + '/apibuilder/'}, name='apibuilder'),
            url(r'{0}/login(/?)'.format(self.options['web_root']), LoginHandler, name='login'),
            url(r'{0}/logout(/?)'.format(self.options['web_root']), LogoutHandler, name='logout'),

            url(r'{0}/calendar/?'.format(self.options['web_root']), CalendarHandler, name='calendar'),

            # routes added by @route decorator
            # Plus naked index with missing web_root prefix
        ] + Route.get_routes(self.options['web_root']))

    def run(self):
        if self.enable_https:
            protocol = "https"
            ssl_options = {"certfile": self.https_cert, "keyfile": self.https_key}
        else:
            protocol = "http"
            ssl_options = None

        logger.log("Starting SickChill on " + protocol + "://" + str(self.options['host']) + ":" + str(
            self.options['port']) + "/")

        try:
            self.server = self.app.listen(self.options['port'], self.options['host'], ssl_options=ssl_options,
                                          xheaders=sickbeard.HANDLE_REVERSE_PROXY, protocol=protocol)
        except socket_error as ex:
            err_msg = ""
            if ex.errno == errno.EADDRINUSE:  # Address/port combination already in use
                if sickbeard.LAUNCH_BROWSER and not self.daemon:
                    sickbeard.launchBrowser('https' if sickbeard.ENABLE_HTTPS else 'http', self.options['port'], sickbeard.WEB_ROOT)
                    logger.log("Launching browser and exiting")
                err_msg = "already in use!"

            logger.log("Could not start webserver on port {0}: {1}".format(self.options['port'], err_msg or ex))
            # noinspection PyProtectedMember
            os._exit(1)
        except Exception as ex:
            logger.log("Could not start webserver on port {0}: {1}".format(self.options['port'], ex))

            # noinspection PyProtectedMember
            os._exit(1)

        try:
            self.io_loop.start()
            self.io_loop.close(True)
        except (IOError, ValueError):
            # Ignore errors like "ValueError: I/O operation on closed kqueue fd". These might be thrown during a reload.
            pass

    def shutdown(self):
        self.alive = False
        self.io_loop.stop()
