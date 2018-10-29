# coding=utf-8

from __future__ import print_function, unicode_literals

import os
import threading
from socket import errno, error as SocketError

from tornado.ioloop import IOLoop
from tornado.web import Application, RedirectHandler, StaticFileHandler

import sickchill
from sickchill import logger
from sickchill.helpers import create_https_certificates, generateApiKey
from sickchill.routes import route
from sickchill.webapi import ApiHandler
from sickchill.webserve import CalendarHandler, KeyHandler, LoginHandler, LogoutHandler
from sickchill.helper.encoding import ek


class SRWebServer(threading.Thread):  # pylint: disable=too-many-instance-attributes
    def __init__(self, options=None):
        threading.Thread.__init__(self)
        self.daemon = True
        self.alive = True
        self.name = "TORNADO"
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
        if sickchill.ROOT_DIRS:
            root_dirs = sickchill.ROOT_DIRS.split('|')
            self.video_root = root_dirs[int(root_dirs[0]) + 1]
        else:
            self.video_root = None

        # web root
        if self.options['web_root']:
            sickchill.WEB_ROOT = self.options['web_root'] = ('/' + self.options['web_root'].lstrip('/').strip('/'))

        # api root
        if not sickchill.API_KEY:
            sickchill.API_KEY = generateApiKey()
        self.options['api_root'] = r'{0}/api/{1}'.format(sickchill.WEB_ROOT, sickchill.API_KEY)

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
                    sickchill.ENABLE_HTTPS = False
                    self.enable_https = False

            if not (ek(os.path.exists, self.https_cert) and ek(os.path.exists, self.https_key)):
                logger.log("Disabled HTTPS because of missing CERT and KEY files", logger.WARNING)
                sickchill.ENABLE_HTTPS = False
                self.enable_https = False

        # Load the app
        self.app = Application(
            [],
            debug=True,
            autoreload=False,
            gzip=sickchill.WEB_USE_GZIP,
            cookie_secret=sickchill.WEB_COOKIE_SECRET,
            login_url='{0}/login/'.format(self.options['web_root']),
            static_path=self.options['data_root'],
            static_url_prefix='{0}/'.format(self.options['web_root']),
        )

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
             {"path": ek(os.path.join, sickchill.CACHE_DIR, 'images')}),

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

            # Web calendar handler (Needed for the "Unprotected Calendar" option)
            (r'{0}/calendar/?'.format(self.options['web_root']), CalendarHandler),

            # webui handlers
        ] + route.get_routes(self.options['web_root']))

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
                                          xheaders=sickchill.HANDLE_REVERSE_PROXY, protocol=protocol)
        except SocketError as ex:
            err_msg = ""
            if ex.errno == errno.EADDRINUSE:  # Address/port combination already in use
                if sickchill.LAUNCH_BROWSER and not self.daemon:
                    sickchill.launchBrowser('https' if sickchill.ENABLE_HTTPS else 'http', self.options['port'], sickchill.WEB_ROOT)
                    logger.log("Launching browser and exiting")
                err_msg = "already in use!"

            logger.log("Could not start webserver on port {0}: {1}".format(self.options['port'], err_msg or ex))
            os._exit(1)  # pylint: disable=protected-access
        except Exception as ex:
            logger.log("Could not start webserver on port {0}: {1}".format(self.options['port'], ex))
            os._exit(1)  # pylint: disable=protected-access

        try:
            self.io_loop.start()
            self.io_loop.close(True)
        except (IOError, ValueError):
            # Ignore errors like "ValueError: I/O operation on closed kqueue fd". These might be thrown during a reload.
            pass

    def shutdown(self):
        self.alive = False
        self.io_loop.stop()
