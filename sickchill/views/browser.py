import json
import os

from sickchill.oldbeard import config
from sickchill.oldbeard.browser import foldersAtPath

from .index import WebRoot
from .routes import Route


@Route("/browser(/?.*)", name="filebrowser")
class WebFileBrowser(WebRoot):
    def index(self):
        self.set_header("Cache-Control", "max-age=0,no-cache,no-store")
        self.set_header("Content-Type", "application/json")

        path = self.get_argument("path")
        includeFiles = config.checkbox_to_value(self.get_argument("includeFiles", False, strip=True))
        fileTypes = self.get_argument("fileTypes", "", strip=True).split(",")

        return json.dumps(foldersAtPath(path, True, includeFiles, fileTypes))

    def complete(self, term, includeFiles=False, fileTypes=""):
        self.set_header("Cache-Control", "max-age=0,no-cache,no-store")
        self.set_header("Content-Type", "application/json")

        includeFiles = config.checkbox_to_value(self.get_argument("includeFiles", False, strip=True))
        term = self.get_argument("term", strip=True)
        fileTypes = self.get_argument("fileTypes", "", strip=True).split(",")
        paths = [entry["path"] for entry in foldersAtPath(os.path.dirname(term), includeFiles=includeFiles, fileTypes=fileTypes) if "path" in entry]

        return json.dumps(paths)
