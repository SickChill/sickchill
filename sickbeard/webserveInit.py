import os
import traceback
import sickbeard
import webserve
import webapi

import tornado.options
from sickbeard import logger
from sickbeard.helpers import create_https_certificates
from tornado.web import Application, StaticFileHandler, RedirectHandler, HTTPError
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop

server = None

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

def initWebServer(options={}):
    options.setdefault('port', 8081)
    options.setdefault('host', '0.0.0.0')
    options.setdefault('log_dir', None)
    options.setdefault('username', '')
    options.setdefault('password', '')
    options.setdefault('web_root', '/')
    assert isinstance(options['port'], int)
    assert 'data_root' in options

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
''' % options['web_root']

    # tornado setup
    enable_https = options['enable_https']
    https_cert = options['https_cert']
    https_key = options['https_key']

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
                        debug=sickbeard.DEBUG,
                        gzip=True,
                        xheaders=True,
                        cookie_secret='61oETzKXQAGaYdkL5gEmGeJJFuYh7EQnp2XdTP1o/Vo=',
                        login_url='/login'
    )

    # Index Handler
    app.add_handlers(".*$", [
        (r"/", RedirectHandler, {'url': '/home/'}),
        (r'/login', webserve.LoginHandler),
        (r'/api/(.*)(/?)', webapi.Api),
        (r'%s(.*)(/?)' % options['web_root'], webserve.IndexHandler)
    ])

    # Static Path Handler
    app.add_handlers(".*$", [
        ('%s/%s/(.*)([^/]*)' % (options['web_root'], 'images'), MultiStaticFileHandler,
         {'paths': [os.path.join(options['data_root'], 'images'),
                    os.path.join(sickbeard.CACHE_DIR, 'images'),
                    os.path.join(sickbeard.CACHE_DIR, 'images', 'thumbnails')]}),
        ('%s/%s/(.*)([^/]*)' % (options['web_root'], 'css'), MultiStaticFileHandler,
         {'paths': [os.path.join(options['data_root'], 'css')]}),
        ('%s/%s/(.*)([^/]*)' % (options['web_root'], 'js'), MultiStaticFileHandler,
         {'paths': [os.path.join(options['data_root'], 'js')]})

    ])

    global server

    if enable_https:
        protocol = "https"
        server = HTTPServer(app, no_keep_alive=True,
                                 ssl_options={"certfile": https_cert, "keyfile": https_key})
    else:
        protocol = "http"
        server = HTTPServer(app, no_keep_alive=True)

    logger.log(u"Starting SickRage on " + protocol + "://" + str(options['host']) + ":" + str(
        options['port']) + "/")

    try:
        server.listen(options['port'], options['host'])
    except:
        pass

def shutdown():
    global server

    logger.log('Shutting down tornado')
    try:
        IOLoop.current().stop()
    except RuntimeError:
        pass
    except:
        logger.log('Failed shutting down the server: %s' % traceback.format_exc(), logger.ERROR)