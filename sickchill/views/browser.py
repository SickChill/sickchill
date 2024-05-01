import json
from pathlib import Path

from sickchill import settings
from sickchill.oldbeard import config
from sickchill.oldbeard.browser import folders_at_path
from sickchill.views.index import WebRoot
from sickchill.views.routes import Route


@Route("/browser(/?.*)", name="filebrowser")
class WebFileBrowser(WebRoot):
    def index(self):
        self.set_header("Cache-Control", "max-age=0,no-cache,no-store")
        self.set_header("Content-Type", "application/json")

        path = self.get_argument("path")
        include_files = config.checkbox_to_value(self.get_argument("includeFiles", "false"))
        file_types = self.get_argument("fileTypes", "*").split(",")

        path = Path(path)
        if not path.exists():
            path = Path(settings.DATA_DIR)
        return json.dumps(folders_at_path(path, include_parent=True, include_files=include_files, file_types=file_types))

    def complete(self):
        self.set_header("Cache-Control", "max-age=0,no-cache,no-store")
        self.set_header("Content-Type", "application/json")

        include_files = config.checkbox_to_value(self.get_argument("includeFiles", "false"))
        term = self.get_argument("term")
        file_types = self.get_argument("fileTypes", "*").split(",")

        paths = []
        for entry in folders_at_path(Path(term), include_parent=True, include_files=include_files, file_types=file_types):
            if "path" in entry:
                paths.append(entry.get("path", ""))

        return json.dumps(paths)
