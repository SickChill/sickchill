import os
import datetime
import sickbeard
import webserve

from sickbeard import logger
from sickbeard.helpers import create_https_certificates
from tornado.web import Application, StaticFileHandler, RedirectHandler, HTTPError
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop

class MultiStaticFileHandler(StaticFileHandler):
    def initialize(self, paths, default_filename=None):
        self.paths = paths

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


class webserverInit():
    def __init__(self, options, cycleTime=datetime.timedelta(seconds=3)):

        self.amActive = False
        self.lastRun = datetime.datetime.fromordinal(1)
        self.cycleTime = cycleTime
        self.abort = False

        self.server = None
        self.ioloop = None
        self.tasks = []

        self.options = options
        self.options.setdefault('port', 8081)
        self.options.setdefault('host', '0.0.0.0')
        self.options.setdefault('log_dir', None)
        self.options.setdefault('username', '')
        self.options.setdefault('password', '')
        self.options.setdefault('web_root', '/')
        assert isinstance(self.options['port'], int)
        assert 'data_root' in self.options

        def http_error_401_hander(status, message, traceback, version):
            """ Custom handler for 401 error """
            if status != "401 Unauthorized":
                logger.log(u"Tornado caught an error: %s %s" % (status, message), logger.ERROR)
                logger.log(traceback, logger.DEBUG)
            return r'''<!DOCTYPE html>
    <html>
        <head>
            <title>%s</title>
        </head>
        <body>
            <br/>
            <font color="#0000FF">Error %s: You need to provide a valid username and password.</font>
        </body>
    </html>
    ''' % ('Access denied', status)

        def http_error_404_hander(status, message, traceback, version):
            """ Custom handler for 404 error, redirect back to main page """
            return r'''<!DOCTYPE html>
    <html>
        <head>
            <title>404</title>
            <script type="text/javascript" charset="utf-8">
              <!--
              location.href = "%s/home/"
              //-->
            </script>
        </head>
        <body>
            <br/>
        </body>
    </html>
    ''' % self.options['web_root']

        # tornado setup
        enable_https = self.options['enable_https']
        https_cert = self.options['https_cert']
        https_key = self.options['https_key']

        if enable_https:
            # If either the HTTPS certificate or key do not exist, make some self-signed ones.
            if not (https_cert and os.path.exists(https_cert)) or not (https_key and os.path.exists(https_key)):
                if not create_https_certificates(https_cert, https_key):
                    logger.log(u"Unable to create CERT/KEY files, disabling HTTPS")
                    sickbeard.ENABLE_HTTPS = False
                    enable_https = False

            if not (os.path.exists(https_cert) and os.path.exists(https_key)):
                logger.log(u"Disabled HTTPS because of missing CERT and KEY files", logger.WARNING)
                sickbeard.ENABLE_HTTPS = False
                enable_https = False

        # Load the app
        app = Application([],
                            log_function=lambda x: None,
                            debug=False,
                            gzip=True,
                            cookie_secret='61oETzKXQAGaYdkL5gEmGeJJFuYh7EQnp2XdTP1o/Vo=',
                            login_url='/login',
                            autoreload=True
        )

        # Index Handler
        app.add_handlers(".*$", [
            (r"/", RedirectHandler, {'url': '/home/'}),
            (r'/login', webserve.LoginHandler),
            (r'%s(.*)(/?)' % self.options['web_root'], webserve.IndexHandler)
        ])

        # Static Path Handler
        app.add_handlers(".*$", [
            ('%s/%s/(.*)([^/]*)' % (self.options['web_root'], 'images'), MultiStaticFileHandler,
             {'paths': [os.path.join(self.options['data_root'], 'images'),
                        os.path.join(sickbeard.CACHE_DIR, 'images'),
                        os.path.join(sickbeard.CACHE_DIR, 'images', 'thumbnails')]}),
            ('%s/%s/(.*)([^/]*)' % (self.options['web_root'], 'css'), MultiStaticFileHandler,
             {'paths': [os.path.join(self.options['data_root'], 'css')]}),
            ('%s/%s/(.*)([^/]*)' % (self.options['web_root'], 'js'), MultiStaticFileHandler,
             {'paths': [os.path.join(self.options['data_root'], 'js')]})

        ])

        if enable_https:
            protocol = "https"
            self.server = HTTPServer(app, no_keep_alive=True,
                                     ssl_options={"certfile": https_cert, "keyfile": https_key})
        else:
            protocol = "http"
            self.server = HTTPServer(app, no_keep_alive=True)

        logger.log(u"Starting SickRage on " + protocol + "://" + str(self.options['host']) + ":" + str(
            self.options['port']) + "/")

        self.ioloop = IOLoop.current()

    def start(self):
        self.server.listen(self.options['port'], self.options['host'])
        self.ioloop.start()

    def stop(self):
        self.ioloop.stop()

    def close(self):
        self.ioloop.close()

    def start_tasks(self):
        for task in self.tasks:
            task.start()

    def stop_tasks(self):
        for task in self.tasks:
            task.stop()
