import os
import traceback
import sickbeard
import webserve
import webapi

from sickbeard import logger
from sickbeard.helpers import create_https_certificates
from tornado.web import Application, StaticFileHandler, RedirectHandler, HTTPError
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop

server = None


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


def initWebServer(options={}):
    options.setdefault('port', 8081)
    options.setdefault('host', '0.0.0.0')
    options.setdefault('log_dir', None)
    options.setdefault('username', '')
    options.setdefault('password', '')
    options.setdefault('web_root', '/')
    assert isinstance(options['port'], int)
    assert 'data_root' in options

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
                        debug=False,
                        gzip=True,
                        xheaders=sickbeard.HANDLE_REVERSE_PROXY,
                        cookie_secret='61oETzKXQAGaYdkL5gEmGeJJFuYh7EQnp2XdTP1o/Vo='
    )

    # Main Handler
    app.add_handlers(".*$", [
        (r"%s" % options['web_root'], RedirectHandler, {'url': '%s/home/' % options['web_root']}),
        (r'%s/api/(.*)(/?)' % options['web_root'], webapi.Api),
        (r'%s/(.*)(/?)' % options['web_root'], webserve.MainHandler)
    ])

    # Static Path Handler
    app.add_handlers(".*$", [
        (r'%s/(favicon\.ico)' % options['web_root'], MultiStaticFileHandler,
         {'paths': [os.path.join(options['data_root'], 'images/ico/favicon.ico')]}),
        (r'%s/%s/(.*)(/?)' % (options['web_root'], 'images'), MultiStaticFileHandler,
         {'paths': [os.path.join(options['data_root'], 'images'),
                    os.path.join(sickbeard.CACHE_DIR, 'images')]}),
        (r'%s/%s/(.*)(/?)' % (options['web_root'], 'css'), MultiStaticFileHandler,
         {'paths': [os.path.join(options['data_root'], 'css')]}),
        (r'%s/%s/(.*)(/?)' % (options['web_root'], 'js'), MultiStaticFileHandler,
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

    server.listen(options['port'], options['host'])

def shutdown():

    logger.log('Shutting down tornado IO loop')
    try:
        IOLoop.current().stop()
    except RuntimeError:
        pass
    except:
        logger.log('Failed shutting down tornado IO loop: %s' % traceback.format_exc(), logger.ERROR)