import threading
from typing import TYPE_CHECKING

from flask import Flask

from sickchill import settings

from .views.shows import shows_blueprint

if TYPE_CHECKING:
    from sickchill.views.server_settings import SRWebServer


class FlaskServer(threading.Thread):
    def __init__(self, host, port, tornado: "SRWebServer"):
        super().__init__(name="FLASK")
        self.alive = True
        self.daemon = False
        self.host = host
        self.port = port
        self.web_root = tornado.web_root
        self.key = tornado.https_key
        self.cert = tornado.https_cert
        self.enable_https = settings.ENABLE_HTTPS

        self.app: Flask = Flask(
            "sickchill.frontend", template_folder="sickchilll/frontend/templates", static_folder="sickchill/frontend/static", static_url_path="/static"
        )
        print(self.app.logger.handlers)
        self.app.config.from_object("sickchill.frontend.configurations.DevelopmentConfig")
        self.app.register_blueprint(shows_blueprint)
        self.app.jinja_env.auto_reload = True
        self.cookie_secret = tornado.app.settings["cookie_secret"]

        self.app.logger.debug("Debug is enabled")

        self.app.config["EXPLAIN_TEMPLATE_LOADING"] = True
        self.app.config["TEMPLATES_AUTO_RELOAD"] = True
        self.app.config["JSONIFY_PRETTYPRINT_REGULAR"] = True
        self.app.config["APPLICATION_ROOT"] = self.web_root
        self.app.config["SECRET_KEY"] = self.cookie_secret

        if self.enable_https:
            self.app.config["ssl_context"] = (self.cert, self.key)
            self.app.config["host"] = self.host
            self.app.config["port"] = self.port
            self.app.config["PREFERRED_URL_SCHEME"] = "https"
            self.app.config["SESSION_COOKIE_SECURE"] = True

            # TODO: Should this be configurable?
            # self.app.config["PERMANENT_SESSION_LIFETIME"] = datetime.timedelta(days=31)

    def run(self):
        self.app.logger.info(f"Starting SickFlask on {('http', 'https')[self.enable_https]}://{self.host}:{self.port}")
        self.app.run(use_reloader=False)

    def stop(self):
        self.app.logger.info("Stopping SickFlask")
        self.alive = False
        del self.app
