# coding=utf-8
import os
import threading

from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.routes import route
from tornado.web import Application, RedirectHandler, StaticFileHandler

import sickbeard
from sickbeard import logger
from sickbeard.helpers import create_https_certificates, generateApiKey
from sickbeard.webapi import ApiHandler
from sickbeard.webserve import CalendarHandler, KeyHandler, LoginHandler, LogoutHandler
from sickrage.helper.encoding import ek


class SRWebServer(threading.Thread):  # pylint: disable=too-many-instance-attributes
    def __init__(self, options=None, io_loop=None):
        threading.Thread.__init__(self)
        self.daemon = True
        self.alive = True
        self.name = "TORNADO"
        self.io_loop = io_loop or IOLoop.current()

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
                    logger.log(u"Unable to create CERT/KEY files, disabling HTTPS")
                    sickbeard.ENABLE_HTTPS = False
                    self.enable_https = False

            if not (ek(os.path.exists, self.https_cert) and ek(os.path.exists, self.https_key)):
                logger.log(u"Disabled HTTPS because of missing CERT and KEY files", logger.WARNING)
                sickbeard.ENABLE_HTTPS = False
                self.enable_https = False

        # Load the app
        self.app = Application(
            [],
            debug=True,
            autoreload=False,
            gzip=sickbeard.WEB_USE_GZIP,
            cookie_secret=sickbeard.WEB_COOKIE_SECRET,
            login_url='{0}/login/'.format(self.options['web_root']),
        )

        # Main Handlers
        self.app.add_handlers('.*$', [
            # webapi handler
            (r'{0}(/?.*)'.format(self.options['api_root']), ApiHandler),

            # webapi key retrieval
            (r'{0}/getkey(/?.*)'.format(self.options['web_root']), KeyHandler),

            # webapi builder redirect
            (r'{0}/api/builder'.format(self.options['web_root']), RedirectHandler, {"url": self.options['web_root'] + '/apibuilder/'}),

            # webui login/logout handlers
            (r'{0}/login(/?)'.format(self.options['web_root']), LoginHandler),
            (r'{0}/logout(/?)'.format(self.options['web_root']), LogoutHandler),

            # Web calendar handler (Needed because option Unprotected calendar)
            (r'{0}/calendar'.format(self.options['web_root']), CalendarHandler),

            # webui handlers
        ] + route.get_routes(self.options['web_root']))

        # Static File Handlers
        self.app.add_handlers(".*$", [
            # favicon
            (r'{0}/(favicon\.ico)'.format(self.options['web_root']), StaticFileHandler,
             {"path": ek(os.path.join, self.options['data_root'], 'images/ico/favicon.ico')}),

            # images
            (r'{0}/images/(.*)'.format(self.options['web_root']), StaticFileHandler,
             {"path": ek(os.path.join, self.options['data_root'], 'images')}),

            # cached images
            (r'{0}/cache/images/(.*)'.format(self.options['web_root']), StaticFileHandler,
             {"path": ek(os.path.join, sickbeard.CACHE_DIR, 'images')}),

            # css
            (r'{0}/css/(.*)'.format(self.options['web_root']), StaticFileHandler,
             {"path": ek(os.path.join, self.options['data_root'], 'css')}),

            # javascript
            (r'{0}/js/(.*)'.format(self.options['web_root']), StaticFileHandler,
             {"path": ek(os.path.join, self.options['data_root'], 'js')}),

            # fonts
            (r'{0}/fonts/(.*)'.format(self.options['web_root']), StaticFileHandler,
             {"path": ek(os.path.join, self.options['data_root'], 'fonts')}),

            # videos
            (r'{0}/videos/(.*)'.format(self.options['web_root']), StaticFileHandler,
             {"path": self.video_root})
        ])

    def run(self):
        if self.enable_https:
            protocol = "https"
            ssl_options = {"certfile": self.https_cert, "keyfile": self.https_key}
        else:
            protocol = "http"
            ssl_options = None

        logger.log(u"Starting SickRage on " + protocol + "://" + str(self.options['host']) + ":" + str(
            self.options['port']) + "/")

        try:
            self.server = self.app.listen(self.options['port'], self.options['host'], ssl_options=ssl_options,
                                          xheaders=sickbeard.HANDLE_REVERSE_PROXY, protocol=protocol)
        except Exception:
            if sickbeard.LAUNCH_BROWSER and not self.daemon:
                sickbeard.launchBrowser('https' if sickbeard.ENABLE_HTTPS else 'http', self.options['port'], sickbeard.WEB_ROOT)
                logger.log(u"Launching browser and exiting")
            logger.log(u"Could not start webserver on port {0}, already in use!".format(self.options['port']))
            os._exit(1)  # pylint: disable=protected-access

        try:
            self.io_loop.start()
            self.io_loop.close(True)
        except (IOError, ValueError):
            # Ignore errors like "ValueError: I/O operation on closed kqueue fd". These might be thrown during a reload.
            pass

    def shutDown(self):
        self.alive = False
        self.io_loop.stop()
