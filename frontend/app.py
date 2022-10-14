import threading

from flask import Flask

from .views.shows import shows_blueprint


class FlaskServer(threading.Thread):
    def __init__(self, host, port):
        super().__init__(name="FLASK")
        self.host = host
        self.port = port
        self.daemon = True
        self.alive = True

    def run(self):
        self.app = Flask("SickFlask", template_folder="frontend/templates", static_folder="frontend/static", static_url_path="/static")
        self.app.config.from_object("frontend.configurations.DevelopmentConfig")
        self.app.register_blueprint(shows_blueprint)
        self.app.run(host=self.host, port=self.port, use_reloader=False)

    def stop(self):
        self.alive = False
        del self.app
