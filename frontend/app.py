"""
This is the global flask application under which all web interfaces for sickchill media types run on
"""

import threading
from logging.config import dictConfig

from flask import Flask

from .config import blueprint as config_blueprint
from .movies import blueprint as movies_blueprint
from .shows import blueprint as shows_blueprint


class FlaskServer(threading.Thread):
    """Flask application class to set up the sickchill flask webserver interface"""

    def __init__(self, host, port):
        super().__init__(name="FLASK")
        self.app = None
        self.host = host
        self.port = port
        self.daemon = True
        self.alive = True

    def run(self):
        """Run the flask server"""
        self.app = Flask("SickFlask", template_folder="frontend/templates", static_folder="frontend/static", static_url_path="/static")
        self.app.config.from_object(DevelopmentConfig)

        self.app.register_blueprint(config_blueprint)
        self.app.register_blueprint(shows_blueprint)
        self.app.register_blueprint(movies_blueprint)
        routes = "\n\t\t".join(f"{rule}" for rule in self.app.url_map.iter_rules())
        self.app.logger.debug(f"{self.app.name} Route:\n\t\t{routes}")

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


if __name__ == "__main__":
    dictConfig(
        {
            "version": 1,
            "formatters": {
                "default": {
                    "format": "[%(asctime)s] %(levelname)s in %(module)s: %(message)s",
                }
            },
            "handlers": {"wsgi": {"class": "logging.StreamHandler", "stream": "ext://flask.logging.wsgi_errors_stream", "formatter": "default"}},
            "root": {"level": "DEBUG", "handlers": ["wsgi"]},
        }
    )
