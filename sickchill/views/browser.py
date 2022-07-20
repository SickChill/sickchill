import json
import os

from tornado.escape import xhtml_unescape

from sickchill.oldbeard.browser import foldersAtPath

from .index import WebRoot
from .routes import Route


@Route("/browser(/?.*)", name="filebrowser")
class WebFileBrowser(WebRoot):
    def index(self, path="", includeFiles=False, fileTypes=""):

        self.set_header("Cache-Control", "max-age=0,no-cache,no-store")
        self.set_header("Content-Type", "application/json")

        return json.dumps(foldersAtPath(xhtml_unescape(path), True, bool(int(includeFiles)), fileTypes.split(",")))

    def complete(self, term, includeFiles=False, fileTypes=""):

        self.set_header("Cache-Control", "max-age=0,no-cache,no-store")
        self.set_header("Content-Type", "application/json")
        paths = [
            entry["path"]
            for entry in foldersAtPath(os.path.dirname(xhtml_unescape(term)), includeFiles=bool(int(includeFiles)), fileTypes=fileTypes.split(","))
            if "path" in entry
        ]

        return json.dumps(paths)
