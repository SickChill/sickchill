import os
import socket
import time
import threading
import sys
import sickbeard
import webserve
import webapi

from sickbeard import logger
from sickbeard.helpers import create_https_certificates
from tornado.web import Application, StaticFileHandler, RedirectHandler, HTTPError
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop


class MultiStaticFileHandler(StaticFileHandler):
    def initialize(self, paths, default_filename=None):
        self.paths = paths
        self.default_filename = default_filename

    def get(self, path, include_body=True):
        for p in self.paths:
            try:
                # Initialize the Static file with a path
                super(MultiStaticFileHandler, self).initialize(p)
                # Try to get the file
                return super(MultiStaticFileHandler, self).get(path)
            except HTTPError as exc:
                # File not found, carry on
                if exc.status_code == 404:
                    continue
                raise

        # Oops file not found anywhere!
        raise HTTPError(404)


class SRWebServer(threading.Thread):
    def __init__(self, options={}, io_loop=None):
        threading.Thread.__init__(self)
        self.daemon = True
        self.alive = True
        self.name = "TORNADO"
        self.io_loop = io_loop or IOLoop.current()

        self.options = options
        self.options.setdefault('port', 8081)
        self.options.setdefault('host', '0.0.0.0')
        self.options.setdefault('log_dir', None)
        self.options.setdefault('username', '')
        self.options.setdefault('password', '')
        self.options.setdefault('web_root', None)
        assert isinstance(self.options['port'], int)
        assert 'data_root' in self.options

        # video root
        if sickbeard.ROOT_DIRS:
            root_dirs = sickbeard.ROOT_DIRS.split('|')
            self.video_root = root_dirs[int(root_dirs[0]) + 1]
        else:
            self.video_root = None

        # web root
        self.options['web_root'] = ('/' + self.options['web_root'].lstrip('/')) if self.options[
            'web_root'] else ''

        # tornado setup
        self.enable_https = self.options['enable_https']
        self.https_cert = self.options['https_cert']
        self.https_key = self.options['https_key']

        if self.enable_https:
            # If either the HTTPS certificate or key do not exist, make some self-signed ones.
            if not (self.https_cert and os.path.exists(self.https_cert)) or not (
                self.https_key and os.path.exists(self.https_key)):
                if not create_https_certificates(self.https_cert, self.https_key):
                    logger.log(u"Unable to create CERT/KEY files, disabling HTTPS")
                    sickbeard.ENABLE_HTTPS = False
                    self.enable_https = False

            if not (os.path.exists(self.https_cert) and os.path.exists(self.https_key)):
                logger.log(u"Disabled HTTPS because of missing CERT and KEY files", logger.WARNING)
                sickbeard.ENABLE_HTTPS = False
                self.enable_https = False

        # Load the app
        self.app = Application([],
                                 debug=True,
                                 autoreload=False,
                                 gzip=True,
                                 xheaders=sickbeard.HANDLE_REVERSE_PROXY,
                                 cookie_secret='61oETzKXQAGaYdkL5gEmGeJJFuYh7EQnp2XdTP1o/Vo='
        )

        # Main Handler
        self.app.add_handlers(".*$", [
            (r'%s/api/(.*)(/?)' % self.options['web_root'], webapi.Api),
            (r'%s/(.*)(/?)' % self.options['web_root'], webserve.MainHandler),
            (r'(.*)', webserve.MainHandler)
        ])

        # Static Path Handler
        self.app.add_handlers(".*$", [
            (r'%s/(favicon\.ico)' % self.options['web_root'], MultiStaticFileHandler,
             {'paths': [os.path.join(self.options['data_root'], 'images/ico/favicon.ico')]}),
            (r'%s/%s/(.*)(/?)' % (self.options['web_root'], 'images'), MultiStaticFileHandler,
             {'paths': [os.path.join(self.options['data_root'], 'images'),
                        os.path.join(sickbeard.CACHE_DIR, 'images')]}),
            (r'%s/%s/(.*)(/?)' % (self.options['web_root'], 'css'), MultiStaticFileHandler,
             {'paths': [os.path.join(self.options['data_root'], 'css')]}),
            (r'%s/%s/(.*)(/?)' % (self.options['web_root'], 'js'), MultiStaticFileHandler,
             {'paths': [os.path.join(self.options['data_root'], 'js')]}),
        ])

        # Static Videos Path
        if self.video_root:
            self.app.add_handlers(".*$", [
                (r'%s/%s/(.*)' % (self.options['web_root'], 'videos'), MultiStaticFileHandler,
                 {'paths': [self.video_root]}),
            ])

    def run(self):
        if self.enable_https:
            protocol = "https"
            self.server = HTTPServer(self.app, ssl_options={"certfile": self.https_cert, "keyfile": self.https_key})
        else:
            protocol = "http"
            self.server = HTTPServer(self.app)

        logger.log(u"Starting SickRage on " + protocol + "://" + str(self.options['host']) + ":" + str(
            self.options['port']) + "/")

        try:
            self.server.listen(self.options['port'], self.options['host'])
        except:
            etype, evalue, etb = sys.exc_info()
            logger.log(
                "Could not start webserver on %s. Excpeption: %s, Error: %s" % (self.options['port'], etype, evalue),
                logger.ERROR)
            return

        try:
            self.io_loop.start()
            self.io_loop.close(True)
        except (IOError, ValueError):
            # Ignore errors like "ValueError: I/O operation on closed kqueue fd". These might be thrown during a reload.
            pass

    def shutDown(self):
        self.alive = False
        if self.server:
            logger.log("Shutting down tornado")
            self.server.stop()
            self.io_loop.stop()
            self.join()