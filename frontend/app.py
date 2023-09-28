"""
This is the global flask application under which all web interfaces for sickchill media types run on
"""

import threading

from flask import Flask

from .config import config_blueprint
from .shows import shows_blueprint
from .movies import movies_blueprint

from .utils import logger


class FlaskServer(threading.Thread):
    """Flask application class to set up the sickchill flask webserver interface"""

    def __init__(self, host, port):
        super().__init__(name="FLASK")
        self.host = host
        self.port = port
        self.daemon = True
        self.alive = True

    def run(self):
        """Run the flask server"""
        self.app = Flask("SickFlask", template_folder="frontend/templates", static_folder="frontend/static", static_url_path="/static")
        self.app.config.from_object("frontend.app.DevelopmentConfig")

        self.app.register_blueprint(config_blueprint)
        self.app.register_blueprint(shows_blueprint)
        self.app.register_blueprint(movies_blueprint)
        routes = "\n\t\t".join(f"{rule}" for rule in self.app.url_map.iter_rules())
        logger.debug(f"{self.app.name} Route:\n\t\t{routes}")

        self.app.run(host=self.host, port=self.port, use_reloader=False)

    def stop(self):
        """Stop the flask server"""
        self.alive = False
        del self.app


class BaseConfig:
    """
    Base config class
    """

    DEBUG = True
    TESTING = False


class ProductionConfig(BaseConfig):
    """
    Production specific config
    """

    DEBUG = False


class DevelopmentConfig(BaseConfig):
    """
    Development environment specific configuration
    """

    DEBUG = True
    TESTING = True
