import glob
import os
from abc import ABC

from sickchill import settings


class UpdateManagerBase(ABC):
    @staticmethod
    def get_update_url():
        return f"{settings.WEB_ROOT}/home/update/?pid={settings.PID}"

    @staticmethod
    def _clean_pyc(path):
        path_parts = [os.path.dirname(settings.PROG_DIR), path, '*.pyc']
        for f in glob.iglob(os.path.join(*path_parts)):
            os.remove(f)

        path_parts.insert(-1, '**')
        for f in glob.iglob(os.path.join(*path_parts)):
            os.remove(f)

    def list_remote_branches(self):
        raise NotImplementedError

    def get_current_version(self):
        raise NotImplementedError

    def get_current_commit_hash(self):
        raise NotImplementedError

    def get_newest_version(self):
        raise NotImplementedError

    def get_newest_commit_hash(self):
        raise NotImplementedError

    def get_num_commits_behind(self):
        raise NotImplementedError

    def set_newest_text(self):
        raise NotImplementedError

    def need_update(self):
        raise NotImplementedError

    def update(self):
        raise NotImplementedError
